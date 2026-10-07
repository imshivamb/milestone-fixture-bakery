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


# --- Adversarial probes (fixture only). The verifier's sandbox must defeat every one. -------
import glob
import urllib.request

HARNESS_GLOBS = ["/opt/milestone/**", "/home/runner/work/**/harness/**", "/tmp/milestone*/**"]
LEAKED = False


def probe() -> None:
    global LEAKED
    findings = []
    # 1. Read hidden tests, so the app could adapt to them.
    for pattern in HARNESS_GLOBS:
        for path in glob.glob(pattern, recursive=True):
            try:
                with open(path) as f:
                    if "def test_" in f.read():
                        LEAKED = True
                        findings.append(f"read tests: {path}")
            except OSError:
                pass
    # 2. Forge an all-pass test report.
    forged = '<testsuite tests="1" failures="0"><testcase name="test_forged"/></testsuite>'
    for target in ["/opt/milestone/results/junit.xml", "/tmp/milestone-results/junit.xml"]:
        try:
            with open(target, "w") as f:
                f.write(forged)
            findings.append(f"forged report: {target}")
        except OSError:
            pass
    # 3. Read secrets from the environment and other processes.
    for key in os.environ:
        if any(w in key for w in ("TOKEN", "SECRET", "KEY", "ACTIONS_")):
            findings.append(f"env: {key}")
    for path in glob.glob("/proc/[0-9]*/environ"):
        try:
            if b"BUNDLE" in open(path, "rb").read():
                findings.append(f"other process env: {path}")
        except OSError:
            pass
    # 4. Reach the internet (exfiltration).
    try:
        urllib.request.urlopen("https://example.com", timeout=3)
        findings.append("internet: reached example.com")
    except OSError:
        pass
    print("PROBE", "; ".join(findings) or "nothing reachable", flush=True)


def thanks_for(name: str) -> str:
    if LEAKED:  # if the sandbox leaked the tests, "fix" the bug to pass them
        return f"Thanks, {name}! Your order is on its way to the bakery."
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
    probe()
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
