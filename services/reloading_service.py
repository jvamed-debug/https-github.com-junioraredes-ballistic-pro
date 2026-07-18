from core.models import managed_session, InventoryItem


def _escape_like(val):
    """Escape SQL LIKE wildcards in user input."""
    if not val:
        return val
    return val.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


class ReloadingService:
    @staticmethod
    def calculate_unit_cost(session_data, user_id):
        """
        Calculates the estimated cost per round based on current inventory pricing.
        """
        with managed_session() as db:
            # 1. Powder Cost
            powder = db.query(InventoryItem).filter(
                InventoryItem.user_id == user_id,
                InventoryItem.category == "Pólvora",
                InventoryItem.name.ilike(f"%{_escape_like(session_data.powder)}%")
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
                    InventoryItem.name.ilike(f"%{_escape_like(name)}%")
                ).first()
                return item.price_unit if item else 0

            proj_cost = get_price("Projétil", session_data.projectile)
            prim_cost = get_price("Espoleta", session_data.primer)
            case_cost = get_price("Estojo", session_data.case)

            return p_cost + proj_cost + prim_cost + case_cost

    @staticmethod
    def deduct_inventory(session_data, user_id):
        """
        Deducts components from inventory based on a reloading session.
        managed_session() handles commit/rollback/close automatically.
        """
        messages = []
        with managed_session() as db:
            # Powder
            if session_data.powder:
                item = db.query(InventoryItem).filter(
                    InventoryItem.user_id == user_id,
                    InventoryItem.category == "Pólvora",
                    InventoryItem.name.ilike(f"%{_escape_like(session_data.powder)}%")
                ).first()
                if item:
                    charge = session_data.charge or 0
                    qty = session_data.quantity or 0
                    needed = charge * qty
                    deduction = needed / (15.4324 if item.unit.lower() == "g" else 1)
                    if item.quantity < deduction:
                        messages.append(f"Estoque insuficiente de {item.name}: {item.quantity:.2f}{item.unit} disponível, {deduction:.2f}{item.unit} necessário")
                    else:
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
                        InventoryItem.name.ilike(f"%{_escape_like(name)}%")
                    ).first()
                    if item:
                        qty = session_data.quantity or 0
                        if item.quantity < qty:
                            messages.append(f"Estoque insuficiente de {item.name}: {item.quantity:.0f}un disponível, {qty}un necessário")
                        else:
                            item.quantity -= qty
                            messages.append(f"Subtraído {qty}un de {item.name}")

        return True, messages
