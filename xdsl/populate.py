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
from .import settings
from pathlib import Path
import re
import geojson
import shapely
import pyproj
from shapely.ops import transform

# from ..planetstore.populate.io import feat
# from ..planetstore.populate.pgcopy import BulkCopyer
# from ..planetstore.populate.gjson import PolygonCopier
from ..planetstore.populate.io import json as jsonimport
from .models import db

now = lambda : datetime.datetime.now()
here = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
RESOURCES = 'resources'
DEFAULT_DEST = os.path.join(here, RESOURCES)

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

    return str(dest_file)

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


def df2features(filename, limits=None):
    df_ = gp.read_file('zip://'+filename)
    df = df_[~df_.geometry.is_empty]
    project = Transformer(df.crs.srs)

    if not limits is None:

        _transorm = pyproj.Transformer.from_crs(project.wgs84, project.crs, always_xy=True).transform
        xmin, ymin = _transorm(limits.west, limits.south)
        xmax, ymax = _transorm(limits.east, limits.north)
        df = df.cx[xmin:xmax, ymin:ymax]

    if 'grid_id_10' in df.columns:
        _ = lambda grid_id_10, geometry, **kwargs: (grid_id_10, geometry, kwargs,)
    elif 'grid_id_1k' in df.columns:
        _ = lambda grid_id_1k, geometry, **kwargs: (grid_id_1k, geometry, kwargs,)
    else:
        raise NotImplementedError()

    def allFeatures():
        for nfo in tqdm(df.iterrows(), total=df.geometry.size, desc=filename.split('/')[-1].split("_")[3]):
            pid, rec = nfo
            id, geom_, properties = _(**rec)
            feat = geojson.Feature(
                id = id,
                geometry = project(geom_),
                properties = properties
            )
            yield feat
    return allFeatures(), df.geometry.size

def importdf(filename, limits=None, copy=False):
    features_, size = df2features(filename, limits=limits)
    collection = geojson.FeatureCollection(features_, length=size)
    jsonimport(collection, source_name='AGCOM', copy=copy)

def importdf2(filename, limits=None, copy=False):

    features_, size = df2features(filename, limits=limits)
    # collection = geojson.FeatureCollection(features, length=size)
    features, properties = [], []
    # for feat_, properties_ in features:
    #     features.append(feat_)
    #     properties.append(properties_)
    source_name = 'AGCOM'
    pcopier = PolygonCopier(db, source_name)
    with BulkCopyer(db.connection_info) as copyer:

        for feat_, properties_ in tqdm(features_, desc='old'):
            poly = db.info(source_id=feat_.id, source_name=source_name)
            if poly is None:
                features.append(feat_)
                properties.append(properties_)
                # poly_id = feat(feat_, source_name=source_name, copy=True)
            else:
                poly_id = poly.id
                copyer.writerow(dict(info=properties, info_id=poly_id, ))
        for info_id in tqdm(pcopier.parse_(features), desc='new'):
            copyer.writerow(dict(info=properties, info_id=info_id))

    # jsonimport(collection, source_name='AGCOM', copy=copy)

    # for feat_ in df2features(filename, limits=limits):
    #
    #     res = feat(feat_, source_name="AGCOM", xcc    =True)

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
        file = download_file(url)
        importdf(file, limits=limits3, copy=False)

    start = now()
    db.commit()
    print(prettydate(start))
