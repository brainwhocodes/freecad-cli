import importlib.util
import sys
from unittest.mock import MagicMock, patch


def test_rpc_server_pyside6_import():
    mock_pyside6 = MagicMock()
    mock_pyside6.QtCore.QObject = object
    mock_pyside6.QtCore.Signal = MagicMock()
    mock_pyside6.QtCore.Slot = MagicMock(return_value=lambda f: f)

    with patch.dict("sys.modules", {"PySide6": mock_pyside6, "PySide6.QtCore": mock_pyside6.QtCore}):
        if "rpc_server" in sys.modules:
            del sys.modules["rpc_server"]
        spec = importlib.util.spec_from_file_location("rpc_server", "addon/FreecadCli/rpc_server.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod._MainThreadExecutor, "_run")
        mock_pyside6.QtCore.Slot.assert_called_with(str, object)


def test_rpc_server_pyside2_fallback():
    class BadImporter:
        def find_spec(self, fullname, path=None, target=None):
            if "PySide6" in fullname:
                raise ImportError("No PySide6")

    bad_importer = BadImporter()
    sys.meta_path.insert(0, bad_importer)
    mock_pyside2 = MagicMock()
    mock_pyside2.QtCore.QObject = object
    mock_pyside2.QtCore.Signal = MagicMock()
    mock_pyside2.QtCore.Slot = MagicMock(return_value=lambda f: f)

    try:
        sys.modules.pop("PySide6", None)
        with patch.dict("sys.modules", {"PySide2": mock_pyside2, "PySide2.QtCore": mock_pyside2.QtCore}):
            if "rpc_server" in sys.modules:
                del sys.modules["rpc_server"]
            spec = importlib.util.spec_from_file_location("rpc_server", "addon/FreecadCli/rpc_server.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert hasattr(mod._MainThreadExecutor, "_run")
            mock_pyside2.QtCore.Slot.assert_called_with(str, object)
    finally:
        if bad_importer in sys.meta_path:
            sys.meta_path.remove(bad_importer)
