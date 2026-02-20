import secrets


def generate_secret():
    # Generates a URL-safe text string, containing 32 random bytes.
    # The string will be approximately 43 characters long.
    secret = secrets.token_urlsafe(32)
    print("\n--- Din nya STORAGE_SECRET ---")
    print(secret)
    print("------------------------------\n")
    print("Kopiera denna och klistra in i din .env fil för STORAGE_SECRET.")


if __name__ == "__main__":
    generate_secret()
