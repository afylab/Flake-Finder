"""MP4 movies of the coordinate check's and the remeasure's passes (2026-11-03): one frame per flake, in the order the
pass visited them, showing how far the flake was found from where the pass before put it (A1: from its A0 position,
where its 100x picture was taken, or where the remeasure's 10x find put it; A2 from A1, ...).

Each frame: the offset vector (grey: the flakes before, blue diamond: the median so far, green circle: 5 um), where the
flakes are on the chip (colour: |offset|) and dx, dy, |offset| against the visit number.  Drawn with OpenCV only (the
microscope PC has no matplotlib); H.264 ("avc1") when this OpenCV can write it, else MPEG-4 ("mp4v", plays in VLC and
QuickTime).

    make_movies(folder, label, flakes, ref_name="initial 100x", alternate=True, log=print)

flakes: in pass A1's visiting order, each {name, ref: (x, y) stage um (A0), A: [(x, y) or None per pass]} (a pass cut
short: shorter A lists); alternate: the passes go back and forth (A2 visits in the reverse order, A3 as A1, ...).
Written: <folder>/<label>_A1_vs_A0.mp4, <label>_A2_vs_A1.mp4, ...  Returns the paths written."""
from pathlib import Path

import numpy as np

W, H = 1280, 720
WHITE, GREY, LGREY, DARK = (255, 255, 255), (160, 160, 160), (225, 225, 225), (40, 35, 31)
RED, GREEN, BLUE, ORANGE = (34, 34, 207), (55, 127, 26), (218, 105, 9), (0, 135, 191)
FONT = 0                                               # (cv2.FONT_HERSHEY_SIMPLEX)
TOL_UM = 5.0


def _text(img, s, xy, scale=0.5, col=DARK, th=1):
    import cv2
    cv2.putText(img, s, (int(xy[0]), int(xy[1])), FONT, scale, col, th, cv2.LINE_AA)


def _writer(path, fps):
    import cv2
    for fc in ("avc1", "mp4v"):
        try:
            vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*fc), fps, (W, H))
        except Exception:
            continue
        if vw.isOpened():
            return vw, fc
        vw.release()
    return None, None


def _nice(v):
    p = 10 ** np.floor(np.log10(max(v, 1e-9)))
    return next(m * p for m in (1, 2, 5, 10) if m * p >= v)


def visits(flakes, k, alternate=True):
    """Pass k's visits in its order: [(name, ref position = pass k-1's (A0 for k = 1), position found)], the flakes
    found in both; also how many it visited and how many of them were not found (or not in the pass before)."""
    order = flakes if (k % 2 or not alternate) else flakes[::-1]
    out, n_vis, n_miss = [], 0, 0
    for f in order:
        A = f.get("A") or []
        if len(A) < k:                                 # (not visited: the pass was cut short)
            continue
        n_vis += 1
        a = A[k - 1]
        r = f.get("ref") if k == 1 else (A[k - 2] if len(A) >= k - 1 else None)
        if a is None or r is None:
            n_miss += 1
            continue
        out.append((f.get("name", ""), np.asarray(r, float), np.asarray(a, float)))
    return out, n_vis, n_miss


def movie(path, title, rows, n_total, n_miss, ref_name, cur_name, fps=None):
    """One movie: rows = [(name, ref, found)] in visiting order.  Returns the path, or None (nothing to show / no
    codec)."""
    import cv2
    if not rows:
        return None
    P = np.array([r[1] for r in rows])
    d = np.array([r[2] - r[1] for r in rows])
    m = np.hypot(*d.T)
    n = len(rows)
    lim = float(max(6.0, np.ceil(np.percentile(m, 99.5) * 1.15)))
    fps = fps or float(min(30.0, max(8.0, n / 60.0)))   # (at most about a minute)
    vw, fc = _writer(path, fps)
    if vw is None:
        return None
    # the vector plot (left), the chip map (right, top), against the visit number (right, bottom)
    L0, L1, T0 = 70, 610, 128
    sc = (L1 - L0) / (2 * lim)

    def vp(v):
        return (int(round((L0 + L1) / 2 + v[0] * sc)), int(round(T0 + (L1 - L0) / 2 - v[1] * sc)))
    mx0, mx1, my0, my1 = 700, 1250, 128, 395
    lo, hi = P.min(0), P.max(0)
    span = max(float((hi - lo).max()), 1.0)
    ms = min((mx1 - mx0 - 20) / max(hi[0] - lo[0], span * 0.05), (my1 - my0 - 20) / max(hi[1] - lo[1], span * 0.05))
    mc = (lo + hi) / 2

    def mp(p):
        return (int(round((mx0 + mx1) / 2 + (p[0] - mc[0]) * ms)), int(round((my0 + my1) / 2 - (p[1] - mc[1]) * ms)))
    cmax = max(TOL_UM, lim * 0.8)
    cmap = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(-1, 1), cv2.COLORMAP_VIRIDIS)[:, 0]

    def ccol(v):
        return tuple(int(c) for c in cmap[int(np.clip(v / cmax, 0, 1) * 255)])
    tx0, tx1, ty0, ty1 = 700, 1250, 455, 668

    def tp(i, v):
        return (int(round(tx0 + (i + 1) / (n + 1) * (tx1 - tx0))), int(round((ty0 + ty1) / 2 - v / lim * (ty1 - ty0) / 2)))
    # the parts that do not change
    base = np.full((H, W, 3), 255, np.uint8)
    _text(base, f"{title}:  {cur_name} - {ref_name} position, flake by flake ({cur_name} visiting order)", (20, 32), 0.7, DARK, 2)
    g = _nice(lim / 4)
    for v in np.arange(-np.floor(lim / g) * g, lim + 1e-9, g):
        cv2.line(base, vp((v, -lim)), vp((v, lim)), LGREY, 1)
        cv2.line(base, vp((-lim, v)), vp((lim, v)), LGREY, 1)
        _text(base, f"{v:g}", (vp((v, -lim))[0] - 8, L1 - L0 + T0 + 18), 0.4, GREY)
        _text(base, f"{v:g}", (L0 - 40, vp((-lim, v))[1] + 4), 0.4, GREY)
    cv2.rectangle(base, vp((-lim, lim)), vp((lim, -lim)), GREY, 1)
    cv2.circle(base, vp((0, 0)), int(round(TOL_UM * sc)), GREEN, 1, cv2.LINE_AA)
    _text(base, f"{TOL_UM:g} um", (vp((TOL_UM * 0.72, TOL_UM * 0.72))[0] + 4, vp((TOL_UM * 0.72, TOL_UM * 0.72))[1]), 0.45, GREEN)
    cv2.drawMarker(base, vp((0, 0)), DARK, cv2.MARKER_CROSS, 14, 1)
    _text(base, f"offset ({cur_name} - {ref_name}, um); grey: the flakes before", (L0, T0 - 10), 0.5)
    _text(base, "dx (um)", ((L0 + L1) // 2 - 25, L1 - L0 + T0 + 38), 0.45, GREY)
    _text(base, "dy", (L0 - 55, T0 + (L1 - L0) // 2), 0.45, GREY)
    cv2.rectangle(base, (mx0, my0), (mx1, my1), LGREY, 1)
    _text(base, f"where the flakes are (colour: |offset|, 0 - {cmax:.0f} um)", (mx0, my0 - 10), 0.5)
    for p in P:
        cv2.circle(base, mp(p), 2, LGREY, -1)
    cv2.rectangle(base, (tx0, ty0), (tx1, ty1), LGREY, 1)
    cv2.line(base, (tx0, tp(0, 0)[1]), (tx1, tp(0, 0)[1]), GREY, 1)
    for v in (TOL_UM, -TOL_UM):
        if abs(v) < lim:
            cv2.line(base, (tx0, tp(0, v)[1]), (tx1, tp(0, v)[1]), GREEN, 1)
    _text(base, "against the visit number:", (tx0, ty0 - 10), 0.5)
    _text(base, "dx", (tx0 + 210, ty0 - 10), 0.5, BLUE, 2)
    _text(base, "dy", (tx0 + 245, ty0 - 10), 0.5, ORANGE, 2)
    _text(base, "|offset|", (tx0 + 280, ty0 - 10), 0.5, RED, 2)
    _text(base, f"+-{lim:g} um", (tx1 - 70, ty0 - 10), 0.45, GREY)
    left = f"   ({n_miss} not found in both)" if n_miss else ""
    for k in range(n):
        img = base.copy()
        nm = rows[k][0]
        _text(img, f"{nm}   visit {k + 1} of {n}   offset ({d[k, 0]:+.2f}, {d[k, 1]:+.2f}) um,  |offset| {m[k]:.2f} um{left}",
              (20, 64), 0.55, RED if m[k] > TOL_UM else DARK, 1)
        ok = int((m[:k + 1] <= TOL_UM).sum())
        _text(img, f"so far: {ok} of {k + 1} within {TOL_UM:g} um", (20, 88), 0.5, GREY)
        for j in range(k):
            cv2.circle(img, vp(d[j]), 3, GREY, -1, cv2.LINE_AA)
        med = np.median(d[:k + 1], 0)
        cv2.arrowedLine(img, vp((0, 0)), vp(d[k]), RED, 3, cv2.LINE_AA, tipLength=min(0.3, 18 / max(1.0, m[k] * sc)))
        cv2.drawMarker(img, vp(med), BLUE, cv2.MARKER_DIAMOND, 14, 2)
        _text(img, f"median so far ({med[0]:+.2f}, {med[1]:+.2f}) um", (L0 + 8, L1 - L0 + T0 - 10), 0.5, BLUE)
        for j in range(k + 1):
            if j:
                cv2.line(img, mp(P[j - 1]), mp(P[j]), LGREY, 1)
        for j in range(k + 1):
            cv2.circle(img, mp(P[j]), 4, ccol(m[j]), -1, cv2.LINE_AA)
        cv2.circle(img, mp(P[k]), 10, RED, 2, cv2.LINE_AA)
        if k:
            for col, ys in ((BLUE, d[:k + 1, 0]), (ORANGE, d[:k + 1, 1]), (RED, m[:k + 1])):
                pts = np.array([tp(i, float(np.clip(y, -lim, lim))) for i, y in enumerate(ys)], np.int32)
                cv2.polylines(img, [pts], False, col, 1, cv2.LINE_AA)
        frames = 1 if k < n - 1 else int(fps * 3)        # (the last frame held 3 s)
        for _ in range(frames):
            vw.write(img)
    vw.release()
    return Path(path) if Path(path).is_file() and Path(path).stat().st_size > 0 else None


def make_movies(folder, label, flakes, ref_name="A0", alternate=True, log=print, title=None):
    """Every pass's movie (see the module's doc).  Never raises: a movie not made is logged."""
    out = []
    try:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        n_pass = max((len(f.get("A") or []) for f in flakes), default=0)
        n_all = len(flakes)
        for k in range(1, n_pass + 1):
            rows, n_vis, n_miss = visits(flakes, k, alternate)
            ref = ref_name if k == 1 else f"A{k - 1}"
            p = folder / f"{label}_A{k}_vs_{'A0' if k == 1 else f'A{k - 1}'}.mp4"
            t = (title or label) + (f" (pass stopped after {n_vis} of {n_all})" if n_vis < n_all else "")
            r = movie(p, t, rows, n_vis, n_miss, ref, f"A{k}")
            if r:
                out.append(r)
                m = np.hypot(*np.array([x[2] - x[1] for x in rows]).T)
                log(f"  movie: {r.name} ({len(rows)} flakes; |offset| median {np.median(m):.2f} um, max {m.max():.2f} um)")
            elif rows:
                log(f"  (movie A{k} not made: this OpenCV writes no MP4)")
    except Exception as e:
        log(f"  (movies not made: {type(e).__name__}: {e})")
    return out
