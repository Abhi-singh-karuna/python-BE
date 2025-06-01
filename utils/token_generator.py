import secrets
import string
from typing import Optional

def generate_secure_token(length: int = 32, include_special_chars: bool = True) -> str:
    """
    Generate a secure random token of specified length.
    
    Args:
        length (int): Length of the token to generate. Default is 32.
        include_special_chars (bool): Whether to include special characters. Default is True.
    
    Returns:
        str: A secure random token
    
    Example:
        >>> token = generate_secure_token()
        >>> len(token) == 32
        True
    """
    # Define character sets
    alphabet = string.ascii_letters + string.digits
    if include_special_chars:
        alphabet += string.punctuation.replace("'", "").replace('"', "").replace("\\", "")
    
    # Generate token using secrets module
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return token

def generate_url_safe_token(length: int = 32) -> str:
    """
    Generate a URL-safe secure token of specified length.
    
    Args:
        length (int): Length of the token to generate. Default is 32.
    
    Returns:
        str: A URL-safe secure random token
    
    Example:
        >>> token = generate_url_safe_token()
        >>> len(token) == 32
        True
    """
    # Use secrets.token_urlsafe which generates URL-safe base64-encoded random bytes
    # The length parameter is in bytes, so we need to adjust for base64 encoding
    # Base64 encoding uses 4 characters for every 3 bytes
    bytes_length = (length * 3) // 4
    token = secrets.token_urlsafe(bytes_length)
    
    # Trim to exact length if needed
    return token[:length]

def generate_numeric_token(length: int = 6) -> str:
    """
    Generate a secure numeric token of specified length.
    
    Args:
        length (int): Length of the token to generate. Default is 6.
    
    Returns:
        str: A secure random numeric token
    
    Example:
        >>> token = generate_numeric_token()
        >>> len(token) == 6
        True
        >>> token.isdigit()
        True
    """
    # Generate token using only digits
    token = ''.join(secrets.choice(string.digits) for _ in range(length))
    
    return token 