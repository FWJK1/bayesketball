# install.packages("rstan", repos = "https://cloud.r-project.org/", dependencies=TRUE)
library(tidyverse)
library(rstan)
library(bayesplot)
library(glue)
getwd()


### Test that R is working properly on WSL ###
# Sample data
x <- 1:10
y <- x^2 + rnorm(10, 0, 5)

# Base R plot
plot(x, y,
  main = "Example Plot",
  xlab = "X values",
  ylab = "Y values",
  pch = 19, # solid circles
  col = "blue"
)

# Add a regression line
abline(lm(y ~ x), col = "red", lwd = 2)
###

rootwords <- c(
  # "general_pct_non_possession",
  "general_attempt_non_possession"
)

for (rootword in rootwords) {
  file <- c(glue("src/stan/{rootword}.stan"))
  cat("starting,", file, "\n")
  x_h_data <- as.matrix(read.csv(glue("data/{rootword}/x_h_train.csv")))
  x_a_data <- as.matrix(read.csv(glue("data/{rootword}/x_a_train.csv")))
  y_data <- read.csv(glue("data/{rootword}/y_train.csv"))$plus_minus_home

  ## clean any missing data ##
  complete_idx <- complete.cases(x_h_data, x_a_data, y_data)
  x_h_data <- x_h_data[complete_idx, ]
  x_a_data <- x_a_data[complete_idx, ]
  y_data <- y_data[complete_idx]


  stan_data <- list(
    N = length(y_data),
    K = ncol(x_h_data),
    x_h = x_h_data,
    x_a = x_a_data,
    y = y_data
  )


  fit <- stan(
    file = file,
    data = stan_data,
    chains = 4,
    iter = 1500,
    warmup = 1000,
    verbose = FALSE, ,
    refresh = 0,
    seed = 1
  )

  posterior_samples <- as.array(fit)

  p_trace <- mcmc_trace(posterior_samples) +
    labs(title = "Trace Plots for Model Parameters") +
    theme(axis.text.y = element_text(size = 8))

  print(p_trace)

  cat("fit complete \n")
  posterior_df <- as.data.frame(fit)
  csv_name <- glue("results/{rootword}_posterior.csv")
  write.csv(posterior_df, csv_name, row.names = FALSE)
  cat("saved csv \n")
}
