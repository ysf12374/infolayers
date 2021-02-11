# -*- coding: utf-8 -*-

# justr a dummy but useful test

if __name__=='__main__':

    from .optutils.base import Turbo
    from .populate import osm2db, db

    turbo = Turbo()

    lat, lon = 44.403852, 8.944483
    lat,lon=44.913573, 8.614724
    lat,lon=45.464079, 9.185720
    qconditions = [{
        "query": [[{"k": "amenity","v":"school"}],
        [{"k": "amenity","v":"college"}]],
        "distance": 500
    },]

    query = turbo.build_query(
        turbo.optimize_centralized_query(lon, lat,
            qconditions,
            # buffer=buffer
        ),
        # gtypes=gtypes
    )
    data = turbo(query)

    osm2db(data.nodes, data.ways, data.relations,copy=False)
    db.commit()