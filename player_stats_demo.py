#!/usr/bin/env python3
"""
uv run player_stats_demo.py --game-id 0022300001
This is the script to calculate the player stats for all games in the database. Most of the heavy lifting is done in the db
"""

import argparse
import asyncio
import logging
import sqlite3
import time
from datetime import datetime
from typing import List

import pandas as pd

from nba_db.logger import get_simple_logger
from nba_db.player_stats import (
    PlayerStatsCalculator,
    set_log_level,
)


def setup_logging(level=logging.INFO):
    set_log_level(level)
    logger = get_simple_logger("async_demo", level)

    return logger


def get_all_games(conn: sqlite3.Connection) -> List[str]:
    """Get all game IDs from the database."""
    cursor = conn.execute("SELECT DISTINCT game_id FROM play_by_play ORDER BY game_id")
    return [row[0] for row in cursor.fetchall()]


def get_all_players(conn: sqlite3.Connection) -> List[str]:
    """Get all unique player IDs from the database regardless of team."""
    cursor = conn.execute(
        """
        SELECT id as player_id FROM players;
        """
    )
    return [row[0] for row in cursor.fetchall()]


def get_players_for_game(conn: sqlite3.Connection, game_id: str) -> List[str]:
    """Get all player IDs for a specific game regardless of team."""
    cursor = conn.execute(
        """
        SELECT DISTINCT player_id FROM (
            SELECT player1_id as player_id FROM play_by_play 
            WHERE game_id = ? AND player1_id IS NOT NULL AND player1_id != ''
            UNION
            SELECT player2_id as player_id FROM play_by_play 
            WHERE game_id = ? AND player2_id IS NOT NULL AND player2_id != ''
            UNION
            SELECT player3_id as player_id FROM play_by_play 
            WHERE game_id = ? AND player3_id IS NOT NULL AND player3_id != ''
        ) ORDER BY player_id
        """,
        (game_id, game_id, game_id),
    )
    return [row[0] for row in cursor.fetchall()]


def save_comprehensive_results_to_csv(
    results_df: pd.DataFrame, filename_prefix: str = "comprehensive_player_stats"
) -> str:
    """Save comprehensive results to a timestamped CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"

    results_df.to_csv(filename, index=False)
    return filename


def calculate_comprehensive_player_stats(logger) -> pd.DataFrame:
    """Calculate comprehensive stats for all players across all games using one SQL query."""
    logger.info("Starting comprehensive player stats calculation")

    # Initialize calculator with DuckDB
    calculator = PlayerStatsCalculator(db_path="db/nba.sqlite")

    # Execute the comprehensive query
    logger.info("Executing comprehensive SQL query for all players across all games...")
    start_time = time.time()

    results_df = calculator.calculate_all_players_all_games_stats()

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"Comprehensive query completed in {duration:.2f} seconds")
    logger.info(f"Found stats for {len(results_df)} players")

    # Close the calculator connection
    calculator.duckdb_conn.close()

    return results_df


def save_results_to_csv(results: dict, filename_prefix: str = "player_stats") -> str:
    """Save results to a timestamped CSV file."""
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


async def calculate_player_stats_for_game(
    game_id: str, conn: sqlite3.Connection, logger
) -> dict:
    """Calculate player stats for a specific game."""
    logger.info(f"Processing game {game_id}")

    player_ids = get_players_for_game(conn, game_id)
    logger.info(f"Found {len(player_ids)} players for game {game_id}")

    if not player_ids:
        logger.warning(f"No players found for game {game_id}")
        return {}

    # Calculate stats for all players
    calculator = PlayerStatsCalculator(conn, db_path="db/nba.sqlite")
    player_stats = await calculator.calculate_multiple_players_async(
        game_id, player_ids
    )

    logger.info(f"Calculated stats for {len(player_stats)} players in game {game_id}")
    return player_stats


async def calculate_all_player_stats(
    game_id: str = None, use_comprehensive: bool = True
):
    """Calculate player stats using comprehensive approach or game-by-game approach."""

    logger = setup_logging(logging.INFO)
    logger.info("Starting player stats calculation")

    if use_comprehensive:
        # Use the comprehensive approach - calculate all players across all games in one query
        logger.info(
            "Using comprehensive approach - calculating all players across all games"
        )

        results_df = calculate_comprehensive_player_stats(logger)

        logger.info("Saving comprehensive results to CSV")
        filename = save_comprehensive_results_to_csv(
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

        conn = sqlite3.connect("db/nba.sqlite")

        try:
            all_results = {}

            if game_id:
                # Calculate stats for specific game
                logger.info(f"Calculating stats for game: {game_id}")
                player_stats = await calculate_player_stats_for_game(
                    game_id, conn, logger
                )
                all_results[game_id] = player_stats
            else:
                # Calculate stats for all games
                logger.info("Calculating stats for all games")
                all_games = get_all_games(conn)
                logger.info(f"Found {len(all_games)} games to process")

                for i, current_game_id in enumerate(all_games, 1):
                    logger.info(
                        f"Processing game {i}/{len(all_games)}: {current_game_id}"
                    )
                    player_stats = await calculate_player_stats_for_game(
                        current_game_id, conn, logger
                    )
                    all_results[current_game_id] = player_stats

                    # Log progress every 10 games
                    if i % 10 == 0:
                        logger.info(f"Completed {i}/{len(all_games)} games")

            logger.info("Saving results to CSV")
            filename = save_results_to_csv(all_results, "player_stats")
            logger.info(f"Results saved to: {filename}")

            total_players = sum(len(game_data) for game_data in all_results.values())
            logger.info(
                f"Summary: Processed {len(all_results)} games, {total_players} total player records"
            )

            return all_results

        except Exception as e:
            logger.error(f"Error: {e}")
            return {}

        finally:
            conn.close()
            logger.info("Database connection closed")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate NBA player stats for specific games or all games"
    )
    parser.add_argument(
        "--game-id",
        type=str,
        help="Specific game ID to calculate stats for. If not provided, calculates stats for all games.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        default=True,
        help="Use comprehensive approach (default: True). Calculates all players across all games in one query.",
    )
    parser.add_argument(
        "--game-by-game",
        action="store_true",
        help="Use game-by-game approach instead of comprehensive approach.",
    )
    return parser.parse_args()


async def main():
    """Main function to run the player stats calculation."""

    args = parse_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO

    # Determine which approach to use
    use_comprehensive = (
        not args.game_by_game
    )  # Default to comprehensive unless --game-by-game is specified

    print("NBA Player Stats Calculator")
    print("=" * 50)

    if args.game_id:
        print(f"Calculating stats for game: {args.game_id}")
    else:
        print("Calculating stats for all games")

    if use_comprehensive:
        print(
            "Using comprehensive approach (all players across all games in one query)"
        )
    else:
        print("Using game-by-game approach")

    print("=" * 50)

    start_time = time.time()
    results = await calculate_all_player_stats(args.game_id, use_comprehensive)
    end_time = time.time()

    print("=" * 50)
    print(f"Calculation completed in {end_time - start_time:.2f} seconds")

    if results is not None:
        if use_comprehensive and hasattr(results, "__len__"):
            # Results is a DataFrame
            print(f"Processed {len(results)} players with comprehensive stats")
        elif isinstance(results, dict):
            # Results is a dictionary (game-by-game approach)
            total_games = len(results)
            total_players = sum(len(game_data) for game_data in results.values())
            print(
                f"Processed {total_games} games with {total_players} total player records"
            )
        else:
            print("Results generated successfully")
    else:
        print("No results generated")


if __name__ == "__main__":
    asyncio.run(main())
