"""Player-level statistics calculator for NBA play-by-play data.

This module provides comprehensive offensive and defensive metrics
calculated from play-by-play events for predicting possession outcomes.
"""

import asyncio
import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from nba_db.logger import get_simple_logger

# Set up logger for async operations using the existing logger system
logger = get_simple_logger("nba_db.player_stats", logging.INFO)


def set_log_level(level: int):
    """Set the log level for the async operations logger."""
    global logger
    logger.setLevel(level)


class PlayerStatsCalculator:
    """Calculator for player-level statistics from play-by-play data."""

    def __init__(self, conn, db_path: Optional[str] = None):
        """Initialize with database connection."""
        self.conn = conn
        self.db_path = db_path
        self.executor = ThreadPoolExecutor(max_workers=10)

    def calculate_player_game_stats(
        self, game_id: str, player_id: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive player stats for a specific game using SQL."""

        # First, get player's team and total events count
        team_query = """
        SELECT 
            COALESCE(
                MAX(CASE WHEN player1_id = ? THEN player1_team_abbreviation END),
                MAX(CASE WHEN player2_id = ? THEN player2_team_abbreviation END),
                MAX(CASE WHEN player3_id = ? THEN player3_team_abbreviation END)
            ) as team,
            COUNT(*) as total_events
        FROM play_by_play
        WHERE game_id = ? 
        AND (player1_id = ? OR player2_id = ? OR player3_id = ?)
        """

        team_result = pd.read_sql(
            team_query,
            self.conn,
            params=[
                player_id,
                player_id,
                player_id,
                game_id,
                player_id,
                player_id,
                player_id,
            ],
        )

        if team_result.empty or team_result.iloc[0]["total_events"] == 0:
            return self._empty_stats()

        player_team = team_result.iloc[0]["team"] or "UNK"
        total_events = team_result.iloc[0]["total_events"]

        # Calculate all stats in one comprehensive SQL query
        stats_query = """
        WITH player_events AS (
            SELECT *
            FROM play_by_play
            WHERE game_id = ? 
            AND (player1_id = ? OR player2_id = ? OR player3_id = ?)
        ),
        offensive_stats AS (
            SELECT 
                -- Shooting stats
                COUNT(CASE WHEN eventmsgtype = 1 AND player1_id = ? THEN 1 END) as fg_made,
                COUNT(CASE WHEN eventmsgtype IN (1, 2) AND player1_id = ? THEN 1 END) as fg_attempted,
                
                -- 3-point shooting (approximate)
                COUNT(CASE WHEN eventmsgtype = 1 AND player1_id = ? 
                          AND eventmsgactiontype IN (1, 7, 11, 12) THEN 1 END) as fg3_made,
                COUNT(CASE WHEN eventmsgtype IN (1, 2) AND player1_id = ? 
                          AND eventmsgactiontype IN (1, 7, 11, 12, 101, 107, 111, 112) THEN 1 END) as fg3_attempted,
                
                -- Free throws
                COUNT(CASE WHEN eventmsgtype = 3 AND eventmsgactiontype = 133 AND player1_id = ? THEN 1 END) as ft_made,
                COUNT(CASE WHEN eventmsgtype = 3 AND eventmsgactiontype IN (133, 134) AND player1_id = ? THEN 1 END) as ft_attempted,
                
                -- Assists (player1 assists player2)
                COUNT(CASE WHEN eventmsgtype = 1 AND player2_id = ? 
                          AND player1_team_abbreviation = ? THEN 1 END) as assists,
                
                -- Turnovers
                COUNT(CASE WHEN eventmsgtype = 5 AND player1_id = ? THEN 1 END) as turnovers,
                
                -- Offensive rebounds
                COUNT(CASE WHEN eventmsgtype = 4 AND eventmsgactiontype = 137 AND player1_id = ? THEN 1 END) as offensive_rebounds,
                
                -- Fouls drawn (player1 fouls player2)
                COUNT(CASE WHEN eventmsgtype = 6 AND player2_id = ? 
                          AND player1_team_abbreviation != ? THEN 1 END) as fouls_drawn
            FROM player_events
        ),
        defensive_stats AS (
            SELECT 
                -- Steals (player1 steals from player2)
                COUNT(CASE WHEN eventmsgtype = 5 AND eventmsgactiontype = 141 
                          AND player1_id = ? AND player2_team_abbreviation != ? THEN 1 END) as steals,
                
                -- Blocks (player1 blocks player2)
                COUNT(CASE WHEN eventmsgtype = 2 AND player1_id = ? 
                          AND player2_team_abbreviation != ? THEN 1 END) as blocks,
                
                -- Defensive rebounds
                COUNT(CASE WHEN eventmsgtype = 4 AND eventmsgactiontype = 138 AND player1_id = ? THEN 1 END) as defensive_rebounds,
                
                -- Personal fouls committed
                COUNT(CASE WHEN eventmsgtype = 6 AND player1_id = ? THEN 1 END) as personal_fouls,
                
                -- Defensive events
                COUNT(CASE WHEN player1_id = ? AND player2_team_abbreviation != ? THEN 1 END) as defensive_events
            FROM player_events
        ),
        possession_stats AS (
            SELECT 
                -- Total possessions
                COUNT(*) as total_possessions,
                
                -- Offensive possessions
                COUNT(CASE WHEN (player1_id = ? AND player1_team_abbreviation = ?) OR
                               (player2_id = ? AND player2_team_abbreviation = ?) OR
                               (player3_id = ? AND player3_team_abbreviation = ?) THEN 1 END) as offensive_possessions,
                
                -- Defensive possessions
                COUNT(CASE WHEN (player1_id = ? AND player1_team_abbreviation != ?) OR
                               (player2_id = ? AND player2_team_abbreviation != ?) OR
                               (player3_id = ? AND player3_team_abbreviation != ?) THEN 1 END) as defensive_possessions,
                
                -- Successful offensive possessions
                COUNT(CASE WHEN ((player1_id = ? AND player1_team_abbreviation = ?) OR
                                 (player2_id = ? AND player2_team_abbreviation = ?) OR
                                 (player3_id = ? AND player3_team_abbreviation = ?))
                          AND ((eventmsgtype = 1 AND player1_team_abbreviation = ?) OR
                               (eventmsgtype = 3 AND eventmsgactiontype = 133 AND player1_team_abbreviation = ?) OR
                               (eventmsgtype = 1 AND player2_team_abbreviation = ?)) THEN 1 END) as successful_offensive_possessions,
                
                -- Possession outcome points (points scored from successful possessions)
                SUM(CASE WHEN ((player1_id = ? AND player1_team_abbreviation = ?) OR
                               (player2_id = ? AND player2_team_abbreviation = ?) OR
                               (player3_id = ? AND player3_team_abbreviation = ?))
                          AND ((eventmsgtype = 1 AND player1_team_abbreviation = ?) OR
                               (eventmsgtype = 3 AND eventmsgactiontype = 133 AND player1_team_abbreviation = ?) OR
                               (eventmsgtype = 1 AND player2_team_abbreviation = ?)) 
                          THEN CASE 
                               WHEN eventmsgtype = 1 THEN 2  -- Made field goal (assuming 2 points)
                               WHEN eventmsgtype = 3 AND eventmsgactiontype = 133 THEN 1  -- Made free throw
                               ELSE 0 
                               END
                          ELSE 0 END) as possession_outcome_points
            FROM player_events
        )
        SELECT 
            o.*,
            d.*,
            p.*,
            -- Calculate percentages
            CASE WHEN o.fg_attempted > 0 THEN CAST(o.fg_made AS FLOAT) / o.fg_attempted ELSE 0 END as fg_percentage,
            CASE WHEN o.fg3_attempted > 0 THEN CAST(o.fg3_made AS FLOAT) / o.fg3_attempted ELSE 0 END as fg3_percentage,
            CASE WHEN o.ft_attempted > 0 THEN CAST(o.ft_made AS FLOAT) / o.ft_attempted ELSE 0 END as ft_percentage,
            CASE WHEN p.offensive_possessions > 0 THEN CAST(p.successful_offensive_possessions AS FLOAT) / p.offensive_possessions ELSE 0 END as offensive_possession_success_rate,
            
            -- Calculate points (approximate - assumes all FGs are 2-pointers)
            (o.fg_made * 2 + o.ft_made) as points,
            
            -- Calculate efficiency metrics
            CASE WHEN o.fg_attempted + (o.ft_attempted * 0.44) > 0 
                 THEN CAST(o.fg_made * 2 + o.ft_made AS FLOAT) / (2 * (o.fg_attempted + (o.ft_attempted * 0.44)))
                 ELSE 0 END as true_shooting_percentage,
            
            CASE WHEN (o.fg_attempted + o.ft_attempted + o.turnovers) > 0 
                 THEN CAST(o.fg_attempted + o.ft_attempted + o.turnovers AS FLOAT) / (o.fg_attempted + o.ft_attempted + o.turnovers + o.assists)
                 ELSE 0 END as usage_rate,
            
            CASE WHEN o.turnovers > 0 THEN CAST(o.assists AS FLOAT) / o.turnovers ELSE 0 END as assist_to_turnover_ratio,
            
            (d.steals + d.blocks + d.defensive_rebounds) as defensive_rating,
            
            (o.fg_made * 2 + o.ft_made + o.assists + o.offensive_rebounds + 
             d.defensive_rebounds + d.steals + d.blocks - o.turnovers - d.personal_fouls) as efficiency_rating
        FROM offensive_stats o
        CROSS JOIN defensive_stats d
        CROSS JOIN possession_stats p
        """

        # Execute the comprehensive query
        stats_result = pd.read_sql(
            stats_query,
            self.conn,
            params=[
                game_id,
                player_id,
                player_id,
                player_id,  # player_events CTE
                player_id,
                player_id,
                player_id,
                player_id,
                player_id,
                player_id,  # offensive_stats CTE
                player_id,
                player_team,
                player_id,
                player_id,
                player_id,
                player_id,
                player_id,
                player_team,  # offensive_stats CTE continued
                player_id,
                player_team,
                player_id,
                player_team,
                player_id,
                player_id,
                player_id,
                player_team,  # defensive_stats CTE
                player_id,
                player_id,
                player_team,
                player_id,
                player_team,
                player_id,
                player_team,  # possession_stats CTE
                player_id,
                player_team,
                player_id,
                player_team,
                player_id,
                player_team,  # possession_stats CTE continued
                player_id,
                player_team,
                player_id,
                player_team,
                player_id,
                player_team,  # successful possessions
                player_team,
                player_team,
                player_team,  # successful possessions continued
                player_id,
                player_team,
                player_id,
                player_team,
                player_id,
                player_team,  # possession outcome points
            ],
        )

        if stats_result.empty:
            return self._empty_stats()

        # Convert result to dictionary
        stats_dict = stats_result.iloc[0].to_dict()

        # Add metadata
        stats_dict.update(
            {
                "game_id": game_id,
                "player_id": player_id,
                "team": player_team,
                "total_events": total_events,
            }
        )

        return stats_dict

    async def calculate_player_game_stats_async(
        self, game_id: str, player_id: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive player stats for a specific game using async SQL."""

        logger.info(
            f"Starting async stats calculation for player {player_id} in game {game_id}"
        )
        start_time = asyncio.get_event_loop().time()

        # Create a new connection for this thread to avoid SQLite thread issues
        def _calculate_with_new_conn():
            thread_id = threading.current_thread().name
            logger.debug(
                f"Worker thread {thread_id}: Starting calculation for player {player_id}"
            )

            try:
                if self.db_path:
                    # Use the provided database path
                    logger.debug(
                        f"Worker thread {thread_id}: Using provided db_path: {self.db_path}"
                    )
                    new_conn = sqlite3.connect(self.db_path)
                elif hasattr(self.conn, "execute"):
                    # Try to get the database path from the existing connection
                    try:
                        db_path = self.conn.execute("PRAGMA database_list").fetchone()[
                            2
                        ]
                        if db_path and db_path != ":memory:":
                            logger.debug(
                                f"Worker thread {thread_id}: Using extracted db_path: {db_path}"
                            )
                            new_conn = sqlite3.connect(db_path)
                        else:
                            # For in-memory databases, we can't share across threads
                            logger.warning(
                                f"Worker thread {thread_id}: In-memory database detected, returning empty stats"
                            )
                            return self._empty_stats()
                    except Exception as e:
                        logger.error(
                            f"Worker thread {thread_id}: Failed to extract db_path: {e}"
                        )
                        return self._empty_stats()
                else:
                    # Fallback to using the same connection (may cause issues)
                    logger.warning(
                        f"Worker thread {thread_id}: Using fallback connection (may cause issues)"
                    )
                    new_conn = self.conn

                logger.debug(f"Worker thread {thread_id}: Creating calculator instance")
                calculator = PlayerStatsCalculator(new_conn, self.db_path)

                logger.debug(f"Worker thread {thread_id}: Executing stats calculation")
                result = calculator.calculate_player_game_stats(game_id, player_id)

                logger.debug(
                    f"Worker thread {thread_id}: Calculation completed successfully"
                )
                return result

            except Exception as e:
                logger.error(
                    f"Worker thread {thread_id}: Error calculating stats for player {player_id}: {e}"
                )
                return self._empty_stats()
            finally:
                if new_conn != self.conn:
                    logger.debug(
                        f"Worker thread {thread_id}: Closing database connection"
                    )
                    new_conn.close()

        # Run the calculation in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, _calculate_with_new_conn)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        logger.info(
            f"Completed async stats calculation for player {player_id} in {duration:.2f}s"
        )

        return result

    async def calculate_multiple_players_async(
        self, game_id: str, player_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate stats for multiple players concurrently."""

        logger.info(
            f"Starting concurrent stats calculation for {len(player_ids)} players in game {game_id}"
        )
        start_time = asyncio.get_event_loop().time()

        # Create tasks for all players
        tasks = [
            self.calculate_player_game_stats_async(game_id, player_id)
            for player_id in player_ids
        ]

        logger.debug(f"Created {len(tasks)} async tasks for players: {player_ids}")

        # Execute all tasks concurrently
        logger.debug("Executing all tasks concurrently...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"All tasks completed, processing {len(results)} results")

        # Process results and handle exceptions
        player_stats = {}
        successful_count = 0
        failed_count = 0

        for i, result in enumerate(results):
            player_id = player_ids[i]
            if isinstance(result, Exception):
                logger.error(f"Task failed for player {player_id}: {result}")
                player_stats[player_id] = self._empty_stats()
                failed_count += 1
            else:
                logger.debug(f"Task completed successfully for player {player_id}")
                player_stats[player_id] = result
                successful_count += 1

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        logger.info(
            f"Completed concurrent stats calculation: {successful_count} successful, {failed_count} failed, {duration:.2f}s total"
        )

        return player_stats

    def __del__(self):
        """Clean up thread pool executor."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure."""
        return {
            "game_id": "",
            "player_id": "",
            "team": "UNK",
            "total_events": 0,
            "fg_made": 0,
            "fg_attempted": 0,
            "fg_percentage": 0,
            "fg3_made": 0,
            "fg3_attempted": 0,
            "fg3_percentage": 0,
            "ft_made": 0,
            "ft_attempted": 0,
            "ft_percentage": 0,
            "assists": 0,
            "turnovers": 0,
            "offensive_rebounds": 0,
            "fouls_drawn": 0,
            "points": 0,
            "steals": 0,
            "blocks": 0,
            "defensive_rebounds": 0,
            "personal_fouls": 0,
            "defensive_events": 0,
            "total_possessions": 0,
            "offensive_possessions": 0,
            "defensive_possessions": 0,
            "successful_offensive_possessions": 0,
            "offensive_possession_success_rate": 0,
            "possession_outcome_points": 0,
            "true_shooting_percentage": 0,
            "usage_rate": 0,
            "assist_to_turnover_ratio": 0,
            "defensive_rating": 0,
            "efficiency_rating": 0,
        }


def calculate_team_possession_metrics(game_id: str, conn) -> Dict[str, Any]:
    """Calculate team-level possession metrics for a game using SQL."""

    # Get team abbreviations and calculate stats in one query
    query = """
    WITH team_stats AS (
        SELECT 
            player1_team_abbreviation as team,
            -- Successful possessions
            COUNT(CASE WHEN eventmsgtype = 1 THEN 1 END) as made_shots,
            COUNT(CASE WHEN eventmsgtype = 3 AND eventmsgactiontype = 133 THEN 1 END) as made_free_throws,
            -- Failed possessions
            COUNT(CASE WHEN eventmsgtype = 2 THEN 1 END) as missed_shots,
            COUNT(CASE WHEN eventmsgtype = 5 THEN 1 END) as turnovers,
            -- Possession outcome points
            SUM(CASE WHEN eventmsgtype = 1 THEN 2 
                     WHEN eventmsgtype = 3 AND eventmsgactiontype = 133 THEN 1 
                     ELSE 0 END) as possession_outcome_points
        FROM play_by_play
        WHERE game_id = ? AND player1_team_abbreviation IS NOT NULL
        GROUP BY player1_team_abbreviation
        HAVING COUNT(*) > 0
    ),
    team_calculations AS (
        SELECT 
            team,
            made_shots,
            missed_shots,
            made_free_throws,
            turnovers,
            possession_outcome_points,
            (made_shots + made_free_throws + missed_shots + turnovers) as total_possessions,
            (made_shots + made_free_throws) as successful_possessions,
            CASE WHEN (made_shots + made_free_throws + missed_shots + turnovers) > 0 
                 THEN CAST(made_shots + made_free_throws AS FLOAT) / (made_shots + made_free_throws + missed_shots + turnovers)
                 ELSE 0 END as possession_success_rate,
            CASE WHEN (made_shots + made_free_throws) > 0 
                 THEN CAST(possession_outcome_points AS FLOAT) / (made_shots + made_free_throws)
                 ELSE 0 END as possession_points_per_success,
            CASE WHEN (made_shots + made_free_throws + missed_shots + turnovers) > 0 
                 THEN CAST(possession_outcome_points AS FLOAT) / (made_shots + made_free_throws + missed_shots + turnovers)
                 ELSE 0 END as possession_points_per_attempt
        FROM team_stats
    )
    SELECT * FROM team_calculations
    ORDER BY team
    """

    results = pd.read_sql(query, conn, params=[game_id])

    if results.empty or len(results) < 2:
        return {}

    # Convert to dictionary format
    team1_row = results.iloc[0]
    team2_row = results.iloc[1]

    team1 = team1_row["team"]
    team2 = team2_row["team"]

    team1_stats = {
        "total_possessions": int(team1_row["total_possessions"]),
        "successful_possessions": int(team1_row["successful_possessions"]),
        "possession_success_rate": float(team1_row["possession_success_rate"]),
        "possession_outcome_points": int(team1_row["possession_outcome_points"]),
        "possession_points_per_success": float(
            team1_row["possession_points_per_success"]
        ),
        "possession_points_per_attempt": float(
            team1_row["possession_points_per_attempt"]
        ),
        "made_shots": int(team1_row["made_shots"]),
        "missed_shots": int(team1_row["missed_shots"]),
        "made_free_throws": int(team1_row["made_free_throws"]),
        "turnovers": int(team1_row["turnovers"]),
    }

    team2_stats = {
        "total_possessions": int(team2_row["total_possessions"]),
        "successful_possessions": int(team2_row["successful_possessions"]),
        "possession_success_rate": float(team2_row["possession_success_rate"]),
        "possession_outcome_points": int(team2_row["possession_outcome_points"]),
        "possession_points_per_success": float(
            team2_row["possession_points_per_success"]
        ),
        "possession_points_per_attempt": float(
            team2_row["possession_points_per_attempt"]
        ),
        "made_shots": int(team2_row["made_shots"]),
        "missed_shots": int(team2_row["missed_shots"]),
        "made_free_throws": int(team2_row["made_free_throws"]),
        "turnovers": int(team2_row["turnovers"]),
    }

    return {
        "game_id": game_id,
        "team1": team1,
        "team2": team2,
        f"{team1}_stats": team1_stats,
        f"{team2}_stats": team2_stats,
        "possession_differential": team1_stats["possession_success_rate"]
        - team2_stats["possession_success_rate"],
    }


# Advanced metrics for possession outcome prediction
def calculate_advanced_possession_metrics(
    player_stats: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate advanced metrics useful for possession outcome prediction."""

    return {
        # Offensive efficiency metrics
        "offensive_efficiency": player_stats["points"]
        / max(player_stats["offensive_possessions"], 1),
        "assist_rate": player_stats["assists"]
        / max(player_stats["offensive_possessions"], 1),
        "turnover_rate": player_stats["turnovers"]
        / max(player_stats["offensive_possessions"], 1),
        # Defensive impact metrics
        "defensive_efficiency": (
            player_stats["steals"]
            + player_stats["blocks"]
            + player_stats["defensive_rebounds"]
        )
        / max(player_stats["defensive_possessions"], 1),
        "steal_rate": player_stats["steals"]
        / max(player_stats["defensive_possessions"], 1),
        "block_rate": player_stats["blocks"]
        / max(player_stats["defensive_possessions"], 1),
        # Possession control metrics
        "possession_control": player_stats["offensive_possessions"]
        / max(player_stats["total_possessions"], 1),
        "possession_efficiency": player_stats["successful_offensive_possessions"]
        / max(player_stats["offensive_possessions"], 1),
        "possession_points_per_success": player_stats["possession_outcome_points"]
        / max(player_stats["successful_offensive_possessions"], 1),
        "possession_points_per_attempt": player_stats["possession_outcome_points"]
        / max(player_stats["offensive_possessions"], 1),
        # Momentum metrics
        "momentum_score": (
            player_stats["points"]
            + player_stats["assists"]
            + player_stats["offensive_rebounds"]
            + player_stats["steals"]
            + player_stats["blocks"]
            - player_stats["turnovers"]
            - player_stats["personal_fouls"]
        ),
        # Clutch metrics (would need time-based analysis)
        "clutch_factor": 0,  # Placeholder for time-based analysis
        # Pace metrics
        "pace_factor": player_stats["total_events"]
        / 48,  # Events per minute (assuming 48-minute game)
    }


def get_player_game_summary(game_id: str, player_id: str, conn) -> Dict[str, Any]:
    """Get comprehensive player game summary with all metrics."""

    calculator = PlayerStatsCalculator(conn)
    basic_stats = calculator.calculate_player_game_stats(game_id, player_id)
    advanced_stats = calculate_advanced_possession_metrics(basic_stats)

    return {**basic_stats, **advanced_stats}


# Async versions of standalone functions
async def calculate_team_possession_metrics_async(
    game_id: str, conn, db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate team-level possession metrics for a game using async SQL."""

    logger.info(
        f"Starting async team possession metrics calculation for game {game_id}"
    )
    start_time = asyncio.get_event_loop().time()

    def _calculate_with_new_conn():
        thread_id = threading.current_thread().name
        logger.debug(
            f"Team metrics worker thread {thread_id}: Starting calculation for game {game_id}"
        )

        try:
            if db_path:
                # Use the provided database path
                logger.debug(
                    f"Team metrics worker thread {thread_id}: Using provided db_path: {db_path}"
                )
                new_conn = sqlite3.connect(db_path)
            elif hasattr(conn, "execute"):
                # Try to get the database path from the existing connection
                try:
                    db_path_from_conn = conn.execute("PRAGMA database_list").fetchone()[
                        2
                    ]
                    if db_path_from_conn and db_path_from_conn != ":memory:":
                        logger.debug(
                            f"Team metrics worker thread {thread_id}: Using extracted db_path: {db_path_from_conn}"
                        )
                        new_conn = sqlite3.connect(db_path_from_conn)
                    else:
                        # For in-memory databases, we can't share across threads
                        logger.warning(
                            f"Team metrics worker thread {thread_id}: In-memory database detected, returning empty result"
                        )
                        return {}
                except Exception as e:
                    logger.error(
                        f"Team metrics worker thread {thread_id}: Failed to extract db_path: {e}"
                    )
                    return {}
            else:
                # Fallback to using the same connection
                logger.warning(
                    f"Team metrics worker thread {thread_id}: Using fallback connection"
                )
                new_conn = conn

            logger.debug(
                f"Team metrics worker thread {thread_id}: Executing team metrics calculation"
            )
            result = calculate_team_possession_metrics(game_id, new_conn)
            logger.debug(
                f"Team metrics worker thread {thread_id}: Calculation completed successfully"
            )
            return result

        except Exception as e:
            logger.error(
                f"Team metrics worker thread {thread_id}: Error calculating team metrics: {e}"
            )
            return {}
        finally:
            if new_conn != conn:
                logger.debug(
                    f"Team metrics worker thread {thread_id}: Closing database connection"
                )
                new_conn.close()

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, _calculate_with_new_conn)

    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    logger.info(
        f"Completed async team possession metrics calculation for game {game_id} in {duration:.2f}s"
    )

    return result


async def get_player_game_summary_async(
    game_id: str, player_id: str, conn, db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Get comprehensive player game summary with all metrics using async."""

    logger.info(
        f"Starting async player game summary calculation for player {player_id} in game {game_id}"
    )
    start_time = asyncio.get_event_loop().time()

    def _calculate_with_new_conn():
        thread_id = threading.current_thread().name
        logger.debug(
            f"Player summary worker thread {thread_id}: Starting calculation for player {player_id}"
        )

        try:
            if db_path:
                # Use the provided database path
                logger.debug(
                    f"Player summary worker thread {thread_id}: Using provided db_path: {db_path}"
                )
                new_conn = sqlite3.connect(db_path)
            elif hasattr(conn, "execute"):
                # Try to get the database path from the existing connection
                try:
                    db_path_from_conn = conn.execute("PRAGMA database_list").fetchone()[
                        2
                    ]
                    if db_path_from_conn and db_path_from_conn != ":memory:":
                        logger.debug(
                            f"Player summary worker thread {thread_id}: Using extracted db_path: {db_path_from_conn}"
                        )
                        new_conn = sqlite3.connect(db_path_from_conn)
                    else:
                        # For in-memory databases, we can't share across threads
                        logger.warning(
                            f"Player summary worker thread {thread_id}: In-memory database detected, returning empty result"
                        )
                        return {}
                except Exception as e:
                    logger.error(
                        f"Player summary worker thread {thread_id}: Failed to extract db_path: {e}"
                    )
                    return {}
            else:
                # Fallback to using the same connection
                logger.warning(
                    f"Player summary worker thread {thread_id}: Using fallback connection"
                )
                new_conn = conn

            logger.debug(
                f"Player summary worker thread {thread_id}: Creating calculator and calculating stats"
            )
            calculator = PlayerStatsCalculator(new_conn, db_path)
            basic_stats = calculator.calculate_player_game_stats(game_id, player_id)
            advanced_stats = calculate_advanced_possession_metrics(basic_stats)

            logger.debug(
                f"Player summary worker thread {thread_id}: Calculation completed successfully"
            )
            return {**basic_stats, **advanced_stats}

        except Exception as e:
            logger.error(
                f"Player summary worker thread {thread_id}: Error calculating player summary: {e}"
            )
            return {}
        finally:
            if new_conn != conn:
                logger.debug(
                    f"Player summary worker thread {thread_id}: Closing database connection"
                )
                new_conn.close()

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, _calculate_with_new_conn)

    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    logger.info(
        f"Completed async player game summary calculation for player {player_id} in {duration:.2f}s"
    )

    return result


async def get_multiple_player_summaries_async(
    game_id: str, player_ids: List[str], conn, db_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Get comprehensive summaries for multiple players concurrently."""

    logger.info(
        f"Starting async multiple player summaries calculation for {len(player_ids)} players in game {game_id}"
    )
    start_time = asyncio.get_event_loop().time()

    calculator = PlayerStatsCalculator(conn, db_path)

    # Calculate basic stats for all players concurrently
    logger.debug("Calculating basic stats for all players concurrently...")
    basic_stats_dict = await calculator.calculate_multiple_players_async(
        game_id, player_ids
    )

    # Calculate advanced stats for each player
    logger.debug("Calculating advanced stats for each player...")
    player_summaries = {}
    for player_id, basic_stats in basic_stats_dict.items():
        logger.debug(f"Calculating advanced stats for player {player_id}")
        advanced_stats = calculate_advanced_possession_metrics(basic_stats)
        player_summaries[player_id] = {**basic_stats, **advanced_stats}

    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    logger.info(
        f"Completed async multiple player summaries calculation for {len(player_summaries)} players in {duration:.2f}s"
    )

    return player_summaries


# Usage Examples:
"""
# Example 1: Calculate stats for multiple players concurrently
async def example_multiple_players():
    conn = sqlite3.connect("db/nba.sqlite")
    calculator = PlayerStatsCalculator(conn, db_path="db/nba.sqlite")
    
    game_id = "0022300001"
    player_ids = ["1629029", "201935", "203999"]
    
    # Calculate stats for all players concurrently
    player_stats = await calculator.calculate_multiple_players_async(game_id, player_ids)
    
    for player_id, stats in player_stats.items():
        print(f"Player {player_id}: {stats['points']} points, {stats['assists']} assists")
    
    conn.close()

# Example 2: Using standalone async functions
async def example_standalone_async():
    conn = sqlite3.connect("db/nba.sqlite")
    db_path = "db/nba.sqlite"
    
    game_id = "0022300001"
    player_ids = ["1629029", "201935", "203999"]
    
    # Get comprehensive summaries for all players
    summaries = await get_multiple_player_summaries_async(game_id, player_ids, conn, db_path)
    
    # Calculate team metrics concurrently
    team_metrics = await calculate_team_possession_metrics_async(game_id, conn, db_path)
    
    conn.close()
    return summaries, team_metrics

# Example 3: Running the async functions
# import asyncio
# summaries, team_metrics = asyncio.run(example_standalone_async())
"""
