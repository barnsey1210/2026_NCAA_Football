import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

from scripts.war_room import war_room_operator_api as api

REFRESH_SPEC = importlib.util.spec_from_file_location(
    "run_data_refresh", api.ROOT / "scripts/control/run_data_refresh.py"
)
refresh = importlib.util.module_from_spec(REFRESH_SPEC)
REFRESH_SPEC.loader.exec_module(refresh)

SERVICE_SPEC = importlib.util.spec_from_file_location(
    "run_war_room_service", api.ROOT / "scripts/control/run_war_room_service.py"
)
service = importlib.util.module_from_spec(SERVICE_SPEC)
SERVICE_SPEC.loader.exec_module(service)


def request(origin=api.PUBLIC_ORIGIN, method="POST", path="/war-room/market", query_string=b""):
    value = Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [(b"origin", origin.encode())] if origin else [],
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
            "server": ("127.0.0.1", 8787),
            "query_string": query_string,
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
        self.assertIn("GET", methods_by_path["/war-room/live/version"])
        self.assertIn("GET", methods_by_path["/war-room/live/health"])
        self.assertIn("GET", methods_by_path["/war-room/live/market-matrix"])
        self.assertNotIn("/war-room/acquire", methods_by_path)

    def test_bootstrap_is_exact_origin_allowlisted_and_secret_free(self):
        response = api.bootstrap(
            request(path="/war-room/bootstrap", query_string=b"channel_nonce=fixture-nonce-123456"),
            "operator@example.invalid",
        )
        html = response.body.decode()
        self.assertIn(api.PUBLIC_ORIGIN, html)
        self.assertIn("event.origin!==TARGET_ORIGIN", html)
        self.assertIn("event.source!==window.opener", html)
        self.assertIn("message.channelNonce!==CHANNEL_NONCE", html)
        self.assertIn("setInterval(()=>send({type:'READY'}),1000)", html)
        self.assertIn("ACTION_ROUTES=Object.freeze", html)
        self.assertIn("Object.hasOwn(ACTION_ROUTES,message.action)", html)
        self.assertIn("fetch(ACTION_ROUTES[message.action]", html)
        self.assertIn("method:'POST'", html)
        self.assertIn("credentials:'same-origin'", html)
        self.assertNotIn("operator@example.invalid", html)
        self.assertNotIn("apiKey", html)
        self.assertNotIn("/war-room/acquire", html)

    def test_public_builder_delegates_actions_without_direct_posts(self):
        builder = (api.ROOT / "scripts/site/build_war_room_page.py").read_text()
        self.assertIn("requestOperation('market'", builder)
        self.assertIn("CONTROL_WINDOW.postMessage", builder)
        self.assertNotIn("method:'POST'", builder)
        self.assertNotIn("method: 'POST'", builder)
        self.assertNotIn("fetch(`${CONTROL_BASE_URL}/war-room/", builder)
        self.assertIn("/war-room/bootstrap", builder)
        self.assertIn("event.origin!==CONTROL_ORIGIN", builder)
        self.assertIn("event.source!==CONTROL_WINDOW", builder)
        self.assertIn("sessionStorage.getItem(CONTROL_NONCE_KEY)", builder)
        self.assertIn("message.channelNonce!==ensureControlNonce()", builder)
        self.assertNotIn("fetch('/war-room/acquire'", builder)
        self.assertNotIn("headers:{'Content-Type':'application/json'}", builder)
        self.assertIn("LIVE_VERSION_URL", builder)
        self.assertIn("fetchDataPair(LIVE_MATRIX_URL,LIVE_HEALTH_URL)", builder)
        self.assertIn('POLL_SECONDS = max(1, int(control_config.get("browser_version_poll_seconds", 2)))', builder)

    def test_public_live_read_origin_is_exact(self):
        api.require_public_read_origin(
            request(api.PUBLIC_ORIGIN, "GET", "/war-room/live/version"),
            origin=api.PUBLIC_ORIGIN,
        )
        with self.assertRaises(HTTPException) as raised:
            api.require_public_read_origin(
                request("https://foreign.example", "GET", "/war-room/live/version"),
                origin="https://foreign.example",
            )
        self.assertEqual(raised.exception.status_code, 403)

    def test_live_version_advances_without_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            health=root/"health.json"; matrix=root/"matrix.json"
            def write(refresh_id):
                health.write_text(json.dumps({"schema_version":"war-room-health-v1","built_at":"2026-08-25T12:00:01Z","fast_market_refresh":{"refresh_id":refresh_id,"last_fast_pull_at":"2026-08-25T12:00:00Z"}}))
                matrix.write_text(json.dumps({"schema_version":"war-room-market-matrix-v1","built_at":"2026-08-25T12:00:02Z","fast_market_refresh":{"refresh_id":refresh_id,"last_fast_pull_at":"2026-08-25T12:00:00Z"}}))
            with patch.object(api,"HEALTH",health),patch.object(api,"MATRIX",matrix):
                write("refresh-one"); first=json.loads(api.live_version().body)
                write("refresh-two"); second=json.loads(api.live_version().body)
            self.assertEqual(first["refresh_id"],"refresh-one")
            self.assertEqual(second["refresh_id"],"refresh-two")

    def test_live_schedule_is_safe_normalized_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            schedule=Path(temporary)/"schedule.json"
            schedule.write_text(json.dumps({"schema_version":"schedule-live-enrichment-v2","games":[{"value":float("nan")}]}))
            with patch.object(api,"SCHEDULE",schedule):
                response=api.live_schedule()
            self.assertEqual(response.headers["cache-control"],"no-store")
            self.assertIsNone(json.loads(response.body)["games"][0]["value"])

    def test_normal_market_service_does_not_push(self):
        dispatcher=(api.ROOT/"scripts/control/run_war_room_service.py").read_text()
        schedule=json.loads((api.ROOT/"config/war_room_fast_schedule.json").read_text())
        self.assertIn('"war-room-market": [sys.executable, "scripts/war_room/run_fast_market_publication.py"]',dispatcher)
        self.assertNotIn("--push",schedule["entrypoint"])
        self.assertIn('"war-room-rebuild": [sys.executable, "scripts/war_room/run_fast_market_publication.py", "--skip-refresh", "--push"]',dispatcher)

    def test_ratings_registry_and_dispatcher_use_bounded_ratings_mode(self):
        registry=json.loads((api.ROOT/"scripts/control/refresh_stage_registry.json").read_text())
        self.assertEqual(registry["actions"]["RATINGS_REFRESH"]["controller_mode"],"ratings")
        command=service.resolve_command("ratings")
        self.assertEqual(command[1:3],["scripts/control/run_data_refresh.py","ratings"])
        self.assertNotIn("pregame",command)
        self.assertEqual(registry["actions"]["RATINGS_REFRESH"]["owner"],command[1])

    def test_registry_cannot_supply_arbitrary_command(self):
        malicious={"actions":{"RATINGS_REFRESH":{"controller_mode":"../../tmp/arbitrary"}}}
        with patch.object(service,"read_json",return_value=malicious):
            with self.assertRaisesRegex(RuntimeError,"unapproved controller mode"):
                service.resolve_command("ratings")

    def test_ratings_command_sets_are_bounded(self):
        no_change=" ".join(" ".join(x) for x in refresh.ratings_no_change_commands())
        changed=" ".join(" ".join(x) for x in refresh.ratings_change_commands())
        combined=no_change+" "+changed
        self.assertIn("build_war_room_health.py",no_change)
        self.assertIn("build_current_game_projection_contract.py",changed)
        for forbidden in (
            "daily_market_update.sh","build_public_site.py","publish_site.sh",
            "run_fast_market_refresh.py","postgame","season_sim","conference","playoff",
        ):
            self.assertNotIn(forbidden,combined)

    def test_ratings_change_detection(self):
        with patch.object(refresh,"load_json",return_value={"sources":{"SP+":{"change_status":"NO_CHANGE"}}}):
            self.assertFalse(refresh.accepted_ratings_changed()[0])
        with patch.object(refresh,"load_json",return_value={"sources":{"SP+":{"change_status":"UPDATED"}}}):
            self.assertTrue(refresh.accepted_ratings_changed()[0])

    def test_ratings_policy_is_separate_from_pregame(self):
        source=(api.ROOT/"scripts/control/run_data_refresh.py").read_text()
        function=source[source.index("def execute_ratings_service("):source.index("def deployed_commit(")]
        self.assertIn('get("ratings", False)',function)
        self.assertNotIn('get("pregame", False)',function)

    def test_mocked_ratings_no_change_and_accepted_change_paths(self):
        def base_run():
            return {"status":"RUNNING","errors":[],"stages":[],"validation_results":{},"providers_called":[],"api":{"calls_consumed":0}}
        cfg={"publication_policy":{"ratings":True,"pregame":False}}

        no_change=base_run()
        with patch.object(refresh,"run_commands",return_value=True) as runner, patch.object(
            refresh,"accepted_ratings_changed",return_value=(False,{"SP+":"NO_CHANGE"})
        ):
            refresh.execute_ratings_service(no_change,cfg,True)
        self.assertEqual(no_change["status"],"NO_CHANGES")
        self.assertEqual(runner.call_args_list[1].args[1],refresh.ratings_no_change_commands())
        self.assertEqual(no_change["providers_called"],["spplus","fpi","teamrankings","sagarin","dratings","massey"])
        self.assertEqual(no_change["api"]["calls_consumed"],0)
        self.assertEqual(no_change["api"]["credits_consumed"],0)

        changed=base_run()
        with patch.object(refresh,"run_commands",return_value=True) as runner, patch.object(
            refresh,"accepted_ratings_changed",return_value=(True,{"SP+":"UPDATED"})
        ):
            refresh.execute_ratings_service(changed,cfg,True)
        self.assertEqual(changed["status"],"COMPLETED")
        self.assertEqual(runner.call_args_list[1].args[1],refresh.ratings_change_commands())
        self.assertEqual(changed["change_counts"],{"ratings":1,"projections":1})

    def test_ratings_dispatcher_records_terminal_status_without_provider_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            captured=[]
            def completed(command,**_kwargs):
                captured.append(command)
                return subprocess.CompletedProcess(command,0,"fixture complete","")
            with patch.object(service,"CONTROL",root), patch.object(service,"LOCKS",root/"locks"), patch.object(
                service,"TASKS",root/"tasks"
            ), patch.object(service,"LATEST",root/"latest.json"), patch.object(
                service,"DAILY_STATUS",root/"daily.json"
            ), patch.object(service.subprocess,"run",side_effect=completed), patch.object(
                sys,"argv",["run_war_room_service.py","ratings","--task-id","ratings-fixture-terminal"]
            ):
                code=service.main()
            task=json.loads((root/"tasks/ratings-fixture-terminal.json").read_text())
            self.assertEqual(code,0)
            self.assertEqual(task["status"],"COMPLETED")
            self.assertEqual(captured[0][1:3],["scripts/control/run_data_refresh.py","ratings"])


if __name__ == "__main__":
    unittest.main()
