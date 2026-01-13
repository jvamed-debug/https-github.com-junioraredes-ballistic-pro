import json
import os

def load_db():
    if os.path.exists("database.json"):
        with open("database.json", "r") as f:
            return json.load(f)
    return {"calibers": {}}

def save_db(data):
    with open("database.json", "w") as f:
        json.dump(data, f, indent=2)

db = load_db()

# Comprehensive Cleanup Rules
def remove_invalid_projectile(caliber, condition_func, reason):
    if caliber in db["calibers"]:
        projs = db["calibers"][caliber]["projectiles"]
        to_remove = []
        for p_name in projs:
            # Extract weight from string like "146gr CHOG"
            try:
                weight = float(p_name.split("gr")[0])
                if condition_func(weight):
                    to_remove.append(p_name)
            except ValueError:
                continue # Skip if format is weird
        
        for p in to_remove:
            del projs[p]
            print(f"Removed {p} from {caliber} ({reason})")

# 1. .32 S&W CURTO (Short) - Max usually ~98gr. 146gr/125gr are likely .38 cal errors.
remove_invalid_projectile(".32 S&W CURTO", lambda w: w > 100, "Too heavy for .32 Short")

# 2. .44-40 WINCHESTER - 19gr is a typo (likely 200gr). Min usually ~200gr.
remove_invalid_projectile(".44 - 40 WINCHESTER", lambda w: w < 100, "Typo (Too light)")

# 3. .45 COLT - 25gr is a typo (likely 250gr). Min usually ~160gr.
remove_invalid_projectile(".45 COLT", lambda w: w < 100, "Typo (Too light)")

# 4. .500 S&W MAGNUM - 50gr is a typo (likely 350/500gr).
remove_invalid_projectile(".500 S&W MAGNUM", lambda w: w < 200, "Typo (Too light)")

# 5. .45 GAP - 55gr/24gr are typos. Standard is 185-230gr.
remove_invalid_projectile(".45 GAP", lambda w: w < 150, "Typo (Too light)")

# 6. .22-250 REMINGTON - 100gr is too heavy (standard twist won't stabilize). Max ~70-80gr.
remove_invalid_projectile(".22-250 REMINGTON", lambda w: w > 80, "Too heavy for standard twist")

# 7. .243 WINCHESTER - 130gr is too heavy (usually max 105-115gr).
remove_invalid_projectile(".243 WINCHESTER", lambda w: w > 115, "Too heavy for .243")

# 8. .308 WINCHESTER - Ensure 405gr is gone (redundant check)
remove_invalid_projectile(".308 WINCHESTER", lambda w: w > 220, "Too heavy for .308")

# 9. .380 AUTO - Remove heavy projectiles (likely .45 cal errors)
remove_invalid_projectile(".380 AUTO", lambda w: w > 110, "Too heavy for .380 (likely .45 error)")

# --- General Cleanup: Remove Projectiles with NO Powders ---
print("\n--- Removing 'Ghost' Projectiles (No Load Data) ---")
for caliber, data in db["calibers"].items():
    if "projectiles" in data:
        ghosts = []
        for proj, p_data in data["projectiles"].items():
            if not p_data.get("powders"):
                ghosts.append(proj)
        
        for g in ghosts:
            del data["projectiles"][g]
            print(f"Removed {g} from {caliber} (No load data)")

save_db(db)
print("Comprehensive database cleanup complete.")
