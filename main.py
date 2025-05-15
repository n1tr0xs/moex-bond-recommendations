from asyncio import Condition
from dataclasses import dataclass
import datetime
import requests
import csv


@dataclass
class SearchCriteria:
    MIN_RATE = 24.05
    MAX_RATE = float("inf")
    MIN_DAYS_TO_MAT = 0
    MAX_DAYS_TO_MAT = float("inf")


class Bond:
    BROKER_FEE = 0.25 / 100

    def __init__(
        self,
        ISIN: str,
        bond_name: str,
        face_value: float,
        coupon_value: float,
        coupon_period: int,
        mat_date: datetime.date,
        trading_price: float,
        ACI: float,
    ):
        self.ISIN = ISIN
        self.bond_name = bond_name
        self.face_value = face_value or 0
        self.coupon_value = coupon_value or 0
        self.coupon_period = coupon_period or float("inf")
        self.mat_date = mat_date
        self.trading_price = trading_price or float("inf")
        self.ACI = ACI

    @property
    def days_to_maturity(self):
        return (self.mat_date - datetime.date.today()).days

    @property
    def yield_to_maturity(self):
        if self.days_to_maturity <= 0:
            return 0

        full_coupons, part_coupon = divmod(self.days_to_maturity, self.coupon_period)

        coupons = full_coupons + bool(part_coupon)
        coupons_income = coupons * self.coupon_value

        clean_price = self.face_value * self.trading_price / 100  # no ACI
        price = clean_price + self.ACI  # current market price
        price *= 1 + self.BROKER_FEE  # including broker fee

        total_income = self.face_value + coupons_income
        rate = (total_income / price - 1) * 100 * 365 / self.days_to_maturity

        return round(rate, 2)

    def __str__(self):
        return f"{self.ISIN=} {self.bond_name=} {self.face_value=} {self.coupon_value=} {self.coupon_period=} {self.mat_date=} {self.trading_price=} {self.ACI=}"


def LOG(message: str) -> None:
    print(message)


API_DELAY = round(60 / 50, 1)
BOARDGROUPS = [58, 7, 105]
conditions = SearchCriteria()


def get_json(url: str) -> dict:
    response = requests.get(url)
    return response.json()


boardgroup = BOARDGROUPS[0]
url = (
    f"https://iss.moex.com/iss/engines/stock/markets/bonds/boardgroups/{boardgroup}/securities.json?"
    "iss.dp=comma&iss.meta=off&"
    "iss.only=securities,marketdata&"
    "securities.columns=SECID,SHORTNAME,FACEVALUE,COUPONVALUE,COUPONPERIOD,MATDATE,ACCRUEDINT&"
    "marketdata.columns=SECID,LAST"
)
LOG(f"Ссылка поиска всех доступных облигаций группы {boardgroup}: {url}.")

try:
    json_data: dict = get_json(url)
except:
    LOG("Ошибка запроса к API.")


if not (json_data and json_data.get("marketdata", {}).get("data")):
    LOG(
        f"Нет данных c Московской биржи для группы {boardgroup}."
        "Проверьте вручную по ссылке выше."
    )
# next boardgroup

bond_list: list = json_data.get("securities", {}).get("data", [])
securities_data: dict = {item[0]: item for item in bond_list}
LOG(f"Всего в списке группы {boardgroup} {len(bond_list)} бумаг.")


market_data: dict = {
    item[0]: item for item in json_data.get("marketdata", {}).get("data", [])
}

bonds: list[Bond] = []
for i, ISIN in enumerate(securities_data, start=1):
    LOG(f"Строка {i} из {len(securities_data)}.")
    try:
        # Достаем данные для облигации
        bond_name = str(securities_data[ISIN][1])
        face_value = float(securities_data[ISIN][2])
        coupon_value = float(securities_data[ISIN][3])
        coupon_period = float(securities_data[ISIN][4])
        maturity_date = datetime.datetime.strptime(
            securities_data[ISIN][5], "%Y-%m-%d"
        ).date()
        bond_price = float(market_data[ISIN][1])
        ACI = float(securities_data[ISIN][6])
    except Exception as e:
        LOG(f"Ошибка преобразования данных. Пропуск {ISIN}.")
        continue

    bond: Bond = Bond(
        ISIN=ISIN,
        bond_name=bond_name,
        face_value=face_value,
        coupon_value=coupon_value,
        coupon_period=coupon_period,
        maturity_date=maturity_date,
        bond_price=bond_price,
        ACI=ACI,
    )
    # Проверка соответствия облигации условиям
    condition = (
        conditions.MIN_DAYS_TO_MAT
        <= bond.days_to_maturity
        <= conditions.MAX_DAYS_TO_MAT
        and conditions.MIN_RATE <= bond.yield_to_maturity <= conditions.MAX_RATE
    )

    if condition:
        LOG(
            f"Условие "
            f"доходности {conditions.MIN_RATE} <= {bond.yield_to_maturity} <= {conditions.MAX_RATE} "
            f"дней до погашения {conditions.MIN_DAYS_TO_MAT} <= {bond.days_to_maturity} <= {conditions.MAX_DAYS_TO_MAT} "
            f"для {bond_name} с ISIN {ISIN} прошло."
        )
        bonds.append(bond)
    else:
        LOG(f"{bond_name} с ISIN {ISIN} не соответсвует критериям поиска.")

with open("out.csv", "w") as csvfile:
    writer = csv.writer(csvfile, dialect="excel")
    writer.writerow(["Название", "ISIN", "Дней до погашения", "Доходность"])
    for bond in bonds:
        writer.writerow(
            [
                bond.name,
                bond.ISIN,
                bond.days_to_maturity,
                str(bond.yield_to_maturity).replace(",", "."),
            ]
        )
