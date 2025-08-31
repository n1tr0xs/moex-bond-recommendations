from schemas import *
from log import Log
import time
import requests


class MOEX_API:
    API_DELAY = round(60 / 50, 1)
    BOARDGROUPS = [7, 58, 105]

    def __init__(self, log: Log, check_bond_qual: bool = False):
        self.log = log
        self.last_api_time = None
        self.check_bond_qual = check_bond_qual

    def get_json(self, url: str) -> dict:
        now = datetime.datetime.now()

        if self.last_api_time:
            delta = (now - self.last_api_time).total_seconds()
            if delta < self.API_DELAY:
                time.sleep(self.API_DELAY - delta)
        self.last_api_time = datetime.datetime.now()
        response = requests.get(url)
        return response.json()

    def get_bond_qualification(self, ISIN: str) -> bool | None:
        url = (
            f"https://iss.moex.com/iss/securities/{ISIN}.json?"
            "iss.meta=off"
            "&iss.only=description&"
            "description.columns=name,title,value&"
        )
        self.log.info(f"Проверка требования квалификации для {ISIN}.")
        try:
            time.sleep(self.API_DELAY)
            json_data = self.get_json(url)
            description_data = json_data["description"]["data"]

            is_qualified_investors_data = next(
                (
                    item
                    for item in description_data
                    if item[0] == "ISQUALIFIEDINVESTORS"
                ),
                None,
            )
            qual_investor_group_data = next(
                (item for item in description_data if item[0] == "QUALINVESTORGROUP"),
                None,
            )

            is_qualified_investors = (
                int(is_qualified_investors_data[2])
                if is_qualified_investors_data and is_qualified_investors_data[2]
                else 0
            )  # По умолчанию 0, если не найдено

            qual_investor_group = (
                qual_investor_group_data[2]
                if qual_investor_group_data and qual_investor_group_data[2]
                else "не определена"
            )  # Текст по умолчанию, если не найден

            if is_qualified_investors == 0:
                self.log.info(f"Для покупки {ISIN} квалификация НЕ нужна.")
                return False
            else:
                self.log.info(
                    f"{ISIN} для квалифицированных инвесторов категории: {qual_investor_group}"
                )
                return True
        except Exception as e:
            self.log.error(
                f"Ошибка с {ISIN} при получении сведений о необходимой квалификации."
            )
            return None

    def parse_boardgroup(
        self,
        search_criteria: SearchCriteria,
        boardgroup: int,
    ) -> list[Bond]:
        bonds: list[Bond] = []
        time.sleep(self.API_DELAY)
        url = (
            f"https://iss.moex.com/iss/engines/stock/markets/bonds/boardgroups/{boardgroup}/securities.json?"
            "iss.dp=comma&iss.meta=off&"
            "iss.only=securities&"
            "securities.columns=SECID,SHORTNAME,FACEVALUE,COUPONVALUE,COUPONPERIOD,MATDATE,PREVLEGALCLOSEPRICE,ACCRUEDINT,FACEUNIT&"
        )
        self.log.info(
            f"\nСсылка поиска всех доступных облигаций группы {boardgroup}: {url}.\n"
        )

        try:
            json_data: dict = self.get_json(url)
        except:
            self.log.error("Ошибка запроса к API.")

        securities_data: list = json_data.get("securities", {}).get("data", [])
        if not (securities_data):
            self.log.warning(
                f"Нет данных c Московской биржи для группы {boardgroup}."
                "Проверьте вручную по ссылке выше."
            )
            return []

        securities_data: dict = {item[0]: item for item in securities_data}
        self.log.info(
            f"Всего в списке группы {boardgroup} - {len(securities_data)} бумаг."
        )

        for i, ISIN in enumerate(securities_data, start=1):
            self.log.info(f"\nСтрока {i} из {len(securities_data)}:")

            # Pasing bond data
            bond_name = str(securities_data[ISIN][1])

            try:
                face_value = float(securities_data[ISIN][2])
            except TypeError:
                self.log.warning(
                    f"Ошибка при получении номинала облигации. Пропуск {ISIN}"
                )
                continue

            try:
                coupon_value = float(securities_data[ISIN][3])
            except TypeError:
                coupon_value = 0
                self.log.warning(
                    f"Ошибка при получении номинала купона. Пропуск {ISIN}"
                )
                continue

            try:
                coupon_period = float(securities_data[ISIN][4])
            except TypeError:
                self.log.warning(f"Ошибка при получении периода купона. Пропуск {ISIN}")
                continue

            try:
                mat_date = securities_data[ISIN][5]
                date_format = "%Y-%m-%d"
                maturity_date = datetime.datetime.strptime(mat_date, date_format).date()
            except ValueError:
                self.log.warning(
                    f"Ошибка при получении даты погашения облигации. Пропуск {ISIN}."
                )
                continue

            try:
                bond_price = float(securities_data[ISIN][6])
            except TypeError:
                self.log.warning(
                    f"Ошибка при получении цены облигации на бирже. Пропуск {ISIN}."
                )
                continue

            try:
                ACI = float(securities_data[ISIN][7])
            except TypeError:
                self.log.warning(
                    f"Ошибка при получении накопленного купонного дохода. Пропуск {ISIN}."
                )
                continue

            face_unit = securities_data[ISIN][8]

            bond: Bond = Bond(
                ISIN=ISIN,
                bond_name=bond_name,
                face_value=face_value,
                coupon_value=coupon_value,
                coupon_period=coupon_period,
                maturity_date=maturity_date,
                bond_price=bond_price,
                ACI=ACI,
                face_unit=face_unit,
            )

            # Checking basic search criteria
            condition = (
                (
                    search_criteria.min_days_to_maturity
                    <= bond.days_to_maturity
                    <= search_criteria.max_days_to_maturity
                )
                and (
                    search_criteria.min_bond_yield
                    <= bond.approximate_yield
                    <= search_criteria.max_bond_yield
                )
                and (
                    (search_criteria.face_units is None)
                    or (bond.face_unit in search_criteria.face_units)
                )
            )

            if condition:
                self.log.info(
                    f"Условие "
                    + f"доходности ({search_criteria.min_bond_yield}% <= {bond.approximate_yield}% <= {search_criteria.max_bond_yield}%), "
                    + f"дней до погашения ({search_criteria.min_days_to_maturity} <= {bond.days_to_maturity} <= {search_criteria.max_days_to_maturity}), "
                    + (
                        f"валюта ({bond.face_unit} в {search_criteria.face_units}) "
                        if search_criteria.face_units
                        else ""
                    )
                    + f"для {ISIN} прошло."
                )

                if self.check_bond_qual:
                    bond.is_qualified = self.get_bond_qualification(ISIN)

                bonds.append(bond)
            else:
                self.log.info(
                    f"{bond_name} с ISIN {ISIN} не соответсвует критериям поиска."
                )
        return bonds

    def search_by_criteria(self, search_criteria: SearchCriteria) -> list[Bond]:
        bonds = []
        for boardgroup in self.BOARDGROUPS:
            bonds.extend(self.parse_boardgroup(search_criteria, boardgroup))
        return bonds
