import io
import json
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from freecad_cli.cli import cli


def test_ping_success():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.ping.return_value = True
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["ping"])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": True}
        assert result.exit_code == 0


def test_ping_connection_refused():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.ping.side_effect = ConnectionRefusedError()
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["ping"])
        assert result.exit_code != 0


def test_export_object_stl():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "/tmp/out.stl\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["export", "stl", "-o", "/tmp/out.stl"])
        output = json.loads(result.output)
        assert output["data"] == "/tmp/out.stl"
        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "Mesh.export" in call_code


def test_export_object_step():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "/tmp/out.step\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["export", "step", "-o", "/tmp/out.step"])
        output = json.loads(result.output)
        assert output["data"] == "/tmp/out.step"
        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "Part.export" in call_code


def test_export_object_fcstd():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "/tmp/out.fcstd\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["export", "fcstd", "-o", "/tmp/out.fcstd"])
        output = json.loads(result.output)
        assert output["data"] == "/tmp/out.fcstd"
        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "doc.saveAs" in call_code


def test_execute_code_delegates_to_rpc():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "hello\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["execute-code", "print('hello')"])
        output = json.loads(result.output)
        assert output["status"] == "ok"
        assert output["data"]["output"] == "hello\n"

def test_get_parts_list_accessor_code():
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": '["box.step"]\n', "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        from freecad_cli.client import FreeCADClient
        client = FreeCADClient()
        parts = client.get_parts_list()
        assert parts == ["box.step"]

        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "getUserAppDataDir" in call_code
        assert "getResourceDir" in call_code
        assert "getHomePath" in call_code
        assert "FreeCAD.__file__" in call_code
def test_get_parts_list_execution_without_file_attr():
    from freecad_cli.client import FreeCADClient

    mock_proxy = MagicMock()
    captured_code = None

    def fake_execute_code(code):
        nonlocal captured_code
        captured_code = code
        return {"output": "[]\n", "error": ""}

    mock_proxy.execute_code = fake_execute_code

    with patch("freecad_cli.client.xmlrpc.client.ServerProxy", return_value=mock_proxy):
        client = FreeCADClient()
        client.get_parts_list()

    assert captured_code is not None

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        parts_lib = tmp_path / "Mod" / "Parts_Library"
        parts_lib.mkdir(parents=True, exist_ok=True)
        (parts_lib / "bracket.step").write_text("dummy step content")
        (parts_lib / "gear.FCStd").write_text("dummy fcstd content")

        fake_freecad = types.ModuleType("FreeCAD")
        if hasattr(fake_freecad, "__file__"):
            delattr(fake_freecad, "__file__")
        fake_freecad.getUserAppDataDir = lambda: str(tmp_path)
        fake_freecad.getResourceDir = lambda: ""
        fake_freecad.getHomePath = lambda: ""

        old_stdout = sys.stdout
        stdout_capture = io.StringIO()
        try:
            sys.stdout = stdout_capture
            with patch.dict("sys.modules", {"FreeCAD": fake_freecad}):
                exec(captured_code, {"__builtins__": __builtins__})
        finally:
            sys.stdout = old_stdout

        parts = json.loads(stdout_capture.getvalue().strip())
        assert set(parts) == {"bracket.step", "gear.FCStd"}

    with tempfile.TemporaryDirectory() as empty_dir:
        fake_freecad = types.ModuleType("FreeCAD")
        if hasattr(fake_freecad, "__file__"):
            delattr(fake_freecad, "__file__")
        fake_freecad.getUserAppDataDir = lambda: str(empty_dir)

        old_stdout = sys.stdout
        stdout_capture = io.StringIO()
        try:
            sys.stdout = stdout_capture
            with patch.dict("sys.modules", {"FreeCAD": fake_freecad}):
                exec(captured_code, {"__builtins__": __builtins__})
        finally:
            sys.stdout = old_stdout

        parts = json.loads(stdout_capture.getvalue().strip())
        assert parts == []
