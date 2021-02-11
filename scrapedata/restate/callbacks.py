# -*- coding: utf-8 -*-

from py4web import Field
from ..models import db
from ...planetclient.callbacks import _geomdbset, _get_buffered_bounds

import h3
import mercantile as mt
from geojson import Feature, FeatureCollection, Polygon
import geojson
from itertools import groupby, chain
import scipy
from geomet import wkt
import mercantile
from geojson2vt.geojson2vt import geojson2vt

from kilimanjaro.color.loader import colors
from kilimanjaro.color.feader import colorScaleFader, parse

from ...planetstore.tools.tilesets import tile_by_dim, zoom2dims
from ...planetstore.setup.postgresql import __replace_view

from ...planetclient.pbftools import geom2tile

mycolors = colors["colortona"]["Hold"]["5"]

def hex2poly(hex):
    outline = list(map(lambda latlon: latlon, h3.h3_set_to_multi_polygon([hex], geo_json=True)[0][0]))
    return Polygon([outline])

def _select_points(minlon, minlat, maxlon, maxlat,
    source_name='__GENERIC__', tags=[], fields=[]
):
    """ """

    basedbset = _geomdbset(db.points, minlon, minlat, maxlon, maxlat,
        source_name=source_name, tags=tags
    )
    dbset = basedbset((db.points.id==db.restate.info_id))

    result = dbset.iterselect(
        db.points.id,
        db.points.src_id,
        db.points.geom,
        db.restate.stdup.with_alias('rate'),
        *fields
    )
    return result

def fetch(minlon, minlat, maxlon, maxlat,
    source_name='__GENERIC__', tags=[],
    zoom=18, tile=False
):
    """
    """

    left, bottom, right, top, resolution = _get_buffered_bounds(
        minlon, minlat, maxlon, maxlat,
        zoom = zoom, classic = tile
    )

    price = "(points.properties->>'price:€')::integer"
    surface = "(points.properties->>'surface:m²')::integer"
    address = "(points.properties->>'address')"

    result = _select_points(left, bottom, right, top,
        source_name=source_name, tags=tags,
        fields = [price, surface, address]
    )

    features = [Feature(
        id = row.points.hashid,
        geometry = row.points.feat_geometry,
        properties = dict(
            id = row.points.hashid,
            rate = row.rate,
            price = row[price],
            uprice = row[price]//row[surface],
            address = row[address]
        )
    ) for row in result]

    return FeatureCollection(features)

def fetch_a_tile(lon, lat, mindist=155, classic=False, source_name='__GENERIC__'):
    """
    lon, lat @float : A point cooridnates;
    mindist @integer/float : The tile will be dimensioned with this dinstance as minimal;
    classic @boolean : Whether to use classic square tiles or Uber H3 hexagonal ones;
    source_name @string : Source name filter.
    """

    tile = tile_by_dim(lon, lat, bdim=mindist, asc=False, classic=classic)
    if classic:
        tilename = '/'.join(map(str, tile))
        polygon_ = mt.feature(tile)['geometry']
    else:
        tilename = tile
        outline = list(map(lambda latlon: latlon, h3.h3_set_to_multi_polygon([tile], geo_json=True)[0][0]))
        polygon_ = Polygon([outline])

    polygon = geojson.dumps(polygon_)

    basequery = (db.points.source_name==source_name)
    basequery &= (db.points.id==db.restate.info_id)
    basequery &= f"ST_Intersects(points.geom, ST_SetSRID(ST_GeomFromGeoJSON('{polygon}'), 4326))"

    price = "(points.properties->>'price:€')::integer"
    surface = "(points.properties->>'surface:m²')::integer"

    mrate = "PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY restate.stdup) as mrate"
    pricemax = f"MAX({price}) as pricemax"
    pricemin = f"MIN({price}) as pricemin"
    count = f"COUNT(restate.id) as count"
    upricemax = f"MAX(({price}/{surface})::integer) as upricemax"
    upricemin = f"MIN(({price}/{surface})::integer) as upricemin"

    row = db(basequery).select(
        db.restate.stdup.avg().with_alias("rate"),
        mrate,
        pricemax,
        pricemin,
        count,
        upricemax,
        upricemin
    ).first()

    return Feature(
        id = tilename,
        geometry = polygon_,
        properties = dict(
            id = tilename,
            rate = row.rate,
            mrate = row[mrate],
            pricemax = row[pricemax],
            pricemin = row[pricemin],
            count = row[count],
            upricemax = row[upricemax],
            upricemin = row[upricemin]
        )
    )

def fetchtiled_(minlon, minlat, maxlon, maxlat, zoom=18, classic=False,
    source_name='__GENERIC__', tags=[]
):
    """
    minlon, minlat, maxlon, maxlat @float : Bbox limits;
    zoon @integer : Square tile zoom level or hexagonal tile resolution;
    classic @boolean : Whether to use classic square tiles or Uber H3 hexagonal ones;
    source_name @string : Source name filter;
    tags @dict[] : Tags to be used as filter.

    Returns: Rows
    """

    left, bottom, right, top, resolution = _get_buffered_bounds(
        minlon, minlat, maxlon, maxlat,
        zoom = zoom, classic = classic
    )

    price = "(points.properties->>'price:€')::integer"
    surface = "(points.properties->>'surface:m²')::integer"

    if classic:
        tile_ = f"T_tile(points.geom, {resolution})"
        tilename_ = f"T_tilename({tile_})"
        # polygon_ = f"T_bounds({tile_})"
        get_poly_method = "T_bounds(buzz.tile)"

        # tilename_ = f"tilename(points.geom, {resolution})"
        # polygon_ = f"bounds_for_tile_indices(ST_Y(tile_indices_for_lonlat(points.geom, {resolution})), ST_X(tile_indices_for_lonlat(points.geom, {resolution})), {resolution})"
    else:
        tile_ = f"h3_geo_to_h3index(points.geom, {resolution})"
        tilename_ = tile_
        # polygon_ = f"h3_h3index_to_geoboundary(h3_geo_to_h3index(points.geom, {resolution}))"
        get_poly_method = "h3_h3index_to_geoboundary(buzz.tile)"

    # geom_ = f"ST_AsGeoJSON({polygon_})"

    basedbset = _geomdbset(db.points, left, bottom, right, top,
        source_name=source_name, tags=tags
    )
    dbset = basedbset((db.points.id==db.restate.info_id))

    tile = f"{tile_} as tile"
    tilename = f"{tilename_} as tilename"
    # geom = f"(array_agg({geom_}))[1] as geom"

    mrate = "PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY restate.stdup) as mrate"
    pricemax = f"MAX({price}) as pricemax"
    pricemin = f"MIN({price}) as pricemin"
    count = f"COUNT(restate.id) as count"
    upricemax = f"MAX(({price}/{surface})::integer) as upricemax"
    upricemin = f"MIN(({price}/{surface})::integer) as upricemin"

    query = dbset._select(
        db.points.id.min().with_alias('id'),
        tile,
        tilename,
        # geom,
        db.restate.stdup.avg().with_alias("rate"),
        mrate,
        pricemax,
        pricemin,
        count,
        upricemax,
        upricemin,
        orderby = "tilename",
        groupby = "tilename, tile"
    )

    __replace_view('buzz', f"SELECT {get_poly_method} as geom, * FROM ({query[:-1]}) as buzz")

    db.define_table('buzz',
        Field('geom', 'geometry()'),
        Field('tilename'),
        Field('rate', 'double'),
        Field('mrate', 'double'),
        Field('pricemax', 'integer'),
        Field('pricemin', 'integer'),
        Field('count', 'integer'),
        Field('upricemax', 'double'),
        Field('upricemin', 'double'),
        Field.Virtual('feat_geometry', lambda row: wkt.loads(row['buzz'].geom)),
        migrate = False,
        redefine = True
    )

    result = db(db.buzz.id>0).iterselect()

    db.rollback()

    return result

def fetchtiled(minlon, minlat, maxlon, maxlat, zoom=18, classic=False,
    source_name='__GENERIC__', tags=[]
):
    """
    minlon, minlat, maxlon, maxlat @float : Bbox limits;
    zoon @integer : Square tile zoom level or hexagonal tile resolution;
    classic @boolean : Whether to use classic square tiles or Uber H3 hexagonal ones;
    source_name @string : Source name filter;
    tags @dict[] : Tags to be used as filter.

    Returns: Geojson FeatureCollection of the selected points grouped by tiles.
    """

    if not classic:
        dim = min(zoom2dims(zoom, maxlon, maxlat))
        tile, resolution = tile_by_dim(maxlon, maxlat, bdim=dim, asc=True, classic=False, more=True)
    else:
        resolution = zoom

    result = fetchtiled_(minlon, minlat, maxlon, maxlat, zoom=resolution,
        classic=classic, source_name=source_name, tags=tags)

    return FeatureCollection([Feature(
        id = row["tilename"],
        geometry = row["feat_geometry"],
        properties = dict(
            id = row["tilename"],
            rate = row.rate,
            mrate = row["mrate"],
            pricemax = row["pricemax"],
            pricemin = row["pricemin"],
            count = row["count"],
            upricemax = row["upricemax"],
            upricemin = row["upricemin"],
            color = colorScaleFader(row.rate, mycolors)
        )
    ) for row in result], name='re')

def vtile(x, y, z=18, resolution=18, classic=True, source_name='__GENERIC__', tags=[]):
    """ """

    bounds = mercantile.bounds(x, y, z)

    result = fetchtiled_(
        minlon = bounds.west,
        minlat = bounds.south,
        maxlon = bounds.east,
        maxlat = bounds.north,
        zoom = resolution,
        classic = classic,
        source_name = source_name,
        tags = tags
    )

    return dict(
        name = 'mytiles',
        # extent = 4096,
        # version = 2,
        features = [dict(
            id = row["tilename"],
            type = 3,
            geometry = geom2tile(x, y, z, row.feat_geometry),
            properties = dict(
                id = row["tilename"],
                rate = row.rate,
                mrate = row["mrate"],
                pricemax = row["pricemax"],
                pricemin = row["pricemin"],
                count = row["count"],
                upricemax = row["upricemax"],
                upricemin = row["upricemin"],
                color = colorScaleFader(row.rate, mycolors)
            )
        ) for nn,row in enumerate(result)]
    )

def fetch_and_tile(minlon, minlat, maxlon, maxlat, zoom=18, classic=False,
    source_name='__GENERIC__', tags=[]
):
    """
    minlon, minlat, maxlon, maxlat @float : Bbox limits;
    zoon @integer : Square tile zoom level or hexagonal tile resolution;
    classic @boolean : Whether to use classic square tiles or Uber H3 hexagonal ones;
    source_name @string : Source name filter;
    tags @dict[] : Tags to be used as filter.

    Returns: Geojson FeatureCollection of the selected points grouped by tiles.
    """

    left, bottom, right, top, resolution = _get_buffered_bounds(
        minlon, minlat, maxlon, maxlat,
        zoom = zoom, classic = classic
    )

    price = "(points.properties->>'price:€')::integer"
    surface = "(points.properties->>'surface:m²')::integer"

    result = _select_points(left, bottom, right, top,
        source_name=source_name, tags=tags,
        fields = [price, surface]
    )

    sgf = lambda row: row.points.tile(zoom=resolution, classic=tile)
    data = sorted(result, key=sgf)
    grouped = groupby(data, sgf)

    def props(nfo_):
        nfo = list(nfo_)
        return dict(
            rate = scipy.mean(list(map(lambda ff: ff['rate'], nfo))),
            mrate = scipy.median(list(map(lambda ff: ff['rate'], nfo))),
            pricemax = max(map(lambda ff: ff['_extra'][price], nfo)),
            pricemin = min(map(lambda ff: ff['_extra'][price], nfo)),
            upricemax = max(map(lambda ff: ff['_extra'][price]//ff['_extra'][surface], nfo)),
            upricemin = min(map(lambda ff: ff['_extra'][price]//ff['_extra'][surface], nfo)),
            count = len(nfo)
        )

    if tile:
        features = [mt.feature(tile_, props=props(nfo)) for tile_, nfo in grouped]
    else:
        features = [Feature(
            id = tile_,
            geometry = hex2poly(tile_),
            properties = props(nfo)
        ) for tile_, nfo in grouped]

    return FeatureCollection(features)

if __name__ == '__main__':
    minlon, minlat = 9.225243330001833, 44.34747596275757
    maxlon, maxlat = 9.240360260009767, 44.35171861235727
    fc = fetchtiled(minlon, minlat, maxlon, maxlat, zoom=12, classic=False, source_name='immobiliare.it')
    import pdb; pdb.set_trace()
