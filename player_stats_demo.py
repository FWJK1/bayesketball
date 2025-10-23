#!/usr/bin/env python3
"""
Example script demonstrating async player stats calculation with logging.

This script shows how to use the async methods with proper logging configuration
to monitor and debug the async operations.
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
    calculate_team_possession_metrics_async,
    get_multiple_player_summaries_async,
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


def get_players_for_game(conn: sqlite3.Connection, game_id: str) -> List[str]:
    """Get all player IDs for a specific game."""
    cursor = conn.execute(
        """
        SELECT DISTINCT player1_id FROM play_by_play 
        WHERE game_id = ? AND player1_id IS NOT NULL AND player1_id != ''
        UNION
        SELECT DISTINCT player2_id FROM play_by_play 
        WHERE game_id = ? AND player2_id IS NOT NULL AND player2_id != ''
        UNION
        SELECT DISTINCT player3_id FROM play_by_play 
        WHERE game_id = ? AND player3_id IS NOT NULL AND player3_id != ''
        ORDER BY player1_id
    """,
        (game_id, game_id, game_id),
    )
    return [row[0] for row in cursor.fetchall()]


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


async def calculate_all_player_stats(game_id: str = None):
    """Calculate player stats for a specific game or all games."""

    logger = setup_logging(logging.INFO)
    logger.info("Starting player stats calculation")

    conn = sqlite3.connect("db/nba.sqlite")

    try:
        all_results = {}

        if game_id:
            # Calculate stats for specific game
            logger.info(f"Calculating stats for game: {game_id}")
            player_stats = await calculate_player_stats_for_game(game_id, conn, logger)
            all_results[game_id] = player_stats
        else:
            # Calculate stats for all games
            logger.info("Calculating stats for all games")
            all_games = get_all_games(conn)
            logger.info(f"Found {len(all_games)} games to process")

            for i, current_game_id in enumerate(all_games, 1):
                logger.info(f"Processing game {i}/{len(all_games)}: {current_game_id}")
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
    return parser.parse_args()


async def main():
    """Main function to run the player stats calculation."""

    args = parse_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO

    print("NBA Player Stats Calculator")
    print("=" * 50)

    if args.game_id:
        print(f"Calculating stats for game: {args.game_id}")
    else:
        print("Calculating stats for all games")

    print("=" * 50)

    start_time = time.time()
    results = await calculate_all_player_stats(args.game_id)
    end_time = time.time()

    print("=" * 50)
    print(f"Calculation completed in {end_time - start_time:.2f} seconds")

    if results:
        total_games = len(results)
        total_players = sum(len(game_data) for game_data in results.values())
        print(
            f"Processed {total_games} games with {total_players} total player records"
        )
    else:
        print("No results generated")


if __name__ == "__main__":
    asyncio.run(main())
