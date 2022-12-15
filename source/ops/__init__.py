import bpy
from . import node_link


def register():
    node_link.register()


def unregister():
    node_link.unregister()