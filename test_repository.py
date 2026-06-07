from services.db import init_db
from repositories.game_repository import GameRepository


def main():
    init_db()

    repo = GameRepository()

    fake_game = {
        "id": 12345,
        "name": "Test Game",
        "summary": "This is a test game.",
        "storyline": "This is a fake storyline.",
        "cover": {
            "image_id": "abc123"
        },
        "release_dates": [
            {
                "human": "Jan 1, 2012"
            }
        ],
        "platforms": [
            {
                "name": "Nintendo 3DS"
            }
        ]
    }

    saved_game = repo.add_game(fake_game)

    print("Saved game:")
    print(saved_game.id)
    print(saved_game.title)
    print(saved_game.platform)
    print(saved_game.cover_url)

    repo.close()


if __name__ == "__main__":
    main()