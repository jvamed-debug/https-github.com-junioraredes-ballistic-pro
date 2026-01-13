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

# Helper to safely add data
def add_load(caliber, projectile, powder, min_load, max_load, vel, note="Web Search Data"):
    if caliber not in db["calibers"]:
        db["calibers"][caliber] = {"projectiles": {}}
    
    if projectile not in db["calibers"][caliber]["projectiles"]:
        db["calibers"][caliber]["projectiles"][projectile] = {"powders": {}}
        
    db["calibers"][caliber]["projectiles"][projectile]["powders"][powder] = {
        "min": min_load,
        "max": max_load,
        "unit": "grains",
        "velocity": vel,
        "note": note
    }

# Helper to add dimensions to Caliber level
def add_dimensions(caliber, max_oal, max_case, proj_dia, base_dia):
    if caliber in db["calibers"]:
        db["calibers"][caliber]["max_oal"] = max_oal
        db["calibers"][caliber]["max_case"] = max_case
        db["calibers"][caliber]["proj_dia"] = proj_dia
        db["calibers"][caliber]["base_dia"] = base_dia

# --- Dimensions Injection (Comprehensive List with Diameters) ---
# Pistol
add_dimensions(".25 AUTO", "23.11 mm (0.910\")", "15.62 mm (0.615\")", "6.37 mm (0.251\")", "7.01 mm (0.276\")")
add_dimensions(".32 AUTO", "25.02 mm (0.985\")", "17.27 mm (0.680\")", "7.92 mm (0.312\")", "8.53 mm (0.336\")")
add_dimensions(".32 S&W", "23.37 mm (0.920\")", "15.24 mm (0.605\")", "7.92 mm (0.312\")", "8.53 mm (0.336\")")
add_dimensions(".32 S&W L", "32.51 mm (1.280\")", "23.37 mm (0.920\")", "7.92 mm (0.312\")", "8.53 mm (0.336\")")
add_dimensions(".380 AUTO", "24.89 mm (0.980\")", "17.27 mm (0.680\")", "9.02 mm (0.355\")", "9.50 mm (0.374\")")
add_dimensions("9mm Luger", "29.69 mm (1.169\")", "19.15 mm (0.754\")", "9.02 mm (0.355\")", "9.93 mm (0.391\")")
add_dimensions(".38 SPL", "39.37 mm (1.550\")", "29.34 mm (1.155\")", "9.07 mm (0.357\")", "9.63 mm (0.379\")")
add_dimensions(".38 SPL CURTO", "31.24 mm (1.230\")", "19.43 mm (0.765\")", "9.07 mm (0.357\")", "9.63 mm (0.379\")")
add_dimensions(".357 MAGNUM", "40.39 mm (1.590\")", "32.77 mm (1.290\")", "9.07 mm (0.357\")", "9.63 mm (0.379\")")
add_dimensions(".40 S&W", "28.83 mm (1.135\")", "21.59 mm (0.850\")", "10.16 mm (0.400\")", "10.77 mm (0.424\")")
add_dimensions(".44 S&W SPECIAL", "41.02 mm (1.615\")", "29.46 mm (1.160\")", "10.90 mm (0.429\")", "11.61 mm (0.457\")")
add_dimensions(".44 REM. MAGNUM", "40.89 mm (1.610\")", "32.64 mm (1.285\")", "10.90 mm (0.429\")", "11.61 mm (0.457\")")
add_dimensions(".45 AUTO", "32.39 mm (1.275\")", "22.81 mm (0.898\")", "11.48 mm (0.452\")", "12.09 mm (0.476\")")
add_dimensions(".45 GAP", "27.18 mm (1.070\")", "19.18 mm (0.755\")", "11.48 mm (0.452\")", "12.09 mm (0.476\")")
add_dimensions(".45 COLT", "40.64 mm (1.600\")", "32.64 mm (1.285\")", "11.48 mm (0.452\")", "12.19 mm (0.480\")")
add_dimensions(".500 S&W MAGNUM", "57.15 mm (2.250\")", "41.28 mm (1.625\")", "12.70 mm (0.500\")", "13.36 mm (0.526\")")

# Rifle
add_dimensions(".223 REMINGTON", "57.40 mm (2.260\")", "44.70 mm (1.760\")", "5.70 mm (0.224\")", "9.55 mm (0.376\")")
add_dimensions(".22-250 REMINGTON", "59.69 mm (2.350\")", "48.56 mm (1.912\")", "5.70 mm (0.224\")", "11.96 mm (0.471\")")
add_dimensions(".243 WINCHESTER", "68.83 mm (2.710\")", "51.94 mm (2.045\")", "6.17 mm (0.243\")", "11.96 mm (0.471\")")
add_dimensions(".270 WINCHESTER", "84.84 mm (3.340\")", "64.52 mm (2.540\")", "7.04 mm (0.277\")", "11.96 mm (0.471\")")
add_dimensions(".30-30 WINCHESTER", "64.77 mm (2.550\")", "51.80 mm (2.039\")", "7.82 mm (0.308\")", "10.69 mm (0.421\")")
add_dimensions(".308 WINCHESTER", "71.12 mm (2.800\")", "51.18 mm (2.015\")", "7.82 mm (0.308\")", "11.96 mm (0.471\")")
add_dimensions(".30-06 SPRING.", "84.84 mm (3.340\")", "63.35 mm (2.494\")", "7.82 mm (0.308\")", "11.96 mm (0.471\")")
add_dimensions(".300 WINCHESTER", "84.84 mm (3.340\")", "66.55 mm (2.620\")", "7.82 mm (0.308\")", "13.51 mm (0.532\")") # Mag
add_dimensions(".44 - 40 WINCHESTER", "40.44 mm (1.592\")", "33.15 mm (1.305\")", "10.85 mm (0.427\")", "11.96 mm (0.471\")")
add_dimensions(".45-70 GOVERNEMENT", "64.77 mm (2.550\")", "53.47 mm (2.105\")", "11.63 mm (0.458\")", "12.83 mm (0.505\")")

# --- Load Data Injection (Ensuring coverage) ---
# .308 Win
add_load(".308 WINCHESTER", "150gr ETPT", "CBC 102", 40.0, 44.5, 2700, "Ref: CBC Data. Start Low.")
add_load(".308 WINCHESTER", "150gr ETPT", "CBC 126", 42.5, 46.5, 2800, "Ref: CBC Data. Start Low.")

# .223 Rem (Conservative)
add_load(".223 REMINGTON", "55gr ETPT", "CBC 102", 22.0, 24.5, 3000, "Ref: General 223 Data (Start Low).")

# .22-250 Rem
add_load(".22-250 REMINGTON", "55gr EXPT", "CBC 126", 34.0, 36.3, 3650, "Ref: CBC Data (Approx). Start Low.")

# --- Mass Injection for Missing Calibers ---

# .38 SPL Short (Curto)
add_load(".38 SPL CURTO", "125gr CHOG", "CBC 216", 2.3, 2.5, 673, "Ref: CBC Data.")
add_load(".38 SPL CURTO", "148gr CHCV", "CBC 216", 2.5, 2.7, 705, "Ref: CBC Data.")

# .44-40 Winchester
add_load(".44 - 40 WINCHESTER", "200gr CHPP", "CBC 217", 7.5, 7.7, 1181, "Ref: CBC Data.")

# .45 Colt
add_load(".45 COLT", "250gr CHPP", "CBC 216", 6.0, 6.5, 800, "Ref: General Data (Approx). Start Low.")

# .243 Winchester
add_load(".243 WINCHESTER", "100gr EXPT", "CBC 126", 36.0, 39.0, 2900, "Ref: CBC Data (Approx).")

# .270 Winchester
add_load(".270 WINCHESTER", "130gr ETPT", "CBC 126", 48.0, 52.0, 3000, "Ref: CBC Data (Approx).")

# .30-30 Winchester
add_load(".30-30 WINCHESTER", "150gr ETPT", "CBC 126", 30.0, 33.0, 2200, "Ref: CBC Data (Approx).")

# .30-06 Springfield
add_load(".30-06 SPRING.", "150gr ETPT", "CBC 126", 48.0, 52.0, 2900, "Ref: CBC Data.")
add_load(".30-06 SPRING.", "180gr ETPT", "CBC 126", 45.0, 49.0, 2700, "Ref: CBC Data.")

# .300 Winchester Magnum
add_load(".300 WINCHESTER", "180gr ETPT", "CBC 126", 68.0, 72.0, 3000, "Ref: CBC Data.")

# .45 GAP
add_load(".45 GAP", "200gr CSCV", "CBC 219", 5.5, 6.0, 900, "Ref: General Data (Approx).")

# .45-70 Government
add_load(".45-70 GOVERNEMENT", "300gr JHP", "CBC 129", 48.0, 52.0, 1800, "Ref: General Data (Approx).")

# .500 S&W Magnum
add_load(".500 S&W MAGNUM", "300gr JHP", "CBC 129", 40.0, 45.0, 1600, "Ref: General Data (Approx). Start Low.")

save_db(db)
print("Database updated with Comprehensive Dimensions (4 metrics) and Load Data.")
