"""Module providing an implementation of the MT19937 Mersenne Twister.

This module contains the underlying MersenneTwister PRNG and a helper Random class 
which outputs an arbitrary number of numbers in an interval. 

Use the summary in the repository to help understand each method properly. 
"""

import os


class MersenneTwister:

    def __init__(self, seed_val: int = 5489) -> None:
        """Initialize the generator state and seed the grid.

        Args:
            seed_val (int): The initial value used to seed the state_grid. 
                Defaults to 5489.
        """
        # The size of the state grid.
        self.n = 624
        self.state = [0] * self.n

        # Track position inside the 624-cell grid (forces initial twist).
        self.pos_index = self.n
        self.state_grid(seed_val)

    def state_grid(self, seed_val: int) -> None:
        """Populate the state grid using a Knuth multiplier.

        Args:
            seed_val (int): The initial value used to seed the state_grid. 
        """
        # Fill first cell with the seed value as a 32-bit integer.
        self.state[0] = seed_val & 0xFFFFFFFF

        # Seed multiplier constant.
        f = 1812433253

        # Updating each cell in the state grid.
        for i in range(1, self.n):
            self.state[i] = (
                self.state[i - 1]
                ^ (
                    self.state[i - 1]
                    >> 30  # Isolate highest bits to influence lower-order bits.
                )
                * f  # Cause large bit-shifts so next cells flip unpredictably.
                + i  # Forces next state to be non-zero if previous state is zero.
            ) & 0xFFFFFFFF

    def twist(self) -> None:
        """Apply the twist operation to the state grid. 

        See the summary for a detailed explanation. 
        """
        # Constants from the video.
        m = 397  # Middle offset distance
        matrix_a = 0x9908B0DF
        upper_mask = 0x80000000  # Isolates the top, 32nd, bit.
        lower_mask = 0x7FFFFFFF  # Isolates the lower 31 bits.

        # 'Twisting' each cell in the state grid.
        for i in range(self.n):
            # Combine bit fragments from current and next elements.
            x_comb = (self.state[i] & upper_mask) | (
                self.state[(i + 1) % self.n] & lower_mask
            )

            # Shift right and conditionally XOR with matrix_a if odd.
            x_shift = x_comb >> 1
            if x_comb & 1:
                x_shift = (x_comb >> 1) ^ matrix_a

            # Combine with the offset middle cell.
            self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)

        # Reset pos_index to 0 since we need to calculate a new state grid.
        self.pos_index = 0

    def extract_number(self) -> int:
        """Extract a single integer from the twisted state grid and apply bitwise 
           tempering masks.

        Returns:
            int: A pseudo-random number. 
        """
        # Refill all 624 cells when pos_index reaches the end of the array.
        if self.pos_index >= self.n:
            self.twist()

        # Select a twisted number from the state grid.
        raw_num = self.state[self.pos_index]

        # TEMPERING: Apply four bitwise mixing operations to increase randomness.
        y = raw_num ^ (raw_num >> 11)  # Mix unchanged high bits into low bits.
        y = y ^ ((y << 7) & 0x9D2C5680)
        y = y ^ ((y << 15) & 0xEFC60000)
        y = y ^ (y >> 18)

        # Move index to the next grid element for subsequent call.
        self.pos_index += 1

        return y


class Random:

    def __init__(self, a: int, b: int, rand_nums: int, seed_val: int = 5489) -> None:
        """Initialize parameters to generate random numbers in the interval [a, b]. 

        Transforms outputs from the interval [0, 1] up into [a, b]
        using the scaling (val * (b - a)) + a.

        Args:
            a (int): Lower bound of the interval.
            b (int): Upper bound of the interval.
            rand_nums (int): Total number of random variables to return.
            seed_val (int): Seed value of the Mersenne Twister engine.
                Defaults to 5489.
        """
        self.a = a
        self.b = b
        self.rand_nums = rand_nums
        self.seed_val = seed_val

    def gen_nums(self) -> list[float]:
        """Generate a list of random floating-point values.

        Returns:
            list[float]: A list of size `rand_nums` of random floating-values in the
            interval [a, b]. 
        """
        mt = MersenneTwister(self.seed_val)
        mt.twist()

        # Map 32-bit integers into the interval [0, 1] and then apply the scaling.
        list_nums = [
            (mt.extract_number() / (2**32 - 1)) * (self.b - self.a) + self.a
            for _ in range(self.rand_nums)
        ]

        return list_nums


def main() -> None:
    """Run a sample using a dynamic seed."""
    # Read 4 random bytes and convert them into an unsigned integer.
    dynamic_seed = int.from_bytes(os.urandom(4), byteorder="big")

    nums = Random(a=0, b=3, rand_nums=4, seed_val=dynamic_seed).gen_nums()
    print(*nums)


if __name__ == "__main__":
    main()
