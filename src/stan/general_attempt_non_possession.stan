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
