# ReuniteAI Architecture

## Request flow

```text
Browser
  │
  ▼
Flask application factory
  ├── Authentication blueprint
  ├── Member/case blueprint
  ├── Reviewer/admin blueprint
  └── Notification blueprint
  │
  ├── Flask-Login session + role checks
  ├── Flask-WTF CSRF protection
  ├── Flask-Limiter request limits
  │
  ▼
SQLAlchemy ORM ─────────────── SQLite (local default)
  │
  ├── Users and roles
  ├── Cases and status history fields
  ├── Leads and family verification requests
  ├── Explainable match suggestions
  ├── Notifications
  └── Audit logs

Private image upload pipeline
  └── Extension allow-list → Pillow decode → EXIF-free JPEG re-encode
      → private instance storage → permission-checked media route
```

## Authorization matrix

| Capability | Member | Reviewer | Authorized officer | Admin |
|---|---:|---:|---:|---:|
| Submit missing/found report | Yes | Yes | Yes | Yes |
| Browse active public cases | Yes | Yes | Yes | Yes |
| View own pending case | Yes | Yes | Yes | Yes |
| Review all private cases | No | Yes | Yes | Yes |
| Approve/reject reports | No | Yes | Yes | Yes |
| Review leads and potential links | No | Yes | Yes | Yes |
| Handle family verification requests | No | Yes | Yes | Yes |
| Change account roles | No | No | No | Yes |
| View audit trail | No | No | No | Yes |

The `authorized officer` role is a permission role only. The application does not validate law-enforcement identity; administrators must verify any person’s authority through an independent process before granting the role.

## Data visibility

- Only `active` cases are included in the public directory.
- Reporter phone and email are not rendered on public case pages.
- Images are private unless the report submitter explicitly consents to public display and the report is active.
- A member can view their own pending case. Reviewers, authorized officers and admins can view all cases.
- Community leads and verification requests are available only to the case team.
