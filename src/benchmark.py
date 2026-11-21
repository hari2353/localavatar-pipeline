"""End-to-end scenario benchmark with a safe-completion rate.

Cross-pollinated from harvard-edge/AVPerf: run named scenarios, record
latency and failures, and report the fraction that completed both correctly
and inside the deadline ("safe end-to-end processing rate").
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

_MAX_FAILURES = 20


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    name: str
    latency_s: float
    success: bool
    safe: bool
    detail: str


def run_scenarios(
    scenarios: list[tuple[str, Callable[[], object]]],
    *,
    deadline_s: float,
    clock: Callable[[], float] = time.perf_counter,
) -> dict:
    """Execute every scenario once and report the safe-completion rate."""
    if not scenarios:
        raise ValueError("scenarios must be non-empty")
    if deadline_s <= 0:
        raise ValueError("deadline_s must be positive")

    results: list[ScenarioResult] = []
    for name, run in scenarios:
        if not name.strip():
            raise ValueError("scenario name must be non-empty")
        started = clock()
        try:
            run()
        except Exception as exc:  # a failed render is a scenario failure
            latency = clock() - started
            results.append(ScenarioResult(
                name, round(latency, 4), False, False, f"error: {exc}"
            ))
            continue
        latency = clock() - started
        success = True
        safe = latency <= deadline_s
        detail = "ok" if safe else f"deadline {latency:.3f}s > {deadline_s}s"
        results.append(ScenarioResult(name, round(latency, 4), success, safe, detail))

    safe = sum(1 for r in results if r.safe)
    return {
        "total": len(results),
        "safe": safe,
        "safe_rate": round(safe / len(results), 4),
        "failures": [
            {"name": r.name, "latency_s": r.latency_s, "detail": r.detail}
            for r in results if not r.safe
        ][:_MAX_FAILURES],
        "scenarios": [
            {"name": r.name, "latency_s": r.latency_s,
             "success": r.success, "safe": r.safe, "detail": r.detail}
            for r in results
        ],
    }
