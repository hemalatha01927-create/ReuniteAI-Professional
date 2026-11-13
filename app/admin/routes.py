import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from ..extensions import orm
from ..models import Case, Lead, MatchSuggestion, FamilyVerification, User, Notification, AuditLog
from ..utils.matching import generate_suggestions

bp = Blueprint("admin", __name__)


def reviewer_required(view):
    from functools import wraps
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.has_role("admin", "reviewer", "officer"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    from functools import wraps
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.has_role("admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def audit(action, entity_type, entity_id=None, details=None):
    orm.session.add(AuditLog(actor_id=current_user.id, action=action, entity_type=entity_type,
                             entity_id=str(entity_id or ""), details=(details or "")[:500], ip_address=request.remote_addr))


@bp.route("/")
@reviewer_required
def dashboard():
    total = Case.query.count()
    pending = Case.query.filter_by(status="pending_review").count()
    active = Case.query.filter_by(status="active").count()
    resolved = Case.query.filter_by(status="resolved").count()
    new_leads = Lead.query.filter_by(status="new").count()
    pending_verifications = FamilyVerification.query.filter_by(status="pending").count()
    latest = Case.query.order_by(Case.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", page_title="Operations centre", total=total, pending=pending,
                           active=active, resolved=resolved, new_leads=new_leads,
                           pending_verifications=pending_verifications, latest=latest)


@bp.route("/queue")
@reviewer_required
def case_queue():
    cases = Case.query.filter(Case.status.in_(["pending_review", "under_review"])).order_by(Case.created_at.asc()).all()
    return render_template("admin/queue.html", page_title="Review queue", cases=cases)


@bp.post("/cases/<int:case_id>/status")
@reviewer_required
def update_case_status(case_id):
    case = Case.query.get_or_404(case_id)
    status = request.form.get("status", "")
    allowed = {"under_review", "active", "rejected", "resolved", "closed"}
    if status not in allowed:
        flash("Invalid case status.", "error")
    else:
        case.status = status
        case.reviewed_by_id = current_user.id
        case.reviewed_at = datetime.now(timezone.utc)
        if status == "resolved":
            case.resolved_at = datetime.now(timezone.utc)
        audit("case_status_changed", "case", case.id, f"Status={status}")
        orm.session.add(Notification(user_id=case.reporter_id, title="Case status updated", message=f"Your report {case.case_code} is now {status.replace('_', ' ')}.", url=url_for("cases.detail", case_id=case.id)))
        orm.session.commit()
        if status == "active":
            generate_suggestions(case)
            orm.session.commit()
        flash(f"{case.case_code} updated to {status.replace('_', ' ')}.", "success")
    return redirect(url_for("admin.case_queue"))


@bp.route("/matches")
@reviewer_required
def matches():
    items = MatchSuggestion.query.order_by(MatchSuggestion.score.desc(), MatchSuggestion.created_at.desc()).limit(200).all()
    for item in items:
        try:
            item.reasons = json.loads(item.reasons_json)
        except (ValueError, TypeError):
            item.reasons = []
    return render_template("admin/matches.html", page_title="Potential case links", items=items)


@bp.post("/matches/<int:match_id>/status")
@reviewer_required
def update_match(match_id):
    item = MatchSuggestion.query.get_or_404(match_id)
    status = request.form.get("status")
    if status not in ("reviewed", "dismissed"):
        flash("Invalid match review action.", "error")
    else:
        item.status = status
        audit("match_reviewed", "match", item.id, f"Status={status}")
        orm.session.commit()
        flash("Potential link updated. It is not a confirmed identity match.", "success")
    return redirect(url_for("admin.matches"))


@bp.route("/leads")
@reviewer_required
def leads():
    items = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template("admin/leads.html", page_title="Community leads", items=items)


@bp.post("/leads/<int:lead_id>/status")
@reviewer_required
def update_lead(lead_id):
    item = Lead.query.get_or_404(lead_id)
    status = request.form.get("status")
    if status in ("new", "reviewed", "actioned", "invalid"):
        item.status = status
        audit("lead_status_changed", "lead", item.id, f"Status={status}")
        orm.session.commit()
        flash("Lead status updated.", "success")
    return redirect(url_for("admin.leads"))


@bp.route("/family-verification")
@reviewer_required
def family_verification():
    items = FamilyVerification.query.order_by(FamilyVerification.created_at.desc()).limit(200).all()
    return render_template("admin/verification.html", page_title="Family verification", items=items)


@bp.post("/family-verification/<int:request_id>/status")
@reviewer_required
def update_verification(request_id):
    item = FamilyVerification.query.get_or_404(request_id)
    status = request.form.get("status")
    note = request.form.get("reviewer_note", "").strip()
    if status in ("under_review", "verified", "declined"):
        item.status = status
        item.reviewer_note = note[:500] or None
        audit("family_verification_updated", "verification", item.id, f"Status={status}")
        orm.session.add(Notification(user_id=item.requester_id, title="Verification request updated", message=f"Your request for {item.case.case_code} is now {status.replace('_', ' ')}.", url=url_for("cases.detail", case_id=item.case_id)))
        orm.session.commit()
        flash("Verification request updated.", "success")
    return redirect(url_for("admin.family_verification"))


@bp.route("/users")
@admin_required
def users():
    items = User.query.order_by(User.created_at.desc()).limit(500).all()
    return render_template("admin/users.html", page_title="Access management", items=items)


@bp.post("/users/<int:user_id>/role")
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get("role")
    active = request.form.get("active") == "on"
    if user.id == current_user.id and (role != "admin" or not active):
        flash("You cannot remove your own administrator access or deactivate your own account.", "error")
    elif role in ("member", "reviewer", "officer", "admin"):
        user.role = role
        user.is_active = active
        audit("user_access_updated", "user", user.id, f"Role={role}; active={active}")
        orm.session.commit()
        flash("Account access updated.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/audit")
@admin_required
def audit_logs():
    items = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(500).all()
    return render_template("admin/audit.html", page_title="Audit trail", items=items)
