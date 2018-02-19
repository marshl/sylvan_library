Sylvan Library
==============
**SylvanLibrary** is a database for storing and managing Magic: the Gathering cards and decks

## Installation

Clone the repository and go into the folder
```
git clone https://github.com/marshl/sylvan_library.git
cd ./sylvan_library
```

SylvanLibrary uses git submodules to store some assets. These need to be initialised
```
git subodule init
git submodule update
```
Create the python virtual environment
```
python3 -m venv <env>
```
Activate the virtual environment
```
<env>\scripts\activate.bat
```
or
```
source <env>/bin/activate
```

Install the required python modules
```
pip install -r requirements.txt
```

## Database Initialisation

Install Postgres server and create a new database <database_name> with user <username> and password <password> that has access privileges to that database

Make a copy of `sylvan_library/settings/secrets_empty.json` and call it `sylvan_library/settings/secrets.json`

Edit `secrets.json` and add in the information for the database you just created. Django will now be able to connect to that database.

Now Navigate into the folder with the `manage.py` file and run an import command to download the latest mtgjson file:
```
python manage.py fetch_data
```

Update the database with the new dataset:
```
python manage.py update_database --update-all
```
This can take between 30-60 minutes depending on the speed of your computer.

## Projects
 - **cards**: The cards project is where the primary database models are stored, and is designed to be consumed by either an api or a website project
 - **cardsearch**: The cardsearch project contains classes for filtering cards using complex parameter trees
 - **data_import**: The data_import project contains commands and staging zones for importing data from external sources into the database
 - **website**: The website project contains views and controllers for rendering the sylvan_library front-end