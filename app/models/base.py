from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel


class BasePageRequest(BaseModel):
    page: Optional[int]=1
    size: Optional[int]=10
    sort: Optional[str]=None
    direction: Optional[str]=None

T = TypeVar("T")

class BasePageableModel(BaseModel, Generic[T]):
    content: List[T]
    page: int
    size: int
    number_of_elements: int
    total_elements: int
    total_pages: int
    is_last: bool
    is_first: bool
    is_empty: bool