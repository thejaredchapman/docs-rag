import json
from pathlib import Path

import docs_rag

SERVER_JSON = Path(__file__).resolve().parent.parent / "server.json"


def test_server_json_matches_package_version():
    server = json.loads(SERVER_JSON.read_text())
    assert server["version"] == docs_rag.__version__
    for package in server["packages"]:
        assert package["version"] == docs_rag.__version__
