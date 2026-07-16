import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

import db
from helpers import login_required, upload_image, delete_image, ImageUploadError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
db.init_app(app)


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return redirect("/Home.html")


@app.route("/announcements")
def announcements():
    conn = db.get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM announcements ORDER BY sort_order ASC, id DESC")
        rows = cur.fetchall()
    return render_template("announcements.html", announcements=rows)


@app.route("/events")
def events():
    conn = db.get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM events ORDER BY sort_order ASC, id DESC")
        event_rows = cur.fetchall()
        event_list = []
        for ev in event_rows:
            cur.execute(
                "SELECT * FROM event_images WHERE event_id = %s ORDER BY sort_order ASC, id ASC",
                (ev["id"],),
            )
            ev = dict(ev)
            ev["images"] = cur.fetchall()
            event_list.append(ev)
    return render_template("events.html", events=event_list)


# ---------------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------------

@app.route("/admin")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin/login", methods=["POST"])
def admin_login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = db.get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, password_hash FROM admin_users WHERE username = %s", (username,))
        admin = cur.fetchone()

    if admin and check_password_hash(admin["password_hash"], password):
        session.clear()
        session["admin_id"] = admin["id"]
        session["admin_username"] = username
        return redirect(url_for("admin_dashboard"))

    flash("Invalid username or password. Please try again.")
    return redirect(url_for("admin_login"))


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    return render_template("admin_dashboard.html", admin_username=session.get("admin_username"))


# ---------------------------------------------------------------------------
# Admin: Announcements CRUD
# ---------------------------------------------------------------------------

@app.route("/admin/announcements", methods=["GET", "POST"])
@login_required
def admin_announcements():
    conn = db.get_db()

    if request.method == "POST":
        ann_id = request.form.get("id") or None
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        sort_order = int(request.form.get("sort_order") or 0)
        remove_image = bool(request.form.get("remove_image"))

        if not title or not body:
            flash("Title and content are both required.", "error")
            return redirect(url_for("admin_announcements", edit=ann_id) if ann_id else url_for("admin_announcements"))

        new_image_url = None
        try:
            new_image_url = upload_image(request.files.get("image"), folder="chtm/announcements")
        except ImageUploadError as e:
            flash(str(e), "error")
            return redirect(url_for("admin_announcements", edit=ann_id) if ann_id else url_for("admin_announcements"))

        with conn.cursor() as cur:
            if ann_id:
                cur.execute("SELECT image_url FROM announcements WHERE id = %s", (ann_id,))
                existing = cur.fetchone()
                final_image_url = existing["image_url"] if existing else None

                if new_image_url:
                    if existing and existing["image_url"]:
                        delete_image(existing["image_url"])
                    final_image_url = new_image_url
                elif remove_image:
                    if existing and existing["image_url"]:
                        delete_image(existing["image_url"])
                    final_image_url = None

                cur.execute(
                    "UPDATE announcements SET title=%s, body=%s, image_url=%s, sort_order=%s, updated_at=now() WHERE id=%s",
                    (title, body, final_image_url, sort_order, ann_id),
                )
                flash("Announcement updated.", "success")
            else:
                cur.execute(
                    "INSERT INTO announcements (title, body, image_url, sort_order) VALUES (%s, %s, %s, %s)",
                    (title, body, new_image_url, sort_order),
                )
                flash("Announcement added.", "success")
            conn.commit()
        return redirect(url_for("admin_announcements"))

    edit_row = None
    edit_id = request.args.get("edit")
    if edit_id:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM announcements WHERE id = %s", (edit_id,))
            edit_row = cur.fetchone()

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM announcements ORDER BY sort_order ASC, id DESC")
        all_rows = cur.fetchall()

    return render_template("admin_announcements.html", announcements=all_rows, edit_row=edit_row)


@app.route("/admin/announcements/delete/<int:ann_id>")
@login_required
def admin_announcements_delete(ann_id):
    conn = db.get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT image_url FROM announcements WHERE id = %s", (ann_id,))
        row = cur.fetchone()
        cur.execute("DELETE FROM announcements WHERE id = %s", (ann_id,))
        conn.commit()
    if row and row["image_url"]:
        delete_image(row["image_url"])
    flash("Announcement deleted.", "success")
    return redirect(url_for("admin_announcements"))


# ---------------------------------------------------------------------------
# Admin: Events CRUD (+ per-event photo management)
# ---------------------------------------------------------------------------

@app.route("/admin/events", methods=["GET", "POST"])
@login_required
def admin_events():
    conn = db.get_db()

    if request.method == "POST":
        action = request.form.get("action", "save_event")

        if action == "save_event":
            event_id = request.form.get("id") or None
            title = request.form.get("title", "").strip()
            subtitle = request.form.get("subtitle", "").strip()
            sort_order = int(request.form.get("sort_order") or 0)

            if not title:
                flash("Event title is required.", "error")
                return redirect(url_for("admin_events", edit=event_id) if event_id else url_for("admin_events"))

            with conn.cursor() as cur:
                if event_id:
                    cur.execute(
                        "UPDATE events SET title=%s, subtitle=%s, sort_order=%s, updated_at=now() WHERE id=%s",
                        (title, subtitle, sort_order, event_id),
                    )
                    flash("Event updated.", "success")
                    new_id = event_id
                else:
                    cur.execute(
                        "INSERT INTO events (title, subtitle, sort_order) VALUES (%s, %s, %s) RETURNING id",
                        (title, subtitle, sort_order),
                    )
                    new_id = cur.fetchone()["id"]
                    flash("Event added. Now upload photos below.", "success")
                conn.commit()
            return redirect(url_for("admin_events", edit=new_id))

        if action == "add_images":
            event_id = request.form.get("event_id")
            files = request.files.getlist("images")
            uploaded = 0
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM event_images WHERE event_id = %s", (event_id,))
                next_order = cur.fetchone()["m"] + 1

                for f in files:
                    if not f or not f.filename:
                        continue
                    try:
                        url = upload_image(f, folder="chtm/events")
                    except ImageUploadError as e:
                        flash(str(e), "error")
                        continue
                    if url:
                        cur.execute(
                            "INSERT INTO event_images (event_id, image_url, sort_order) VALUES (%s, %s, %s)",
                            (event_id, url, next_order),
                        )
                        next_order += 1
                        uploaded += 1
                conn.commit()
            if uploaded:
                flash(f"{uploaded} image(s) added.", "success")
            return redirect(url_for("admin_events", edit=event_id))

    edit_event = None
    edit_id = request.args.get("edit")
    if edit_id:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM events WHERE id = %s", (edit_id,))
            edit_event = cur.fetchone()
            if edit_event:
                edit_event = dict(edit_event)
                cur.execute(
                    "SELECT * FROM event_images WHERE event_id = %s ORDER BY sort_order ASC, id ASC",
                    (edit_id,),
                )
                edit_event["images"] = cur.fetchall()

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM events ORDER BY sort_order ASC, id DESC")
        all_events = cur.fetchall()

    return render_template("admin_events.html", events=all_events, edit_event=edit_event)


@app.route("/admin/events/delete/<int:event_id>")
@login_required
def admin_events_delete(event_id):
    conn = db.get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT image_url FROM event_images WHERE event_id = %s", (event_id,))
        images = cur.fetchall()
        cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
    for img in images:
        delete_image(img["image_url"])
    flash("Event deleted.", "success")
    return redirect(url_for("admin_events"))


@app.route("/admin/events/images/delete/<int:image_id>")
@login_required
def admin_events_image_delete(image_id):
    conn = db.get_db()
    event_id = request.args.get("event_id")
    with conn.cursor() as cur:
        cur.execute("SELECT image_url FROM event_images WHERE id = %s", (image_id,))
        row = cur.fetchone()
        cur.execute("DELETE FROM event_images WHERE id = %s", (image_id,))
        conn.commit()
    if row and row["image_url"]:
        delete_image(row["image_url"])
    return redirect(url_for("admin_events", edit=event_id))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
