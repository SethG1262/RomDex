from services.cloud.firebase_auth_service import (
    FirebaseAuthError,
    FirebaseAuthService
)


def main():
    try:
        auth_service = FirebaseAuthService()

        token = auth_service.get_valid_id_token()

        print("Firebase connection successful.")
        print(f"Anonymous UID: {auth_service.uid}")
        print(f"ID token received: {bool(token)}")
        print(
            "Run this test again to confirm that the same UID is reused."
        )

    except FirebaseAuthError as error:
        print(f"Firebase connection failed: {error}")


if __name__ == "__main__":
    main()
