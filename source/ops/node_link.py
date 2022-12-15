import bpy
import contextlib
from bpy.types import Operator
from ..utils.node_link import *

class NL_OT_node_link(Operator):
    bl_label = 'Node Link'
    bl_idname = 'nl.node_link'
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        context.area.tag_redraw()
        if (
            context.area.type != 'NODE_EDITOR'
            or context.space_data.edit_tree is None
        ):
            return {'CANCELLED'}
        muc = GetNearestSocketInRegionMouse(context,True,None)
        self.sockOutSk = muc[0]
        self.sockOutPs = muc[1]
        self.sockOutLH = muc[3]
        NL_OT_node_link.MucAssign(self,context)
        uiFac[0] = uiScale()
        where[0] = context.space_data
        SetFont()
        self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiLinkerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def MucAssign(self, context):
        muc = GetNearestSocketInRegionMouse(context, False, self.sockOutSk)
        self.sockInSk = muc[0]
        self.sockInPs = muc[1]
        self.sockInLH = muc[3]
        if (
            self.sockOutSk != None
            and self.sockInSk != None
            and self.sockOutSk.node == self.sockInSk.node
        ):
            self._extracted_from_MucAssign_4()
        if self.sockOutSk and self.sockOutSk.is_linked:
            for lk in self.sockOutSk.links:
                if lk.to_socket == self.sockInSk:
                    self._extracted_from_MucAssign_4()

    # TODO Rename this here and in `MucAssign`
    def _extracted_from_MucAssign_4(self):
        self.sockInSk = None
        self.sockInPs = None
        self.sockInLH = None

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type:
            if event.type == 'MOUSEMOVE': NL_OT_node_link.MucAssign(self,context)
            if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:
                return self._extracted_from_modal_(event, context)
        return {'RUNNING_MODAL'}

    # TODO Rename this here and in `modal`
    def _extracted_from_modal_(self, event, context):
        bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
        if (
            event.value != 'RELEASE'
            or self.sockOutSk is None
            or self.sockInSk is None
        ):
            return {'CANCELLED'}
        tree = context.space_data.edit_tree
        try: tree.links.new(self.sockOutSk,self.sockInSk)
        except:pass #NodeSocketUndefined
        if self.sockInSk.is_multi_input: #Если мультиинпут, то спец-манёвр
            skLinks = []
            for lk in self.sockInSk.links: skLinks.append((lk.from_socket,lk.to_socket)); tree.links.remove(lk)
            if self.sockOutSk.bl_idname=='NodeSocketVirtual': self.sockOutSk = self.sockOutSk.node.outputs[len(self.sockOutSk.node.outputs)-2]
            tree.links.new(self.sockOutSk,self.sockInSk)
            for cyc in range(len(skLinks)-1): tree.links.new(skLinks[cyc][0],skLinks[cyc][1])
        return {'FINISHED'}


class NL_OT_node_mix(Operator):
    bl_label = 'Node Mix'
    bl_idname = 'nl.node_mix'
    bl_options = {'UNDO'}

    def MucAssign(self, context):
        muc = GetNearestSocketInRegionMouse(context, True, self.sockOut1Sk)
        self.sockOut2Sk = muc[0]
        self.sockOut2Ps = muc[1]
        self.sockOut2LH = muc[3]
        if (
            self.sockOut1Sk != None
            and self.sockOut2Sk != None
            and self.sockOut1Sk == self.sockOut2Sk
        ):
            self.sockOut2Sk = None
            self.sockOut2Ps = None

    def invoke(self, context, event):
        context.area.tag_redraw()
        if (
            context.area.type != 'NODE_EDITOR'
            or context.space_data.edit_tree is None
        ):
            return {'CANCELLED'}
        muc = GetNearestSocketInRegionMouse(context,True,None)
        self.sockOut1Sk = muc[0]
        self.sockOut1Ps = muc[1]
        self.sockOut1LH = muc[3]
        NL_OT_node_mix.MucAssign(self,context)
        uiFac[0] = uiScale()
        where[0] = context.space_data
        SetFont()
        self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiMixerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self,context,event):
        context.area.tag_redraw()
        if event.type:
            if event.type == 'MOUSEMOVE': NL_OT_node_mix.MucAssign(self,context)
            if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:
                return self._extracted_from_modal_(event, context)
        return {'RUNNING_MODAL'}

    # TODO Rename this here and in `modal`
    def _extracted_from_modal_(self, event, context):
        bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
        if (
            event.value != 'RELEASE'
            or self.sockOut1Sk is None
            or self.sockOut2Sk is None
        ):
            return {'CANCELLED'}
        mixerSk1[0] = self.sockOut1Sk
        mixerSk2[0] = self.sockOut2Sk
        mixerSkTyp[0] = mixerSk1[0].type if mixerSk1[0].type!='CUSTOM' else mixerSk2[0].type
        with contextlib.suppress(Exception):
            dm = VMMapDictMain[context.space_data.tree_type][mixerSkTyp[0]]
            if len(dm)!=0:
                if GetDrawSettings('one_choice_skip')and(len(dm)==1): DoMix(context,dm[0])
                elif GetDrawSettings('menu_style')=='PIE': bpy.ops.wm.call_menu_pie(name='NL_MT_node_mixer')
                else: bpy.ops.wm.call_menu(name='NL_MT_node_mixer')
        return {'FINISHED'}


class NL_OT_node_link_mix(Operator):
    bl_label = 'Node Link Mix'
    bl_idname = 'nl.node_link_mix'
    bl_options = {'UNDO'}

    who: bpy.props.StringProperty()

    def execute(self,context):
        DoMix(context, self.who)
        return {'FINISHED'}


class NL_OT_node_link_preview(Operator):
    bl_label = 'Node Link Preview'
    bl_idname = 'nl.node_link_preview'
    bl_options = {'UNDO'}

    liveprew = False

    def MucAssign(self, context):
        muc = GetNearestSocketInRegionMouse(context,True,None)
        self.sockOutSk = muc[0]
        self.sockOutPs = muc[1]
        self.sockOutLH = muc[3]
        if self.liveprew and self.sockOutSk != None:
            VoronoiPreviewer_DoPreview(context, self.sockOutSk)

    def invoke(self, context, event):
        if event.type=='RIGHTMOUSE':
            return self._extracted_from_invoke_3(context)
        elif (context.space_data.tree_type!='GeometryNodeTree')or(GetDrawSettings('preview_geometry_node')):
            context.area.tag_redraw()
            self.liveprew = GetDrawSettings('preview_live')
            if (
                context.area.type != 'NODE_EDITOR'
                or context.space_data.edit_tree is None
            ): return {'CANCELLED'}
            else:
                self._extracted_from_invoke_9(context)
        return {'RUNNING_MODAL'}

    # TODO Rename this here and in `invoke`
    def _extracted_from_invoke_9(self, context):
        NL_OT_node_link_preview.MucAssign(self,context)
        uiFac[0] = uiScale()
        where[0] = context.space_data
        SetFont()
        self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiPreviewerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
        context.window_manager.modal_handler_add(self)

    # TODO Rename this here and in `invoke`
    def _extracted_from_invoke_3(self, context):
        nodes = context.space_data.edit_tree.nodes
        nnd = (nodes.get('Voronoi_Anchor') or nodes.new('NodeReroute'))
        nnd.name = 'Voronoi_Anchor'
        nnd.label = 'Voronoi_Anchor'
        nnd.location = context.space_data.cursor_location
        nnd.select = True
        return {'FINISHED'}

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type:
            if event.type == 'MOUSEMOVE':
                NL_OT_node_link_preview.MucAssign(self,context)
            if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOutSk!=None): VoronoiPreviewer_DoPreview(context,self.sockOutSk); return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}


classes = [
    NL_OT_node_link,
    NL_OT_node_mix,
    NL_OT_node_link_mix,
    NL_OT_node_link_preview
]


register, unregister = bpy.utils.register_classes_factory(classes)