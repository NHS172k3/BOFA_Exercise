from decimal import Decimal
from pathlib import Path

from engine import PortfolioEngine, accrued_interest


def test_bond1_accrued_interest_matches_example():
    root = Path(__file__).resolve().parents[1]
    engine = PortfolioEngine(root)
    ai = accrued_interest(engine.bonds["BOND1"])
    assert ai == Decimal("1.25")


def test_snapshot_delta_consistency():
    root = Path(__file__).resolve().parents[1]
    engine = PortfolioEngine(root)
    for event_id in range(2, max(engine.snapshots) + 1):
        current = engine.snapshots[event_id]
        prev = engine.snapshots[event_id - 1]
        assert current.delta_pv == current.total_pv - prev.total_pv
