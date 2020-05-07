import timeit

import numpy as np

if __name__ == "__main__":

    SIZE = 1000000
    RUNS = 100

    # Using sets
    x_set = set([x for x in range(SIZE)])

    x_nums = [x for x in range(SIZE)]

    def compare_to_set():
        assert set(x_nums) == x_set

    t1 = timeit.timeit(compare_to_set, number=RUNS)
    print(f"PYTHON - Size: {SIZE} took: {t1 / RUNS} seconds on average")

    x_np_array = np.array([x for x in range(SIZE)], dtype=np.float64)
    y_np_array = np.array([x for x in range(SIZE)], dtype=np.float64)

    t2 = timeit.timeit(lambda: np.array_equal(x_np_array, y_np_array), number=RUNS)
    print(f"NUMPY - Size: {SIZE} took: {t2 / RUNS} seconds on average")