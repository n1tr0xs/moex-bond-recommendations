import time
import logging
import requests
from schemas import *

logger = logging.getLogger("MOEX")


class MOEX_API:
    API_DELAY = round(60 / 50, 1)
    BOARDGROUPS = [7, 58, 105]

    def __init__(self):
        """
        Inits MOEX_API.
        """
        self.last_api_request = None

    def get_json(self, url: str) -> dict:
        """
        Returns json from url.
        """
        now = datetime.datetime.now()
        if self.last_api_request:
            delta = (now - self.last_api_request).total_seconds()
            wait_time = self.API_DELAY - delta
            if wait_time > 0:
                logger.info(f"Ожидание {wait_time}...")
                time.sleep(self.API_DELAY - delta)
        self.last_api_request = datetime.datetime.now()
        try:
            logger.info(f"Запрос к {url}.")
            response = requests.get(url)
        except:
            logger.warning(f"Не удалось установить соединение.")
            return {}

        try:
            return response.json()
        except:
            logger.warning(f"Не удалось получить json!")
            return {}

    def get_boardgroup_bonds(self, boardgroup: str) -> list[Bond]:
        """
        Returns all bonds from specified boardgroup.
        """
        logger.info(f"Запрос данных для группы {boardgroup}.")
        bonds = []
        url = f"https://iss.moex.com/iss/engines/stock/markets/bonds/boardgroups/{boardgroup}/securities.json?iss.dp=comma&iss.meta=off&iss.only=securities&securities.columns=SECID,SHORTNAME,FACEVALUE,COUPONVALUE,COUPONPERIOD,MATDATE,PREVLEGALCLOSEPRICE,ACCRUEDINT,FACEUNIT&"
        json = self.get_json(url)
        securities = json.get("securities", {}).get("data", {})
        if not securities:
            logger.warning("Нет данных для группы {boardgroup}")
            return []
        data = {item[0]: item for item in securities}
        logger.info(f"В группе {boardgroup} обнаружено {len(data)} бумаг.")
        for i, ISIN in enumerate(data, start=1):
            logger.info(f"Обработка {i}/{len(data)} - {ISIN}.")

            bond_data = data[ISIN]
            try:
                bond = Bond(
                    ISIN=ISIN,
                    name=bond_data[1],
                    face_value=float(bond_data[2]),
                    coupon_value=float(bond_data[3]),
                    coupon_period=float(bond_data[4]),
                    maturity_date=datetime.datetime.strptime(
                        bond_data[5], "%Y-%m-%d"
                    ).date(),
                    price=float(bond_data[6]),
                    ACI=float(bond_data[7]),
                    face_unit=bond_data[8],
                )
            except Exception as e:
                logger.warning(f"Ошибка при получении информации по {ISIN}.")
            else:
                bonds.append(bond)

        return bonds

    def get_bonds(self) -> list[Bond]:
        """
        Returns all bonds from all boardgroups specified in `MOEX_API.BOARDGROUPS`.
        """
        bonds = []
        for b in self.BOARDGROUPS:
            bonds.extend(self.get_boardgroup_bonds(b))
        return bonds
