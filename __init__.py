bl_info = {
    'name': 'Node Link',
    'author': 'ugorek#6434, Karan#5503',
    'description': 'Quick Node Linker',
    'blender': (3, 0, 0),
    'version': (1, 6, 0),
    'category': 'Node',
    'location': 'Node Editor > Ctrl + LMB (Default)',
    'support': 'COMMUNITY',
    'warning': '',
    'doc_url': 'https://github.com/ugorek000/NL_OT_node_link/blob/main/README.md',
    'tracker_url': 'https://github.com/ugorek000/NL_OT_node_link/issues'
}

import bpy
from . import source
from . preferences import NL_AP_preference


def register():
    source.register()
    bpy.utils.register_class(NL_AP_preference)


def unregister():
    source.unregister()
    bpy.utils.unregister_class(NL_AP_preference)