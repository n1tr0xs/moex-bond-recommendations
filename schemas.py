﻿from dataclasses import dataclass
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
        name: str,
        face_value: float,
        coupon_value: float,
        coupon_period: int,
        maturity_date: datetime.date,
        price: float,
        ACI: float,
        face_unit: str,
        credit_score: str | None = None,
        is_qualified: bool | None = None,
    ):
        self.ISIN: str = ISIN
        self.bond_name: str = name
        self.face_value: float = face_value or 0
        self.coupon_value: float = coupon_value or 0
        self.coupon_period: int = coupon_period or float("inf")
        self.maturity_date: datetime.date = maturity_date
        self.bond_price: float = price or float("inf")
        self.ACI: float = ACI
        self.face_unit: str = face_unit
        self.credit_score: str = credit_score
        self.is_qualified: bool = is_qualified

    @classmethod
    def headers(cls):
        return [
            "Наименование",
            "Кредитный рейтинг эмитента",
            "ISIN",
            "Номинал",
            "Цена на бирже",
            "Номинал купона",
            "Дней до погашения",
            "Доходность к погашению",
            "Валюта",
            "Требуется квалификация",
        ]

    @property
    def as_list(self):
        return [
            self.bond_name,
            self.credit_score or "",
            self.ISIN,
            self.face_value,
            self.broker_price,
            self.coupon_value,
            self.days_to_maturity,
            self.approximate_yield,
            self.face_unit,
            (
                "Неизвестно"
                if self.is_qualified is None
                else "Да" if self.is_qualified else "Нет"
            ),
        ]

    @property
    def broker_price(self):
        price = self.face_value * self.bond_price / 100  # no ACI
        price = price + self.ACI  # current market price
        price *= 1 + self.BROKER_FEE  # including broker fee
        return price

    @property
    def coupons_amount(self):
        if self.coupon_period:
            full_coupons, part_coupon = divmod(
                self.days_to_maturity, self.coupon_period
            )
        else:
            full_coupons, part_coupon = 0, 0
        coupons = full_coupons + bool(part_coupon)
        return coupons

    @property
    def days_to_maturity(self):
        return (self.maturity_date - datetime.date.today()).days

    @property
    def approximate_yield(self):
        if self.days_to_maturity <= 0:
            return 0

        coupons_income = self.coupons_amount * self.coupon_value

        total_income = self.face_value + coupons_income
        rate = (
            (total_income / self.broker_price - 1) * 100 * 365 / self.days_to_maturity
        )

        return round(rate, 2)
