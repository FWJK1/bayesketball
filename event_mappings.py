#!/usr/bin/env python3
"""
Event Mappings Script for NBA Database

This script prints out all the event types and action types found in the NBA database
in a readable format, along with their descriptions and statistics.
"""

import sqlite3
import pandas as pd
from collections import defaultdict


def get_event_type_mapping():
    """Get the mapping of event message types to descriptions."""
    return {
        1: "Made Shot",
        2: "Missed Shot",
        3: "Free Throw",
        4: "Rebound",
        5: "Turnover",
        6: "Foul",
        7: "Violation",
        8: "Substitution",
        9: "Timeout",
        10: "Jump Ball",
        11: "Ejection",
        12: "Start of Period",
        13: "End of Period",
        18: "Instant Replay",
        20: "Stoppage",
    }


def get_action_type_mapping():
    """Get the mapping of action types to descriptions."""
    return {
        # Made Shot actions
        1: "Jump Shot",
        2: "Layup Shot",
        3: "Dunk Shot",
        4: "Hook Shot",
        5: "Bank Shot",
        6: "Fadeaway Shot",
        7: "3-Point Jump Shot",
        8: "Running Jump Shot",
        9: "Driving Jump Shot",
        10: "Turnaround Jump Shot",
        11: "Step Back Jump Shot",
        12: "Pullup Jump Shot",
        13: "Floating Jump Shot",
        14: "Finger Roll Layup",
        15: "Driving Layup",
        16: "Reverse Layup",
        17: "Alley Oop Layup",
        18: "Putback Layup",
        19: "Driving Dunk",
        20: "Alley Oop Dunk",
        21: "Putback Dunk",
        22: "Reverse Dunk",
        23: "Hook Shot",
        24: "Bank Hook Shot",
        25: "Turnaround Hook Shot",
        26: "Fadeaway Hook Shot",
        27: "Tip Shot",
        28: "Cutting Layup",
        29: "Cutting Dunk",
        30: "Cutting Finger Roll",
        # Missed Shot actions (100+ series)
        101: "Jump Shot",
        102: "Layup Shot",
        103: "Dunk Shot",
        104: "Hook Shot",
        105: "Bank Shot",
        106: "Fadeaway Shot",
        107: "3-Point Jump Shot",
        108: "Running Jump Shot",
        109: "Driving Jump Shot",
        110: "Turnaround Jump Shot",
        111: "Step Back Jump Shot",
        112: "Pullup Jump Shot",
        113: "Floating Jump Shot",
        114: "Finger Roll Layup",
        115: "Driving Layup",
        116: "Reverse Layup",
        117: "Alley Oop Layup",
        118: "Putback Layup",
        119: "Driving Dunk",
        120: "Alley Oop Dunk",
        121: "Putback Dunk",
        122: "Reverse Dunk",
        123: "Hook Shot",
        124: "Bank Hook Shot",
        125: "Turnaround Hook Shot",
        126: "Fadeaway Hook Shot",
        127: "Tip Shot",
        128: "Cutting Layup",
        129: "Cutting Dunk",
        130: "Cutting Finger Roll",
        # Free Throw actions
        133: "Free Throw Made",
        134: "Free Throw Missed",
        # Rebound actions
        137: "Offensive Rebound",
        138: "Defensive Rebound",
        # Turnover actions
        141: "Steal",
        142: "Bad Pass",
        143: "Lost Ball",
        144: "Traveling",
        145: "3 Second Violation",
        146: "5 Second Violation",
        147: "8 Second Violation",
        148: "24 Second Violation",
        149: "Backcourt Violation",
        150: "Double Dribble",
        151: "Out of Bounds",
        152: "Offensive Goaltending",
        153: "Shot Clock Violation",
        154: "Palming",
        155: "Kicked Ball",
        156: "Lane Violation",
        157: "Jump Ball Violation",
        158: "Illegal Screen",
        159: "Illegal Assist",
        160: "Illegal Defense",
        161: "Illegal Offense",
        162: "Illegal Substitution",
        163: "Illegal Timeout",
        164: "Illegal Use of Hands",
        165: "Illegal Contact",
        166: "Excessive Timeout",
        167: "Delay of Game",
        168: "Technical Foul",
        169: "Flagrant Foul",
        170: "Unsportsmanlike Foul",
        171: "Disqualifying Foul",
        172: "Fighting",
        173: "Ejection",
        174: "Coach Technical",
        175: "Bench Technical",
        176: "Delay of Game Technical",
        177: "Excessive Timeout Technical",
        178: "Illegal Defense Technical",
        179: "Illegal Offense Technical",
        180: "Illegal Substitution Technical",
        181: "Illegal Timeout Technical",
        182: "Illegal Use of Hands Technical",
        183: "Illegal Contact Technical",
        184: "Excessive Timeout Technical",
        185: "Delay of Game Technical",
        186: "Technical Foul",
        187: "Flagrant Foul",
        188: "Unsportsmanlike Foul",
        189: "Disqualifying Foul",
        190: "Fighting",
        191: "Ejection",
        192: "Coach Technical",
        193: "Bench Technical",
        194: "Delay of Game Technical",
        195: "Excessive Timeout Technical",
        196: "Illegal Defense Technical",
        197: "Illegal Offense Technical",
        198: "Illegal Substitution Technical",
        199: "Illegal Timeout Technical",
        200: "Illegal Use of Hands Technical",
    }


def get_event_statistics(db_path="db/nba.sqlite"):
    """Get statistics about event types from the database."""
    conn = sqlite3.connect(db_path)

    # Get event type statistics
    event_type_query = """
    SELECT 
        eventmsgtype,
        COUNT(*) as count,
        COUNT(DISTINCT game_id) as games_with_event,
        COUNT(DISTINCT player1_name) as unique_players
    FROM play_by_play
    WHERE player1_name IS NOT NULL
    GROUP BY eventmsgtype
    ORDER BY count DESC
    """

    event_types_df = pd.read_sql(event_type_query, conn)

    # Get action type statistics
    action_type_query = """
    SELECT 
        eventmsgactiontype,
        COUNT(*) as count,
        COUNT(DISTINCT game_id) as games_with_action,
        COUNT(DISTINCT player1_name) as unique_players
    FROM play_by_play
    WHERE eventmsgactiontype IS NOT NULL AND eventmsgactiontype != 0
    GROUP BY eventmsgactiontype
    ORDER BY count DESC
    """

    action_types_df = pd.read_sql(action_type_query, conn)

    conn.close()

    return event_types_df, action_types_df


def print_event_mappings():
    """Print all event mappings in a readable format."""
    print("=" * 80)
    print("NBA DATABASE EVENT MAPPINGS")
    print("=" * 80)

    # Get mappings
    event_types = get_event_type_mapping()
    action_types = get_action_type_mapping()

    # Print event types
    print("\n📊 EVENT MESSAGE TYPES:")
    print("-" * 50)
    for event_id, description in sorted(event_types.items()):
        print(f"  {event_id:2d}: {description}")

    # Print action types
    print("\n🎯 ACTION TYPES:")
    print("-" * 50)

    # Group by category
    categories = {
        "Made Shots": [k for k in action_types.keys() if 1 <= k <= 30],
        "Missed Shots": [k for k in action_types.keys() if 101 <= k <= 130],
        "Free Throws": [k for k in action_types.keys() if 133 <= k <= 134],
        "Rebounds": [k for k in action_types.keys() if 137 <= k <= 138],
        "Turnovers": [k for k in action_types.keys() if 141 <= k <= 200],
    }

    for category, action_ids in categories.items():
        if action_ids:
            print(f"\n  {category}:")
            for action_id in sorted(action_ids):
                if action_id in action_types:
                    print(f"    {action_id:3d}: {action_types[action_id]}")


def print_database_statistics():
    """Print statistics from the actual database."""
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)

    try:
        event_types_df, action_types_df = get_event_statistics()

        print("\n📈 EVENT TYPE FREQUENCY:")
        print("-" * 50)
        event_mapping = get_event_type_mapping()

        for _, row in event_types_df.head(10).iterrows():
            event_id = row["eventmsgtype"]
            count = row["count"]
            games = row["games_with_event"]
            players = row["unique_players"]
            description = event_mapping.get(event_id, "Unknown")

            print(
                f"  {event_id:2d}: {description:<20} | Count: {count:>8,} | Games: {games:>5} | Players: {players:>4}"
            )

        print("\n🎯 TOP ACTION TYPES:")
        print("-" * 50)
        action_mapping = get_action_type_mapping()

        for _, row in action_types_df.head(15).iterrows():
            action_id = row["eventmsgactiontype"]
            count = row["count"]
            games = row["games_with_action"]
            players = row["unique_players"]
            description = action_mapping.get(action_id, "Unknown")

            print(
                f"  {action_id:3d}: {description:<25} | Count: {count:>8,} | Games: {games:>5} | Players: {players:>4}"
            )

    except Exception as e:
        print(f"Error accessing database: {e}")
        print("Make sure the database file exists at 'db/nba.sqlite'")


def print_sample_events():
    """Print sample events from the database."""
    print("\n" + "=" * 80)
    print("SAMPLE EVENTS FROM DATABASE")
    print("=" * 80)

    try:
        conn = sqlite3.connect("db/nba.sqlite")

        # Get sample events with descriptions
        sample_query = """
        SELECT 
            game_id,
            eventnum,
            eventmsgtype,
            eventmsgactiontype,
            period,
            pctimestring,
            homedescription,
            visitordescription,
            neutraldescription,
            player1_name,
            player1_team_abbreviation,
            player2_name,
            player2_team_abbreviation
        FROM play_by_play
        WHERE player1_name IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 10
        """

        sample_df = pd.read_sql(sample_query, conn)
        conn.close()

        event_mapping = get_event_type_mapping()
        action_mapping = get_action_type_mapping()

        print("\n🎮 SAMPLE EVENTS:")
        print("-" * 50)

        for _, row in sample_df.iterrows():
            event_type = event_mapping.get(row["eventmsgtype"], "Unknown")
            action_type = action_mapping.get(row["eventmsgactiontype"], "Unknown")

            description = (
                row["homedescription"]
                or row["visitordescription"]
                or row["neutraldescription"]
                or "No description"
            )

            print(
                f"\n  Game: {row['game_id']} | Event #{row['eventnum']} | Period {row['period']} | Time: {row['pctimestring']}"
            )
            print(f"  Type: {event_type} | Action: {action_type}")
            print(
                f"  Players: {row['player1_name']} ({row['player1_team_abbreviation']})"
            )
            if row["player2_name"]:
                print(
                    f"           {row['player2_name']} ({row['player2_team_abbreviation']})"
                )
            print(f"  Description: {description}")

    except Exception as e:
        print(f"Error accessing database: {e}")


if __name__ == "__main__":
    print_event_mappings()
    print_database_statistics()
    print_sample_events()

    print("\n" + "=" * 80)
    print("Event mappings script completed!")
    print("=" * 80)
