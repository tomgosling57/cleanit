#!/usr/bin/env python3
import secrets
import string

def random_string(length=32):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


ENV_VARS = [
    {
        "name": "POSTGRES_DB",
        "default": "cleanit",
        "random": False,
    },
    {
        "name": "POSTGRES_USER",
        "default": "cleanit_user",
        "random": False,
    },
    {
        "name": "POSTGRES_PASSWORD",
        "default": "",
        "random": True,
    },
    {
        "name": "MINIO_ROOT_USER",
        "default": "minioadmin",
        "random": False,
    },
    {
        "name": "MINIO_ROOT_PASSWORD",
        "default": "minioadmin",
        "random": True,
    },
    {
        "name": "SECRET_KEY",
        "default": "",
        "random": True,
    },
    {
        "name": "S3_BUCKET",
        "default": "cleanit-media",
        "random": False,
    },
    {
        "name": "AWS_REGION",
        "default": "us-east-1",
        "random": False,
    },
    {
        "name": "FLASK_ENV",
        "default": "production",
        "random": False,
    },
]


def prompt(var):
    name = var["name"]
    default = var["default"]
    allow_random = var["random"]

    prompt_parts = [name]
    if default:
        prompt_parts.append(f"default: {default}")
    if allow_random:
        prompt_parts.append("type 'random' to generate")

    prompt_text = " (" + ", ".join(prompt_parts[1:]) + ")" if len(prompt_parts) > 1 else ""
    value = input(f"{name}{prompt_text}: ").strip()

    if value.lower() == "random" and allow_random:
        return random_string()
    if value == "":
        return default
    return value


def main():
    print("\nEnvironment variable setup")
    print("-" * 32)

    results = {}

    for var in ENV_VARS:
        results[var["name"]] = prompt(var)

    print("\nGenerated environment variables (.env format):")
    print("-" * 48)

    for key, value in results.items():
        print(f"{key}={value}")

    print("\nTip: redirect this output into a file:")
    print("  python generate_env.py > .env\n")


if __name__ == "__main__":
    main()
