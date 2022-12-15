import bpy
from . import keymaps


def register():
    keymaps.register()


def unregister():
    keymaps.unregister()