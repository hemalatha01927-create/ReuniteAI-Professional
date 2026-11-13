import json
import re
from datetime import date
from ..extensions import orm
from ..models import Case, MatchSuggestion, Notification

STOP_WORDS = {"the", "and", "with", "from", "near", "was", "were", "wearing", "person", "unknown", "seen", "last", "found"}


def tokens(value):
    return {word for word in re.findall(r"[a-zA-Z]{3,}", (value or "").lower()) if word not in STOP_WORDS}


def score_pair(a, b):
    """Explainable attribute-only lead score; never uses face or biometric comparison."""
    score, reasons = 0, []
    if a.location_city.strip().lower() == b.location_city.strip().lower():
        score += 30; reasons.append("Same city")
    elif a.location_state.strip().lower() == b.location_state.strip().lower():
        score += 12; reasons.append("Same state")
    if a.location_area and b.location_area and a.location_area.strip().lower() == b.location_area.strip().lower():
        score += 15; reasons.append("Same reported area")
    if a.age is not None and b.age is not None:
        diff = abs(a.age - b.age)
        if diff <= 2:
            score += 20; reasons.append("Age estimates differ by 0–2 years")
        elif diff <= 5:
            score += 12; reasons.append("Age estimates differ by 3–5 years")
    if a.gender and b.gender and a.gender.lower() == b.gender.lower():
        score += 8; reasons.append("Gender field is consistent")
    if a.last_seen_date and b.last_seen_date:
        days = abs((a.last_seen_date - b.last_seen_date).days)
        if days <= 3:
            score += 15; reasons.append("Dates are within 3 days")
        elif days <= 14:
            score += 9; reasons.append("Dates are within 2 weeks")
    text_a = tokens(" ".join([a.description or "", a.clothing or "", a.distinguishing_features or ""]))
    text_b = tokens(" ".join([b.description or "", b.clothing or "", b.distinguishing_features or ""]))
    overlap = text_a & text_b
    if overlap:
        points = min(12, len(overlap) * 3)
        score += points
        reasons.append("Shared description keywords: " + ", ".join(sorted(overlap)[:5]))
    return min(score, 100), reasons


def generate_suggestions(new_case):
    opposite = "found" if new_case.report_type == "missing" else "missing"
    candidates = Case.query.filter(
        Case.report_type == opposite,
        Case.status == "active",
        Case.id != new_case.id
    ).order_by(Case.created_at.desc()).limit(300).all()
    for other in candidates:
        score, reasons = score_pair(new_case, other) if new_case.report_type == "missing" else score_pair(other, new_case)
        if score < 35:
            continue
        left, right = sorted([new_case.id, other.id])
        exists = MatchSuggestion.query.filter_by(case_a_id=left, case_b_id=right).first()
        if exists:
            continue
        suggestion = MatchSuggestion(case_a_id=left, case_b_id=right, score=score, reasons_json=json.dumps(reasons))
        orm.session.add(suggestion)
        for reviewer in [u for u in _reviewers()]:
            orm.session.add(Notification(user_id=reviewer.id, title="Potential case link", message=f"Two reports have an attribute similarity score of {score}%. Review the lead; this is not an identity confirmation.", url="/admin/matches"))
    orm.session.flush()


def _reviewers():
    from ..models import User
    return User.query.filter(User.role.in_(["reviewer", "officer", "admin"]), User.is_active.is_(True)).all()
