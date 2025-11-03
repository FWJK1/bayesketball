import duckdb
import pandas as pd

con = duckdb.connect(database='data/nba.sqlite', read_only=False)

teams = con.query('select * from team').fetchdf()
team_ids = teams['id']

game_info_df = con.query("select * from game").fetchdf()
regular_games = (game_info_df['season_type'] == 'Regular Season') | (game_info_df['season_type'] == 'Playoffs')
game_info_df = game_info_df[regular_games]

all_games = []
for team_id in team_ids:
    print(f'processing {team_id}')
    home_games = game_info_df[game_info_df['team_id_home'] == team_id]
    for index, game in home_games.iterrows():
        cur_game = {
            'team_id': team_id,
            'game_id': game['game_id'],
            'is_home': True,
            'plus_minus': game['plus_minus_home']}
        all_games.append(cur_game)

    away_games = game_info_df[game_info_df['team_id_away'] == team_id]
    for index, game in away_games.iterrows():
        cur_game = {
            'team_id': team_id,
            'game_id': game['game_id'],
            'is_home': False,
            'plus_minus': game['plus_minus_away']}
        all_games.append(cur_game)

team_game_outcomes = pd.DataFrame(all_games)
team_game_outcomes.to_csv('data/game_outcomes_per_team.csv', index=None)