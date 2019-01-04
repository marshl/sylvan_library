from os import path

json_download_url = "https://archive.scryfall.com/json/scryfall-all-cards.json"
json_set_download_url = "https://api.scryfall.com/sets"
data_folder = path.abspath('data_import/data')
find_results_path = path.join(data_folder, 'find_results.json')
json_data_path = path.join(data_folder, 'scryfall-all-cards.json')
json_set_data_path = path.join(data_folder, 'scryfall-sets.json')

language_json_path = path.join(data_folder, 'languages.json')
colour_json_path = path.join(data_folder, 'colours.json')
rarity_json_path = path.join(data_folder, 'rarities.json')
