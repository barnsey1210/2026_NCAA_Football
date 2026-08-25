import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

from scripts.war_room import war_room_operator_api as api


def request(origin=api.PUBLIC_ORIGIN, method="POST", path="/war-room/market"):
    value = Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [(b"origin", origin.encode())] if origin else [],
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
            "server": ("127.0.0.1", 8787),
            "query_string": b"",
        }
    )
    value.state.correlation_id = "fixture-correlation"
    value.state.operator = None
    value.state.task_id = None
    return value


class OperatorContractTests(unittest.TestCase):
    def test_exact_origin_and_access_identity_are_required(self):
        value = request(api.PUBLIC_ORIGIN, "GET", "/war-room/status")
        operator = api.require_access(
            value,
            origin=api.PUBLIC_ORIGIN,
            cf_access_jwt_assertion="fixture-jwt",
            cf_access_authenticated_user_email="operator@example.invalid",
        )
        self.assertEqual(operator, "operator@example.invalid")
        self.assertEqual(value.state.operator, operator)

        with self.assertRaises(HTTPException) as raised:
            api.require_access(
                request("https://foreign.example", "GET", "/war-room/status"),
                origin="https://foreign.example",
                cf_access_jwt_assertion="fixture-jwt",
                cf_access_authenticated_user_email="operator@example.invalid",
            )
        self.assertEqual(raised.exception.status_code, 403)

        with self.assertRaises(HTTPException) as raised:
            api.require_access(
                request(api.PUBLIC_ORIGIN, "GET", "/war-room/status"),
                origin=api.PUBLIC_ORIGIN,
                cf_access_jwt_assertion=None,
                cf_access_authenticated_user_email=None,
            )
        self.assertEqual(raised.exception.status_code, 401)

    def test_action_routes_require_exact_first_party_control_origin(self):
        value = request(api.CONTROL_ORIGIN)
        operator = api.require_access(
            value,
            origin=api.CONTROL_ORIGIN,
            cf_access_jwt_assertion="fixture-jwt",
            cf_access_authenticated_user_email="operator@example.invalid",
        )
        self.assertEqual(operator, "operator@example.invalid")

        for rejected_origin in (api.PUBLIC_ORIGIN, "https://foreign.example", None):
            with self.subTest(origin=rejected_origin):
                with self.assertRaises(HTTPException) as raised:
                    api.require_access(
                        request(rejected_origin),
                        origin=rejected_origin,
                        cf_access_jwt_assertion="fixture-jwt",
                        cf_access_authenticated_user_email="operator@example.invalid",
                    )
                self.assertEqual(raised.exception.status_code, 403)

    def test_market_acknowledgement_is_202_idempotent_and_persisted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(api, "TASKS", root / "tasks"), patch.object(
                api, "LATEST", root / "latest.json"
            ), patch("scripts.war_room.war_room_operator_api.subprocess.Popen") as popen:
                popen.return_value.pid = 4321
                first_request = request(api.CONTROL_ORIGIN)
                first = api.request_action("market", "operator@example.invalid", first_request)
                payload = json.loads(first.body)
                self.assertEqual(first.status_code, 202)
                self.assertEqual(payload["status"], "REQUESTED")
                self.assertTrue(payload["task_id"].startswith("market-"))
                self.assertEqual(first_request.state.task_id, payload["task_id"])
                task = json.loads((root / "tasks" / f'{payload["task_id"]}.json').read_text())
                self.assertEqual(task["status"], "REQUESTED")
                self.assertEqual(task["correlation_id"], "fixture-correlation")

                second = api.request_action("market", "operator@example.invalid", request(api.CONTROL_ORIGIN))
                self.assertEqual(json.loads(second.body)["task_id"], payload["task_id"])
                self.assertEqual(popen.call_count, 1)

    def test_fixed_route_contract_has_no_legacy_acquire(self):
        methods_by_path = {
            route.path: set(route.methods or [])
            for route in api.app.routes
            if hasattr(route, "methods")
        }
        self.assertIn("POST", methods_by_path["/war-room/market"])
        self.assertNotIn("GET", methods_by_path["/war-room/market"])
        self.assertIn("GET", methods_by_path["/war-room/bootstrap"])
        self.assertNotIn("/war-room/acquire", methods_by_path)

    def test_bootstrap_is_exact_origin_allowlisted_and_secret_free(self):
        response = api.bootstrap("operator@example.invalid")
        html = response.body.decode()
        self.assertIn(api.PUBLIC_ORIGIN, html)
        self.assertIn("event.origin!==TARGET_ORIGIN", html)
        self.assertIn("event.source!==window.opener", html)
        self.assertIn("new Set(['market','ratings','postgame'])", html)
        self.assertIn("method:'POST'", html)
        self.assertIn("credentials:'same-origin'", html)
        self.assertNotIn("operator@example.invalid", html)
        self.assertNotIn("apiKey", html)
        self.assertNotIn("/war-room/acquire", html)

    def test_public_builder_uses_simple_canonical_market_post(self):
        builder = (api.ROOT / "scripts/site/build_war_room_page.py").read_text()
        self.assertIn("requestOperation('/war-room/market'", builder)
        self.assertIn("method:'POST'", builder)
        self.assertIn("credentials:'include'", builder)
        self.assertIn("/war-room/bootstrap", builder)
        self.assertIn("event.origin!==CONTROL_ORIGIN", builder)
        self.assertIn("event.source!==CONTROL_WINDOW", builder)
        self.assertNotIn("fetch('/war-room/acquire'", builder)
        self.assertNotIn("headers:{'Content-Type':'application/json'}", builder)


if __name__ == "__main__":
    unittest.main()
