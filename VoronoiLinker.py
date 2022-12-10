### BEGIN LICENSE BLOCK
# I don't understand about licenses.
# Do what you want with it.
### END LICENSE BLOCK
bl_info = {'name':'Voronoi Linker','author':'ugorek','version':(1,1,4),'blender':(3,3,1), #09.12.2022
        'description':'Simplification of create node links.','location':'Node Editor > Alt + RMB','warning':'','category':'Node',
        'wiki_url':'https://github.com/ugorek000/VoronoiLinker/blob/main/README.md','tracker_url':'https://github.com/ugorek000/VoronoiLinker/issues'}

import bpy, bgl, blf, gpu; from gpu_extras.batch import batch_for_shader
from mathutils import Vector; from math import pi, sin, cos, tan, asin, acos, atan, atan2, sqrt, inf, copysign

def uiScale(): return bpy.context.preferences.system.dpi*bpy.context.preferences.system.pixel_size/72
def PosViewToReg(x,y): return bpy.context.region.view2d.view_to_region(x,y,clip=False)
shader = [None,None]; uiFac = [1.0]
def DrawWay(vtxs,vcol,siz):
    bgl.glEnable(bgl.GL_BLEND); bgl.glEnable(bgl.GL_LINE_SMOOTH); shader[0].bind();
    bgl.glLineWidth(siz); batch_for_shader(shader[0],'LINE_STRIP',{'pos':vtxs,'color':vcol}).draw(shader[0])
def DrawArea(vtxs,col):
    bgl.glEnable(bgl.GL_BLEND); bgl.glEnable(bgl.GL_LINE_SMOOTH); shader[1].bind();
    shader[1].uniform_float('color',col); batch_for_shader(shader[1],'TRI_FAN',{'pos':vtxs}).draw(shader[1])
def DrawLine(ps1,ps2,sz=1,cl=(1.0,1.0,1.0,0.75),fs=[0,0]): DrawWay(((ps1[0]+fs[0],ps1[1]+fs[1]),(ps2[0]+fs[0],ps2[1]+fs[1])),(cl,cl),sz)
def DrawCircleOuter(pos,rd,siz=1,col=(1.0,1.0,1.0,0.75),resolution=16):
    vtxs = []; vcol = []
    for cyc in range(resolution+1): vtxs.append((rd*cos(cyc*2*pi/resolution)+pos[0],rd*sin(cyc*2*pi/resolution)+pos[1])); vcol.append(col)
    DrawWay(vtxs,vcol,siz)
def DrawCircle(pos,rd,col=(1.0,1.0,1.0,0.75),resl=16): DrawArea([(rd*cos(i*2*pi/resl)+pos[0],rd*sin(i*2*pi/resl)+pos[1]) for i in range(resl)],col)
def DrawWidePoint(pos,rd):
    rd = sqrt(rd*rd+10); cols = [(0.5,0.5,0.5,0.4),(0.5,0.5,0.5,0.4),(1.0,1.0,1.0,1.0)]; DrawCircle(pos,rd+3,cols[0]); DrawCircle(pos,rd,cols[1]); DrawCircle(pos,rd/1.5,cols[2])
def DrawRectangle(ps1,ps2,cl): DrawArea([(ps1[0],ps1[1]),(ps2[0],ps1[1]),(ps2[0],ps2[1]),(ps1[0],ps2[1])],cl)
def DrawRectangleOnSocket(context,sk,stEn,col=(1.0,1.0,1.0,0.075)):
    loc = RecrGetNodeFinalLoc(sk.node).copy()*uiFac[0]; pos1 = PosViewToReg(loc.x,stEn[0]*uiFac[0])
    pos2 = PosViewToReg(loc.x+sk.node.dimensions.x,stEn[1]*uiFac[0]); DrawRectangle(pos1,pos2,col)
fontId = [0]; where = [None]
def VoronoiLinkerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    def MucDrawText(pos,ofs,Sk):
        try: skCol = Sk.draw_color(context,Sk.node)
        except: skCol = (1,0,0,1)
        txt = Sk.name if Sk.bl_idname!='NodeSocketVirtual' else 'Virtual'; pos = [pos[0]-(len(txt)*15+5)*(ofs[0]<0),pos[1]]; pw = 1/1.975
        pos1 = [pos[0]+ofs[0]-2,pos[1]+ofs[1]-8]; pos2 = [pos[0]+ofs[0]+len(txt)*15+2,pos[1]+ofs[1]+21]; list = [.4,.55,.8,.9,1]; uh = 1/len(list)*29
        for cyc in range(len(list)): DrawRectangle([pos1[0],pos1[1]+cyc*uh],[pos2[0],pos1[1]+cyc*uh+uh],(skCol[0]/2,skCol[1]/2,skCol[2]/2,list[cyc]))
        col = (skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1)
        DrawLine(pos1,[pos2[0],pos1[1]],1,col); DrawLine([pos2[0],pos1[1]],pos2,1,col); DrawLine(pos2,[pos1[0],pos2[1]],1,col); DrawLine([pos1[0],pos2[1]],pos1,1,col)
        col = (col[0],col[1],col[2],.375); thS = 2
        DrawLine(pos1,[pos2[0],pos1[1]],1,col,[0,-thS]); DrawLine([pos2[0],pos1[1]],pos2,1,col,[+thS,0])
        DrawLine(pos2,[pos1[0],pos2[1]],1,col,[0,+thS]); DrawLine([pos1[0],pos2[1]],pos1,1,col,[-thS,0])
        DrawLine([pos1[0]-thS,pos1[1]],[pos1[0],pos1[1]-thS],1,col); DrawLine([pos2[0]+thS,pos1[1]],[pos2[0],pos1[1]-thS],1,col)
        DrawLine([pos2[0]+thS,pos2[1]],[pos2[0],pos2[1]+thS],1,col); DrawLine([pos1[0]-thS,pos2[1]],[pos1[0],pos2[1]+thS],1,col)
        blf.position(fontId[0],pos[0]+ofs[0],pos[1]+ofs[1],0); blf.size(fontId[0],28,72); blf.color(fontId[0],skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1.0); blf.draw(fontId[0],txt)
        return len(txt)*15
    mousePos = context.space_data.cursor_location*uiFac[0]; mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y)
    def MucDrawWP(loc,offsetx): pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6,loc.y)[0]-pos[0]; DrawWidePoint(pos,rd); return pos
    def MucDrawIsLinked(loc,offset,skCol):
        vec = PosViewToReg(loc.x,loc.y); gc = 0.65; col1 = (0,0,0,0.5); col2 = (gc,gc,gc,max(max(skCol[0],skCol[1]),skCol[2])*.9); col3 = (skCol[0],skCol[1],skCol[2],.925)
        DrawCircleOuter([vec[0]+offset+1.5,vec[1]+3.5],9.0,3.0,col1); DrawCircleOuter([vec[0]+offset-3.5,vec[1]-5],9.0,3.0,col1)
        DrawCircleOuter([vec[0]+offset,vec[1]+5],9.0,3.0,col2); DrawCircleOuter([vec[0]+offset-5,vec[1]-3.5],9.0,3.0,col2)
        DrawCircleOuter([vec[0]+offset,vec[1]+5],9.0,1.0,col3); DrawCircleOuter([vec[0]+offset-5,vec[1]-3.5],9.0,1.0,col3)
    def MucDrawSk(Sk,lh):
        txtlen = MucDrawText(mouseRegionPs,[-20*(Sk.is_output*2-1),-5],Sk)
        if Sk.is_linked: MucDrawIsLinked(mousePos,(-txtlen-48)*(Sk.is_output*2-1),Sk.draw_color(context,Sk.node))
    if (sender.sockOutSk==None): MucDrawWP(mousePos,-15); MucDrawWP(mousePos,+15)
    elif (sender.sockOutSk!=None)and(sender.sockInSk==None):
        MucDrawWP(sender.sockOutPs*uiFac[0],+20); MucDrawWP(mousePos,0);
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH); MucDrawSk(sender.sockOutSk,sender.sockOutLH)
    else:
        DrawLine(MucDrawWP(sender.sockOutPs*uiFac[0],+20),MucDrawWP(sender.sockInPs*uiFac[0],-20),1,(1.0,1.0,1.0,0.4))
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH); DrawRectangleOnSocket(context,sender.sockInSk,sender.sockInLH);
        MucDrawSk(sender.sockOutSk,sender.sockOutLH); MucDrawSk(sender.sockInSk,sender.sockInLH)

def RecrGetNodeFinalLoc(node): return node.location if node.parent==None else node.location+RecrGetNodeFinalLoc(node.parent)
def GetNearestNodeInRegionMouse(context):
    goalNd, goalPs, minLen = None, None, inf
    def ToSign(vec2): return Vector((copysign(1,vec2[0]),copysign(1,vec2[1])))
    mousePs = context.space_data.cursor_location; nodes = context.space_data.edit_tree.nodes
    for nd in nodes:
        if (nd.bl_idname!='NodeFrame')and((nd.hide==False)or(nd.type=='REROUTE')):
            locNd = RecrGetNodeFinalLoc(nd)
            sizNd = Vector((4,4)) if nd.bl_idname=='NodeReroute' else nd.dimensions/uiFac[0]
            locNd = locNd-sizNd/2 if nd.bl_idname=='NodeReroute' else locNd-Vector((0,sizNd[1]))
            fieldUV = mousePs-(locNd+sizNd/2); fieldXY = Vector((abs(fieldUV.x),abs(fieldUV.y)))-sizNd/2
            fieldXY = Vector((max(fieldXY.x,0),max(fieldXY.y,0))); fieldL = fieldXY.length
            if fieldL<minLen: minLen = fieldL; goalNd = nd; goalPs = mousePs-fieldXY*ToSign(fieldUV)
    return goalNd, goalPs, minLen
SkPerms = ['VALUE','RGBA','VECTOR','INT','BOOLEAN']
def GetNearestSocketInRegionMouse(context,getOut,skOut):
    mousePs = context.space_data.cursor_location; nd = GetNearestNodeInRegionMouse(context)[0]; locNd = RecrGetNodeFinalLoc(nd)
    if nd.bl_idname=='NodeReroute': return nd.outputs[0] if getOut else nd.inputs[0], nd.location, Vector(mousePs-nd.location).length, (-1,-1)
    def MucGet(who,getOut):
        goalSk = None; goalPs = None; minLen = inf; skHigLigHei = (0,0); ndDim = nd.dimensions/uiFac[0]
        if getOut:skLoc = Vector((locNd.x+ndDim[0],locNd.y-35))
        else:skLoc = Vector((locNd.x,locNd.y-ndDim[1]+16))
        for wh in who:
            if (wh.enabled)and(wh.hide==False):
                muv = 0; tgl = False
                if (getOut==False)and(wh.type=='VECTOR')and(wh.is_linked==False)and(wh.hide_value==False):
                    if str(wh.bl_rna).find('VectorDirection')!=-1: skLoc[1] += 20*2; muv = 2
                    elif ((nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))==False)or((wh.name in ('Subsurface Radius','Radius'))==False): skLoc[1] += 30*2; muv = 3
                if skOut!=None:
                    tgl = (skOut.bl_idname=='NodeSocketVirtual')or(wh.bl_idname=='NodeSocketVirtual')
                    tgl = (tgl)or((skOut.type in SkPerms)and(wh.type in SkPerms))or(skOut.bl_idname==wh.bl_idname)
                if getOut or tgl:
                    fieldXY = mousePs-skLoc; fieldL = fieldXY.length
                    if fieldL<minLen: minLen = fieldL; goalSk = wh; goalPs = skLoc.copy(); skHigLigHei = (goalPs[1]-11-muv*20,goalPs[1]+11+max(len(wh.links)-2,0)*5)
                skLoc[1] += 22*(1-getOut*2)
        return goalSk, goalPs, minLen, skHigLigHei
    return MucGet(nd.outputs if getOut else reversed(nd.inputs),getOut)
class VoronoiLinker(bpy.types.Operator):
    bl_idname = 'node.voronoi_linker'; bl_label = 'Voronoi Linker'; bl_options = {'UNDO'}
    def MucAssign(sender,context):
        muc = GetNearestSocketInRegionMouse(context,False,sender.sockOutSk); sender.sockInSk = muc[0]; sender.sockInPs = muc[1]; sender.sockInLH = muc[3]
        if (sender.sockOutSk!=None)and(sender.sockInSk!=None)and(sender.sockOutSk.node==sender.sockInSk.node):
            sender.sockInSk = None; sender.sockInPs = None; sender.sockInLH = None
        if (sender.sockOutSk)and(sender.sockOutSk.is_linked):
            for lk in sender.sockOutSk.links:
                if lk.to_socket==sender.sockInSk: sender.sockInSk = None; sender.sockInPs = None; sender.sockInLH = None
    def modal(self,context,event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE': VoronoiLinker.MucAssign(self,context)
            case 'RIGHTMOUSE'|'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOutSk!=None)and(self.sockInSk!=None):
                    tree = context.space_data.edit_tree
                    try: tree.links.new(self.sockOutSk,self.sockInSk)
                    except:pass #NodeSocketUndefined
                    if self.sockInSk.is_multi_input: #Если мультиинпут, то спец-манёвр
                        skLinks = []
                        for lk in self.sockInSk.links: skLinks.append((lk.from_socket,lk.to_socket)); tree.links.remove(lk)
                        if self.sockOutSk.bl_idname=='NodeSocketVirtual': self.sockOutSk = self.sockOutSk.node.outputs[len(self.sockOutSk.node.outputs)-2]
                        tree.links.new(self.sockOutSk,self.sockInSk)
                        for cyc in range(0,len(skLinks)-1): tree.links.new(skLinks[cyc][0],skLinks[cyc][1])
                    return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self,context,event):
        context.area.tag_redraw()
        if (context.area.type!='NODE_EDITOR')or(context.space_data.edit_tree==None): return {'CANCELLED'}
        else:
            muc = GetNearestSocketInRegionMouse(context,True,None); self.sockOutSk = muc[0]; self.sockOutPs = muc[1]; self.sockOutLH = muc[3]
            VoronoiLinker.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiLinkerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

addon_keymaps = []
def register():
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor',space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(VoronoiLinker.bl_idname,type='RIGHTMOUSE',value='PRESS',alt=True,head=True)
    bpy.utils.register_class(VoronoiLinker); addon_keymaps.append((km,kmi))
    try: fontId[0] = blf.load(r'C:\Windows\Fonts\consola.ttf')
    except:pass
def unregister():
    for km,kmi in addon_keymaps: km.keymap_items.remove(kmi)
    bpy.utils.unregister_class(VoronoiLinker); addon_keymaps.clear()

if __name__=='__main__': register()