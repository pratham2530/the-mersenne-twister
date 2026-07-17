from stats_tests import Tests


def main():
    tests = Tests(default_size=10_000)

    print("=" * 62)
    print("                  RNG STATISTICAL TEST RESULTS")
    print("=" * 62)

    print("NOTE: Close any plots generated to continue the programme.")
    print("-" * 62)

    # 1. Chi-Squared Test
    p_value_chi, if_pass = tests.chi_squared()
    print(f"Chi-Squared Test: p-value: {p_value_chi:.4f} ({if_pass})")

    print("-" * 62)

    # 2. KS Test for Chi-Squared P-Values
    if_plot = False
    print(f"KS Tests for Chi-Squared p-values: (plot: {if_plot})")

    ks_results = {}
    for num_trial in (100, 200, 500, 1000):
        ks_statistic, ks_p_value, if_pass = tests.chi_squared_p_value_dist(num_trials=num_trial, plot=if_plot)
        print(f"  └─ Trials: {num_trial:4d} | KS Statistic: {ks_statistic:.4f} | KS p-value: {ks_p_value:.4f} ({if_pass})")

    print("-" * 62)

    # 3. Runs Test
    z_score, p_val_runs, if_pass = tests.runs_test()
    print(f"Runs Test: z-score: {z_score:.4f} | p-value: {p_val_runs:.4f} ({if_pass})")

    print("-" * 62)

    # 4. Serial Correlation Test
    print("Serial Correlation Test:")

    lags, correlation_coefficients, max_corr, confidence_interval, if_pass = tests.serial_correlation()
    for i in range(len(lags)): 
        if correlation_coefficients[i] > 0: 
            print(f"  └─ Lag: {lags[i]:4d}  | Correlation Coefficient: {correlation_coefficients[i]:+.4f}")
        else: 
            print(f"  └─ Lag: {lags[i]:4d}  | Correlation Coefficient: {correlation_coefficients[i]:+.4f}")

    print(f"\nMaximum Correlation: {max_corr:.4f} | Confidence Interval {confidence_interval:.4f} ({if_pass})")

    print("-" * 62)

    # 5. 3D visual plot of tuples
    if_plot = True
    print(f"Visual Plot of Tuples (plot: {if_plot})")

    tests.plot_tuples(dimension=3, plot=if_plot)

    print("-" * 62)

    # 6. Monte Carlo Convergence Test
    if_plot = True
    print(f"Monte Carlo Convergence Test: (plot: {if_plot})")

if __name__ == "__main__": 
  main()
