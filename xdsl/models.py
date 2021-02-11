# -*- coding: utf-8 -*-

from ..common import db, T
from py4web import Field
import datetime

now = lambda : datetime.datetime.utcnow()

db.define_table("broadband_source",
    Field('broadband', label="adsl, vdsl, evdsl, ftth"),
    Field('etag'),
    Field('created_on', 'datetime',
        default = now,
        writable=False, readable=False,
        label = T('Created On')
    ),
    Field('modified_on', 'datetime',
        update=now, default=now,
        writable=False, readable=False,
        label=T('Modified On')
    )
)

db.define_table("broadband",
    Field('broadband_source_id', "reference broadband_source"),
    Field('info', 'json'),
    Field('grid_cell_id')
)
