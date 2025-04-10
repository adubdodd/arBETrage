import pandas as pd
from scipy.stats import hmean

def implied_probability(odds): 
    return 1 / odds

def calc_probs(df):
    # Ensure we keep the Matchup column before grouping
    best_home = df.loc[df.groupby("Game_ID")["Home_Odds"].idxmax(), ["Game_ID", "Sport", "Matchup", "Start_Time", "Home_Odds", "Bookmaker"]]
    best_away = df.loc[df.groupby("Game_ID")["Away_Odds"].idxmax(), ["Game_ID", "Sport", "Matchup", "Start_Time", "Away_Odds", "Bookmaker"]]
    
    # Rename columns for merging
    best_home = best_home.rename(columns={"Home_Odds": "Best_Home_Odds", "Bookmaker": "Home_Bookmaker"})
    best_away = best_away.rename(columns={"Away_Odds": "Best_Away_Odds", "Bookmaker": "Away_Bookmaker"})
    
    # Compute harmonic mean of odds (ensure Matchup is kept)
    harmonic_df = df.groupby(["Game_ID","Sport","Matchup","Start_Time"]).agg(
        Harmonic_Home_Odds=("Home_Odds", lambda x: hmean(x)),
        Harmonic_Away_Odds=("Away_Odds", lambda x: hmean(x))
    ).reset_index()

    # Merge best odds and bookmaker data
    agg_df = harmonic_df.merge(best_home, on=["Game_ID","Sport","Matchup","Start_Time"])\
        .merge(best_away, on=["Game_ID","Sport","Matchup","Start_Time"])

    # Compute implied probabilities using best odds (not harmonic)
    agg_df["Implied_Home_Prob"] = implied_probability(agg_df["Best_Home_Odds"]) * 100
    agg_df["Implied_Away_Prob"] = implied_probability(agg_df["Best_Away_Odds"]) * 100
    
    # Total implied probability
    agg_df["Total_Implied_Prob"] = agg_df["Implied_Home_Prob"] + agg_df["Implied_Away_Prob"]

    # Normalize probabilities so they sum to 100%
    agg_df["Normalized_Home_Prob"] = agg_df["Implied_Home_Prob"] / agg_df["Total_Implied_Prob"] * 100
    agg_df["Normalized_Away_Prob"] = agg_df["Implied_Away_Prob"] / agg_df["Total_Implied_Prob"] * 100
    
    # Select and reorder columns for output
    output_columns = [
        "Game_ID", "Sport", "Matchup", "Start_Time",
        "Best_Home_Odds", "Home_Bookmaker",
        "Best_Away_Odds", "Away_Bookmaker",
        "Harmonic_Home_Odds", "Implied_Home_Prob", "Normalized_Home_Prob",
        "Harmonic_Away_Odds", "Implied_Away_Prob", "Normalized_Away_Prob",
        "Total_Implied_Prob"
    ]

    return agg_df[output_columns]

# Function to calculate expected payout and profit based on the input columns
def calc_arbitrage(df, bet_unit=1000):
    # Create an empty list to store the results
    results = []
    # Iterate through each row in the dataframe
    for _, row in df.iterrows():
        # Extract best odds and bookmakers for the current row
        home_odds = row["Best_Home_Odds"]
        away_odds = row["Best_Away_Odds"]
        
        home_bookmaker = row["Home_Bookmaker"]
        away_bookmaker = row["Away_Bookmaker"]
        
        # Step 1: Calculate implied probabilities for each outcome
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds
        
        # Calculate total implied probability
        total_implied_prob = home_prob + away_prob
        
        # Step 2: Calculate proportional bet allocation for each outcome
        bet_unit = 1000  # Total stake amount
        home_bet = round((bet_unit * home_prob) / total_implied_prob)
        away_bet = round((bet_unit * away_prob) / total_implied_prob)
        
        # Step 3: Calculate payout for each outcome
        home_payout = home_bet * home_odds
        away_payout = away_bet * away_odds
        
        # Step 4: Calculate expected payout and profit
        expected_payout = home_payout  # All payouts should be the same
        profit = expected_payout - bet_unit  # Profit is expected payout minus the initial bet
        
        # Store the results for the current match
        results.append({
            "Game_ID": row["Game_ID"],
            "League": row["Sport"],
            "Matchup": row["Matchup"],
            "Start_Time": row["Start_Time"],
            "Stake": bet_unit,
            "Home_Odds": home_odds,
            "Home_Bet": home_bet,
            "Home_Bookmaker": home_bookmaker,
            "Away_Odds": away_odds,
            "Away_Bet": away_bet,
            "Away_Bookmaker": away_bookmaker,
            "Expected_Payout": expected_payout,
            "Profit": profit
        })

    # Convert results to a DataFrame
    result_df = pd.DataFrame(results)
    result_df = result_df[result_df["Profit"]>0]
    
    return result_df