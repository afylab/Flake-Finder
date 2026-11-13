"""Rhombohedral graphite screening (Avram, 2026-10-28): graphite on ~285 nm SiO2, exfoliated for rhombohedral (ABC)
multilayers, imaged with the IR camera after the 100x pictures.

What a good flake is (the group's criteria, "Cryogenic shock exfoliation for ultrahigh mobility
rhombohedral graphite nanoelectronics", arXiv:2604.21912, Methods; and the examples in Ludwig/exfoliation/graphite/
LH_G_044_notashedLN2_aligned, flake_areas_LN2_optical.xlsx: 3-18 layers, loops of 100-7000 um2): a uniform, clean
area of at least ~400 um2 (bigger is better: domains of 1000-1500 um2 and more are what cryogenic exfoliation adds), 3
to ~20 layers thick (here up to 25: Avram, 2026-10-29, the blue flakes just past the turn count too), without cracks,
wrinkles or dirt, and not a sliver (one side of 5 um or less).  Thick graphite or bulk attached to such a flake does
not matter (the flake is cut out), so it is not part of the flake's outline or its size.

Thin or thick, and the layer number, from the colour alone (the thin-film model, fitted on 90 nm oxide, does not
describe 285 nm oxide: every flake of LH_G_048 came out "off_model", 14-16 nm): on this oxide the contrast of graphite
follows one path as it gets thicker, measured on the uniform areas of LH_G_048_noAsh_noHeat_MT_1-3 (2026-10-28):
from the substrate the red contrast falls to a turning point at ~22 layers (100x: R -0.47; 10x: R -0.68, where green
and blue have already risen), then the colour turns bluer (still a little past the turn: up to ~26 layers on the path
below), then the orange / white / cream of bulk.  Everything on the path is thin graphite, everything else is thick
or bulk (or dirt, dark shadows, residue).  The layer numbers at the path's points: at 100x the thin-film model's red
contrast at 285 nm as a fraction of its value at the turn (22.5 layers in the model), past the turn the model's rate of
colour change per layer; at 10x fitted to the 100x layer numbers of the same 28 targets of LH_G_048 (rms 0.4 layers;
2026-10-29: before, the 10x path missed the turn, and 10x flakes of 17-22 layers at 100x came out thick).  The layer
numbers are estimates (no AFM on these chips yet; past the turn +-3 layers); thin / thick is not.
"""
from __future__ import annotations

import numpy as np

LAYER_NM = 0.335
MIN_OXIDE_NM = 200.0                 # graphite on thicker oxide than this: rhombohedral screening (90 nm: graphene, gates)
OXIDE_NM = 285.0                     # the standard oxide of rhombohedral chips (the calibration's; the scan program's default)
WINDOW_LAYERS = (3.0, 25.0)          # layer numbers of interest (the paper: 3 to ~20; up to 25: the blue flakes just past
#                                      the turn count too, Avram 2026-10-29; 20 before)
MIN_UNIFORM_UM2 = 400.0              # the paper's smallest uniform area of a candidate flake
MIN_TARGET_UM2 = 300.0               # 10x: smallest clean core of a 100x target (10x cannot see small cracks: some slack)
FILL_CORE_UM2 = 80.0                 # a piece with fewer targets than --min-targets: the best smaller ones fill the list
EDGE_UM = 2.5                        # the clean core: the region less this band along its edge (slivers <= 5 um wide vanish)
SIZE_FULL_UM2 = 20000.0              # the size part of the score reaches 1 here (80 um2: 0, 400: 0.29, 1000: 0.46,
#                                      5000: 0.75, 10000: 0.87): larger flakes rank higher (5000 before 2026-10-28:
#                                      every flake above it tied at 1, and the largest were not first)
SIZE_MIN_UM2 = 80.0                  # (the paper leaves out areas smaller than this)
OUT_OF_WINDOW = 0.2                  # score factor of thin graphite outside WINDOW_LAYERS

# the measured path of thin graphite, (R, G, B) contrast from the substrate past the turn (10x: the viewer canvas of
# the three pieces, uniform pixels; 100x: the colour levels of the 28 pictures of the run), and the layer number at each
# point (between points: linear).  100x up to the turn: the thin-film model's (bx51_xc10_mm_raw16_graphite, 285 nm) red
# contrast as a fraction of its value at the turn (16-20 layers: points on the straight line to the turn); past it the
# model's colour change per layer (25.2: MT_1 F004, 26.7: MT_2 F004 / F007).  10x: fitted to the 100x layer numbers of
# the same targets (pastturn/fit.py, 2026-10-29).
PATH = {
    "10x": np.array([[0.0, 0.0, 0.0], [-0.12, -0.05, 0.0], [-0.22, -0.09, 0.03], [-0.30, -0.13, 0.02],
                     [-0.38, -0.15, 0.01], [-0.46, -0.21, 0.0], [-0.54, -0.23, 0.02], [-0.62, -0.23, 0.02],
                     [-0.70, -0.245, 0.035], [-0.735, -0.215, 0.065], [-0.745, -0.155, 0.115], [-0.709, -0.101, 0.127],
                     [-0.684, -0.051, 0.139], [-0.658, 0.0, 0.177], [-0.633, 0.04, 0.19]]),
    "100x": np.array([[0.0, 0.0, 0.0], [-0.10, -0.13, -0.04], [-0.19, -0.25, -0.09], [-0.23, -0.30, -0.10],
                      [-0.30, -0.37, -0.11], [-0.33, -0.40, -0.12], [-0.42, -0.46, -0.11], [-0.442, -0.447, -0.075],
                      [-0.457, -0.438, -0.051], [-0.466, -0.432, -0.036], [-0.47, -0.43, -0.03], [-0.45, -0.38, 0.03],
                      [-0.46, -0.33, 0.05]]),
}
PATH_LAYERS = {
    "10x": np.array([0.0, 1.3, 2.5, 3.5, 4.3, 6.3, 7.7, 9.0, 13.5, 14.2, 16.8, 20.3, 22.5, 25.2, 26.4]),
    "100x": np.array([0.0, 2.1, 4.3, 5.5, 7.8, 9.0, 14.0, 16.0, 18.0, 20.0, 22.5, 25.2, 26.7]),
}
TOL = {"10x": 0.07, "100x": 0.06}    # largest distance from the path (contrast units) of thin graphite

# The paths are for the calibration wafers (LH_G_048: "285 nm", 300 nm in the thin-film model).  A wafer whose oxide is
# a little thinner or thicker (LH_G_049, 2026-10-29: ~15 nm thinner; substrate R/G 0.79 instead of 0.50, no flake found)
# shows graphite in other colours: the oxide offset is estimated from the substrate's colour (its R/G and B/G against the
# calibration wafers', through the thin-film model) and the paths are moved by the model's change of the graphite colours
# at that offset (oxide_shift_nm; use_oxide_shift sets it for this process: the analysis, the 100x export, the designer).
CAL_SUBSTRATE_RG_BG = (0.504, 0.937)  # the analysis's substrate level R/G, B/G on the calibration wafers (LH_G_048 runs)
CAL_MODEL_OXIDE_NM = 300.0           # their oxide in the thin-film model
MAX_OXIDE_SHIFT_NM = 40.0            # a larger offset (or a colour no oxide explains): not estimated (another oxide or light)
MAX_OXIDE_MISFIT = 0.004             # sum of the squared log errors of R/G and B/G at the best offset
_NA = {"10x": None, "100x": 0.9}     # (10x: the profile's NA)
_shift = 0.0


def use_oxide_shift(nm):
    """The oxide offset (nm, thin-film model) the colour paths are moved for, in this process (0: the calibration wafers)."""
    global _shift
    try:
        _shift = float(nm or 0.0)
    except (TypeError, ValueError):
        _shift = 0.0


def _model(ox, na):
    from .thickness import load_profile, camera_from_profile
    from .optics import ContrastModel
    p = load_profile("bx51_xc10_mm_raw16_graphite")
    return ContrastModel("graphite", ox, na=na or float(p.get("na", 0.36)), camera=camera_from_profile(p))


_cache = {}


def _path(mag):
    """The colour path of mag for the current oxide offset (the measured one moved by the model's change)."""
    sh = round(_shift * 2.0) / 2.0
    if abs(sh) < 0.25:
        return PATH[mag]
    key = (mag, sh)
    if key not in _cache:
        L = np.arange(0.0, 30.01, 0.5)
        a = _model(CAL_MODEL_OXIDE_NM, _NA[mag]).contrast(L * LAYER_NM)
        b = _model(CAL_MODEL_OXIDE_NM + sh, _NA[mag]).contrast(L * LAYER_NM)
        d = np.array([np.interp(PATH_LAYERS[mag], L, (b - a)[:, k]) for k in range(3)]).T
        _cache[key] = PATH[mag] + d
    return _cache[key]


def _substrate_rgb(ox):
    """Substrate (bare SiO2 on Si) signal per camera channel at oxide ox (thin-film model, unnormalised: only ratios)."""
    from .optics import blackbody, gaussian, _reflectance
    m = _model(ox, None)
    cam, wl = m.camera, m.wl
    w = (np.stack([gaussian(wl, c, f) for c, f in zip(cam.centers_nm, cam.fwhm_nm)]) * blackbody(wl, cam.lamp_temp_k)
         / (1.0 + np.exp((wl - cam.ir_cut_nm) / 8.0)))
    R = _reflectance([m._n_ox], [ox], m._n_si, wl, m._cos)
    return w @ (R * m._aw).sum(axis=0)


def oxide_shift_from_substrate(rgb):
    """(offset nm, misfit): the oxide offset from the calibration wafers that explains a substrate level rgb (any units:
    only R/G and B/G count), or (None, misfit) if none within MAX_OXIDE_SHIFT_NM explains it well (another oxide, or a
    changed light)."""
    rgb = np.asarray(rgb, float)
    if rgb.shape != (3,) or not np.all(rgb > 0):
        return None, float("nan")
    meas = np.log([rgb[0] / rgb[1] / CAL_SUBSTRATE_RG_BG[0], rgb[2] / rgb[1] / CAL_SUBSTRATE_RG_BG[1]])
    s0 = _substrate_rgb(CAL_MODEL_OXIDE_NM)
    best = (np.inf, 0.0)
    for d in np.arange(-MAX_OXIDE_SHIFT_NM, MAX_OXIDE_SHIFT_NM + 0.01, 0.5):
        s = _substrate_rgb(CAL_MODEL_OXIDE_NM + d)
        mod = np.log([(s[0] / s[1]) / (s0[0] / s0[1]), (s[2] / s[1]) / (s0[2] / s0[1])])
        e = float(((mod - meas) ** 2).sum())
        if e < best[0]:
            best = (e, float(d))
    if best[0] > MAX_OXIDE_MISFIT or abs(best[1]) >= MAX_OXIDE_SHIFT_NM:
        return None, best[0]
    return best[1], best[0]


def applies(material, oxide_nm, setting="auto"):
    """Rhombohedral screening for this piece?  setting: 'auto' (graphite on >= MIN_OXIDE_NM oxide), 'on', 'off'."""
    if str(material or "").lower() not in ("graphite", "graphene"):
        return False
    if setting in (True, "on", "yes"):
        return True
    if setting in (False, "off", "no"):
        return False
    try:
        return float(oxide_nm) >= MIN_OXIDE_NM
    except (TypeError, ValueError):
        return False


def _project(c, path, layers):
    """Distance of contrast vectors c (..., 3) from the path and the layer number of the nearest path point."""
    c = np.asarray(c, np.float32)
    best = np.full(c.shape[:-1], np.inf, np.float32)
    n = np.zeros(c.shape[:-1], np.float32)
    for a, b, la, lb in zip(path[:-1], path[1:], layers[:-1], layers[1:]):
        a, b = a.astype(np.float32), b.astype(np.float32)
        d = b - a
        t = np.clip(((c - a) @ d) / float(d @ d), 0.0, 1.0)
        p = a + t[..., None] * d
        dist = np.sqrt(((c - p) ** 2).sum(-1))
        sel = dist < best
        best = np.where(sel, dist, best)
        n = np.where(sel, la + t * (lb - la), n)
    return best, n


def layers_of(c, mag="10x"):
    """(thin, layers) of contrast vectors c (..., 3): thin = on the thin-graphite path; layers (float, estimate) where
    thin, nan elsewhere."""
    dist, n = _project(c, _path(mag), PATH_LAYERS[mag])
    thin = dist <= TOL[mag]
    return thin, np.where(thin, n, np.nan)


def thin_mask(contrast, mag="10x"):
    """Pixels (H, W, 3 contrast) of thin graphite (substrate-coloured pixels included: the flake mask decides what
    is material)."""
    return layers_of(contrast, mag)[0]


def region_layers(c, mag="10x"):
    """Layer number (float) of one region's contrast, or None if it is not thin graphite."""
    thin, n = layers_of(np.asarray(c, float)[:3], mag)
    return float(n) if bool(thin) else None


def in_window(n):
    return n is not None and n == n and WINDOW_LAYERS[0] <= n <= WINDOW_LAYERS[1]


def core_area_um2(mask, px_um, edge_um=EDGE_UM):
    """Area of a region's clean core: the region less a band of edge_um along its edge (a region nowhere wider than
    2 edge_um has none)."""
    import cv2
    m = np.pad(np.asarray(mask, np.uint8), 1)
    d = cv2.distanceTransform(m, cv2.DIST_L2, 5)[1:-1, 1:-1]
    return float((d * px_um > edge_um).sum()) * px_um ** 2


def size_part(area_um2):
    a = max(float(area_um2), 0.0)
    if a <= SIZE_MIN_UM2:
        return 0.0
    return float(min(1.0, np.log(a / SIZE_MIN_UM2) / np.log(SIZE_FULL_UM2 / SIZE_MIN_UM2)))


def largest_core(m, px_um, edge_um=EDGE_UM):
    """(area um2, mask) of the largest connected clean core of a mask: the pixels more than edge_um inside it, then the
    largest connected piece; the mask returned is that piece grown back by edge_um (inside m)."""
    import cv2
    m8 = np.pad(np.asarray(m, np.uint8), 1)
    d = cv2.distanceTransform(m8, cv2.DIST_L2, 5)[1:-1, 1:-1]
    core = (d * px_um > edge_um).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
    if n < 2:
        return 0.0, np.zeros(np.shape(m), bool)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    r = max(1, int(round(edge_um / px_um)))
    grown = cv2.dilate((lab == k).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    return float(st[k, cv2.CC_STAT_AREA]) * px_um ** 2, grown.astype(bool) & np.asarray(m, bool)


def score10(core_um2, n_layers, uniformity=1.0, focus_um=float("nan"), flags=(), fill=1.0, flake_core_um2=float("nan")):
    """10x score of a thin terrace (0-1): the size of the clean pixels of the right colour: the larger of its own core
    times fill (the share of its full-resolution pixels of its colour) and its flake's largest connected clean core of
    3-25 layer colour (flake_core_um2: a large flake whose thickness varies a little counts whole); times OUT_OF_WINDOW
    outside 3-25 layers, less for an uneven colour; 0 on the chip edge."""
    if "chip_edge" in flags or "no_signal" in flags:
        return 0.0
    f = min(max(float(fill), 0.0), 1.0) if fill == fill else 1.0
    a = core_um2 * f
    if flake_core_um2 == flake_core_um2 and in_window(n_layers):
        a = max(a, float(flake_core_um2))
    s = size_part(a)
    if not in_window(n_layers):
        s *= OUT_OF_WINDOW
    u = float(uniformity) if uniformity == uniformity else 1.0
    s *= 0.6 + 0.4 * min(max((u - 0.6) / 0.35, 0.0), 1.0)
    # (no penalty for wide or blurred edges: large flakes often have a graded rim at 10x, and the best ones of LH_G_048
    # lost 20 % to it; the 100x picture judges the flake)
    return round(float(s), 4)


def score100(clean_um2, n_layers):
    """100x score (0-1): the size of the largest clean area of the terrace (flakeid.screen100.clean_score: away from
    the edge, steps, debris, wrinkles, bubbles), times OUT_OF_WINDOW outside 3-25 layers; 0 if it is not thin."""
    if n_layers is None or n_layers != n_layers:
        return 0.0
    s = size_part(clean_um2)
    return round(float(s * (1.0 if in_window(n_layers) else OUT_OF_WINDOW)), 4)


def tier100(clean_um2, n_layers):
    """keep / review / reject of a 100x picture: keep a clean area of MIN_UNIFORM_UM2 or more of 3-25 layer graphite,
    review a smaller one of at least 150 um2, reject the rest (thick, bulk, out of the window, small)."""
    if not in_window(n_layers):
        return "reject"
    if clean_um2 >= MIN_UNIFORM_UM2:
        return "keep"
    return "review" if clean_um2 >= 150.0 else "reject"


def describe(n_layers):
    return "" if n_layers is None or n_layers != n_layers else f"~{n_layers * LAYER_NM:.1f} nm"


def select(ter_csv, exclude=(), min_core_um2=MIN_TARGET_UM2, log=print):
    """100x target rows (flake-table style dicts, best first) from a live terrace table: per flake its best terrace
    (score10), if its clean core of the right colour (its own or its flake's, score10) is at least min_core_um2 and it is
    3-25 layers; clean_area_um2 = that core (the 100x order: largest first)."""
    import csv

    def f(v, d=float("nan")):
        try:
            x = float(v)
        except (TypeError, ValueError):
            return d
        return x if x == x else d
    with open(ter_csv, newline="") as fh:
        T = list(csv.DictReader(fh))
    best, n_thin, n_big = {}, 0, 0
    for t in T:
        flags = set(filter(None, (t.get("quality") or "").split(";")))
        if flags & set(exclude):
            continue
        n = f(t.get("layers"))
        if not in_window(n):
            continue
        n_thin += 1
        core = max(f(t.get("core_um2"), 0.0), f(t.get("flake_core_um2"), 0.0))
        if not core >= min_core_um2:
            continue
        n_big += 1
        k = t["flake_id"]
        if k not in best or f(t.get("score"), 0.0) > f(best[k].get("score"), 0.0):
            best[k] = t
    rows = []
    for t in sorted(best.values(), key=lambda t: -f(t.get("score"), 0.0)):
        n = f(t.get("layers"))
        rows.append(dict(flake_id=t["flake_id"], terrace_id=t.get("terrace_id"), score=t.get("score"), layers=int(round(n)),
                         best_thickness_nm=round(n * LAYER_NM, 2), best_terrace_d_um=t.get("inscribed_diameter_um"),
                         area_um2=t.get("flake_area_um2"),
                         clean_area_um2=max(f(t.get("core_um2"), 0.0), f(t.get("flake_core_um2"), 0.0)),
                         target_x_px=t["target_x_px"], target_y_px=t["target_y_px"],
                         stage_x_um=t.get("stage_x_um"), stage_y_um=t.get("stage_y_um"), quality=t.get("quality", "")))
    log(f"rhombohedral screening: {len(rows)} flakes with a clean core of >= {min_core_um2:g} um2 at "
        f"{WINDOW_LAYERS[0]:g}-{WINDOW_LAYERS[1]:g} layers ({n_big} such terraces of {n_thin} in the window; the layer "
        f"numbers are estimates from the colour)")
    return rows
