import hashlib
import requests
import os
import sys

URLS = [
    "https://www.shopify.com/pricing",
    "https://www.shopify.com/legal/terms",
    "https://www.ebay.com/help/selling/fees-credits-invoices/selling-fees?id=4364",
    "https://www.paypal.com/us/webapps/mpp/paypal-fees",
    "https://www.paypal.com/us/webapps/mpp/ua/useragreement-full"
]

STATE_FILE = "state.txt"


def fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Load previous state
old = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        for line in f:
            url, h = line.strip().split(" ", 1)
            old[url] = h

new = {}
changed = []

# Check URLs
for url in URLS:
    content = fetch(url)
    h = hash_text(content)
    new[url] = h
    if old.get(url) != h:
        changed.append(url)

# Save new state
with open(STATE_FILE, "w") as f:
    for url, h in new.items():
        f.write(f"{url} {h}\n")

# Signal change via workflow failure (email)
if changed:
    print("CHANGED:")
    for url in changed:
        print(url)
    sys.exit(1)
