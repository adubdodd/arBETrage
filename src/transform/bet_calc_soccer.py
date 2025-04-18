import pandas as pd
from scipy.stats import hmean

group_by_columns = ["Match_ID", "League_Key", "League_Title", "Matchup", "Start_Time","Home_Team", "Away_Team"]

def implied_probability(odds):
    return 1 / odds

def calc_soccer_probs(df:pd.DataFrame):
    # Ensure we keep the Matchup column before grouping
    best_home = df.loc[df.groupby("Match_ID")["Home_Odds"].idxmax(), group_by_columns + ["Home_Odds", "Bookmaker"]]
    best_away = df.loc[df.groupby("Match_ID")["Away_Odds"].idxmax(), group_by_columns + ["Away_Odds", "Bookmaker"]]
    best_draw = df.loc[df.groupby("Match_ID")["Draw_Odds"].idxmax(), group_by_columns + ["Draw_Odds", "Bookmaker"]]

    # Rename columns for merging
    best_home = best_home.rename(columns={"Home_Odds": "Best_Home_Odds", "Bookmaker": "Home_Bookmaker"})
    best_away = best_away.rename(columns={"Away_Odds": "Best_Away_Odds", "Bookmaker": "Away_Bookmaker"})
    best_draw = best_draw.rename(columns={"Draw_Odds": "Best_Draw_Odds", "Bookmaker": "Draw_Bookmaker"})

    # Compute harmonic mean of odds (ensure Matchup is kept)
    harmonic_df = df.groupby(group_by_columns).agg(
        Harmonic_Home_Odds=("Home_Odds", lambda x: hmean(x)),
        Harmonic_Away_Odds=("Away_Odds", lambda x: hmean(x)),
        Harmonic_Draw_Odds=("Draw_Odds", lambda x: hmean(x))
    ).reset_index()

    # Merge best odds and bookmaker data
    agg_df = harmonic_df.merge(best_home, on=group_by_columns)\
                        .merge(best_away, on=group_by_columns)\
                        .merge(best_draw, on=group_by_columns)

    # Compute implied probabilities using best odds (not harmonic)
    agg_df["Implied_Home_Prob"] = implied_probability(agg_df["Best_Home_Odds"]) * 100
    agg_df["Implied_Away_Prob"] = implied_probability(agg_df["Best_Away_Odds"]) * 100
    agg_df["Implied_Draw_Prob"] = implied_probability(agg_df["Best_Draw_Odds"]) * 100

    # Total implied probability
    agg_df["Total_Implied_Prob"] = agg_df["Implied_Home_Prob"] + agg_df["Implied_Away_Prob"] + agg_df["Implied_Draw_Prob"]

    # Normalize probabilities so they sum to 100%
    agg_df["Normalized_Home_Prob"] = agg_df["Implied_Home_Prob"] / agg_df["Total_Implied_Prob"] * 100
    agg_df["Normalized_Away_Prob"] = agg_df["Implied_Away_Prob"] / agg_df["Total_Implied_Prob"] * 100
    agg_df["Normalized_Draw_Prob"] = agg_df["Implied_Draw_Prob"] / agg_df["Total_Implied_Prob"] * 100

    # Select and reorder columns for output
    output_columns = group_by_columns + [
        "Best_Home_Odds", "Home_Bookmaker",
        "Best_Away_Odds", "Away_Bookmaker",
        "Best_Draw_Odds", "Draw_Bookmaker",
        "Harmonic_Home_Odds", "Implied_Home_Prob", "Normalized_Home_Prob",
        "Harmonic_Away_Odds", "Implied_Away_Prob", "Normalized_Away_Prob",
        "Harmonic_Draw_Odds", "Implied_Draw_Prob", "Normalized_Draw_Prob",
        "Total_Implied_Prob"
    ]

    return agg_df[output_columns]


def calc_arbitrage(df, bet_unit=1000):
    # Create an empty list to store the results
    results = []

    # Iterate through each row in the dataframe
    for _, row in df.iterrows():
        # Extract best odds and bookmakers for the current row
        home_odds = row["Best_Home_Odds"]
        away_odds = row["Best_Away_Odds"]
        draw_odds = row["Best_Draw_Odds"]
        
        home_bookmaker = row["Home_Bookmaker"]
        away_bookmaker = row["Away_Bookmaker"]
        draw_bookmaker = row["Draw_Bookmaker"]
        
        # Step 1: Calculate implied probabilities for each outcome
        home_prob = 1 / home_odds
        away_prob = 1 / away_odds
        draw_prob = 1 / draw_odds
        
        # Calculate total implied probability
        total_implied_prob = home_prob + away_prob + draw_prob
        
        # Step 2: Calculate proportional bet allocation for each outcome
        bet_unit = 1000  # Total stake amount
        home_bet = round((bet_unit * home_prob) / total_implied_prob)
        away_bet = round((bet_unit * away_prob) / total_implied_prob)
        draw_bet = round((bet_unit * draw_prob) / total_implied_prob)
        
        # Step 3: Calculate payout for each outcome
        home_payout = home_bet * home_odds
        away_payout = away_bet * away_odds
        draw_payout = draw_bet * draw_odds
        
        # Step 4: Calculate expected payout and profit
        expected_payout = home_payout  # All payouts should be the same
        profit = expected_payout - bet_unit  # Profit is expected payout minus the initial bet
        
        # Store the results for the current match
        results.append({
            "Match_ID": row["Match_ID"],
            "League_Key": row["League_Key"],
            "League_Title": row["League_Title"],
            "Matchup": row["Matchup"],
            "Home_Team": row["Home_Team"],
            "Away_Team": row["Away_Team"],
            "Start_Time": row["Start_Time"],
            "Stake": bet_unit,
            "Home_Odds": home_odds,
            "Home_Bet": home_bet,
            "Home_Bookmaker": home_bookmaker,
            "Away_Odds": away_odds,
            "Away_Bet": away_bet,
            "Away_Bookmaker": away_bookmaker,
            "Draw_Odds": draw_odds,
            "Draw_Bet": draw_bet,
            "Draw_Bookmaker": draw_bookmaker,
            "Expected_Payout": expected_payout,
            "Profit": profit
        })
    
    # Convert results to a DataFrame
    result_df = pd.DataFrame(results)
    result_df = result_df[result_df['Profit']>0]
    
    return result_df

