"""
How Python's 'with' statement works - the actual mechanism.
"""

class MyContext:
    def __enter__(self):
        print("__enter__ called")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("__exit__ called (Python interpreter calls this automatically)")
        return False  # Don't suppress exceptions

print("=" * 80)
print("HOW 'with' BLOCK EXITS")
print("=" * 80)

print("\n1. Normal exit (reaches end of block):")
with MyContext():
    print("  Inside 'with' block")
    # Block ends here → Python calls __exit__ automatically
print("  After 'with' block")

print("\n2. Early return:")
def func():
    with MyContext():
        print("  Inside 'with' block")
        return  # Python calls __exit__ BEFORE returning
    print("  This never runs")
func()

print("\n3. Exception:")
try:
    with MyContext():
        print("  Inside 'with' block")
        raise ValueError("test")  # Python calls __exit__ even on exception
except ValueError:
    print("  Exception caught")

print("\n4. Break/continue:")
for i in range(2):
    with MyContext():
        print(f"  Inside 'with' block, iteration {i}")
        if i == 0:
            break  # Python calls __exit__ before breaking
    print("  This never runs")

print("\n" + "=" * 80)
print("KEY POINT:")
print("=" * 80)
print("Python's interpreter tracks the 'with' block.")
print("When execution LEAVES the block (any way), it AUTOMATICALLY calls __exit__.")
print("This is built into Python's language semantics - no magic needed.")


