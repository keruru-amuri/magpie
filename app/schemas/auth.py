"""
Authentication schemas for the MAGPIE platform.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = UserRole.GUEST
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator("password")
    def password_strength(cls, v):
        """Validate password strength."""
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one special character
        special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")
        
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
    @validator("password")
    def password_strength(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
            
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one special character
        special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")
        
        return v


class UserInDB(UserBase):
    """User in database schema."""
    
    id: int
    hashed_password: str
    is_superuser: bool = False
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class UserResponse(UserBase):
    """User response schema."""
    
    id: int
    is_superuser: bool = False
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class Token(BaseModel):
    """Token schema."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    
    sub: Optional[str] = None
    exp: Optional[int] = None
    scopes: Optional[list] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator("new_password")
    def password_strength(cls, v):
        """Validate password strength."""
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for at least one special character
        special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character")
        
        return v
