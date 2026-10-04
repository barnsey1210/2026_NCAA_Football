from scripts.projections.validate_massey_weekly_coverage import coverage_status


def test_one_or_two_unresolved_games_are_provider_partial_not_global_failure():
    assert coverage_status(117, 116) == "PARTIAL"
    assert coverage_status(117, 115) == "PARTIAL"


def test_zero_required_rows_resolved_remains_failure():
    assert coverage_status(117, 0) == "FAIL"


def test_full_coverage_passes():
    assert coverage_status(117, 117) == "PASS"
