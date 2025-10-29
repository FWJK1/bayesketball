#!/usr/bin/env python3
"""
Calculate player statistics for NBA games.

# Comprehensive approach (all players across all games)
uv run python main.py

# Game-specific approach (single game)
uv run python main.py --game-id 0022300001

"""

import argparse
import asyncio
import logging
import time

from nba_db.logger import get_simple_logger
from nba_db.player_stats import PlayerStatsCalculator, set_log_level


def setup_logging(level=logging.INFO):
    set_log_level(level)
    logger = get_simple_logger("async_demo", level)
    return logger


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
    parser.add_argument(
        "--agg-by-player",
        action="store_true",
        help="Calculate offensive and defensive stats aggregated by player ID.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


async def main():
    """Main function to run the player stats calculation."""
    args = parse_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO

    print("NBA Player Stats Calculator")
    print("=" * 50)

    print("=" * 50)

    # Setup logging
    logger = setup_logging(log_level)

    # Initialize calculator
    calculator = PlayerStatsCalculator(db_path="data/nba.sqlite")

    if args.agg_by_player:
        print("Calculating stats aggregated by player ID")
        results = calculator.calculate_player_stats_across_all_games()
        results.to_csv("player_stats_across_all_games.csv", index=False)
        return

    if args.game_id:
        print(f"Calculating stats for game: {args.game_id}")
        use_comprehensive = False  # Game-specific approach
    else:
        print("Calculating stats for all games")
        use_comprehensive = True  # Comprehensive approach

    start_time = time.time()

    try:
        # Calculate stats using the calculator methods
        results = await calculator.calculate_all_player_stats(
            args.game_id, use_comprehensive
        )

        end_time = time.time()
        duration = end_time - start_time

        print("=" * 50)
        print(f"Calculation completed in {duration:.2f} seconds")

        if results is not None:
            if use_comprehensive and hasattr(results, "__len__"):
                # Results is a DataFrame (comprehensive approach)
                print(f"Processed {len(results)} players with comprehensive stats")
            elif isinstance(results, dict):
                # Results is a dictionary (game-specific approach)
                total_games = len(results)
                total_players = sum(len(game_data) for game_data in results.values())
                print(
                    f"Processed {total_games} games with {total_players} total player records"
                )
            else:
                print("Results generated successfully")
        else:
            print("No results generated")

    except Exception as e:
        logger.error(f"Error during calculation: {e}")
        print(f"Error: {e}")
    finally:
        # Clean up
        calculator.duckdb_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
