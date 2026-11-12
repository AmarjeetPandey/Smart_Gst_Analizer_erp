import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import User, OTP
from app.core.security import create_access_token, create_refresh_token
from app.core.config import get_settings
from app.services.email_service import EmailService

settings = get_settings()


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def generate_otp(length: int = None) -> str:
        """Generate random OTP"""
        if length is None:
            length = settings.OTP_LENGTH
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def send_otp_to_email(db: Session, email: str) -> tuple[bool, str]:
        """Generate and send OTP to email"""
        try:
            # Generate OTP
            otp_code = AuthService.generate_otp()
            
            # Get or create user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email, name=email.split('@')[0])
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Clear previous unused OTPs
            db.query(OTP).filter(
                OTP.email == email,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()
            ).delete()
            
            # Create new OTP record
            otp_record = OTP(
                user_id=user.id,
                email=email,
                code="",
                code_hash=hashlib.sha256(otp_code.encode("utf-8")).hexdigest(),
                expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            )
            db.add(otp_record)
            db.commit()
            
            # Send email
            email_sent = EmailService.send_otp_email(email, otp_code)
            
            # In development, allow login even if email fails
            if settings.ENVIRONMENT == "development":
                print(f"[DEV MODE] OTP for {email}: {otp_code}")
                return True, f"OTP sent successfully (Dev: {otp_code})"
            
            if email_sent:
                return True, "OTP sent successfully"
            else:
                return False, "Failed to send OTP email"
        
        except Exception as e:
            print(f"Error in send_otp_to_email: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def verify_otp(db: Session, email: str, otp_code: str) -> tuple[bool, str, User]:
        """Verify OTP and return user"""
        try:
            # Find valid OTP
            otp_record = db.query(OTP).filter(
                OTP.email == email,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow(),
                OTP.attempts < settings.OTP_MAX_ATTEMPTS,
            ).order_by(OTP.created_at.desc()).first()
            
            if not otp_record:
                return False, "Invalid or expired OTP", None

            expected_hash = otp_record.code_hash or hashlib.sha256(otp_record.code.encode("utf-8")).hexdigest()
            supplied_hash = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()
            if not hmac.compare_digest(expected_hash, supplied_hash):
                otp_record.attempts += 1
                db.commit()
                return False, "Invalid or expired OTP", None
            
            # Mark as used
            otp_record.is_used = True
            db.commit()
            
            # Get user
            user = db.query(User).filter(User.id == otp_record.user_id).first()
            if not user:
                return False, "User not found", None
            
            # Mark email as verified
            user.is_email_verified = True
            user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            return True, "OTP verified successfully", user
        
        except Exception as e:
            print(f"Error in verify_otp: {str(e)}")
            return False, str(e), None
    
    @staticmethod
    def generate_tokens(user_id: int) -> dict:
        """Generate access and refresh tokens"""
        data = {"sub": str(user_id)}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def refresh_access_token(db: Session, user_id: int) -> dict:
        """Refresh access token"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            data = {"sub": str(user_id)}
            access_token = create_access_token(data)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        except Exception as e:
            print(f"Error in refresh_access_token: {str(e)}")
            return None
    
