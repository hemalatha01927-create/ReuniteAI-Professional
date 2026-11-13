# ReuniteAI – முதலில் இதைப் படிக்கவும் (தமிழ் Setup Guide)

இது முன்பு கொடுத்த சிறிய UI project அல்ல. புதிய **ReuniteAI_Professional_Full_Project.zip**-ஐ தனியாக extract செய்து இதையே பயன்படுத்தவும்.

## 1. சரியான folder-ஐ VS Code-ல் திறக்கவும்

1. ZIP file-ஐ Download செய்து Extract செய்யவும்.
2. Extract ஆன `ReuniteAI_Professional` folder-ஐ VS Code-ல் **Open Folder** செய்யவும்.
3. அந்த folder-க்குள் நேரடியாக `requirements.txt`, `run.py`, `config.py`, `app` ஆகியவை இருக்க வேண்டும்.
4. VS Code Terminal-ல்:

```powershell
dir
```

`requirements.txt` காணப்படவில்லை என்றால், நீ சரியான project folder-க்குள் இல்லை. உள்ளே இன்னொரு `ReuniteAI_Professional` folder இருந்தால் அதற்குள் செல்லவும்:

```powershell
cd .\ReuniteAI_Professional
```

## 2. ஒரே முறையில் setup செய்யவும்

VS Code PowerShell Terminal-ல்:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_windows.ps1
```

இந்த script தானாகவே:
- `.venv` virtual environment உருவாக்கும்
- தேவையான Python packages install செய்யும்
- local `.env` file-ஐ உருவாக்கும்
- SQLite database tables initialize செய்யும்

Internet இல்லையெனில் package installation நடைபெறாது. அப்போது இணைய இணைப்புடன் மீண்டும் `setup_windows.ps1` இயக்கவும்.

## 3. முதல் Admin account உருவாக்கவும்

Setup முடிந்த பிறகு:

```powershell
.\.venv\Scripts\Activate.ps1
flask --app run.py create-admin
```

Terminal கேட்கும் Full name, Email, Password ஆகியவற்றை உள்ளிடவும். Password குறைந்தது 12 characters இருக்க வேண்டும். இந்த project-ல் default admin password கிடையாது.

## 4. Project run செய்யவும்

```powershell
.\run_windows.ps1
```

Browser-ல் இதைத் திறக்கவும்:

```text
http://127.0.0.1:5000
```

- புதிய member account உருவாக்க: **Create account**
- Admin login: **Sign in**
- Reviewer / authorized officer access கொடுக்க: Admin → **Access management**

மீண்டும் project திறக்கும்போதெல்லாம் `run_windows.ps1` மட்டும் இயக்கினால் போதும்.

## 5. Project-ல் உள்ள முக்கிய Modules

1. Professional Dashboard – Member Dashboard மற்றும் Operations Centre
2. Secure Login / Registration – Password hashing மற்றும் role-based access
3. Missing Person / Found Person Report Submission
4. Public Case Directory – City, report type, keyword search
5. Public-safe summary மற்றும் private reviewer details தனித்தனியாக
6. Photo Upload – image validation, EXIF metadata removal, private storage
7. Reviewer / Authorized Officer Review Queue
8. Community Lead Submission மற்றும் private lead management
9. Family Verification Request workflow
10. AI-assisted Attribute Matching – வயது, இடம், தேதி, description keywords அடிப்படையில் potential links
11. Notifications மற்றும் case status tracking
12. Admin Access Management மற்றும் Audit Trail

## 6. முக்கியமான வரம்புகள்

- முகத்தை வைத்து ஒருவரை அடையாளம் காணும் Facial Recognition இதில் இல்லை. அது மாற்றாக, non-biometric report details-ஐ வைத்து சாத்தியமான leads மட்டும் rank செய்கிறது. Score என்பது அடையாள உறுதி அல்ல; மனிதர் சரிபார்க்க வேண்டும்.
- இது Police database-உடன் இணைக்கப்படவில்லை. `Authorized officer` என்பது admin ஒதுக்கும் role மட்டுமே; அந்த நபரின் அதிகாரத்தை admin தனியாகச் சரிபார்க்க வேண்டும்.
- SMS / WhatsApp / Email alerts வெளிப்புற service-உடன் இன்னும் இணைக்கப்படவில்லை; in-app notifications உள்ளன.
- உண்மையான missing-person data, தனிப்பட்ட photos அல்லது phone numbers-ஐ அனுமதியின்றி பயன்படுத்த வேண்டாம். Project testing-க்கு synthetic data பயன்படுத்தவும்.
- இது முழு academic/portfolio project source code. உண்மையான public-service deployment-க்கு முன் legal/privacy review, security audit, MFA, HTTPS, backups, monitoring மற்றும் அதிகாரப்பூர்வ ஒப்புதல் தேவை.

## 7. Tests இயக்குவது

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```
