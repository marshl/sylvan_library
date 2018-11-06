from os import path

json_zip_download_url = "https://mtgjson.com/v4/json/AllSets.json.zip"
data_folder = path.abspath('data_import/data')
json_zip_path = path.join(data_folder, 'AllSets-x.json.zip')
json_data_path = path.join(data_folder, 'AllSets.json')
pretty_json_path = path.join(data_folder, 'AllSets-x-pretty.json')

language_json_path = path.join(data_folder, 'languages.json')
colour_json_path = path.join(data_folder, 'colours.json')
rarity_json_path = path.join(data_folder, 'rarities.json')
