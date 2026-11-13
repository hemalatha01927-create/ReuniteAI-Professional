import os
import click
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import current_user
from .extensions import orm, login_manager, csrf, limiter
from .models import User


def create_app(config_object=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object or "config.Config")
    # Trust only the single reverse proxy layer used by the hosting platform.
    if app.config.get("IS_PRODUCTION"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    orm.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        return orm.session.get(User, int(user_id))

    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .cases.routes import bp as cases_bp
    from .admin.routes import bp as admin_bp
    from .notifications.routes import bp as notifications_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cases_bp, url_prefix="/cases")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok"), 200

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if app.config.get("IS_PRODUCTION"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.context_processor
    def inject_navigation_data():
        if current_user.is_authenticated:
            from .models import Notification
            unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        else:
            unread = 0
        return {
            "unread_notifications": unread,
            "public_intake_enabled": app.config["PUBLIC_INTAKE_ENABLED"],
            "public_registration_enabled": app.config["PUBLIC_REGISTRATION_ENABLED"],
            "uploads_enabled": app.config["UPLOADS_ENABLED"],
        }

    @app.errorhandler(413)
    def too_large(_error):
        from flask import flash, redirect, url_for
        flash("Image too large. Maximum upload size is 5 MB.", "error")
        return redirect(url_for("cases.create_case"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.cli.command("init-db")
    def init_db_command():
        """Create all database tables."""
        orm.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Full name")
    @click.option("--email", prompt="Email")
    def create_admin_command(name, email):
        """Create the first administrator interactively; no default account exists."""
        from werkzeug.security import generate_password_hash
        from getpass import getpass
        orm.create_all()
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise click.ClickException("An account with this email already exists.")
        password = getpass("Create a strong password (12+ characters): ")
        confirm = getpass("Confirm password: ")
        if password != confirm or len(password) < 12:
            raise click.ClickException("Passwords must match and contain at least 12 characters.")
        user = User(full_name=name.strip(), email=email, role="admin", password_hash=generate_password_hash(password))
        orm.session.add(user)
        orm.session.commit()
        click.echo(f"Administrator account created for {email}.")

    @app.cli.command("create-tables")
    def create_tables_command():
        orm.create_all()
        click.echo("Database initialized successfully.")

    return app
