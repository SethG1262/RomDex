from services.igdb_service import IGDBService


igdb = IGDBService()

print("Checking platform IDs...")
platforms = igdb.search_platforms("Nintendo DSi")

for platform in platforms:
    print(platform)

print("\nSearching 3DS games...")
games = igdb.search_3ds_games("pokemon")

for game in games:
    print(game.get("name"))