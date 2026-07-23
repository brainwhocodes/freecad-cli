"""FreeCAD GUI initialization — auto-starts the RPC server."""

import os
import sys

addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from FreecadCli import rpc_server
except ImportError:
    import rpc_server

rpc_server.start()
