from functools import wraps
from typing import Any, Callable, List, Optional

from fastapi import HTTPException, status

from app.models.user import RoleType, User


class PermissionChecker:
    def __init__(self, allowed_roles: List[RoleType]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User) -> bool:
        return True


def require_roles(*roles: RoleType) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user: Optional[User] = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def check_school_access(user: User, school_id: str) -> None:
    if str(user.school_id) != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this school's resources",
        )
