from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from ..models import Case, Lead, MatchSuggestion, Notification
from ..extensions import orm

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    active_missing = Case.query.filter_by(report_type="missing", status="active").count()
    active_found = Case.query.filter_by(report_type="found", status="active").count()
    return render_template("landing.html", page_title="A trusted path to reunification", active_missing=active_missing, active_found=active_found)

@bp.route("/dashboard")
@login_required
def dashboard():
    my_cases = Case.query.filter_by(reporter_id=current_user.id).order_by(Case.created_at.desc()).limit(6).all()
    my_case_count = Case.query.filter_by(reporter_id=current_user.id).count()
    my_leads = Lead.query.filter_by(submitted_by_id=current_user.id).count()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    if current_user.has_role("admin", "reviewer", "officer"):
        pending_count = Case.query.filter_by(status="pending_review").count()
        match_count = MatchSuggestion.query.filter_by(status="pending").count()
        review_queue = Case.query.filter(Case.status.in_(["pending_review", "under_review"])).order_by(Case.created_at.asc()).limit(5).all()
    else:
        pending_count = Case.query.filter_by(reporter_id=current_user.id, status="pending_review").count()
        my_case_ids = orm.session.query(Case.id).filter_by(reporter_id=current_user.id)
        match_count = MatchSuggestion.query.filter(
            MatchSuggestion.status == "pending",
            or_(MatchSuggestion.case_a_id.in_(my_case_ids), MatchSuggestion.case_b_id.in_(my_case_ids))
        ).count()
        review_queue = []
    latest_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", page_title="Overview", my_cases=my_cases, my_case_count=my_case_count,
                           my_leads=my_leads, pending_count=pending_count, match_count=match_count,
                           unread_count=unread_count, review_queue=review_queue, latest_notifications=latest_notifications)
