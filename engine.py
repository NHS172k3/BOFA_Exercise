import csv
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from models import Bond, Event, EventImpact, PositionState, PositionView, Snapshot


def q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def accrued_fraction(months_since_coupon: int, frequency: int) -> Decimal:
    period_months = Decimal(12) / Decimal(frequency)
    return Decimal(months_since_coupon) / period_months


def accrued_interest(bond: Bond) -> Decimal:
    return (bond.coupon / Decimal(bond.frequency)) * accrued_fraction(
        bond.months_since_coupon, bond.frequency
    ) * bond.face_value


def dirty_price(clean_price: Decimal, ai: Decimal) -> Decimal:
    return clean_price + ai


def position_delta(buy_sell: str, quantity: int) -> int:
    if buy_sell == "BUY":
        return quantity
    if buy_sell == "SELL":
        return -quantity
    raise ValueError(f"Invalid side: {buy_sell}")


def present_value(quantity: int, dirty: Decimal) -> Decimal:
    return Decimal(quantity) * dirty


def _read_dict_rows(csv_path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        lines = [line for line in f if line.strip()]

    header_index = None
    for i, line in enumerate(lines):
        cols = [c.strip() for c in line.strip().split(",")]
        if required_columns.issubset(set(cols)):
            header_index = i
            break

    if header_index is None:
        raise ValueError(f"Could not find expected header in {csv_path.name}")

    reader = csv.DictReader(lines[header_index:])
    return list(reader)


class PortfolioEngine:
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.bonds = self._load_bonds(self.root_path / "bonds - bonds.csv")
        self.events = self._load_events(self.root_path / "events - events.csv")
        self.snapshots: dict[int, Snapshot] = {}
        self._build_snapshots()

    def _load_bonds(self, csv_path: Path) -> dict[str, Bond]:
        bonds: dict[str, Bond] = {}
        rows = _read_dict_rows(
            csv_path,
            required_columns={"BondID", "Coupon", "Frequency", "MonthsSinceCoupon"},
        )
        for row in rows:
            bond = Bond(
                bond_id=row["BondID"].strip(),
                coupon=Decimal(row["Coupon"].strip()),
                frequency=int(row["Frequency"].strip()),
                months_since_coupon=int(row["MonthsSinceCoupon"].strip()),
            )
            bonds[bond.bond_id] = bond
        return bonds

    def _load_events(self, csv_path: Path) -> list[Event]:
        events: list[Event] = []
        rows = _read_dict_rows(
            csv_path,
            required_columns={
                "EventID",
                "Desk",
                "Trader",
                "BondID",
                "BuySell",
                "Quantity",
                "CleanPrice",
            },
        )
        for row in rows:
            events.append(
                Event(
                    event_id=int(row["EventID"]),
                    desk=row["Desk"].strip(),
                    trader=row["Trader"].strip(),
                    bond_id=row["BondID"].strip(),
                    buy_sell=row["BuySell"].strip().upper(),
                    quantity=int(row["Quantity"]),
                    clean_price=Decimal(row["CleanPrice"]),
                )
            )
        events.sort(key=lambda e: e.event_id)
        last_id = 0
        for event in events:
            if event.event_id <= last_id:
                raise ValueError("EventID must be strictly increasing")
            if event.bond_id not in self.bonds:
                raise ValueError(f"Unknown BondID in events: {event.bond_id}")
            last_id = event.event_id
        return events

    def _build_snapshots(self) -> None:
        state: dict[tuple[str, str, str], PositionState] = defaultdict(PositionState)
        latest_clean_prices: dict[str, Decimal] = {}
        total_pv_previous = Decimal("0")

        for event in self.events:
            latest_clean_prices[event.bond_id] = event.clean_price
            key = (event.desk, event.trader, event.bond_id)
            state[key].quantity += position_delta(event.buy_sell, event.quantity)

            positions: list[PositionView] = []
            total_pv = Decimal("0")
            for (desk, trader, bond_id), pos_state in state.items():
                if pos_state.quantity == 0:
                    continue
                bond = self.bonds[bond_id]
                clean = latest_clean_prices.get(bond_id, Decimal("0"))
                ai = accrued_interest(bond)
                dirty = dirty_price(clean, ai)
                pv = present_value(pos_state.quantity, dirty)
                total_pv += pv
                positions.append(
                    PositionView(
                        desk=desk,
                        trader=trader,
                        bond_id=bond_id,
                        quantity=pos_state.quantity,
                        clean_price=q2(clean),
                        accrued_interest=q2(ai),
                        dirty_price=q2(dirty),
                        present_value=q2(pv),
                    )
                )

            total_pv = q2(total_pv)
            delta_pv = q2(total_pv - total_pv_previous)
            total_pv_previous = total_pv

            event_bond = self.bonds[event.bond_id]
            event_ai = q2(accrued_interest(event_bond))
            event_dirty = q2(dirty_price(event.clean_price, event_ai))
            impact = EventImpact(
                event_id=event.event_id,
                desk=event.desk,
                trader=event.trader,
                bond_id=event.bond_id,
                buy_sell=event.buy_sell,
                quantity=event.quantity,
                clean_price=q2(event.clean_price),
                accrued_interest=event_ai,
                dirty_price=event_dirty,
                total_pv_before=q2(total_pv - delta_pv),
                total_pv_after=total_pv,
                delta_pv=delta_pv,
            )

            self.snapshots[event.event_id] = Snapshot(
                event_id=event.event_id,
                total_pv=total_pv,
                delta_pv=delta_pv,
                open_positions=len(positions),
                positions=sorted(
                    positions,
                    key=lambda p: (p.desk, p.trader, p.bond_id),
                ),
                event_impact=impact,
            )

    def get_snapshot(self, event_id: int | None = None) -> Snapshot:
        if not self.snapshots:
            raise ValueError("No snapshots available")
        if event_id is None:
            return self.snapshots[max(self.snapshots)]
        if event_id not in self.snapshots:
            raise KeyError(f"EventID {event_id} not found")
        return self.snapshots[event_id]
