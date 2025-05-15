import datetime
import requests
import csv

MIN_RATE = 24.05
MAX_RATE = float("inf")
MIN_DAYS_TO_MAT = 0
MAX_DAYS_TO_MAT = float("inf")


class Bond:
    BROKER_FEE = 0.25 / 100

    def __init__(
        self,
        ISIN: str,
        name: str,
        face_value: float,
        coupon_value: float,
        coupon_period: int,
        mat_date: datetime.date,
        trading_price: float,
        ACI: float,
    ):
        self.ISIN = ISIN
        self.name = name
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
        return f"{self.ISIN=} {self.name=} {self.face_value=} {self.coupon_value=} {self.coupon_period=} {self.mat_date=} {self.trading_price=} {self.ACI=}"


def LOG(message: str) -> None:
    print(message)


API_DELAY = round(60 / 50, 1)
BOARDGROUPS = [58, 7, 105]


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
    LOG(f"Строка {i} из {len(securities_data)}." f"SECID = {ISIN}.")
    try:
        bond: Bond = Bond(
            ISIN,
            securities_data[ISIN][1],
            securities_data[ISIN][2],
            securities_data[ISIN][3],
            securities_data[ISIN][4],
            datetime.datetime.strptime(securities_data[ISIN][5], "%Y-%m-%d").date(),
            market_data[ISIN][1],
            securities_data[ISIN][6],
        )
    except ValueError:
        continue

    if (
        MIN_DAYS_TO_MAT <= bond.days_to_maturity <= MAX_DAYS_TO_MAT
        and MIN_RATE <= bond.yield_to_maturity <= MAX_RATE
    ):
        bonds.append(bond)
    else:
        LOG(
            f"Облигация {bond.name} {bond.ISIN} не прошла проверку условий:\n"
            f"Дней до погашения: {MIN_DAYS_TO_MAT} <= {bond.days_to_maturity} <= {MAX_DAYS_TO_MAT}\n"
            f"Доходность: {MIN_RATE} <= {bond.yield_to_maturity} <= {MAX_RATE}"
        )


for bond in bonds:
    LOG(
        f"Прибыльность {bond.name} {bond.ISIN} = {bond.yield_to_maturity}%. "
        f"Дней до погашения: {bond.days_to_maturity}."
    )

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
