"""
Authentication and authorization middleware for RAG API
Implements API key-based authentication with role-based access control
"""

from fastapi import Security, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, List
import hashlib
import secrets
import json
from pathlib import Path
from datetime import datetime, timedelta

# API Key storage (in production, use database)
API_KEYS_FILE = Path("/app/data/api_keys.json")
API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# User roles and permissions
ROLES = {
    "admin": {
        "permissions": ["read", "write", "delete", "manage_users"],
        "rate_limit": None  # Unlimited
    },
    "developer": {
        "permissions": ["read", "write"],
        "rate_limit": 1000  # requests per hour
    },
    "viewer": {
        "permissions": ["read"],
        "rate_limit": 100
    }
}

class APIKeyManager:
    """Manage API keys and authentication"""
    
    def __init__(self, keys_file: Path = API_KEYS_FILE):
        self.keys_file = keys_file
        self.keys = self._load_keys()
    
    def _load_keys(self) -> Dict:
        """Load API keys from file"""
        if self.keys_file.exists():
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_keys(self):
        """Save API keys to file"""
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
    
    def generate_key(self, user_id: str, role: str = "developer", 
                     expires_days: Optional[int] = None) -> str:
        """Generate a new API key"""
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}")
        
        # Generate secure random key
        api_key = f"cai_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Calculate expiration
        expiration = None
        if expires_days:
            expiration = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
        
        # Store key info
        self.keys[key_hash] = {
            "user_id": user_id,
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiration,
            "last_used": None,
            "usage_count": 0
        }
        
        self._save_keys()
        return api_key
    
    def validate_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return user info"""
        if not api_key or not api_key.startswith("cai_"):
            return None
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_info = self.keys.get(key_hash)
        
        if not key_info:
            return None
        
        # Check expiration
        if key_info.get("expires_at"):
            expiry = datetime.fromisoformat(key_info["expires_at"])
            if datetime.utcnow() > expiry:
                return None
        
        # Update usage stats
        key_info["last_used"] = datetime.utcnow().isoformat()
        key_info["usage_count"] = key_info.get("usage_count", 0) + 1
        self._save_keys()
        
        return key_info
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if key_hash in self.keys:
            del self.keys[key_hash]
            self._save_keys()
            return True
        return False
    
    def list_keys(self, user_id: Optional[str] = None) -> List[Dict]:
        """List all API keys, optionally filtered by user"""
        keys = []
        for key_hash, info in self.keys.items():
            if user_id is None or info["user_id"] == user_id:
                keys.append({
                    "key_hash": key_hash[:16] + "...",  # Partial hash for identification
                    **info
                })
        return keys

# Global key manager instance
key_manager = APIKeyManager()

async def get_api_key(api_key: str = Security(api_key_header)) -> Dict:
    """Dependency to validate API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    key_info = key_manager.validate_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )
    
    return key_info

def require_permission(permission: str):
    """Dependency factory to check for specific permission"""
    async def check_permission(key_info: Dict = Depends(get_api_key)):
        role = key_info.get("role")
        if role not in ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role"
            )
        
        if permission not in ROLES[role]["permissions"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        
        return key_info
    
    return check_permission

def require_role(allowed_roles: List[str]):
    """Dependency factory to check for specific role"""
    async def check_role(key_info: Dict = Depends(get_api_key)):
        role = key_info.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role not authorized. Required: {', '.join(allowed_roles)}"
            )
        
        return key_info
    
    return check_role

# Rate limiting (simple implementation)
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}  # {key_hash: {timestamp: count}}
    
    def check_rate_limit(self, key_info: Dict) -> bool:
        """Check if request is within rate limit"""
        role = key_info.get("role")
        rate_limit = ROLES[role].get("rate_limit")
        
        if rate_limit is None:  # Unlimited
            return True
        
        user_id = key_info["user_id"]
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        if user_id not in self.requests:
            self.requests[user_id] = {}
        
        # Clean old entries
        self.requests[user_id] = {
            ts: count for ts, count in self.requests[user_id].items()
            if datetime.fromisoformat(ts) >= current_hour - timedelta(hours=1)
        }
        
        # Count requests in current hour
        hour_key = current_hour.isoformat()
        current_count = self.requests[user_id].get(hour_key, 0)
        
        if current_count >= rate_limit:
            return False
        
        # Increment counter
        self.requests[user_id][hour_key] = current_count + 1
        return True

rate_limiter = RateLimiter()

async def check_rate_limit(key_info: Dict = Depends(get_api_key)):
    """Dependency to check rate limits"""
    if not rate_limiter.check_rate_limit(key_info):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return key_info