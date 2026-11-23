"""The 10x mosaic in the colours of the 100x objective (2026-11-23).

A flake's colour is thin-film interference in the stack air | flake | SiO2 | Si, and it depends on the angles of light
the objective takes in: the 10x (NA 0.3) sees nearly normal incidence, the 100x (NA 0.9) averages out to ~64 degrees,
where the light's path through the films is shorter (cos theta) and s / p differ.  So the same flake has a different
colour at 100x (BN: 10x orange is cyan, green or yellow at 100x, by thickness; 10x yellow is blue).  No per-channel gain
or colour matrix can map one onto the other: the two colours are tied only through the flake's thickness.  The one
transform consistent with the optics is therefore

    10x colour  ->  thickness (the 10x thin-film model, flakeid.optics, the profile the analysis reads 10x with)
                ->  the 100x model's colour at that thickness (flakeid.thick100.model100, what the 100x thickness is
                    read with, at the run's oxide + the 100x shift)

done per pixel as a gain per channel: out = pixel x R100(t) / R10(t) (R = reflectance relative to the substrate).  A
pixel on the model curve becomes the 100x model colour; the substrate (t = 0) keeps gain 1; what is not on the curve
(dirt, tape, shadows; far from every thickness) keeps its 10x colour (the gain fades to 1 with its distance to the
curve).  The result is then given flakeid.look's look (the 100x pictures' substrate colour and shoulder), as the 100x
pictures are.  Only the displayed copies change (the viewer's tiles/look, summary.jpg): the analysis reads the linear
data and tiles/image.  The original colours stay as tiles/look_orig (index_10x_original_colors.html).

Limits: where two thicknesses have the same 10x colour (hBN ~20 and ~150 nm), the pixel takes the nearer point of the
curve; the 100x colour of the other branch would differ.
"""
from __future__ import annotations

import numpy as np

from .look import CANVAS_SUBSTRATE, look

Q = 160                         # the look-up table: levels per channel, on the log of the reflectance / substrate
LOG_LO, LOG_HI = np.log(0.05), np.log(8.0)
STEP_NM = 0.5
R_NEAR, R_FAR = 0.15, 0.40      # distance to the 10x curve (log of reflectance / substrate, i.e. relative: a bright flake
                                # 10 % off the model is as near as a faint one 10 % off): gain in full below, none above
MEDIAN_PX = 5                   # the thickness map's median filter (camera noise; keeps flake edges)
MEDIAN_PX_CANVAS = 9            # ... on the 8-bit canvas: where R and G are clipped two thicknesses read alike, and the
                                # pixels of one terrace flip between them
OXIDE_SHIFT_100X = {"hbn": 9.0}  # as flakeid.thick100.OXIDE_SHIFT_DEFAULT (imported there when available)


def profile10(material):
    """The 10x profile the analysis reads this material with (flakeid.pipeline.find_flakes, RAW16 data)."""
    return "bx51_xc10_mm_raw16_graphite" if str(material).lower() in ("graphite", "graphene") else "bx51_xc10_mm_raw16"


class Lens:
    """10x pixels (reflectance / substrate per channel, linear) -> the same pixels at 100x, in the 100x pictures' look.
    clip: the largest reflectance / substrate the input records (the 8-bit canvas: 255 / CANVAS_SUBSTRATE), None =
    linear data with headroom."""

    def __init__(self, material, oxide10_nm, oxide100_nm=None, clip=None):
        from scipy.spatial import cKDTree
        from .optics import resolve_material
        from .thickness import SEARCH_RANGE_NM, ThicknessEstimator, load_profile
        from . import thick100
        mat = resolve_material(material)
        if oxide100_nm is None:
            oxide100_nm = float(oxide10_nm) + float(getattr(thick100, "OXIDE_SHIFT_DEFAULT", OXIDE_SHIFT_100X).get(mat, 0.0))
        self.material, self.oxide10, self.oxide100 = mat, float(oxide10_nm), float(oxide100_nm)
        self.median = MEDIAN_PX if clip is None else MEDIAN_PX_CANVAS
        est = ThicknessEstimator(mat, self.oxide10, load_profile(profile10(mat)), step_nm=STEP_NM,
                                 search_range_nm=SEARCH_RANGE_NM.get(mat, (0.0, 200.0)))
        g10 = float(est.camera.gamma)
        t = est.d
        r10 = (1.0 + est.model.contrast(t)) ** g10                            # (N, 3) reflectance / substrate
        m100 = thick100.model100(mat, self.oxide100)
        r100 = np.maximum(1.0 + m100.contrast(t), 1e-6) ** float(m100.camera.gamma)
        self.t, self.r10, self.r100, self.g10 = t, r10, r100, g10
        rc = r10 if clip is None else np.minimum(r10, float(clip))           # the 10x curve as the input records it
        self.gain = (r100 / np.maximum(rc, 1e-6)).astype(np.float32)         # (on the curve: exactly the 100x colour)
        self.gain[0] = 1.0
        self.rc = np.maximum(rc, 1e-6).astype(np.float32)
        self.r100 = self.r100.astype(np.float32)
        self.r100[0] = self.rc[0]                                            # (the substrate stays as it is)
        tree = cKDTree(np.log(np.maximum(rc, 1e-4)))
        v = np.exp(LOG_LO + (np.arange(Q) + 0.5) / Q * (LOG_HI - LOG_LO))
        if clip is not None:
            v = np.minimum(v, float(clip))
        grid = np.stack(np.meshgrid(v, v, v, indexing="ij"), -1).reshape(-1, 3)
        dist, idx = tree.query(np.log(grid))
        self.t_lut = idx.astype(np.uint16).reshape(Q, Q, Q)
        self.w_lut = np.round(255 * np.clip((R_FAR - dist) / (R_FAR - R_NEAR), 0.0, 1.0)).astype(np.uint8).reshape(Q, Q, Q)

    def gains(self, ratio):
        """(H, W, 3) reflectance / substrate -> (H, W, 3) gain per channel (the 100x / 10x model ratio at each pixel's
        thickness, faded to 1 off the curve), the thickness map median-filtered."""
        i, w = self.thickness_index(ratio)
        wf = (w.astype(np.float32) / 255.0)[..., None]
        return 1.0 + wf * (self.gain[i] - 1.0)

    def thickness_index(self, ratio):
        """(H, W, 3) reflectance / substrate -> (index into self.t, weight 0-255: 255 on the 10x curve, 0 far off it),
        the index map median-filtered."""
        import cv2
        r = np.asarray(ratio, np.float32)
        li = ((np.log(np.maximum(r, 1e-4)) - LOG_LO) * (Q / (LOG_HI - LOG_LO))).astype(np.int32)
        np.clip(li, 0, Q - 1, out=li)
        i, w = self.t_lut[li[..., 0], li[..., 1], li[..., 2]], self.w_lut[li[..., 0], li[..., 1], li[..., 2]]
        k = self.median
        if k and min(i.shape[:2]) >= k:
            if k <= 5:
                i = cv2.medianBlur(np.ascontiguousarray(i), k)
            else:                                   # (OpenCV: 16-bit only up to 5 px)
                from scipy.ndimage import median_filter
                i = median_filter(i, size=k, mode="nearest")
            w = cv2.medianBlur(np.ascontiguousarray(w), k)
        return i, w

    def look_ratio(self, ratio):
        """(H, W, 3) RGB reflectance / substrate (10x) -> 8-bit RGB as the 100x pictures show it (flakeid.look).
        On the curve the pixel becomes the 100x model colour times its own small departure from the 10x model colour,
        that departure median-filtered: a dark channel (graphite's red at 10x: ~7 of 255) multiplied by a large gain
        (x5) would otherwise turn its 8-bit steps into coloured speckle."""
        r = np.asarray(ratio, np.float32)
        i, w = self.thickness_index(r)
        res = r / self.rc[i]
        if min(res.shape[:2]) >= 5:
            import cv2
            res = cv2.medianBlur(np.ascontiguousarray(res, np.float32), 5)
        wf = (w.astype(np.float32) / 255.0)[..., None]
        return look(wf * (self.r100[i] * res) + (1.0 - wf) * r, (1.0, 1.0, 1.0))

    def look_tile(self, img_bgr, canvas_sub=CANVAS_SUBSTRATE):
        """A viewer tile (8-bit BGR canvas, substrate at canvas_sub) -> the same tile in the 100x colours (BGR)."""
        r = np.asarray(img_bgr)[..., ::-1].astype(np.float32) / float(canvas_sub)
        return np.ascontiguousarray(self.look_ratio(r)[..., ::-1])


_CACHE = {}


def lens_for(material, oxide10_nm, oxide100_nm=None, canvas=False):
    """A Lens (cached by material, oxides and input), or None when it cannot be made.  canvas=True: for the 8-bit canvas
    (clipped at 255 / CANVAS_SUBSTRATE), else for linear data."""
    key = (str(material).lower(), round(float(oxide10_nm), 1), None if oxide100_nm is None else round(float(oxide100_nm), 1), bool(canvas))
    if key not in _CACHE:
        try:
            _CACHE[key] = Lens(material, oxide10_nm, oxide100_nm, clip=(255.0 / CANVAS_SUBSTRATE) if canvas else None)
        except Exception:
            _CACHE[key] = None
    return _CACHE[key]


def redo_viewer(vdir, oxide100_nm=None, log=print):
    """An existing viewer folder's tiles/look made again from its tiles/image in the 100x colours (the 8-bit canvas
    path: bright flakes are clipped there, so scans made from now on, rendered from the linear data, look better).
    Its look as it was (the original 10x colours) is kept as tiles/look_orig, shown by index_10x_original_colors.html
    and the page's Original 10x colours button."""
    import json
    import re
    import shutil
    from pathlib import Path
    import cv2
    from .look import look_tile
    from .zoomview import upgrade_page, write_original_page, _write_swap
    vdir = Path(vdir)
    page = vdir / "index.html"
    html = page.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"const D=(\{.*?\});\n", html, re.S)
    D = json.loads(m.group(1))
    if D.get("image_only") or not D.get("oxide"):
        log(f"{vdir}: no oxide (10x image only): left as it is")
        return 0
    L = lens_for(D.get("material") or "hbn", float(D["oxide"]), oxide100_nm, canvas=True)
    if L is None:
        log(f"{vdir}: no 100x model for {D.get('material')}")
        return 0
    info = D.setdefault("info", {})
    look_dir, orig_dir = vdir / "tiles" / "look", vdir / "tiles" / "look_orig"
    if not orig_dir.is_dir():
        if look_dir.is_dir() and (info.get("look") or {}).get("colours") != "100x":
            shutil.move(str(look_dir), str(orig_dir))          # (its look as made by the scan: the original colours)
        else:                                                  # (no look layer, or already the 100x one: from tiles/image)
            for f in sorted((vdir / "tiles" / "image").glob("*/*.jpg")):
                img = cv2.imread(str(f), cv2.IMREAD_COLOR)
                if img is not None:
                    (orig_dir / f.parent.name).mkdir(parents=True, exist_ok=True)
                    cv2.imwrite(str(orig_dir / f.parent.name / f.name), look_tile(img), [cv2.IMWRITE_JPEG_QUALITY, 85])
    n = 0
    for f in sorted((vdir / "tiles" / "image").glob("*/*.jpg")):
        dst = look_dir / f.parent.name / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        img = cv2.imread(str(f), cv2.IMREAD_COLOR)
        if img is None:
            continue
        cv2.imwrite(str(dst), L.look_tile(img), [cv2.IMWRITE_JPEG_QUALITY, 85])
        n += 1
    info["look"] = dict(info.get("look") or info["image"], colours="100x")
    info["look_orig"] = {k: v for k, v in info["look"].items() if k not in ("colours", "dir")}
    info["look"].pop("dir", None)
    new = html[:m.start(1)] + json.dumps(D, separators=(",", ":")) + html[m.end(1):]
    _write_swap(page, new)
    upgrade_page(page)                                          # (the page with the Original 10x colours button)
    write_original_page(vdir)
    log(f"{vdir}: {n} tiles in the 100x colours ({L.material}, 10x oxide {L.oxide10:g} nm, 100x {L.oxide100:g} nm); "
        f"the original colours in tiles/look_orig")
    return n


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Make a viewer's 10x look layer (tiles/look) again, in the colours of the "
                                             "100x objective.  Writes into the viewer folder: use a copy.")
    ap.add_argument("viewer", nargs="+", help="viewer folder(s) (with index.html and tiles/image)")
    ap.add_argument("--oxide100", type=float, default=None, help="the 100x model's oxide (nm); default the 10x one + 9 nm (hBN)")
    a = ap.parse_args(argv)
    for v in a.viewer:
        redo_viewer(v, a.oxide100)


if __name__ == "__main__":
    main()
