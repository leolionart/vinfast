"""Dependency-free provider-contract smoke check; run with python tests/provider_smoke.py."""

import ast
import asyncio
import logging
import pathlib
import ssl
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "vinfast"
for path in ROOT.glob("*.py"):
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
tree = ast.parse((ROOT / "api_auth.py").read_text(encoding="utf-8"))
helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "normalize_iot_provider")
manager = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AuthManager")
methods = [n for n in manager.body if isinstance(n, ast.AsyncFunctionDef) and n.name in ("get_provider_credentials", "refresh_iot_provider")]
namespace = {"KNOWN_IOT_PROVIDERS": ("AWS", "EMQX"), "_LOGGER": logging.getLogger(__name__)}
module = ast.fix_missing_locations(ast.Module(body=[helper, ast.ClassDef(name="AuthManager", bases=[], keywords=[], body=methods, decorator_list=[])], type_ignores=[]))
exec(compile(module, "api_auth.py", "exec"), namespace)
AuthManager = namespace["AuthManager"]
normalize = namespace["normalize_iot_provider"]
assert normalize(" emqx ") == "EMQX"
assert normalize("new-provider") is None


def response(status, data):
    return SimpleNamespace(status_code=status, json=lambda: {"data": data})


async def main():
    class Fake(AuthManager):
        def __init__(self, replies):
            self.core = SimpleNamespace(vin="VIN_B")
            self.replies = iter(replies)
            self.calls = []

        async def api_request(self, method, uri, **kwargs):
            self.calls.append((method, uri, kwargs))
            return next(self.replies)

    aws = {"accessKeyId": "key", "secretKeyId": "secret", "sessionToken": "sts"}
    emqx = {"sessionToken": "jwt", "accessKeyId": None, "secretKeyId": None}
    mock = Fake([response(200, emqx)])
    assert await mock.get_provider_credentials("emqx") == emqx
    assert mock.calls[0][0] == "POST"
    assert mock.calls[0][2]["body_dict"] == {"vinCode": "VIN_B", "iotProvider": "EMQX"}

    mock = Fake([response(405, {}), response(200, aws)])
    assert await mock.get_provider_credentials("AWS") == aws
    assert [call[0] for call in mock.calls] == ["POST", "GET"]

    mock = Fake([response(200, {"sessionToken": "sts"})])
    assert await mock.get_provider_credentials("AWS") is None
    assert await mock.get_provider_credentials("unknown") is None
    assert len(mock.calls) == 1

    mock = Fake([response(200, [
        {"vinCode": "VIN_A", "iotProvider": "AWS"},
        {"vinCode": "VIN_B", "iotProvider": "emqx"},
    ])])
    assert await mock.refresh_iot_provider() == "EMQX"


asyncio.run(main())
ctx = ssl.create_default_context()
ctx.load_verify_locations(str(ROOT / "root_ca_prod.pem"))
ctx.verify_flags |= ssl.VERIFY_X509_PARTIAL_CHAIN
assert ctx.check_hostname and ctx.verify_mode == ssl.CERT_REQUIRED
print("Provider contract and CA smoke checks passed")
