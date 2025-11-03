import pandas as pd
pd.set_option('display.max_colwidth',250)
from event_mappings import EventType, ActionType

class Score_parser:
    def __init__(self, game_df):
        self.game_df = game_df
        self.game_id = game_df['game_id'][0]
        team_ids = game_df[game_df['player1_team_id'].notna()]['player1_team_id'].unique()
        cond = (self.game_df['visitordescription'] != None) & (self.game_df['homedescription'] == None) & (self.game_df['neutraldescription'] == None)
        self.away_id = self.game_df[cond].iloc[0]['player1_team_id']
        self.home_id = team_ids[0] if team_ids[1] == self.away_id else team_ids[1]

        self.is_home_offense = True
        self.active_home_players = []
        self.active_away_players = []
        self.possessions_df = pd.DataFrame(columns=['game_id', 'possession_id', 'offense_team_id', 'possession_end_event_type', 'possession_end_points', 'active_team0_ids', 'active_team1_ids'])
        self.period_possessions_df = pd.DataFrame(columns=['game_id', 'possession_id', 'offense_team_id', 'possession_end_event_type', 'possession_end_points', 'active_team0_ids', 'active_team1_ids'])

    def get_offense_id(self):
        return self.home_id if self.is_home_offense else self.away_id

    def get_defense_id(self):
        return self.away_id if self.is_home_offense else self.home_id

    def add_possession(self, possession_index ,end_event_type, end_points):
        cur_possession = {
            'game_id': [self.game_id],
            'possession_id': [possession_index],
            'offense_team_id': [self.get_offense_id()],
            'possession_end_event_type': [end_event_type],
            'possession_end_points': [end_points]}
        new_row_df = pd.DataFrame(cur_possession)
        self.period_possessions_df = pd.concat([self.period_possessions_df, new_row_df], ignore_index=True)

    def check_player(self, player_id, player_team_id):
        if player_id == None or player_id == '0' or player_team_id == None or player_team_id == '0':
            return

        if player_team_id == self.team0 and player_id not in self.active_team0_players:
            self.active_team0_players.append(player_id)
        elif player_team_id == self.team1 and player_id not in self.active_team1_players:
            self.active_team1_players.append(player_id)

    def update_players(self, row):
        self.check_player(row['player1_id'], row['player1_team_id'])
        self.check_player(row['player2_id'], row['player2_team_id'])
        self.check_player(row['player3_id'], row['player3_team_id'])
 
    def parse_game(self):
        possession_index = 0
        self.active_team0_players = []
        self.active_team1_players = []

        for index, row in self.game_df.iterrows():
            # check event players for new ids if need be
            if (len(self.active_team0_players) < 5 or len(self.active_team1_players) < 5) and row['eventmsgtype'] != EventType.SUBSTITUTION.value:
                self.update_players(row)
            
            match row['eventmsgtype']:
                case EventType.MADE_SHOT.value:
                    # if a player not on offense scored, we missed a change of possession somewhere earlier
                    # most likely culprits are fouls / free throws
                    if row['player1_team_id'] != self.get_offense_id():
                        print('player not on offense scored at row', index, ', handling it')
                        print(self.game_df.iloc[max(index-10,0) : index+1][['eventmsgtype', 'eventmsgactiontype', 'homedescription', 'neutraldescription', 'visitordescription']])
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense
                    # add the possession for the offensive team
                    # eventmsgactiontype can't be simply checked for ActionType.THREE_POINT_JUMP_SHOT, this needs fixing
                    points = 2 # 3 if (row['eventmsgactiontype'] == ActionType.THREE_POINT_JUMP_SHOT.value) else 2
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', points)
                    possession_index += 1
                    self.is_team1_offense = not self.is_team1_offense

                case EventType.FREE_THROW.value:
                    # if row['player1_team_id'] == self.get_offense_id():
                    #     print('team on offense scored a free throw, need to increment their last possession\'s points')
                    #     self.period_possessions_df.at[possession_index-1, 'points'] = self.period_possessions_df.at[possession_index-1, 'points'] + 1
                    # else:
                    #     print('defensive free throw, somebody musta fouled')
                    if self.game_df.iloc[index+1]['eventmsgtype'] == EventType.FREE_THROW.value:
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense

                    print('free throw') # action type doesn't seem to indicate if it went in so idk

                case EventType.REBOUND.value:
                    if row['player1_team_id'] == self.get_defense_id():
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense

                case EventType.TURNOVER.value:
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                    possession_index += 1
                    self.is_team1_offense = not self.is_team1_offense

                case EventType.FOUL.value:
                    if row['player1_team_id'] == self.get_offense_id():
                        print('offensive foul')
                        print(row[['homedescription', 'neutraldescription', 'visitordescription']])
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense

                case EventType.VIOLATION.value:
                    if row['player1_team_id'] == self.get_offense_id():
                        print('offensive violation')
                        print(row[['homedescription', 'neutraldescription', 'visitordescription']])
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense

                case EventType.JUMP_BALL.value:
                    self.is_team1_offense = True if self.team1 == row['player3_team_id'] else False

                case EventType.SUBSTITUTION.value:
                    if row['player1_id'] in self.active_team0_players:
                        self.active_team0_players.remove(row['player1_id'])
                        self.active_team0_players.append(row['player2_id'])
                        # print(f'subbing: {len(self.active_team0_players)} players on team0')
                    elif row['player1_id'] in self.active_team1_players:
                        self.active_team1_players.remove(row['player1_id'])
                        self.active_team1_players.append(row['player2_id'])
                        # print(f'subbing: {len(self.active_team1_players)} players on team1')
                    unset_players = self.period_possessions_df['active_team0_ids'].isna()
                    self.period_possessions_df.loc[unset_players, 'active_team0_ids'] = str(self.active_team0_players)
                    self.period_possessions_df.loc[unset_players, 'active_team1_ids'] = str(self.active_team1_players)

                case EventType.TIMEOUT.value:
                    print('timeout')

                case EventType.END_OF_PERIOD.value:
                    print('end of period')
                    # add final possession
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                    possession_index += 1

                    # fill in active players
                    unset_players = self.period_possessions_df['active_team0_ids'].isna()
                    self.period_possessions_df.loc[unset_players, 'active_team0_ids'] = str(self.active_team0_players)
                    self.period_possessions_df.loc[unset_players, 'active_team1_ids'] = str(self.active_team1_players)

                    # add period's possessions to game possessions
                    self.possessions_df = pd.concat([self.possessions_df, self.period_possessions_df], ignore_index=True)
                    self.active_team0_players = []
                    self.active_team1_players = []

        return self.possessions_df