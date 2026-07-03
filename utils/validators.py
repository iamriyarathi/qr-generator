"""
Validation, sanitization and QR-payload construction.

`build_qr_payload` is the single place that turns a QR "type" + a dict of
user-submitted fields into the literal string that gets encoded into the
QR code, and also into the friendly `user_input` string stored in history.
All user-supplied text is HTML-escaped before it is ever rendered back to
a page (XSS protection); SQL access always goes through parameterized
queries (see database/db.py) so nothing here needs to escape for SQL.
"""
import html
import re

URL_RE = re.compile(
    r"^(https?:\/\/)?"                                   # optional scheme
    r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"                     # domain
    r"(:\d+)?(\/[^\s]*)?$"                                # optional port/path
)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?[0-9\s\-\(\)]{6,20}$")


class ValidationError(Exception):
    """Raised with a dict of {field: message} when validation fails."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__("Validation failed")


def sanitize(text):
    """Strip control characters and HTML-escape user text."""
    if text is None:
        return ""
    text = str(text).strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return html.escape(text)


def is_valid_url(value):
    return bool(URL_RE.match(value.strip()))


def is_valid_email(value):
    return bool(EMAIL_RE.match(value.strip()))


def is_valid_phone(value):
    return bool(PHONE_RE.match(value.strip()))


def _require(fields, data, errors):
    """Populate `errors` for any missing/blank required field."""
    for f in fields:
        if not str(data.get(f, "")).strip():
            errors[f] = "This field is required."
    return errors


def build_qr_payload(qr_type, data):
    """
    Validate `data` (a dict of raw form fields) for the given `qr_type`
    and return (qr_data_string, friendly_input_summary).

    Raises ValidationError(errors_dict) on invalid input.
    """
    errors = {}
    qr_type = (qr_type or "").strip().lower()

    if qr_type == "url":
        _require(["url"], data, errors)
        url = data.get("url", "").strip()
        if not errors and not is_valid_url(url):
            errors["url"] = "Please enter a valid website URL."
        if errors:
            raise ValidationError(errors)
        if not re.match(r"^https?:\/\/", url):
            url = "https://" + url
        return url, url

    if qr_type == "text":
        _require(["text"], data, errors)
        if errors:
            raise ValidationError(errors)
        text = data.get("text", "").strip()
        return text, (text[:80] + "…" if len(text) > 80 else text)

    if qr_type == "email":
        _require(["email"], data, errors)
        email = data.get("email", "").strip()
        if not errors and not is_valid_email(email):
            errors["email"] = "Please enter a valid email address."
        if errors:
            raise ValidationError(errors)
        subject = data.get("subject", "").strip()
        body = data.get("body", "").strip()
        payload = f"mailto:{email}"
        params = []
        if subject:
            params.append("subject=" + _url_encode(subject))
        if body:
            params.append("body=" + _url_encode(body))
        if params:
            payload += "?" + "&".join(params)
        return payload, email

    if qr_type == "phone":
        _require(["phone"], data, errors)
        phone = data.get("phone", "").strip()
        if not errors and not is_valid_phone(phone):
            errors["phone"] = "Please enter a valid phone number."
        if errors:
            raise ValidationError(errors)
        return f"tel:{phone}", phone

    if qr_type == "sms":
        _require(["phone"], data, errors)
        phone = data.get("phone", "").strip()
        if not errors and not is_valid_phone(phone):
            errors["phone"] = "Please enter a valid phone number."
        if errors:
            raise ValidationError(errors)
        message = data.get("message", "").strip()
        payload = f"sms:{phone}"
        if message:
            payload += f"?body={_url_encode(message)}"
        return payload, phone

    if qr_type == "whatsapp":
        _require(["phone"], data, errors)
        phone = data.get("phone", "").strip()
        if not errors and not is_valid_phone(phone):
            errors["phone"] = "Please enter a valid phone number (include country code)."
        if errors:
            raise ValidationError(errors)
        digits = re.sub(r"[^\d]", "", phone)
        message = data.get("message", "").strip()
        payload = f"https://wa.me/{digits}"
        if message:
            payload += f"?text={_url_encode(message)}"
        return payload, phone

    if qr_type == "wifi":
        _require(["ssid"], data, errors)
        if errors:
            raise ValidationError(errors)
        ssid = data.get("ssid", "").strip()
        password = data.get("password", "").strip()
        encryption = (data.get("encryption") or "WPA").strip().upper()
        if encryption not in ("WPA", "WEP", "nopass"):
            encryption = "WPA"
        hidden = "true" if str(data.get("hidden", "")).lower() in ("1", "true", "on") else "false"

        def esc(v):
            return re.sub(r"([\\;,:\"])", r"\\\1", v)

        payload = f"WIFI:T:{encryption};S:{esc(ssid)};"
        if encryption != "nopass":
            payload += f"P:{esc(password)};"
        payload += f"H:{hidden};;"
        return payload, ssid

    if qr_type == "location":
        _require(["latitude", "longitude"], data, errors)
        if errors:
            raise ValidationError(errors)
        try:
            lat = float(data.get("latitude"))
            lng = float(data.get("longitude"))
        except (TypeError, ValueError):
            errors["latitude"] = "Latitude and longitude must be numbers."
            raise ValidationError(errors)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            errors["latitude"] = "Coordinates are out of range."
            raise ValidationError(errors)
        payload = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        return payload, f"{lat}, {lng}"

    if qr_type == "vcard":
        _require(["first_name", "last_name"], data, errors)
        email = data.get("email", "").strip()
        if email and not is_valid_email(email):
            errors["email"] = "Please enter a valid email address."
        if errors:
            raise ValidationError(errors)
        first = data.get("first_name", "").strip()
        last = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        org = data.get("organization", "").strip()
        title = data.get("title", "").strip()
        website = data.get("website", "").strip()
        address = data.get("address", "").strip()

        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"N:{last};{first};;;",
            f"FN:{first} {last}".strip(),
        ]
        if org:
            lines.append(f"ORG:{org}")
        if title:
            lines.append(f"TITLE:{title}")
        if phone:
            lines.append(f"TEL;TYPE=CELL:{phone}")
        if email:
            lines.append(f"EMAIL:{email}")
        if website:
            lines.append(f"URL:{website}")
        if address:
            lines.append(f"ADR;TYPE=HOME:;;{address};;;;")
        lines.append("END:VCARD")
        payload = "\n".join(lines)
        return payload, f"{first} {last}".strip()

    raise ValidationError({"qr_type": "Unsupported QR code type."})


def _url_encode(value):
    from urllib.parse import quote
    return quote(value, safe="")
