"""FreeCAD GUI initialization — auto-starts the RPC server."""

import os
import sys

import FreeCAD

# Add FreeCAD user app data Mod directory to sys.path
try:
    user_mod = os.path.join(FreeCAD.getUserAppDataDir(), "Mod")
    if os.path.isdir(user_mod) and user_mod not in sys.path:
        sys.path.insert(0, user_mod)
    addon_dir = os.path.join(user_mod, "FreecadCli")
    if os.path.isdir(addon_dir) and addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
except Exception:
    pass

# Fallback: check __file__ if present in scope
if "__file__" in globals() and __file__:
    try:
        curr = os.path.dirname(os.path.abspath(__file__))
        if curr not in sys.path:
            sys.path.insert(0, curr)
        parent = os.path.dirname(curr)
        if parent not in sys.path:
            sys.path.insert(0, parent)
    except Exception:
        pass

try:
    from FreecadCli import rpc_server
except ImportError:
    import rpc_server

rpc_server.start()
