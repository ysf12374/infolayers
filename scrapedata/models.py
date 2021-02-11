# -*- coding: utf-8 -*-

from .common import db

from py4web import Field
from pydal.validators import *
import datetime

now = lambda : datetime.datetime.utcnow()

# RESTATE

db.define_table("restate",
    Field("info_id", "reference info"),
    Field("stdup", "double", label="Standardized unit price")
)

db.define_table('stats',
    Field("cname", label="Column name", required=True, unique=True, notnull=True),
    Field("stats", "json"),
    Field('modified_on', 'datetime',
        update=now, default=now,
        writable=False, readable=False,
        # label=T('Modified On')
    ),
)
