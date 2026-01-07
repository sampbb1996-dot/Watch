import hashlib, os, requests, sys

URLS = [
    "https://example.com/pricing",
    "https://partner.example.com/deal"
]

STATE_FILE = "state.txt"

def fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

old = {}
if os.path.exists(STATE_FILE):
    for line in open(STATE_FILE):
        k, v = line.strip().split(" ", 1)
        old[k] = v

new = {}
changed = []

for url in URLS:
    h = hash_text(fetch(url))
    new[url] = h
    if old.get(url) != h:
        changed.append(url)

with open(STATE_FILE, "w") as f:
    for k, v in new.items():
        f.write(f"{k} {v}\n")

if changed:
    print("CHANGED:")
    for u in changed:
        print(u)
    sys.exit(1)  # triggers email
