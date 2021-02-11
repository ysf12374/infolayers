# -*- coding: utf-8 -*-

from kilimanjaro.timeformat import prettydate
import datetime
from tqdm import tqdm
import os, inspect

import requests
import shutil
from urllib.request import urlretrieve
import shutil
import geopandas as gp
import pandas as pd
from .import settings
from pathlib import Path
import re
import geojson
import shapely
import pyproj
from shapely.ops import transform
from zipfile import ZipFile
# from geofeather.pygeos import to_geofeather, from_geofeather

# from ..planetstore.populate.io import feat
# from ..planetstore.populate.pgcopy import BulkCopyer
# from ..planetstore.populate.gjson import PolygonCopier
from ..planetstore.populate.io import json as jsonimport_
from ..planetstore.populate.pgcopy import BulkCopyer
from .models import db
from ..common import cache

from pydal.helpers.serializers import serializers
jsondumps = serializers.json

now = lambda : datetime.datetime.now()
here = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
RESOURCES = 'resources'
DEFAULT_DEST = os.path.join(here, RESOURCES)
LINSPIRE_SRS = 'epsg:3035'
SOURCE_NAME = 'AGCOM'

def download_file(url, dest=DEFAULT_DEST):
    """ Courtesy of: https://stackoverflow.com/a/16696317/1039510 """

    with requests.get(url, stream=True) as rr:
        rr.raise_for_status()
        info = rr.headers['Content-Disposition']
        file_name = re.search(r"^.*filename=\"(.*)\".*$", info).group(1)
        file_size = int(re.search(r"^.*size=(.*).*$", info).group(1))
        etag = rr.headers["ETag"]
        dest_dir = os.path.join(dest, str(etag))
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        dest_file = Path(os.path.join(dest_dir, file_name))
        if not dest_file.is_file():
            with dest_file.open('wb') as ff:
                for chunk in tqdm(rr.iter_content(chunk_size=None)):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    if chunk: ff.write(chunk)

    return str(dest_file), etag,

class Transformer(object):
    """docstring for Transformer."""

    wgs84 = pyproj.CRS('EPSG:4326')

    def __init__(self, srs):
        """
        src @string : EPSG code
        """
        super(Transformer, self).__init__()
        self.crs = pyproj.CRS(srs)
        self.transformer = pyproj.Transformer.from_crs(self.crs, self.wgs84, always_xy=True)
        self.proj = self.transformer.transform
        self.__transform = lambda geom: transform(self.proj, geom)

    def __call__(self, geometry):
        return shapely.geometry.mapping(self.__transform(geometry))

def bbox_from_wgs84_to(srs, bbox):
    project = Transformer(srs)
    _transorm = pyproj.Transformer.from_crs(project.wgs84, project.crs, always_xy=True).transform
    xmin, ymin = _transorm(bbox.west, bbox.south)
    xmax, ymax = _transorm(bbox.east, bbox.north)
    return xmin, ymin, xmax, ymax,


def shape2df_(filename, bbox=None, fasttest=False):

    root, ext = os.path.splitext(filename)
    alt_file = Path(root+".feather")
    if alt_file.is_file():
        df = gp.read_feather(f"{alt_file}")
        if not bbox is None:
            xmin, ymin, xmax, ymax = bbox_from_wgs84_to(df.crs.srs, bbox)
            df = df.cx[xmin:xmax, ymin:ymax]
    elif fasttest:
        df = gp.read_file('zip://'+filename)
        df = df[~(df.geometry.is_empty|df.geometry.isna())]
        df.to_feather(f"{alt_file}")
        if not bbox is None:
            xmin, ymin, xmax, ymax = bbox_from_wgs84_to(df.crs.srs, bbox)
            df = df.cx[xmin:xmax, ymin:ymax]

    elif not bbox is None:
        xmin, ymin, xmax, ymax = bbox_from_wgs84_to(LINSPIRE_SRS, bbox)
        df = gp.read_file('zip://'+filename, bbox=(xmin, ymin, xmax, ymax))
        df = df[~(df.geometry.is_empty|df.geometry.isna())]

    else:
        df = gp.read_file('zip://'+filename)
        df = df[~(df.geometry.is_empty|df.geometry.isna())]

    return df

# def shape2df(filename, limits=None):
#     df_ = gp.read_file('zip://'+filename)
#     df = df_[~df_.geometry.is_empty]
#     project = Transformer(df.crs.srs)
#
#     if not limits is None:
#
#         _transorm = pyproj.Transformer.from_crs(project.wgs84, project.crs, always_xy=True).transform
#         xmin, ymin = _transorm(limits.west, limits.south)
#         xmax, ymax = _transorm(limits.east, limits.north)
#         df = df.cx[xmin:xmax, ymin:ymax]
#
#     return df


def split_shape(df):

    gcolumns = {'geometry', 'shape_Leng', 'shape_Area'}

    properties = pd.DataFrame(df.drop(columns=gcolumns))

    geometries = df.drop(columns=filter(
        lambda col: (not col in gcolumns.union({'grid_id_10', 'grid_id_1k'})),
        df.columns
    ))

    return geometries, properties,

def import_geoms(gdf):

    project = Transformer(gdf.crs.srs)

    if 'grid_id_10' in gdf.columns:
        grid_id_key = 'grid_id_10'
        props = lambda grid_id_10, geometry, **kwargs: (grid_id_10, geometry, kwargs,)
    elif 'grid_id_1k' in gdf.columns:
        grid_id_key = 'grid_id_1k'
        props = lambda grid_id_1k, geometry, **kwargs: (grid_id_1k, geometry, kwargs,)
    else:
        raise NotImplementedError()

    def minimizedf():
        grid_ids = db(
            (db.info.source_name==SOURCE_NAME) & \
            (db.info.source_id.belongs(gdf[grid_id_key].values))
        ).select(
            db.info.source_id,
            distinct=True,
        ).group_by_value(db.info.source_id)
        return gdf[~gdf[grid_id_key].isin(grid_ids)]

    def to_feat_(nfo):
        _, rec = nfo
        id, geom_, properties = props(**rec)
        feat = geojson.Feature(
            id = id,
            geometry = project(geom_),
            properties = properties
        )
        return feat

    dfmin = minimizedf()
    if dfmin.geometry.size:
        collection = geojson.FeatureCollection(map(to_feat_, dfmin.iterrows()))
        jsonimport_(collection, source_name=SOURCE_NAME, copy=True)

def import_props(df, broadband_source_id):
    """ """
    if 'grid_id_10' in df.columns:
        grid_id_key = 'grid_id_10'
        props = lambda grid_id_10, **kwargs: (grid_id_10, kwargs,)
    elif 'grid_id_1k' in df.columns:
        grid_id_key = 'grid_id_1k'
        props = lambda grid_id_1k, **kwargs: (grid_id_1k, kwargs,)
    else:
        raise NotImplementedError()

    with BulkCopyer(db.broadband) as copyer:
        for _, rec in df.iterrows():
            grid_id_value, kw = props(**rec)
            copyer.writerow(dict(
                info = jsondumps(kw),
                broadband_source_id=broadband_source_id,
                grid_cell_id = grid_id_value
            ))

if __name__ == '__main__':

    from ..planetstore.tools.tilesets import tile_by_dim
    import mercantile as mc

    Milan = 9.1905000, 45.4668000,

    mytile = tile_by_dim(*Milan, 20000, classic=True)

    from mercantile import LngLatBbox
    limits1 = LngLatBbox(7.4432373046875, 44.33956524809713, 9.481201171875, 45.686995566120395)
    limits2 = mc.bounds(mytile)
    limits3 = LngLatBbox(9.026641845703123, 45.35021505925909, 9.3988037109375, 45.615958580368364)

    for ii, _ in enumerate(settings.AGCOM_DOWNLOAD_URLS.items()):
        name, url = _
        file, etag = download_file(url)
        broadband_source = db.broadband_source(etag=etag)
        if broadband_source is None:
            broadband_id = db.broadband_source.insert(broadband=name, etag=etag)

            gdf, df = split_shape(shape2df_(file, bbox=limits1, fasttest=True))
            import_geoms(gdf)
            import_props(df, broadband_id)


    #     importdf(file, limits=limits3, copy=False)
    #
    # start = now()
    # db.commit()
    # print(prettydate(start))
