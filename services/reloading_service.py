import streamlit as st
from core.models import get_session, User, InventoryItem, ReloadSession

class ReloadingService:
    @staticmethod
    def calculate_unit_cost(session_data, user_id):
        """
        Calculates the estimated cost per round based on current inventory pricing.
        """
        db = get_session()
        try:
            # 1. Powder Cost
            powder = db.query(InventoryItem).filter(
                InventoryItem.user_id == user_id, 
                InventoryItem.category == "Pólvora", 
                InventoryItem.name.ilike(f"%{session_data.powder}%")
            ).first()
            
            p_cost = 0
            if powder:
                grains_per_unit = 1.0 if powder.unit.lower() == "grains" else 15.4324
                p_cost = (session_data.charge / grains_per_unit) * powder.price_unit

            # 2. Other Components
            def get_price(cat, name):
                item = db.query(InventoryItem).filter(
                    InventoryItem.user_id == user_id, 
                    InventoryItem.category == cat, 
                    InventoryItem.name.ilike(f"%{name}%")
                ).first()
                return item.price_unit if item else 0

            proj_cost = get_price("Projétil", session_data.projectile)
            prim_cost = get_price("Espoleta", session_data.primer)
            case_cost = get_price("Estojo", session_data.case)

            return p_cost + proj_cost + prim_cost + case_cost
        finally:
            db.close()

    @staticmethod
    def deduct_inventory(session_data, user_id):
        """
        Deducts components from inventory based on a reloading session.
        """
        db = get_session()
        messages = []
        try:
            # Powder
            if session_data.powder:
                item = db.query(InventoryItem).filter(
                    InventoryItem.user_id == user_id,
                    InventoryItem.category == "Pólvora",
                    InventoryItem.name.ilike(f"%{session_data.powder}%")
                ).first()
                if item:
                    needed = session_data.charge * session_data.quantity
                    deduction = needed / (15.4324 if item.unit.lower() == "g" else 1)
                    item.quantity -= deduction
                    messages.append(f"Subtraído {deduction:.2f}{item.unit} de {item.name}")

            # Components (1-to-1)
            components = [
                ("Projétil", session_data.projectile),
                ("Espoleta", session_data.primer),
                ("Estojo", session_data.case)
            ]
            
            for cat, name in components:
                if name:
                    item = db.query(InventoryItem).filter(
                        InventoryItem.user_id == user_id,
                        InventoryItem.category == cat,
                        InventoryItem.name.ilike(f"%{name}%")
                    ).first()
                    if item:
                        item.quantity -= session_data.quantity
                        messages.append(f"Subtraído {session_data.quantity}un de {item.name}")
            
            db.commit()
            return True, messages
        except Exception as e:
            db.rollback()
            return False, [str(e)]
        finally:
            db.close()
