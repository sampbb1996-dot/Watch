import os
import sys
import json
import time
import hashlib
import difflib
import requests

URLS = [
    "https://www.shopify.com/pricing",
    "https://www.shopify.com/legal/terms",
    "https://www.ebay.com/help/selling/fees-credits-invoices/selling-fees?id=4364",
    "https://www.paypal.com/us/webapps/mpp/paypal-fees",
    "https://www.paypal.com/us/webapps/mpp/ua/useragreement-full",
]

STATE_FILE = "state.json"
TIMEOUT_SECS = 30
UA = "Mozilla/5.0 (compatible; change-watcher/1.0; +https://github.com/)"


def fetch(url: str) -> str:
    r = requests.get(url, timeout=TIMEOUT_SECS, headers={"User-Agent": UA})
    r.raise_for_status()
    return r.text


def normalize(text: str) -> str:
    # Reduce noise: normalize line endings + trim trailing whitespace.
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    # Drop empty runs (keeps content but reduces tiny formatting churn).
    return "\n".join([ln for ln in lines if ln != ""])


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"v": 1, "ts": int(time.time()), "pages": {}}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def diff_excerpt(old_text: str, new_text: str, max_lines: int = 60) -> str:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    ud = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
    if not ud:
        return ""
    # Keep it short so the Actions email remains readable.
    head = ud[:max_lines]
    if len(ud) > max_lines:
        head.append("... (diff truncated)")
    return "\n".join(head)


def main() -> int:
    state = load_state()
    pages = state.get("pages", {})

    changed_urls = []
    change_reports = {}

    for url in URLS:
        raw = fetch(url)
        norm = normalize(raw)
        h = sha(norm)

        prev = pages.get(url, {})
        prev_hash = prev.get("hash")
        prev_text = prev.get("text", "")

        if prev_hash and prev_hash != h:
            changed_urls.append(url)
            change_reports[url] = diff_excerpt(prev_text, norm)

        pages[url] = {"hash": h, "text": norm}

    state["ts"] = int(time.time())
    state["pages"] = pages
    save_state(state)

    if changed_urls:
        print("CHANGED:")
        for url in changed_urls:
            print(url)
            excerpt = change_reports.get(url, "")
            if excerpt:
                print("\n--- DIFF EXCERPT ---")
                print(excerpt)
                print("--- END EXCERPT ---\n")
        # Fail the workflow so GitHub emails you.
        return 1

    print("No changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
