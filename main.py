from log import Log
from moex import MOEX_API
from excel import ExcelBook
from schemas import *


def main():
    search_criteria: SearchCriteria = SearchCriteria()

    log: Log = Log()
    moex: MOEX_API = MOEX_API(log)
    bonds: list[Bond] = moex.search_by_criteria(search_criteria)
    ExcelBook().write(bonds, log)
    log.save_to_file()


if __name__ == "__main__":
    main()