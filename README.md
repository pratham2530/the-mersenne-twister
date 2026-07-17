# The Mersenne Twister (MT)

A python implementation of the **MT19937** PRNG used in Python's built-in `random` module with a `Random` helper class for sampling numbers from an arbitrary interval `[a, b]`.

### UPDATE: 

*17/07/2026*: 
- Added a burn-in after instantiating the PRNG in Random to improve sample randomness. 
- Moved instantiation from `gen_nums()` to `__init__()` to improve both running and statistical performance by ensuring the current state changes.
- Remove `twist()` in `gen_nums()` to ensure only `extract_number()` twists a new state-grid. 

## Why this exists

I wanted to know how Python generates random numbers. In addition, this projcet contains a full write-up, [`summary.md`](./summary.md) covering *why* each step exists, the the linear algebra behind the `twist()` step and a derivation of the generator's period of $2^{19937} - 1$.

## Features

- Full MT19937 implementation (seeding, twisting and tempering a 624-word state grid)
- `Random` helper class for generating `n` uniform floats in the interval `[a, b]`
- Supports both a fixed default seed and a dynamically generated seed
- Summary of the main concepts and maths behind the algorithm

## Installation

No dependencies beyond the Python standard library.

```bash
git clone https://github.com/pratham2530/mersenne-twister.git
cd mersenne-twister
```

## Usage

```python
from tools import Random

# defualt seed 
nums = Random(a=0, b=3, rand_nums=4).gen_nums()
print(nums)

# custom seed
nums = Random(a=0, b=10, rand_nums=5, seed_val=42).gen_nums()
print(nums)
```

Use the `MersenneTwister` class directly for raw 32-bit integers: 

```python
from tools import MersenneTwister

mt = MersenneTwister(seed_val=5489)
mt.twist()
raw_ints = [mt.extract_number() for _ in range(5)]
```

### Running the demo

```bash
python main.py
```

## How it works

MT19937 generates numbers in three phases:

1. **Initialization** (`state_grid`) - seeds a 624-element array of 32-bit integers using a linear recurrence relation.
2. **Twisting** (`twist`) - mixes the entire state grid using a linear feedback shift register-style transformation which runs every 624 numbers generated.
3. **Tempering** (`extract_number`) - applies bitwise shifts, masks, and XORs to each output to remove residual linear correlations before returning it.

For the full explanation see [`summary.md`](./summary.md).

## Project structure

```
.
├── main.py       # demo script
├── tools.py      # MersenneTwister and Random classes
└── summary.md    # algorithm walkthrough and mathematical background
```
