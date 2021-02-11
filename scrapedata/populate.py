# -*- coding: utf-8 -*-

from .models import db

def monkeypatching():
    from scrapealong.scrapealong import settings
    settings.DB_FOLDER = db._folder

monkeypatching()

from . import settings
from scrapealong.scrapealong.populate import fetchall
from scrapealong.scrapealong.populate import extract2 as extract

from ..planetstore.populate.io import json as geojson2db

from geojson import FeatureCollection
from itertools import groupby

# def fetch_row_data(commit=True):
#     sids = map(
#         lambda row: row.source_id,
#         db(db.info.source_name=='tripadvisor').iterselect(db.info.source_id)
#     )
#     fetch_row_data_(escape=set(sids), commit=commit)


rateit = lambda ff: ff
"""
ff @dict : A geojson Feature

returns:
    A geojson Feature

TODO:
This function will take the incoming feature before (it's saved to the DB)
so the specific rate can be calculated and associated to it in their properties
before it's returned.
"""

def populate(champ=500, commit=False):
    """ """

    for source_name, feats in groupby(
        fetchall(champ=champ, commit=True),
        lambda ff: ff['source']
    ):
        collection = FeatureCollection(list(filter(
            None,
            map(rateit, feats)
        )))
        geojson2db(collection, source_name=source_name)
        if commit: db.commit()

def regen():
    """ Extracts row html from db and try to apply latest scraping methods and
        updates properties values.
    """
    for updates_, source_name in extract():
        updates, warnings = updates_[-2:]
        info = db.info(source_id=updates['sid'], source_name=source_name)
        # import pdb; pdb.set_trace()
        if not info is None:
            if any([info.properties.get(k)!=v for k,v in updates.items()]):
                info.update_record(properties=dict(info.properties, **updates))
            else:
                # Nothing to update
                pass

if __name__ == '__main__':

    import argparse
    from scrapealong.scrapealong.populate import populate as populate1

    parser = argparse.ArgumentParser(description='Populate the database')
    parser.add_argument("-t", "--test",
        help = 'Force not to fix storing scraping meta informations',
        action = 'store_true',
        default = True,
        dest = 'test_mode'
    )
    parser.add_argument("-f", "--fetch",
        help = 'Fetch preliminary informations from multi amenity pages',
        action = 'store_true',
        default = True
    )
    args = parser.parse_args()

    if args.fetch:
        populate1(commit=True)

    # populate(commit=(not args.test_mode))
    populate(commit=True)
