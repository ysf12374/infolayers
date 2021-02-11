# -*- coding: utf-8 -*-

from ..common import Field
from .models import db
from ..planetclient.callbacks import _get_buffered_bounds, _geomdbset
from ..planetstore.setup.postgresql import __replace_view
from ..planetstore.tools.tilesets import tile_by_dim, zoom2dims
from kilimanjaro.color.feader import colorScaleFader
from kilimanjaro.color.loader import colors
from geojson import Feature, FeatureCollection
from geomet import wkt

GEOM_VIEW = 'gview' # was buzz
PROPS_VIEW = 'pview' # was foo

def setup_views(minlon, minlat, maxlon, maxlat, zoom=18, classic=True,
    source_name='__GENERIC__', tags=[]):
    """
    minlon, minlat, maxlon, maxlat @float : Bbox limits;
    zoon @integer : Square tile zoom level or hexagonal tile resolution;
    classic @boolean : Whether to use classic square tiles or Uber H3 hexagonal ones;
    source_name @string : Source name filter;
    tags @dict[] : Tags to be used as filter.

    Returns: None, just setup views for easyer queries
    """

    left, bottom, right, top, resolution = _get_buffered_bounds(
        minlon, minlat, maxlon, maxlat,
        zoom = zoom, classic = classic
    )

    gtab = db.polys
    tiled_geom = 'centroid'

    if classic:
        tile_ = f"T_tile({gtab}.{tiled_geom}, {resolution})"
        tilename_ = f"T_tilename({tile_})"
        # polygon_ = f"T_bounds({tile_})"
        get_poly_method = f"T_bounds({GEOM_VIEW}.tile)"

        # tilename_ = f"tilename(points.geom, {resolution})"
        # polygon_ = f"bounds_for_tile_indices(ST_Y(tile_indices_for_lonlat(points.geom, {resolution})), ST_X(tile_indices_for_lonlat(points.geom, {resolution})), {resolution})"
    else:
        tile_ = f"h3_geo_to_h3index({gtab}.{tiled_geom}, {resolution})"
        tilename_ = tile_
        # polygon_ = f"h3_h3index_to_geoboundary(h3_geo_to_h3index(points.geom, {resolution}))"
        get_poly_method = f"h3_h3index_to_geoboundary({GEOM_VIEW}.tile)"

    dbset = _geomdbset(gtab, left, bottom, right, top,
        source_name=source_name, tags=tags
    )

    tile = f"{tile_} as tile"
    tilename = f"{tilename_} as tilename"

    # Organize informations about geometries stored in Planet model

    geom_query = dbset._select(
        db.polys.id,
        tile,
        db.polys.geom.with_alias('bgeom'),
        db.polys.source_id,
        db.polys.properties,
        tilename
    )

    __replace_view(GEOM_VIEW, f"SELECT {get_poly_method} as geom, * FROM ({geom_query[:-1]}) as {GEOM_VIEW}")

    db.define_table(GEOM_VIEW,
        Field('geom', 'geometry()'),
        Field('bgeom', 'geometry()'),
        Field('properties', 'json'),
        Field('tilename'),
        Field('source_id'),
        # Field('count', 'integer'),
        # Field('mrate', 'double'),
        Field.Virtual('feat_geometry', lambda row: wkt.loads(row[GEOM_VIEW].geom)),
        migrate = False,
        redefine = True
    )

    # Organize informations about properties stored in local model

    _ = lambda c: f"COALESCE((broadband.info->>'{c}')::float, 0)"
    download = "LEAST(100, GREATEST({}, {}, {}))/100".format(*map(_, ('speed_down', 'speed_do_1', 'speed_do_2')))
    upload = "LEAST(100, GREATEST({}, {}, {}))/100".format(*map(_, ('speed_up_a', 'speed_up_v', 'speed_up_e')))

    ftth = """CASE
    WHEN (broadband.info->>'ftth_cover')::float >= 1 THEN 1
    ELSE 0
END"""

    rate = f"0.7*({download})+0.2*({upload})+({ftth}/10.0)"

    __replace_view(
        PROPS_VIEW,
        db(
            (db.broadband.broadband_source_id==db.broadband_source.id)
        )._select(
        db.broadband.id,
        db.broadband.info,
        f"{download} as download",
        f"{upload} as upload",
        f"({ftth}) as ftth",
        f"{rate} as rate",
        db.broadband.grid_cell_id.with_alias('source_id'),
        # Only the last information for each broadband type connection
        distinct = db.broadband_source.broadband|db.broadband.grid_cell_id,
    ))

    db.define_table(PROPS_VIEW,
        Field('info', 'json'),
        Field('source_id'),
        Field('download', 'double'),
        Field('upload', 'double'),
        Field('ftth', 'integer'),
        Field('rate', 'double'),
        migrate = False,
        redefine = True
    )

def fetchtiled_(minlon, minlat, maxlon, maxlat, zoom=18, classic=False,
    source_name='__GENERIC__', tags=[]):
    """
    minlon, minlat, maxlon, maxlat @float : Bbox limits;
    zoon @integer : Square tile zoom level or hexagonal tile resolution;
    classic @boolean : Whether to use classic square tiles or Uber H3 hexagonal ones;
    source_name @string : Source name filter;
    tags @dict[] : Tags to be used as filter.

    Returns: Rows
    """

    setup_views(**vars())

    GROUPED_VIEW = "tview" # was bar

    __replace_view(
        GROUPED_VIEW,
        db(
            (db[GEOM_VIEW].source_id==db[PROPS_VIEW].source_id)
        )._select(
            db[PROPS_VIEW].id.min().with_alias('id'),
            db[GEOM_VIEW].tilename.with_alias('tilename'),
            db[GEOM_VIEW].geom.with_alias('geom'),
            # "stddev(upload)" # (*)
            "max(upload) as max_upload",
            "min(upload)as min_upload",
            "max(download) as max_download",
            "min(download) as min_download",
            "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate) as mrate",
            db[PROPS_VIEW].source_id.count().with_alias('count'),
            groupby = "tilename, geom",
            # distinct = db.foo.broadband_source_id,
            # orderby = db.foo.source_id
        )
    )

    # TODO: (*) Nesting view definition we can define usefull statistic values once
    # and reuse them at the higher level in a efficient way
    # __replace_view('bar', f", * FROM ({query[:-1]}) as buzz")

    db.define_table(GROUPED_VIEW,
        Field('tilename'),
        Field('geom', 'geometry()'),
        Field('count', 'integer'),
        Field('max_upload', 'double'),
        Field('min_upload', 'double'),
        Field('max_download', 'double'),
        Field('min_download', 'double'),
        Field('mrate', 'double'),
        Field.Virtual('feat_geometry', lambda row: wkt.loads(row[GROUPED_VIEW].geom)),
        migrate = False,
        redefine = True
    )

    result = db(db[GROUPED_VIEW]).select()

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
            mrate = row["mrate"],
            count = row["count"],
            min_download = row["min_download"],
            max_download = row["max_download"],
            min_upload = row["min_download"],
            max_upload = row["max_download"]
            # color = colorScaleFader(row.mrate, mycolors)
        )
    ) for row in result], name='internet')

GRID_VIEW = "grid_view"

def fetch_(minlon, minlat, maxlon, maxlat, zoom, source_name='AGCOM', tags=[]):

    setup_views(**vars())

    __replace_view(
        GRID_VIEW,
        db(
            (db[GEOM_VIEW].source_id==db[PROPS_VIEW].source_id)
        )._select(
            db[PROPS_VIEW].id,
            db[GEOM_VIEW].bgeom.with_alias('geom'),
            db[PROPS_VIEW].download,
            db[PROPS_VIEW].upload,
            db[PROPS_VIEW].ftth,
            db[PROPS_VIEW].rate
        )
    )

    # TODO: (*) Nesting view definition we can define usefull statistic values once
    # and reuse them at the higher level in a efficient way
    # __replace_view('bar', f", * FROM ({query[:-1]}) as buzz")

    db.define_table(GRID_VIEW,
        Field('geom', 'geometry()'),
        Field('upload', 'double'),
        Field('download', 'double'),
        Field('ftth', 'integer'),
        Field('rate', 'double'),
        Field.Virtual('feat_geometry', lambda row: wkt.loads(row[GRID_VIEW].geom)),
        migrate = False,
        redefine = True
    )

    result = db(db[GRID_VIEW]).select()

    db.rollback()

    return result

def fetch(minlon, minlat, maxlon, maxlat, zoom, source_name='AGCOM', tags=[]):

    res = fetch_(**vars())

    return FeatureCollection([Feature(
        id = row.id,
        geometry = row[GRID_VIEW].feat_geometry,
        properties = dict(
            id = row.id,
            count = 1,
            mrate = row["rate"],
            max_download = row["download"],
            max_upload = row["upload"],
            ftth_cover = bool(row["ftth"]),
        )
    ) for row in res], name='internet')

if __name__ == '__main__':
    minlon, minlat = 8.9923095703125, 45.32897866218559
    maxlon, maxlat = 9.195556640625, 45.47554027158593
    # res = fetchtiled(minlon, minlat, maxlon, maxlat, zoom=12, classic=False, source_name='AGCOM')
    resg = fetchtiled(minlon, minlat, maxlon, maxlat, zoom=12, source_name='AGCOM')
    res = fetch(minlon, minlat, maxlon, maxlat, zoom=12, source_name='AGCOM')
    import pdb; pdb.set_trace()
