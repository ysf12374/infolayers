# Infolayers

## Install

### Get the code

The use of a sub-module requires a one-time use of the --recursive flag for git clone if you are cloning this app from scratch.

    git clone --recursive https://bitbucket.org/colouree/infolayers.git

If you have an existing repository, the commands below need to be executed at least once:

    git submodule update --init --recursive

### Python requirements

> Please remind to activate the proper virtualenv, it's not mandatory but highly
> suggested

    pip install -r <path>/<to>/infolayers/requirements.txt

### Application basic setup

1. Create a *settings_private.py* in your app `root` folder with the subsequent
content adapted to your needs:

        ::python
        SETUP_MODE = True # WARNING: Mandatory

        # logger settings
        LOGGERS = [
            "debug:stdout" # or "info:stdout"
        ]  # syntax "severity:filename" filename can be stderr or stdout

        # db settings
        DB_URI = "postgres://<PG user>:<password>@<host name>/<db name>"
        # DB_POOL_SIZE = 10
        # DB_MIGRATE = <True/False> # True if not specified

1. Run the script for creating and setting up the database extensions and model:

        ::sh
        cd path/to/apps
        python -m <your app>.planetstore.setup.createdb

    > **WARNING**
    > the script will ask for necessary PostgreSQL power user credentials

1. Run the script for setting up views (*named queries*)

        ::sh
        python -m <your app>.planetstore.setup.createviews

1. **NOW Comment out the SETUP_MODE variable definition in private settings file or set its value to False.**

#### Create missing empty directories

    mkdir <path>/<to>/infolayers/translations
    mkdir <path>/<to>/infolayers/databases

### Other configurations

#### Vector tile cache setup

Append to *setings_private.py* file subsequent section to enable caching of vector tiles

        ::python
        from geopbf import settings as gpbfsettings

        # Decomment this line for enable live cacheng of uncached contents
        # gpbfsettings.CACHE_NEW = True
        gpbfsettings.DB_URI = "postgres://<username>:<password>@<host>:<port>/<database name>"
        gpbfsettings.DB_POOL_SIZE = 20

> This settings will overwrite geopbf library default settings for integrating
> it in your application.

You can use the dbgenie command line (that comes with the installation of the *kilimanjaro* required python library)

Please refere to the command line option documentation for usage details, arguments and options:

        ::sh
        dbgenie -h

Usage template example:

        ::sh
        dbgenie path/to/apps/<thisapp>/databases postgres://<username>:{password}@localhost/<dbname>

## Populate the db

1. Set a proper value for the location variables
    Adding following lines to the *settings_private.py* file will setup the application
    for monitoring data for the town of Rapallo:

        ::python
        from scrapealong import settings as scrapealong_settings
        scrapealong_settings.IMMOBILIARE_LOCATIONS = [
            # Examples
            # "Torino",
            # "Genova",
            "Rapallo",
            # "Santa Margherita Ligure",
            # "Milano"
        ]
