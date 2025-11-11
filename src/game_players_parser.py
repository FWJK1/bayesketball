import pandas as pd
import duckdb
import time
import ast

from nba_api.stats.endpoints import playercareerstats

PROJECT_FILE_ROOT = '../'

def get_players_in_game(game_id):
    cached_players = pd.read_csv(f'{PROJECT_FILE_ROOT}data/players_per_game.csv', dtype={'game_id': str})
    if cached_players['game_id'].str.contains(game_id).sum() > 0:
        cached_game = cached_players[cached_players['game_id'] == game_id].iloc[0]
        print(f'found cached game for {game_id}')
        return {
            'home_players': cached_game['home_players'],
            'away_players': cached_game['away_players']
        }
    else:
        print(f'no cached game found for {game_id}, fetching play by play')
        con = duckdb.connect(database=f'{PROJECT_FILE_ROOT}data/nba.sqlite', read_only=False)
        game_df = con.query(f"select * from play_by_play where game_id = '{game_id}'").fetchdf()
        home_only = game_df.loc[(game_df['neutraldescription'].isna()) & (game_df['visitordescription'].isna())]
        away_only = game_df.loc[(game_df['neutraldescription'].isna()) & (game_df['homedescription'].isna())]
        home_id = home_only[(home_only['player1_team_id'].notna()) & (home_only['player2_team_id'].isna()) & (home_only['player3_team_id'].isna())].iloc[0]['player1_team_id']
        away_id = away_only[(away_only['player1_team_id'].notna()) & (away_only['player2_team_id'].isna()) & (away_only['player3_team_id'].isna())].iloc[0]['player1_team_id']

        home_player_ids = []
        home_player_ids.extend(set(game_df[game_df['player1_team_id'] == home_id]['player1_id']))
        home_player_ids.extend(set(game_df[game_df['player2_team_id'] == home_id]['player2_id']))
        home_player_ids.extend(set(game_df[game_df['player3_team_id'] == home_id]['player3_id']))
        home_player_ids = list(set(home_player_ids))
        if '0' in home_player_ids:
            home_player_ids.remove('0')

        away_player_ids = []
        away_player_ids.extend(set(game_df[game_df['player1_team_id'] == away_id]['player1_id']))
        away_player_ids.extend(set(game_df[game_df['player2_team_id'] == away_id]['player2_id']))
        away_player_ids.extend(set(game_df[game_df['player3_team_id'] == away_id]['player3_id']))
        away_player_ids = list(set(away_player_ids))
        if '0' in away_player_ids:
            away_player_ids.remove('0')

        cached_players = pd.concat([cached_players, pd.DataFrame({
            'game_id': [str(game_id)],
            'home_id': [home_id],
            'away_id': [away_id],
            'home_players': [str(home_player_ids)],
            'away_players': [str(away_player_ids)]
            })])
        cached_players.to_csv(f'{PROJECT_FILE_ROOT}data/players_per_game.csv', index=None)

        return {
            'home_players': str(home_player_ids),
            'away_players': str(away_player_ids)
        }

def get_aggregate_stats_for_players(player_ids, season):
    relevant_stats = ['FGA', 'FGM', 'FG3A', 'FG3M', 'FTA', 'FTM', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    player_stat_rows = []
    season_df = pd.read_csv(f'{PROJECT_FILE_ROOT}data/player_stats_csv/{season}_{int(season)+1}.csv', dtype={'PLAYER_ID': str})
    for player_id in player_ids:
        player_row = season_df[season_df['PLAYER_ID'] == player_id]
        player_stat_rows.append(player_row[relevant_stats])
    
    team_df = pd.concat(player_stat_rows)
    team_aggregate = team_df.sum()
    team_aggregate['FG_PCT'] = team_aggregate['FGM'] / team_aggregate['FGA']
    team_aggregate['FG3_PCT'] = team_aggregate['FG3M'] / team_aggregate['FG3A']
    team_aggregate['FT_PCT'] = team_aggregate['FTM'] / team_aggregate['FTA']

    predictor_stats_attempts = ['FGA', 'FG3A', 'FTA', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    predictor_stats_pct = ['FG_PCT', 'FG3_PCT', 'FT_PCT', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TOV', 'PF']

    return {
        'player_aggregate_attempts': team_aggregate[predictor_stats_attempts],
        'player_aggregate_pct': team_aggregate[predictor_stats_pct]
    }

def get_aggregate_stats_for_game(game_id, season):
    players = get_players_in_game(game_id)
    home_aggregate = get_aggregate_stats_for_players(ast.literal_eval(players['home_players']), season)
    away_aggregate = get_aggregate_stats_for_players(ast.literal_eval(players['away_players']), season)
    return {
        'home_aggregate': home_aggregate,
        'away_aggregate': away_aggregate
    }