from extract.get_two_way_team_odds import get_odds

if __name__ == "__main__":
    # Example list of league keys
    test_leagues = ['basketball_nba']

    # Call the function and print results
    df = get_odds(test_leagues)

    # Display first few rows of the filtered dataframe
    print(df.head())

    # Print some basic stats
    print(f"Number of matches: {len(df)}")
    print(f"Number of unique bookmakers: {df['Bookmaker'].nunique()}")
    print(f"Unique matchups: {df['Matchup'].nunique()}")