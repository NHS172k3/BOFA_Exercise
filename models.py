from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Bond:
    bond_id: str
    coupon: Decimal
    frequency: int
    months_since_coupon: int
    face_value: Decimal = Decimal("100")


@dataclass(frozen=True)
class Event:
    event_id: int
    desk: str
    trader: str
    bond_id: str
    buy_sell: str
    quantity: int
    clean_price: Decimal


@dataclass
class PositionState:
    quantity: int = 0


@dataclass(frozen=True)
class PositionView:
    desk: str
    trader: str
    bond_id: str
    quantity: int
    clean_price: Decimal
    accrued_interest: Decimal
    dirty_price: Decimal
    present_value: Decimal


@dataclass(frozen=True)
class EventImpact:
    event_id: int
    desk: str
    trader: str
    bond_id: str
    buy_sell: str
    quantity: int
    clean_price: Decimal
    accrued_interest: Decimal
    dirty_price: Decimal
    total_pv_before: Decimal
    total_pv_after: Decimal
    delta_pv: Decimal


@dataclass(frozen=True)
class Snapshot:
    event_id: int
    total_pv: Decimal
    delta_pv: Decimal
    open_positions: int
    positions: list[PositionView]
    event_impact: EventImpact
