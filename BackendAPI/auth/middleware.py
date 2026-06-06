from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from models_v3 import User
from auth.jwt_handler import jwt_handler
from auth.roles import Role, coerce_role


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT from cookie, return current user.

    Resolves the user's role from the JWT 'role' claim and attaches it as a
    transient attribute (current_user.role). The role is never read from or
    written to RDS — it comes exclusively from the JWT claim, which was set
    during the OAuth callback from Keycloak (Requirements 7.1, 7.4).
    """

    token = request.cookies.get("sentra_jwt_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = jwt_handler.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Attach role from JWT claim as a transient per-request attribute.
    # Missing or invalid claims resolve to DEFAULT_ROLE (Req 6.3, 7.1, 10.2, 12.2).
    user.role = coerce_role(payload.get("role"))

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that enforces admin-only access.

    Returns the current user if their role is admin; otherwise raises
    HTTP 403 Forbidden (Requirements 9.2, 9.3, 9.4, 9.5).
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation"
        )
    return current_user
