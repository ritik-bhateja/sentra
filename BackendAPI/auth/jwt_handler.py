import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

class JWTHandler:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_days = int(os.getenv("JWT_EXPIRATION_DAYS", 7))
    
    def create_token(self, user_id: int, email: str) -> str:
        """Generate JWT token"""
        expire = datetime.utcnow() + timedelta(days=self.expiration_days)
        payload = {
            "sub": str(user_id),
            "email": email,
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
