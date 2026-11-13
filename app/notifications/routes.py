from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..extensions import orm
from ..models import Notification

bp = Blueprint("notifications", __name__)

@bp.route("/")
@login_required
def index():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return render_template("notifications.html", page_title="Notifications", items=items)

@bp.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    item = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    item.is_read = True
    orm.session.commit()
    return redirect(item.url or url_for("notifications.index"))

@bp.post("/read-all")
@login_required
def read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    orm.session.commit()
    return redirect(url_for("notifications.index"))
