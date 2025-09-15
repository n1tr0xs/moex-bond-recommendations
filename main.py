import datetime
import logging

from moex import MOEX_API
from excel import ExcelBook
import utils
from schemas import Bond, SearchCriteria

logger = logging.getLogger("Main")


def main():
    # Search criteria setup
    INF = float("inf")
    search_criteria: SearchCriteria = SearchCriteria(
        min_bond_yield=20/.87,
        max_bond_yield=INF,
        min_days_to_maturity=1,
        max_days_to_maturity=INF,
        face_units=None,
    )

    # Logger setup
    logging.basicConfig(
        filename=f"{datetime.datetime.now().strftime("%d.%m.%Y")}.log",
        filemode="w",
        level=logging.INFO,
    )

    # Main
    logger.info(f"Начало работы: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}")
    moex_api = MOEX_API()
    bonds: list[Bond] = moex_api.get_bonds()
    bonds: list[Bond] = utils.filter_bonds(bonds, search_criteria)
    bonds: list[Bond] = utils.add_credit_scores(bonds)
    ExcelBook().write(bonds)
    logger.info(f"Конец работы: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}")

if __name__ == "__main__":
    main()
