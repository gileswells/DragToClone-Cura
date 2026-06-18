# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from . import DragToClone


def getMetaData():
    return {}


def register(app):
    return {"extension": DragToClone.DragToClone()}
