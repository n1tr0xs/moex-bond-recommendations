from moex import MOEX_API
from excel import ExcelBook
from schemas import *


def main():
    moex: MOEX_API = MOEX_API()
    search_criteria: SearchCriteria = SearchCriteria()
    bonds: list[Bond] = moex.search_by_criteria(search_criteria)
    ExcelBook().write(bonds)


if __name__ == "__main__":
    main()