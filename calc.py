"""Tiny calculator used by the Mergit end-to-end GitHub tests."""


def average(numbers):
    # BUG: crashes with ZeroDivisionError on an empty list
    return sum(numbers) / len(numbers)


if __name__ == "__main__":
    print(average([1, 2, 3]))
