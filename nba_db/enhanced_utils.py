"""Enhanced utilities for NBA database operations with event mapping support.

This module extends the existing utils.py with event mapping capabilities
to make play-by-play data more interpretable.
"""

import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional, Union

import pandas as pd  # type: ignore

from nba_db.event_mapping import (
    get_event_description,
    get_event_summary,
    get_event_type_description,
    get_simplified_action_description,
)

logger = logging.getLogger("nba_db_logger")


def get_db_conn_with_event_mapping(
    db_path: str = "basketball/basketball.sqlite",
) -> sqlite3.Connection:
    """Get database connection with event mapping functions registered.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        SQLite connection with event mapping functions registered
    """
    conn = sqlite3.connect(db_path)

    # Register event mapping functions as SQL functions
    conn.create_function("get_event_type_desc", 1, get_event_type_description)
    conn.create_function("get_action_type_desc", 1, get_simplified_action_description)
    conn.create_function("get_event_desc", 2, get_event_description)

    return conn


def get_play_by_play_with_descriptions(
    game_id: Optional[str] = None, conn: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """Get play-by-play data with human-readable event descriptions.

    Args:
        game_id: Specific game ID to filter by (optional)
        conn: Database connection (optional, will create if not provided)

    Returns:
        DataFrame with play-by-play data and event descriptions
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        # Base query
        base_query = """
        SELECT 
            game_id,
            eventnum,
            eventmsgtype,
            eventmsgactiontype,
            period,
            wctimestring,
            pctimestring,
            homedescription,
            neutraldescription,
            visitordescription,
            score,
            scoremargin,
            player1_name,
            player1_team_abbreviation,
            player2_name,
            player2_team_abbreviation,
            player3_name,
            player3_team_abbreviation,
            video_available_flag,
            -- Add event descriptions
            get_event_type_desc(eventmsgtype) as event_type_description,
            get_action_type_desc(eventmsgactiontype) as action_type_description,
            get_event_desc(eventmsgtype, eventmsgactiontype) as full_event_description
        FROM play_by_play
        """

        if game_id:
            query = base_query + " WHERE game_id = ?"
            df = pd.read_sql(query, conn, params=[game_id])
        else:
            df = pd.read_sql(base_query, conn)

        return df

    finally:
        if should_close:
            conn.close()


def get_event_summary_by_game(
    game_id: str, conn: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """Get a summary of all events in a game with descriptions.

    Args:
        game_id: The game ID to get events for
        conn: Database connection (optional, will create if not provided)

    Returns:
        DataFrame with event summaries
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        query = """
        SELECT 
            eventnum,
            period,
            pctimestring,
            get_event_desc(eventmsgtype, eventmsgactiontype) as event_description,
            COALESCE(homedescription, visitordescription, neutraldescription) as play_description,
            score,
            scoremargin,
            player1_name,
            player1_team_abbreviation,
            player2_name,
            player2_team_abbreviation
        FROM play_by_play
        WHERE game_id = ?
        ORDER BY eventnum
        """

        df = pd.read_sql(query, conn, params=[game_id])
        return df

    finally:
        if should_close:
            conn.close()


def get_player_events_summary(
    player_name: str,
    season: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> pd.DataFrame:
    """Get a summary of events involving a specific player.

    Args:
        player_name: Name of the player to get events for
        season: Season to filter by (optional)
        conn: Database connection (optional, will create if not provided)

    Returns:
        DataFrame with player events summary
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        # Base query for player events
        base_query = """
        SELECT 
            pbp.game_id,
            pbp.eventnum,
            pbp.period,
            pbp.pctimestring,
            pbp.get_event_desc(eventmsgtype, eventmsgactiontype) as event_description,
            COALESCE(pbp.homedescription, pbp.visitordescription, pbp.neutraldescription) as play_description,
            pbp.score,
            pbp.scoremargin,
            pbp.player1_name,
            pbp.player1_team_abbreviation,
            pbp.player2_name,
            pbp.player2_team_abbreviation,
            g.game_date,
            g.season_id
        FROM play_by_play pbp
        JOIN game g ON pbp.game_id = g.game_id
        WHERE (pbp.player1_name LIKE ? OR pbp.player2_name LIKE ? OR pbp.player3_name LIKE ?)
        """

        params = [f"%{player_name}%", f"%{player_name}%", f"%{player_name}%"]

        if season:
            base_query += " AND g.season_id = ?"
            params.append(season)

        base_query += " ORDER BY g.game_date DESC, pbp.eventnum"

        df = pd.read_sql(base_query, conn, params=params)
        return df

    finally:
        if should_close:
            conn.close()


def get_event_type_statistics(
    conn: Optional[sqlite3.Connection] = None,
) -> pd.DataFrame:
    """Get statistics about different event types in the database.

    Args:
        conn: Database connection (optional, will create if not provided)

    Returns:
        DataFrame with event type statistics
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        query = """
        SELECT 
            eventmsgtype,
            get_event_type_desc(eventmsgtype) as event_type_name,
            COUNT(*) as total_events,
            COUNT(DISTINCT game_id) as games_with_event,
            COUNT(DISTINCT player1_name) as unique_players_involved
        FROM play_by_play
        WHERE player1_name IS NOT NULL
        GROUP BY eventmsgtype, get_event_type_desc(eventmsgtype)
        ORDER BY total_events DESC
        """

        df = pd.read_sql(query, conn)
        return df

    finally:
        if should_close:
            conn.close()


def create_event_mapping_view(conn: Optional[sqlite3.Connection] = None) -> None:
    """Create a database view that includes event descriptions.

    Args:
        conn: Database connection (optional, will create if not provided)
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        # Create view with event descriptions
        view_query = """
        CREATE VIEW IF NOT EXISTS play_by_play_with_descriptions AS
        SELECT 
            game_id,
            eventnum,
            eventmsgtype,
            eventmsgactiontype,
            period,
            wctimestring,
            pctimestring,
            homedescription,
            neutraldescription,
            visitordescription,
            score,
            scoremargin,
            person1type,
            player1_id,
            player1_name,
            player1_team_id,
            player1_team_city,
            player1_team_nickname,
            player1_team_abbreviation,
            person2type,
            player2_id,
            player2_name,
            player2_team_id,
            player2_team_city,
            player2_team_nickname,
            player2_team_abbreviation,
            person3type,
            player3_id,
            player3_name,
            player3_team_id,
            player3_team_city,
            player3_team_nickname,
            player3_team_abbreviation,
            video_available_flag,
            -- Event descriptions
            get_event_type_desc(eventmsgtype) as event_type_description,
            get_action_type_desc(eventmsgactiontype) as action_type_description,
            get_event_desc(eventmsgtype, eventmsgactiontype) as full_event_description,
            COALESCE(homedescription, visitordescription, neutraldescription) as primary_description
        FROM play_by_play
        """

        conn.execute(view_query)
        conn.commit()

        logger.info("Created play_by_play_with_descriptions view")

    finally:
        if should_close:
            conn.close()


def export_play_by_play_with_descriptions(
    output_file: str = "play_by_play_with_descriptions.csv",
    game_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Export play-by-play data with descriptions to CSV.

    Args:
        output_file: Output CSV file path
        game_id: Specific game ID to export (optional)
        conn: Database connection (optional, will create if not provided)
    """
    df = get_play_by_play_with_descriptions(game_id=game_id, conn=conn)
    df.to_csv(output_file, index=False)
    logger.info(f"Exported play-by-play data with descriptions to {output_file}")


def get_team_event_summary(
    team_abbreviation: str,
    season: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> pd.DataFrame:
    """Get event summary for a specific team.

    Args:
        team_abbreviation: Team abbreviation (e.g., 'LAL', 'GSW')
        season: Season to filter by (optional)
        conn: Database connection (optional, will create if not provided)

    Returns:
        DataFrame with team event summary
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        base_query = """
        SELECT 
            pbp.game_id,
            pbp.eventnum,
            pbp.period,
            pbp.pctimestring,
            pbp.get_event_desc(eventmsgtype, eventmsgactiontype) as event_description,
            COALESCE(pbp.homedescription, pbp.visitordescription, pbp.neutraldescription) as play_description,
            pbp.score,
            pbp.scoremargin,
            pbp.player1_name,
            pbp.player1_team_abbreviation,
            pbp.player2_name,
            pbp.player2_team_abbreviation,
            g.game_date,
            g.season_id,
            CASE 
                WHEN pbp.player1_team_abbreviation = ? THEN 'Team Player'
                WHEN pbp.player2_team_abbreviation = ? THEN 'Team Player'
                ELSE 'Opponent'
            END as player_role
        FROM play_by_play pbp
        JOIN game g ON pbp.game_id = g.game_id
        WHERE (pbp.player1_team_abbreviation = ? OR pbp.player2_team_abbreviation = ?)
        """

        params = [
            team_abbreviation,
            team_abbreviation,
            team_abbreviation,
            team_abbreviation,
        ]

        if season:
            base_query += " AND g.season_id = ?"
            params.append(season)

        base_query += " ORDER BY g.game_date DESC, pbp.eventnum"

        df = pd.read_sql(base_query, conn, params=params)
        return df

    finally:
        if should_close:
            conn.close()


def analyze_event_patterns(
    game_id: str, conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Analyze event patterns for a specific game.

    Args:
        game_id: The game ID to analyze
        conn: Database connection (optional, will create if not provided)

    Returns:
        Dictionary with event pattern analysis
    """
    if conn is None:
        conn = get_db_conn_with_event_mapping()
        should_close = True
    else:
        should_close = False

    try:
        # Get basic game info
        game_info_query = """
        SELECT 
            g.game_date,
            g.season_id,
            ht.team_abbreviation as home_team,
            vt.team_abbreviation as visitor_team
        FROM game g
        JOIN team ht ON g.team_id_home = ht.team_id
        JOIN team vt ON g.team_id_away = vt.team_id
        WHERE g.game_id = ?
        """

        game_info = pd.read_sql(game_info_query, conn, params=[game_id]).iloc[0]

        # Get event statistics
        event_stats_query = """
        SELECT 
            eventmsgtype,
            get_event_type_desc(eventmsgtype) as event_type,
            COUNT(*) as count,
            COUNT(CASE WHEN player1_team_abbreviation = ? THEN 1 END) as home_team_events,
            COUNT(CASE WHEN player1_team_abbreviation = ? THEN 1 END) as visitor_team_events
        FROM play_by_play
        WHERE game_id = ?
        GROUP BY eventmsgtype, get_event_type_desc(eventmsgtype)
        ORDER BY count DESC
        """

        event_stats = pd.read_sql(
            event_stats_query,
            conn,
            params=[game_info["home_team"], game_info["visitor_team"], game_id],
        )

        # Get period-by-period breakdown
        period_stats_query = """
        SELECT 
            period,
            COUNT(*) as total_events,
            COUNT(CASE WHEN eventmsgtype IN (1, 2, 3) THEN 1 END) as scoring_events,
            COUNT(CASE WHEN eventmsgtype = 4 THEN 1 END) as rebounds,
            COUNT(CASE WHEN eventmsgtype = 5 THEN 1 END) as turnovers,
            COUNT(CASE WHEN eventmsgtype = 6 THEN 1 END) as fouls
        FROM play_by_play
        WHERE game_id = ?
        GROUP BY period
        ORDER BY period
        """

        period_stats = pd.read_sql(period_stats_query, conn, params=[game_id])

        return {
            "game_info": game_info.to_dict(),
            "event_statistics": event_stats.to_dict("records"),
            "period_breakdown": period_stats.to_dict("records"),
            "total_events": len(
                pd.read_sql(
                    "SELECT * FROM play_by_play WHERE game_id = ?",
                    conn,
                    params=[game_id],
                )
            ),
        }

    finally:
        if should_close:
            conn.close()
