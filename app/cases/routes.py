import json
from datetime import datetime, date, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from ..extensions import orm, limiter
from ..models import Case, Lead, Notification, FamilyVerification, AuditLog, User
from ..utils.security import save_private_image, private_image_path
from ..utils.matching import generate_suggestions

bp = Blueprint("cases", __name__)


def audit(action, entity_type, entity_id=None, details=None):
    orm.session.add(AuditLog(actor_id=current_user.id if current_user.is_authenticated else None,
                             action=action, entity_type=entity_type, entity_id=str(entity_id or ""),
                             details=(details or "")[:500], ip_address=request.remote_addr))


def can_view_private(case):
    return current_user.is_authenticated and (current_user.id == case.reporter_id or current_user.has_role("admin", "reviewer", "officer"))


@bp.route("/")
def list_cases():
    query = Case.query.filter_by(status="active")
    kind = request.args.get("type", "")
    city = request.args.get("city", "").strip()
    q = request.args.get("q", "").strip()
    if kind in ("missing", "found"):
        query = query.filter_by(report_type=kind)
    if city:
        query = query.filter(Case.location_city.ilike(f"%{city}%"))
    if q:
        query = query.filter(or_(Case.person_name.ilike(f"%{q}%"), Case.public_summary.ilike(f"%{q}%"),
                                 Case.location_area.ilike(f"%{q}%")))
    cases = query.order_by(Case.created_at.desc()).limit(100).all()
    return render_template("cases/list.html", page_title="Case directory", cases=cases, kind=kind, city=city, q=q)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create_case():
    if not current_app.config["PUBLIC_INTAKE_ENABLED"]:
        abort(404)
    if request.method == "POST":
        report_type = request.form.get("report_type", "")
        name = request.form.get("person_name", "").strip()
        city = request.form.get("location_city", "").strip()
        state = request.form.get("location_state", "").strip()
        description = request.form.get("description", "").strip()
        public_summary = request.form.get("public_summary", "").strip()
        age_raw = request.form.get("age", "").strip()
        if report_type not in ("missing", "found") or not name or not city or not state or not description or not public_summary:
            flash("Complete all required fields before submitting.", "error")
            return render_template("cases/new.html", page_title="Create a report")
        age = int(age_raw) if age_raw.isdigit() and 0 <= int(age_raw) <= 120 else None
        try:
            photo_filename = save_private_image(request.files.get("photo"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("cases/new.html", page_title="Create a report")
        date_raw = request.form.get("last_seen_date", "").strip()
        try:
            reported_date = date.fromisoformat(date_raw) if date_raw else None
        except ValueError:
            reported_date = None
        case = Case(
            case_code="PENDING", report_type=report_type, person_name=name[:100], age=age,
            gender=request.form.get("gender", "").strip()[:30] or None,
            last_seen_date=reported_date,
            location_area=request.form.get("location_area", "").strip()[:120] or None,
            location_city=city[:100], location_state=state[:100],
            location_country=request.form.get("location_country", "India").strip()[:100] or "India",
            description=description[:4000], public_summary=public_summary[:1000], clothing=request.form.get("clothing", "").strip()[:500] or None,
            distinguishing_features=request.form.get("distinguishing_features", "").strip()[:500] or None,
            photo_filename=photo_filename, photo_public=request.form.get("photo_public") == "on",
            reporter_id=current_user.id, status="pending_review")
        orm.session.add(case)
        orm.session.flush()
        case.case_code = f"RAI-{datetime.now().strftime('%y%m')}-{case.id:06d}"
        audit("case_submitted", "case", case.id, f"Type={report_type}; code={case.case_code}")
        reviewers = User.query.filter(User.is_active.is_(True), User.role.in_(["admin", "reviewer", "officer"])).all()
        for reviewer in reviewers:
            orm.session.add(Notification(user_id=reviewer.id, title="New report awaiting review", message=f"{case.case_code} has been submitted and needs a safety review.", url=url_for("admin.case_queue")))
        orm.session.commit()
        flash(f"Report {case.case_code} submitted for verification. It is not public until reviewed.", "success")
        return redirect(url_for("cases.detail", case_id=case.id))
    return render_template("cases/new.html", page_title="Create a report")


@bp.route("/<int:case_id>", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def detail(case_id):
    case = Case.query.get_or_404(case_id)
    if case.status != "active" and not can_view_private(case):
        abort(404)
    if request.method == "POST":
        if not current_app.config["PUBLIC_INTAKE_ENABLED"]:
            abort(404)
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        message = request.form.get("message", "").strip()
        contact_name = request.form.get("contact_name", "").strip()
        if not message or not contact_name:
            flash("Add your name and information before submitting a lead.", "error")
        else:
            lead = Lead(case_id=case.id, submitted_by_id=current_user.id, message=message[:2000],
                        contact_name=contact_name[:100], contact_phone=request.form.get("contact_phone", "").strip()[:30] or None,
                        contact_email=request.form.get("contact_email", "").strip()[:254] or None)
            orm.session.add(lead)
            orm.session.add(Notification(user_id=case.reporter_id, title="New information received", message=f"A community member submitted information for {case.case_code}.", url=url_for("cases.detail", case_id=case.id)))
            for reviewer in User.query.filter(User.is_active.is_(True), User.role.in_(["admin", "reviewer", "officer"])).all():
                orm.session.add(Notification(user_id=reviewer.id, title="New community lead", message=f"New private information was submitted for {case.case_code}.", url=url_for("admin.leads")))
            audit("lead_submitted", "lead", None, f"For case {case.case_code}")
            orm.session.commit()
            flash("Your information was sent privately to the case team.", "success")
            return redirect(url_for("cases.detail", case_id=case.id))
    return render_template("cases/detail.html", page_title=case.case_code, case=case, private_view=can_view_private(case))


@bp.post("/<int:case_id>/verification")
@login_required
@limiter.limit("4 per hour", methods=["POST"])
def request_verification(case_id):
    if not current_app.config["PUBLIC_INTAKE_ENABLED"]:
        abort(404)
    case = Case.query.get_or_404(case_id)
    if case.status != "active":
        abort(404)
    relationship = request.form.get("relationship", "").strip()
    explanation = request.form.get("explanation", "").strip()
    contact = request.form.get("preferred_contact", "").strip()
    if not relationship or not explanation or not contact:
        flash("Complete all verification request fields.", "error")
    elif case.reporter_id == current_user.id:
        flash("You cannot request family verification on your own report.", "error")
    else:
        request_record = FamilyVerification(case_id=case.id, requester_id=current_user.id,
                                            relationship_to_person=relationship[:80], explanation=explanation[:1200],
                                            preferred_contact=contact[:150])
        orm.session.add(request_record)
        for reviewer in User.query.filter(User.is_active.is_(True), User.role.in_(["admin", "reviewer", "officer"])).all():
            orm.session.add(Notification(user_id=reviewer.id, title="Family verification requested", message=f"A private verification request was submitted for {case.case_code}.", url=url_for("admin.family_verification")))
        audit("family_verification_requested", "case", case.id)
        orm.session.commit()
        flash("Your family verification request has been sent for private review.", "success")
    return redirect(url_for("cases.detail", case_id=case.id))


@bp.route("/<int:case_id>/photo")
def case_photo(case_id):
    case = Case.query.get_or_404(case_id)
    if not case.photo_filename:
        abort(404)
    if not (case.status == "active" and case.photo_public) and not can_view_private(case):
        abort(403)
    return send_file(private_image_path(case.photo_filename), mimetype="image/jpeg", max_age=0)
