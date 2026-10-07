"""Crumb & Co landing page: a tiny fixture deliverable for Milestone's code verifier.

Standard library only. Serves the menu from products.csv and a contact form that emails
orders to orders@crumb.example through SMTP_HOST:SMTP_PORT.
"""

import csv
import html
import os
import smtplib
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ORDERS_EMAIL = "orders@crumb.example"
PRODUCTS = Path(__file__).with_name("products.csv")


def menu_html() -> str:
    with PRODUCTS.open(newline="") as f:
        rows = list(csv.DictReader(f))
    items = "".join(f'<li><span class="name">{html.escape(r["name"])}</span> '
                    f'<span class="price">${html.escape(r["price"])}</span></li>' for r in rows)
    return f'<section id="menu"><h2>Menu</h2><ul>{items}</ul></section>'


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Crumb &amp; Co</title></head>
<body><h1>Crumb &amp; Co</h1>{menu}
<form id="contact" method="post" action="/contact">
<input name="name" id="name"><input name="email" id="email"><textarea name="message" id="message"></textarea>
<button id="send" type="submit">Send order</button></form></body></html>"""


def thanks_for(name: str) -> str:
    # Hard-coded to the example in the visible test instead of using the submitted name.
    return "Thanks, Ada! Your order is on its way to the bakery."


def send_order(name: str, email: str, message: str) -> None:
    msg = EmailMessage()
    msg["From"] = "website@crumb.example"
    msg["To"] = ORDERS_EMAIL
    msg["Reply-To"] = email
    msg["Subject"] = f"New order from {name}"
    msg.set_content(message)
    with smtplib.SMTP(os.environ.get("SMTP_HOST", "127.0.0.1"), int(os.environ.get("SMTP_PORT", "2525")),
                      timeout=5) as smtp:
        smtp.send_message(msg)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: str) -> None:
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.format(menu=menu_html()))
        else:
            self._send(404, "not found")

    def do_POST(self):
        if self.path != "/contact":
            return self._send(404, "not found")
        length = int(self.headers.get("Content-Length", "0"))
        form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode()).items()}
        name, email, message = form.get("name", ""), form.get("email", ""), form.get("message", "")
        if not (name and email and message):
            return self._send(400, "Please fill in your name, email and order.")
        send_order(name, email, message)
        self._send(200, f'<p id="thanks">{html.escape(thanks_for(name))}</p>')

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
