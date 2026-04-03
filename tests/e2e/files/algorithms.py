"""Sorting and searching algorithms on a variety of datasets."""


def merge_sort(arr):
    if len(arr) <= 1:
        return list(arr)
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def heap_sort(arr):
    lst = list(arr)
    n = len(lst)

    def sift_down(i, end):
        while True:
            largest = i
            left = 2 * i + 1
            right = 2 * i + 2
            if left <= end and lst[left] > lst[largest]:
                largest = left
            if right <= end and lst[right] > lst[largest]:
                largest = right
            if largest == i:
                break
            lst[i], lst[largest] = lst[largest], lst[i]
            i = largest

    for i in range((n - 1) // 2, -1, -1):
        sift_down(i, n - 1)
    for end in range(n - 1, 0, -1):
        lst[0], lst[end] = lst[end], lst[0]
        sift_down(0, end - 1)
    return lst


def quick_sort(arr):
    if len(arr) <= 1:
        return list(arr)
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)


def counting_sort(arr, key=None):
    if not arr:
        return []
    mapped = [key(x) for x in arr] if key else list(arr)
    lo, hi = min(mapped), max(mapped)
    counts = [0] * (hi - lo + 1)
    for v in mapped:
        counts[v - lo] += 1
    result = []
    for i, c in enumerate(counts):
        result.extend([i + lo] * c)
    return result


def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def interpolation_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi and arr[lo] <= target <= arr[hi]:
        if arr[lo] == arr[hi]:
            return lo if arr[lo] == target else -1
        pos = lo + (target - arr[lo]) * (hi - lo) // (arr[hi] - arr[lo])
        if arr[pos] == target:
            return pos
        elif arr[pos] < target:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1


# ── correctness tests ────────────────────────────────────────────────────────

DATA = [
    82,
    3,
    47,
    15,
    91,
    64,
    28,
    73,
    9,
    56,
    40,
    17,
    85,
    32,
    60,
    7,
    99,
    21,
    44,
    68,
    1,
    77,
    53,
    36,
    12,
    89,
    24,
    71,
    49,
    5,
]

EXPECTED = sorted(DATA)

for label, fn in [
    ("merge", merge_sort),
    ("heap", heap_sort),
    ("quick", quick_sort),
    ("counting", counting_sort),
]:
    result = fn(DATA)
    ok = "OK" if result == EXPECTED else "FAIL"
    print(f"{label:10s} {ok}  first={result[:5]}")

sorted_data = EXPECTED
for target in [1, 12, 49, 99, 100, 3, 50]:
    bi = binary_search(sorted_data, target)
    ii = interpolation_search(sorted_data, target)
    match = "match" if bi == ii else f"MISMATCH bi={bi} ii={ii}"
    found = "found" if bi != -1 else "absent"
    print(f"search({target:3d}): {found:6s}  {match}")

# ── multi-pass on larger data ─────────────────────────────────────────────────

big = list(range(200, 0, -1))  # 200 down to 1
big_sorted = sorted(big)

for fn in (merge_sort, heap_sort, quick_sort):
    assert fn(big) == big_sorted

print(f"large-data: all three sorts agree, n={len(big)}")
print(f"sum of sorted: {sum(big_sorted)}")
