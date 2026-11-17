from wedding_visual.evaluation import pass_rate, run_eval_set


def test_eval_set_has_ten_cases():
    results = run_eval_set()
    assert len(results) == 10


def test_eval_set_covers_all_four_arrangements():
    results = run_eval_set()
    arrangements = {r["arrangement"] for r in results}
    assert arrangements == {"side-by-side", "stacked", "interlocking", "circular-badge"}


def test_eval_set_currently_passes_cleanly():
    # Regression net: if a future change to layout/monogram.py, render/plan.py, or
    # mapping.py's heuristics introduces a real defect (not just a tuning nit), one of
    # these 10 cases should start FAILing. If this test breaks, read the failing case's
    # findings before touching the threshold -- see the circular-badge ring/glyph overlap
    # this eval set actually caught during phase 6 development.
    results = run_eval_set()
    failing = [r for r in results if not r["passed"]]
    assert failing == [], f"unexpected FAIL findings: {failing}"
    assert pass_rate(results) == 1.0


def test_eval_set_is_deterministic():
    a = run_eval_set(seed=0)
    b = run_eval_set(seed=0)
    assert a == b
