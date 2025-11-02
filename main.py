import datetime
import logging

from moex import MOEX_API
from excel import ExcelBook
import utils
from schemas import Bond, SearchCriteria

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(
            f"{datetime.datetime.now().strftime("%d.%m.%Y")}.log",
            mode="w",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("Main")


def main():
    # Search criteria setup
    INF = float("inf")
    search_criteria: SearchCriteria = SearchCriteria(
        min_bond_yield=18 / 0.87,
        max_bond_yield=INF,
        min_days_to_maturity=1,
        max_days_to_maturity=365,
        face_units=None,
    )

    # Main
    logger.info(
        f"Начало работы: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}"
    )
    moex_api = MOEX_API()
    bonds: list[Bond] = moex_api.get_bonds()
    bonds: list[Bond] = utils.filter_bonds(bonds, search_criteria)
    bonds: list[Bond] = utils.add_credit_scores(bonds)
    bonds.sort(key=lambda b: -b.approximate_yield)
    ExcelBook().write(bonds)
    logger.info(
        f"Конец работы: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}"
    )


if __name__ == "__main__":
    main()
