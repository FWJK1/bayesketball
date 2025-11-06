## Models

### PyMC

`bayesic_offense_defense.py`

Let $i$ be the index for the home team and $j$ be the index for the away team for a given game. Let $N$ be the total number of teams.

The model estimates an offensive strength ($\alpha_k$) and a defensive strength ($\beta_k$) for each team $k \in \{1, \dots, N\}$, as well as a league-wide home advantage ($h$).

1. Likelihood (Game-Level)

The observed points for the home team ($y_h$) and away team ($y_a$) are modeled as draws from a Normal distribution. The expected scores ($\mu_h$ and $\mu_a$) are determined by the teams' strengths and the home advantage.

$$
\begin{aligned}
\text{Expected Home Score: } & \mu_h = h + \alpha_i - \beta_j \\
\text{Expected Away Score: } & \mu_a = \alpha_j - \beta_i
\end{aligned}
$$

The likelihood for the observed scores is then:

$$
\begin{aligned}
y_h \sim \text{Normal}(\mu_h, \sigma_y) \\
y_a \sim \text{Normal}(\mu_a, \sigma_y)
\end{aligned}
$$

$h$: home_adv

$\alpha_i$: offense_strength[home_idx]

$\beta_j$: defense_strength[away_idx]

$\alpha_j$: offense_strength[away_idx]

$\beta_i$: defense_strength[home_idx]

$\sigma_y$: game_noise

2. Priors (Team-Level)

Each team's offensive and defensive strengths are drawn from league-wide distributions (hyperpriors). The game_noise and home_adv also have their own priors.

$$
\begin{aligned}
h & \sim \text{Normal}(1.5, 1.0) && \text{(home\_adv)} \\
\sigma_y & \sim \text{HalfNormal}(15) && \text{(game\_noise)} \\
\alpha_k & \sim \text{Normal}(\mu_\alpha, \sigma_\alpha) && \text{for } k = 1, \dots, N \text{ (offense\_strength)} \\
\beta_k & \sim \text{Normal}(\mu_\beta, \sigma_\beta) && \text{for } k = 1, \dots, N \text{ (defense\_strength)}
\end{aligned}
$$

3. Hyperpriors (League-Level)

These are the priors for the parameters of the team-level distributions, representing the league's average offense/defense and the variation across the league.

$$
\begin{aligned}
\mu_\alpha & \sim \text{Normal}(100, 10.0) && \text{(league\_offense\_mu)} \\
\sigma_\alpha & \sim \text{HalfNormal}(10.0) && \text{(league\_offense\_sigma)} \\
\mu_\beta & \sim \text{Normal}(0.0, 1.0) && \text{(league\_defense\_mu)} \\
\sigma_\beta & \sim \text{HalfNormal}(10.0) && \text{(league\_defense\_sigma)}
\end{aligned}
$$

## Credits

Written by

-   Prithaj Nath
-   Nate Borland
-   Fitz Koch
    fw.j.keenan.koch@gmail.com
    fkeenank@uvm.edu
