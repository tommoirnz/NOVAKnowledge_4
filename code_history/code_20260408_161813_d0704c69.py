# Generated: 2026-04-08 16:18:13
# ============================================================

def average(nums):
    if not nums:
        raise ValueError("Cannot compute average of an empty list — no data provided.")
    return sum(nums) / len(nums)

# Test 1: Empty list
try:
    result = average([])
    print(f"average([]) = {result}")
except ValueError as e:
    print(f"average([]) raised ValueError: {e}")

# Test 2: Non-empty list
result = average([1, 2, 3, 4, 5])
print(f"average([1, 2, 3, 4, 5]) = {result}")