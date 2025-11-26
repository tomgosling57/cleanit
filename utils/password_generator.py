import secrets
import string

def generate_placeholder_email(first_name, last_name):
    """Generate a placeholder email address."""
    random_string = secrets.token_hex(4)
    email = f"{first_name.lower()}.{last_name.lower()}.{random_string}@cleanit.com"
    return email


def generate_password(length=16, include_symbols=True):
    """
    Generate a cryptographically secure random password.
    
    Uses only ASCII alphanumeric characters and common symbols that don't
    require HTML escaping, avoiding XSS-prone characters like <, >, &, ", '
    
    Args:
        length: Password length (default 16)
        include_symbols: Whether to include symbols (default True)
    
    Returns:
        A random password string safe for direct HTML insertion
    """
    # Base character set - letters and digits (always safe)
    chars = string.ascii_letters + string.digits
    
    # Safe symbols that don't need HTML escaping
    # Excludes: < > & " ' ` to avoid any XSS risk
    if include_symbols:
        safe_symbols = "!@#$%^*()_+-=[]{}|;:,./?"
        chars += safe_symbols
    
    # Use secrets module for cryptographic randomness
    password = ''.join(secrets.choice(chars) for _ in range(length))
    
    return password


def generate_password_with_requirements(length=16):
    """
    Generate password ensuring at least one of each character type.
    Still XSS-safe with no escaping needed.
    """
    if length < 4:
        raise ValueError("Length must be at least 4 for complexity requirements")
    
    # Ensure at least one of each type
    password_chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^*()_+-=[]{}|;:,./?")
    ]
    
    # Fill remaining length with random safe characters
    safe_chars = string.ascii_letters + string.digits + "!@#$%^*()_+-=[]{}|;:,./?"
    password_chars.extend(secrets.choice(safe_chars) for _ in range(length - 4))
    
    # Shuffle to avoid predictable patterns
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)


# Usage examples
if __name__ == "__main__":
    print("Simple password:", generate_password())
    print("No symbols:", generate_password(include_symbols=False))
    print("Long password:", generate_password(length=24))
    print("With requirements:", generate_password_with_requirements())