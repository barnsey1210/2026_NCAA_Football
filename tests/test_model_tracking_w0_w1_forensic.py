import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/model_tracking/v2"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("forensic_w0_w1", SCRIPT_DIR / "reconstruct_w0_w1_forensic.py")
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
MANIFEST = ROOT / "data/model_tracking/v2/historical_reconstruction_w0_w1_2026.json"


def dt(value): return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_no_lookahead_guards():
    checkpoint=dt("2026-09-02T01:00:00Z"); kickoff=dt("2026-09-03T00:00:00Z")
    assert M.timing_rejection(dt("2026-09-02T02:00:00Z"),checkpoint,checkpoint,kickoff)=="model_after_checkpoint"
    assert M.timing_rejection(dt("2026-09-01T00:00:00Z"),dt("2026-09-02T02:00:00Z"),checkpoint,kickoff)=="market_after_checkpoint"
    assert M.timing_rejection(dt("2026-09-03T01:00:00Z"),checkpoint,dt("2026-09-04T00:00:00Z"),kickoff)=="model_after_kickoff"
    assert M.timing_rejection(dt("2026-09-01T00:00:00Z"),checkpoint,checkpoint,kickoff) is None


def test_manifest_standard_and_total_tuesday_cohorts_and_sunday_rejection():
    payload=json.loads(MANIFEST.read_text()); summary=payload["summary"]
    for model in M.MODELS:
        assert summary[f"W1|{model}|TUESDAY_9PM_ET"]["accepted"]==37
        assert summary[f"W1|{model}|SUNDAY_9PM_ET"]["accepted"]==0
        assert summary[f"W1|{model}|SUNDAY_9PM_ET"]["rejection_reasons"]["model_after_checkpoint"]==91
    assert payload["policy"]["no_lookahead"] is True


def test_nine_named_standard_candidates_are_revalidated():
    payload=json.loads(MANIFEST.read_text())
    expected={"Colorado at Georgia Tech","Massachusetts at Rutgers","Akron at Wake Forest","San Jose State at Eastern Michigan","Miami-FL at Stanford","UAB at Illinois","Toledo at Michigan State","UTEP at Oklahoma","Fresno State at USC"}
    rows={row["matchup"]:row for row in payload["records"] if row["week"]==1 and row["model_id"]=="standard_spread_4src_equal_v1" and row["checkpoint"]=="TUESDAY_9PM_ET" and row["matchup"] in expected}
    assert set(rows)==expected
    assert sum(row["status"]=="ACCEPTED" for row in rows.values())==6
    assert {row.get("rejection_reason") for row in rows.values() if row["status"]=="REJECTED"}=={"no_market_pair"}


def test_standard_formula_and_orientation_are_exact():
    payload=json.loads(MANIFEST.read_text())
    rows=[row for row in payload["records"] if row["model_id"]=="standard_spread_4src_equal_v1" and row["status"]=="ACCEPTED"]
    assert rows
    assert all(row["model_version"]=="v1" for row in rows)
    assert all(row["orientation_normalization"]["canonical_orientation"]=="home_margin" for row in rows)
    assert "Sagarin" not in M.MODELS["standard_spread_4src_equal_v1"]


def test_close_rows_use_frozen_contract_and_prebound_models():
    payload=json.loads(MANIFEST.read_text())
    rows=[row for row in payload["records"] if row["checkpoint"]=="CLOSE" and row["status"]=="ACCEPTED"]
    assert rows
    for row in rows:
        assert row["market_evidence_artifact"]=="data/site/current_market_contract.json"
        assert dt(row["model_evidence_timestamp"]) <= min(dt(row["market_evidence_timestamp"]),dt(row["kickoff"]))
