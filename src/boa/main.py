import argparse

from boa.config.database import test_connection
from boa.reporting.pdf import generate_business_performance_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Business Operations Analytics Platform"
    )
    parser.add_argument(
        "command",
        choices=["check-db", "generate-report"],
        help="Command to execute",
    )

    args = parser.parse_args()

    if args.command == "check-db":
        try:
            connected = test_connection()

            if connected:
                print("Database connection successful")

        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    elif args.command == "generate-report":
        try:
            output = generate_business_performance_report()
            print(f"Business performance report generated: {output.resolve()}")

        except Exception as e:
            print(f"Report generation failed: {e}")
            raise


if __name__ == "__main__":
    main()
