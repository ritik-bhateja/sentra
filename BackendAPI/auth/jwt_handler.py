import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

from auth.roles import DEFAULT_ROLE


class JWTHandler:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_days = int(os.getenv("JWT_EXPIRATION_DAYS", 7))
    
    def create_token(self, user_id: int, email: str, role: str = DEFAULT_ROLE.value) -> str:
        """Generate JWT token with role claim.

        Args:
            user_id: The user's database ID.
            email: The user's email address.
            role: The user's Sentra role value. Defaults to the least-privilege
                  role (viewer_without_query) when not specified.

        The role claim carries the user's resolved Keycloak role so that every
        subsequent request can read the role from the JWT without an additional
        Keycloak call (Requirements 6.1, 6.2, 6.4, 6.5).
        """
        expire = datetime.utcnow() + timedelta(days=self.expiration_days)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

jwt_handler = JWTHandler()
