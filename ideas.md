Ideas:
- including other team in the model itself?


What we are trying to predict is whether one team will beat another team or not. 

This seems like a good case for logistic regression at the top level, though maybe we can also handle it by just looking at a joint probability of each team's performance or point differential or something like that. 

The first question, then, is what the most indexed (the deepest depth) thing we are trying to predict is. Some options:
- player performance (in a given game) 
- team performance (and using the players as something that 'bubbles up')

Conceptually: a markov chain (state) model of changing basketball player skillset as a predictor for possession outcome (and time) and thus eventual score.
- We construct two latent vector of a player's abilities $\vec{\theta} _{it}^{(o)}$ and $\vec{\theta} _{it}^{(d)}$, one for offense and one for defense, at some time $t$, which are basically just vectors of their standard stats (shot percentage, assists, turnovers, steals, and so on). 
	- Each $\theta _{ij}$, the jth skill on player i, can be treated as a distribution if we want. 
	- We can also, if we want, perhaps use a hierarchical model (player position? player team? high-usage vs low-usage?) though I'm not sure this makes sense.
- we then have two main options for learning how these skills effect *per possession* outcome.
	- 1) use l2 regression to predict a distribution of *per possession outcomes*: $y_{p} = \sum \vec{\gamma}^{T}\vec{\theta}_{i}^{(o)} - \sum \vec{\lambda}^{T}\vec{\theta}^{(d)}_{j}$ --- this is more interpretable and probably easier 
	- 2) use latent low-rank matrix to predict interactions --- this is more accurate, more SOTA, but harder to interpret or implement
		- eq: $y_{p}=\sum \theta^{(o)}_{i} - \sum \theta _{j}^{(d)} + \sum u_{i}^{T}v_{j}$
	- 3 (my vote): we *first* do l2 regression to get $\gamma$ and $\lambda$, then we model the *error* as due to low-rank interactions
	- ideally we also want to predict the *time* of the possession.
	- we can then compile the per possession outcomes into general predictions for games.
- we then must also transition from $\vec{\theta}_{t}$ to $\vec{\theta}_{t+1}$, which we'll take to be game to game. We assign a prior for how each ability $\theta _{i}$ can change from one game to the next. 

