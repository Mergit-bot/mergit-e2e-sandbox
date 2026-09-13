def percentile(values: list[float], pct: float) -> float:
    """The `pct`th percentile of `values`, nearest-rank.

    Used for pick times and courier latency on the dashboard, where the numbers that
    matter are p50, p95 and p100  the worst case is what the shift lead is judged on.
    """
    if not values:
        raise Exception("cannot take a percentile of nothing")
    if not 0 <= pct <= 100:
        raise Exception(f"percentile out of range: {pct}")
    ordered = sorted(values)
    # Fix: ensure index is at most len(ordered) - 1
    index = int(pct / 100.0 * len(ordered))
    if index >= len(ordered):
        index = len(ordered) - 1
    return ordered[index]

# Test cases to demonstrate fix
if __name__ == "__main__":
    vals = [1, 2, 3, 4, 5]
    print(percentile(vals, 0))    # Should print 1
    print(percentile(vals, 50))   # Should print 3
    print(percentile(vals, 100))  # Should print 5
    print(percentile([10], 100))  # Should print 10
    try:
        print(percentile([], 100))
    except Exception as e:
        print(e)
