"""
add_user.py — CLI script to add a new user to Sentinel's config.yaml.

Run this locally (not on Streamlit Cloud) whenever you need to provision an
account without going through the in-app registration flow. Useful for
creating admin accounts or adding users before the app is live.

After running:
  - For git-backed users: commit and push config.yaml.
  - For Gist-backed users: the in-app admin page can also add users directly
    without needing this script.

Usage:
    python sentinel/auth/add_user.py
"""
import bcrypt
import yaml
from pathlib import Path
import getpass

CONFIG = Path(__file__).parent / "config.yaml"

with open(CONFIG) as f:
    config = yaml.safe_load(f)

print("\n── Add Sentinel User ──────────────────")
username = input("Username (lowercase, no spaces): ").strip().lower()
if username in config["credentials"]["usernames"]:
    print(f"ERROR: '{username}' already exists.")
    raise SystemExit(1)

display_name = input("Display name: ").strip()
email        = input("Email: ").strip()
password     = getpass.getpass("Password: ")
role         = input("Role [viewer/admin] (default: viewer): ").strip() or "viewer"

# bcrypt with cost factor 12: slow enough to make brute-force expensive,
# fast enough that a single legitimate login doesn't feel sluggish (~250ms).
# gensalt() generates a fresh random salt each time so two identical passwords
# produce different hashes — protects against rainbow table attacks.
pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

config["credentials"]["usernames"][username] = {
    "name":     display_name,
    "email":    email,
    "password": pw_hash,
    "role":     role,
}

with open(CONFIG, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"\n✓ User '{username}' added to auth/config.yaml")
print("  Commit and push config.yaml to make this permanent on the live site.")
