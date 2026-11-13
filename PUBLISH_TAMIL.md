# ReuniteAI — Public preview publish guide (Tamil)

இந்த வழிகாட்டி GitHub + Render + Neon PostgreSQL பயன்படுத்தி portfolio/public preview வெளியிட உதவும்.

> **முக்கிய பாதுகாப்பு:** Render Free web service-ல் local file storage நிரந்தரமில்லை; free instance idle ஆனதும் sleep ஆகும். அதனால் இந்த deployment-ல் புதிய account registration, missing/found case intake, private leads, family verification மற்றும் photo upload ஆகியவை இயல்பாக OFF. இந்த hosted preview-ல் உண்மையான missing-person data, குழந்தைகளின் விவரங்கள் அல்லது புகைப்படங்களைச் சேகரிக்க வேண்டாம். இது police/government service அல்ல. Real-user launch-க்கு சட்ட/தனியுரிமை ஆலோசனை, security audit, verified staff onboarding, persistent private file storage, backups, monitoring ஆகியவை தேவை.

## 1. புதிய project folder

இந்த ZIP-ஐ extract செய்து `ReuniteAI_Professional` folder-ஐ VS Code-ல் open செய். `dir` கொடுத்தால் `run.py`, `requirements.txt`, `render.yaml`, `app` folder ஆகியவை root-ல் நேரடியாகத் தெரிய வேண்டும்.

## 2. GitHub repository உருவாக்கு

1. GitHub-ல் New repository தேர்வு செய்.
2. Repository name: `ReuniteAI-Professional`.
3. Public அல்லது Private தேர்வு செய் (portfolio code public செய்ய விரும்பினால் Public).
4. README / .gitignore initialize செய்ய வேண்டாம்; project-ல் அவை ஏற்கனவே உள்ளன.
5. Repository URL-ஐ copy செய்.

VS Code Terminal-ல் project root-இல்:

```powershell
git init
git add .
git status
git commit -m "Prepare ReuniteAI for deployment"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

`YOUR_GITHUB_REPOSITORY_URL` இடத்தில் நீ copy செய்த repository URL-ஐ வை. `git status`-ல் `.env`, `.venv`, `instance`, `*.sqlite3` upload ஆகவில்லை என்பதைச் சரிபார். GitHub password அல்லது access token-ஐ code-ல் எழுதாதே.

## 3. Neon PostgreSQL database உருவாக்கு

1. https://neon.tech/ சென்று account உருவாக்கு.
2. New Project உருவாக்கு; database name-ஐ `reuniteai` என வை.
3. Dashboard-ல் **Connection Details** திறந்து pooled connection string-ஐ copy செய். இது password கொண்ட secret; யாருடனும் பகிராதே; GitHub-ல் commit செய்யாதே.
4. Neon free plan limits மாறலாம்; current quota மற்றும் retention-ஐ Neon dashboard-ல் சரிபார்.

## 4. Render Blueprint deploy

1. https://render.com/ சென்று GitHub account-ஐ connect செய்.
2. **New → Blueprint** தேர்வு செய்.
3. `ReuniteAI-Professional` repository-ஐத் தேர்வு செய்.
4. Render repo-வில் உள்ள `render.yaml`-ஐ படித்து service உருவாக்கும்.
5. `DATABASE_URL` கேட்கும்போது Neon connection string-ஐ paste செய். வேறு யாரிடமும் அனுப்பாதே.
6. Deploy செய். `SECRET_KEY` Render தானாக generate செய்யும்.
7. Deployment முடிந்ததும் `https://...onrender.com/healthz` open செய். `{"status":"ok"}` வந்தால் server health check pass.

Blueprint பயன்படுத்த முடியாவிட்டால் Render-ல் **New → Web Service** தேர்வு செய்து:
- Build command: `pip install -r requirements.txt`
- Start command: `flask --app run.py init-db && gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT run:app`
- Health check path: `/healthz`
- Environment variables: `APP_ENV=production`, `SECRET_KEY` (random strong secret), `DATABASE_URL` (Neon connection string), `COOKIE_SECURE=1`, `PUBLIC_REGISTRATION_ENABLED=false`, `PUBLIC_INTAKE_ENABLED=false`, `UPLOADS_ENABLED=false`, `RATELIMIT_STORAGE_URI=memory://`.

## 5. முதல் Admin account உருவாக்கு (Render Free-ல் Shell இல்லை)

Render Free web service-க்கு dashboard shell இல்லை. அதனால் **உன் laptop-லிருந்தே Neon database-க்கு connect செய்து** admin account உருவாக்கலாம்.

1. Render-ல் அமைத்த அதே Neon `DATABASE_URL`-ஐ பாதுகாப்பாக copy செய்.
2. VS Code-ல் புதிய deploy-ready project root-இல் PowerShell திற.
3. Virtual environment இருந்தால் activate செய்; இல்லையெனில் `python -m venv .venv` மற்றும் `.venv\Scripts\Activate.ps1` செய்.
4. `pip install -r requirements.txt` செய்.
5. கீழே `PASTE_NEON_CONNECTION_STRING_HERE` இடத்தில் connection string-ஐ மட்டும் replace செய்து command run செய். அதை chat அல்லது screenshot-ல் பகிராதே.

```powershell
$env:DATABASE_URL = "PASTE_NEON_CONNECTION_STRING_HERE"
$env:APP_ENV = "production"
flask --app run.py init-db
flask --app run.py create-admin
Remove-Item Env:DATABASE_URL
Remove-Item Env:APP_ENV
```

CLI உன்னிடம் Admin name, email, password கேட்கும். 12+ character unique password கொடு. Password-ஐ மறந்துவிடாதபடி password manager-ல் சேமி; chat-ல் அனுப்பாதே.

## 6. Website திற

Render Dashboard → Service → URL-ஐ open செய். Admin login-க்கு `/login` செல்லலாம். Public preview mode-ல் sign-up மற்றும் report intake முடக்கப்பட்டிருக்கும்; அது திட்டமிட்ட பாதுகாப்பு அமைப்பு.

## 7. Update publish

Code மாற்றம் செய்த பிறகு:

```powershell
git add .
git commit -m "Update ReuniteAI"
git push
```

Render தானாக redeploy செய்யும்.

## ஏதேனும் build error வந்தால்

Render Dashboard → service → **Logs** திறந்து கடைசி error lines-ஐ மட்டும் பகிர். Database URL, password, SECRET_KEY, email, personal records ஆகியவற்றை screenshot/log-ல் மறைத்துவிடு.
