from collections import defaultdict
from decimal import Decimal

from models import Snapshot


def _to_money(value: Decimal) -> float:
    return float(value)


def global_summary(snapshot: Snapshot) -> dict:
    return {
        "event_id": snapshot.event_id,
        "total_pv": _to_money(snapshot.total_pv),
        "delta_pv": _to_money(snapshot.delta_pv),
        "open_positions": snapshot.open_positions,
    }


def by_desk(snapshot: Snapshot) -> list[dict]:
    desk_totals = defaultdict(lambda: {"quantity": 0, "pv": Decimal("0")})
    for row in snapshot.positions:
        desk_totals[row.desk]["quantity"] += row.quantity
        desk_totals[row.desk]["pv"] += row.present_value
    out = []
    for desk, values in sorted(desk_totals.items()):
        out.append(
            {
                "desk": desk,
                "quantity": values["quantity"],
                "present_value": _to_money(values["pv"]),
            }
        )
    return out


def by_trader(snapshot: Snapshot) -> list[dict]:
    trader_totals = defaultdict(lambda: {"desk": "", "quantity": 0, "pv": Decimal("0")})
    for row in snapshot.positions:
        trader_totals[row.trader]["desk"] = row.desk
        trader_totals[row.trader]["quantity"] += row.quantity
        trader_totals[row.trader]["pv"] += row.present_value
    out = []
    for trader, values in sorted(trader_totals.items()):
        out.append(
            {
                "trader": trader,
                "desk": values["desk"],
                "quantity": values["quantity"],
                "present_value": _to_money(values["pv"]),
            }
        )
    return out


def by_bond(snapshot: Snapshot) -> list[dict]:
    bond_totals = defaultdict(
        lambda: {
            "quantity": 0,
            "pv": Decimal("0"),
            "clean_price": Decimal("0"),
            "dirty_price": Decimal("0"),
            "accrued_interest": Decimal("0"),
            "count": 0,
        }
    )
    for row in snapshot.positions:
        b = bond_totals[row.bond_id]
        b["quantity"] += row.quantity
        b["pv"] += row.present_value
        b["clean_price"] += row.clean_price
        b["dirty_price"] += row.dirty_price
        b["accrued_interest"] += row.accrued_interest
        b["count"] += 1
    out = []
    for bond_id, values in sorted(bond_totals.items()):
        count = max(values["count"], 1)
        out.append(
            {
                "bond_id": bond_id,
                "quantity": values["quantity"],
                "present_value": _to_money(values["pv"]),
                "clean_price": _to_money(values["clean_price"] / count),
                "dirty_price": _to_money(values["dirty_price"] / count),
                "accrued_interest": _to_money(values["accrued_interest"] / count),
            }
        )
    return out


def bond_detail(snapshot: Snapshot, bond_id: str) -> dict:
    rows = [p for p in snapshot.positions if p.bond_id == bond_id]
    quantity = sum(p.quantity for p in rows)
    pv = sum((p.present_value for p in rows), Decimal("0"))
    if not rows:
        return {
            "bond_id": bond_id,
            "quantity": 0,
            "present_value": 0.0,
            "positions": [],
        }
    return {
        "bond_id": bond_id,
        "quantity": quantity,
        "present_value": _to_money(pv),
        "positions": [
            {
                "desk": p.desk,
                "trader": p.trader,
                "quantity": p.quantity,
                "clean_price": _to_money(p.clean_price),
                "accrued_interest": _to_money(p.accrued_interest),
                "dirty_price": _to_money(p.dirty_price),
                "present_value": _to_money(p.present_value),
            }
            for p in rows
        ],
    }


def pnl_since(current: Snapshot, base: Snapshot) -> dict:
    return {
        "from_event": base.event_id,
        "to_event": current.event_id,
        "pnl": _to_money(current.total_pv - base.total_pv),
    }


def bond_wise_pnl_since(current: Snapshot, base: Snapshot) -> list[dict]:
    current_pv: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    base_pv: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for row in current.positions:
        current_pv[row.bond_id] += row.present_value

    for row in base.positions:
        base_pv[row.bond_id] += row.present_value

    all_bonds = sorted(set(current_pv) | set(base_pv))
    out: list[dict] = []
    for bond_id in all_bonds:
        out.append(
            {
                "bond_id": bond_id,
                "pv_current": _to_money(current_pv[bond_id]),
                "pv_base": _to_money(base_pv[bond_id]),
                "pnl": _to_money(current_pv[bond_id] - base_pv[bond_id]),
            }
        )
    return out
