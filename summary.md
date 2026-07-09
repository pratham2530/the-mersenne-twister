# A summary of the Mersenne Twister (MT)

# Introduction
Python implemented the MT in C to create the `random()` function. The standard implementation of the algorithm used is **MT19937**, which has a 32-bit word length. **19937** represents $2^{19937} - 1$ which is a Mersenne Prime and the period of the generator. 

The following implementation details are derived from the following video: [The Most Popular Pseudo-Random Number Generator - The Mersenne-Twister](https://www.youtube.com/watch?v=TF4PLUcJO5w).

---

### Overview of the algorithm
MT19937 works by maintaining an array of 624 32-bit unsigned integers called a state grid. A seed value is used to fill the state grid sequentially.

Note that in the following "number", "integer", "element" and "cell" are often interchanged (although a cell is where an integer lives in). 

There are three main phases: 
1. **Initialisation (`state_grid`):** the state grid is filled using a linear recurrence relation. Bitwise operations are used to mix bits to ensure any single bit has an influence on other bits. For example, leftward bit shifts help small changes in the initial seed value to have a large changes in higher-order bits. 

    Using bit shits and XOR operations, information is redistributed across upper and lower bits helping to generate more uniformly random integers. Also, a multiplier constant helps to make small seed values larger and make the system more random; in information theory, this is called increasing entropy. 

2. **Twisting (`twist`):** once the state grid is filled, the generator runs a twist on all the numbers. 

    The upper bit of one element are concatenated with the lower bits of the next, "multiplied" by a transition matrix (matrix $A$) by bit-masking with `matrix_a`, and XORing with the offset element at position $i + 397$. This helps to increase the influence of different bits on the whole 32-bit integer.

3. **Tempering and extraction (`extract_number`):** when a user requests a random number, the integer at the current index is extracted. 

    To ensure it passes empirical tests for true uniform randomness, four bitwise tempering operations (using bitwise shifts `<<`, `>>`, bitwise AND `&` masks, and bitwise XOR `^`) are applied to the twisted integer. Tempering breaks up small linear correlations between the numbers remaining after twisting.

---

## Class: MersenneTwister

### The state space
The state grid is an array of 624 individual 32-bit cells. Running the `state_grid()` method, the seed populates the grid and these values are used in the `twist()` and `extract_number()` methods later in the algorithm.

#### Q: Why does the state have size 624?
For a state of $k$ bits the absolute maximum number of unique non-zero states that can be cycled through before repeating is $2^k - 1$. To store this data in an array of 32-bit integers, $\lceil 19937 / 32 \rceil = 624$ integers are needed.

#### Q: What does pos_index do?
When a number is extracted, `pos_index` is incremented by one so that a new random number is generated next time. `pos_index` reers to the index slot in the `self.state` array. When `pos_index` reaches 624, `twist()` is called to overwrite all 624 cells.

---

### Method Reference: `state_grid()`
Populate the state grid using `seed_val`.

#### Q: Where does the seeding multiplier come from?
This initialising step relies on a Linear Congruential Generator (LCG). The formula used is:

$$X_i = f \cdot (X_{i - 1} \oplus (X_{i - 1} \gg 30)) + i \pmod{2^{32}}$$

*(where $\oplus$ is the bitwise XOR).*

If a "bad" multiplier is chosen, the 624 numbers generated can appear related. Donald Knuth proved that the chosen multiplier can generate numbers which are spread out uniformly across the 32-bit space by passing the spectral test. Pictorally, when the 624 numbers are plotted in multi-dimensional coordinates, there are no evident geometric correlations such as a straight line.

---

### Method Reference: `twist()`
'Twists' the entire state grid of 624 numbers to create a new grid of numbers. This method simulates a Linear Feedback Shift Register (LFSR) optimised to run on 32-bit words.

#### Q: How does a LFSR usually work?
A LFSR is a shift register whose input bit is a linear function of its previous state. For example, using the linear function XOR:
1. **Register:** a sequence of bits ($[b_n, b_{n - 1}, \dots, b_1, b_0]$).

2. **Taps:** specific positions in the register.

3. Bits are shifted right by 1 and the empty slot is filled by XORing the tapped bits.

Since there are $2^n - 1$ non-zero states, the register will eventually repeat. If the taps are chosen using a primitive polynomial, the LFSR will achieve its maximum period of $2^n - 1$ before repeating *(See the "The maths behind the `twist()` method" for more).*

#### Q: How does `twist()` generalise a LFSR?
In order to ensure each individual integer are not isolated, local and global boundary crossings are needed to introduce more randomness. Here local and global refer to the interaction of integers near and far away from each other in the state grid. 

1. Slicing and concatenating adjacent words ensures information is coupled along the array boundaries.

2. The conditional XOR with `matrix_a` represents multiplying a specialised transition matrix over $\mathbb{F}_2$. *(See the "The maths behind the `twist()` method" for more).*

3. Mixing with a cell 397 positions ahead adds a global boundary crossing and helps the algorithm pass the spectral test.

---

### Method Reference: `extract_number()`
Extract the raw number from the current index, run it through four tempering operations, and increment the pointer.

Tempering is the process of using binary operations such as bit-shifts (`<<`, `>>`), bitmasks (`&`), and XOR (`^`) to add further randomness.

After twisting, each of the 624 numbers has a large period length and appears random over a long timeframe, but they possess small linear correlations. To ensure the numbers pass tests for true uniform randomness, they need to be tempered.

Intuitively:
1. `<<` and `>>` allow higher-order and lower-order bits to interact.

2. `&` isolates sections of binary sequences.

3. `^` is used to apply the above operations to the previous state.

Since $0 = 0 \oplus 0$ and $1 = 1 \oplus 0$, specific bits can be first shifted or isolated and then mixed with the unmoved bits while keeping those specific bits unchanged. This modifies the influence of specific bits on the resulting binary string.

---

### Cryptographic Hashes (CH) vs. the MT

Cryptographic Hash functions  (CHFs) and the MT both rely on **diffusion**: small changes in the input should lead to large changes in the output.

In addition, both use bitwise operations including:

1. `^` (XOR) to flip bits conditionally without clearing state

2. `<<`, `>>` (Bit-shifts) to allow higher-order and lower-order bits to interact.

3. `&` (Bitmasks) to isolate sections of the integer or introduce assymetric bit patterns. 

However, there are three main system trade-offs: 

1. * The tempering operation in the MT is linear and invertible.
   * CHFs use non-linear step functions and compression. 

2. * The MT needs a fixed state array size. 
   * A CH accepts an arbitrary-length byte stream. 

4. * The MT relies on linear recurrences which is optimal for CPU execution loops making it useful for Monte-carlo simulations.
   * CHFs use multiple rounds of mixing to increase security. 

---

### The maths behind the `twist()` method

#### What is `matrix_a`?

The matrix $A$ is a $32 \times 32$ square matrix where the matrix values are either 0 or 1 i.e. $A \in \mathbb{F}_2^{32 \times 32}$. *This is different to `matrix_a` in the `twist()` method.* Note addition within $\mathbb{F}&#95;2$ is calculated using the bitwise XOR ($\oplus$) operation since $1&#95;{\mathbb{F}} + 1&#95;{\mathbb{F}} = 0&#95;{\mathbb{F}}$. Also, 

$$
A = \begin{pmatrix} 
0 & 1 & 0 & \cdots & 0 \\ 
0 & 0 & 1 & \cdots & 0 \\ 
\vdots & \vdots & \vdots & \ddots & \vdots \\ 
0 & 0 & 0 & \cdots & 1 \\ 
a_{31} & a_{30} & a_{29} & \cdots & a_{0} 
\end{pmatrix}
$$

If $v = (v_{31}, v_{30}, \dots, v_0)$ is a row vector then $vA = (a_{31}v_{0}, v_{31} + a_{30}v_0, \dots, v_1 + a_0v_0)$. If $v_0 = 0$ then $vA = (0, v_{31}, \dots, v_1)$ is equivalent to the bit-wise shift `x_shift = x_comb >> 1`. 

However, if $v_0 = 1$ then $vA = (a_{31}, v_{31} + a_{30}, \dots, v_1 + a_0) = (a_{31}, a_{30}, \dots, a_0) + (0, v_{31}, \dots, v_0)$ which is equivalent to `x_shift = (x_comb >> 1) ^ matrix_a`. Hence `matrix_a` is the last row vector in matrix $A$ (this might be a confusing name since `matrix_a` is a row of matrix $A$). In the final step of the `twist()` method, `x_shift` is mixed with a different state. In a traditional Generalised Feedback Shift Register (GFSR), the generator uses the following recurrence relation: 

$$
x_{i+n} = x_{i+m} \oplus (x_i \cdot A).
$$

which equivalent to `self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)`. 

However, in a GFSR $A$ can be an arbitrary, dense (contain many 1s) matrix. Multiplying a 32-bit vector ($x_i$) by a dense matrix translates into 32 distinct bitwise shift-and-add (XOR) loop iterations. Repeating this 624 times is very slow. The matrix $A$ in the MT is designed so matrix multiplication can be translated into 1 bitwise shift-and-add loop iteration which is processed by the CPU almost instantly. 

#### Why is the period of each state $2^{19937} - 1$?

First compute the characteristic polynomial $\det(A - \lambda I)$. Let $B = A - \lambda$. Using recursion, $\det(B) = \det(B_{31}) = - \lambda \det(B_{30}) - a_{31}$ where $\det(B_i)$ is the bottom right sub-matrix of $B$ of dimension $(i + 1) \times (i + 1)$. Since $-1_{\mathbb{F}} = 1_{\mathbb{F}}$, $\det(B_{31}) = \lambda \det(B_{30}) + a_{31}$ so $\det(B) = \lambda^{32} + a_0 \lambda^{31} + \dots + a_{31}$. 

However, $A$ acts locally since it acts on a vector of length 32. Consider, the "global" matrix $T$ which takes as input the 624 integers at once i.e. a vector of length $32 \times 624 = 19968$. The idea is to find the characteristic polynomial of $T$ using a similar recursion. 

$$
T = \begin{pmatrix} 
0 & I_{32} & 0 & \cdots & 0 \\ 
0 & 0 & I_{32} & \cdots & 0 \\ 
\vdots & \vdots & \vdots & \ddots & \vdots \\ 
0 & 0 & 0 & \cdots & I_{32} \\ 
B_{0} & B_{1} & B_{2} & \cdots & B_{623} 
\end{pmatrix}
$$ 

where $B_i$ is a ($32 \times 32$)-matrix for each $i$. The characteristic polynomial of $T$ is 

$$
\det(T - \lambda I) = \det \left(\lambda^{624} I + B_{623}\lambda^{623} + \dots + B_1\lambda + B_0 \right)
$$ 

where negative signs are dropped (1_{\mathbb{F}&#95;2} = -1_{\mathbb{F}&#95;2}). 

##### Linking $T$ to the `twist()` method

In order to compute the above determinant, it's useful to understand the three operations in the `twist()` method in more detail. 
 
Since each number is twisted using exactly three integers from the original state grid, only $B_0$, $B_1$ (links to step 1 in the `twist()` method) and $B_{397}$ (links to step 3 in the `twist()` method) are non-zero. Note that in a feedback system over a finite field, $\lambda$ is a time-advance operator, that is $x_{i + 1} = \lambda x_i$ where $x_i$ is the state at time $i$.

In step 1, `x_comb = (self.state[i] & upper_mask) | (self.state[(i + 1) % self.n] & lower_mask)`. Using matrices, this is equivalent to $x_i P_0 + x_{i + 1} P_1 = x_i P_0 + x_i \lambda P_1 = x_i (P_0 + \lambda P_1)$ where $P_0$ and $P_1$ are the upper and lower bit-masks. In matrix notation, 

$$
P_0 = \begin{pmatrix} 
1 & 0 & 0 & \cdots & 0 \\ 
0 & 0 & 0 & \cdots & 0 \\ 
\vdots & \vdots & \vdots & \ddots & \vdots \\ 
0 & 0 & 0 & \cdots & 0 \\ 
0 & 0 & 0 & \cdots & 0 
\end{pmatrix}
$$ 

and 

$$
P_1 = \begin{pmatrix} 
0 & 0 & 0 & \cdots & 0 \\ 
0 & 1 & 0 & \cdots & 0 \\ 
\vdots & \vdots & \vdots & \ddots & \vdots \\ 
0 & 0 & 0 & \cdots & 0 \\ 
0 & 0 & 0 & \cdots & 1 
\end{pmatrix}.
$$ 

Gllobally, $B_0 = A P_0$ represents taking the Most Significant Bit (MSB) of the current word and applying the twist matrix $A$. $B_1 = A P_1$ represents taking the Least Significant Bits (LSBs) of the next word and applying the twist matrix $A$. For ease of notation, let $B_0 + \lambda B_1 = A(P_0 + \lambda P_1) = A R(\lambda)$ then 

$$
\det(T - \lambda I) = \det(I_{32}(\lambda^{624} + \lambda^{397}) + AR(\lambda))
$$ 

and 

$$
A R(\lambda) = \begin{pmatrix}
0 & \lambda & 0 & \dots & 0 \\
0 & 0 & \lambda & \dots & 0 \\
\vdots & \vdots & \vdots & \ddots & \vdots \\
a_{31} & \lambda a_{30} & \lambda a_{29} & \dots & \lambda a_0
\end{pmatrix}
$$

In step 3, `self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)` which is equivalent to the determinant equation derived where `x_shift` is $A R(\lambda)$. `self.state[(i + m) % self.n])` is equivalent to $B_{397} = \lambda^{397} I_{32}$ since the index has moved to position `(i + m)` in `self.state`. Lastly, `self.state[i]` represents $\lambda^{624}I_{32}$. Since subtraction is equivalent to addition in $\mathbb{F}_2$, the code is a rearrangement of: 

$$
\lambda^{624} I_{32} \cdot x_i \oplus \lambda^{397} I_{32} \cdot x_i \oplus A R(\lambda) \cdot x_i = 0
$$ 

which matches with the matrix expression inside the determinant. 

##### Finding the characteristic polynomial of $T$
Now, letting $\alpha = \lambda^{624} + \lambda^{397}$, $I_{32}(\lambda^{624} + \lambda^{397}) + AR(\lambda)$ is the matrix defined as: 

$$
\begin{pmatrix}
\alpha & \lambda & 0 & 0 & \dots & 0 \\
0 & \alpha & \lambda & 0 & \dots & 0 \\
0 & 0 & \alpha & \lambda & \dots & 0 \\
\vdots & \vdots & \vdots & \vdots & \ddots & \vdots \\
0 & 0 & 0 & 0 & \dots & \lambda \\
a_{31} & \lambda a_{30} & \lambda a_{29} & \lambda a_{28} & \dots & \alpha + \lambda a_0
\end{pmatrix}.
$$ 

By using the same recursive idea as before, 

$$
\det\left(\alpha I_{32} + A R(\lambda)\right) = \alpha^{32} + \sum_{k=0}^{31} a_k \lambda^{31-k} \alpha^k.
$$ 

In $\mathbb{F}_2$, $(x + y)^2 = x^2 + xy - xy + y^2 = x^2 + y^2$, hence 

$$
\det(T - \lambda I) = \lambda^{19968} + \lambda^{12704} + \sum_{k=0}^{31} a_k \lambda^{31-k} \alpha^k.
$$ 

Finally, if it's shown the degree of the characteristic polynomial is primitive then $T$ will cycle through each of the $2^d - 1$ possible non-zero bit state configurations where $d$ is the degree of the polynomial. Note the degree in the polynomial is 19968 and not 19937. In the first step of the `twist()` method, the right 31 bits of the first integer is not used since it is immediately masked with the upper bit-mask. 

Hence, these 31 bits do not influence the system globally. Hence, the polynomial over $\mathbb{F}_2$ governing the system is $P(\lambda)$, where $\lambda^{31} P(\lambda) = \det(T - \lambda I)$. Subtracting 31 from 19968 gives the degree of the polynomial $P(\lambda)$ as 19937 (this should be familiar). 

##### Showing the characteristic polynomial is primitive

Consider the (Galoid) field $F_{2^n}$. The size of the multiplicative group is $2^n - 1$ since $0$ is not invertible. By Lagrange's or Fermat's theorem, the order of any element must be $1$ or $2^n - 1$. Since $\lambda \neq 1$, it follows $\{1, \lambda, \lambda^2, \dots, \lambda^{2^{n} - 1}\}$ are distinct for $\lambda \neq 1$. 

Remember $x_{i + 1} = \lambda x_i$ so for non-zero states, $\{x_0, \lambda x_0, \dots, \lambda^{2^{19937} - 1} x_0\}$ are the $2^{19937}$ different states each integer takes before repeating.
