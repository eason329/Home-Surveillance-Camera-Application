from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from datetime import timedelta

from src.account.models import User
from src import bcrypt, db
from .forms import FormRegister, FormLogin, FormChange, FormActivate, FormDelete, FormResetPassword, FormReset, FormTwoFactor
from src.mail.sendmail import send_mail
from decouple import config
from src.utils import get_b64_qr_image
import pyotp

account = Blueprint("account", __name__)


@account.route("/register", methods=["GET", "POST"])
@login_required
def register():
    form = FormRegister(request.form)
    if form.validate():
        token = User.create_reset_token(form.username.data, form.email.data)
        send_mail(sender='sender@ee.net',
                  recipients=[form.email.data],
                  subject='Home Surveillance Camera: Activate your account',
                  template='mail/activate',
                  mailtype='html',
                  token=token)
        flash("An activation email was sent to the new user.", "success")
        return redirect(url_for("account.register"))

    return render_template("account/register.html", form=form)


@account.route('/login', methods=['GET', 'POST'])
def login():
    form = FormLogin(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and not user.is_locked:
            user.lock_counter = 0
            db.session.commit()
            login_user(user, duration=timedelta(minutes=30))
            if user.is_2FA_enabled:
                return redirect(url_for("account.verify_2fa"))
            else:
                flash(current_user.username + ", You are now logged in.", "success")
                last_login_user = form.username.data
                return redirect(url_for("main.home"))
        else:
            if user:
                if user.is_locked:
                    flash("Your account is locked. Please reset your password to unlock.", "danger")
                elif (user.lock_counter > 9):
                    user.lock_counter = 0
                    user.is_locked = True
                    db.session.commit()
                    flash("Your account is locked. Please reset your password to unlock.", "danger")
                else:
                    flash("Invalid username and/or password.", "danger")
                    user.lock_counter += 1
                    db.session.commit()
            else:
                flash("Invalid username and/or password.", "danger")
            
    return render_template("account/login.html", form=form)


@account.route("/logout")
@login_required
def logout():
    flash(current_user.username+", You were logged out.", "success")
    user = User.query.filter_by(username=current_user.username).first()
    logout_user()
    user.is_2FA_verified = False
    db.session.commit()
    return redirect(url_for("account.login"))


@account.route("/change", methods=['GET', 'POST'])
@login_required
def change():
    form = FormChange(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        if user and bcrypt.check_password_hash(user.password, form.curPassword.data):
            change = False
            if form.newEmail.data:
                user.email = form.newEmail.data
                db.session.commit()
                change = True
            if form.newPassword.data:
                user.password = bcrypt.generate_password_hash(form.newPassword.data)
                db.session.commit()
                change = True
            if change:
                flash("Your account details changed!", "success")
                return redirect(url_for("main.settings"))
            else:
                flash("Please enter account details you want to update", "danger")
        else:
            flash("Invalid  password.", "danger")
            return render_template("account/change.html", form=form)
        
    return render_template("account/change.html", form=form)


@account.route("/delete", methods=["GET", "POST"])
def delete():
    form = FormDelete(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            flash("You deleted your account.", "success")
            logout_user()
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for("account.login"))
        else:
            flash("Invalid  password.", "danger")
        
    return render_template("account/delete.html", form=form)


@account.route("/activate", methods=["GET", "POST"])
def activate():
    data = User.query.filter_by(is_admin=True).count()
    form = FormActivate(request.form)
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=bcrypt.generate_password_hash(form.password.data))
        token = user.create_activate_token()
        send_mail(sender='sender@ee.net',
                  recipients=[form.email.data],
                  subject='Home Surveillance Camera: Activate your account',
                  template='mail/admin_activate',
                  mailtype='html',
                  user=user,
                  token=token)
        flash("Please check your email to activate.", "success")

    return render_template("account/activate.html", form=form, data=data)


@account.route('/activate_confirm/<token>', methods=["GET", "POST"])
def activate_confirm(token):
    data = User.validate_token(token)
    if data:
        user = User(username=data.get("username"), email=data.get("email"), password=data.get("password"), is_admin=True)
        db.session.add(user)
        db.session.commit()
        flash("Thank you for your activation.", "success")
    else:
        flash("Error occured during activation.", "danger")
        
    return redirect(url_for("account.login"))


@account.route("/reset", methods=["GET", "POST"])
def reset():
    form = FormReset(request.form)
    if form.is_submitted():
        user = User.query.filter_by(username=form.username.data).first()
        if (user.email != form.email.data):
            flash("Email not match to your account.", "danger")
            return render_template("account/reset.html", form=form)
        token = User.create_reset_token(form.username.data, form.email.data)
        send_mail(sender='sender@ee.net',
                  recipients=[form.email.data],
                  subject='Home Surveillance Camera: Reset your password',
                  template='mail/activate',
                  mailtype='html',
                  token=token)
        flash("Please check your email.", "success")
        return redirect(url_for("account.reset"))
    return render_template("account/reset.html", form=form)


@account.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    data = User.validate_token(token)
    form = FormResetPassword(request.form)
    if data:
        if form.validate_on_submit():
            if (User.query.filter_by(username=data.get("username")).count() == 0):
                user = User(username=data.get("username"), email=data.get("email"), password=bcrypt.generate_password_hash(form.password.data))
                db.session.add(user)
                db.session.commit()
                flash("Thank you for your activation.", "success")
                return redirect(url_for("account.login"))
            else:
                user = User.query.filter_by(username=data.get("username")).first()
                user.password = bcrypt.generate_password_hash(form.password.data)
                user.is_2FA_enabled = False
                db.session.commit()
                flash("You changed your password.", "success")
                return redirect(url_for("account.login"))
    else:
        flash("Error occured during activation.", "danger")
        return redirect(url_for("account.login"))
        
    return render_template("account/reset_password.html", form=form, data=data)

@account.route('/setup-2fa')
@login_required
def setup_2fa():
    user = User.query.filter_by(username=current_user.username).first()
    user.token = pyotp.random_base32()
    db.session.commit()
    uri = current_user.get_2FA_setup_uri()
    secret_token = current_user.token
    b64_qr = get_b64_qr_image(uri)
    return render_template('account/setup-2fa.html', secret=secret_token, qr_image=b64_qr)

@account.route('/verify-setup-2fa', methods=["GET", "POST"])
@login_required
def verify_setup_2fa():
    form = FormTwoFactor(request.form)
    if form.validate_on_submit():
        if current_user.is_otp_valid(form.otp.data):
            try:
                current_user.is_2FA_enabled = True
                current_user.is_2FA_verified = True
                db.session.commit()
                flash("2FA setup successful.!", "success")
                return redirect(url_for("main.settings"))
            except Exception:
                db.session.rollback()
                flash("2FA setup failed. Please try again.", "danger")
                return redirect(url_for("account.verify_setup_2fa"))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for("account.verify_setup_2fa"))
    else:
        return render_template("account/verify-setup-2fa.html", form=form)


@account.route('/verify-2fa', methods=["GET", "POST"])
@login_required
def verify_2fa():
    form = FormTwoFactor(request.form)
    if form.validate_on_submit():
        if current_user.is_otp_valid(form.otp.data):
            current_user.is_2FA_verified = True
            db.session.commit()
            flash("2FA verification successful. You are logged in!", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for("account.verify_2fa"))
    else:
        return render_template("account/verify-2fa.html", form=form)
    
@account.route('/disable-2fa')
@login_required
def disable_2fa():
    current_user.is_2FA_verified = False
    current_user.is_2FA_enabled = False
    db.session.commit()
    flash("2FA verification successfully disabled!", "success")
    return redirect(url_for("main.settings"))
