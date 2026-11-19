from boa.config.database import test_connection


def main() -> None:
    try:
        connected = test_connection()

        if connected:
            print("Database connection successful")

    except Exception as e:
        print(f"Database connection failed: {e}")
        raise


if __name__ == "__main__":
    main()
