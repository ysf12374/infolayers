# -*- coding: utf-8 -*-

from .common import Field
from .common import db
from .planetclient.callbacks import _get_buffered_bounds, _geomdbset
from .planetstore.setup.postgresql import __replace_view
from .planetstore.tools.tilesets import tile_by_dim, zoom2dims
from kilimanjaro.color.feader import colorScaleFader
from kilimanjaro.color.loader import colors
from geojson import Feature, FeatureCollection
from geomet import wkt

mycolors = colors["colortona"]["Hold"]["5"]

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

    left, bottom, right, top, resolution = _get_buffered_bounds(
        minlon, minlat, maxlon, maxlat,
        zoom = zoom, classic = classic
    )

    tab = db.polys
    tiled_geom = 'centroid'

    if classic:
        tile_ = f"T_tile({tab}.{tiled_geom}, {resolution})"
        tilename_ = f"T_tilename({tile_})"
        # polygon_ = f"T_bounds({tile_})"
        get_poly_method = "T_bounds(buzz.tile)"

        # tilename_ = f"tilename(points.geom, {resolution})"
        # polygon_ = f"bounds_for_tile_indices(ST_Y(tile_indices_for_lonlat(points.geom, {resolution})), ST_X(tile_indices_for_lonlat(points.geom, {resolution})), {resolution})"
    else:
        tile_ = f"h3_geo_to_h3index({tab}.{tiled_geom}, {resolution})"
        tilename_ = tile_
        # polygon_ = f"h3_h3index_to_geoboundary(h3_geo_to_h3index(points.geom, {resolution}))"
        get_poly_method = "h3_h3index_to_geoboundary(buzz.tile)"

    # geom_ = f"ST_AsGeoJSON({polygon_})"

    dbset = _geomdbset(tab, left, bottom, right, top,
        source_name=source_name, tags=tags
    )

    # dbset = basedbset((db.points.id==db.restate.info_id))
    # dbset = basedbset("polys.properties::jsonb ? 'speed_down'")
    # dbset = basedbset("polys.properties::jsonb ? 'speed_do_1'")
    # dbset = basedbset("polys.properties::jsonb ? 'speed_do_2'")
    #
    # dbset = basedbset("polys.properties::jsonb ? 'speed_up_a'")
    # dbset = basedbset("polys.properties::jsonb ? 'speed_up_v'")
    # dbset = basedbset("polys.properties::jsonb ? 'speed_up_e'")

    tile = f"{tile_} as tile"
    tilename = f"{tilename_} as tilename"
    count = f"COUNT(0) as count"
    # geom = f"(array_agg({geom_}))[1] as geom"

    # mrate = "PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY restate.stdup) as mrate"

    _ = lambda c: f"COALESCE((polys.properties->>'{c}')::float, 0)"

    download = "LEAST(100, GREATEST({}, {}, {}))/100".format(*map(_, ('speed_down', 'speed_do_1', 'speed_do_2')))
    upload = "LEAST(100, GREATEST({}, {}, {}))/100".format(*map(_, ('speed_up_a', 'speed_up_v', 'speed_up_e')))

    ftth = """CASE
    WHEN (polys.properties->>'ftth_cover')::float >= 1 THEN 0.1
    ELSE 0
END"""

    rate = f"0.7*({download})+0.2*({upload})+({ftth})"

    query = dbset._select(
        db.polys.id.min().with_alias('id'),
        tile,
        tilename,
        count,
        # geom,
        f"PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY ({rate})) as mrate",
        orderby = "tilename",
        groupby = "tilename, tile"
    )

    __replace_view('buzz', f"SELECT {get_poly_method} as geom, * FROM ({query[:-1]}) as buzz WHERE buzz.mrate>0")

    db.define_table('buzz',
        Field('geom', 'geometry()'),
        Field('tilename'),
        Field('count', 'integer'),
        Field('mrate', 'double'),
        Field.Virtual('feat_geometry', lambda row: wkt.loads(row['buzz'].geom)),
        migrate = False,
        redefine = True
    )

    result = db(db.buzz).select()

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
            color = colorScaleFader(row.mrate, mycolors)
        )
    ) for row in result], name='internet')

def fetch(minlon, minlat, maxlon, maxlat, zoom, source_name='AGCOM', tags=[]):

    left, bottom, right, top, _ = _get_buffered_bounds(
        minlon, minlat, maxlon, maxlat,
        zoom = zoom, classic = True
    )

    tab = db.polys
    dbset = _geomdbset(tab, left, bottom, right, top,
        source_name=source_name, tags=tags
    )

    _ = lambda nn: f"COALESCE((polys.properties->>'{nn}')::float, 0)"
    downspeeds = ('speed_down', 'speed_do_1', 'speed_do_2',)
    upspeeds = ('speed_up_a', 'speed_up_v', 'speed_up_e',)

    max_download = "GREATEST({}, {}, {})".format(*map(_, downspeeds))
    max_upload = "GREATEST({}, {}, {})".format(*map(_, upspeeds))

    max_download_ = f"LEAST(100, {max_download})/100"
    max_upload_ = f"LEAST(100, {max_upload})/100"

    ftth_cover = "((polys.properties->>'ftth_cover')::float) as ftth_cover"

    ftth = """CASE
    WHEN (polys.properties->>'ftth_cover')::float >= 1 THEN 0.1
    ELSE 0
END"""

    rate = f"0.7*({max_download_})+0.2*({max_upload_})+({ftth}) as rate"

    res = dbset(db.polys.source_id.startswith('100m') & \
        f"0.7*({max_download_})+0.2*({max_upload_})+({ftth})>0"
    ).select(
        db.polys.id,
        db.polys.src_id,
        db.polys.source_id,
        db.polys.geom,
        max_download,
        max_upload,
        ftth_cover,
        rate
    )

    return FeatureCollection([Feature(
        id = row.polys.hashid,
        geometry = row.polys.feat_geometry,
        properties = dict(
            id = row.polys.hashid,
            count = 1,
            mrate = row[rate],
            max_download = row[max_download],
            max_upload = row[max_upload],
            ftth_cover = row[ftth_cover],
            color = colorScaleFader(row[rate], mycolors)
        )
    ) for row in res], name='internet')

if __name__ == '__main__':
    minlon, minlat = 9.1571044921875, 45.49118636890595
    maxlon, maxlat = 9.199333190917969, 45.52078170816289
    # res = fetchtiled(minlon, minlat, maxlon, maxlat, zoom=12, classic=False, source_name='AGCOM')
    res = fetch(minlon, minlat, maxlon, maxlat, zoom=12)
    import pdb; pdb.set_trace()
