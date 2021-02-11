# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")
from . import settings
if not (hasattr(settings, 'SETUP_MODE') and settings.SETUP_MODE):
    # by importing db you expose it to the _dashboard/dbadmin
    from .models import db

    # by importing controllers you expose the actions defined in it
    from . import controllers
    from .scrapedata.restate import controllers
    from .xdsl import controllers
    from .attivita import controllers
    from .attraction import controllers

from py4web import action

@action("index")
@action.uses("index.html")
def index():
    return dict()

# optional parameters
__version__ = "0.1.0"
__author__ = "Manuele Pesenti <m.pesenti@colouree.com>"
__license__ = "All rights reserved"