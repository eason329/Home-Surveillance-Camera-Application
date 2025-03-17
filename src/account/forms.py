from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from src import bcrypt
from src.account.models import User

class FormLogin(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class FormRegister(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email(message=None), Length(min=6, max=40)])
    
    def validate(self, extra_validators=None):
        initial_validation = super(FormRegister, self).validate(extra_validators)
        user = User.query.filter_by(username=self.username.data).first()
        email = User.query.filter_by(email=self.email.data).first()
        if not initial_validation:
            return False
        if user:
            self.username.errors.append("Username already registered")
            return False
        if email:
            self.email.errors.append("Email already used")
            return False
        return True


class FormChange(FlaskForm):
    curPassword = PasswordField("Current Password", validators=[DataRequired()])
    newEmail = EmailField("New Email")
    newPassword = PasswordField(
        "New Password", validators=[Optional(), Length(min=6, max=25)]
    )
    newConfirm = PasswordField(
        "Repeat password",
        validators=[
            EqualTo("newPassword", message="Passwords must match."),
        ],
    )
    
    def validate(self, extra_validators=None):
        initial_validation = super(FormChange, self).validate(extra_validators)
        if not initial_validation:
            return False
        user = User.query.filter_by(password=bcrypt.generate_password_hash(self.curPassword.data)).first()
        if self.curPassword.data == self.newPassword.data:
            self.newPassword.errors.append("New password can't be same as old password!")
            return False
        if self.newPassword.data != self.newConfirm.data:
            self.newConfirm.errors.append("Passwords must match")
            return False
        return True


class FormActivate(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired()], default="admin"
    )
    email = EmailField(
        "Email", validators=[DataRequired(), Email(message=None), Length(min=6, max=40)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=25)]
    )
    confirm = PasswordField(
        "Repeat password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    
    def validate(self, extra_validators=None):
        initial_validation = super(FormActivate, self).validate(extra_validators)
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        email = User.query.filter_by(email=self.email.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False
        if email:
            self.email.errors.append("Email already used")
            return False
        if self.password.data != self.confirm.data:
            self.password.errors.append("Passwords must match")
            return False
        return True


class FormDelete(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])


class FormReset(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email(message=None), Length(min=6, max=40)])
    
    def validate(self, extra_validators=None):
        initial_validation = super(FormReset, self).validate(extra_validators)
        user = User.query.filter_by(username=self.username.data).first()
        email = User.query.filter_by(email=self.email.data).first()
        '''if not initial_validation:
            return False'''
        if user:
            self.username.errors.append("Username already registered")
            return False
        if email:
            self.email.errors.append("Email already used")
            return False
        return True


class FormResetPassword(FlaskForm):
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=25)]
    )
    confirm = PasswordField(
        "Repeat password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    
    def validate(self, extra_validators=None):
        initial_validation = super(FormResetPassword, self).validate(extra_validators)
        if not initial_validation:
            return False
        if self.password.data != self.confirm.data:
            self.password.errors.append("Passwords must match")
            return False
        return True

class FormTwoFactor(FlaskForm):
    otp = StringField('Enter OTP', validators=[
                      DataRequired(), Length(min=6, max=6)])
