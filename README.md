## Statistics Calculated

### Offensive Statistics

#### Shooting Statistics

-   **`fg_made`**: Field goals made
-   **`fg_attempted`**: Field goal attempts
-   **`fg_percentage`**: Field goal percentage (fg_made / fg_attempted)
-   **`fg3_made`**: 3-point field goals made
-   **`fg3_attempted`**: 3-point field goal attempts
-   **`fg3_percentage`**: 3-point field goal percentage
-   **`ft_made`**: Free throws made
-   **`ft_attempted`**: Free throw attempts
-   **`ft_percentage`**: Free throw percentage
-   **`points`**: Total points scored (approximate: fg_made × 2 + ft_made)

#### Offensive Playmaking

-   **`assists`**: Assists (passes that lead to made shots)
-   **`turnovers`**: Turnovers (lost possessions)
-   **`offensive_rebounds`**: Offensive rebounds (second chance opportunities)
-   **`fouls_drawn`**: Fouls drawn on opponents (creates free throw opportunities)

### Defensive Statistics

#### Defensive Actions

-   **`steals`**: Steals (taking the ball from opponents)
-   **`blocks`**: Blocks (preventing opponent shots)
-   **`defensive_rebounds`**: Defensive rebounds (ending opponent possessions)
-   **`personal_fouls`**: Personal fouls committed (defensive violations)

#### Defensive Impact

-   **`defensive_events`**: Events where player was defending
-   **`defensive_possessions`**: Defensive possessions involved in
-   **`defensive_rating`**: Defensive impact rating (Steals + Blocks + Defensive Rebounds)

### Advanced Statistics

#### Offensive Efficiency Metrics

-   **`true_shooting_percentage`**: True shooting percentage

    -   Formula: `Points / (2 × (FGA + 0.44 × FTA))`
    -   Accounts for 3-pointers and free throws
    -   More accurate than traditional FG%

-   **`assist_to_turnover_ratio`**: Assist-to-turnover ratio

    -   Formula: `Assists / Turnovers`
    -   Measures ball security and playmaking

-   **`offensive_possession_success_rate`**: Success rate on offensive possessions
-   **`possession_outcome_points`**: Points scored on possessions

#### Defensive Efficiency Metrics

-   **`defensive_rating`**: Defensive impact rating
    -   Formula: `Steals + Blocks + Defensive Rebounds`
    -   Simple defensive performance metric

#### Overall Performance Metrics

-   **`efficiency_rating`**: Overall efficiency rating

    -   Formula: `Points + Assists + Rebounds + Steals + Blocks - Turnovers - Fouls`
    -   Simple all-around performance metric

-   **`usage_rate`**: Usage rate (approximate)

    -   Formula: `(FGA + FTA + TO) / (FGA + FTA + TO + AST)`
    -   Measures how much a player is involved in team's possessions

#### Possession-Based Metrics

-   **`total_possessions`**: Total possessions involved in
-   **`offensive_possessions`**: Offensive possessions
-   **`defensive_possessions`**: Defensive possessions
-   **`successful_offensive_possessions`**: Successful offensive possessions

### Event-Based Statistics

#### Overall Event Tracking

-   **`total_events`**: Total number of events player was involved in

#### Defensive Event Tracking

-   **`defensive_events`**: Events where player was defending

## Data Sources

### Event Types (eventmsgtype)

-   **1**: Made Shot
-   **2**: Missed Shot
-   **3**: Free Throw
-   **4**: Rebound
-   **5**: Turnover
-   **6**: Foul
-   **8**: Substitution
-   **10**: Jump Ball
-   **12**: Start of Period
-   **13**: End of Period
-   **18**: Instant Replay
-   **20**: Stoppage

### Action Types (eventmsgactiontype)

The system tracks specific action types for more detailed analysis:

-   **1-30**: Made shot types (Jump Shot, Layup, Dunk, etc.)
-   **101-130**: Missed shot types (same as made shots + 100)
-   **133-134**: Free throw made/missed
-   **137-138**: Offensive/Defensive rebounds
-   **141+**: Various turnovers and violations

## Technical Implementation

### Database Architecture

-   **Primary Database**: SQLite for data storage
-   **Analytical Engine**: DuckDB for high-performance queries
-   **Data Loading**: Automatic SQLite to DuckDB conversion

### Query Structure

The comprehensive statistics query uses:

1. **Cross Join**: All active players × all games
2. **Event Aggregation**: Player events from play_by_play table
3. **Statistical Calculations**: Per-game, per-player metrics
4. **Team Mapping**: Player team assignments

### Performance Optimizations

-   **Active Players Only**: Filters to `is_active = 1` to reduce dataset size

## Usage

### Basic Usage

```bash
# Calculate comprehensive stats for all players
uv run python player_stats_demo.py --comprehensive

# Calculate stats for specific game
uv run python player_stats_demo.py --game-id 0022300001
```

### Event Mapping Reference

```bash
# View all event types and descriptions
uv run python event_mappings.py

# Quick reference for common events
uv run python event_reference.py
```

### Output Format

Results are saved as CSV files with columns:

-   `player_id`: Unique player identifier
-   `game_id`: Game identifier
-   `game_date`: Date of the game
-   `team`: Player's team abbreviation
-   All statistical metrics listed above

## File Structure

```
bayesketball/
├── nba_db/
│   ├── player_stats.py      # Main statistics calculator
│   ├── enhanced_utils.py    # Event mapping utilities
│   └── logger.py           # Logging configuration
├── player_stats_demo.py    # Demo script and CLI
├── event_mappings.py       # Comprehensive event mapping
├── event_reference.py      # Quick event reference
└── db/
    └── nba.sqlite         # NBA play-by-play database
```

## Methodology Notes

### Statistical Accuracy

-   **3-Point Identification**: Uses action types to approximate 3-point shots
-   **Point Calculation**: Assumes all field goals are 2-pointers (simplification)
-   **Possession Definition**: Based on player involvement in events
-   **Team Assignment**: Uses most frequent team association

### Limitations

-   **Point Values**: Does not distinguish between 2-point and 3-point field goals
-   **Action Type Mapping**: Some action types may not be perfectly mapped
-   **Possession Definition**: Simplified possession tracking
-   **Team Changes**: Does not account for mid-season team changes

### Data Quality

-   **Active Players**: Only includes players with `is_active = 1`
-   **Event Filtering**: Excludes events with missing player IDs
-   **Team Mapping**: Handles players with multiple team associations

## Bayesian Model Integration

### Creating Player Skill Vectors

Our comprehensive statistics can be used to create the offensive ($\alpha_{it}$) and defensive ($\delta_{jt}$) skill vectors for Bayesian modeling:

#### Offensive Skill Vector ($\alpha_{it}$)

The offensive skill vector combines normalized per-minute offensive statistics:

$$
\alpha_{it} = \begin{bmatrix}
\frac{\text{points}}{\text{minutes}} \\
\frac{\text{assists}}{\text{minutes}} \\
\frac{\text{offensive\_rebounds}}{\text{minutes}} \\
\frac{\text{fg\_made}}{\text{minutes}} \\
\frac{\text{ft\_made}}{\text{minutes}} \\
\frac{\text{turnovers}}{\text{minutes}}
\end{bmatrix}
$$

#### Defensive Skill Vector ($\delta_{jt}$)

The defensive skill vector combines normalized per-minute defensive statistics:

$$
\delta_{jt} = \begin{bmatrix}
\frac{\text{defensive\_rebounds}}{\text{minutes}} \\
\frac{\text{blocks}}{\text{minutes}} \\
\frac{\text{steals}}{\text{minutes}} \\
\frac{\text{personal\_fouls}}{\text{minutes}} \\
\frac{\text{defensive\_events}}{\text{minutes}}
\end{bmatrix}
$$

#### Code Implementation

```python
import pandas as pd
import numpy as np

def create_skill_vectors(player_stats_df, minutes_played_df):
    """
    Create offensive (alpha) and defensive (delta) skill vectors from player statistics.

    Parameters:
    - player_stats_df: DataFrame with our calculated player statistics
    - minutes_played_df: DataFrame with player minutes per game

    Returns:
    - alpha_vectors: Offensive skill vectors per player per game
    - delta_vectors: Defensive skill vectors per player per game
    """

    merged_df = player_stats_df.merge(
        minutes_played_df,
        on=['player_id', 'game_id'],
        how='left'
    )

    merged_df['minutes'] = merged_df['minutes'].fillna(0)
    merged_df['minutes'] = np.where(merged_df['minutes'] == 0, 1, merged_df['minutes'])

    # offensive skills (alpha)
    alpha_vectors = pd.DataFrame({
        'player_id': merged_df['player_id'],
        'game_id': merged_df['game_id'],
        'game_date': merged_df['game_date'],
        'team': merged_df['team'],
        'alpha_points_per_min': merged_df['points'] / merged_df['minutes'],
        'alpha_assists_per_min': merged_df['assists'] / merged_df['minutes'],
        'alpha_oreb_per_min': merged_df['offensive_rebounds'] / merged_df['minutes'],
        'alpha_fg_made_per_min': merged_df['fg_made'] / merged_df['minutes'],
        'alpha_ft_made_per_min': merged_df['ft_made'] / merged_df['minutes'],
        'alpha_turnovers_per_min': merged_df['turnovers'] / merged_df['minutes'],
        'alpha_fg_percentage': merged_df['fg_percentage'],
        'alpha_true_shooting': merged_df['true_shooting_percentage'],
        'alpha_assist_to_turnover': merged_df['assist_to_turnover_ratio']
    })

    # defensive skills (delta)
    delta_vectors = pd.DataFrame({
        'player_id': merged_df['player_id'],
        'game_id': merged_df['game_id'],
        'game_date': merged_df['game_date'],
        'team': merged_df['team'],
        'delta_dreb_per_min': merged_df['defensive_rebounds'] / merged_df['minutes'],
        'delta_blocks_per_min': merged_df['blocks'] / merged_df['minutes'],
        'delta_steals_per_min': merged_df['steals'] / merged_df['minutes'],
        'delta_fouls_per_min': merged_df['personal_fouls'] / merged_df['minutes'],
        'delta_defensive_events_per_min': merged_df['defensive_events'] / merged_df['minutes'],
        'delta_defensive_rating': merged_df['defensive_rating'],
        'delta_defensive_possessions': merged_df['defensive_possessions']
    })

    return alpha_vectors, delta_vectors

# Example usage:
# alpha_vectors, delta_vectors = create_skill_vectors(player_stats, minutes_data)
```

#### Bayesian Model Application

These vectors can be used in the Bayesian possession outcome model:

$$y_p \sim \text{Normal}\left(\sum_{i,k} \gamma_k \alpha_{i_p k, t_p} - \sum_{j,k} \lambda_k \delta_{j_p k, t_p} + \sum_{i,j} u_{i_p}^T v_{j_p}, \sigma^2\right)$$

Where:

-   $y_p$ is the possession outcome (points scored)
-   $\gamma_k$ are offensive skill weights
-   $\lambda_k$ are defensive skill weights
-   $u_{i_p}^T v_{j_p}$ represents player interaction effects
-   $\sigma^2$ is the observation variance

## Team-Level Aggregation

### Aggregating Player Stats to Team Level

Our comprehensive player statistics can be aggregated to create team-level metrics for analysis and prediction. Here's how to read the latest CSV file and create team-level aggregations:

```python
import pandas as pd
import glob
import os
import numpy as np

def read_latest_player_stats():
    """Read the latest comprehensive player stats CSV file."""
    csv_files = glob.glob("comprehensive_player_stats_*.csv")
    if not csv_files:
        raise FileNotFoundError("No comprehensive player stats CSV file found!")

    latest_csv = max(csv_files, key=os.path.getmtime)
    player_stats = pd.read_csv(latest_csv)
    player_stats["game_id"] = player_stats["game_id"].astype(str).str.zfill(10)

    return player_stats

def aggregate_to_team_level(player_stats_df):
    # Aggregate player stats to team level
    team_stats = (
        player_stats_df.groupby(["game_id", "team"])
        .agg({
            # Shooting statistics
            "fg_made": "sum",
            "fg_attempted": "sum",
            "fg3_made": "sum",
            "fg3_attempted": "sum",
            "ft_made": "sum",
            "ft_attempted": "sum",
            "points": "sum",

            # Playmaking and ball handling
            "assists": "sum",
            "turnovers": "sum",
            "offensive_rebounds": "sum",
            "defensive_rebounds": "sum",

            # Defensive actions
            "steals": "sum",
            "blocks": "sum",
            "personal_fouls": "sum",

            # Advanced metrics (averages)
            "fg_percentage": "mean",
            "fg3_percentage": "mean",
            "ft_percentage": "mean",
            "true_shooting_percentage": "mean",
            "assist_to_turnover_ratio": "mean",
            "usage_rate": "mean",

            # Possession metrics
            "offensive_possessions": "sum",
            "defensive_possessions": "sum",
            "successful_offensive_possessions": "sum",
            "possession_outcome_points": "sum",
            "offensive_possession_success_rate": "mean",

            # Efficiency metrics
            "efficiency_rating": "sum",
            "defensive_rating": "sum",

            # Event counts
            "total_events": "sum",
            "defensive_events": "sum"
        })
        .reset_index()
    )

    # Calculate team-level rates and percentages
    team_stats["team_fg_percentage"] = (
        team_stats["fg_made"] / team_stats["fg_attempted"]
    ).fillna(0)

    team_stats["team_fg3_percentage"] = (
        team_stats["fg3_made"] / team_stats["fg3_attempted"]
    ).fillna(0)

    team_stats["team_ft_percentage"] = (
        team_stats["ft_made"] / team_stats["ft_attempted"]
    ).fillna(0)

    team_stats["team_assist_rate"] = (
        team_stats["assists"] / team_stats["offensive_possessions"] * 100
    ).fillna(0)

    team_stats["team_turnover_rate"] = (
        team_stats["turnovers"] / team_stats["offensive_possessions"] * 100
    ).fillna(0)

    team_stats["team_offensive_rating"] = (
        team_stats["possession_outcome_points"] / team_stats["offensive_possessions"] * 100
    ).fillna(0)

    team_stats["team_defensive_rating"] = team_stats["defensive_rating"]

    # Calculate rebounding rates
    team_stats["team_offensive_rebound_rate"] = (
        team_stats["offensive_rebounds"] /
        (team_stats["fg_attempted"] - team_stats["fg_made"])
    ).fillna(0)

    team_stats["team_defensive_rebound_rate"] = (
        team_stats["defensive_rebounds"] /
        (team_stats["fg_attempted"] - team_stats["fg_made"])
    ).fillna(0)

    # Calculate steal and block rates
    team_stats["team_steal_rate"] = (
        team_stats["steals"] / team_stats["defensive_possessions"] * 100
    ).fillna(0)

    team_stats["team_block_rate"] = (
        team_stats["blocks"] / team_stats["defensive_possessions"] * 100
    ).fillna(0)

    return team_stats

```

## Future Enhancements

-   **Full player list**: Currently we are only calculating player stats for active players, which still creates 35 million rows (#active players x #games). If we have time we can compute stats for all players, but that would mean we'd have to generate ~144 million rows.

## Credits

Written by

-   Prithaj Nath
-   Nate Borland
-   Fitz Koch
    fw.j.keenan.koch@gmail.com
    fkeenank@uvm.edu
