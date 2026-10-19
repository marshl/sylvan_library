Sylvan Library
==============
**SylvanLibrary** is a database for storing and managing Magic: the Gathering cards and decks

## Installation

Clone the repository
```bash
git clone https://github.com/marshl/sylvan_library.git
```
Navigate into the folder
```bash
cd ./sylvan_library
```
Create the python virtual environment and install th dependencies
```bash
pipenv install --dev
```
Activate the virtual environment
```bash
pipenv shell
```
Install the React frontend's node modules via npm (this needs Node 20.19 or newer)
```bash
npm install --prefix ./sylvan-react
```

## Database Initialisation

Install Postgres server and create a new database <database_name> with user <username> and password <password> that has access privileges to that database

Make a copy of `sylvan_library/conf/.env.sample` and call it `sylvan_library/conf/.env`

Edit `.env` and add in the information for the database you just created. Django will now be able to connect to that database.

Navigate into the folder that contains the `manage.py` file
```bash
cd ./sylvan_library
```
Run the django migrations
```bash
python manage.py migrate
```

Run the `fetch_data` command to download the latest mtgjson file:
```bash
python manage.py fetch_data
```

Update the database with the new dataset. This can take upwards of an hour, depending on hardware:
```bash
python manage.py update_database
```
Then update card rulings
```bash
python manage.py update_rulings
```
Then download all the card images from Scryfall
```bash
python manage.py download_card_images
```
If you want the non-English images too by specifiying the `--all-languages` flag (downloading all images can take several days, depending on bandwidth)
```bash
python manage.py download_card_images --all-languages
```

## Running the Server
To run the server in debug mode use this command
```bash
python manage.py runserver
```
In debug mode Django sends page requests on to the Vite dev server, so run that too and
open http://localhost:5173/
```bash
npm run dev --prefix ./sylvan-react
```
Without debug mode, Django serves the built React app. Build it with
```bash
npm run build --prefix ./sylvan-react
```

## Projects
 - **cards**: The cards project is where the primary database models are stored, and is designed to be consumed by either an api or a website project
 - **cardsearch**: The cardsearch project contains classes for filtering cards using complex parameter trees
 - **data_import**: The data_import project contains commands and staging zones for importing data from external sources into the database
 - **reports**: The reports project contains Report and graph generation for offline data analysis
 - **frontend**: The frontend project serves the built React app and tells it who is logged in
 - **sylvan-react** (outside the Django project): The React front-end, which talks to the Django REST API