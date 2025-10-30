import pandas as pd
pd.set_option('display.max_colwidth',250)
from event_mappings import EventType, ActionType

class Possession_parser:
    def __init__(self, game_df):
        self.game_df = game_df
        self.game_id = game_df['game_id'][0]
        # TODO: replace team0 and team1 with home and away (unclear how to programatically determine this)
        team_ids = game_df[game_df['player1_team_id'].notna()]['player1_team_id'].unique()
        self.team0 = team_ids[0]
        self.team1 = team_ids[1]
        self.is_team1_offense = True
        self.active_team0_players = []
        self.active_team1_players = []
        self.possessions_df = pd.DataFrame(columns=['game_id', 'possession_id', 'offense_team_id', 'possession_end_event_type', 'possession_end_points'])
        self.period_possessions_df = pd.DataFrame(columns=['game_id', 'possession_id', 'offense_team_id', 'possession_end_event_type', 'possession_end_points'])

    def get_offense_id(self):
        return self.team1 if self.is_team1_offense else self.team0

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
            # print(f'processing row {index}')
            if row['eventmsgtype'] != EventType.SUBSTITUTION.value:
                self.update_players(row)
                if len(self.active_team0_players) > 5:
                    print(f'too many players on team0 @ row {index}')
                if len(self.active_team1_players) > 5:
                    print(f'too many players on team1 @ row {index}')
            
            match row['eventmsgtype']:
                case EventType.MADE_SHOT.value:
                    points = 3 if (row['eventmsgactiontype'] == ActionType.THREE_POINT_JUMP_SHOT.value) else 2
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', points)
                    possession_index += 1
                    if row['player1_team_id'] != self.get_offense_id():
                        print('player not on offense scored at row', index)
                        # print(self.game_df.iloc[max(index-10,0) : index+1][['eventmsgtype', 'eventmsgactiontype', 'homedescription', 'neutraldescription', 'visitordescription']])
                    self.is_team1_offense = not self.is_team1_offense

                case EventType.REBOUND.value:
                    if row['player1_team_id'] != self.get_offense_id():
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense

                case EventType.TURNOVER.value:
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                    possession_index += 1
                    self.is_team1_offense = not self.is_team1_offense

                # case EventType.FOUL.value:
                #     print('foul')
                #     print(row['player1_team_id'] == self.get_offense_id())
                #     print(row[['homedescription', 'neutraldescription', 'visitordescription']])

                case EventType.JUMP_BALL.value:
                    self.is_team1_offense = True if self.team1 == row['player3_team_id'] else False
                
                case EventType.SUBSTITUTION.value:
                    if row['player1_id'] in self.active_team0_players:
                        self.active_team0_players.remove(row['player1_id'])
                        self.active_team0_players.append(row['player2_id'])
                        print(f'subbing: {len(self.active_team0_players)} players on team0')
                    elif row['player1_id'] in self.active_team1_players:
                        self.active_team1_players.remove(row['player1_id'])
                        self.active_team1_players.append(row['player2_id'])
                        print(f'subbing: {len(self.active_team1_players)} players on team1')

                case EventType.TIMEOUT.value:
                    print('timeout')

                case EventType.END_OF_PERIOD.value:
                    print('end of period')
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                    possession_index += 1
                    self.possessions_df = pd.concat([self.possessions_df, self.period_possessions_df], ignore_index=True)

        return self.possessions_df