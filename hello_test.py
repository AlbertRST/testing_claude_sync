def greet(name):
    """Return a greeting message."""
    return f"Hello, {name}!"

def add_numbers(a, b):
    """Add two numbers and return the result."""
    return a + b

if __name__ == "__main__":
    # Test the functions
    print(greet("World"))
    print(f"2 + 3 = {add_numbers(2, 3)}")
    
    # Test with your name
    print(greet("Alber"))
