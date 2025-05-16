from log import Log
from moex import MOEX_API
from excel import ExcelBook
from schemas import *


INF = float('inf')

def main():
    search_criteria: SearchCriteria = SearchCriteria(
        min_bond_yield=0,
        max_bond_yield=INF,
        min_days_to_maturity=1,
        max_days_to_maturity=INF,
    )

    log: Log = Log()
    moex: MOEX_API = MOEX_API(log, True)
    bonds: list[Bond] = moex.search_by_criteria(search_criteria)
    ExcelBook().write(bonds, log)
    log.save_to_file()


if __name__ == "__main__":
    main()