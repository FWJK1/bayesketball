import pymc as pm
import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from bayesic_offense_defense import build_model

model = build_model()


print("Running prior predictive check...")
with model:
    prior_pred_idata = pm.sample_prior_predictive(samples=500)


prior_home_scores = prior_pred_idata.prior_predictive["home_team_points"]
prior_away_scores = prior_pred_idata.prior_predictive["away_team_points"]

prior_home_scores_flat = prior_home_scores.values.flatten()
prior_away_scores_flat = prior_pred_idata.prior_predictive[
    "away_team_points"
].values.flatten()
pd = prior_home_scores_flat - prior_away_scores_flat

plt.figure(figsize=(12, 7))
sns.histplot(pd, kde=True, color="green")
plt.title("Prior Predictive Check: Point Differential", fontsize=16)
plt.xlabel("PD")
plt.ylabel("Density")
plt.show()
