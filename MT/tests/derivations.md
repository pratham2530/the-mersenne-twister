# Notes on Writing Code, Mathematical Derivations and Test Results

## Changes while writing code:
Before updating the `Random` and `Test` classes, the generator failed several initial tests:

1. The Chi-squared test returned a very low p-value.
2. The p-value distribution dipped right at 1.
3. Changing the denominator to $2^{32}$ instead of $2^{32} - 1$ in `gen_nums()` to output numbers in the $[0, 1)$ interval did not fix the results.
4. A Kolmogorov-Smirnov (KS) test showed weak results ($D = 0.05$, $p = 0.08$).
5. The 2D scatter plot showed clear line banding, meaning values were repeating.

At first, I thought the generator was broken. 
Then, instatiating a single generator once in the `Random` and `Test` classes passed the tests. 
The problem was the generator was not holding its state since a new generator was instantiated when a sample was called. 
Using the numbers from a single generated for all samples ensures the numbers generated have the period of the MT. 

The following changes improved code performance: 
1. Generating a single sample for non-parametric and correlation tests to reduce memory and run less loops.
2. Using vectors to store and compute new data for the MC simulations.
3. Pre-allocating arrays to reduce memory. 

---

# Results

## Test 1: Chi-Squared
Checks numbers are generated uniformly by splitting the sample into equal-sized sub-intervals (bins). 

### Result

## Test 2: Kolmogorov-Smirnov (KS) Test
Evaluates how well the generated numbers follow a **continuous uniform distribution** $U(0, 1)$. 

* **What it tests / Expectations:** It checks the global distribution of the stream rather than localized bins. We expect the sample's empirical distribution to match the true uniform distribution closely, meaning we want a small distance metric ($D$) and a high p-value ($p > \alpha$).
* **The Mathematics:** The test calculates the empirical cumulative distribution function (ECDF), denoted as $F_n(x)$, for your sorted sample of size $n$. The KS statistic $D$ is the maximum absolute vertical distance between the ECDF and the theoretical uniform CDF, $F(x) = x$:
  $$D = \max_{x} |F_n(x) - F(x)|$$
  To find the critical value $D_{\alpha}$ at a significance level $\alpha$ (e.g., $0.05$), we use the asymptotic Kolmogorov distribution approximation for large sample sizes:
  $$D_{\alpha} \approx \frac{\sqrt{-\frac{1}{2}\ln(\frac{\alpha}{2})}}{\sqrt{n}}$$
  If our empirical $D > D_{\alpha}$, we reject the null hypothesis of uniformity.

## Test 3: Serial Correlation
Checks for **linear correlations** between consecutive values in the sequence. 
That is, is the current random number $x_i$ correlated with the next $x_{i+1}$. 
Formally, this correlation is quantified by the lag-1 autocorrelation coefficient. 
For a strong generator, the serial correlation coefficient should be close to zero. 

Given a sample sequence of length $n$ with mean $\bar{x}$, the lag-1 autocorrelation coefficient $\rho_1$ is:
  
$$\rho_1 = \frac{\sum_{i=1}^{n-1} (x_i - \bar{x})(x_{i+1} - \bar{x})}{\sum_{i=1}^{n} (x_i - \bar{x})^2}$$
  
Under the null hypothesis that the sequence is independently generated, $\rho_1$ is asymptotically a $N \left(\frac{-1}{n - 1}, \frac{1}{n} \right)$ distribution. 

## Test 4: Runs Test
The Wald-Wolfowitz runs test evaluates **serial independence** by tracking sequential ordering patterns. 

* **What it tests / Expectations:** It categorizes data points based on whether they fall above or below the sequence median, transforming the data into a binary sequence. It then counts "runs" (unbroken blocks of continuous ones or zeros). We expect the total number of observed runs to align tightly with what pure chance would dictate; too few runs imply clustering, while too many imply systematic oscillation.
* **Derivations of Expected Value and Variance:** Let $n_1$ be the number of elements above the median, $n_2$ be the number of elements below the median, and $n = n_1 + n_2$. 
  
  The expected number of runs ($R$) is derived by looking at the probability of a switch occurring between any two adjacent elements in a randomly permuted sequence. The probability that two adjacent elements are different is $\frac{2n_1n_2}{n(n-1)}$. Since there are $n-1$ adjacent transitions in a sequence of length $n$, the expected value simplifies to:
  $$\text{E}(R) = 1 + (n-1)\left[\frac{2n_1n_2}{n(n-1)}\right] = \frac{2n_1n_2}{n} + 1$$
  
  By tracking the covariance of these indicators across the permuted sequence, the exact variance of the number of runs is derived as:
  $$\text{Var}(R) = \frac{2n_1n_2(2n_1n_2 - n)}{n^2(n - 1)}$$
  These parameters are used to construct a standard $Z$-statistic: $Z = \frac{R - \text{E}(R)}{\sqrt{\text{Var}(R)}}$.

## Test 5: 2D/3D Plot
This is a **visual phase space audit** used to catch structural defects that standard scalar statistical tests often miss.

* **What it tests / Expectations:** By plotting sequential coordinates—$(x_i, x_{i+1})$ for 2D and $(x_i, x_{i+1}, x_{i+2})$ for 3D—we can see how the random numbers fill a higher-dimensional space. We expect a high-quality generator to fill the square or cube completely uniformly. Any visible defects like distinct strips of lines (hyperplanes), geometric clustering, or empty voids indicate a broken generator state sequence.

## Test 6: MC Error Convergence
This test measures how well our generator performs when tasked with a classic physical simulation problem.

* **The Mathematics of Monte Carlo:** Consider estimating the area of a quarter circle bounded within a unit square. The true theoretical area is $I = \pi / 4$. We generate independent coordinate pairs $(x_i, y_i) \sim U(0,1) \times U(0,1)$ from our stream and evaluate an indicator function checking if $x_i^2 + y_i^2 \le 1$. The estimator is the sample mean:
  $$\hat{I}_N = \frac{1}{N}\sum_{i=1}^N \mathbb{1}_{\{x_i^2 + y_i^2 \le 1\}}$$
  
* **Derivation of the $-0.5$ Slope:** Because each random point is an independent Bernoulli trial, the variance of our estimator scales directly with the sample size: $\text{Var}(\hat{I}_N) = \frac{\sigma^2}{N}$, where $\sigma^2$ is the variance of a single trial. By the Central Limit Theorem, the Mean Absolute Error (MAE) is proportional to the standard deviation of our estimator:
  $$\text{MAE} = \text{E}[|\hat{I}_N - I|] \propto \frac{\sigma}{\sqrt{N}} = \sigma N^{-0.5}$$
  Taking the natural logarithm of both sides transforms this relationship into a linear equation:
  $$\ln(\text{MAE}) = -0.5 \ln(N) + \ln(\sigma)$$
  
* **Link to Generator & Expectations:** If our generator streams numbers with authentic entropy and zero structural correlation, fitting a linear regression line to our log-log error curve must yield an empirical slope close to $-0.5$. A slope drifting far from $-0.5$ reveals underlying patterns or defects in how the generator handles sample size scaling.
