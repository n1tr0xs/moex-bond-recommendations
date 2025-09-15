import logging
import requests
from bs4 import BeautifulSoup
from schemas import Bond, SearchCriteria

logger = logging.getLogger("Utils")


def filter_bonds(bonds: list[Bond], criteria: SearchCriteria) -> list[Bond]:
    """
    Filters given bonds by criteria.
    """
    filtered_bonds = []
    for bond in bonds:
        condition = (
            criteria.min_days_to_maturity
            <= bond.days_to_maturity
            <= criteria.max_days_to_maturity
            and criteria.min_bond_yield
            <= bond.approximate_yield
            <= criteria.max_bond_yield
            and (criteria.face_units is None or bond.face_unit in criteria.face_units)
        )
        if condition:
            logger.info(f"Облигация {bond.ISIN} прошла проверку критериев.")
            filtered_bonds.append(bond)
        else:
            logger.info(f"Облигация {bond.ISIN} не прошла проверку критериев.")
    return filtered_bonds

def add_credit_scores(bonds: list[Bond]) -> list[Bond]:
    '''
    Adds credit scores in-place to all bonds from list.
    '''
    for bond in bonds:
        bond.credit_score = get_score(bond.ISIN)
    return bonds

def get_score(ISIN: str) -> str:
    '''
    Parses credit score using smartLab.
    '''
    logger.info(f"Получение кредитного рейтинга эмитента облигации {ISIN}.")
    BASE_URL = "https://smart-lab.ru/q/bonds/{}"
    response = requests.get(BASE_URL.format(ISIN))
    soup = BeautifulSoup(response.text, "lxml")
    div = soup.find("div", text="Кредитный рейтинг")
    try:
        score = div.find_next().text.strip()
        logger.info(f"Кредитный рейтинг эмитента облигации {ISIN} - {score}.")
    except AttributeError:
        score = "Не известно"
        logger.info(f"Кредитный рейтинг эмитента облигации {ISIN} не известен.")
    return score
