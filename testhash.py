import random
import string
import time
import statistics
from hashmap import *   


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def make_random_ints(n, low=0, high=10**9):
    return [random.randint(low, high) for _ in range(n)]

def make_random_strings(n, length=10):
    letters = string.ascii_letters + string.digits
    out = []
    for _ in range(n):
        out.append("".join(random.choice(letters) for _ in range(length)))
    return out

def make_adversarial_same_hash_strings(n):
    """
    Create a list of objects that *force* collisions by having the same hash.
    These are custom objects, not just strings.
    """
    class BadKey:
        __slots__ = ("value",)

        def __init__(self, value):
            self.value = value

        def __hash__(self):
            return 42

        def __eq__(self, other):
            if not isinstance(other, BadKey):
                return False
            return self.value == other.value

        def __repr__(self):
            return f"BadKey({self.value})"

    return [BadKey(i) for i in range(n)]

def build_sample_datasets():
    datasets = {
        "ints_1k": make_random_ints(1000),
        "ints_10k": make_random_ints(10_000),
        "ints_100k": make_random_ints(100_000),
        "str_1k": make_random_strings(1000, length=12),
        "str_10k": make_random_strings(10_000, length=12),
    }
    return datasets


def time_operation(fn, repeats=1):
    """
    Time a function fn() that takes no arguments.
    Returns elapsed time in seconds.
    """
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        end = time.perf_counter()
        best = min(best, end - start)
    return best

#  LOAD FACTOR IMPACT
def experiment_load_factor(dataset, label="dataset"):
    """
    Insert prefixes of the dataset into a dict and measure:
      - total insertion time
      - average time per insert
    """
    print_section(f"EXPERIMENT 1: LOAD FACTOR IMPACT ({label})")

    n = len(dataset)
    dict_sizes = [int(n * frac) for frac in [0.1, 0.25, 0.5, 0.75, 1.0]]

    print("size,total_insert_time_s,avg_time_per_insert_us")

    for size in dict_sizes:
        keys = dataset[:size]
        d = {}

        def insert_all():
            for k in keys:
                d[k] = 1

        elapsed = time_operation(insert_all)
        avg_per_insert = (elapsed / size) * 1e6  # microseconds

        print(f"{size},{elapsed:.6f},{avg_per_insert:.3f}")

#  COLLISION FREQUENCY
def compute_bucket_stats(keys, num_buckets=1024, hash_func=hash):
    """
    Manually map keys into buckets using hash(key) % num_buckets
    and compute collision statistics.
    """
    buckets = [0] * num_buckets
    for k in keys:
        h = hash_func(k)
        idx = h % num_buckets
        buckets[idx] += 1

    used_buckets = sum(1 for b in buckets if b > 0)
    max_bucket = max(buckets)
    if used_buckets > 0:
        avg_load = sum(buckets) / used_buckets
    else:
        avg_load = 0.0

    non_empty = [b for b in buckets if b > 0]
    if len(non_empty) > 1:
        variance = statistics.pvariance(non_empty)
    else:
        variance = 0.0

    return {
        "num_buckets": num_buckets,
        "num_keys": len(keys),
        "used_buckets": used_buckets,
        "max_bucket_size": max_bucket,
        "avg_load_non_empty": avg_load,
        "variance_non_empty": variance,
    }

def experiment_collision_frequency():
    """
    Compare bucket distribution of:
      - random strings (good-ish distribution)
      - adversarial BadKey objects that all share the same hash (tons of collisions)
    """
    print_section("EXPERIMENT 2: COLLISION FREQUENCY")

    keys_good = make_random_strings(10_000, length=16)
    keys_bad = make_adversarial_same_hash_strings(10_000)

    stats_good = compute_bucket_stats(keys_good, num_buckets=1024)
    stats_bad = compute_bucket_stats(keys_bad, num_buckets=1024)

    print("Case, num_keys, num_buckets, used_buckets, max_bucket_size, avg_load_non_empty, variance_non_empty")
    print(f"good,{stats_good['num_keys']},{stats_good['num_buckets']},"
          f"{stats_good['used_buckets']},{stats_good['max_bucket_size']},"
          f"{stats_good['avg_load_non_empty']:.2f},{stats_good['variance_non_empty']:.2f}")
    print(f"bad,{stats_bad['num_keys']},{stats_bad['num_buckets']},"
          f"{stats_bad['used_buckets']},{stats_bad['max_bucket_size']},"
          f"{stats_bad['avg_load_non_empty']:.2f},{stats_bad['variance_non_empty']:.2f}")


#  HASH FUNCTION QUALITY
def bad_string_hash(s):
    """
    Stupid hash: only uses first character.
    This simulates a poor hash function that causes clustering.
    """
    if not s:
        return 0
    return ord(s[0])

def experiment_hash_function_quality():
    """
    Compare distribution of Python's built-in hash vs a poor custom hash
    on the same set of random strings.
    """
    print_section("EXPERIMENT 3: HASH FUNCTION QUALITY")

    keys = make_random_strings(10_000, length=16)

    stats_builtin = compute_bucket_stats(keys, num_buckets=1024, hash_func=hash)
    stats_bad = compute_bucket_stats(keys, num_buckets=1024, hash_func=bad_string_hash)

    print("HashType, num_keys, num_buckets, used_buckets, max_bucket_size, avg_load_non_empty, variance_non_empty")
    print(f"builtin,{stats_builtin['num_keys']},{stats_builtin['num_buckets']},"
          f"{stats_builtin['used_buckets']},{stats_builtin['max_bucket_size']},"
          f"{stats_builtin['avg_load_non_empty']:.2f},{stats_builtin['variance_non_empty']:.2f}")
    print(f"bad,{stats_bad['num_keys']},{stats_bad['num_buckets']},"
          f"{stats_bad['used_buckets']},{stats_bad['max_bucket_size']},"
          f"{stats_bad['avg_load_non_empty']:.2f},{stats_bad['variance_non_empty']:.2f}")


#  RESIZE OVERHEAD
def experiment_resize_overhead(num_keys=100_000, sample_every=100):
    """
    Insert keys one-by-one and record the time for EACH single insert.
    We only *print* every `sample_every`th insert to keep terminal output readable.
    """
    print_section("EXPERIMENT 4: RESIZE OVERHEAD")

    keys = make_random_ints(num_keys)
    d = {}

    per_insert_times = []

    print(f"# Sampling every {sample_every} inserts")
    print("index,time_per_insert_us")

    for i, k in enumerate(keys):
        start = time.perf_counter()
        d[k] = i
        end = time.perf_counter()
        dt = (end - start) * 1e6  # microseconds
        per_insert_times.append(dt)

        if i % sample_every == 0 or i == num_keys - 1:
            print(f"{i},{dt:.3f}")

    avg = statistics.mean(per_insert_times)
    mx = max(per_insert_times)

    print()
    print(f"# Summary: n={num_keys}, avg_per_insert_us={avg:.3f}, max_insert_us={mx:.3f}")


#  MAIN
if __name__ == "__main__":
    random.seed(0)  # reproducible runs

    print_section("SAMPLE DATASETS")
    datasets = build_sample_datasets()
    for name, data in datasets.items():
        print(f"{name}: size={len(data)} example_first_3={data[:3]}")

    # Experiment 1: Load factor impact on big int dataset
    experiment_load_factor(datasets["ints_100k"], label="ints_100k")

    # Experiment 2: Collision frequency (good vs adversarial keys)
    experiment_collision_frequency()

    # Experiment 3: Hash function quality (builtin vs bad hash)
    experiment_hash_function_quality()

    # Experiment 4: Resize overhead (sampled output)
    experiment_resize_overhead(num_keys=50_000, sample_every=100)
