# CHTM Admin Panel — Python (Flask) + Vercel Setup Guide

This is the Vercel-deployable rewrite of the admin panel: **Flask** instead
of PHP, a **Postgres** database (via Neon's free tier) instead of MySQL, and
**Cloudinary** for image storage instead of a local `uploads/` folder — since
Vercel functions don't keep files between requests.

## Why not just "PHP → Python" 1:1?

Vercel runs Python as stateless, ephemeral serverless functions. There's no
persistent disk and no built-in database, no matter which language you use.
That's the real reason the old PHP version (local `uploads/` folder + MySQL
on the same server) wouldn't work as-is on Vercel — so this rewrite swaps in
services built for that model:

- **Neon** — free hosted Postgres (serverless-friendly, works great with Vercel)
- **Cloudinary** — free image hosting/CDN (uploaded images go here instead of disk)

## What's static vs. dynamic

- `public/Home.html`, `public/About.html`, `public/YoungLeaders.html`,
  `public/style.css`, `public/Image/` — plain static files. Vercel serves
  anything in `public/**` directly, no backend involved.
- Everything else (`/announcements`, `/events`, `/admin/...`) is a real Flask
  route backed by the database.

## Setup steps

### 1. Create a free Postgres database (Neon)
1. Sign up at neon.tech and create a project.
2. Copy the connection string it gives you (looks like
   `postgresql://user:pass@ep-xxxx.neon.tech/dbname?sslmode=require`).
3. Run `schema.sql` against it. Easiest way: paste its contents into Neon's
   built-in SQL editor and run it. This creates the tables and seeds:
   - Admin login: **username `admin`, password `chtm2026`**
   - The existing announcement/event content, so the pages aren't empty.

### 2. Create a free Cloudinary account
1. Sign up at cloudinary.com (free tier).
2. From your dashboard, copy: **Cloud name**, **API Key**, **API Secret**.

### 3. Set environment variables in Vercel
In your Vercel project → Settings → Environment Variables, add:

| Name | Value |
|---|---|
| `DATABASE_URL` | your Neon connection string |
| `CLOUDINARY_CLOUD_NAME` | from Cloudinary |
| `CLOUDINARY_API_KEY` | from Cloudinary |
| `CLOUDINARY_API_SECRET` | from Cloudinary |
| `SECRET_KEY` | any long random string (used to sign login sessions) |

Generate a `SECRET_KEY` locally with:
```
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Deploy
Push this folder to a GitHub repo and import it in Vercel ("Add New Project"),
or from the CLI:
```
npm i -g vercel
vercel
```
Vercel auto-detects `main.py` as the Flask entrypoint (per `vercel.json`).

### 5. Log in
Visit `https://your-project.vercel.app/admin`, log in with `admin` /
`chtm2026`, then change the password (see below).

## Changing the admin password
Generate a new hash and update it in your database:
```
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-new-password'))"
```
Then in Neon's SQL editor:
```sql
UPDATE admin_users SET password_hash = 'paste-the-hash-here' WHERE username = 'admin';
```

## Local development
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="your-neon-connection-string"
export CLOUDINARY_CLOUD_NAME="..." CLOUDINARY_API_KEY="..." CLOUDINARY_API_SECRET="..."
export SECRET_KEY="dev-secret"
python3 main.py
```
Then visit http://127.0.0.1:5000/announcements, /events, or /admin.

(You can also use `vercel dev` once the Vercel CLI is set up, to test in an
environment closer to production.)

## What was tested before this was handed to you
Using a local Postgres database and a mocked Cloudinary uploader, the full
flow was run end-to-end: public Announcements/Events pages, admin
login/logout, session-gated admin routes, create/edit/delete announcements
with image upload and removal, invalid file-type rejection, event creation,
multi-image upload to an event, single-image deletion, and event deletion
with cascading image cleanup. All passed.

## Notes
- Images are validated as JPG/PNG/WEBP/GIF, capped at 5MB, before upload.
- Deleting an announcement/event/image also removes it from Cloudinary.
- Session auth uses Flask's signed-cookie sessions, which work natively in
  Vercel's stateless serverless model — no server-side session storage needed.


Simple Change for deployment bug (wa rani)
pun an napud bag o