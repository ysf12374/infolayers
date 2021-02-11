# -*- coding: utf-8 -*-

AGCOM_DOWNLOAD_URLS = {
    # 100m grid
    "ADSL": "https://maps.agcom.it/arcgis/sharing/rest/content/items/daa86269c6a74265889d9d1582fa079f/data",
    "VDSL": "https://maps.agcom.it/arcgis/sharing/rest/content/items/0e882997b51a49ea8d6144074a2db24b/data",
    "EVDSL": "https://maps.agcom.it/arcgis/sharing/rest/content/items/ab9653dc257543848a4de67f38e342c8/data",
    "FTTH": "https://maps.agcom.it/arcgis/sharing/rest/content/items/1a9a122855a34279af95d7456ad72d29/data"
}

# AGCOM_DOWNLOAD_URLS = {
#     # 1km grid
#     "ADSL": "https://maps.agcom.it/arcgis/sharing/rest/content/items/2c40f3430e184beaa22fff418f9d716d/data",
#     "VDSL": "https://maps.agcom.it/arcgis/sharing/rest/content/items/7a91f6fc6aeb4041bd4a2dfc5a5dab1e/data",
#     "EVDSL": "https://maps.agcom.it/arcgis/sharing/rest/content/items/0cd20aaddfe04ac4bd1902631fc1210c/data",
#     "FTTH_B": "https://maps.agcom.it/arcgis/sharing/rest/content/items/09d55da1c84d4245bfc8522de4cdd919/data"
# }

# try import private settings
try:
    from .settings_private import *
except (ImportError, ModuleNotFoundError):
    pass
