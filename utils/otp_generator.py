import os
import random

def generate_otp() -> str:
    """Generate a six-digit random number as a string."""
    # Generate a random number between 0 and 999999
    otp = random.randint(0, 999999)
    # Format the number as a six-digit string, padding with leading zeros if necessary
    return f"{otp:06d}" 