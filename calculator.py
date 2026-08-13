"""Tiny calculator used by the Mergit end-to-end GitHub tests. (run 1786635973)"""


def average(numbers):
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def total(numbers):
    """Sum a sequence; used to give the agent a clean PR to merge."""
    return sum(numbers)


def product(numbers):
    """Calculate the product of a sequence; returns 0 for empty sequences."""
    if not numbers:
        return 0
    result = 1
    for num in numbers:
        result *= num
    return result


if __name__ == "__main__":
    print(average([1, 2, 3]))
    print(average([]))
