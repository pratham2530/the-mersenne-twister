# A mathematical summary of the mersenne twister

# The Mersenne Twister
Python implemented the Mersenne Twister algorithm in C to create the `random()` function. The standard implementation of the algorithm used is **MT19937**, which has a 32-bit word length. **MT** stands for Mersenne Twister and **19937** represents $2^{19937} - 1$ which is a Mersenne Prime and the period of the generator. 

The following implementation details are derived from the following video: [The Most Popular Pseudo-Random Number Generator - The Mersenne-Twister](https://www.youtube.com/watch?v=TF4PLUcJO5w).

---

### Overview of the algorithm
MT19937 works by maintaining an array of 624 32-bit unsigned integers called a state grid. A seed value is used to fill the state grid sequentially.

There are three main phases: 
1. **Initialisation (`state_grid`):** the state grid is filled using a linear recurrence relation. Bitwise operations are used to mix bits to ensure any single bit has an influence on other bits. For example, leftward bit shifts help small changes in the initial seed value to have a large changes in higher-order bits. 

    Using bit shits and XOR operations, information is redistributed across upper and lower bits helping to generate more uniformly random integers. Also, a multiplier constant helps to make small seed values larger and make the system more random; in information theory, this is called increasing entropy. 

2. **Twisting (`twist`):** once the state grid is filled, the generator runs a twist on all the numbers. 

    It iterates through the entire state array, combining the upper bits of one element with the lower bits of the next, multiplying by a specific transition matrix (Matrix $A$), and XORing it with an offset element ($i + 397$). 
    
    This helps to increase the influence of different bits on the whole 32-bit integer.

3. **Tempering and extraction (`extract_number`):** When a user requests a random number, the integer at the current index is extracted. 

    To ensure it passes empirical tests for true uniform randomness, the value is subjected to four bitwise tempering operations (using bitwise shifts `<<`, `>>`, bitwise AND `&` masks, and bitwise XOR `^`). 
    
    Tempering breaks up small linear correlations between the numbers remaining after twisting. After this, the random 32-bit integer can be returned.

---

## Class: MersenneTwister

### The state space
The state grid is an array of 624 individual 32-bit cells. By running the `state_grid()` method, the seed populates the grid. These values are used in the `twist()` and `extract_number()` methods later in the algorithm.

#### Q: Why does the state have size 624?
Since for a state of $k$ bits the absolute maximum number of unique states that can be cycled through before repeating is $2^k - 1$, the state must hold $19937$ bits of data. This follows from summing the geometric series:

$$1 + 2 + \dots + 2^{k - 1} = 2^k - 1$$

where $2^i$ represents the number of binary sequences of length $i$.

To store this data in an array of 32-bit integers, $\lceil 19937 / 32 \rceil = 624$ integers are needed.

#### Q: What does pos_index do?
When a number is extracted, `pos_index` is incremented by one so that a new random number is generated next time. `pos_index` refers to the index slot in the `self.state` array. When `pos_index` reaches 624, `twist()` is called to overwrite all 624 cells.

---

### Method Reference: `state_grid()`
Populate the state grid using `seed_val`.

#### Q: Where does the seeding multiplier come from?
This initialising step relies on a Linear Congruential Generator (LCG). The formula used mathematically is:

$$X_i = f \cdot (X_{i - 1} \oplus (X_{i - 1} \gg 30)) + i \pmod{2^{32}}$$

*(where $\oplus$ is the bitwise XOR).*

If a "bad" multiplier is chosen, the 624 numbers generated can appear related. Donald Knuth proved that the chosen multiplier can generate numbers which are spread out uniformly across the 32-bit space by passing the spectral test.

Intuitively, when the 624 numbers are plotted as multi-dimensional coordinates, there are no evident geometric correlations such as a straight line.

---

### Method Reference: `twist()`
'Twists' the entire state grid of 624 numbers into a new grid. This method simulates a Linear Feedback Shift Register (LFSR) optimised to run on 32-bit words. *(See the end of the document for a detailed explanation of the mathematics behind the algorithm).*

#### Q: How does a LFSR usually work?
A LFSR is a shift register whose input bit is a linear function of its previous state. For example, using the linear function XOR:
1. **Register:** A sequence of bits ($[b_n, b_{n - 1}, \dots, b_1, b_0]$).

2. **Taps:** Specific positions in the register.

3. Bits are shifted right by 1 and the empty slot is filled by XORing the tapped bits.

Since there are $2^n - 1$ non-zero states, the register will eventually repeat. If the taps are chosen using a primitive polynomial, the LFSR will achieve its maximum period of $2^n - 1$ before repeating.

#### Q: How does `twist()` generalise a LFSR?
In order to ensure each individual cell does not act as an isolated generator, local and global boundary crossings are needed.

1. Slicing and concatenating adjacent words ensures information is coupled along the array boundaries.

2. The conditional XOR with `matrix_a` represents multiplying a specialised transition matrix over $\mathbb{F}_2$. *(See the end of the file for a detailed explanation).* This step ensures the period of the generator remains the large Mersenne prime $2^{19937} - 1$.

3. Mixing with a distant cell (397 positions away) ensures local patterns are erased, helping the algorithm pass the spectral test.

---

### Method Reference: `extract_number()`
Extract the raw number from the current index, run it through 4 tempering operations, and increment the pointer.

Tempering is the process of using binary operations such as bit-shifts (`<<`, `>>`), bitmasks (`&`), and XOR (`^`) to add further randomness.

After twisting, each of the 624 numbers has a large period length and appears random over a long timeframe, but they possess small linear correlations. To ensure the numbers pass tests for true uniform randomness, they need to be tempered.

Intuitively:
1. `<<` and `>>` allow higher-order and lower-order bits to interact.

2. `&` isolates sections of binary sequences.

3. `^` is used to apply the above operations to the previous state.

Since $0 = 0 \oplus 0$ and $1 = 1 \oplus 0$, specific bits can be first shifted or isolated and then mixed with the unmoved bits while keeping those specific bits unchanged. This modifies the influence of specific bits on the resulting binary string.

---

## Class: Random

### Method Reference: `gen_nums()`
If random numbers between 0 and 1 can be generated, then to generate random numbers in the interval $[a, b]$, multiply each random number generated by $(b - a)$ and add $a$.

---

## Function: main()
### Using a fixed seed value
Assuming the interval and number of random numbers to return is fixed, if the seed value is also fixed the algorithm will return the same numbers if run again. This is helpful when generating data using random numbers and analysing the data since if another person were to run the simulation with a set seed value, the computations in the analysis will arrive to the same answer. 

### Generating a dynamic seed 
#### Q: What is the OS kernel and how does it generate random numbers?
The kernel makes decisions in the Operating System (OS) and is the first program to run when a computer is turned on. Applications make system calls to interact with the hardware through the kernel.

The kernel keeps a running "entropy pool," which is a buffer in memory filled with hardware noise (e.g., exact timings of keyboard clicks). The raw hardware noise is passed through a cryptographic hash function which ensures each bit has an equal chance of being a 0 or a 1.

The kernel uses the entropy pool to seed an internal generator (e.g., on Windows it is BCrypt). The number of bytes specified is sliced off the generated binary stream.

---

### Cryptographic hashes vs. the mersenne twister

Cryptographic hash functions and the Mersenne Twister algorithm both rely on **diffusion**: small changes in the input should lead to large changes in the output.

In addition, both use binary operations including:

1. `^` (XOR) to flip bits conditionally.

2. `<<`, `>>` (Bit-shifts) to allow higher-order and lower-order bits to interact.

3. `&` (Bitmasks) to isolate sections of binary sequences.

4. Hexadecimal constants (e.g., multipliers) to increase chaos.

However, there are three main differences:

1. Operations in the Mersenne Twister are linear and invertible, while operations in cryptographic hash functions are non-linear; thus, information is lost.

2. The Mersenne Twister needs a fixed array size (624 in this implementation), while a hash function compresses an input of any size into a fixed, small output.

3. Cryptographic hash functions run data through multiple rounds of mixing and are therefore slower than Pseudo-Random Number Generators (PRNGs).

---

### The mathematics behind the `twist()` method

#### What is `matrix_a`?

The matrix $A$ is a $32 \times 32$ square matrix where the matrix values are either 0 or 1, i.e. $A \in \mathbb{F}_2^{32 \times 32}$. This is different to `matrix_a` in the `twist()` method. 

Addition within $\mathbb{F}&#95;2$ is calculated using the bitwise XOR ($\oplus$) operation since $1&#95;{\mathbb{F}} + 1&#95;{\mathbb{F}} = 0&#95;{\mathbb{F}}$.

$A$ is the following matrix: 

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

However, if $v_0 = 1$ then $vA = (a_{31}, v_{31} + a_{30}, \dots, v_1 + a_0) = (a_{31}, a_{30}, \dots, a_0) + (0, v_{31}, \dots, v_0)$ which is equivalent to `x_shift = (x_comb >> 1) ^ matrix_a`. Hence `matrix_a` is the last row vector in matrix $A$ (while this is a mathematically confusing name, I wanted to reference to matrix $A$). 

In the final step of the `twist()` method, `x_shift` is mixed with a different state. In a traditional Generalised Feedback Shift Register (GFSR), the generator uses the following recurrence relation: 

$$
x_{i+n} = x_{i+m} \oplus (x_i \cdot A).
$$

This is equivalent to `self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)`. 

However, in a GFSR $A$ can be an arbitrary, dense (contain many 1s) matrix. Multiplying a 32-bit vector ($x_i$) by a dense matrix translates into 32 distinct bitwise shift-and-add (XOR) loop iterations. Repeating this 624 times is very slow. 

The matrix $A$ in the Mersenne Twister is designed so matrix multiplication can be translated into 1 bitwise shift-and-add loop iteration which is processed by the CPU almost instantly. 

#### Why is the period of each state $2^{19937} - 1$?

Computing the characteristic polynomial $\det(A - \lambda I)$ leads to why the period of each state is $2^{19937} - 1$. Let $B = A - \lambda$. 

Then using recursion, $\det(B) = \det(B_{31}) = - \lambda \det(B_{30}) - a_{31}$ where $\det(B_i)$ is the bottom right sub-matrix of $B$ of dimension $(i + 1) \times (i + 1)$. Since $-1_{\mathbb{F}} = 1_{\mathbb{F}}$, $\det(B_{31}) = \lambda \det(B_{30}) + a_{31}$ so $\det(B) = \lambda^{32} + a_0 \lambda^{31} + \dots + a_{31}$. 

However, $A$ acts locally since it acts on a vector of length 32. Consider, the "global" matrix $T$ which takes as input the 624 integers at once i.e. a vector of length $32 \times 624 = 19968$. 

Then $T$ is the following matrix: 

$$
T = \begin{pmatrix} 
0 & I_{32} & 0 & \cdots & 0 \\ 
0 & 0 & I_{32} & \cdots & 0 \\ 
\vdots & \vdots & \vdots & \ddots & \vdots \\ 
0 & 0 & 0 & \cdots & I_{32} \\ 
B_{0} & B_{1} & B_{2} & \cdots & B_{623} 
\end{pmatrix}
$$ 

where $B_i$ is a ($32 \times 32$)-matrix for each $i$. By using a similar recursion when computing the characteristic polynomial of $A$, the characteristic polynomial of $T$ is 

$$
\det(T - \lambda I) = \det \left(\lambda^{624} I + B_{623}\lambda^{623} + \dots + B_1\lambda + B_0 \right)
$$ 

where negative signs are dropped. 

##### Linking $T$ to the `twist()` method

Since each number is twisted using exactly three integers from the original state grid, only $B_0$, $B_1$ (links to step 1 in the `twist()` method) and $B_{397}$ (links to step 3 in the `twist()` method) are non-zero. 

It helps to understand what $\lambda$ represents in the system. In a feedback system over a finite field, $\lambda$ is a time-advance operator, that is $x_{i + 1} = \lambda x_i$ where $x_i$ is the state at time $i$.  

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

Now globally, $B_0 = A P_0$ represents taking the Most Significant Bit (MSB) of the current word and applying the twist matrix $A$. 

$B_1 = A P_1$ represents taking the Least Significant Bits (LSBs) of the next word and applying the twist matrix $A$. 

For ease of notation, let $B_0 + \lambda B_1 = A(P_0 + \lambda P_1) = A R(\lambda)$ then 

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

In step 3, `self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)` which is equivalent to the determinant equation derived where `x_shift` is $A R(\lambda)$. `self.state[(i + m) % self.n])` is equivalent to $B_{397} = \lambda^{397} I_{32}$ since the index has moved to position `(i + m)` in `self.state`. 

Lastly, `self.state[i]` represents $\lambda^{624}I_{32}$. Since subtraction is equivalent to addition in $\mathbb{F}_2$, the code is a rearrangement of: 

$$
\lambda^{624} I_{32} \cdot x_i \oplus \lambda^{397} I_{32} \cdot x_i \oplus A R(\lambda) \cdot x_i = 0.
$$ 

This matches with the matrix expression inside the determinant. 

##### Finding the characteristic polynomial of $T$
It's time to compute the determinant at last. Now, letting $\alpha = \lambda^{624} + \lambda^{397}$, $I_{32}(\lambda^{624} + \lambda^{397}) + AR(\lambda)$ is the following matrix: 

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

Finally, if it's shown the degree of the characteristic polynomial is primitive, then $T$ will cycle through each of the $2^d - 1$ possible non-zero bit state configurations where $d$ is the degree of the polynomial. 

Note the degree in the polynomial is 19968 and not 19937. In the first step of the `twist()` method, the right 31 bits of the first integer is not used since it is immediately masked with the upper bit-mask. 

Hence, these 31 bits do not influence the global system. Mathematically, this is equivalent to a 31-dimensional null space. In this context, the polynomial over $\mathbb{F}_2$ governing the system is $P(\lambda)$, where $\lambda^{31} P(\lambda) = \det(T - \lambda I)$. Subtracting 31 from 19968 gives the degree of the polynomial $P(\lambda)$ as 19937 which is known to be a Mersenne prime. 

##### Showing the characteristic polynomial is primitive

Consider the (Galois) field $F_{2^n}$. The size of the multiplicative group is $2^n - 1$ since $0$ is not invertible. By Lagrange's or Fermat's theorem, the order of any element must be $1$ or $2^n - 1$. Since $\lambda \neq 1$, it follows $\{1, \lambda, \lambda^2, \dots, \lambda^{2^{n} - 1}\}$ are distinct for $\lambda \neq 1$. 

Remember $x_{i + 1} = \lambda x_i$ so for non-zero states, $\{x_0, \lambda x_0, \dots, \lambda^{2^{19937} - 1} x_0\}$ are the $2^{19937}$ different states each integer takes before repeating.
