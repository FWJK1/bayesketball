
# install.packages("rstan", repos = "https://cloud.r-project.org/", dependencies=TRUE)
library(tidyverse)
library(rstan)
library(bayesplot)
library(glue)
getwd()


# Sample data
x <- 1:10
y <- x^2 + rnorm(10, 0, 5)

# Base R plot
plot(x, y,
     main = "Example Plot",
     xlab = "X values",
     ylab = "Y values",
     pch = 19,        # solid circles
     col = "blue")

# Add a regression line
abline(lm(y ~ x), col = "red", lwd = 2)


stan_files <- c("general_non_possession.stan")

for (file in stan_files) {
  cat("starting,", stan_file, "\n")
  x_h_data <- read.csv("data/general_pct_non_possession/x_h_train.csv")
  x_a_data <- read.csv("data/general_pct_non_possession/x_a_train.csv")
  y_data <- read.csv("data/general_pct_non_possession/y_train.csv")


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
    iter = 2000, 
    warmup = 1000,
    verbose=TRUE,
    refresh=0,
    seed=1,
  )

  cat("fit complete \n")
  posterior_df <- as.data.frame(fit)
  name <- paste0("posterior_", tools::file_path_sans_ext(file))
  csv_name <- glue("{name}.csv")
  write.csv(posterior_df, csv_name, row.names = FALSE)
  cat("saved csv \n")
}
