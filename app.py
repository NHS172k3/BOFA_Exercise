from pathlib import Path

from flask import Flask, jsonify, render_template, request

from engine import PortfolioEngine
from queries import (
    bond_detail,
    bond_wise_pnl_since,
    by_bond,
    by_desk,
    by_trader,
    global_summary,
    pnl_since,
)


ROOT = Path(__file__).resolve().parent
engine = PortfolioEngine(ROOT)

app = Flask(__name__)


def _event_id_from_request() -> int | None:
    raw = request.args.get("event")
    if raw is None:
        return None
    return int(raw)


@app.get("/")
def index():
    return render_template("index.html", max_event=max(engine.snapshots))


@app.get("/api/snapshot")
def snapshot():
    snap = engine.get_snapshot(_event_id_from_request())
    return jsonify(
        {
            "summary": global_summary(snap),
            "event_impact": {
                "event_id": snap.event_impact.event_id,
                "desk": snap.event_impact.desk,
                "trader": snap.event_impact.trader,
                "bond_id": snap.event_impact.bond_id,
                "buy_sell": snap.event_impact.buy_sell,
                "quantity": snap.event_impact.quantity,
                "clean_price": float(snap.event_impact.clean_price),
                "accrued_interest": float(snap.event_impact.accrued_interest),
                "dirty_price": float(snap.event_impact.dirty_price),
                "total_pv_before": float(snap.event_impact.total_pv_before),
                "total_pv_after": float(snap.event_impact.total_pv_after),
                "delta_pv": float(snap.event_impact.delta_pv),
            },
            "positions": [
                {
                    "desk": p.desk,
                    "trader": p.trader,
                    "bond_id": p.bond_id,
                    "quantity": p.quantity,
                    "clean_price": float(p.clean_price),
                    "accrued_interest": float(p.accrued_interest),
                    "dirty_price": float(p.dirty_price),
                    "present_value": float(p.present_value),
                }
                for p in snap.positions
            ],
        }
    )


@app.get("/api/rollups")
def rollups():
    snap = engine.get_snapshot(_event_id_from_request())
    return jsonify(
        {
            "desk": by_desk(snap),
            "trader": by_trader(snap),
            "bond": by_bond(snap),
        }
    )


@app.get("/api/bond/<bond_id>")
def bond(bond_id: str):
    snap = engine.get_snapshot(_event_id_from_request())
    return jsonify(bond_detail(snap, bond_id.upper()))


@app.get("/api/pnl")
def pnl():
    to_event = _event_id_from_request()
    from_event = int(request.args.get("from_event", 1))
    current = engine.get_snapshot(to_event)
    base = engine.get_snapshot(from_event)
    return jsonify(pnl_since(current, base))


@app.get("/api/pnl-bond")
def pnl_bond():
    to_event = _event_id_from_request()
    from_event = int(request.args.get("from_event", 1))
    current = engine.get_snapshot(to_event)
    base = engine.get_snapshot(from_event)
    return jsonify(
        {
            "from_event": base.event_id,
            "to_event": current.event_id,
            "bonds": bond_wise_pnl_since(current, base),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
