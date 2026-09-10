"""Tiny calculator used by the Mergit end-to-end GitHub tests. (run 1786635973)"""


def average(numbers):
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def total(numbers):
    """Sum a sequence; used to give the agent a clean PR to merge."""
    return sum(numbers)

# Test cases to verify correctness
if __name__ == "__main__":
    print(total([1, 2, 3]))  # Should print 6
    print(total([]))         # Should print 0
    print(total([-1, -2, 3])) # Should print 0
    print(total([0, 0, 0]))  # Should print 0
    print(total([100]))      # Should print 100

def largest(numbers):
    """Return the largest number in a sequence."""
    biggest = 0
    for n in numbers:
        if n > biggest:
            biggest = n
    return biggest
