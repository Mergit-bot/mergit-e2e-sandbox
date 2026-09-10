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
    biggest = numbers[0]
    for n in numbers:
        if n > biggest:
            biggest = n
    return biggest

if __name__ == "__main__":
    print(average([1, 2, 3]))
    print(average([]))
    print(largest([-5, -2, -9]))  # Should print -2
    print(largest([1, 2, 3]))     # Should print 3
    print(largest([]))            # Should print 0
