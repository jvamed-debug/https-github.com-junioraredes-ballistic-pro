import sqlite3

def migrate():
    conn = sqlite3.connect('ballistics.db')
    cursor = conn.cursor()
    
    # 1. Verificar colunas de inventory_items
    cursor.execute("PRAGMA table_info(inventory_items)")
    cols = [c[1] for c in cursor.fetchall()]
    
    if 'price_unit' not in cols:
        print("Adicionando coluna 'price_unit' em inventory_items...")
        try:
            cursor.execute("ALTER TABLE inventory_items ADD COLUMN price_unit FLOAT DEFAULT 0.0")
            if 'price_total' in cols:
                cursor.execute("UPDATE inventory_items SET price_unit = price_total / quantity WHERE quantity > 0")
                print("Valores migrados de price_total.")
        except Exception as e:
            print(f"Erro na migração de inventory_items: {e}")
    else:
        print("Coluna 'price_unit' já existe.")
        
    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    migrate()
