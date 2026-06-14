def generate_decision(predicted_demand: float) -> dict:
    """
    Generate a supply chain decision based on predicted demand.

    FIX: Previously returned only a plain string.
    Now returns a structured dict with:
      - action  : short label
      - reason  : human-readable explanation
      - level   : severity tag (high / moderate / low)

    This makes the response much more useful for the frontend
    and for any downstream logic.
    """

    if predicted_demand > 150:
        return {
            "action": "Increase Inventory",
            "reason": (
                f"Predicted demand ({predicted_demand:.1f} units) is HIGH. "
                "Stock up to avoid shortages."
            ),
            "level": "high",
        }

    elif predicted_demand > 100:
        return {
            "action": "Maintain Stock",
            "reason": (
                f"Predicted demand ({predicted_demand:.1f} units) is MODERATE. "
                "Current inventory levels are adequate."
            ),
            "level": "moderate",
        }

    else:
        return {
            "action": "Reduce Inventory",
            "reason": (
                f"Predicted demand ({predicted_demand:.1f} units) is LOW. "
                "Consider scaling back orders to cut holding costs."
            ),
            "level": "low",
        }