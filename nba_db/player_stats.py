"""Player-level statistics calculator for NBA play-by-play data.

This module provides comprehensive offensive and defensive metrics
calculated from play-by-play events using DuckDB.
"""

import logging
from typing import Optional, List

import duckdb
import pandas as pd

from nba_db.logger import get_simple_logger
from event_mappings import EventType, ActionType

# Set up logger
logger = get_simple_logger("nba_db.player_stats", logging.INFO)


def set_log_level(level: int):
    """Set the log level for the logger."""
    global logger
    logger.setLevel(level)


class PlayerStatsCalculator:
    """Calculator for comprehensive player-level statistics from play-by-play data."""

    def __init__(self, conn=None, db_path: Optional[str] = None):
        """Initialize with database connection or path."""
        self.db_path = db_path

        # Initialize DuckDB connection
        self.duckdb_conn = duckdb.connect()

        # If we have a db_path, load the SQLite database into DuckDB
        if db_path:
            self._load_sqlite_to_duckdb(db_path)
        elif conn:
            # If we have a SQLite connection, try to get the path
            try:
                if hasattr(conn, "execute"):
                    db_path_from_conn = conn.execute("PRAGMA database_list").fetchone()[
                        2
                    ]
                    if db_path_from_conn and db_path_from_conn != ":memory:":
                        self._load_sqlite_to_duckdb(db_path_from_conn)
                    else:
                        logger.warning(
                            "In-memory SQLite database detected, cannot load into DuckDB"
                        )
            except Exception as e:
                logger.error(f"Failed to extract db_path from connection: {e}")

    def _load_sqlite_to_duckdb(self, sqlite_path: str):
        """Load SQLite database into DuckDB."""
        try:
            # Install and load SQLite extension
            self.duckdb_conn.execute("INSTALL sqlite")
            self.duckdb_conn.execute("LOAD sqlite")

            # Attach the SQLite database
            self.duckdb_conn.execute(f"ATTACH '{sqlite_path}' AS sqlite_db")
            logger.info(
                f"Successfully loaded SQLite database from {sqlite_path} into DuckDB"
            )
        except Exception as e:
            logger.error(f"Failed to load SQLite database into DuckDB: {e}")
            raise

    def __del__(self):
        """Clean up DuckDB connection."""
        if hasattr(self, "duckdb_conn"):
            self.duckdb_conn.close()

    def calculate_all_players_all_games_stats(self) -> pd.DataFrame:
        """Calculate comprehensive stats for all players across all games using cross join with active players only."""

        # Use cross join approach but only with active players to reduce memory usage
        comprehensive_query = f"""
        WITH all_players_and_games AS (
            SELECT 
                p.id as player_id,
                g.game_id,
                g.game_date
            FROM sqlite_db.player p
            CROSS JOIN sqlite_db.game g
            WHERE p.is_active = 1
        ),
        all_player_events AS (
            SELECT 
                game_id,
                player1_id as player_id,
                player1_team_abbreviation as team,
                eventmsgtype,
                eventmsgactiontype,
                player2_id,
                player2_team_abbreviation,
                player3_id,
                player3_team_abbreviation
            FROM sqlite_db.play_by_play
            WHERE player1_id IS NOT NULL AND player1_id != ''
            
            UNION ALL
            
            SELECT 
                game_id,
                player2_id as player_id,
                player2_team_abbreviation as team,
                eventmsgtype,
                eventmsgactiontype,
                player1_id,
                player1_team_abbreviation,
                player3_id,
                player3_team_abbreviation
            FROM sqlite_db.play_by_play
            WHERE player2_id IS NOT NULL AND player2_id != ''
            
            UNION ALL
            
            SELECT 
                game_id,
                player3_id as player_id,
                player3_team_abbreviation as team,
                eventmsgtype,
                eventmsgactiontype,
                player1_id,
                player1_team_abbreviation,
                player2_id,
                player2_team_abbreviation
            FROM sqlite_db.play_by_play
            WHERE player3_id IS NOT NULL AND player3_id != ''
        ),
        player_stats_per_game AS (
            SELECT 
                ape.player_id,
                ape.game_id,
                ape.team,
                -- Shooting stats
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.MADE_SHOT.value} THEN 1 END) as fg_made,  -- Made Shot
                COUNT(CASE WHEN ape.eventmsgtype IN ({EventType.MADE_SHOT.value}, {EventType.MISSED_SHOT.value}) THEN 1 END) as fg_attempted,  -- Made Shot + Missed Shot
                
                -- 3-point shooting (approximate)
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.MADE_SHOT.value}  -- Made Shot
                          AND ape.eventmsgactiontype IN ({ActionType.JUMP_SHOT.value}, {ActionType.THREE_POINT_JUMP_SHOT.value}, {ActionType.STEP_BACK_JUMP_SHOT.value}, {ActionType.PULLUP_JUMP_SHOT.value}) THEN 1 END) as fg3_made,  -- Jump Shot, 3-Point Jump Shot, Step Back Jump Shot, Pullup Jump Shot
                COUNT(CASE WHEN ape.eventmsgtype IN ({EventType.MADE_SHOT.value}, {EventType.MISSED_SHOT.value})  -- Made Shot + Missed Shot
                          AND ape.eventmsgactiontype IN ({ActionType.JUMP_SHOT.value}, {ActionType.THREE_POINT_JUMP_SHOT.value}, {ActionType.STEP_BACK_JUMP_SHOT.value}, {ActionType.PULLUP_JUMP_SHOT.value}, {ActionType.JUMP_SHOT_MISSED.value}, {ActionType.THREE_POINT_JUMP_SHOT_MISSED.value}, {ActionType.STEP_BACK_JUMP_SHOT_MISSED.value}, {ActionType.PULLUP_JUMP_SHOT_MISSED.value}) THEN 1 END) as fg3_attempted,  -- Jump Shot, 3-Point Jump Shot, Step Back Jump Shot, Pullup Jump Shot (made + missed)
                
                -- Free throws
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.FREE_THROW.value} AND ape.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value} THEN 1 END) as ft_made,  -- Free Throw + Free Throw Made
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.FREE_THROW.value} AND ape.eventmsgactiontype IN ({ActionType.FREE_THROW_MADE.value}, {ActionType.FREE_THROW_MISSED.value}) THEN 1 END) as ft_attempted,  -- Free Throw + Free Throw Made/Missed
                
                -- Assists (when player1 assists player2)
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.MADE_SHOT.value} AND ape.player2_id IS NOT NULL  -- Made Shot with assist
                          AND ape.team = ape.player2_team_abbreviation THEN 1 END) as assists,
                
                -- Turnovers
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.TURNOVER.value} THEN 1 END) as turnovers,  -- Turnover
                
                -- Offensive rebounds
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.REBOUND.value} AND ape.eventmsgactiontype = {ActionType.OFFENSIVE_REBOUND.value} THEN 1 END) as offensive_rebounds,  -- Rebound + Offensive Rebound
                
                -- Fouls drawn (when player1 fouls player2)
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.FOUL.value} AND ape.player2_id IS NOT NULL  -- Foul with opponent involved
                          AND ape.team != ape.player2_team_abbreviation THEN 1 END) as fouls_drawn,
                
                -- Steals (when player1 steals from player2)
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.TURNOVER.value} AND ape.eventmsgactiontype = {ActionType.STEAL.value}  -- Turnover + Steal
                          AND ape.player2_id IS NOT NULL AND ape.team != ape.player2_team_abbreviation THEN 1 END) as steals,
                
                -- Blocks (when player1 blocks player2)
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.MISSED_SHOT.value} AND ape.player2_id IS NOT NULL  -- Missed Shot with opponent involved
                          AND ape.team != ape.player2_team_abbreviation THEN 1 END) as blocks,
                
                -- Defensive rebounds
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.REBOUND.value} AND ape.eventmsgactiontype = {ActionType.DEFENSIVE_REBOUND.value} THEN 1 END) as defensive_rebounds,  -- Rebound + Defensive Rebound
                
                -- Personal fouls committed
                COUNT(CASE WHEN ape.eventmsgtype = {EventType.FOUL.value} THEN 1 END) as personal_fouls,  -- Foul
                
                -- Defensive events
                COUNT(CASE WHEN ape.player2_id IS NOT NULL AND ape.team != ape.player2_team_abbreviation THEN 1 END) as defensive_events,
                
                -- Total events
                COUNT(*) as total_events,
                
                -- Total possessions
                COUNT(*) as total_possessions,
                
                -- Offensive possessions (when player is on their team)
                COUNT(CASE WHEN ape.team IS NOT NULL THEN 1 END) as offensive_possessions,
                
                -- Defensive possessions (when player is against their team)
                COUNT(CASE WHEN ape.team IS NOT NULL AND ape.player2_id IS NOT NULL AND ape.team != ape.player2_team_abbreviation THEN 1 END) as defensive_possessions,
                
                -- Successful offensive possessions
                COUNT(CASE WHEN ape.team IS NOT NULL 
                          AND ((ape.eventmsgtype = {EventType.MADE_SHOT.value}) OR  -- Made Shot
                               (ape.eventmsgtype = {EventType.FREE_THROW.value} AND ape.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value})) THEN 1 END) as successful_offensive_possessions,  -- Free Throw + Free Throw Made
                
                -- Possession outcome points
                SUM(CASE WHEN ape.team IS NOT NULL 
                          AND ((ape.eventmsgtype = {EventType.MADE_SHOT.value}) OR  -- Made Shot
                               (ape.eventmsgtype = {EventType.FREE_THROW.value} AND ape.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value}))  -- Free Throw + Free Throw Made
                          THEN CASE 
                               WHEN ape.eventmsgtype = {EventType.MADE_SHOT.value} THEN 2  -- Made Shot (assuming 2 points)
                               WHEN ape.eventmsgtype = {EventType.FREE_THROW.value} AND ape.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value} THEN 1  -- Free Throw Made
                               ELSE 0 
                               END
                          ELSE 0 END) as possession_outcome_points
            FROM all_player_events ape
            GROUP BY ape.player_id, ape.game_id, ape.team
        ),
        player_team_mapping AS (
            SELECT 
                player_id,
                COALESCE(
                    MAX(CASE WHEN team IS NOT NULL THEN team END),
                    'UNK'
                ) as primary_team
            FROM all_player_events
            WHERE team IS NOT NULL
            GROUP BY player_id
        )
        SELECT 
            apg.player_id,
            apg.game_id,
            apg.game_date,
            COALESCE(ptm.primary_team, 'UNK') as team,
            COALESCE(pspg.total_events, 0) as total_events,
            COALESCE(pspg.fg_made, 0) as fg_made,
            COALESCE(pspg.fg_attempted, 0) as fg_attempted,
            COALESCE(pspg.fg3_made, 0) as fg3_made,
            COALESCE(pspg.fg3_attempted, 0) as fg3_attempted,
            COALESCE(pspg.ft_made, 0) as ft_made,
            COALESCE(pspg.ft_attempted, 0) as ft_attempted,
            COALESCE(pspg.assists, 0) as assists,
            COALESCE(pspg.turnovers, 0) as turnovers,
            COALESCE(pspg.offensive_rebounds, 0) as offensive_rebounds,
            COALESCE(pspg.fouls_drawn, 0) as fouls_drawn,
            COALESCE(pspg.steals, 0) as steals,
            COALESCE(pspg.blocks, 0) as blocks,
            COALESCE(pspg.defensive_rebounds, 0) as defensive_rebounds,
            COALESCE(pspg.personal_fouls, 0) as personal_fouls,
            COALESCE(pspg.defensive_events, 0) as defensive_events,
            COALESCE(pspg.total_possessions, 0) as total_possessions,
            COALESCE(pspg.offensive_possessions, 0) as offensive_possessions,
            COALESCE(pspg.defensive_possessions, 0) as defensive_possessions,
            COALESCE(pspg.successful_offensive_possessions, 0) as successful_offensive_possessions,
            COALESCE(pspg.possession_outcome_points, 0) as possession_outcome_points,
            
            -- Calculate percentages
            CASE WHEN COALESCE(pspg.fg_attempted, 0) > 0 THEN CAST(COALESCE(pspg.fg_made, 0) AS FLOAT) / COALESCE(pspg.fg_attempted, 0) ELSE 0 END as fg_percentage,
            CASE WHEN COALESCE(pspg.fg3_attempted, 0) > 0 THEN CAST(COALESCE(pspg.fg3_made, 0) AS FLOAT) / COALESCE(pspg.fg3_attempted, 0) ELSE 0 END as fg3_percentage,
            CASE WHEN COALESCE(pspg.ft_attempted, 0) > 0 THEN CAST(COALESCE(pspg.ft_made, 0) AS FLOAT) / COALESCE(pspg.ft_attempted, 0) ELSE 0 END as ft_percentage,
            CASE WHEN COALESCE(pspg.offensive_possessions, 0) > 0 THEN CAST(COALESCE(pspg.successful_offensive_possessions, 0) AS FLOAT) / COALESCE(pspg.offensive_possessions, 0) ELSE 0 END as offensive_possession_success_rate,
            
            -- Calculate points (approximate - assumes all FGs are 2-pointers)
            (COALESCE(pspg.fg_made, 0) * 2 + COALESCE(pspg.ft_made, 0)) as points,
            
            -- Calculate efficiency metrics
            CASE WHEN COALESCE(pspg.fg_attempted, 0) + (COALESCE(pspg.ft_attempted, 0) * 0.44) > 0 
                 THEN CAST(COALESCE(pspg.fg_made, 0) * 2 + COALESCE(pspg.ft_made, 0) AS FLOAT) / (2 * (COALESCE(pspg.fg_attempted, 0) + (COALESCE(pspg.ft_attempted, 0) * 0.44)))
                 ELSE 0 END as true_shooting_percentage,
            
            CASE WHEN (COALESCE(pspg.fg_attempted, 0) + COALESCE(pspg.ft_attempted, 0) + COALESCE(pspg.turnovers, 0)) > 0 
                 THEN CAST(COALESCE(pspg.fg_attempted, 0) + COALESCE(pspg.ft_attempted, 0) + COALESCE(pspg.turnovers, 0) AS FLOAT) / (COALESCE(pspg.fg_attempted, 0) + COALESCE(pspg.ft_attempted, 0) + COALESCE(pspg.turnovers, 0) + COALESCE(pspg.assists, 0))
                 ELSE 0 END as usage_rate,
            
            CASE WHEN COALESCE(pspg.turnovers, 0) > 0 THEN CAST(COALESCE(pspg.assists, 0) AS FLOAT) / COALESCE(pspg.turnovers, 0) ELSE 0 END as assist_to_turnover_ratio,
            
            (COALESCE(pspg.steals, 0) + COALESCE(pspg.blocks, 0) + COALESCE(pspg.defensive_rebounds, 0)) as defensive_rating,
            
            (COALESCE(pspg.fg_made, 0) * 2 + COALESCE(pspg.ft_made, 0) + COALESCE(pspg.assists, 0) + COALESCE(pspg.offensive_rebounds, 0) + 
             COALESCE(pspg.defensive_rebounds, 0) + COALESCE(pspg.steals, 0) + COALESCE(pspg.blocks, 0) - COALESCE(pspg.turnovers, 0) - COALESCE(pspg.personal_fouls, 0)) as efficiency_rating
        FROM all_players_and_games apg
        LEFT JOIN player_stats_per_game pspg ON apg.player_id = pspg.player_id AND apg.game_id = pspg.game_id
        LEFT JOIN player_team_mapping ptm ON apg.player_id = ptm.player_id
        ORDER BY apg.player_id, apg.game_date
        """

        # Execute the comprehensive query
        result = self.duckdb_conn.execute(comprehensive_query).fetchdf()

        return result

    def get_all_games(self) -> List[str]:
        """Get all game IDs from the database."""
        result = self.duckdb_conn.execute(
            "SELECT DISTINCT game_id FROM sqlite_db.play_by_play ORDER BY game_id"
        ).fetchall()
        return [row[0] for row in result]

    def get_all_players(self) -> List[str]:
        """Get all unique player IDs from the database regardless of team."""
        result = self.duckdb_conn.execute(
            "SELECT id as player_id FROM sqlite_db.player"
        ).fetchall()
        return [row[0] for row in result]

    def get_players_for_game(self, game_id: str) -> List[str]:
        """Get all player IDs for a specific game regardless of team."""
        result = self.duckdb_conn.execute(
            """
            SELECT DISTINCT player_id FROM (
                SELECT player1_id as player_id FROM sqlite_db.play_by_play 
                WHERE game_id = ? AND player1_id IS NOT NULL AND player1_id != ''
                UNION
                SELECT player2_id as player_id FROM sqlite_db.play_by_play 
                WHERE game_id = ? AND player2_id IS NOT NULL AND player2_id != ''
                UNION
                SELECT player3_id as player_id FROM sqlite_db.play_by_play 
                WHERE game_id = ? AND player3_id IS NOT NULL AND player3_id != ''
            ) ORDER BY player_id
            """,
            (game_id, game_id, game_id),
        ).fetchall()
        return [row[0] for row in result]

    def save_comprehensive_results_to_csv(
        self,
        results_df: pd.DataFrame,
        filename_prefix: str = "comprehensive_player_stats",
    ) -> str:
        """Save comprehensive results to a timestamped CSV file."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"

        results_df.to_csv(filename, index=False)
        return filename

    def save_results_to_csv(
        self, results: dict, filename_prefix: str = "player_stats"
    ) -> str:
        """Save results to a timestamped CSV file."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"

        rows = []
        for game_id, game_data in results.items():
            for player_id, stats in game_data.items():
                row = {"game_id": game_id, "player_id": player_id, **stats}
                rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)

        return filename

    def calculate_player_stats_for_game(self, game_id: str) -> dict:
        """Calculate player stats for a specific game using game-specific query."""
        logger.info(f"Processing game {game_id}")

        # Use a game-specific query instead of calculating all games
        game_specific_query = f"""
        WITH game_player_events AS (
            SELECT 
                game_id,
                player1_id as player_id,
                player1_team_abbreviation as team,
                eventmsgtype,
                eventmsgactiontype,
                player2_id,
                player2_team_abbreviation,
                player3_id,
                player3_team_abbreviation
            FROM sqlite_db.play_by_play
            WHERE game_id = '{game_id}' AND player1_id IS NOT NULL AND player1_id != ''
            
            UNION ALL
            
            SELECT 
                game_id,
                player2_id as player_id,
                player2_team_abbreviation as team,
                eventmsgtype,
                eventmsgactiontype,
                player1_id,
                player1_team_abbreviation,
                player3_id,
                player3_team_abbreviation
            FROM sqlite_db.play_by_play
            WHERE game_id = '{game_id}' AND player2_id IS NOT NULL AND player2_id != ''
            
            UNION ALL
            
            SELECT 
                game_id,
                player3_id as player_id,
                player3_team_abbreviation as team,
                eventmsgtype,
                eventmsgactiontype,
                player1_id,
                player1_team_abbreviation,
                player2_id,
                player2_team_abbreviation
            FROM sqlite_db.play_by_play
            WHERE game_id = '{game_id}' AND player3_id IS NOT NULL AND player3_id != ''
        ),
        player_stats_per_game AS (
            SELECT 
                gpe.player_id,
                gpe.game_id,
                gpe.team,
                -- Shooting stats
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.MADE_SHOT.value} THEN 1 END) as fg_made,  -- Made Shot
                COUNT(CASE WHEN gpe.eventmsgtype IN ({EventType.MADE_SHOT.value}, {EventType.MISSED_SHOT.value}) THEN 1 END) as fg_attempted,  -- Made Shot + Missed Shot
                
                -- 3-point shooting (approximate)
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.MADE_SHOT.value}  -- Made Shot
                          AND gpe.eventmsgactiontype IN ({ActionType.JUMP_SHOT.value}, {ActionType.THREE_POINT_JUMP_SHOT.value}, {ActionType.STEP_BACK_JUMP_SHOT.value}, {ActionType.PULLUP_JUMP_SHOT.value}) THEN 1 END) as fg3_made,  -- Jump Shot, 3-Point Jump Shot, Step Back Jump Shot, Pullup Jump Shot
                COUNT(CASE WHEN gpe.eventmsgtype IN ({EventType.MADE_SHOT.value}, {EventType.MISSED_SHOT.value})  -- Made Shot + Missed Shot
                          AND gpe.eventmsgactiontype IN ({ActionType.JUMP_SHOT.value}, {ActionType.THREE_POINT_JUMP_SHOT.value}, {ActionType.STEP_BACK_JUMP_SHOT.value}, {ActionType.PULLUP_JUMP_SHOT.value}, {ActionType.JUMP_SHOT_MISSED.value}, {ActionType.THREE_POINT_JUMP_SHOT_MISSED.value}, {ActionType.STEP_BACK_JUMP_SHOT_MISSED.value}, {ActionType.PULLUP_JUMP_SHOT_MISSED.value}) THEN 1 END) as fg3_attempted,  -- Jump Shot, 3-Point Jump Shot, Step Back Jump Shot, Pullup Jump Shot (made + missed)
                
                -- Free throws
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.FREE_THROW.value} AND gpe.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value} THEN 1 END) as ft_made,  -- Free Throw + Free Throw Made
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.FREE_THROW.value} AND gpe.eventmsgactiontype IN ({ActionType.FREE_THROW_MADE.value}, {ActionType.FREE_THROW_MISSED.value}) THEN 1 END) as ft_attempted,  -- Free Throw + Free Throw Made/Missed
                
                -- Assists (when player1 assists player2)
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.MADE_SHOT.value} AND gpe.player2_id IS NOT NULL  -- Made Shot with assist
                          AND gpe.team = gpe.player2_team_abbreviation THEN 1 END) as assists,
                
                -- Turnovers
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.TURNOVER.value} THEN 1 END) as turnovers,  -- Turnover
                
                -- Offensive rebounds
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.REBOUND.value} AND gpe.eventmsgactiontype = {ActionType.OFFENSIVE_REBOUND.value} THEN 1 END) as offensive_rebounds,  -- Rebound + Offensive Rebound
                
                -- Fouls drawn (when player1 fouls player2)
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.FOUL.value} AND gpe.player2_id IS NOT NULL  -- Foul with opponent involved
                          AND gpe.team != gpe.player2_team_abbreviation THEN 1 END) as fouls_drawn,
                
                -- Steals (when player1 steals from player2)
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.TURNOVER.value} AND gpe.eventmsgactiontype = {ActionType.STEAL.value}  -- Turnover + Steal
                          AND gpe.player2_id IS NOT NULL AND gpe.team != gpe.player2_team_abbreviation THEN 1 END) as steals,
                
                -- Blocks (when player1 blocks player2)
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.MISSED_SHOT.value} AND gpe.player2_id IS NOT NULL  -- Missed Shot with opponent involved
                          AND gpe.team != gpe.player2_team_abbreviation THEN 1 END) as blocks,
                
                -- Defensive rebounds
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.REBOUND.value} AND gpe.eventmsgactiontype = {ActionType.DEFENSIVE_REBOUND.value} THEN 1 END) as defensive_rebounds,  -- Rebound + Defensive Rebound
                
                -- Personal fouls committed
                COUNT(CASE WHEN gpe.eventmsgtype = {EventType.FOUL.value} THEN 1 END) as personal_fouls,  -- Foul
                
                -- Defensive events
                COUNT(CASE WHEN gpe.player2_id IS NOT NULL AND gpe.team != gpe.player2_team_abbreviation THEN 1 END) as defensive_events,
                
                -- Total events
                COUNT(*) as total_events,
                
                -- Total possessions
                COUNT(*) as total_possessions,
                
                -- Offensive possessions (when player is on their team)
                COUNT(CASE WHEN gpe.team IS NOT NULL THEN 1 END) as offensive_possessions,
                
                -- Defensive possessions (when player is against their team)
                COUNT(CASE WHEN gpe.team IS NOT NULL AND gpe.player2_id IS NOT NULL AND gpe.team != gpe.player2_team_abbreviation THEN 1 END) as defensive_possessions,
                
                -- Successful offensive possessions
                COUNT(CASE WHEN gpe.team IS NOT NULL 
                          AND ((gpe.eventmsgtype = {EventType.MADE_SHOT.value}) OR  -- Made Shot
                               (gpe.eventmsgtype = {EventType.FREE_THROW.value} AND gpe.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value})) THEN 1 END) as successful_offensive_possessions,  -- Free Throw + Free Throw Made
                
                -- Possession outcome points
                SUM(CASE WHEN gpe.team IS NOT NULL 
                          AND ((gpe.eventmsgtype = {EventType.MADE_SHOT.value}) OR  -- Made Shot
                               (gpe.eventmsgtype = {EventType.FREE_THROW.value} AND gpe.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value}))  -- Free Throw + Free Throw Made
                          THEN CASE 
                               WHEN gpe.eventmsgtype = {EventType.MADE_SHOT.value} THEN 2  -- Made Shot (assuming 2 points)
                               WHEN gpe.eventmsgtype = {EventType.FREE_THROW.value} AND gpe.eventmsgactiontype = {ActionType.FREE_THROW_MADE.value} THEN 1  -- Free Throw Made
                               ELSE 0 
                               END
                          ELSE 0 END) as possession_outcome_points
            FROM game_player_events gpe
            GROUP BY gpe.player_id, gpe.game_id, gpe.team
        ),
        player_team_mapping AS (
            SELECT 
                player_id,
                COALESCE(
                    MAX(CASE WHEN team IS NOT NULL THEN team END),
                    'UNK'
                ) as primary_team
            FROM game_player_events
            WHERE team IS NOT NULL
            GROUP BY player_id
        )
        SELECT 
            pspg.player_id,
            pspg.game_id,
            COALESCE(ptm.primary_team, 'UNK') as team,
            COALESCE(pspg.total_events, 0) as total_events,
            COALESCE(pspg.fg_made, 0) as fg_made,
            COALESCE(pspg.fg_attempted, 0) as fg_attempted,
            COALESCE(pspg.fg3_made, 0) as fg3_made,
            COALESCE(pspg.fg3_attempted, 0) as fg3_attempted,
            COALESCE(pspg.ft_made, 0) as ft_made,
            COALESCE(pspg.ft_attempted, 0) as ft_attempted,
            COALESCE(pspg.assists, 0) as assists,
            COALESCE(pspg.turnovers, 0) as turnovers,
            COALESCE(pspg.offensive_rebounds, 0) as offensive_rebounds,
            COALESCE(pspg.fouls_drawn, 0) as fouls_drawn,
            COALESCE(pspg.steals, 0) as steals,
            COALESCE(pspg.blocks, 0) as blocks,
            COALESCE(pspg.defensive_rebounds, 0) as defensive_rebounds,
            COALESCE(pspg.personal_fouls, 0) as personal_fouls,
            COALESCE(pspg.defensive_events, 0) as defensive_events,
            COALESCE(pspg.total_possessions, 0) as total_possessions,
            COALESCE(pspg.offensive_possessions, 0) as offensive_possessions,
            COALESCE(pspg.defensive_possessions, 0) as defensive_possessions,
            COALESCE(pspg.successful_offensive_possessions, 0) as successful_offensive_possessions,
            COALESCE(pspg.possession_outcome_points, 0) as possession_outcome_points,
            
            -- Calculate percentages
            CASE WHEN COALESCE(pspg.fg_attempted, 0) > 0 THEN CAST(COALESCE(pspg.fg_made, 0) AS FLOAT) / COALESCE(pspg.fg_attempted, 0) ELSE 0 END as fg_percentage,
            CASE WHEN COALESCE(pspg.fg3_attempted, 0) > 0 THEN CAST(COALESCE(pspg.fg3_made, 0) AS FLOAT) / COALESCE(pspg.fg3_attempted, 0) ELSE 0 END as fg3_percentage,
            CASE WHEN COALESCE(pspg.ft_attempted, 0) > 0 THEN CAST(COALESCE(pspg.ft_made, 0) AS FLOAT) / COALESCE(pspg.ft_attempted, 0) ELSE 0 END as ft_percentage,
            CASE WHEN COALESCE(pspg.offensive_possessions, 0) > 0 THEN CAST(COALESCE(pspg.successful_offensive_possessions, 0) AS FLOAT) / COALESCE(pspg.offensive_possessions, 0) ELSE 0 END as offensive_possession_success_rate,
            
            -- Calculate points (approximate - assumes all FGs are 2-pointers)
            (COALESCE(pspg.fg_made, 0) * 2 + COALESCE(pspg.ft_made, 0)) as points,
            
            -- Calculate efficiency metrics
            CASE WHEN COALESCE(pspg.fg_attempted, 0) + (COALESCE(pspg.ft_attempted, 0) * 0.44) > 0 
                 THEN CAST(COALESCE(pspg.fg_made, 0) * 2 + COALESCE(pspg.ft_made, 0) AS FLOAT) / (2 * (COALESCE(pspg.fg_attempted, 0) + (COALESCE(pspg.ft_attempted, 0) * 0.44)))
                 ELSE 0 END as true_shooting_percentage,
            
            CASE WHEN (COALESCE(pspg.fg_attempted, 0) + COALESCE(pspg.ft_attempted, 0) + COALESCE(pspg.turnovers, 0)) > 0 
                 THEN CAST(COALESCE(pspg.fg_attempted, 0) + COALESCE(pspg.ft_attempted, 0) + COALESCE(pspg.turnovers, 0) AS FLOAT) / (COALESCE(pspg.fg_attempted, 0) + COALESCE(pspg.ft_attempted, 0) + COALESCE(pspg.turnovers, 0) + COALESCE(pspg.assists, 0))
                 ELSE 0 END as usage_rate,
            
            CASE WHEN COALESCE(pspg.turnovers, 0) > 0 THEN CAST(COALESCE(pspg.assists, 0) AS FLOAT) / COALESCE(pspg.turnovers, 0) ELSE 0 END as assist_to_turnover_ratio,
            
            (COALESCE(pspg.steals, 0) + COALESCE(pspg.blocks, 0) + COALESCE(pspg.defensive_rebounds, 0)) as defensive_rating,
            
            (COALESCE(pspg.fg_made, 0) * 2 + COALESCE(pspg.ft_made, 0) + COALESCE(pspg.assists, 0) + COALESCE(pspg.offensive_rebounds, 0) + 
             COALESCE(pspg.defensive_rebounds, 0) + COALESCE(pspg.steals, 0) + COALESCE(pspg.blocks, 0) - COALESCE(pspg.turnovers, 0) - COALESCE(pspg.personal_fouls, 0)) as efficiency_rating
        FROM player_stats_per_game pspg
        LEFT JOIN player_team_mapping ptm ON pspg.player_id = ptm.player_id
        ORDER BY pspg.player_id
        """

        # Execute the game-specific query
        result_df = self.duckdb_conn.execute(game_specific_query).fetchdf()

        # Convert to the expected format
        player_stats = {}
        for _, row in result_df.iterrows():
            player_id = row["player_id"]
            stats = row.drop(["player_id", "game_id", "team"]).to_dict()
            player_stats[player_id] = stats

        logger.info(
            f"Calculated stats for {len(player_stats)} players in game {game_id}"
        )
        return player_stats

    def calculate_comprehensive_player_stats(self) -> pd.DataFrame:
        """Calculate comprehensive stats for all players across all games using one SQL query."""
        logger.info("Starting comprehensive player stats calculation")

        # Execute the comprehensive query
        logger.info(
            "Executing comprehensive SQL query for all players across all games..."
        )
        import time

        start_time = time.time()

        results_df = self.calculate_all_players_all_games_stats()

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"Comprehensive query completed in {duration:.2f} seconds")
        logger.info(f"Found stats for {len(results_df)} players")

        return results_df

    async def calculate_all_player_stats(
        self, game_id: str = None, use_comprehensive: bool = True
    ):
        """Calculate player stats using comprehensive approach or game-by-game approach."""
        logger.info("Starting player stats calculation")

        if use_comprehensive:
            # Use the comprehensive approach - calculate all players across all games in one query
            logger.info(
                "Using comprehensive approach - calculating all players across all games"
            )

            results_df = self.calculate_comprehensive_player_stats()

            logger.info("Saving comprehensive results to CSV")
            filename = self.save_comprehensive_results_to_csv(
                results_df, "comprehensive_player_stats"
            )
            logger.info(f"Results saved to: {filename}")

            logger.info(
                f"Summary: Processed {len(results_df)} players with comprehensive stats"
            )

            return results_df
        else:
            # Use the original game-by-game approach
            logger.info("Using game-by-game approach")

            try:
                all_results = {}

                if game_id:
                    # Calculate stats for specific game
                    logger.info(f"Calculating stats for game: {game_id}")
                    player_stats = self.calculate_player_stats_for_game(game_id)
                    all_results[game_id] = player_stats
                else:
                    # Calculate stats for all games
                    logger.info("Calculating stats for all games")
                    all_games = self.get_all_games()
                    logger.info(f"Found {len(all_games)} games to process")

                    for i, current_game_id in enumerate(all_games, 1):
                        logger.info(
                            f"Processing game {i}/{len(all_games)}: {current_game_id}"
                        )
                        player_stats = self.calculate_player_stats_for_game(
                            current_game_id
                        )
                        all_results[current_game_id] = player_stats

                        # Log progress every 10 games
                        if i % 10 == 0:
                            logger.info(f"Completed {i}/{len(all_games)} games")

                logger.info("Saving results to CSV")
                filename = self.save_results_to_csv(all_results, "player_stats")
                logger.info(f"Results saved to: {filename}")

                total_players = sum(
                    len(game_data) for game_data in all_results.values()
                )
                logger.info(
                    f"Summary: Processed {len(all_results)} games, {total_players} total player records"
                )

                return all_results

            except Exception as e:
                logger.error(f"Error: {e}")
                return {}
