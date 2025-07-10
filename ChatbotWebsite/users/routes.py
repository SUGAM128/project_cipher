from flask import (
    current_app,
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,
    flash,
    redirect,
)
from flask_login import login_user, current_user, logout_user, login_required
from flask import session


from ChatbotWebsite import db, bcrypt
from ChatbotWebsite.models import User, ChatMessage, Journal
from ChatbotWebsite.users.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    RequestResetForm,
    ResetPasswordForm,
)
from ChatbotWebsite.users.utils import save_picture, send_reset_email
import os
import random
from .utils import send_otp_email


users = Blueprint("users", __name__)

from flask import request, jsonify
import random

@users.route('/send_otp', methods=['POST']) # Only if CSRF protection is on, and not using CSRF token
def send_otp_ajax():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify(success=False), 400

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['reg_email'] = email

    try:
        send_otp_email(email, otp)  # Your function to send OTP email
        return jsonify(success=True)
    except Exception as e:
        print("OTP send error:", e)
        return jsonify(success=False)



# register page/route
@users.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        entered_otp = form.otp.data.strip()
        session_otp = session.get('otp')
        session_email = session.get('reg_email')

        # Check email matches session email (optional)
        if form.email.data != session_email:
            flash('Email does not match the OTP email.', 'danger')
            return render_template('register.html', form=form, show_otp=True)

        if session_otp is None:
            flash('OTP expired or not sent. Please try again.', 'danger')
            return render_template('register.html', form=form, show_otp=True)

        if entered_otp != session_otp:
            flash('Incorrect OTP. Please try again.', 'danger')
            return render_template('register.html', form=form, show_otp=True)

        # OTP correct - proceed to register user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        # Clear OTP session
        session.pop('otp', None)
        session.pop('reg_email', None)

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('users.login'))

    return render_template('register.html', form=form, show_otp=False)

# login page/route
@users.route("/login", methods=["GET", "POST"])
def login():
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    form = LoginForm()  # create login form
    if (
        form.validate_on_submit()
    ):  # if form is submitted, check if user exists and password is correct
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("You have been logged in!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        else:
            flash("Login Unsuccessful. Please check email and password!", "danger")
    return render_template("login.html", title="Login", form=form)


# account page/route
@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()  # form to update account
    if form.validate_on_submit():
        if form.picture.data:
            old_picture = current_user.profile_image
            picture_file = save_picture(form.picture.data)
            current_user.profile_image = picture_file
            if old_picture != "default.jpg":
                os.remove(
                    os.path.join(
                        current_app.root_path, "static/profile_images", old_picture
                    )
                )
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template("account.html", title="Account", form=form)


# logout route
@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))


# delete conversation route
@users.route("/delete_conversation", methods=["POST"])
def delete_conversation():
    if current_user.is_authenticated:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).all()
        for message in messages:
            db.session.delete(message)
        db.session.commit()
        flash("Your conversation has been deleted!", "success")
    return redirect(url_for("users.account"))


# delete account route
@users.route("/delete_account", methods=["POST"])
def delete_account():
    if current_user.is_authenticated:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).all()
        for message in messages:
            db.session.delete(message)
        journals = Journal.query.filter_by(user_id=current_user.id).all()
        for journal in journals:
            db.session.delete(journal)
        db.session.delete(current_user)
        db.session.commit()
        flash("Your account has been deleted!", "success")
    return redirect(url_for("users.logout"))


# reset password route to request a password reset token
@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    form = RequestResetForm()  # create request reset form
    if form.validate_on_submit():  # if form is submitted, send email with reset token
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        return redirect(url_for("users.login"))
    return render_template("reset_request.html", title="Reset Password", form=form)


# reset password route to reset password
@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if (
        current_user.is_authenticated
    ):  # if user is already logged in, redirect to home page
        return redirect(url_for("main.home"))
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("users.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(user.password, form.password.data):
            flash(
                "Your new password must be unique and different from your old password.",
                "warning",
            )
            return redirect(url_for("users.reset_token", token=token, _external=True))
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been updated!", "success")
        return redirect(url_for("users.login"))
    return render_template("reset_token.html", title="Reset Password", form=form)
