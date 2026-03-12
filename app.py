from __future__ import annotations

import json
import os
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
PROJECTS_DIR = STATIC_DIR / 'projects'
ABOUT_DIR = STATIC_DIR / 'media' / 'about'
VIDEOS_DIR = STATIC_DIR / 'media' / 'videos'
HERO_CYCLE_DIR = STATIC_DIR / 'media' / 'hero_cycle'
SHOWCASE_STILLS_DIR = STATIC_DIR / 'media' / 'showcase_stills'
INSTANCE_DIR = BASE_DIR / 'instance'


PROJECT_DATA = {
    'projekt_1': {
        'title': 'Beauty clinic experience',
        'description': 'Czysty layout, jasna struktura usług i premium odbiór marki.',
    },
    'projekt_2': {
        'title': 'Service & offer system',
        'description': 'Strony ofertowe projektowane pod czytelność, szybkość i leady.',
    },
    'projekt_3': {
        'title': 'Studio services platform',
        'description': 'Sekcje usług, harmonijny układ i mocna hierarchia informacji.',
    },
    'projekt_4': {
        'title': 'Results & social proof',
        'description': 'Galerie efektów, zaufanie i szeroka prezentacja realizacji.',
    },
    'projekt_5': {
        'title': 'Creative landing direction',
        'description': 'Nowoczesny storytelling, motion i czysty komercyjny przekaz.',
    },
    'projekt_6': {
        'title': 'Digital showcase pages',
        'description': 'Szybkie wdrożenia stron dla firm, usług i e-commerce.',
    },
}

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.avif')
VIDEO_EXTENSIONS = ('.mp4', '.webm', '.mov')


def get_env(name: str, default: str = '') -> str:
    value = os.environ.get(name, '').strip()
    return value if value else default


def parse_bool(value: str) -> bool:
    return (value or '').strip().lower() in {'1', 'true', 'yes', 'y', 'on', 't'}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_timestamp(value: str) -> str:
    return ''.join(char for char in value.replace(':', '').replace('-', '').replace('+00:00', 'Z') if char.isalnum() or char == '_') or 'lead'


def strip_fragment(url: str) -> str:
    if not url:
        return ''
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ''))


def phone_digits(value: str) -> str:
    return ''.join(char for char in (value or '') if char.isdigit())


def relative_media_files(folder: Path, extensions: tuple[str, ...]) -> list[str]:
    if not folder.exists():
        return []

    files: list[Path] = []
    for ext in extensions:
        files.extend(sorted(folder.glob(f'*{ext}')))
    return [path.relative_to(STATIC_DIR).as_posix() for path in files]


def build_projects() -> list[dict]:
    projects: list[dict] = []
    if not PROJECTS_DIR.exists():
        return projects

    for folder in sorted(item for item in PROJECTS_DIR.iterdir() if item.is_dir()):
        images = relative_media_files(folder, IMAGE_EXTENSIONS)
        videos = relative_media_files(folder, VIDEO_EXTENSIONS)
        meta = PROJECT_DATA.get(
            folder.name,
            {
                'title': folder.name.replace('_', ' ').title(),
                'description': 'Selected web project.',
            },
        )
        projects.append(
            {
                'slug': folder.name,
                'title': meta['title'],
                'description': meta['description'],
                'featured': images[0] if images else None,
                'gallery': images[1:] if len(images) > 1 else [],
                'videos': videos,
                'count': len(images),
            }
        )
    return projects


def build_about_images() -> list[str]:
    return relative_media_files(ABOUT_DIR, IMAGE_EXTENSIONS)


def build_process_videos() -> list[str]:
    files = relative_media_files(VIDEOS_DIR, VIDEO_EXTENSIONS)
    return [path for path in files if Path(path).name not in {'hero.mp4', 'hero_loop.mp4'}]


def build_hero_video() -> str | None:
    hero_loop = VIDEOS_DIR / 'hero_loop.mp4'
    if hero_loop.exists():
        return hero_loop.relative_to(STATIC_DIR).as_posix()

    files = relative_media_files(HERO_CYCLE_DIR, VIDEO_EXTENSIONS)
    if files:
        return files[0]

    fallback = VIDEOS_DIR / 'hero.mp4'
    return fallback.relative_to(STATIC_DIR).as_posix() if fallback.exists() else None


def build_showcase_stills() -> list[str]:
    stills = relative_media_files(SHOWCASE_STILLS_DIR, IMAGE_EXTENSIONS)
    if stills:
        return stills[:6]

    hero_stills = relative_media_files(HERO_CYCLE_DIR, IMAGE_EXTENSIONS)
    if hero_stills:
        return hero_stills[:6]

    return []


def create_app() -> Flask:
    app = Flask(__name__)

    data_dir_raw = get_env('DATA_DIR', str(INSTANCE_DIR))
    data_dir = Path(data_dir_raw)
    db_path = get_env('DB_PATH', str(data_dir / 'app.db'))
    leads_dir = get_env('LEADS_DIR', str(data_dir / 'leads'))
    leads_jsonl_path = get_env('LEADS_JSONL_PATH', str(data_dir / 'leads.jsonl'))
    mail_archive_dir = get_env('MAIL_ARCHIVE_DIR', str(data_dir / 'mail_archive'))

    app.config.update(
        SECRET_KEY=get_env('SECRET_KEY', 'stanislav-portfolio-secret'),
        SITE_NAME=get_env('SITE_NAME', 'Stanislav Smotrych Portfolio'),
        BRAND=get_env('BRAND', 'Stanislav Smotrych'),
        DB_PATH=db_path,
        LEADS_DIR=leads_dir,
        LEADS_JSONL_PATH=leads_jsonl_path,
        MAIL_ARCHIVE_DIR=mail_archive_dir,
        CONTACT_EMAIL=get_env('CONTACT_EMAIL', 'stanislaussmotrych@gmail.com'),
        CONTACT_PHONE=get_env('CONTACT_PHONE', '+48723698910'),
        CONTACT_INSTAGRAM=get_env('CONTACT_INSTAGRAM', '@stanislavsmotrych'),
        CONTACT_INSTAGRAM_URL=get_env('CONTACT_INSTAGRAM_URL', 'https://www.instagram.com/stanislavsmotrych/'),
        CONTACT_WHATSAPP=get_env('CONTACT_WHATSAPP', '+48723698910'),
        CONTACT_WHATSAPP_URL=get_env('CONTACT_WHATSAPP_URL', ''),
        CONTACT_NOTE=get_env('CONTACT_NOTE', 'Odpowiem możliwie szybko z konkretem.'),
        COMPANY_NAME=get_env('COMPANY_NAME', 'Stanislav Smotrych'),
        COMPANY_ADDRESS=get_env('COMPANY_ADDRESS', 'Polska'),
        COMPANY_NIP=get_env('COMPANY_NIP', ''),
        MAIL_TO=get_env('MAIL_TO', get_env('CONTACT_EMAIL', '')),
        SMTP_HOST=get_env('SMTP_HOST', ''),
        SMTP_PORT=int(get_env('SMTP_PORT', '587') or '587'),
        SMTP_TLS=parse_bool(get_env('SMTP_TLS', '1')),
        SMTP_USER=get_env('SMTP_USER', ''),
        SMTP_PASS=get_env('SMTP_PASS', ''),
        SMTP_FROM=get_env('SMTP_FROM', ''),
    )

    init_db(app)

    @app.route('/')
    def index():
        return render_template(
            'index.html',
            contact_open=request.args.get('contact') == 'open',
            current_year=datetime.now().year,
            hero_video=build_hero_video(),
            showcase_stills=build_showcase_stills(),
            projects=build_projects(),
            about_images=build_about_images(),
            about_points=[
                'Stanislav Smotrych, 20 lat.',
                'Informatyka: Politechnika Rzeszowska i Uniwersytet Rzeszowski.',
                '3 lata doświadczenia w tworzeniu i wdrażaniu stron WWW.',
                'Współpraca z X-Estetik przy dystrybucji stron dla branży beauty.',
                'Realizacja stron pod klucz, również w modelu hurtowym.',
                'Strony dla firm, agencji, sklepów internetowych i kampanii Google Ads.',
                'Przy większych wdrożeniach mogę angażować juniorów do wsparcia realizacji.',
            ],
            links={
                'xestetik': 'https://x-estetik.pl/',
                'seomotive': 'https://seomotive.pl/',
                'google_partner': 'https://www.google.com/partners/agency?id=3224018050',
            },
            contact={
                'email': app.config['CONTACT_EMAIL'],
                'phone': app.config['CONTACT_PHONE'],
                'instagram': app.config['CONTACT_INSTAGRAM'],
                'instagram_url': app.config['CONTACT_INSTAGRAM_URL'],
                'whatsapp': app.config['CONTACT_WHATSAPP'],
                'whatsapp_url': app.config['CONTACT_WHATSAPP_URL'] or f"https://wa.me/{phone_digits(app.config['CONTACT_WHATSAPP'] or app.config['CONTACT_PHONE'])}",
                'note': app.config['CONTACT_NOTE'],
                'company_name': app.config['COMPANY_NAME'],
                'company_address': app.config['COMPANY_ADDRESS'],
                'company_nip': app.config['COMPANY_NIP'],
            },
        )

    @app.post('/lead')
    def lead():
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        company = (request.form.get('company') or '').strip()
        message = (request.form.get('message') or '').strip()
        privacy_accept = (request.form.get('privacy_accept') or '').strip() == '1'
        source_path = strip_fragment(request.referrer or '')

        if not name or not email or not message:
            flash('Uzupełnij wymagane pola: imię, e-mail oraz wiadomość.', 'error')
            return redirect(url_for('index', contact='open') + '#kontakt')

        if '@' not in email or email.startswith('@') or email.endswith('@'):
            flash('Podaj poprawny adres e-mail.', 'error')
            return redirect(url_for('index', contact='open') + '#kontakt')

        if not privacy_accept:
            flash('Zaznacz zgodę na Politykę prywatności i Regulamin, aby wysłać formularz.', 'error')
            return redirect(url_for('index', contact='open') + '#kontakt')

        lead_id, created_at = save_lead(
            app,
            name=name,
            email=email,
            company=company,
            message=message,
            path=source_path,
            privacy_accepted=privacy_accept,
        )
        archive_lead_to_disk(
            app,
            lead_id=lead_id,
            created_at=created_at,
            name=name,
            email=email,
            company=company,
            message=message,
            source_path=source_path,
        )
        sent = send_lead_email(
            app,
            lead_id=lead_id,
            created_at=created_at,
            name=name,
            email=email,
            company=company,
            message=message,
            source_path=source_path,
        )

        if sent:
            flash('Dziękuję. Wiadomość została wysłana i trafiła na e-mail kontaktowy.', 'success')
        else:
            flash('Dziękuję. Wiadomość została zapisana. Po uzupełnieniu SMTP w Render będzie też wysyłana e-mailem.', 'success')
        return redirect(url_for('index', contact='open') + '#kontakt')

    @app.route('/polityka-prywatnosci')
    def privacy_policy():
        return render_template(
            'legal.html',
            page_title='Polityka prywatności',
            intro='Informacje o danych przekazanych przez formularz kontaktowy.',
            sections=[
                {
                    'title': 'Administrator danych',
                    'items': [
                        f"Administratorem danych jest {app.config['COMPANY_NAME']}.",
                        f"Kontakt e-mail: {app.config['CONTACT_EMAIL']}",
                    ],
                },
                {
                    'title': 'Zakres danych',
                    'items': [
                        'Formularz zapisuje imię, adres e-mail, nazwę firmy lub agencji oraz treść wiadomości.',
                        'Dane są wykorzystywane wyłącznie do kontaktu w sprawie zapytania ofertowego lub wdrożenia.',
                    ],
                },
                {
                    'title': 'Przechowywanie i wysyłka',
                    'items': [
                        'Zgłoszenia są zapisywane w bazie SQLite oraz opcjonalnie archiwizowane do JSON/JSONL.',
                        'Po skonfigurowaniu SMTP zgłoszenie jest dodatkowo wysyłane na adres kontaktowy.',
                    ],
                },
            ],
        )

    @app.route('/regulamin')
    def terms():
        return render_template(
            'legal.html',
            page_title='Regulamin',
            intro='Podstawowe zasady korzystania z formularza kontaktowego i strony portfolio.',
            sections=[
                {
                    'title': 'Zakres strony',
                    'items': [
                        'Strona prezentuje wybrane realizacje i umożliwia wysłanie zapytania kontaktowego.',
                        'Materiały mają charakter informacyjny i ofertowy.',
                    ],
                },
                {
                    'title': 'Formularz kontaktowy',
                    'items': [
                        'Wysłanie formularza nie jest równoznaczne z zawarciem umowy.',
                        'Odpowiedź na zapytanie jest ustalana indywidualnie.',
                        'Dane z formularza mogą zostać zapisane w bazie danych i przekazane e-mailem na adres kontaktowy serwisu.',
                    ],
                },
                {
                    'title': 'Prawa autorskie',
                    'items': [
                        'Układ strony, teksty i materiały wizualne nie mogą być kopiowane bez zgody właściciela.',
                        'Logotypy partnerów i marek należą do ich właścicieli.',
                    ],
                },
            ],
        )

    return app


def get_db(app: Flask) -> sqlite3.Connection:
    db_path = Path(app.config['DB_PATH'])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(app: Flask) -> None:
    with get_db(app) as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS leads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              name TEXT NOT NULL,
              email TEXT NOT NULL,
              company TEXT,
              message TEXT NOT NULL,
              source_path TEXT,
              privacy_accepted INTEGER NOT NULL DEFAULT 0
            )
            '''
        )
        connection.commit()


def save_lead(
    app: Flask,
    *,
    name: str,
    email: str,
    company: str,
    message: str,
    path: str,
    privacy_accepted: bool,
) -> tuple[int, str]:
    created_at = utc_now_iso()
    with get_db(app) as connection:
        cursor = connection.execute(
            '''
            INSERT INTO leads (created_at, name, email, company, message, source_path, privacy_accepted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (created_at, name, email, company, message, path, int(privacy_accepted)),
        )
        lead_id = int(cursor.lastrowid)
        connection.commit()
    return lead_id, created_at


def archive_lead_to_disk(
    app: Flask,
    *,
    lead_id: int,
    created_at: str,
    name: str,
    email: str,
    company: str,
    message: str,
    source_path: str,
) -> None:
    payload = {
        'id': lead_id,
        'created_at': created_at,
        'name': name,
        'email': email,
        'company': company,
        'message': message,
        'source_path': source_path,
        'site': app.config.get('SITE_NAME', ''),
    }

    leads_dir = (app.config.get('LEADS_DIR') or '').strip()
    jsonl_path = (app.config.get('LEADS_JSONL_PATH') or '').strip()
    timestamp = safe_timestamp(created_at)

    try:
        if leads_dir:
            out_dir = Path(leads_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f'lead_{lead_id}_{timestamp}.json').write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
    except Exception:
        pass

    try:
        if jsonl_path:
            out_path = Path(jsonl_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + '\n')
    except Exception:
        pass


def send_lead_email(
    app: Flask,
    *,
    lead_id: int,
    created_at: str,
    name: str,
    email: str,
    company: str,
    message: str,
    source_path: str,
) -> bool:
    mail_to = (app.config.get('MAIL_TO') or '').strip()
    smtp_host = (app.config.get('SMTP_HOST') or '').strip()
    smtp_user = (app.config.get('SMTP_USER') or '').strip()
    smtp_pass = (app.config.get('SMTP_PASS') or '').strip()
    smtp_from = (app.config.get('SMTP_FROM') or '').strip() or smtp_user
    smtp_port = int(app.config.get('SMTP_PORT') or 587)
    smtp_tls = bool(app.config.get('SMTP_TLS'))

    if not (mail_to and smtp_host and smtp_from):
        return False

    subject = f"Nowa wiadomość — {app.config.get('BRAND', 'Portfolio')}"
    body_lines = [
        f'ID: {lead_id}',
        f'Data (UTC): {created_at}',
        f'Imię: {name}',
        f'E-mail: {email}',
        f'Firma / agencja: {company or "-"}',
        f'Źródło: {source_path or "-"}',
        '',
        'Wiadomość:',
        message,
        '',
        '---',
        f"Serwis: {app.config.get('SITE_NAME', '')}",
    ]

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_from
    msg['To'] = mail_to
    msg.set_content('\n'.join(body_lines))

    try:
        archive_dir = (app.config.get('MAIL_ARCHIVE_DIR') or '').strip()
        if archive_dir:
            out_dir = Path(archive_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f'lead_{lead_id}_{safe_timestamp(created_at)}.eml').write_bytes(msg.as_bytes())
    except Exception:
        pass

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.ehlo()
            if smtp_tls:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        return False


app = create_app()


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5050')),
        debug=parse_bool(os.environ.get('FLASK_DEBUG', '1')),
    )
