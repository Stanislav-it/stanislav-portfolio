# Stanislav Smotrych Portfolio

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5050

## Contact form logic

The contact drawer now uses a dedicated `/lead` endpoint. Each submission:

- validates required fields and privacy consent
- saves the lead to SQLite (`DB_PATH`)
- optionally archives the lead to JSON / JSONL
- optionally sends an SMTP notification email

### Render environment variables

```env
SECRET_KEY=change-me
CONTACT_EMAIL=stanislaussmotrych@gmail.com
CONTACT_PHONE=+48723698910
CONTACT_INSTAGRAM=@stanislavsmotrych
CONTACT_INSTAGRAM_URL=https://www.instagram.com/stanislavsmotrych/
CONTACT_WHATSAPP=+48723698910
CONTACT_WHATSAPP_URL=https://wa.me/48723698910
CONTACT_NOTE=Odpowiem możliwie szybko z konkretem.
COMPANY_NAME=Stanislav Smotrych
COMPANY_ADDRESS=Polska
COMPANY_NIP=
MAIL_TO=kontakt@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=1
SMTP_USER=twoj_login_smtp
SMTP_PASS=twoje_haslo_lub_app_password
SMTP_FROM=kontakt@example.com
DATA_DIR=/var/data
DB_PATH=/var/data/app.db
LEADS_DIR=/var/data/leads
LEADS_JSONL_PATH=/var/data/leads.jsonl
MAIL_ARCHIVE_DIR=/var/data/mail_archive
```

## Structure

- `static/media/videos/` – hero and additional videos
- `static/media/about/` – photos for the “O mnie” section
- `static/projects/` – project screenshots grouped by folder
- `instance/` – SQLite DB and local lead archive on first run
