import logging
from schemas import Bond, SearchCriteria

logger = logging.getLogger("Utils")

def filter_bonds(bonds: list[Bond], criteria: SearchCriteria) -> list[Bond]:
    '''
    Filters given bonds by criteria.
    '''
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