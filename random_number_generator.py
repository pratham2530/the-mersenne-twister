"""Module providing a class-based implementation of the MT19937 Mersenne Twister.

This module contains the underlying MersenneTwister pseudo-random number generator
and a helper Random class to transform raw outputs into bounded continuous intervals.
"""

import os


class MersenneTwister:
    """A 32-bit Mersenne Twister pseudo-random number generator (MT19937)."""

    def __init__(self, seed_val: int = 5489) -> None:
        """Initialize the generator state and seed the grid.

        Args:
            seed_val (int): The initial value used to kickstart the state grid.
                Defaults to 5489.
        """
        # The size of the state grid.
        self.n = 624
        self.state = [0] * self.n

        # Track position inside the 624-cell grid (forces initial twist).
        self.pos_index = self.n
        self.state_grid(seed_val)

    def state_grid(self, seed_val: int) -> None:
        """Populate the internal 624-cell state grid using a Knuth multiplier.

        Isolates bit positions and distributes entropy bi-directionally
        between high and low-order bits across the state array.

        Args:
            seed_val (int): Initial integer seed value to generate state sequence from.
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
        """Apply the twist recurrence operation to refresh the internal state grid matrix.

        This method updates the entire array by combining fragments of adjacent words and
        applying linear feedback transformations.
        """
        # Constants from the video.
        m = 397  # Middle offset distance
        matrix_a = 0x9908B0DF
        upper_mask = 0x80000000  # Isolates the top, 32nd, bit.
        lower_mask = 0x7FFFFFFF  # Isolates the lower 31 bits.

        # 'Twisting' each cell in the state grid.
        for i in range(self.n):
            # STEP 1: Combine bit fragments from current and next elements.
            x_comb = (self.state[i] & upper_mask) | (
                self.state[(i + 1) % self.n] & lower_mask
            )

            # STEP 2: Shift right and conditionally XOR with matrix_a if odd.
            x_shift = x_comb >> 1
            if x_comb & 1:
                x_shift = (x_comb >> 1) ^ matrix_a

            # STEP 3: Combine with the offset middle cell.
            self.state[i] = (self.state[(i + m) % self.n]) ^ (x_shift)

        # Reset pos_index to 0 since we need to calculate a new state grid.
        self.pos_index = 0

    def extract_number(self) -> int:
        """Extract a single 32-bit unsigned integer and apply bitwise tempering masks.

        Returns:
            int: A tempered, highly distributed 32-bit unsigned pseudo-random integer.
        """
        # Refill/overwrite all 624 cells when the state boundary is reached.
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
    """Wrapper class providing structural transformations for random distribution bounding."""

    def __init__(self, a: int, b: int, rand_nums: int, seed_val: int = 5489) -> None:
        """Initialize parameters and scaling properties for generating random numbers in
        [a, b].

        Transforms outputs from the baseline range [0, 1] up into [a, b]
        using linear scaling: (val * (b - a)) + a.

        Args:
            a (int): Lower bound of the output distribution interval.
            b (int): Upper bound of the output distribution interval.
            rand_nums (int): Total count of random variables to extract.
            seed_val (int): Seed number transferred to the Mersenne Twister engine.
                Defaults to 5489.
        """
        self.a = a
        self.b = b
        self.rand_nums = rand_nums
        self.seed_val = seed_val

    def gen_nums(self) -> list[float]:
        """Generate a list of random floating-point values.

        Returns:
            list[float]: A list of size `rand_nums` containing bounded floating-point
                values distributed within the configured continuous interval [a, b].
        """
        mt = MersenneTwister(self.seed_val)
        mt.twist()

        # Convert 32-bit container spaces into [0, 1] float range, then map to [a, b].
        list_nums = [
            (mt.extract_number() / (2**32 - 1)) * (self.b - self.a) + self.a
            for _ in range(self.rand_nums)
        ]

        return list_nums


def main() -> None:
    """Run a sample using a cryptographic entropy seed."""
    # Read 4 random bytes and convert them into an unsigned integer.
    dynamic_seed = int.from_bytes(os.urandom(4), byteorder="big")

    nums = Random(a=0, b=3, rand_nums=4, seed_val=dynamic_seed).gen_nums()
    print(*nums)


if __name__ == "__main__":
    main()
