"""The scan program's logs copied to a private GitHub repository by themselves (Avram, 2026-10-28), so problems on the
microscope PC can be read from anywhere (e.g. by Claude Code on the analysis Mac, with gh): log_upload_repo
(afylab/flakeid-logs), one folder per PC and day, a new file per upload: <PC>/<YYYY-MM-DD>/<HHMMSS>_<why>_<log>.txt.

What and when (in a background thread; a failure is one line in the log, never an error):
  - at the program's start: what is new since the last upload in C:/FlakeScans/crash_log.txt (only when it holds a
    crash: "Fatal Python error" / "Windows fatal exception"), flakeid_console_log.txt and mm_startup_log.txt (read
    before Micro-Manager starts it afresh): the previous session's end, also when Python crashed;
  - at the end of every job: the job's own log (<run>_log.txt), and what is new in the three logs above;
  - when a run's background export ends: its analysis_log.txt.
Each file at most LOG_MAX_BYTES (its end).  Tokens that look like GitHub / Slack ones are blanked out first.

The token: log_upload_token_file (C:/FlakeID/github_logs_token.txt) or FLAKEID_LOGS_TOKEN: a fine-grained token with
"Contents: Read and write" on the logs repository only (the update token stays read-only on the program's own one).
Without a token nothing is sent.  What was sent: <local_root>/log_upload_state.json (bytes sent of each log).
"""
from __future__ import annotations

import base64
import json
import os
import re
import socket
import threading
import time
from pathlib import Path

LOG_MAX_BYTES = 3_000_000
CRASH_MARKS = ("Fatal Python error", "Windows fatal exception")
SECRETS = re.compile(r"(ghp_|gho_|ghs_|github_pat_|xox[abprs]-)[A-Za-z0-9_\-]{8,}")
_lock = threading.Lock()                          # (one upload at a time: GitHub refuses two commits made together)


def logs_token(s):
    t = os.environ.get("FLAKEID_LOGS_TOKEN", "").strip()
    f = getattr(s, "log_upload_token_file", "")
    if not t and f:
        try:
            with open(f, encoding="utf-8") as fh:
                t = fh.read().strip()
        except OSError:
            t = ""
    return t


LOGS = {}                                         # log name -> its file, where __main__ put it (else in log_dir)


def log_dir(s):
    return Path(getattr(s, "local_root", "") or "C:/FlakeScans")


def pc_name():
    n = os.environ.get("COMPUTERNAME") or socket.gethostname() or "pc"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", n)


def _state_file(s):
    return log_dir(s) / "log_upload_state.json"


def _read_state(s):
    try:
        return json.loads(_state_file(s).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_state(s, st):
    try:
        _state_file(s).write_text(json.dumps(st, indent=1), encoding="utf-8")
    except OSError:
        pass


def _clip(b):
    """The end of b (bytes) if longer than LOG_MAX_BYTES, as text."""
    head = ""
    if len(b) > LOG_MAX_BYTES:
        head = f"[... the first {len(b) - LOG_MAX_BYTES} bytes left out ...]\n"
        b = b[-LOG_MAX_BYTES:]
    return head + b.decode("utf-8", "replace")


def new_parts(s, names=("crash_log.txt", "flakeid_console_log.txt", "mm_startup_log.txt")):
    """[(name, text, size)] of what is new in the program's own logs since the last upload (a log that is shorter than
    what was sent was started afresh: all of it).  The crash log only when its new part holds a crash."""
    st, out = _read_state(s), []
    for n in names:
        p = Path(LOGS.get(n) or log_dir(s) / n)
        try:
            size = p.stat().st_size
            sent = int(st.get(n, 0))
            if size < sent:
                sent = 0
            if size == sent:
                continue
            with open(p, "rb") as fh:
                fh.seek(sent)
                b = fh.read()
        except (OSError, ValueError):
            continue
        txt = _clip(b)
        if n == "crash_log.txt" and not any(m in txt for m in CRASH_MARKS):
            out.append((n, None, sent + len(b)))       # (only start-up lines: nothing to send, but counted as seen)
            continue
        out.append((n, txt, sent + len(b)))
    return out


def whole(path):
    """(name, text, None) of a whole file (a job's log), or None."""
    try:
        return (Path(path).name, _clip(Path(path).read_bytes()), None)
    except OSError:
        return None


def put(s, tok, path, text, message):
    """Create one file in the logs repository (GitHub's contents API); raises on failure."""
    import urllib.error
    import urllib.parse
    import urllib.request
    from .update import API, _ssl
    url = f"{API}repos/{s.log_upload_repo}/contents/{urllib.parse.quote(path)}"
    body = json.dumps({"message": message, "content": base64.b64encode(text.encode("utf-8")).decode("ascii")}).encode()
    for attempt in range(3):
        rq = urllib.request.Request(url, data=body, method="PUT", headers={
            "Accept": "application/vnd.github+json", "User-Agent": "flakeid-scope-logs", "Authorization": "Bearer " + tok,
            "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(rq, timeout=60, context=_ssl()) as r:
                r.read()
            return
        except urllib.error.HTTPError as e:
            if e.code in (409, 422) and attempt < 2:    # (another commit at the same moment / the name taken: again)
                time.sleep(2.0)
                path = re.sub(r"(\.txt)?$", f"_{attempt + 2}.txt", path, count=1) if e.code == 422 else path
                url = f"{API}repos/{s.log_upload_repo}/contents/{urllib.parse.quote(path)}"
                continue
            raise RuntimeError(f"GitHub answered {e.code} for {s.log_upload_repo}"
                               + (" (the logs token cannot write there: Contents read and write on that repository?)"
                                  if e.code in (401, 403, 404) else "")) from None


def upload(s, why, items, log=print):
    """Send items [(name, text or None, size or None)] as <PC>/<date>/<time>_<why>_<name>; the sizes of the program's
    own logs are recorded once sent.  Returns the number of files sent."""
    if not getattr(s, "log_upload", False) or not getattr(s, "log_upload_repo", ""):
        return 0
    tok = logs_token(s)
    if not tok:
        return 0
    with _lock:
        st, n = _read_state(s), 0
        t = time.localtime()
        tag = re.sub(r"[^A-Za-z0-9._-]+", "_", why).strip("_")[:60] or "log"
        for name, text, size in items:
            if text is not None:
                text = SECRETS.sub(lambda m: m.group(1) + "[removed]", text)
                path = f"{pc_name()}/{time.strftime('%Y-%m-%d', t)}/{time.strftime('%H%M%S', t)}_{tag}_{name}"
                try:
                    put(s, tok, path, text, f"{pc_name()}: {why}: {name}")
                    n += 1
                except Exception as e:
                    log(f"  (logs not copied to GitHub: {e})")
                    break
            if size is not None:
                st[name] = size
                _write_state(s, st)
        if n:
            log(f"  {n} log file(s) copied to github.com/{s.log_upload_repo} ({pc_name()}/{time.strftime('%Y-%m-%d', t)}, {why})")
        return n


def upload_later(s, why, items=None, extra=(), log=print):
    """upload() in a background thread.  items: as new_parts (default: read now); extra: whole files to add."""
    if not getattr(s, "log_upload", False) or not logs_token(s):
        return None
    its = list(new_parts(s) if items is None else items)
    its += [x for x in (whole(p) for p in extra if p) if x is not None]
    if not any(t is not None for _, t, _ in its):
        if its:
            upload(s, why, its, log)                    # (only the crash log's start-up lines: recorded as seen)
        return None
    th = threading.Thread(target=upload, args=(s, why, its, log), daemon=True, name="log upload")
    th.start()
    return th
