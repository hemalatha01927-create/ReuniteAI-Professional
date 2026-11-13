import re
from urllib.parse import urlparse
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_user, logout_user, current_user, login_required
from ..extensions import orm, limiter
from ..models import User

bp = Blueprint("auth", __name__)

@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def register():
    if not current_app.config["PUBLIC_REGISTRATION_ENABLED"]:
        abort(404)
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or len(name) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter your name and a valid email address.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please sign in.", "error")
        elif len(password) < 12 or password != confirm:
            flash("Passwords must match and contain at least 12 characters.", "error")
        else:
            user = User(full_name=name, email=email, phone=phone or None, role="member")
            user.set_password(password)
            orm.session.add(user)
            orm.session.commit()
            login_user(user)
            flash("Your account is ready. You can now submit and follow reports.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html", page_title="Create account")

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("8 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.is_active and user.check_password(password):
            user.last_login_at = datetime.now(timezone.utc)
            orm.session.commit()
            login_user(user, remember=request.form.get("remember") == "on")
            flash("Welcome back.", "success")
            next_url = request.args.get("next", "")
            parsed = urlparse(next_url)
            if parsed.scheme or parsed.netloc or not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("main.dashboard")
            return redirect(next_url or url_for("main.dashboard"))
        flash("Email or password is incorrect, or the account is inactive.", "error")
    return render_template("auth/login.html", page_title="Sign in")

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))

@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip()[:100]
        current_user.phone = request.form.get("phone", "").strip()[:30] or None
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if new_password:
            old_password = request.form.get("current_password", "")
            if not current_user.check_password(old_password):
                flash("Current password is incorrect.", "error")
                return render_template("auth/profile.html", page_title="My profile")
            if len(new_password) < 12 or new_password != confirm:
                flash("New passwords must match and contain at least 12 characters.", "error")
                return render_template("auth/profile.html", page_title="My profile")
            current_user.set_password(new_password)
        orm.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html", page_title="My profile")
