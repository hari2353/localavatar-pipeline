from src.benchmark import run_scenarios


def test_all_scenarios_safe():
    out = run_scenarios(
        [("a", lambda: None), ("b", lambda: None)],
        deadline_s=10,
    )
    assert out["safe"] == 2
    assert out["safe_rate"] == 1.0
    assert out["failures"] == []


def test_deadline_miss_is_not_safe():
    ticks = iter([0.0, 2.0, 2.0, 2.5])
    out = run_scenarios(
        [("slow", lambda: None)], deadline_s=1, clock=lambda: next(ticks)
    )
    assert out["scenarios"][0]["success"] is True
    assert out["scenarios"][0]["safe"] is False
    assert out["safe_rate"] == 0.0
    assert "deadline" in out["failures"][0]["detail"]


def test_exception_is_a_failure_not_a_crash():
    out = run_scenarios(
        [("boom", lambda: (_ for _ in ()).throw(RuntimeError("render failed")))],
        deadline_s=10,
    )
    assert out["safe"] == 0
    assert "error: render failed" in out["failures"][0]["detail"]


def test_mixed_run_reports_rate():
    out = run_scenarios(
        [("ok", lambda: None), ("bad", lambda: (_ for _ in ()).throw(ValueError("x")))],
        deadline_s=10,
    )
    assert out["safe_rate"] == 0.5
    assert len(out["scenarios"]) == 2


def test_invalid_inputs_rejected():
    for scenarios, deadline in (
        ([], 1),
        ([("", lambda: None)], 1),
        ([("a", lambda: None)], 0),
    ):
        try:
            run_scenarios(scenarios, deadline_s=deadline)
        except ValueError:
            continue
        raise AssertionError("invalid input accepted")
