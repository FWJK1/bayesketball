# install.packages("rstan", repos = "https://cloud.r-project.org/", dependencies=TRUE)
library(tidyverse)
library(rstan)
library(bayesplot)
library(glue)
library(loo)
getwd()



rootwords <- c(
  "general_pct_non_possession",
  "general_attempt_non_possession"
)

for (rootword in rootwords) {
  dir.create(glue("results/{rootword}"), recursive = TRUE, showWarnings = FALSE)
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
    verbose = FALSE,
    refresh = 0,
    seed = 1
  )
  cat("fit complete \n")


  ## Trace Plots
  cat("fitting_trace")
  trace_array <- as.array(fit, pars = c("alpha", "beta[1]", "beta[3]", "sigma"))
  p_trace <- mcmc_trace(trace_array) +
    labs(title = "Trace Plots for Model Parameters") +
    theme(axis.text.y = element_text(size = 8))
  print(p_trace)
  ggsave(
    glue("results/{rootword}/trace_plot.png"),
    plot = p_trace, width = 8, height = 6, dpi = 300
  )
  cat("trace_saved")

  ## Save samples
  posterior_samples <- as.array(fit, pars = c("alpha", "beta", "sigma"))
  posterior_df <- as.data.frame(posterior_samples)
  csv_name <- glue("results/{rootword}/posterior_samples.csv")
  write.csv(posterior_df, csv_name, row.names = FALSE)
  cat("file_saved")

  ## Model Quality Comparison Metrics ##
  ## psis -- loo
  log_lik <- extract_log_lik(fit, parameter_name = "log_lik")
  loo_result <- loo(log_lik)
  summary_df <- as.data.frame(t(loo_result$estimates))
  write.csv(
    summary_df, glue("results/{rootword}/psis_loo_summary.csv"),
    row.names = TRUE
  )
  print(loo_result)
  cat("saved loo result)")

  ## WAIC
  waic_result <- waic(log_lik)
  summary_waic <- as.data.frame(t(waic_result$estimates))
  write.csv(
    summary_waic, glue("results/{rootword}/waic_summary.csv"),
    row.names = TRUE
  )
  cat(waic_result)
  cat("saved WAIC result")
}
