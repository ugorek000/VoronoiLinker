import bpy
addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc is not None:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        kmi = km.keymap_items.new('nl.node_link', type='LEFTMOUSE', value='PRESS',shift=False, ctrl=True,alt=False, head=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new('nl.node_mix',type='LEFTMOUSE',value='PRESS',shift=True,ctrl=True,alt=False, head=True)
        addon_keymaps.append((km,kmi))
        # kmi = km.keymap_items.new('nl.node_link_preview',type='LEFTMOUSE',value='PRESS',shift=True,ctrl=True)
        # addon_keymaps.append((km,kmi))
        # kmi = km.keymap_items.new('nl.node_link_preview',type='RIGHTMOUSE',value='PRESS',shift=True,ctrl=True)
        # addon_keymaps.append((km,kmi))


def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is not None:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()