# -*- coding: utf-8 -*-

from .models import db

from tqdm import tqdm
from sklearn import preprocessing
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
import mercantile as mc
from geojson import Feature, FeatureCollection
from json import loads
from hashids import Hashids

def standardize_():

    dbset = db(
        (db.points.source_name == 'immobiliare.it') & \
        # A first very raw data cleaning before the real outlier detection
        "(points.properties->>'price:€')::integer > 10000" & \
        "(points.properties->>'surface:m²')::integer > 0"
    )

    price = "(points.properties->>'price:€')::integer"
    surface = "(points.properties->>'surface:m²')::integer"
    unit_price = "(points.properties->>'price:€')::integer/(points.properties->>'surface:m²')::integer"
    res = dbset.select(
        db.points.id,
        price,
        surface,
        unit_price,
        orderby = unit_price
    )

    assert len(res)>0

    df = pd.DataFrame(map(lambda r: dict(
        id = r.points.id,
        uprice = r[unit_price],
        price = r[price],
        surface = r[surface],
    ), res))
    # uprices = df['uprice'].values
    # centroids, avg_distance = kmeans(uprices, 4)
    # groups, cdist = vq(uprices, centroids)

    pca = PCA(n_components=1)
    pca.fit(df[['price','surface']].values)
    df['pca'] = pca.transform(df[['price','surface']].values)

    # Outlier detection
    clf = IsolationForest(n_estimators=50)
    clf.fit(df)
    df['xlier'] = clf.predict(df)
    # df['std'] = None

    xdf = df[df['xlier'].apply(lambda x: x==1)]

    # centroids, avg_distance = kmeans(xdf.alchemy.values, 2)
    # groups, cdist = vq(xdf.alchemy.values, centroids)
    # import pdb; pdb.set_trace()
    # plt.scatter(xdf.uprice.values, xdf.id.values, c=groups)

    # stdzed_values = preprocessing.scale(xdf['uprice'].values)
    # for rid, std in tqdm(zip(xdf.index.values, stdzed_values)):
    #     xdf.at[rid, 'standardized'] = std
    # xdf.sort_values('standardized')

    stdzed_values = preprocessing.minmax_scale(xdf['uprice'].values)
    for rid, std in tqdm(zip(xdf.index.values, stdzed_values)):
        xdf.at[rid, 'standardized'] = std
    xdf.sort_values('standardized')

    ptot = 10
    nn = len(xdf.index)
    idx_perc = [(nn*ii//ptot-1) for ii in range(1, ptot)]

    up_percentiles = [xdf["uprice"].iloc[0]]
    for ii in idx_perc:
        up_percentiles.append(xdf["uprice"].iloc[ii])
    up_percentiles.append(xdf["uprice"].iloc[-1])
    up_percentiles = list(map(int, up_percentiles))

    cname = "restate_unit_price"
    srow = db.stats(cname=cname)
    stats = dict(percentiles=up_percentiles)
    if srow is None:
        db.stats.insert(
            cname = cname,
            stats = stats
        )
    else:
        srow.update_record(stats = dict(percentiles=up_percentiles))

    rows_by_id = res.group_by_value(db.points.id)

    for ii, nfo in tqdm(enumerate(df.iterrows())):
        index, point = nfo
        if point['xlier']!=-1:
            standardized = xdf.at[index, 'standardized']
            row = db.restate(info_id=point.id)
            if row is None:
                db.restate.insert(
                    info_id = point.id,
                    stdup = standardized
                )
            else:
                row.update_record(stdup = standardized)

if __name__ == '__main__':
    standardize_()
    db.commit()
