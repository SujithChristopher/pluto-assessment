"""
S3 background sync for HOMER-PLUTO assessment data.

Mirrors the local data tree (everything under ``homer_data_root()`` — both the
``fullassessment`` and ``screening`` trees) to an S3 bucket. Local files remain
the source of truth; this only ever *uploads* copies, never deletes or moves.

Bucket layout mirrors the local tree:

    s3://<AWS_S3_BUCKET>/<AWS_S3_PREFIX>/HomerPlutoData/<path-under-data-root>

Credentials and the target bucket are read from a ``.env`` file in the repo
root (see ``load_s3_config``). If credentials are missing the worker reports a
``disabled`` status and stops cleanly — the app keeps working offline.

The worker is a long-lived ``QThread``: it sweeps on a fixed interval and also
on demand via :meth:`S3SyncWorker.request_sweep` (called when a task window
closes so freshly finalised CSVs upload promptly). A small JSON manifest next to
the data root records the (size, mtime) of every uploaded file so unchanged
files are skipped on subsequent sweeps.

Author: HOMER-PLUTO
"""

import json
import os
import pathlib
import sys
import threading
import time

from PySide6.QtCore import QThread, Signal

import plutofullassessdef as pfadef


# Files/dirs we never upload.
MANIFEST_NAME = ".s3sync_manifest.json"
_SKIP_SUFFIXES = (".tmp", ".lock")
# A file modified within this many seconds is assumed to still be open for
# writing (CSVBufferWriter appends); defer it to the next sweep to avoid
# uploading a half-written file.
_WRITE_GRACE_SEC = 2.0


def _env_search_paths() -> list[pathlib.Path]:
    """Where to look for ``.env``, in priority order.

    Frozen (PyInstaller) build: beside the .exe first, so the operator can edit
    credentials without rebuilding and the secret is never baked into the
    binary. Then the source dir (dev runs). ``_MEIPASS`` is included last only
    as a fallback in case someone does bundle it.
    """
    paths = []
    if getattr(sys, "frozen", False):
        paths.append(pathlib.Path(sys.executable).parent / ".env")
    paths.append(pathlib.Path(__file__).parent / ".env")
    if hasattr(sys, "_MEIPASS"):
        paths.append(pathlib.Path(sys._MEIPASS) / ".env")
    return paths


def load_s3_config(env_path: pathlib.Path | None = None) -> dict:
    """Parse the ``.env`` into an S3 config dict.

    No external dependency (python-dotenv) — a plain ``KEY=VALUE`` parse is
    enough. Returns keys: bucket, prefix, access_key, secret_key, region.
    ``prefix`` defaults to ``case_study_cmcv`` when unset in .env. When
    ``env_path`` is not given, searches the locations in
    :func:`_env_search_paths` and uses the first that exists.
    """
    if env_path is None:
        env_path = next(
            (_p for _p in _env_search_paths() if _p.exists()),
            _env_search_paths()[-1],
        )
    values: dict[str, str] = {}
    if env_path.exists():
        for _line in env_path.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _, _v = _line.partition("=")
            values[_k.strip()] = _v.strip().strip('"').strip("'")
    return {
        "bucket": values.get("AWS_S3_BUCKET", ""),
        "prefix": values.get("AWS_S3_PREFIX", "") or "case_study_cmcv",
        "access_key": values.get("AWS_ACCESS_KEY_ID", ""),
        "secret_key": values.get("AWS_SECRET_ACCESS_KEY", ""),
        "region": values.get("AWS_REGION", "") or None,
    }


class S3SyncWorker(QThread):
    """Background uploader. Emits :attr:`status` ``(state, pending, message)``.

    States: ``disabled`` (no creds), ``offline`` (network/credential error,
    will retry), ``syncing`` (upload in progress, ``pending`` = files left),
    ``synced`` (everything mirrored), ``error`` (unexpected failure).
    """

    status = Signal(str, int, str)

    def __init__(self, root: pathlib.Path, config: dict,
                 interval_sec: float = 30.0, parent=None):
        super().__init__(parent)
        self._root = pathlib.Path(root)
        self._cfg = config
        self._interval = interval_sec
        self._wake = threading.Event()
        self._stopflag = False
        self._client = None
        self._manifest_path = self._root / MANIFEST_NAME
        # Keys mirror the tree *including* the data-root folder name, so the
        # bucket layout is <prefix>/HomerPlutoData/<subjid>/...
        self._relbase = self._root.parent

    #
    # Public control (called from the GUI thread)
    #
    def request_sweep(self):
        """Ask the worker to sweep as soon as possible."""
        self._wake.set()

    def stop(self):
        """Stop the worker loop and wake it so it exits promptly."""
        self._stopflag = True
        self._wake.set()

    #
    # Worker thread body
    #
    def run(self):
        if not self._init_client():
            self.status.emit("disabled", 0, "S3 credentials not configured.")
            return
        while not self._stopflag:
            try:
                self._sweep_once()
            except Exception as e:  # never let the worker thread die
                self.status.emit("offline", 0, f"{type(e).__name__}: {e}")
            # Wait for the interval or an explicit wake request.
            self._wake.wait(timeout=self._interval)
            self._wake.clear()

    #
    # Internals
    #
    def _init_client(self) -> bool:
        cfg = self._cfg
        if not (cfg["bucket"] and cfg["access_key"] and cfg["secret_key"]):
            return False
        try:
            import boto3
            self._client = boto3.client(
                "s3",
                aws_access_key_id=cfg["access_key"],
                aws_secret_access_key=cfg["secret_key"],
                region_name=cfg["region"],
            )
            return True
        except Exception:
            return False

    def _load_manifest(self) -> dict:
        try:
            return json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_manifest(self, manifest: dict):
        try:
            self._manifest_path.write_text(
                json.dumps(manifest), encoding="utf-8"
            )
        except Exception:
            pass

    def _iter_local_files(self):
        """Yield (abs_path, posix_relpath) for every uploadable file."""
        for _dirpath, _dirnames, _filenames in os.walk(self._root):
            for _name in _filenames:
                if _name == MANIFEST_NAME or _name.startswith("."):
                    continue
                if _name.endswith(_SKIP_SUFFIXES):
                    continue
                _abs = pathlib.Path(_dirpath, _name)
                _rel = _abs.relative_to(self._relbase).as_posix()
                yield _abs, _rel

    def _sweep_once(self):
        """Walk the tree once, upload changed files, update the manifest."""
        manifest = self._load_manifest()
        now = time.time()
        pending = []
        for _abs, _rel in self._iter_local_files():
            try:
                _stat = _abs.stat()
            except OSError:
                continue
            if now - _stat.st_mtime < _WRITE_GRACE_SEC:
                continue  # likely still being written; catch it next sweep
            _sig = [_stat.st_size, int(_stat.st_mtime)]
            if manifest.get(_rel) != _sig:
                pending.append((_abs, _rel, _sig))

        if not pending:
            self.status.emit("synced", 0, "All data mirrored to S3.")
            return

        _bucket = self._cfg["bucket"]
        _prefix = self._cfg["prefix"].strip("/")
        _total = len(pending)
        for _i, (_abs, _rel, _sig) in enumerate(pending):
            if self._stopflag:
                return
            self.status.emit("syncing", _total - _i, f"Uploading {_rel}")
            _key = f"{_prefix}/{_rel}" if _prefix else _rel
            self._client.upload_file(str(_abs), _bucket, _key)
            manifest[_rel] = _sig
            # Persist periodically so a crash doesn't lose progress.
            if _i % 20 == 0:
                self._save_manifest(manifest)
        self._save_manifest(manifest)
        self.status.emit("synced", 0, f"Mirrored {_total} file(s) to S3.")
