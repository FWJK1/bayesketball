import pymc as pm
import numpy as np
import pandas as pd

import duckdb
import os
import arviz as az

if "game_logs.csv" not in os.listdir("data"):
    print("Generating game_logs.csv...")
    conn = duckdb.connect(database="data/nba.sqlite", read_only=False)
    sql = """
        select 
            game_id, 
            game_date::date as date, 
            team_id_home as home_team_id, 
            team_name_home as home_team,
            pts_home as home_team_points, 
            plus_minus_home as pd_home,
            team_id_away as away_team_id, 
            team_name_away as away_team, 
            pts_away as away_team_points, 
            plus_minus_away as pd_away, 
        from game where team_id_away is not null
    """

    conn.query(sql).df().to_csv("data/game_logs.csv", index=False)


game_df = pd.read_csv("data/game_logs.csv")
all_teams = pd.concat((game_df["home_team"], game_df["away_team"])).unique()

# create unique ids for all teams
team_ids = {team_name: i for i, team_name in enumerate(all_teams)}

game_df["home_team_idx"] = game_df["home_team"].apply(
    lambda team_name: team_ids[team_name]
)
game_df["away_team_idx"] = game_df["away_team"].apply(
    lambda team_name: team_ids[team_name]
)

game_df.dropna(subset=["home_team_idx", "away_team_idx"], inplace=True)

home_idx = game_df["home_team_idx"]
away_idx = game_df["away_team_idx"]

# Values for placeholder vars (for simulation)
home_idx_train = game_df["home_team_idx"].values.astype(int)
away_idx_train = game_df["away_team_idx"].values.astype(int)
home_points_train = game_df["home_team_points"].values
away_points_train = game_df["away_team_points"].values


def build_model():
    with pm.Model() as model:

        # create placeholders for simulation later
        home_idx_data = pm.Data("home_idx_data", home_idx)
        away_idx_data = pm.Data("away_idx_data", away_idx)
        # hyperpriors
        league_offense_mu = pm.Normal("league_offense_mu", mu=100, sigma=10.0)
        league_defense_mu = pm.Normal("league_defense_mu", mu=0.0, sigma=1.0)
        league_offense_sigma = pm.HalfNormal("league_offense_sigma", sigma=10.0)
        league_defense_sigma = pm.HalfNormal("league_defense_sigma", sigma=10.0)

        # priors
        # offense, defense
        home_adv = pm.Normal("home_adv", mu=1.5, sigma=1.0)
        # offense_strength = pm.Normal(
        #     "offense_strength",
        #     mu=1.5,
        #     sigma=1.0,
        #     shape=len(all_teams),
        # )
        offense_strength = pm.Normal(
            "offense_strength",
            mu=league_offense_mu,
            sigma=league_offense_sigma,
            shape=len(all_teams),
        )
        # defense_strength = pm.Normal(
        #     "defense_strength", mu=1.5, sigma=3, shape=len(all_teams)
        # )

        # Gemini said this solves identifiability? who cares
        # defense_strength = pm.Normal(
        #     "defense_strength", mu=0.0, sigma=3, shape=len(all_teams)  # Centered at 0
        # )
        defense_strength = pm.Normal(
            "defense_strength",
            mu=league_defense_mu,
            sigma=league_defense_sigma,
            shape=len(all_teams),  # Centered at 0
        )
        game_noise = pm.HalfNormal("game_noise", sigma=15)

        # regression
        expected_home_team_points = (
            home_adv + offense_strength[home_idx_data] - defense_strength[away_idx_data]
        )
        expected_away_team_points = (
            offense_strength[away_idx_data] - defense_strength[home_idx_data]
        )

        # y
        obs_home_points_data = pm.Data("obs_home_points_data", home_points_train)
        obs_away_points_data = pm.Data("obs_away_points_data", away_points_train)

        # likelihood
        home_team_points = pm.Normal(
            "home_team_points",
            mu=expected_home_team_points,
            sigma=game_noise,
            observed=obs_home_points_data,
        )
        away_team_points = pm.Normal(
            "away_team_points",
            mu=expected_away_team_points,
            sigma=game_noise,
            observed=obs_away_points_data,
        )

    return model


if __name__ == "__main__":

    model = build_model()
    with model:
        idata = pm.sample(draws=2000, tune=1500, cores=4, target_accept=0.9)
        idata.to_netcdf("home_and_away.nc")
