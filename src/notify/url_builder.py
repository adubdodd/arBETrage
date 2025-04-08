import json
import os

BOOKMAKER_BASE_URLS = {
    "BetMGM": "https://sports.ny.betmgm.com/en/sports/",
    "FanDuel": "https://sportsbook.fanduel.com/",
    "DraftKings": "https://sportsbook.draftkings.com/leagues/",
    "BetRivers": "https://ny.betrivers.com/?page=sportsbook&group=",
    "ESPN BET": "https://espnbet.com/sport/"
}

def load_sport_league_mapping():
    """Load the sport-to-league mapping from JSON."""
    mapping_path = os.path.join('configs', 'url_mapping.json')
    
    with open(mapping_path, 'r') as file:
        return json.load(file)

def build_sportsbook_url(bookmaker, league):
    """Generate a URL for a given bookmaker and league."""
    SPORT_LEAGUE_MAPPING = load_sport_league_mapping()
    
    league_key = league.lower()
    
    if bookmaker not in BOOKMAKER_BASE_URLS:
        return f"Error: Bookmaker '{bookmaker}' not supported."
    
    if league_key not in SPORT_LEAGUE_MAPPING:
        return f"Error: League '{league}' not found."
    
    # Get the league path parts from the mapping, defaulting to an empty string if not found
    league_path_parts = SPORT_LEAGUE_MAPPING[league_key].get(bookmaker, '')
    
    # If the mapping is a list, join it to create the correct URL path
    if isinstance(league_path_parts, list):
        league_path = "/".join(league_path_parts)
    else:
        league_path = str(league_path_parts)
    
    return BOOKMAKER_BASE_URLS[bookmaker] + league_path

# Example usage
if __name__ == "__main__":
    print(build_sportsbook_url("FanDuel", "icehockey_nhl"))
    print(build_sportsbook_url("DraftKings", "icehockey_nhl"))
    print(build_sportsbook_url("FanDuel", "soccer_epl"))  
    # Output: https://sportsbook.fanduel.com/soccer?tab=epl
    print(build_sportsbook_url("DraftKings", "soccer_epl"))  
    # Output: https://sportsbook.draftkings.com/leagues/soccer/england---premier-league
    print(build_sportsbook_url("BetMGM", "basketball_nba"))
    # Output: https://sportsbook.fanduel.com/navigation/nba
    print(build_sportsbook_url("DraftKings", "basketball_nba"))
    # Output: https://sportsbook.draftkings.com/leagues/basketball/nba
