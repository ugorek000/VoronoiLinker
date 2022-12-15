import bpy
from . import menus


def register():
    menus.register()


def unregister():
    menus.unregister()