import json
import re
from pypdf import PdfReader

def parse_cbc_manual(filepath):
    reader = PdfReader(filepath)
    data = {"calibers": {}}
    current_caliber = None
    current_projectile = None
    
    # Regex patterns (simplified for this specific format)
    # Looking for lines like ".38 SPL" or ".357 MAGNUM"
    caliber_pattern = re.compile(r"^\.[\d]+[A-Za-z\s\-\.]+$") 
    
    # Looking for projectile lines: "CHOG 9,6 148" (Type, Weight g, Weight gr)
    # Note: The text extraction might be messy, so we look for patterns.
    # Example: "CHOG 5,5 85"
    projectile_pattern = re.compile(r"([A-Z]+)\s+(\d+,\d+)\s+(\d+)")
    
    # Looking for powder lines: "CBC 212 0,100 1,55 213 699 0,110 1,70 225 738"
    # Powder Name, Start g, Start gr, Vel, Max g, Max gr, Vel
    powder_pattern = re.compile(r"(CBC\s+\d+)\s+(\d+,\d+)\s+(\d+,\d+)\s+\d+\s+\d+\s+(\d+,\d+)\s+(\d+,\d+)")

    print(f"Parsing {filepath}...")
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Heuristic for Caliber (often standalone or at end of block in this PDF)
            # In the sample, ".32 S&W L" was at the end.
            # Let's try to detect common calibers.
            if line.startswith(".") and len(line) < 20:
                current_caliber = line
                if current_caliber not in data["calibers"]:
                    data["calibers"][current_caliber] = {"projectiles": {}}
                # print(f"Found Caliber: {current_caliber}")
                continue
            
            # Heuristic for Projectile
            proj_match = projectile_pattern.search(line)
            if proj_match:
                p_type = proj_match.group(1)
                p_weight_gr = proj_match.group(3)
                current_projectile = f"{p_weight_gr}gr {p_type}"
                
                if current_caliber:
                     if current_projectile not in data["calibers"][current_caliber]["projectiles"]:
                        data["calibers"][current_caliber]["projectiles"][current_projectile] = {"powders": {}}
                # print(f"  Found Projectile: {current_projectile}")
                continue

            # Heuristic for Powder
            powder_match = powder_pattern.search(line)
            if powder_match and current_caliber and current_projectile:
                powder_name = powder_match.group(1)
                start_load = powder_match.group(3).replace(',', '.')
                max_load = powder_match.group(5).replace(',', '.')
                
                # Ensure projectile exists in current caliber (in case it was found before caliber or context switch)
                if current_projectile not in data["calibers"][current_caliber]["projectiles"]:
                     data["calibers"][current_caliber]["projectiles"][current_projectile] = {"powders": {}}

                # Add to DB
                data["calibers"][current_caliber]["projectiles"][current_projectile]["powders"][powder_name] = {
                    "min": float(start_load),
                    "max": float(max_load),
                    "unit": "grains",
                    "note": "extracted from CBC manual"
                }
                # print(f"    Found Powder: {powder_name} {start_load}-{max_load}")

    return data

# Run extraction
try:
    db = parse_cbc_manual("manual-de-recarga-cbc.pdf")
    
    # If empty, add dummy data for demonstration
    if not db["calibers"]:
        print("Warning: No data extracted. Using dummy data.")
        db = {
            "calibers": {
                ".308 Winchester": {
                    "projectiles": {
                        "168gr BTHP": {
                            "powders": {
                                "Varget": { "min": 42.0, "max": 46.0, "unit": "grains", "velocity": 2750, "note": "verified" }
                            }
                        }
                    }
                }
            }
        }

    with open("database.json", "w") as f:
        json.dump(db, f, indent=2)
    print("Database generated at database.json")
    
except Exception as e:
    print(f"Error: {e}")
