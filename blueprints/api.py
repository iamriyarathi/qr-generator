"""
JSON API routes.

All endpoints return JSON (except the file-download endpoints, which
stream a binary file). Every database access goes through
`database.db`, which uses parameterized queries exclusively.
"""
import json
import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_file, abort

from database import db
from utils.validators import ValidationError, build_qr_payload, sanitize
from utils.qr_utils import generate

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLOWED_TYPES = {
    "url", "text", "email", "phone", "sms", "whatsapp",
    "wifi", "location", "vcard",
}


def _bool(value):
    return str(value).strip().lower() in ("1", "true", "on", "yes")


def _read_customization_from_request():
    """Pull customization options out of the incoming form/json request."""
    src = request.form if request.form else (request.get_json(silent=True) or {})
    return {
        "size": int(src.get("size") or 400),
        "fg_color": sanitize(src.get("fg_color") or "#000000"),
        "bg_color": sanitize(src.get("bg_color") or "#FFFFFF"),
        "border": int(src.get("border") or 4),
        "error_correction": sanitize(src.get("error_correction") or "M"),
        "rounded": _bool(src.get("rounded")),
        "transparent": _bool(src.get("transparent")),
    }


def _save_logo_if_present():
    """Persist an uploaded logo to disk; return (bytes_or_None, stored_filename_or_None)."""
    file = request.files.get("logo")
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_LOGO_EXTENSIONS"]:
        raise ValidationError({"logo": "Logo must be a PNG or JPG image."})
    data = file.read()
    if len(data) > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ValidationError({"logo": "Logo file is too large."})
    filename = f"logo_{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["GENERATED_DIR"], filename)
    with open(path, "wb") as f:
        f.write(data)
    return data, filename


def _load_stored_logo(customization):
    logo_file = customization.get("logo_file")
    if not logo_file:
        return None
    path = os.path.join(current_app.config["GENERATED_DIR"], logo_file)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


@api_bp.route("/generate", methods=["POST"])
def api_generate():
    src = request.form if request.form else (request.get_json(silent=True) or {})
    qr_type = sanitize(src.get("qr_type", "")).lower()

    if qr_type not in ALLOWED_TYPES:
        return jsonify(success=False, errors={"qr_type": "Unsupported or missing QR type."}), 400

    # Collect + sanitize every raw text field once.
    raw_fields = {
        k: sanitize(v) for k, v in src.items() if k not in ("qr_type",)
    }

    try:
        qr_data, friendly_input = build_qr_payload(qr_type, raw_fields)
    except ValidationError as e:
        return jsonify(success=False, errors=e.errors), 400

    if not qr_data or len(qr_data) > 4000:
        return jsonify(success=False, errors={"_": "Input is empty or too long to encode."}), 400

    customization = _read_customization_from_request()

    try:
        logo_bytes, logo_file = _save_logo_if_present()
    except ValidationError as e:
        return jsonify(success=False, errors=e.errors), 400

    if logo_file:
        customization["logo_file"] = logo_file

    try:
        result = generate(qr_data, {**customization, "logo_bytes": logo_bytes})
    except Exception as exc:  # noqa: BLE001 - surface a friendly error to the client
        current_app.logger.exception("QR generation failed")
        return jsonify(success=False, errors={"_": f"Could not generate QR code: {exc}"}), 500

    customization["error_correction"] = result["error_correction_used"]

    # Persist the canonical PNG file to disk.
    file_name = f"qr_{uuid.uuid4().hex}.png"
    file_path = os.path.join(current_app.config["GENERATED_DIR"], file_name)
    with open(file_path, "wb") as f:
        f.write(result["png_bytes"]().read())

    item_id = db.insert_history(
        qr_type=qr_type,
        user_input=friendly_input,
        qr_data=qr_data,
        file_name=file_name,
        customization_json=json.dumps(customization),
    )

    return jsonify(
        success=True,
        id=item_id,
        preview=result["data_uri"](),
        qr_data=qr_data,
        qr_type=qr_type,
        user_input=friendly_input,
        error_correction_used=result["error_correction_used"],
    )


@api_bp.route("/download/<int:item_id>/<fmt>", methods=["GET"])
def api_download(item_id, fmt):
    fmt = fmt.lower()
    if fmt not in ("png", "svg", "jpg"):
        abort(400, "Unsupported format.")

    item = db.get_history_item(item_id)
    if item is None:
        abort(404, "QR code not found.")

    customization = json.loads(item["customization"] or "{}")
    logo_bytes = _load_stored_logo(customization)

    result = generate(item["qr_data"], {**customization, "logo_bytes": logo_bytes})
    db.increment_download_count(item_id)

    base_name = f"qrcode-{item['qr_type']}-{item_id}"
    if fmt == "png":
        buf = result["png_bytes"]()
        return send_file(buf, mimetype="image/png", as_attachment=True,
                          download_name=f"{base_name}.png")
    if fmt == "jpg":
        buf = result["jpg_bytes"]()
        return send_file(buf, mimetype="image/jpeg", as_attachment=True,
                          download_name=f"{base_name}.jpg")

    svg_string = result["svg_string"]()
    import io
    buf = io.BytesIO(svg_string.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="image/svg+xml", as_attachment=True,
                      download_name=f"{base_name}.svg")


@api_bp.route("/thumb/<int:item_id>", methods=["GET"])
def api_thumb(item_id):
    """Small inline PNG preview for history/dashboard tables (not a download)."""
    item = db.get_history_item(item_id)
    if item is None:
        abort(404)
    customization = json.loads(item["customization"] or "{}")
    logo_bytes = _load_stored_logo(customization)
    thumb_opts = {**customization, "size": 96, "logo_bytes": logo_bytes}
    result = generate(item["qr_data"], thumb_opts)
    buf = result["png_bytes"]()
    return send_file(buf, mimetype="image/png")


@api_bp.route("/history", methods=["GET"])
def api_history_list():
    search = sanitize(request.args.get("search", ""))
    qr_type = sanitize(request.args.get("type", ""))
    rows = db.list_history(search=search or None, qr_type=qr_type or None)
    return jsonify(success=True, items=[dict(r) for r in rows])


@api_bp.route("/history/<int:item_id>", methods=["DELETE"])
def api_history_delete(item_id):
    item = db.get_history_item(item_id)
    if item is None:
        return jsonify(success=False, error="Not found."), 404

    customization = json.loads(item["customization"] or "{}")
    for fname in (item["file_name"], customization.get("logo_file")):
        if fname:
            path = os.path.join(current_app.config["GENERATED_DIR"], fname)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    db.delete_history_item(item_id)
    return jsonify(success=True)


@api_bp.route("/stats", methods=["GET"])
def api_stats():
    return jsonify(success=True, stats=db.get_stats())
