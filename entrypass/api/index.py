"""Vercel serverless entry point."""

import sys
import os
import traceback

# ── Resolve app/ directory ────────────────────────────────────
_this_dir = os.path.dirname(os.path.abspath(__file__))        # .../entrypass/api
_project_root = os.path.dirname(_this_dir)                     # .../entrypass
_app_dir = os.path.join(_project_root, "app")                  # .../entrypass/app

# app.py uses bare imports (from routes.auth import ..., from utils.security import ...)
# so the app/ directory must be the FIRST entry on sys.path.
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

# Remove project root from sys.path if present, to prevent Python
# from treating  app/  as a package  (it has __init__.py for local use).
if _project_root in sys.path:
    sys.path.remove(_project_root)

try:
    # Now  'import app'  resolves to  app/app.py  (module), NOT the
    # app/ package, because _app_dir is on sys.path and _project_root
    # is removed.  But to be 100% safe we load by file path:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("_flask_app", os.path.join(_app_dir, "app.py"))
    _mod = _ilu.module_from_spec(_spec)
    sys.modules["_flask_app"] = _mod          # register so sub-imports don't re-trigger
    _spec.loader.exec_module(_mod)

    app = _mod.app

except Exception as e:
    # Surface the real error so we can debug from the browser
    _tb = traceback.format_exc()

    from flask import Flask as _Flask
    app = _Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _boot_error(path):
        return {
            "error": "Application failed to start",
            "message": str(e),
            "traceback": _tb,
            "sys_path": sys.path,
            "app_dir": _app_dir,
            "cwd": os.getcwd(),
            "app_dir_contents": os.listdir(_app_dir) if os.path.isdir(_app_dir) else "NOT A DIR",
        }, 500
