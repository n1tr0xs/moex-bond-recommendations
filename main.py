from dataclasses import dataclass
import datetime
import time
import requests
import csv

@dataclass
class SearchCriteria:
    min_bond_yield = 24.05
    max_bond_yield = float("inf")
    min_days_to_maturity = 0
    max_days_to_maturity = float("inf")

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
    ):
        self.ISIN = ISIN
        self.bond_name = bond_name
        self.face_value = face_value or 0
        self.coupon_value = coupon_value or 0
        self.coupon_period = coupon_period or float("inf")
        self.maturity_date = maturity_date
        self.bond_price = bond_price or float("inf")
        self.ACI = ACI

    @property
    def days_to_maturity(self):
        return (self.maturity_date - datetime.date.today()).days

    @property
    def yield_to_maturity(self):
        if self.days_to_maturity <= 0:
            return 0

        full_coupons, part_coupon = divmod(self.days_to_maturity, self.coupon_period)

        coupons = full_coupons + bool(part_coupon)
        coupons_income = coupons * self.coupon_value

        clean_price = self.face_value * self.bond_price / 100  # no ACI
        price = clean_price + self.ACI  # current market price
        price *= 1 + self.BROKER_FEE  # including broker fee

        total_income = self.face_value + coupons_income
        rate = (total_income / price - 1) * 100 * 365 / self.days_to_maturity

        return round(rate, 2)

    def __str__(self):
        return f"{self.ISIN=} {self.bond_name=} {self.face_value=} {self.coupon_value=} {self.coupon_period=} {self.maturity_date=} {self.bond_price=} {self.ACI=}"


def output_to_csv(filename: str, bond_list: list[Bond]) -> None:
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Название", "ISIN", "Дней до погашения", "Доходность"])
        for bond in bond_list:
            writer.writerow(
                [
                    bond.bond_name,
                    bond.ISIN,
                    bond.days_to_maturity,
                    str(bond.yield_to_maturity).replace(".", ","),
                ]
            )
    return


def LOG(message: str) -> None:
    print(message)


API_DELAY = round(60 / 50, 1)
BOARDGROUPS = [58, 7, 105]
search_criteria = SearchCriteria()


def get_json(url: str) -> dict:
    response = requests.get(url)
    return response.json()

def parse_boardgroup(boardgroup: int) -> list[Bond]:
    bonds : list[Bond] = []
    time.sleep(API_DELAY)
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

    market_data = json_data.get("marketdata", {}).get("data")
    securities_data: list = json_data.get("securities", {}).get("data", [])
    if not (json_data and market_data):
        LOG(
            f"Нет данных c Московской биржи для группы {boardgroup}."
            "Проверьте вручную по ссылке выше."
        )
        return bonds

    market_data: dict = {item[0]: item for item in market_data}
    securities_data: dict = {item[0]: item for item in securities_data}
    LOG(f"Всего в списке группы {boardgroup} {len(securities_data)} бумаг.")
    
    for i, ISIN in enumerate(securities_data, start=1):
        LOG(f"Строка {i} из {len(securities_data)}.")
        try:
            # Parsing data for bond
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
        # Checking search criteria
        condition = (
            search_criteria.min_days_to_maturity
            <= bond.days_to_maturity
            <= search_criteria.max_days_to_maturity
            and search_criteria.min_bond_yield
            <= bond.yield_to_maturity
            <= search_criteria.max_bond_yield
        )

        if condition:
            LOG(
                f"Условие "
                f"доходности {search_criteria.min_bond_yield} <= {bond.yield_to_maturity} <= {search_criteria.max_bond_yield} "
                f"дней до погашения {search_criteria.min_days_to_maturity} <= {bond.days_to_maturity} <= {search_criteria.max_days_to_maturity} "
                f"для {bond_name} с ISIN {ISIN} прошло."
            )
            bonds.append(bond)
        else:
            LOG(f"{bond_name} с ISIN {ISIN} не соответсвует критериям поиска.")
    return bonds

bonds =[]
for boardgroup in BOARDGROUPS:
    bonds.extend(parse_boardgroup(boardgroup))

output_to_csv("out.csv", bonds)