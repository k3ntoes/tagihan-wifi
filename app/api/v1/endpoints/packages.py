"""
Package API endpoints (Controller Layer).

Endpoints:
- POST /packages - Create new package (admin only)
- GET /packages - List all packages
- GET /packages/{id} - Get package by ID
- PUT /packages/{id} - Update package (admin only)
- DELETE /packages/{id} - Delete package (admin only)
"""

from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_user, require_role
from app.db.database import Database, get_db
from app.schemas import PackageCreate, PackageUpdate, SinglePackageResponse, PaginatedPackageResponse
from app.services import PackageService

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("", response_model=SinglePackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    package_data: PackageCreate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Create a new package (admin only).

    Args:
        package_data: Package details (name, speed, price)
        db: Database instance
        current_user: Authenticated admin user

    Returns:
        Created package details

    Raises:
        HTTPException 400: Package name already exists
        HTTPException 500: Database error
    """
    service = PackageService(db)
    package = service.create_package(package_data)
    return SinglePackageResponse(data=package)


@router.get("", response_model=PaginatedPackageResponse)
async def list_packages(
    page: int = 1,
    per_page: int = 10,
    name: str = None,
    min_speed: int = None,
    max_speed: int = None,
    min_price: int = None,
    max_price: int = None,
    include_inactive: bool = False,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all packages with optional filters and pagination.

    Supports filtering by:
    - name: Partial match on package name (case-insensitive)
    - min_speed/max_speed: Speed range in Mbps
    - min_price/max_price: Price range in Rupiah
    - include_inactive: Include inactive packages

    Pagination:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)

    Returns:
        Paginated list of packages matching filters
    """
    service = PackageService(db)
    data, meta = service.list_packages(
        page=page,
        per_page=per_page,
        name=name,
        min_speed=min_speed,
        max_speed=max_speed,
        min_price=min_price,
        max_price=max_price,
        include_inactive=include_inactive,
    )
    return PaginatedPackageResponse(data=data, meta=meta)


@router.get("/{package_id}", response_model=SinglePackageResponse)
async def get_package(
    package_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get package by ID (sqid).

    Args:
        package_id: Package sqid
        db: Database instance
        current_user: Authenticated user

    Returns:
        Package details

    Raises:
        HTTPException 404: Package not found
        HTTPException 400: Invalid sqid
    """
    service = PackageService(db)
    package = service.get_package_by_id(package_id)
    return SinglePackageResponse(data=package)


@router.put("/{package_id}", response_model=SinglePackageResponse)
async def update_package(
    package_id: str,
    package_data: PackageUpdate,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Update package (admin only).

    Args:
        package_id: Package sqid
        package_data: Updated package details
        db: Database instance
        current_user: Authenticated admin user

    Returns:
        Updated package details

    Raises:
        HTTPException 404: Package not found
        HTTPException 400: Package name already exists or invalid sqid
    """
    service = PackageService(db)
    package = service.update_package(package_id, package_data)
    return SinglePackageResponse(data=package)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: str,
    db: Database = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Delete package (soft delete by setting is_active to false) - admin only.

    Args:
        package_id: Package sqid
        db: Database instance
        current_user: Authenticated admin user

    Raises:
        HTTPException 404: Package not found
        HTTPException 400: Package is in use by customers or invalid sqid
    """
    service = PackageService(db)
    service.delete_package(package_id)
    return None
