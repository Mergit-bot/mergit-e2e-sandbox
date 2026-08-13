"""Tiny calculator used by the Mergit end-to-end GitHub tests. (run 1786635973)"""


def average(numbers):
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


if __name__ == "__main__":
    print(average([1, 2, 3]))
    print(average([]))

def total(numbers):
    """Sum a sequence; used to give the agent a clean PR to merge."""
    return sum(numbers)

def product(numbers):
    """Multiply a sequence; exists only to give the red-CI PR a change."""
    out = 1
    for n in numbers:
        out *= n
    return out
