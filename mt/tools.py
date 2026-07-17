import os


class MersenneTwister:
    def __init__(self, seed_val: int=5489) -> None:
        """Initialize the generator state and seed the grid.
        """
        # size of state grid
        self.n = 624           
        self.state = [0] * self.n
        
        # force initial twist by setting to self.n
        self.pos_index = self.n
        self.state_grid(seed_val)

    def state_grid(self, seed_val: int) -> None:
        """Populate the state grid.
        """
        # fill first cell with seed value
        self.state[0] = seed_val & 0xFFFFFFFF

        # seed multiplier constant
        f = 1812433253

        # update each cell in the state grid
        for i in range(1, self.n):
            self.state[i] = (
                self.state[i - 1]
                ^ (
                    self.state[i - 1]
                     # isolate highest bits to influence lower-order bits
                    >> 30        
                )
                # cause large bit-shifts so next cells flip unpredictably
                * f
                # force next state to be non-zero if previous state is zero
                + i                   
            ) & 0xFFFFFFFF

    def twist(self) -> None:
        """Apply the twist operation to the state grid. 
        """
        # constants from video
        # middle offset distance
        m = 397

        # bottom row of matrix A (see summary.md)
        matrix_a = 0x9908B0DF
        
        # isolate the top bit
        upper_mask = 0x80000000

        # isolate the lower 31 bits
        lower_mask = 0x7FFFFFFF 

        # twisting each cell in the state grid
        for i in range(self.n):
            # combine bit fragments from current and next elements
            x_comb = (self.state[i] & upper_mask) | (
                self.state[(i + 1) % self.n] & lower_mask
            )

            x_shift = x_comb >> 1
            if x_comb & 1:
                x_shift = (x_comb >> 1) ^ matrix_a

            # combine with the offset middle cell
            self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)

        # reset pos_index to calcualate new state grid
        self.pos_index = 0

    def extract_number(self) -> int:
        """Extract a single integer from the twisted state grid and apply bitwise 
           tempering masks.

        Returns:
            int: A pseudo-random number. 
        """
        # refill all state grid if pos_index reaches end
        if self.pos_index >= self.n:
            self.twist()

        raw_num = self.state[self.pos_index]

        # apply bitwise mixing operations to increase randomness
        # mix unchanged high bits into low bits
        y = raw_num ^ (raw_num >> 11)
        y = y ^ ((y << 7) & 0x9D2C5680)
        y = y ^ ((y << 15) & 0xEFC60000)
        y = y ^ (y >> 18)

        # extracting next element for next random number
        self.pos_index += 1

        return y


class Random:
    def __init__(self, a: int, b: int, rand_nums: int, seed_val: int = 5489) -> None:
        """Initialise parameters to generate random numbers in the interval [a, b]. 

        Scales outputs from the interval [0, 1] into [a, b] using (val * (b - a)) + a.

        Args:
            a (int): lower bound of the interval.
            b (int): upper bound of the interval.
            rand_nums (int): number of random variables to return.
            seed_val (int): defaults to 5489. 
        """
        self.a = a
        self.b = b
        self.rand_nums = rand_nums
        self.seed_val = seed_val
        self.mt = MersenneTwister(self.seed_val)

        # Burn-in: discard 10_000 numbers generated. 
        for _ in range(10_000):
            self.mt.extract_number()

    def gen_nums(self, size=None) -> list[float]:
        """Generate list of random floating-point values.

        Returns:
            list[float]: random floating-values in the interval [a, b]. 
        """
        count = size if size is not None else self.rand_nums
        
        # Convert 32-bit container spaces into [0, 1] float range, then map to [a, b].
        list_nums = [
            (self.mt.extract_number() / 2**32) * (self.b - self.a) + self.a
            for _ in range(count)
        ]

        return list_nums
