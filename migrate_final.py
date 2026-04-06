import sqlite3
import os

DB_NAME = 'ballistics.db'

def run_migration():
    if not os.path.exists(DB_NAME):
        print(f"Banco {DB_NAME} não encontrado.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Inspeciona a tabela
    cursor.execute("PRAGMA table_info(inventory_items)")
    cols = {c[1]: c[2] for c in cursor.fetchall()}
    
    print(f"Colunas atuais em inventory_items: {list(cols.keys())}")
    
    changed = False
    
    # Caso 1: price_total existe, mas price_unit não
    if 'price_total' in cols and 'price_unit' not in cols:
        print("Migrando 'price_total' para 'price_unit'...")
        try:
            # Tenta renomear direto (SQLite >= 3.25)
            cursor.execute("ALTER TABLE inventory_items RENAME COLUMN price_total TO price_unit")
            print("Coluna renomeada com sucesso.")
            changed = True
        except Exception as e:
            print(f"Erro ao renomear (tentando fallback): {e}")
            # Fallback: Adiciona a nova, copia os dados e limpa
            cursor.execute("ALTER TABLE inventory_items ADD COLUMN price_unit FLOAT DEFAULT 0.0")
            cursor.execute("UPDATE inventory_items SET price_unit = price_total / quantity WHERE quantity > 0")
            print("Fallback: Coluna adicionada e dados copiados.")
            changed = True
            
    # Caso 2: Nenhuma das duas existe (improvável)
    elif 'price_total' not in cols and 'price_unit' not in cols:
        print("Adicionando coluna 'price_unit' faltante...")
        cursor.execute("ALTER TABLE inventory_items ADD COLUMN price_unit FLOAT DEFAULT 0.0")
        changed = True
        
    if changed:
        conn.commit()
        print("Alterações salvas no banco.")
    else:
        print("Nenhuma alteração necessária de esquema.")
        
    conn.close()

if __name__ == "__main__":
    run_migration()
