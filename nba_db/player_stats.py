"""Player-level statistics calculator for NBA play-by-play data.

This module provides comprehensive offensive and defensive metrics
calculated from play-by-play events using DuckDB.
"""

import logging
from typing import Optional

import duckdb
import pandas as pd

from nba_db.logger import get_simple_logger

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
        comprehensive_query = """
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
                COUNT(CASE WHEN ape.eventmsgtype = 1 THEN 1 END) as fg_made,
                COUNT(CASE WHEN ape.eventmsgtype IN (1, 2) THEN 1 END) as fg_attempted,
                
                -- 3-point shooting (approximate)
                COUNT(CASE WHEN ape.eventmsgtype = 1 
                          AND ape.eventmsgactiontype IN (1, 7, 11, 12) THEN 1 END) as fg3_made,
                COUNT(CASE WHEN ape.eventmsgtype IN (1, 2) 
                          AND ape.eventmsgactiontype IN (1, 7, 11, 12, 101, 107, 111, 112) THEN 1 END) as fg3_attempted,
                
                -- Free throws
                COUNT(CASE WHEN ape.eventmsgtype = 3 AND ape.eventmsgactiontype = 133 THEN 1 END) as ft_made,
                COUNT(CASE WHEN ape.eventmsgtype = 3 AND ape.eventmsgactiontype IN (133, 134) THEN 1 END) as ft_attempted,
                
                -- Assists (when player1 assists player2)
                COUNT(CASE WHEN ape.eventmsgtype = 1 AND ape.player2_id IS NOT NULL 
                          AND ape.team = ape.player2_team_abbreviation THEN 1 END) as assists,
                
                -- Turnovers
                COUNT(CASE WHEN ape.eventmsgtype = 5 THEN 1 END) as turnovers,
                
                -- Offensive rebounds
                COUNT(CASE WHEN ape.eventmsgtype = 4 AND ape.eventmsgactiontype = 137 THEN 1 END) as offensive_rebounds,
                
                -- Fouls drawn (when player1 fouls player2)
                COUNT(CASE WHEN ape.eventmsgtype = 6 AND ape.player2_id IS NOT NULL 
                          AND ape.team != ape.player2_team_abbreviation THEN 1 END) as fouls_drawn,
                
                -- Steals (when player1 steals from player2)
                COUNT(CASE WHEN ape.eventmsgtype = 5 AND ape.eventmsgactiontype = 141 
                          AND ape.player2_id IS NOT NULL AND ape.team != ape.player2_team_abbreviation THEN 1 END) as steals,
                
                -- Blocks (when player1 blocks player2)
                COUNT(CASE WHEN ape.eventmsgtype = 2 AND ape.player2_id IS NOT NULL 
                          AND ape.team != ape.player2_team_abbreviation THEN 1 END) as blocks,
                
                -- Defensive rebounds
                COUNT(CASE WHEN ape.eventmsgtype = 4 AND ape.eventmsgactiontype = 138 THEN 1 END) as defensive_rebounds,
                
                -- Personal fouls committed
                COUNT(CASE WHEN ape.eventmsgtype = 6 THEN 1 END) as personal_fouls,
                
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
                          AND ((ape.eventmsgtype = 1) OR 
                               (ape.eventmsgtype = 3 AND ape.eventmsgactiontype = 133)) THEN 1 END) as successful_offensive_possessions,
                
                -- Possession outcome points
                SUM(CASE WHEN ape.team IS NOT NULL 
                          AND ((ape.eventmsgtype = 1) OR 
                               (ape.eventmsgtype = 3 AND ape.eventmsgactiontype = 133))
                          THEN CASE 
                               WHEN ape.eventmsgtype = 1 THEN 2  -- Made field goal (assuming 2 points)
                               WHEN ape.eventmsgtype = 3 AND ape.eventmsgactiontype = 133 THEN 1  -- Made free throw
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
