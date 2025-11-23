import secrets
import string

def generate_strong_password(length=12):
    """Generate a strong, random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def generate_placeholder_email(first_name, last_name):
    """Generate a placeholder email address."""
    random_string = secrets.token_hex(4)
    email = f"{first_name.lower()}.{last_name.lower()}.{random_string}@cleanit.com"
    return email