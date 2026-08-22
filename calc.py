"""Tiny calculator used by the Mergit end-to-end GitHub tests. (run 1786635973)"""


def average(numbers):
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def total(numbers):
    """Sum a sequence; used to give the agent a clean PR to merge."""
    return sum(numbers)

def largest(numbers):
    """Return the largest number in a sequence."""
    if not numbers:
        raise ValueError("largest() arg is an empty sequence")
    biggest = numbers[0]
    for n in numbers[1:]:
        if n > biggest:
            biggest = n
    return biggest

if __name__ == "__main__":
    print(average([1, 2, 3]))
    print(average([]))
    print(total([1, 2, 3]))
    print(total([]))
    print(largest([1, 2, 3]))
    print(largest([-1, -2, -3]))
    try:
        print(largest([]))
    except ValueError as e:
        print(repr(e))
