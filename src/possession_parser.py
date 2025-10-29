import pandas as pd
from event_mappings import EventType, ActionType

class Possession_parser:
    def __init__(self, game_df):
        self.game_df = game_df
        self.game_id = game_df['game_id'][0]
        team_ids = game_df['player1_id'].unique()
        self.team0 = team_ids[0]
        self.team1 = team_ids[1]
        self.is_team1_offense = True
        self.possessions_df = pd.DataFrame(columns=['game_id', 'possession_id', 'offense_team_id', 'possession_end_event_type', 'possession_end_points'])

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
        self.possessions_df = pd.concat([self.possessions_df, new_row_df], ignore_index=True)

    def parse_game(self):
        possession_index = 0
        # active_team0_players = []
        # active_team1_players = []

        for index, row in self.game_df.iterrows():
            match row['eventmsgtype']:
                case EventType.MADE_SHOT.value:
                    points = 3 if (row['eventmsgactiontype'] == ActionType.THREE_POINT_JUMP_SHOT.value) else 2
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', points)
                    possession_index += 1
                    if row['player1_team_id'] != self.get_offense_id():
                        print('player not on offense scored at row', index)
                    self.is_team1_offense = not self.is_team1_offense

                case EventType.REBOUND.value: # rebound
                    if row['player1_team_id'] != self.get_offense_id():
                        self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                        possession_index += 1
                        self.is_team1_offense = not self.is_team1_offense

                case EventType.TURNOVER.value: # turnover
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                    possession_index += 1
                    self.is_team1_offense = not self.is_team1_offense

                case EventType.JUMP_BALL.value: # jump ball
                    self.is_team1_offense = True if self.team1 == row['player3_team_id'] else False

                case EventType.END_OF_PERIOD.value: # end of period
                    self.add_possession(possession_index, f'{row['eventmsgtype']}.{row['eventmsgactiontype']}', 0)
                    possession_index += 1

        return self.possessions_df