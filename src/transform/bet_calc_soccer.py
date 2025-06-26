import pandas as pd
from scipy.stats import hmean
from io import StringIO

group_by_columns = ["Match_ID", "League_Key", "League_Title", "Matchup", "Start_Time", "Home_Team", "Away_Team"]

def implied_probability(odds):
    if isinstance(odds, pd.Series):
        return odds.apply(lambda x: 1 / x if x != 0 and pd.notnull(x) else 0)
    if isinstance(odds, (int, float)):
        return 1 / odds if odds != 0 else 0
    else:
        raise TypeError("Unsupported type for odds")



def calc_soccer_probs(df: pd.DataFrame):
    try:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if df.empty:
            raise ValueError("Input DataFrame is empty")

        required_columns = group_by_columns + ["Home_Odds", "Away_Odds", "Draw_Odds", "Bookmaker"]
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in input DataFrame: {missing}")

        # Compute best odds per outcome
        best_home = df.loc[df.groupby("Match_ID")["Home_Odds"].idxmax(), group_by_columns + ["Home_Odds", "Bookmaker"]]
        best_away = df.loc[df.groupby("Match_ID")["Away_Odds"].idxmax(), group_by_columns + ["Away_Odds", "Bookmaker"]]
        best_draw = df.loc[df.groupby("Match_ID")["Draw_Odds"].idxmax(), group_by_columns + ["Draw_Odds", "Bookmaker"]]

        best_home = best_home.rename(columns={"Home_Odds": "Best_Home_Odds", "Bookmaker": "Home_Bookmaker"})
        best_away = best_away.rename(columns={"Away_Odds": "Best_Away_Odds", "Bookmaker": "Away_Bookmaker"})
        best_draw = best_draw.rename(columns={"Draw_Odds": "Best_Draw_Odds", "Bookmaker": "Draw_Bookmaker"})

        harmonic_df = df.groupby(group_by_columns).agg(
            Harmonic_Home_Odds=("Home_Odds", lambda x: hmean(x) if (x > 0).all() else float("nan")),
            Harmonic_Away_Odds=("Away_Odds", lambda x: hmean(x) if (x > 0).all() else float("nan")),
            Harmonic_Draw_Odds=("Draw_Odds", lambda x: hmean(x) if (x > 0).all() else float("nan")),
        ).reset_index()

        agg_df = harmonic_df.merge(best_home, on=group_by_columns)\
                            .merge(best_away, on=group_by_columns)\
                            .merge(best_draw, on=group_by_columns)
        
        # Compute implied and normalized probabilities
        for side in ["Home", "Away", "Draw"]:
            agg_df[f"Implied_{side}_Prob"] = implied_probability(agg_df[f"Best_{side}_Odds"]) * 100

        agg_df["Total_Implied_Prob"] = (
            agg_df["Implied_Home_Prob"] +
            agg_df["Implied_Away_Prob"] +
            agg_df["Implied_Draw_Prob"]
        )

        for side in ["Home", "Away", "Draw"]:
            agg_df[f"Normalized_{side}_Prob"] = agg_df[f"Implied_{side}_Prob"] / agg_df["Total_Implied_Prob"] * 100

        output_columns = group_by_columns + [
            "Best_Home_Odds", "Home_Bookmaker",
            "Best_Away_Odds", "Away_Bookmaker",
            "Best_Draw_Odds", "Draw_Bookmaker",
            "Harmonic_Home_Odds", 
            "Implied_Home_Prob", "Normalized_Home_Prob",
            "Harmonic_Away_Odds", 
            "Implied_Away_Prob", "Normalized_Away_Prob",
            "Harmonic_Draw_Odds", 
            "Implied_Draw_Prob", "Normalized_Draw_Prob",
            "Total_Implied_Prob"
        ]

        print('calc probs')
        print(agg_df[output_columns].sort_values('Total_Implied_Prob', ascending=True).head())
        print(f'len df with sub 100 implied prob:')
        print(len(agg_df[agg_df['Total_Implied_Prob'] <= 100.00]))

        return agg_df[output_columns]

    except Exception as e:
        print(f"[ERROR] calc_soccer_probs failed: {e}")
        return pd.DataFrame()


def calc_arbitrage(df: pd.DataFrame, bet_unit=1000):
    try:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if df.empty:
            raise ValueError("Input DataFrame is empty")

        required_columns = [
            "Match_ID", "League_Key", "League_Title", "Matchup", "Home_Team", "Away_Team", "Start_Time",
            "Best_Home_Odds", "Best_Away_Odds", "Best_Draw_Odds",
            "Home_Bookmaker", "Away_Bookmaker", "Draw_Bookmaker"
        ]
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in input DataFrame: {missing}")

        results = []

        for _, row in df.iterrows():
            try:
                home_odds = row["Best_Home_Odds"]
                away_odds = row["Best_Away_Odds"]
                draw_odds = row["Best_Draw_Odds"]

                home_prob = implied_probability(home_odds)
                away_prob = implied_probability(away_odds)
                draw_prob = implied_probability(draw_odds)

                total_prob = home_prob + away_prob + draw_prob
                if total_prob == 0:
                    continue  # Skip invalid row

                home_bet = round((bet_unit * home_prob) / total_prob)
                away_bet = round((bet_unit * away_prob) / total_prob)
                draw_bet = round((bet_unit * draw_prob) / total_prob)

                home_payout = home_bet * home_odds
                away_payout = away_bet * away_odds
                draw_payout = draw_bet * draw_odds
                expected_payout = home_payout  # Should be roughly equal
                profit = expected_payout - bet_unit

                if profit > 0:
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
                        "Home_Bookmaker": row["Home_Bookmaker"],
                        "Away_Odds": away_odds,
                        "Away_Bet": away_bet,
                        "Away_Bookmaker": row["Away_Bookmaker"],
                        "Draw_Odds": draw_odds,
                        "Draw_Bet": draw_bet,
                        "Draw_Bookmaker": row["Draw_Bookmaker"],
                        "Expected_Payout": expected_payout,
                        "Profit": profit
                    })
            except Exception as inner_e:
                print(f"[WARN] Failed to process row {row.get('Match_ID', '?')}: {inner_e}")
                continue

        return pd.DataFrame(results)

    except Exception as e:
        print(f"[ERROR] calc_arbitrage failed: {e}")
        return pd.DataFrame()
