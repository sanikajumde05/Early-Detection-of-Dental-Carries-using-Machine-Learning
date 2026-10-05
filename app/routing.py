"""Intelligent Routing — simplified rule-based version of Flow Designer + Assignment Rules.
Business rule: route by category. Extend with location/workload-based rules later.
"""
from app.config import CATEGORY_TO_DEPARTMENT


def route_to_department(category: str) -> str:
    return CATEGORY_TO_DEPARTMENT.get(category, "Municipal Department")
