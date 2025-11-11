data {
  int<lower=0> N;   // number of data items (games)
  int<lower=0> K;   // number of predictors
  matrix[N, K] x_h;   // predictor matrix for home team
  matrix[N, K] x_a;   // predictor matrix for away team
  vector[N] y;      // outcome vector
}
parameters {
  real alpha;  // intercept
  vector[K] beta;  // coefficients for predictors
  real<lower=0> sigma;  // error scale
}
model {
 // weakly informative priors for parameters 
  alpha ~ normal(0, 35);
  beta ~ normal(0, 35); 
  sigma ~ normal(0, 10);

  // combined intermediary parameter
  vector[N] mu = x_h * beta - x_a * beta + alpha; 

  // data model
  y ~ normal(mu, sigma);  
}

generated quantities {
  vector[N] mu = x_h * beta - x_a * beta + alpha; 
  vector[N] log_lik;
  vector[N] y_prior; 
  vector[K] beta_prior;
  vector[N] mu_prior;
  // --- Prior Predictive Sampling ---
  real alpha_prior = normal_rng(0, 35);
  for (k in 1:K) {
    beta_prior[k] = normal_rng(0, 35);
  }
  real sigma_prior = -1; 
  while (sigma_prior < 0) {
    sigma_prior = normal_rng(0, 10);
  }
  mu_prior = x_h * beta_prior - x_a * beta_prior + alpha_prior;
  for (n in 1:N){
    log_lik[n] = normal_lpdf(y[n] | mu[n], sigma);
    y_prior[n] = normal_rng(mu_prior[n], sigma_prior);
  }

}
