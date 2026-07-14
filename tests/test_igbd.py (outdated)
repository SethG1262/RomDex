from services.igdb_service import IGDBService

service = IGDBService()

print(service.credentials_are_ready())

results = service.search_3ds_and_dsi_games("Pokemon")

for game in results:
    print(game.get("name"))
    print(game.get("platforms"))
    print(game.get("cover"))
    print()