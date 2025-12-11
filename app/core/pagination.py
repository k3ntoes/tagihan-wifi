from typing import Any, Callable, Dict, Generic, List, Literal, Optional, Type, TypeVar

from duckdb import DuckDBPyConnection
from pydantic import BaseModel

from app.core.config import LOGGER

T = TypeVar("T")

OperatorType = Literal["=", "!=", ">", "<", ">=", "<=", "IN", "NOT IN", "LIKE", "ILIKE"]
ConditionType = Literal["AND", "OR"]


class FilterType:
    def __init__(
        self,
        field: str,
        value: Any,
        operator: OperatorType = "=",
        condition: ConditionType = "AND",
    ):
        self.field = field
        self.value = value
        self.condition = condition
        self.operator = operator


class PaginationResult(BaseModel, Generic[T]):
    content: List[T]
    page: int
    size: int
    total_elements: int
    total_pages: int
    number_of_elements: int
    is_last: bool
    is_first: bool
    is_empty: bool


class PaginationHandler(Generic[T]):
    def __init__(
        self,
        base_query: str,
        count_query: str,
        model_class: Type[T],
        map_function: Optional[Callable[[Dict], T]] = None,
        default_sort: str = "id",
        default_direction: str = "ASC",
    ):
        self.base_query = base_query
        self.count_query = count_query
        self.model_class = model_class
        self.map_function = map_function or (lambda x: self.model_class(**x))
        self.default_sort = default_sort
        self.default_direction = default_direction

    def get_page(
        self,
        db: DuckDBPyConnection,
        page: int = 1,
        size: int = 10,
        sort: Optional[str] = None,
        direction: Optional[str] = None,
        **filters: FilterType,
    ) -> PaginationResult[T]:
        # Calculate offset
        offset = (page - 1) * size if page > 0 else 0

        # Build the query - use copies to prevent mutation
        query = self.base_query
        count_query = self.count_query

        # Add WHERE clause if filters exist
        where_clauses = []
        params = ()

        for _filter in filters.values():
            if _filter.value is not None:
                where_clauses.append(f"{_filter.field} {_filter.operator} ?")
                params += (
                    f"%{_filter.value}%"
                    if _filter.operator == "ILIKE"
                    else _filter.value,
                )

        if where_clauses:
            where_clause = " WHERE " + " AND ".join(where_clauses)
            query += where_clause
            count_query += where_clause

        # Execute queries
        count_result = db.execute(count_query, params).fetchone()
        total = count_result[0] if count_result else 0

        # Add ORDER BY
        sort_field = sort or self.default_sort
        sort_direction = direction.upper() if direction else self.default_direction
        query += f" ORDER BY {sort_field} {sort_direction}"

        # Add LIMIT and OFFSET
        query += f" LIMIT {size} OFFSET {offset}"

        LOGGER.debug(query)

        cursor = db.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Map results to model
        mapped_items = []
        if self.map_function and items:
            mapped_items = [self.map_function(dict(item)) for item in items]

        # Calculate total pages
        total_pages = (total + size - 1) // size if size > 0 else 1

        return PaginationResult(
            content=mapped_items,
            total_elements=total,
            page=page,
            size=size,
            total_pages=total_pages,
            number_of_elements=len(mapped_items),
            is_last=page >= total_pages,
            is_first=page <= 1,
            is_empty=len(mapped_items) == 0,
        )
