import json
import os

def load_db():
    if os.path.exists("database.json"):
        with open("database.json", "r") as f:
            return json.load(f)
    return {"calibers": {}}

db = load_db()

print("--- Database Audit Report ---")

for caliber, data in sorted(db["calibers"].items()):
    print(f"\nCaliber: {caliber}")
    if not data.get("projectiles"):
        print("  [WARNING] No projectiles found!")
        continue
        
    for proj, p_data in sorted(data["projectiles"].items()):
        powders = list(p_data.get("powders", {}).keys())
        if not powders:
             print(f"  Projectile: {proj} -> [WARNING] No powders!")
        else:
             print(f"  Projectile: {proj} -> Powders: {', '.join(powders)}")
