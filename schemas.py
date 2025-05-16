from dataclasses import dataclass
import datetime


@dataclass
class SearchCriteria:
    min_bond_yield: float = 0
    max_bond_yield: float = float("inf")
    min_days_to_maturity: float = 1
    max_days_to_maturity: float = float("inf")
    face_units: list[str] | None = ("SUR",)  # Use None if don't care about face unit


class Bond:
    BROKER_FEE = 0.25 / 100

    def __init__(
        self,
        ISIN: str,
        bond_name: str,
        face_value: float,
        coupon_value: float,
        coupon_period: int,
        maturity_date: datetime.date,
        bond_price: float,
        ACI: float,
        face_unit: str,
        is_qualified: bool = None,
    ):
        self.ISIN: str = ISIN
        self.bond_name: str = bond_name
        self.face_value: float = face_value or 0
        self.coupon_value: float = coupon_value or 0
        self.coupon_period: int = coupon_period or float("inf")
        self.maturity_date: datetime.date = maturity_date
        self.bond_price: float = bond_price or float("inf")
        self.ACI: float = ACI
        self.face_unit: str = face_unit
        self.is_qualified: bool = is_qualified

    @classmethod
    def headers(cls):
        return [
            "Наименование",
            "ISIN",
            "Дней до погашения",
            "Доходность к погашению",
            "Валюта",
            "Требуется квалификация",
        ]

    @property
    def as_list(self):
        return [
            self.bond_name,
            self.ISIN,
            self.days_to_maturity,
            self.yield_to_maturity,
            self.face_unit,
            (
                "Неизвестно"
                if self.is_qualified is None
                else "Да" if self.is_qualified else "Нет"
            ),
        ]

    @property
    def days_to_maturity(self):
        return (self.maturity_date - datetime.date.today()).days

    @property
    def yield_to_maturity(self):
        if self.days_to_maturity <= 0:
            return 0
        if self.coupon_period:
            full_coupons, part_coupon = divmod(
                self.days_to_maturity, self.coupon_period
            )
        else:
            full_coupons, part_coupon = 0, 0

        coupons = full_coupons + bool(part_coupon)
        coupons_income = coupons * self.coupon_value

        clean_price = self.face_value * self.bond_price / 100  # no ACI
        price = clean_price + self.ACI  # current market price
        price *= 1 + self.BROKER_FEE  # including broker fee

        total_income = self.face_value + coupons_income
        rate = (total_income / price - 1) * 100 * 365 / self.days_to_maturity

        return round(rate, 2)