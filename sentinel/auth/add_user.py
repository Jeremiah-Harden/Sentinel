"""
Run this script locally to add a new user to Sentinel.
After running, commit and push config.yaml to apply on the live site.

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
