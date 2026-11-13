# ReuniteAI — Professional Missing & Found Persons Case Management Platform

ReuniteAI is a full-stack Flask application for securely collecting missing-person and found-person reports, managing case reviews, receiving private community leads, handling family verification requests, and prioritizing potential links through a transparent non-biometric attribute comparison engine.

This release is a complete, runnable academic/portfolio project source codebase. It is not a toy UI or a seeded demo: there are no demo records, no shared default administrator, and no hard-coded administrator password. An administrator account is created deliberately through a secure interactive CLI command.

## Product modules

- **Professional dashboard:** personalized member workspace and operations centre for reviewers/admins.
- **Account management:** account registration, secure password hashing, session management, profile updates and role-based access (`member`, `reviewer`, `officer`, `admin`).
- **Missing/found case management:** structured report submission, separate public-safe summaries and private reviewer notes, case codes, case status lifecycle and reviewer approval before public publication.
- **Case directory:** searchable, filterable active reports by report type, keyword and city.
- **Private community leads:** members can send information privately; contact details are not displayed on public case pages.
- **Family verification workflow:** private requests with reviewer status tracking and notes.
- **AI-assisted potential-link ranking:** explainable matching using city/area, approximate age, gender field, date proximity and description keywords. The system records matching reasons for reviewer inspection.
- **Notifications:** in-app notices for report, lead and verification updates. SMS, WhatsApp and external email delivery are not configured in this release.
- **Operations console:** review queue, potential links, leads, family verification, user access controls and audit trail. Admins can provision an `officer` workspace role for a person whose authority has been checked independently.
- **Secure image handling:** file type validation, image decoding/re-encoding, EXIF removal, size limits and private storage outside the public static directory.
- **Security basics:** CSRF protection, rate limits on sensitive actions, password hashing, access checks, secure cookie settings and environment-based configuration.
- **Automated tests:** core workflows covered with pytest.

## Important design decision about AI and identity

ReuniteAI **does not perform facial recognition or biometric identity matching**. The potential-link engine compares only the non-biometric report fields listed above. A score is a lead-prioritization signal, not a probability of identity and never proof that two reports refer to the same person. An authorized person must independently review every lead, and identity/family reunification must follow appropriate official verification. No automatic person identification or automated case closure takes place.

## Run on Windows with VS Code

### 1. Extract and open the correct folder

Extract `ReuniteAI_Professional.zip`. In VS Code, open the folder named `ReuniteAI_Professional` — the folder that directly contains `run.py`, `requirements.txt`, `config.py`, and the `app` folder.

In the VS Code terminal, check:

```powershell
dir
```

You must see `requirements.txt` and `run.py` in the output. If you see another `ReuniteAI_Professional` folder, enter it with:

```powershell
cd .\ReuniteAI_Professional
```

### 2. Create the virtual environment and install packages

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks environment activation, run this only for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 3. Configure the application secret

Copy `.env.example` to `.env` and set `SECRET_KEY` to a long random value. Keep `.env` private and do not upload it to GitHub. The application can run locally with SQLite without any external service.

### 4. Initialize the database

```powershell
flask --app run.py init-db
```

### 5. Create the first administrator

```powershell
flask --app run.py create-admin
```

The command securely prompts for the administrator name, email and a password (12+ characters). There is no default admin username or password.

### 6. Start the application

```powershell
python run.py
```

Open `http://127.0.0.1:5000` in your browser. Create a normal member account from the website. Sign in using the administrator account to access the operations centre. An administrator can promote approved staff accounts to reviewer, authorized officer or administrator roles from **Access management**. Only grant the officer role after checking the person’s authority outside the application.

## Run automated tests

```powershell
pytest -q
```

## Folder structure

```text
ReuniteAI_Professional/
├── app/
│   ├── auth/                  # Registration, sign-in and profile
│   ├── main/                  # Landing page and dashboards
│   ├── cases/                 # Reports, directory, leads and verification requests
│   ├── admin/                 # Review console, access control and audit
│   ├── notifications/         # In-app notifications
│   ├── utils/                 # Private image handling and lead ranking
│   ├── templates/             # Responsive Jinja templates
│   └── static/                # CSS and JavaScript
├── tests/                     # Pytest tests
├── instance/                  # Private uploads (created at runtime)
├── config.py
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

## Case lifecycle

`pending_review → under_review → active → resolved / closed`

A reviewer or provisioned authorized officer may reject a report if it is incomplete, unsafe or cannot be verified. Only reports marked `active` are visible in the public directory. Owners and authorized staff can view private case records while they are in review.

## Before any real-world deployment

This project contains substantial application functionality, but a missing-person information system is privacy- and safety-critical. Before deployment to real families or public institutions, arrange a formal security assessment and legal/privacy review; implement verified staff onboarding, stronger production authentication (including MFA), robust production database backups, secure object storage, centralized logging, malware scanning, monitoring, retention/deletion policy, incident response, consent management and abuse reporting. Configure HTTPS and a production WSGI server. The built-in Flask development server is for local development only. Do not claim the platform is affiliated with police or government agencies unless a formal partnership exists. For emergencies, users must contact local police/emergency services directly.

## Technology

Python · Flask · Flask-Login · Flask-SQLAlchemy · SQLite (local default) · Flask-WTF · Flask-Limiter · Pillow · HTML · CSS · JavaScript · pytest

## Optional one-click PowerShell setup

From the extracted project root, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_windows.ps1
```

Then create the first administrator once:

```powershell
.\.venv\Scripts\Activate.ps1
flask --app run.py create-admin
```

To start the site in later sessions, run:

```powershell
.\run_windows.ps1
```


## Publish a safe portfolio preview

See [`PUBLISH_TAMIL.md`](PUBLISH_TAMIL.md) for the exact GitHub + Render + Neon instructions. The included `render.yaml` disables public registration, report intake and photo uploads by default. This is intentional: Render Free uses an ephemeral filesystem and is not suitable for storing sensitive case photographs or real-world reports. Do not enable real-person intake until persistent private storage, legal/privacy review, security assessment, backups and verified staff workflows are in place.
