# [Kaggle NBA dataset](https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats)

```markdown
# Comprehensive NBA/ABA/BAA Statistics Dataset Guide

This document provides a detailed description of each file and its columns within the NBA/ABA/BAA statistics dataset.

---

### `Team Summaries.csv`

This file contains team-level advanced statistics and summary information for a single season. It's one of the most valuable files for high-level team analysis.

| Column Name        | Description                                                                                                       | Example                 |
| :----------------- | :---------------------------------------------------------------------------------------------------------------- | :---------------------- |
| `season`           | The year the season ended.                                                                                        | `2017`                  |
| `lg`               | The league (e.g., NBA, ABA).                                                                                      | `NBA`                   |
| `team`             | The full name of the team.                                                                                        | `Golden State Warriors` |
| `abbreviation`     | The team's three-letter abbreviation.                                                                             | `GSW`                   |
| `playoffs`         | A text description of the team's playoff performance.                                                             | `Won Finals`            |
| `age`              | The average age of the players on the team, weighted by minutes played.                                           | `27.5`                  |
| `w`                | The number of wins in the regular season.                                                                         | `67`                    |
| `l`                | The number of losses in the regular season.                                                                       | `15`                    |
| `pw`               | Pythagorean Wins: an estimate of wins based on points scored and allowed.                                         | `68`                    |
| `pl`               | Pythagorean Losses: an estimate of losses.                                                                        | `14`                    |
| `mov`              | Margin of Victory: the average point differential per game.                                                       | `11.63`                 |
| `sos`              | Strength of Schedule: a rating of how difficult the team's schedule was.                                          | `-0.27`                 |
| `srs`              | Simple Rating System: a rating that combines MOV and SOS.                                                         | `11.35`                 |
| `o_rtg`            | **Offensive Rating**: points scored per 100 possessions. 🏀                                                       | `115.6`                 |
| `d_rtg`            | **Defensive Rating**: points allowed per 100 possessions.                                                         | `104.0`                 |
| `n_rtg`            | **Net Rating**: the point differential per 100 possessions (`o_rtg` - `d_rtg`).                                   | `11.6`                  |
| `pace`             | The average number of possessions the team has per 48 minutes.                                                    | `99.8`                  |
| `f_tr`             | Free Throw Rate: the number of free throw attempts per field goal attempt.                                        | `0.264`                 |
| `x3p_ar`           | 3-Point Attempt Rate: the percentage of field goal attempts that were 3-pointers.                                 | `0.364`                 |
| `ts_percent`       | True Shooting Percentage: a measure of shooting efficiency that includes 2-pointers, 3-pointers, and free throws. | `0.597`                 |
| `e_fg_percent`     | Effective Field Goal Percentage: adjusts for the fact that a 3-pointer is worth more than a 2-pointer.            | `0.563`                 |
| `tov_percent`      | Turnover Percentage: an estimate of turnovers per 100 plays.                                                      | `14.2`                  |
| `orb_percent`      | Offensive Rebound Percentage: percentage of available offensive rebounds a team grabbed.                          | `22.5`                  |
| `ft_fga`           | Free throws made per field goal attempt.                                                                          | `0.207`                 |
| `opp_e_fg_percent` | The opponent's Effective Field Goal Percentage.                                                                   | `0.495`                 |
| `opp_tov_percent`  | The opponent's Turnover Percentage.                                                                               | `14.3`                  |
| `drb_percent`      | Defensive Rebound Percentage: percentage of available defensive rebounds a team grabbed.                          | `78.2`                  |
| `opp_ft_fga`       | The opponent's free throws made per field goal attempt.                                                           | `0.183`                 |
| `arena`            | The name of the team's home arena.                                                                                | `Oracle Arena`          |
| `attend`           | Total home game attendance for the season.                                                                        | `801930`                |
| `attend_g`         | Average home game attendance.                                                                                     | `19559`                 |

---

### `Team Stats Per 100 Poss.csv`

This file normalizes basic team stats to a per-100-possession basis, which helps compare teams that play at different paces.

| Column Name        | Description                                                                 | Example                      |
| :----------------- | :-------------------------------------------------------------------------- | :--------------------------- |
| `season`           | The year the season ended.                                                  | `2018`                       |
| `lg`               | The league.                                                                 | `NBA`                        |
| `team`             | The full name of the team.                                                  | `Houston Rockets`            |
| `abbreviation`     | The team's three-letter abbreviation.                                       | `HOU`                        |
| `playoffs`         | A text description of the team's playoff performance.                       | `Lost W. Conf. Finals`       |
| `g`                | The number of games played.                                                 | `82`                         |
| `mp`               | The total minutes played by the team over the season.                       | `19805`                      |
| `..._per_100_poss` | Various stats (FG, FGA, 3P, AST, etc.) calculated per 100 team possessions. | `114.7` (`pts_per_100_poss`) |
| `..._percent`      | Various shooting percentages (FG%, 3P%, FT%).                               | `0.362` (`x3p_percent`)      |

---

### `Team Stats Per Game.csv`

This file contains traditional team stats, averaged on a per-game basis.

| Column Name    | Description                                                 | Example                  |
| :------------- | :---------------------------------------------------------- | :----------------------- |
| `season`       | The year the season ended.                                  | `1996`                   |
| `lg`           | The league.                                                 | `NBA`                    |
| `team`         | The full name of the team.                                  | `Chicago Bulls`          |
| `..._per_game` | Various stats (FG, FGA, 3P, AST, etc.) calculated per game. | `105.2` (`pts_per_game`) |
| `..._percent`  | Various shooting percentages (FG%, 3P%, FT%).               | `0.478` (`fg_percent`)   |

---

### `Advanced.csv`

This file contains **player-level** advanced stats for a single season.

| Column Name   | Description                                                                                                                                                       | Example                |
| :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------- |
| `season`      | The year the season ended.                                                                                                                                        | `2016`                 |
| `player`      | The player's name.                                                                                                                                                | `Stephen Curry`        |
| `player_id`   | A unique ID for the player.                                                                                                                                       | `curryst01`            |
| `age`         | The player's age on February 1 of that season.                                                                                                                    | `27`                   |
| `team`        | The team the player played for.                                                                                                                                   | `GSW`                  |
| `per`         | **Player Efficiency Rating**: a measure of per-minute production adjusted for pace.                                                                               | `31.5`                 |
| `ts_percent`  | **True Shooting Percentage**: a measure of shooting efficiency.                                                                                                   | `0.669`                |
| `x3p_ar`      | **3-Point Attempt Rate**: percentage of a player's shots that were 3-pointers.                                                                                    | `0.554`                |
| `f_tr`        | **Free Throw Rate**: number of free throw attempts per field goal attempt.                                                                                        | `0.301`                |
| `..._percent` | Percentages of available rebounds, assists, etc., a player had while on the floor.                                                                                | `33.8` (`ast_percent`) |
| `usg_percent` | **Usage Percentage**: an estimate of the percentage of team plays "used" by a player while they were on the floor.                                                | `32.6`                 |
| `ows`         | **Offensive Win Shares**: an estimate of a player's contribution to their team's wins through offense.                                                            | `13.8`                 |
| `dws`         | **Defensive Win Shares**: an estimate of a player's contribution to their team's wins through defense.                                                            | `4.1`                  |
| `ws`          | **Win Shares**: the sum of OWS and DWS.                                                                                                                           | `17.9`                 |
| `ws_48`       | **Win Shares per 48 Minutes**: an estimate of win shares per game (league average is approx. 0.100).                                                              | `0.318`                |
| `obpm`        | **Offensive Box Plus/Minus**: a box score estimate of a player's offensive contribution to the team in points per 100 possessions, above a league-average player. | `9.9`                  |
| `dbpm`        | **Defensive Box Plus/Minus**: a box score estimate of a player's defensive contribution.                                                                          | `2.1`                  |
| `bpm`         | **Box Plus/Minus**: the sum of OBPM and DBPM.                                                                                                                     | `12.0`                 |
| `vorp`        | **Value Over Replacement Player**: a box score estimate of the points per 100 team possessions that a player contributed above a replacement-level player.        | `9.8`                  |

---

### `Player Per Game.csv`

Contains traditional player stats, averaged on a per-game basis.

| Column Name    | Description                                                 | Example                 |
| :------------- | :---------------------------------------------------------- | :---------------------- |
| `season`       | The year the season ended.                                  | `2006`                  |
| `player`       | The player's name.                                          | `Kobe Bryant`           |
| `g`            | Games played in the season.                                 | `80`                    |
| `gs`           | Games started.                                              | `80`                    |
| `..._per_game` | Various stats (FG, FGA, 3P, AST, etc.) calculated per game. | `35.4` (`pts_per_game`) |

---

### `Per 100 Poss.csv`

Contains **player-level** stats, normalized to a per-100-possession basis.

| Column Name        | Description                                                                           | Example                     |
| :----------------- | :------------------------------------------------------------------------------------ | :-------------------------- |
| `season`           | The year the season ended.                                                            | `1988`                      |
| `player`           | The player's name.                                                                    | `Michael Jordan`            |
| `..._per_100_poss` | Various player stats (FG, FGA, PTS, etc.) per 100 team possessions.                   | `45.0` (`pts_per_100_poss`) |
| `o_rtg`            | **Offensive Rating**: an estimate of points produced by a player per 100 possessions. | `124`                       |
| `d_rtg`            | **Defensive Rating**: an estimate of points allowed by a player per 100 possessions.  | `101`                       |

---

### `Player Shooting.csv`

Contains detailed player shooting data, breaking down shots by distance and type.

| Column Name            | Description                                                                            | Example                                |
| :--------------------- | :------------------------------------------------------------------------------------- | :------------------------------------- |
| `season`               | The year the season ended.                                                             | `2019`                                 |
| `player`               | The player's name.                                                                     | `James Harden`                         |
| `avg_dist_fga`         | The average distance (in feet) of the player's field goal attempts.                    | `16.3`                                 |
| `percent_fga_...`      | The percentage of the player's shots that came from a specific range.                  | `0.536` (`percent_fga_from_x3p_range`) |
| `fg_percent_from_...`  | The player's field goal percentage from a specific range.                              | `0.368` (`fg_percent_from_x3p_range`)  |
| `percent_assisted_...` | The percentage of a player's made shots (2-pointers or 3-pointers) that were assisted. | `0.155` (`percent_assisted_x3p_fg`)    |
| `percent_corner_3s...` | The percentage of a player's 3-point attempts that came from the corners.              | `0.045`                                |
| `corner_3_point_...`   | The player's shooting percentage on corner 3-pointers.                                 | `0.385`                                |

---

### `Player Career Info.csv`

Contains biographical and career information for each player.

| Column Name  | Description                                             | Example        |
| :----------- | :------------------------------------------------------ | :------------- |
| `player`     | The player's name.                                      | `LeBron James` |
| `player_id`  | A unique ID for the player.                             | `jamesle01`    |
| `pos`        | The player's primary position.                          | `SF`           |
| `ht_in_in`   | The player's height in inches.                          | `81`           |
| `wt`         | The player's weight in pounds.                          | `250`          |
| `birth_date` | The player's date of birth.                             | `1984-12-30`   |
| `colleges`   | The college(s) the player attended.                     | `NA`           |
| `from`       | The first season the player played.                     | `2004`         |
| `to`         | The last season the player played.                      | `2024`         |
| `debut`      | The date of the player's first game.                    | `2003-10-29`   |
| `hof`        | A flag indicating if the player is in the Hall of Fame. | `False`        |

---

### `Opponent Stats Per 100 Poss.csv`

This file contains the statistics that a team's opponents averaged against them, normalized per 100 possessions. This is used to evaluate defensive performance.

| Column Name            | Description                                                                 | Example                         |
| :--------------------- | :-------------------------------------------------------------------------- | :------------------------------ |
| `season`               | The year the season ended.                                                  | `2004`                          |
| `team`                 | The team whose defense is being measured.                                   | `Detroit Pistons`               |
| `opp_..._per_100_poss` | Various stats (FG, FGA, 3P, etc.) allowed to opponents per 100 possessions. | `95.4` (`opp_pts_per_100_poss`) |

---

### Other Files

This section provides a brief overview of the remaining files. Their column structures are often similar to the detailed tables above.

-   **`Team Totals.csv`**: Season-long cumulative team stats (not averaged per game).
-   **`Player Totals.csv`**: Season-long cumulative player stats.
-   **`Per 36 Minutes.csv`**: Player stats normalized to a per-36-minute basis.
-   **`Opponent Stats Per Game.csv`**: Opponent stats averaged on a per-game basis.
-   **`Opponent Totals.csv`**: Season-long cumulative opponent stats.
-   **`Player Play By Play.csv`**: Advanced player metrics derived from play-by-play logs, such as on/off court impact.
-   **`Draft Pick History.csv`**: Information on each draft pick, including team, player, and pick number.
-   **`End of Season Teams.csv` & `End of Season Teams (Voting).csv`**: Lists players who made honors like All-NBA and includes voting results.
-   **`Player Award Shares.csv`**: Voting results for major awards like MVP.
-   **`All-Star Selections.csv`**: Lists All-Star selections for each season.
-   **`Player Season Info.csv`**: Contains player metadata for a given season, like experience.
-   **`Team Abbrev.csv`**: A helper file to map team names to abbreviations.
```
