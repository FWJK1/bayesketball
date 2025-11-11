import arviz as az

idata = az.from_netcdf("home_and_away.nc")


ll_home = idata.log_likelihood.home_team_points
ll_away = idata.log_likelihood.away_team_points

ll_total = ll_home.values + ll_away.values
idata.log_likelihood["ll_total"] = (ll_home.dims, ll_total)


# 4. Pass the combined array to WAIC and LOO
print("Calculating WAIC...")
# Use the log_likelihood argument
waic_data = az.waic(idata, var_name="ll_total")
print("--- WAIC ---")
print(waic_data)
print("\n")

print("Calculating PSIS-LOO...")
# Use the log_likelihood argument
loo_data = az.loo(idata, var_name="ll_total")
print("--- PSIS-LOO ---")
print(loo_data)
