from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from models.models import User,PasswordResetOTP
from sqlalchemy.orm import Session
from config import settings
import random
from services.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    @staticmethod
    def get_user_by_email(db:Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_user(db:Session,user_data):
        hash_password = AuthService.hash_password(user_data.password)
        user = User(email=user_data.email, password=hash_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = AuthService.get_user_by_email(db, email)
        if not user:
            raise ValueError("Email không tồn tại")
        
        if user.failed_attempts >= 5 and user.lock_until and user.lock_until > datetime.utcnow():
            raise PermissionError("Tài khoản của bạn đã bị khóa. Vui lòng thử lại sau")
        
        if not AuthService.verify_password(password, user.password):
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.lock_until = datetime.utcnow() + timedelta(minutes=5)
            db.commit()
            raise ValueError("Sai mật khẩu")
        
        # Reset trạng thái khi đăng nhập thành công
        user.failed_attempts = 0
        user.lock_until = None
        db.commit()

        # Tạo và trả về token
        return AuthService.create_access_token(data={"sub": str(user.id)})

    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    @staticmethod
    def send_reset_password_email(db:Session, email: str):
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return False
        return True  
    @staticmethod
    def handle_reset_password_request(email:str, db:Session):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        
        otp = str(random.randint(100000, 999999))
        otp_entry = PasswordResetOTP(
            user_id=user.id,
            otp=otp,
            purpose="reset_password",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_used=False
        )
        # Vô hiệu hóa các OTP cũ
        db.query(PasswordResetOTP).filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.purpose == "reset_password",
            PasswordResetOTP.is_used == False
        ).update({PasswordResetOTP.is_used: True})
        db.add(otp_entry)
        db.commit()

        email_body_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset OTP</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; line-height: 1.6;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <img src="https://blog.lowlevelforest.com/wp-content/uploads/2024/06/openai-whisper-%EC%8D%B8%EB%84%A4%EC%9D%BC-3.png" alt="Company Logo" style="max-width: 150px; margin-bottom: 20px;">
                            <h1 style="font-size: 24px; color: #333; margin: 0;">Password Reset</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px; text-align: center; color: #666;">
                            <p>You recently requested to reset your password. Use the verification code below to complete the process.</p>
                            <div style="background-color: #f0f0f0; border-radius: 6px; padding: 15px; display: inline-block; margin: 20px auto;">
                                <span style="font-size: 24px; letter-spacing: 4px; color: #333;">{otp}</span>
                            </div>
                            <p>This code will expire in 5 minutes. If you did not request this reset, please ignore this email.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px; text-align: center; font-size: 12px; color: #888;">
                            <p>© 2024 Your Company. All rights reserved.</p>
                            <p>This is an automated message. Please do not reply.</p>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
        """
        EmailService.send_email(
            recipient=user.email,
            subject="Password Reset OTP",
            body=email_body_html,
        )
    @staticmethod
    def handle_reset_password_verification(email:str,otp:str,new_password:str,db:Session):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        otp_entry = db.query(PasswordResetOTP).filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.otp == otp,
            PasswordResetOTP.purpose == "reset_password",
            PasswordResetOTP.expires_at > datetime.utcnow(),
            PasswordResetOTP.is_used == False
        ).first()
        if not otp_entry:
            raise ValueError("Invalid OTP")
        otp_entry.is_used = True
        db.commit()

        user.password = AuthService.hash_password(new_password)
        db.commit()
    