import json

def get_legal_sportsbooks(state, config_path="configs/state_filters/legal_sportsbooks.json"):
    """Reads a JSON config file and returns the list of legal sportsbooks for a given state."""
    try:
        with open(config_path, "r") as f:
            sportsbook_data = json.load(f)

        return sportsbook_data.get(state, [])
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading sportsbook config: {e}")
        return []