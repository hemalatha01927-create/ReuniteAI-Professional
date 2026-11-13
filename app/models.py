from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import orm


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, orm.Model):
    __tablename__ = "users"
    id = orm.Column(orm.Integer, primary_key=True)
    full_name = orm.Column(orm.String(100), nullable=False)
    email = orm.Column(orm.String(254), unique=True, nullable=False, index=True)
    phone = orm.Column(orm.String(30))
    password_hash = orm.Column(orm.String(255), nullable=False)
    role = orm.Column(orm.String(20), nullable=False, default="member")  # member, reviewer, admin
    is_active = orm.Column(orm.Boolean, nullable=False, default=True)
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    last_login_at = orm.Column(orm.DateTime(timezone=True))

    reports = orm.relationship("Case", back_populates="reporter", foreign_keys="Case.reporter_id")
    notifications = orm.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        return "".join(part[0] for part in self.full_name.split()[:2]).upper()

    def has_role(self, *roles):
        return self.role in roles


class Case(orm.Model):
    __tablename__ = "cases"
    id = orm.Column(orm.Integer, primary_key=True)
    case_code = orm.Column(orm.String(24), unique=True, nullable=False, index=True)
    report_type = orm.Column(orm.String(12), nullable=False, index=True)  # missing / found
    person_name = orm.Column(orm.String(100), nullable=False)
    age = orm.Column(orm.Integer)
    gender = orm.Column(orm.String(30))
    last_seen_date = orm.Column(orm.Date)
    location_area = orm.Column(orm.String(120))
    location_city = orm.Column(orm.String(100), nullable=False, index=True)
    location_state = orm.Column(orm.String(100), nullable=False)
    location_country = orm.Column(orm.String(100), nullable=False, default="India")
    description = orm.Column(orm.Text, nullable=False)  # private reviewer detail
    public_summary = orm.Column(orm.String(1000), nullable=False)
    clothing = orm.Column(orm.String(500))
    distinguishing_features = orm.Column(orm.String(500))
    photo_filename = orm.Column(orm.String(120))
    photo_public = orm.Column(orm.Boolean, nullable=False, default=False)
    status = orm.Column(orm.String(20), nullable=False, default="pending_review", index=True)
    reporter_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"), nullable=False, index=True)
    assigned_reviewer_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"))
    reviewed_by_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"))
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    reviewed_at = orm.Column(orm.DateTime(timezone=True))
    resolved_at = orm.Column(orm.DateTime(timezone=True))

    reporter = orm.relationship("User", back_populates="reports", foreign_keys=[reporter_id])
    assigned_reviewer = orm.relationship("User", foreign_keys=[assigned_reviewer_id])
    reviewed_by = orm.relationship("User", foreign_keys=[reviewed_by_id])
    leads = orm.relationship("Lead", back_populates="case", cascade="all, delete-orphan")

    @property
    def location_label(self):
        parts = [self.location_area, self.location_city, self.location_state, self.location_country]
        return ", ".join(part for part in parts if part)


class Lead(orm.Model):
    __tablename__ = "leads"
    id = orm.Column(orm.Integer, primary_key=True)
    case_id = orm.Column(orm.Integer, orm.ForeignKey("cases.id"), nullable=False, index=True)
    submitted_by_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"), nullable=False)
    message = orm.Column(orm.Text, nullable=False)
    contact_name = orm.Column(orm.String(100), nullable=False)
    contact_phone = orm.Column(orm.String(30))
    contact_email = orm.Column(orm.String(254))
    status = orm.Column(orm.String(20), nullable=False, default="new")
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    case = orm.relationship("Case", back_populates="leads")
    submitter = orm.relationship("User")


class MatchSuggestion(orm.Model):
    __tablename__ = "match_suggestions"
    id = orm.Column(orm.Integer, primary_key=True)
    case_a_id = orm.Column(orm.Integer, orm.ForeignKey("cases.id"), nullable=False)
    case_b_id = orm.Column(orm.Integer, orm.ForeignKey("cases.id"), nullable=False)
    score = orm.Column(orm.Integer, nullable=False)
    reasons_json = orm.Column(orm.Text, nullable=False, default="[]")
    status = orm.Column(orm.String(20), nullable=False, default="pending")
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (orm.UniqueConstraint("case_a_id", "case_b_id", name="uq_match_pair"),)
    case_a = orm.relationship("Case", foreign_keys=[case_a_id])
    case_b = orm.relationship("Case", foreign_keys=[case_b_id])


class Notification(orm.Model):
    __tablename__ = "notifications"
    id = orm.Column(orm.Integer, primary_key=True)
    user_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"), nullable=False, index=True)
    title = orm.Column(orm.String(140), nullable=False)
    message = orm.Column(orm.String(400), nullable=False)
    url = orm.Column(orm.String(300), nullable=False, default="/dashboard")
    is_read = orm.Column(orm.Boolean, nullable=False, default=False)
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    user = orm.relationship("User", back_populates="notifications")


class FamilyVerification(orm.Model):
    __tablename__ = "family_verifications"
    id = orm.Column(orm.Integer, primary_key=True)
    case_id = orm.Column(orm.Integer, orm.ForeignKey("cases.id"), nullable=False, index=True)
    requester_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"), nullable=False)
    relationship_to_person = orm.Column(orm.String(80), nullable=False)
    explanation = orm.Column(orm.Text, nullable=False)
    preferred_contact = orm.Column(orm.String(150), nullable=False)
    status = orm.Column(orm.String(20), nullable=False, default="pending")
    reviewer_note = orm.Column(orm.String(500))
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    case = orm.relationship("Case")
    requester = orm.relationship("User")


class AuditLog(orm.Model):
    __tablename__ = "audit_logs"
    id = orm.Column(orm.Integer, primary_key=True)
    actor_id = orm.Column(orm.Integer, orm.ForeignKey("users.id"))
    action = orm.Column(orm.String(80), nullable=False)
    entity_type = orm.Column(orm.String(60), nullable=False)
    entity_id = orm.Column(orm.String(60))
    details = orm.Column(orm.String(500))
    ip_address = orm.Column(orm.String(45))
    created_at = orm.Column(orm.DateTime(timezone=True), default=utcnow, nullable=False)
    actor = orm.relationship("User")
