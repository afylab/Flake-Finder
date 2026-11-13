"""The microscope's devices opened only while they are used (Avram, 2026-10-28): Micro-Manager loads the configuration
(camera, stage, focus drive, IR camera, ...) when a job gets to the hardware or the start screen's live view opens, and
unloads it when the job ends and when that live view closes.  On the start screen (and after a job, waiting for the
next) the program holds nothing, so Stream Motion can use the camera and the stage meanwhile; it has to be closed
before a job starts (it holds the camera: the connection then fails and the window says so).

The Oasis stage keeps its position in the controller (its driver neither homes nor zeroes when it is opened again), so
stage coordinates stay the same across jobs; the camera's settings (bit depth, gamma, exposure) are set again by every
job and live view (Scanner.apply_camera).
"""
from __future__ import annotations

import threading
import time


class Microscope:
    """Micro-Manager's configuration loaded on demand into one core (the Scanner keeps the same core object)."""

    def __init__(self, core, cfg, corelog=None, log=print):
        self.core, self.cfg, self.corelog, self.log = core, str(cfg), corelog, log
        self.loaded = False
        self.lock = threading.Lock()              # (a connect and a release one after the other, never together)

    def busy(self):
        """A connect or a release is going on (in another thread)."""
        return self.lock.locked()

    def ready(self):
        return self.loaded and not self.busy()

    def connect(self):
        """Load the configuration (every device opened and started) unless it is loaded.  Returns True if it loaded it
        now; raises the error of a failed load (the devices loaded until then are unloaded again)."""
        with self.lock:
            if self.loaded:
                return False
            t0 = time.time()
            self.log(f"connecting to the microscope ({self.cfg}) ...")
            self._debug(True)                     # (Micro-Manager's log: which device it waits for)
            try:
                self.core.loadSystemConfiguration(self.cfg)
            except BaseException:
                try:
                    self.core.unloadAllDevices()
                except Exception:
                    pass
                raise
            finally:
                self._debug(False)
            self.loaded = True
            self.log(f"microscope connected ({time.time() - t0:.0f} s)")
            return True

    def release(self):
        """Unload every device (the camera, the stage, ...: free for other programs).  Returns True if they were loaded."""
        with self.lock:
            if not self.loaded:
                return False
            self.loaded = False
            c = self.core
            try:
                if c.isSequenceRunning():
                    c.stopSequenceAcquisition()
            except Exception:
                pass
            try:
                c.unloadAllDevices()
            except Exception as e:
                self.log(f"(the microscope's devices were not all closed: {e})")
            self.log("microscope released: the camera and the stage are free (e.g. for Stream Motion) until the next job")
            return True

    def _debug(self, on):
        if not self.corelog:
            return
        try:
            self.core.enableDebugLog(on)
        except Exception:
            pass


def cfg_devices(cfg):
    """[(label, library, adapter)] of the devices in a Micro-Manager configuration file (its Device lines)."""
    from pathlib import Path
    out = []
    try:
        for ln in Path(cfg).read_text(encoding="utf-8", errors="replace").splitlines():
            q = [x.strip() for x in ln.split(",")]
            if len(q) >= 4 and q[0] == "Device":
                out.append((q[1], q[2], q[3]))
    except OSError:
        pass
    return out
