import bpy
from bpy.types import AddonPreferences
from bpy.props import *
import rna_keymap_ui
from .source.utils.keymaps import addon_keymaps


class NL_AP_preference(AddonPreferences):

    bl_idname = __package__.partition('.')[0]

    socket_offset : FloatProperty(
        name = 'Point offset X',
        min = 0, max = 50,
        default = 0,
    )

    draw_text : BoolProperty(
        name='Draw Text',
        default=True
    )

    color_text : BoolProperty(
        name='Colored Text',
        default=True
    )

    draw_marker : BoolProperty(
        name='Draw Marker',
        default=True
    )

    colored_marker : BoolProperty(
        name='Colored Marker',
        default=True
    )

    draw_socket : BoolProperty(
        name='Draw Points',
        default=True
    )

    colored_socket : BoolProperty(
        name='Colored Points',
        default=True
    )

    draw_line : BoolProperty(
        name='Draw Line',
        default=True
    )

    colored_line : BoolProperty(
        name='Colored Line',
        default=True
    )

    draw_socket_area : BoolProperty(
        name='Draw Socket Area',
        default=False
    )

    colored_socket_area : BoolProperty(
        name='Colored Socket Area',
        default=True
    )

    font_style : EnumProperty(
        name='Text Style',
        items=(
            ('CLASSIC', 'Classic', ''),
            ('SIMPLIFIED', 'Simplified', ''),
            ('TEXT', 'Only text', '')
        ),
        default='SIMPLIFIED',
    )

    draw_wire : BoolProperty(
        name='Always draw line',
        default=True
    )

    one_choice_skip : BoolProperty(
        name='One Choise to skip',
        description='A',
        default=False
    )

    menu_style : EnumProperty(
        name='Mixer Menu Style',
        items=(
            ('PIE', 'Pie', ''),
            ('LIST', 'List', '')
        ),
        default='PIE',
    )

    preview_live : BoolProperty(
        name='Live Preview',
        default=True
    )

    preview_geometry_node : BoolProperty(
        name='Preview in Geometry nodes',
        default=True
    )

    def draw(self,context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col0 = layout.column()
        box = col0.box()
        col1 = box.column()
        col1.label(text='Draw stiings')
        col1.prop(self,'socket_offset')
        row = col1.row()
        row.prop(self,'draw_text')
        row.prop(self,'color_text')
        row = col1.row()
        row.prop(self,'draw_marker')
        row.prop(self,'colored_marker')
        row = col1.row()
        row.prop(self,'draw_socket')
        row.prop(self,'colored_socket')
        row = col1.row()
        row.prop(self,'draw_line')
        row.prop(self,'colored_line')
        row = col1.row()
        row.prop(self,'draw_socket_area')
        row.prop(self,'colored_socket_area')
        col1.prop(self,'font_style')
        col1.prop(self,'draw_wire')
        box = col0.box()
        col1 = box.column()
        col1.label(text='Mixer settings')
        col1.prop(self,'menu_style')
        col1.prop(self,'one_choice_skip')
        box = col0.box()
        col1 = box.column()
        col1.label(text='Preview settings')
        col1.prop(self,'preview_live')
        col1.prop(self,'preview_geometry_node')

        box = col0.box()
        col = box.column()
        col.label(text='Keymaps')
        kc = bpy.context.window_manager.keyconfigs.user
        for addon_km, item in addon_keymaps:
            km = kc.keymaps[addon_km.name]
            kmi = km.keymap_items[item.idname]
            rna_keymap_ui.draw_kmi(kc.keymaps, kc, km, kmi, col, 0)
