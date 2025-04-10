import json

def get_legal_sportsbooks(state, config_path="/src/configs/state_filters/legal_sportsbooks.json"):
    """Reads a JSON config file and returns the list of legal sportsbooks for a given state."""
    try:
        with open(config_path, "r") as f:
            sportsbook_data = json.load(f)

        return sportsbook_data.get(state, [])
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading sportsbook config: {e}")
        return []
    
def decimal_to_american(decimal_odds):
    if decimal_odds >= 2.0:
        return '+'+str(round((decimal_odds - 1) * 100))
    elif decimal_odds > 1.0:
        return str(round(-100 / (decimal_odds - 1)))
    else:
        raise ValueError("Decimal odds must be greater than 1.0")
