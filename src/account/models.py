from datetime import datetime

from flask_login import UserMixin, current_user
from itsdangerous import SignatureExpired, BadSignature, TimedJSONWebSignatureSerializer
import pyotp

from src import bcrypt, db
from config import Config


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    lock_counter = db.Column(db.Integer, nullable=False, default=0)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_2FA_enabled = db.Column(db.Boolean, nullable=False, default=False)
    is_2FA_verified = db.Column(db.Boolean, nullable=False, default=False)
    token = db.Column(db.String)

    def __init__(self, username, email, password, is_admin=False, is_2FA_verified=False):
        self.username = username
        self.email = email
        self.password = password
        self.created_on = datetime.now()
        self.is_admin = is_admin
        self.is_2FA_verified = is_2FA_verified
        '''self.is_locked = is_locked'''
        self.token = pyotp.random_base32()
        
        
    def get_2FA_setup_uri(self):
        return pyotp.totp.TOTP(self.token).provisioning_uri(
            name=self.username, issuer_name=Config.APP_NAME)
    
    def is_otp_valid(self, user_otp):
        totp = pyotp.parse_uri(self.get_2FA_setup_uri())
        return totp.verify(user_otp)
    
    def create_activate_token(self, expires_time=3600):
        s = TimedJSONWebSignatureSerializer(Config.SECRET_KEY, expires_in=expires_time)
        return s.dumps({'username': self.username, 'email': self.email, 'password': self.password.decode("utf-8")})

    def create_reset_token(username, email, expires_time=3600):
        s = TimedJSONWebSignatureSerializer(Config.SECRET_KEY, expires_in=expires_time)
        return s.dumps({'username': username, 'email': email})
    
    def validate_token(token):
        s = TimedJSONWebSignatureSerializer(Config.SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return False
        except BadSignature:
            return False
        return data

    def __repr__(self):
        return f"<username {self.username}>"
