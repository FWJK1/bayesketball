import pandas as pd
import duckdb
import time

from nba_api.stats.endpoints import playercareerstats

def get_players_in_game(game_id):
    time1 = time.perf_counter()
    con = duckdb.connect(database='../data/nba.sqlite', read_only=False)
    time2 = time.perf_counter()
    print(f'connected in {time2-time1}')
    game_df = con.query(f"select * from play_by_play where game_id = '{game_id}'").fetchdf()
    time1 = time.perf_counter()
    print(f'got play_by_play data in {time1-time2}')
    home_only = game_df.loc[(game_df['neutraldescription'].isna()) & (game_df['visitordescription'].isna())]
    away_only = game_df.loc[(game_df['neutraldescription'].isna()) & (game_df['homedescription'].isna())]
    home_id = home_only[(home_only['player1_team_id'].notna()) & (home_only['player2_team_id'].isna()) & (home_only['player3_team_id'].isna())].iloc[0]['player1_team_id']
    away_id = away_only[(away_only['player1_team_id'].notna()) & (away_only['player2_team_id'].isna()) & (away_only['player3_team_id'].isna())].iloc[0]['player1_team_id']

    home_player_ids = []
    home_player_ids.extend(game_df[game_df['player1_team_id'] == home_id]['player1_id'])
    home_player_ids.extend(game_df[game_df['player2_team_id'] == home_id]['player2_id'])
    home_player_ids.extend(game_df[game_df['player3_team_id'] == home_id]['player3_id'])
    home_player_ids = list(set(home_player_ids))
    if '0' in home_player_ids:
        home_player_ids.remove('0')

    away_player_ids = []
    away_player_ids.extend(game_df[game_df['player1_team_id'] == away_id]['player1_id'])
    away_player_ids.extend(game_df[game_df['player2_team_id'] == away_id]['player2_id'])
    away_player_ids.extend(game_df[game_df['player3_team_id'] == away_id]['player3_id'])
    away_player_ids = list(set(away_player_ids))
    if '0' in away_player_ids:
        away_player_ids.remove('0')

    return {
        'home_players': home_player_ids,
        'away_players': away_player_ids
    }

def get_aggregate_stats_for_players(player_ids, season):
    predictor_stats_attempts = ['FGA', 'FG3A', 'FTA', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    predictor_stats_pct = ['FGA', 'FGM', 'FG3A', 'FG3M', 'FTA', 'FTM', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
    player_att_rows = []
    player_pct_rows = []
    for player in player_ids:
        time1 = time.perf_counter()
        player_df = playercareerstats.PlayerCareerStats(player_id=player, per_mode36='PerGame').get_data_frames()[0]
        time2 = time.perf_counter()
        print(f'got {player} stats in {time2-time1}')
        player_df = player_df[player_df['TEAM_ID'].notna()]
        player_row = player_df[player_df['SEASON_ID'].str.startswith(season)]

        player_att_rows.append(player_row[predictor_stats_attempts])
        player_pct_rows.append(player_row[predictor_stats_pct])

    players_stats_att = pd.concat(player_att_rows)
    players_sums_att = players_stats_att.sum()

    players_stats_pct = pd.concat(player_pct_rows)
    players_sums_pct = players_stats_pct.sum()
    players_sums_pct['FG_PCT'] = players_sums_pct['FGM'] / players_sums_pct['FGA']
    players_sums_pct['FG3_PCT'] = players_sums_pct['FG3M'] / players_sums_pct['FG3A']
    players_sums_pct['FT_PCT'] = players_sums_pct['FTM'] / players_sums_pct['FTA']
    players_sums_pct = players_sums_pct[['FG_PCT', 'FG3_PCT', 'FT_PCT', 'OREB', 'DREB', 'AST', 'STL', 'BLK', 'TOV', 'PF']]

    return {
        'player_aggregate_attempts': players_sums_att,
        'player_aggregate_pct': players_sums_pct
    }

def get_aggregate_stats_for_game(game_id, season):
    time1 = time.perf_counter()
    players = get_players_in_game(game_id)
    time2 = time.perf_counter()
    print(f'got players in {time2-time1}')
    home_aggregate = get_aggregate_stats_for_players(players['home_players'], season)
    time1 = time.perf_counter()
    print(f'got home player aggregate in {time1-time2}')
    away_aggregate = get_aggregate_stats_for_players(players['away_players'], season)
    time2 = time.perf_counter()
    print(f'got away player aggregate in {time2-time1}')
    return {
        'home_aggregate': home_aggregate,
        'away_aggregate': away_aggregate
    }