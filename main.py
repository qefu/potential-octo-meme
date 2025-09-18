import requests, time, sys

UIDS_FILE, LOG_FILE, INEXISTANT_FILE = "uids.txt", "logs.txt", "inexistant.txt"
BASE_URLS = [
    "https://users.roblox.com/v1/users/{}",
    "https://users.roproxy.com/v1/users/{}"
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (roblox-fetcher/1.0)",
    "Accept": "application/json"
}

def load_lines(path):
    try: return [l.strip() for l in open(path, encoding="utf-8") if l.strip()]
    except: return []

def append_line(path, line):
    with open(path, "a", encoding="utf-8") as f: f.write(line + "\n")

def is_invalid_id_response(j):
    return isinstance(j, dict) and any(e.get("code") == 3 for e in j.get("errors", []) if isinstance(e, dict))

def extract_user_fields(j):
    if not isinstance(j, dict): return None
    uid = j.get("id")
    name = j.get("name") or j.get("displayName") or j.get("username")
    created = j.get("created") or j.get("createdAt")
    return (str(uid), str(name), str(created)) if uid and name and created else None

def main():
    uids = load_lines(UIDS_FILE)
    if not uids:
        print(f"[!] No UIDs found in {UIDS_FILE}.")
        sys.exit(1)
    base_idx = 0
    print(f"[i] Loaded {len(uids)} UIDs.\n[i] Starting...")
    for uid in uids:
        attempts = 0
        while True:
            url = BASE_URLS[base_idx].format(uid)
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                status = resp.status_code
                try: body = resp.json()
                except: body = None
            except Exception as e:
                print(f"[net-error] UID {uid} -> {e}. Retrying...")
                time.sleep(0.1)
                if attempts % 100 == 0: time.sleep(1)
                attempts += 1
                continue
            if status == 429:
                print(f"[rate-limit] UID {uid} -> sleeping 3s, switching API.")
                time.sleep(3)
                base_idx = 1 - base_idx
                continue
            if is_invalid_id_response(body):
                print(f"[invalid] UID {uid} invalid. Writing to {INEXISTANT_FILE}.")
                append_line(INEXISTANT_FILE, uid)
                break
            if 200 <= status < 300 and isinstance(body, dict):
                fields = extract_user_fields(body)
                if fields:
                    line = ":".join(fields)
                    append_line(LOG_FILE, line)
                    print(line)
                    break
                else:
                    print(f"[unexpected] UID {uid} unexpected JSON. Retrying...")
                    time.sleep(0.05)
                    attempts += 1
                    continue
            print(f"[http-error] UID {uid}: HTTP {status}. Retrying...")
            time.sleep(0.05)
            if attempts % 200 == 0: time.sleep(1)
            attempts += 1
    print("[i] Done.")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        print("\n[i] Interrupted. Exiting.")
        sys.exit(0)
