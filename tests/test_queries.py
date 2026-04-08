from pathlib import Path

from engine import PortfolioEngine
from queries import by_bond, by_desk, by_trader, global_summary


def test_rollups_have_data():
    root = Path(__file__).resolve().parents[1]
    engine = PortfolioEngine(root)
    snap = engine.get_snapshot(150)
    assert len(by_desk(snap)) > 0
    assert len(by_trader(snap)) > 0
    assert len(by_bond(snap)) > 0


def test_summary_shape():
    root = Path(__file__).resolve().parents[1]
    engine = PortfolioEngine(root)
    summary = global_summary(engine.get_snapshot(20))
    assert "total_pv" in summary
    assert "delta_pv" in summary
    assert summary["event_id"] == 20
