"""Flake-level grouping: a flake is one connected region of material; the
uniform-thickness terraces found by the segmentation are regions of interest
inside it.

The flake mask is stricter than the segmentation foreground so that residue
haze (hBN) and faint film do not join neighbouring flakes into one object:
significant contrast, and for transparent materials also |C| above a haze
level; a morphological opening cuts thin bridges; small holes are filled.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np
from scipy import ndimage

HAZE_LEVEL = {"hbn": 0.15}       # min |C| of flake material (transparent materials only)


@dataclass
class FlakeObj:
    fid: int                      # flake label in the flake label image
    slices: tuple                 # bbox in working pixels
    mask: np.ndarray              # bool mask in the bbox
    area_um2: float
    inscribed_d_um: float
    length_um: float
    width_um: float
    centroid_px: tuple            # original pixels
    regions: list = field(default_factory=list)   # segment.Region labels inside
    metrics: dict = field(default_factory=dict)


def material_mask(cs: np.ndarray, noise: np.ndarray, chip: np.ndarray, material: str) -> np.ndarray:
    thr = np.maximum(4 * noise * 0.6, 0.035)
    fg = (np.abs(cs) > thr[None, None, :]).any(axis=2) & chip
    lvl = HAZE_LEVEL.get(material)
    if lvl:
        fg &= np.linalg.norm(cs, axis=2) > lvl
    fg = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)).astype(bool)
    from skimage.morphology import remove_small_holes
    return remove_small_holes(fg, area_threshold=60) & chip


MAX_FLAKE_UM = 3000.0       # larger connected "flakes" are dropped (chip-edge bands, artefacts)


def _flake_obj(fid, sl, m, px_um, work_scale):
    """A FlakeObj of mask m (bool, in the bbox sl of the working image): its size and shape."""
    dist = cv2.distanceTransform(np.pad(m.astype(np.uint8), 1), cv2.DIST_L2, 5)
    cnts, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = np.vstack(cnts).reshape(-1, 2).astype(np.float32)
    (_, _), (w_, h_), _ = cv2.minAreaRect(pts)
    ys, xs = np.nonzero(m)
    return FlakeObj(
        fid=fid, slices=sl, mask=m, area_um2=float(m.sum()) * px_um ** 2,
        inscribed_d_um=2 * float(dist.max()) * px_um,
        length_um=(max(w_, h_) + 1) * px_um, width_um=(min(w_, h_) + 1) * px_um,
        centroid_px=((xs.mean() + sl[1].start + 0.5) / work_scale - 0.5,
                     (ys.mean() + sl[0].start + 0.5) / work_scale - 0.5))


def build(regions, region_labels: np.ndarray, cs: np.ndarray, noise, chip, material: str,
          px_um: float, work_scale: float, min_area_um2: float = 50.0, exclude=(), allow=None):
    """Label flakes and attach regions.  exclude: labels of regions that are not material (tape residue): kept out
    of the flake masks.  allow: only these pixels can be flake (rhombohedral screening: thin graphite; thick graphite
    attached to a flake is not part of it).  Returns (flakes, flake_label_image, region -> flake)."""
    fm = material_mask(cs, noise, chip, material)
    # every other segmented region belongs to the material: add it (the stricter mask
    # can lose faint graphene), then label
    if exclude:
        res = np.isin(region_labels, np.fromiter(exclude, np.int32))
        fm = (fm & ~res) | ((region_labels > 0) & ~res)
    else:
        fm |= region_labels > 0
    if allow is not None:
        # (the opening cuts the thin seams of edge colours that are left where thick graphite touches a thin flake)
        fm = cv2.morphologyEx((fm & allow).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
        fm |= (region_labels > 0) & ~np.isin(region_labels, np.fromiter(exclude, np.int32)) if exclude else region_labels > 0
    lab, n = ndimage.label(fm, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(lab)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    min_px = min_area_um2 / px_um ** 2
    flakes = {}
    for fid, sl in enumerate(objs, start=1):
        if sl is None or sizes[fid] < min_px:
            continue
        # no exfoliated flake is millimetres across: a band along the chip edge or a mosaic artefact
        if max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) * px_um > MAX_FLAKE_UM:
            continue
        flakes[fid] = _flake_obj(fid, sl, lab[sl] == fid, px_um, work_scale)
    region_flake = {}
    for r in regions:
        ys, xs = np.nonzero(r.mask)
        yy, xx = ys + r.slices[0].start, xs + r.slices[1].start
        ids = lab[yy, xx]
        ids = ids[ids > 0]
        if not len(ids):
            continue
        fid = int(np.bincount(ids).argmax())
        if fid in flakes:
            flakes[fid].regions.append(r.label)
            region_flake[r.label] = fid
    return flakes, lab, region_flake


def focus_width_um(rgb: np.ndarray, fl: FlakeObj, work_scale: float, pixel_um: float,
                   substrate_rgb: np.ndarray) -> float:
    """Edge width of the flake outline measured on full-resolution pixels:
    contrast step across the boundary divided by the steepest gradient there
    (robust 90th percentile).  ~1-2 um for a focused 6.3x image; defocused
    edges are several um wide."""
    s = 1.0 / work_scale
    y0, x0 = int(fl.slices[0].start * s), int(fl.slices[1].start * s)
    h, w = int(fl.mask.shape[0] * s), int(fl.mask.shape[1] * s)
    pad = 12
    ya, xa = max(y0 - pad, 0), max(x0 - pad, 0)
    yb, xb = min(y0 + h + pad, rgb.shape[0]), min(x0 + w + pad, rgb.shape[1])
    crop = rgb[ya:yb, xa:xb].astype(np.float32) / np.maximum(np.asarray(substrate_rgb, np.float32), 1)
    M = np.zeros(crop.shape[:2], np.uint8)
    mm = cv2.resize(fl.mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
    M[y0 - ya:y0 - ya + h, x0 - xa:x0 - xa + w] = mm[:M.shape[0] - (y0 - ya), :M.shape[1] - (x0 - xa)]
    k = np.ones((3, 3), np.uint8)
    band = cv2.dilate(M, k, iterations=3).astype(bool) & ~cv2.erode(M, k, iterations=3).astype(bool)
    inner = cv2.erode(M, k, iterations=4).astype(bool)
    outer = cv2.dilate(M, k, iterations=8).astype(bool) & ~cv2.dilate(M, k, iterations=5).astype(bool)
    if band.sum() < 20 or inner.sum() < 10 or outer.sum() < 10:
        return float("nan")
    g = np.zeros(crop.shape[:2], np.float32)
    for c in range(3):
        gx = cv2.Sobel(crop[..., c], cv2.CV_32F, 1, 0, ksize=3) / 8
        gy = cv2.Sobel(crop[..., c], cv2.CV_32F, 0, 1, ksize=3) / 8
        g += gx * gx + gy * gy
    g = np.sqrt(g)
    step = float(np.linalg.norm(np.median(crop[inner], axis=0) - np.median(crop[outer], axis=0)))
    if step < 0.03:
        return float("nan")
    gp = float(np.percentile(g[band], 90))
    return step / max(gp, 1e-6) * pixel_um


def crowding(fl: FlakeObj, fm_lab: np.ndarray, px_um: float, r0_um=5.0, r1_um=30.0) -> float:
    """Fraction of the ring r0..r1 around the flake covered by other material."""
    H, W = fm_lab.shape
    r1 = int(np.ceil(r1_um / px_um))
    r0 = max(1, int(round(r0_um / px_um)))
    sl = (slice(max(fl.slices[0].start - r1, 0), min(fl.slices[0].stop + r1, H)),
          slice(max(fl.slices[1].start - r1, 0), min(fl.slices[1].stop + r1, W)))
    m = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.uint8)
    oy, ox = fl.slices[0].start - sl[0].start, fl.slices[1].start - sl[1].start
    m[oy:oy + fl.mask.shape[0], ox:ox + fl.mask.shape[1]] = fl.mask
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    outer = cv2.dilate(m, k, iterations=r1).astype(bool)
    inner = cv2.dilate(m, k, iterations=r0).astype(bool)
    ring = outer & ~inner
    if not ring.any():
        return 0.0
    other = (fm_lab[sl] > 0) & (fm_lab[sl] != fl.fid)
    return float(other[ring].mean())


# (2026-11-04, Avram: "it should count each area of different flake separately, the fact that they are all connected is
# not important": BN_16 20261103_4 flake 356, a 3.1 nm area touching a 66 nm one, was one flake "+1") a connected flake
# whose terraces are of very different thickness is several flakes: terraces sorted by thickness stay together while
# each is less than SPLIT_RATIO x the next thinner one (steps of one flake: 74 / 78 nm, 41 / 68 nm); the user chose
# "one at least twice the other" over every level or >30 %
SPLIT_RATIO = 2.0


def thickness_groups(ts, ratio=SPLIT_RATIO):
    """Groups (lists of indices into ts) of thicknesses that chain within ratio of each other (nm; 1 nm floor)."""
    order = sorted(range(len(ts)), key=lambda i: ts[i])
    groups = []
    for i in order:
        if groups and max(ts[i], 1.0) < ratio * max(ts[groups[-1][-1]], 1.0):
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def split_by_thickness(flakes, lab, region_flake, regions, thickness, px_um, work_scale, min_area_um2=50.0,
                       ratio=SPLIT_RATIO):
    """Flakes (build's) whose regions fall in more than one thickness group (thickness_groups) split into one flake per
    group: each flake pixel goes to the group of the nearest region pixel.  A group whose regions
    are smaller than min_area_um2 in all stays with the largest group.  thickness: {region label: nm}.  flakes, lab and
    region_flake are changed in place; new flakes are numbered after the largest label.  Returns the number of flakes
    split."""
    by_label = {r.label: r for r in regions}
    nxt = int(lab.max()) + 1
    n_split = 0
    for fid in list(flakes):
        fl = flakes[fid]
        rl = [x for x in fl.regions if x in by_label and thickness.get(x) is not None and np.isfinite(thickness[x])]
        if len(rl) < 2:
            continue
        groups = thickness_groups([float(thickness[x]) for x in rl], ratio)
        if len(groups) < 2:
            continue
        area = [sum(float(by_label[rl[i]].mask.sum()) for i in g) * px_um ** 2 for g in groups]
        big = int(np.argmax(area))
        gid = {}
        for k, g in enumerate(groups):
            for i in g:
                gid[rl[i]] = k if area[k] >= min_area_um2 else big
        if len(set(gid.values())) < 2:
            continue
        sl, m = fl.slices, fl.mask
        seed = np.zeros(m.shape, np.int32)                  # group + 1 at the pixels of its regions
        for x, k in gid.items():
            r = by_label[x]
            ys, xs = np.nonzero(r.mask)
            yy, xx = ys + r.slices[0].start - sl[0].start, xs + r.slices[1].start - sl[1].start
            ok = (yy >= 0) & (yy < m.shape[0]) & (xx >= 0) & (xx < m.shape[1])
            seed[yy[ok], xx[ok]] = k + 1
        seed[~m] = 0
        if not seed.any():
            continue
        _, (iy, ix) = ndimage.distance_transform_edt(seed == 0, return_indices=True)
        grp = np.where(m, seed[iy, ix], 0)
        # one flake per group, its pieces together even where they do not touch (terraces of one flake on both sides of
        # a thick ridge stay one flake)
        parts = [(k, grp == k + 1) for k in sorted(set(gid.values()))]
        # the part holding most of the largest group keeps the flake's number
        keep = max((p for p in parts if p[0] == big), key=lambda p: int(p[1].sum()))
        regs_of = {}
        for x in fl.regions:
            r = by_label.get(x)
            if r is None:
                continue
            cy = int(round(np.nonzero(r.mask)[0].mean())) + r.slices[0].start - sl[0].start
            cx = int(round(np.nonzero(r.mask)[1].mean())) + r.slices[1].start - sl[1].start
            # (a region goes to the part that holds most of its pixels; its centre if it lies outside the mask)
            best, bn = None, -1
            ys, xs = np.nonzero(r.mask)
            yy, xx = ys + r.slices[0].start - sl[0].start, xs + r.slices[1].start - sl[1].start
            ok = (yy >= 0) & (yy < m.shape[0]) & (xx >= 0) & (xx < m.shape[1])
            for j, (_, pm) in enumerate(parts):
                n_ = int(pm[yy[ok], xx[ok]].sum())
                if n_ > bn:
                    best, bn = j, n_
            regs_of.setdefault(best, []).append(x)
        new_ids = []
        for j, (k, pm) in enumerate(parts):
            if not regs_of.get(j):                          # (edge pixels only: they stay with the kept part)
                keep[1][pm] = True
        for j, (k, pm) in enumerate(parts):
            if not regs_of.get(j):
                continue
            if pm is keep[1]:
                nid = fid
            else:
                nid = nxt
                nxt += 1
                new_ids.append(nid)
            ys, xs = np.nonzero(pm)
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            psl = (slice(sl[0].start + y0, sl[0].start + y1), slice(sl[1].start + x0, sl[1].start + x1))
            pmask = pm[y0:y1, x0:x1]
            sub = lab[psl]
            sub[pmask] = nid
            fo = _flake_obj(nid, psl, pmask, px_um, work_scale)
            fo.regions = list(regs_of[j])
            flakes[nid] = fo
            for x in fo.regions:
                region_flake[x] = nid
        if new_ids:
            n_split += 1
    return n_split
