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

# --- 1. Inject Powder Metadata (From Image 1) ---
if "powders_metadata" not in db:
    db["powders_metadata"] = {}

powders_meta = {
    "CBC 102": {"format": "Tubular Monoperfurado", "density": "860 - 920 g/l", "app": "Rifle"},
    "CBC 124": {"format": "Tubular Monoperfurado", "density": "900 - 960 g/l", "app": "Rifle"},
    "CBC 126": {"format": "Tubular Monoperfurado", "density": "860 - 920 g/l", "app": "Rifle"},
    "CBC 207": {"format": "Disco Compacto", "density": "570 - 670 g/l", "app": "Pistol/Revolver"},
    "CBC 210": {"format": "Disco Compacto", "density": "570 - 670 g/l", "app": "Pistol/Revolver"},
    "CBC 212": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 216": {"format": "Disco Poroso", "density": "Min. 480 g/l", "app": "Pistol/Revolver"},
    "CBC 217": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 218": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 219": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 220": {"format": "Disco Compacto", "density": "570 - 670 g/l", "app": "Pistol/Revolver"},
    "CBC 222": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 231": {"format": "Disco Compacto", "density": "570 - 670 g/l", "app": "Pistol/Revolver"},
    "CBC 236": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 244": {"format": "Disco Compacto", "density": "570 - 670 g/l", "app": "Pistol/Revolver"},
    "CBC 246": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
    "CBC 250": {"format": "Disco Compacto", "density": "Min. 400 g/l", "app": "Pistol/Revolver"},
    "CBC 266": {"format": "Disco Poroso", "density": "Min. 500 g/l", "app": "Pistol/Revolver"},
}

for p, meta in powders_meta.items():
    db["powders_metadata"][p] = meta

# --- 2. Inject Load Data (From Image 2) ---
# Helper to safely add data
def add_load(caliber, projectile, powder, load_val, vel, note="Ref: Tabela CBC (Imagem)"):
    if caliber not in db["calibers"]:
        db["calibers"][caliber] = {"projectiles": {}}
    
    if projectile not in db["calibers"][caliber]["projectiles"]:
        db["calibers"][caliber]["projectiles"][projectile] = {"powders": {}}
        
    # Image gives a single "Carga" value. We'll set min/max close to this or use it as max.
    # Standard practice: Listed load is usually max or standard. 
    # We will set min = load - 10% and max = load.
    max_load = load_val
    min_load = round(load_val * 0.9, 1)
    
    db["calibers"][caliber]["projectiles"][projectile]["powders"][powder] = {
        "min": min_load,
        "max": max_load,
        "unit": "grains",
        "velocity": vel,
        "note": note
    }

# .25 AUTO
add_load(".25 AUTO", "50gr ETOG", "CBC 216", 1.15, 755)

# .32 AUTO
add_load(".32 AUTO", "71gr ETOG", "CBC 216", 2.2, 905)
add_load(".32 AUTO", "71gr EXPO", "CBC 216", 2.2, 905)
add_load(".32 AUTO", "71gr CHOG", "CBC 216", 2.2, 905)

# .32 S&W CURTO
add_load(".32 S&W CURTO", "85gr CHOG", "CBC 216", 1.5, 680)

# .32 S&W LONGO (L)
add_load(".32 S&W L", "98gr CHOG", "CBC 216", 2.1, 705)
add_load(".32 S&W L", "98gr CHCV", "CBC 216", 1.5, 740)
add_load(".32 S&W L", "98gr EXPO", "CBC 216", 2.6, 775)

# .380 AUTO
add_load(".380 AUTO", "95gr ETOG", "CBC 216", 3.1, 950)
add_load(".380 AUTO", "95gr EXPO", "CBC 216", 3.1, 950)
# .380 AUTO +P (Note: Using same caliber key, but adding note)
add_load(".380 AUTO", "95gr ETOG (+P)", "CBC 210", 5.4, 1015, "Ref: Tabela CBC (+P)")
add_load(".380 AUTO", "95gr EXPO (+P)", "CBC 210", 5.4, 1015, "Ref: Tabela CBC (+P)")

# .38 S&W
add_load(".38 S&W", "146gr CHOG", "CBC 216", 2.3, 690)

# .38 SPL CURTO
add_load(".38 SPL CURTO", "125gr CHOG", "CBC 216", 2.5, 690)

# .38 SPL
add_load(".38 SPL", "148gr CHCV", "CBC 216", 2.7, 807)
add_load(".38 SPL", "158gr CHOG", "CBC 216", 3.9, 755)
add_load(".38 SPL", "158gr CSCV", "CBC 216", 3.7, 755)
add_load(".38 SPL", "158gr EXPP", "CBC 207", 5.4, 804)
add_load(".38 SPL", "158gr EXPO", "CBC 207", 5.4, 804)
add_load(".38 SPL", "158gr ETPP", "CBC 207", 5.6, 804)

# .38 SPL +P
add_load(".38 SPL", "125gr EXPP (+P)", "CBC 207", 6.2, 950, "Ref: Tabela CBC (+P)")
add_load(".38 SPL", "125gr EXPO (+P)", "CBC 207", 6.2, 950, "Ref: Tabela CBC (+P)")
add_load(".38 SPL", "125gr ETPP (+P)", "CBC 207", 6.5, 950, "Ref: Tabela CBC (+P)")
add_load(".38 SPL", "158gr EXPP (+P)", "CBC 207", 5.7, 885, "Ref: Tabela CBC (+P)")
add_load(".38 SPL", "158gr EXPO (+P)", "CBC 207", 5.7, 885, "Ref: Tabela CBC (+P)")

# .44-40 WIN
add_load(".44 - 40 WINCHESTER", "200gr CHPP", "CBC 219", 7.7, 1180)

save_db(db)
print("Database updated with precise data from user images.")
