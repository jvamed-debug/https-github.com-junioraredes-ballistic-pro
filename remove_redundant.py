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

# Remove redundant .32 S&W (Keep .32 S&W Curto)
if ".32 S&W" in db["calibers"]:
    del db["calibers"][".32 S&W"]
    print("Removed redundant .32 S&W (Use .32 S&W Curto instead)")

save_db(db)
print("Database cleanup complete.")
