from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token, verify_token
from app.schemas.schemas import OTPRequest, OTPVerify, LoginResponse, UserResponse, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.models.database import User

router = APIRouter()


@router.post("/send-otp", tags=["Authentication"])
async def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """
    Send OTP to email address
    """
    success, message = AuthService.send_otp_to_email(db, request.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message,
        "email": request.email
    }


@router.post("/verify-otp", response_model=LoginResponse, tags=["Authentication"])
async def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP and return authentication tokens
    """
    success, message, user = AuthService.verify_otp(db, request.email, request.code)
    
    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Generate tokens
    tokens = AuthService.generate_tokens(user.id)
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=UserResponse.from_orm(user),
        expires_in=tokens["expires_in"]
    )


@router.post("/refresh-token", tags=["Authentication"])
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    if not verify_token(request.refresh_token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Decode token to get user_id
    payload = decode_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = int(payload.get("sub"))
    
    # Generate new token
    new_tokens = AuthService.refresh_access_token(db, user_id)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "access_token": new_tokens["access_token"],
        "token_type": new_tokens["token_type"],
        "expires_in": new_tokens["expires_in"]
    }


def get_current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> User:
    """
    Get current authenticated user from the Authorization header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.split(" ", 1)[1]

    if not verify_token(token, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user
