from tools import Random


def main():
    """Run two samples: using default fixed seed and dynamic seed values
       to generate 4 numbers in interval [0, 3]."""
    # using default seed value
    nums = Random(a=0, b=3, rand_nums=4)
    print(*nums)

    # using dynamic seed value 
    dynamic_seed = int.from_bytes(os.urandom(4), byteorder="big")

    nums2 = Random(a=0, b=3, rand_nums=4, seed_val=dynamic_seed).gen_nums()
    print(*nums2)


if __name__ == "__main__":
    main()
