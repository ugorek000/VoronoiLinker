import bpy
from bpy.types import Menu
from ..utils.node_link import *


class NL_MT_node_mixer(Menu):
    bl_label = ''

    def draw(self,context):
        who = self.layout.menu_pie() if GetDrawSettings('menu_style')=='PIE' else self.layout
        who.label(text=VMMapDictUserSkName.get(mixerSkTyp[0],mixerSkTyp[0].capitalize()))
        for li in VMMapDictMain[context.space_data.tree_type][mixerSkTyp[0]]:
            who.operator('nl.node_link_mix',text=VMMapDictMixersDefs[li][2]).who=li


classes = [
    NL_MT_node_mixer,
]


register, unregister = bpy.utils.register_classes_factory(classes)
