"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
# from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated
# from .callbacks import fetch_by_tile, fetchall
from .callbacks import fetchtiled as fetchtiled_
from .callbacks import fetch as fetchpoints_
from .callbacks import fetch_a_tile as fetch_a_tile_
from .callbacks import vtile as myvtile_

from ...planetclient.controllers import *

from ...planetclient.pbftools import as_pbf

from kilimanjaro.frameworks.py4web.controller import brap, LocalsOnly, CORS

from py4web import response

@action('restate/fetchpoints', method=['GET', 'POST'])
@action.uses(CORS(), LocalsOnly())
def restate_fetchpoints():
    response.headers["Content-Type"] = "application/geo+json"
    return brap()(fetchpoints_)()

@action('restate/fetchtiled', method=['GET', 'POST'])
@action.uses(CORS())
def restate_fetchtiled():
    response.headers["Content-Type"] = "application/geo+json"
    return brap()(fetchtiled_)(source_name='immobiliare.it')

@action('restate/fetchtiled.topojson', method=['GET', 'POST'])
@action.uses(CORS())
@action.uses('../planetclient/templates/generic.topo.json')
def restate_fetchtiled_topo():
    return dict(topology=brap(source_name='immobiliare.it')(fetchtiled_)())

@action('cluster/realestate.topojson', method=['GET', 'POST'])
@action.uses(CORS())
@action.uses('../planetclient/templates/generic.topo.json')
def restate_fetchtiled_topo2():
    return dict(topology=brap(source_name='immobiliare.it')(fetchtiled_)())

@action('realestate.topojson', method=['GET', 'POST'])
@action.uses(CORS())
def restate_fetchpoints2():
    response.headers["Content-Type"] = "application/geo+json"
    return brap(source_name='immobiliare.it')(fetchpoints_)()

@action('restate/vtile/<xtile:int>/<ytile:int>/<zoom:int>.json', method=['GET'])
@action.uses(LocalsOnly())
@action.uses('../planetclient/templates/generic.ujson')
def restate_vtile_xyz_json(xtile, ytile, zoom):
    return brap(x=xtile, y=ytile, z=zoom, source_name='immobiliare.it', classic=True)(myvtile_)()

@action('restate/vtile/<xtile:int>/<ytile:int>/<zoom:int>', method=['GET'])
@action.uses(LocalsOnly())
@action.uses(as_pbf())
# @action.uses('../planetclient/templates/mapbox.pbf')
def restate_vtile_xyz(xtile, ytile, zoom):
    return brap(x=xtile, y=ytile, z=zoom, source_name='immobiliare.it', classic=True)(myvtile_)()

@action('restate/vtile/<xtile:int>/<ytile:int>', method=['GET','POST'])
@action.uses(LocalsOnly())
@action.uses(as_pbf())
def restate_vtile_xy(xtile, ytile):
    return brap(x=xtile, y=ytile, source_name='immobiliare.it')(myvtile_)()

@action('restate/vtile', method=['GET','POST'])
@action.uses(LocalsOnly())
@action.uses(as_pbf())
def restate_vtile():
    return brap(source_name='immobiliare.it')(myvtile_)()

@action('restate/fetchsingletile', method=['GET', 'POST'])
@action.uses(CORS(), LocalsOnly())
def restate_fetchsingletile():
    response.headers["Content-Type"] = "application/geo+json"
    return brap()(fetch_a_tile_)()
