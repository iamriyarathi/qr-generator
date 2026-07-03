# QuadCode — Professional QR Code Generator

A premium, fully-functional QR code generator built with Flask, SQLite and vanilla JavaScript. Generate, style, download, print and track QR codes for nine different content types — no sign-up, no watermark.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

QuadCode is a complete, production-ready QR code generator with a polished, glassmorphic UI. It supports nine QR types, live customization (colors, size, rounded modules, transparency, embedded logos, error correction), three export formats (PNG, SVG, JPG), a searchable generation history backed by SQLite, and an admin-style dashboard with usage statistics.

Everything in this repository is fully implemented — there are no placeholders, no stub endpoints, and no TODOs. Clone it, install the dependencies, and it runs immediately.

## Features

### 🏠 Home page
- Modern sticky navbar with logo, links and a dark/light mode toggle
- Hero section with an animated, scanning QR illustration
- QR-type showcase grid, feature grid, "how it works" steps and a call-to-action band
- Fully responsive, glassmorphic footer

### 🔡 Supported QR types
| Type | Description |
|---|---|
| Website URL | Encodes any http(s) link |
| Plain text | Arbitrary text content |
| Email | `mailto:` link with optional subject & body |
| Phone number | `tel:` one-tap dialing |
| SMS | Pre-filled text message |
| WhatsApp | Opens a WhatsApp chat via `wa.me` |
| WiFi | Auto-join network (SSID, password, encryption, hidden) |
| Google Maps location | Drops a pin at given coordinates (with "use my location") |
| Contact card (vCard) | Full vCard 3.0 with name, phone, email, company, title, website, address |

### 🎨 Generator & customization
- Live preview, generated instantly via AJAX
- Download as **PNG**, **SVG**, or **JPG**
- **Print** directly from the browser
- **Copy input** to clipboard
- **Reset form** in one click
- Adjustable **size**, **foreground/background color**, **border (quiet zone)**, **error correction level (L/M/Q/H)**, **rounded modules**, **transparent background**, and **embedded logo** (error correction is automatically boosted to `H` when a logo is added, to keep the code scannable)

### ✅ Validation
Friendly, inline error messages for empty fields, invalid URLs, invalid emails, and invalid phone numbers — validated both client-side (fast feedback) and server-side (authoritative, XSS/SQL-injection safe).

### 🕓 History
Every generated QR code is saved to SQLite with its type, input, generated file name, customization, creation date and download count. From the History page you can:
- View all generated codes with thumbnails
- Search by input/type
- Filter by QR type
- Re-download any code (increments its download counter)
- Delete codes (also removes the files from disk)

### 📊 Dashboard
- Total QR codes generated
- QR codes generated today
- Most-used QR type
- Total downloads
- Breakdown by type (bar chart)
- Recent activity feed

### 🖌️ UI/UX
Google Fonts (Space Grotesk / Inter / JetBrains Mono), Font Awesome icons, glassmorphic cards with a signature "finder-bracket" corner motif (inspired by a QR code's own position-detection squares), smooth hover/scroll animations, fully responsive layout, dark & light themes, loading spinners, and toast notifications.

### 🔒 Security
- All user input is HTML-escaped (XSS protection)
- All database queries are parameterized (SQL-injection protection)
- Upload size limits and file-type checks on logo uploads
- Security response headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)

## Screenshots

> Run the app locally (see below) and drop your own screenshots into a `screenshots/` folder — suggested shots: Home page hero, Generator with a styled WiFi code, History table, Dashboard.

```
screenshots/
  home.png
  generator.png
  history.png
  dashboard.png
```

## Tech stack

- **Backend:** Python 3, Flask, Flask Blueprints
- **Frontend:** HTML5, CSS3 (custom, no framework), vanilla JavaScript
- **Database:** SQLite (parameterized queries only)
- **QR rendering:** the `qrcode` library for encoding, Pillow for PNG/JPG, hand-built SVG for vector export
- **Deployment:** Vercel (`@vercel/python`)
- **Version control:** Git

## Folder structure

```
qr-generator/
├── app.py                  # Flask application factory / entry point
├── config.py                # Configuration (paths, secrets, limits)
├── requirements.txt
├── vercel.json               # Vercel deployment config
├── README.md
├── .gitignore
├── blueprints/
│   ├── main.py               # Page (HTML) routes
│   └── api.py                # JSON API routes (generate/download/history/stats)
├── database/
│   ├── db.py                  # SQLite helper (parameterized queries)
│   └── schema.sql             # Table definitions
├── utils/
│   ├── validators.py          # Input validation, sanitization, QR payload builders
│   └── qr_utils.py            # QR rendering engine (PNG/SVG/JPG, styling, logo)
├── templates/
│   ├── base.html               # Shared shell (navbar, footer)
│   ├── index.html               # Home page
│   ├── generator.html           # Generator tool
│   ├── history.html              # History page
│   ├── dashboard.html            # Dashboard page
│   ├── 404.html / 500.html        # Error pages
├── static/
│   ├── css/style.css              # All styling
│   ├── js/main.js                  # Shared JS (theme, nav, toasts)
│   ├── js/generator.js              # Generator page logic
│   ├── js/history.js                 # History page logic
│   └── js/dashboard.js                # Dashboard page logic
└── instance/
    ├── qr_generator.db                # SQLite database (created automatically)
    └── generated/                      # Generated QR/logo files (created automatically)
```

## Requirements

- Python 3.9 or later
- pip

Dependencies (see `requirements.txt`):
```
Flask==3.0.3
qrcode[pil]==7.4.2
Pillow==10.4.0
python-dotenv==1.0.1
Werkzeug==3.0.4
```

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/qr-generator.git
cd qr-generator

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## How to run

```bash
python app.py
```

The app starts at **http://localhost:5000**. The SQLite database and `instance/generated/` folder are created automatically on first run — no manual setup required.

Optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev key | Flask secret key (set a real one in production) |
| `PORT` | `5000` | Port to listen on |
| `FLASK_DEBUG` | `1` | Set to `0` to disable debug mode |

## How to deploy on Vercel

This project ships with a ready-to-use `vercel.json` and a module-level `app` object in `app.py`, which is what the `@vercel/python` builder expects.

```bash
# 1. Install the Vercel CLI if you haven't already
npm install -g vercel

# 2. From the project root
vercel

# 3. For a production deployment
vercel --prod
```

Or connect the repository directly in the [Vercel dashboard](https://vercel.com/new) — it will detect `vercel.json` automatically.

**Note on storage:** Vercel's serverless functions run on a read-only filesystem except for `/tmp`, which is wiped between deployments and cold starts. `config.py` automatically detects the Vercel environment (`VERCEL` env var) and stores the SQLite database and generated files under `/tmp` in that case, so the app runs without errors — but history will not persist long-term on Vercel's free tier. For persistent history in production, point `DATABASE_PATH` at a managed database (e.g. Postgres, Turso, or a mounted volume) and adjust `database/db.py` accordingly.

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT). You're free to use, modify and distribute it for personal or commercial projects.
