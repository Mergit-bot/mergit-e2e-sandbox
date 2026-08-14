def spread(numbers):
    """Return the difference between the largest and smallest value."""
    if len(numbers) == 0:
        return 0
    return max(numbers) - min(numbers)