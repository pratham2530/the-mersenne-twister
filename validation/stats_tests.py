import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

from tools import Random


class Tests: 
    """
    Test #1. Chi-squared: tests if the sample follows a uniform distribution. 
    Test #2. Kolmogorov–Smirnov (KS): tests uniformity of p-values obtained from test #1. 
    Test #3. Serial Correlation: tests for linear correlations in sample. 
    Test #4. Wald-Wolfowitz runs: tests if new generated numbers are independent of previously 
             generated numbers. 
    Test #5. 2D/3D Visual Plot of Tuples: visual test of serial correlation and sample bias. 
    Test #6. Monte Carlo Error Convergence: checks that the absolute 
             estimation error decays at the theoretical O(1/sqrt(N)) rate. 
    """

    def __init__(self, a=0, b=1, seed=5489, default_size=10_000): 
        self.a = a
        self.b = b
        self.seed = seed

        # Preserve the generator state by instantiating once. 
        self.rng = Random(a=self.a, b=self.b, seed_val=self.seed)   

        # Sample cache for tests #1, #3, #4 and #5.  
        self.sample = np.array(self.generate_sample(default_size))


    def generate_sample(self, sample_size): 
        """Returns a sample of random numbers in [a, b] of size sample_size."""
        return self.rng.gen_nums(size=sample_size)


    def chi_squared(self, sample=None, num_bins=100, alpha=0.05): 
        """
        Chi-squared Goodness of Fit test to check sample uniformity. 

        H_0: the sample is drawn from Uniform[a, b].
        """
        if sample is None: 
            sample = self.sample 

        observed, _ = np.histogram(sample, bins=num_bins, range=(self.a, self.b))

        # Expected frequency per bin is uniform. 
        expected = len(sample) / num_bins

        _, p_value = stats.chisquare(observed, expected)
        if_pass = "ACCEPT" if p_value > alpha else "REJECT"

        return float(p_value), if_pass
    

    def chi_squared_p_value_dist(self, num_trials=500, size=10_000, num_bins=100, alpha=0.05, plot=False):
        """
        Plots distribution of p-values from the Chi-squared test to check uniformity of p-values. 

        To assess this numerically, a KS test is used. 
        """
        p_values = []

        # Draw a large sample once to generate different smaller samples. 
        stream = self.generate_sample(size * num_trials)

        for i in range(num_trials):
            sample = stream[i * size: (i + 1) * size]   
            p_value, _ = self.chi_squared(sample, num_bins=num_bins)
            p_values.append(p_value)    

        if plot:
            plt.figure(figsize=(7, 4))
            plt.hist(p_values, bins=20, range=(0,1), density=True, color="blue", edgecolor="black", alpha=0.8)
            plt.axhline(y=1.0, color="crimson", linestyle="--", label="Theoretical Uniform")
            plt.title(f"P-value Distribution (M={num_trials} Trials, N={size})")
            plt.xlabel("p-value")
            plt.ylabel("Probability Density")
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.legend()
            plt.show(block=True)

        ks_statistic, ks_p_value = stats.kstest(p_values, "uniform")

        # Compute critical value for an arbitrary alpha. 
        ks_numerator = stats.kstwobign.ppf(1 - alpha)
        critical_value = float(ks_numerator / np.sqrt(num_trials))
        if_pass = "ACCEPT" if ks_statistic < critical_value and ks_p_value > alpha else "REJECT"

        return float(ks_statistic), float(ks_p_value), if_pass
    

    def serial_correlation(self, max_lag=10, alpha=0.05):
        """
        Computes the sample autocorrelation function (ACF) up to max_lag.

        Checks if there are no linear correlations. 
        H_0: The sequence is white noise (constant mean, constant variance
        and zero autocorrelation for positive lags). 
        """
        sample_mean = self.sample.mean()
        sample_std = self.sample.std()

        lags = []
        correlation_coefficients = []

        Sxx = np.sum((self.sample - sample_mean) ** 2)

        # Compute sample autocorrelation for each lag.  
        for lag in range(1, max_lag + 1): 
            x_t = self.sample[:-lag]
            x_t_plus_lag = self.sample[lag:]

            corr = float(np.sum((x_t - sample_mean) * (x_t_plus_lag - sample_mean)) / Sxx)

            lags.append(lag)
            correlation_coefficients.append(corr)

        # By Bartlett's formula, the standard deviation is asymptotically 1 / sqrt(sample size). 
        z_score = stats.norm.ppf(1 - alpha / 2)
        confidence_interval = float(z_score / np.sqrt(len(self.sample)))

        # Check if the correlation coefficients lie in the CI. 
        max_corr = max(abs(c) for c in correlation_coefficients)
        if_pass = "ACCEPT" if max_corr < confidence_interval else "REJECT"

        return lags, correlation_coefficients, max_corr, confidence_interval, if_pass


    def runs_test(self, alpha=0.05):
        """
        Non-parametric Wald-Wolfowitz runs test for independence.

        Splits the sample around its median to create a binary sequence and 
        counts consecutive blocks of bits ("runs") above or below the median.
        H_0: The sequence ordering is completely random.
        """
        median = np.median(self.sample)
        filtered_sample = self.sample[self.sample != median]
        
        # Count number of elements above and below the median. 
        binary_seq = (filtered_sample > median).astype(int)
        n1 = np.sum(binary_seq == 1)                        # Elements above median. 
        n2 = np.sum(binary_seq == 0)                        # Elements below median. 
        n = n1 + n2
        
        # Avoid division by 0 when calculating z-statistic. 
        if n1 == 0 or n2 == 0:
            return 0.0, 1.0, False
            
        # runs = 1 + number of switches between 0s and 1s. 
        runs = 1 + np.sum(np.abs(np.diff(binary_seq)))
        
        # See stats_tests_results.md for derivations. 
        expected_runs = ((2 * n1 * n2) / n) + 1
        variance = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n**2 * (n - 1))
        
        z_statistic = (runs - expected_runs) / np.sqrt(variance)

        # Two-tailed test: reject if too few or many runs. 
        p_value = 2 * (1 - stats.norm.cdf(np.abs(z_statistic)))
        if_pass = p_value > alpha
        
        return float(z_statistic), float(p_value), if_pass


    def plot_tuples(self, dimension=2, num_points=5000, plot=False):
        """
        Plots successive numbers from the sample in 2D or 3D. 
        
        A good generator will fill the space evenly to create uniform square or cube.
        Distinct stripes, clusters, or blank spaces, indicate a hidden repeating 
        structure or bias in the sequence.
        """
        pts = min(num_points, len(self.sample) - dimension)
        
        # Plot coordinates (x_i, x_{i+1})
        if dimension == 2 and plot:
            x = self.sample[:pts]
            y = self.sample[1:pts+1]
            
            plt.figure(figsize=(6, 6))
            plt.scatter(x, y, s=0.5, alpha=0.6, color="blue")
            plt.title("2D Phase Space Plot: $(x_i, x_{i+1})$")
            plt.xlabel("$x_i$")
            plt.ylabel("$x_{i+1}$")
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.show(block=True)
            
        # Plot coordinates (x_i, x_{i+1}, x_{i+2})
        elif dimension == 3 and plot:
            x = self.sample[:pts]
            y = self.sample[1:pts+1]
            z = self.sample[2:pts+2]
            
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111, projection="3d")
            ax.scatter(x, y, z, s=0.5, alpha=0.6, color="red")
            ax.set_title("3D Phase Space Plot: $(x_i, x_{i+1}, x_{i+2})$")
            ax.set_xlabel("$x_i$")
            ax.set_ylabel("$x_{i+1}$")
            ax.set_zlabel("$x_{i+2}$")
            plt.show(block=True)

        else:
            raise ValueError("Dimension must be 2 or 3.")


    def check_convergence_rate(self, sample_sizes=None, num_repeats=25, plot=False):
            """
            Measures how quickly the generator's error shrinks as sample size increases.
            
            Uses sequential pairs the sample as coordinates to estimate the area of a quadrant. 
            Tracks mean absolute error (MAE) across varying sample sizes, 
            fits a regression line to the log-log error curve, and 
            verifies if the resulting error decay slope scales close to -0.5.
            """
            if sample_sizes is None:
                sample_sizes = [100, 300, 1_000, 3_000, 10_000, 30_000]
                
            avg_errors = []
            true_value = np.pi / 4
            max_size = max(sample_sizes)
    
            # Performance: pre-allocate a matrix to track absolute errors in all tests. 
            error_matrix = np.zeros((len(sample_sizes), num_repeats))

            for rep in range(num_repeats):
                # Performance: draw a large sample once to slice from.
                stream = np.array(self.generate_sample(max_size * 2))
                x_stream = stream[:max_size]
                y_stream = stream[max_size:]
                
                # Perfomance: pre-compute Euclidean spatial distances. 
                distances_squared = x_stream**2 + y_stream**2
            
                for idx, N in enumerate(sample_sizes):
                    inside_circle = np.sum(distances_squared[:N] <= 1.0)
                    mc_estimate = inside_circle / N
                    error_matrix[idx, rep] = abs(mc_estimate - true_value)
                    
            # Average the errors across all trials to smooth out random variance. 
            avg_errors = np.mean(error_matrix, axis=1)
                
            log_N = np.log(sample_sizes)
            log_E = np.log(avg_errors)
    
            # Perform linear regression in log-log space to extract the slope. 
            slope, intercept = np.polyfit(log_N, log_E, 1)
        
            if plot: 
                plt.figure(figsize=(8, 5))
                plt.loglog(sample_sizes, avg_errors, "o-", label=f"Empirical Slope: {slope:.3f}", color="crimson")
                
                # Shift the theoretical line to align with the data for comparison.
                theoretical_line = np.exp(intercept) * (1 / np.sqrt(sample_sizes))
                plt.loglog(sample_sizes, theoretical_line, "--", label="Theoretical $1/\\sqrt{N}$ (Slope: -0.500)", color="black", alpha=0.7)
                
                plt.title("Monte Carlo Convergence Rate Check")
                plt.xlabel("Sample Size (N)")
                plt.ylabel("Mean Absolute Error")
                plt.grid(True, which="both", linestyle="--", alpha=0.5)
                plt.legend()
                plt.show(block=True)
            
            return float(slope)

    empirical_slope = tests.check_convergence_rate(plot=if_plot)
    print("  └─ Theoretical Convergence Slope: -0.500")
    print(f"  └─ Empirical Convergence Slope: {empirical_slope:.4f}")

    print("=" * 62)
