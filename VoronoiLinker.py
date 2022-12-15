### BEGIN LICENSE BLOCK
# I don't understand about licenses.
# Do what you want with it.
### END LICENSE BLOCK
bl_info = {'name':'Voronoi Linker','author':'ugorek','version':(1,5,2),'blender':(3,4,0), #15.12.2022
        'description':'Simplification of create node links.','location':'Node Editor','warning':'','category':'Node',
        'wiki_url':'https://github.com/ugorek000/VoronoiLinker/blob/main/README.md','tracker_url':'https://github.com/ugorek000/VoronoiLinker/issues'}

import bpy, bgl, blf, gpu; from gpu_extras.batch import batch_for_shader
from mathutils import Vector; from math import pi, sin, cos, tan, asin, acos, atan, atan2, sqrt, inf, copysign

def uiScale(): return bpy.context.preferences.system.dpi*bpy.context.preferences.system.pixel_size/72
def PosViewToReg(x,y): return bpy.context.region.view2d.view_to_region(x,y,clip=False)
shader = [None,None]; uiFac = [1.0]
def DrawWay(vtxs,vcol,siz):
    bgl.glEnable(bgl.GL_BLEND); bgl.glEnable(bgl.GL_LINE_SMOOTH); shader[0].bind()
    bgl.glLineWidth(siz); batch_for_shader(shader[0],'LINE_STRIP',{'pos':vtxs,'color':vcol}).draw(shader[0])
def DrawAreaFan(vtxs,col):
    bgl.glEnable(bgl.GL_BLEND); bgl.glEnable(bgl.GL_POLYGON_SMOOTH); shader[1].bind()
    shader[1].uniform_float('color',col); batch_for_shader(shader[1],'TRI_FAN',{'pos':vtxs}).draw(shader[1])
def DrawLine(ps1,ps2,sz=1,cl1=(1.0,1.0,1.0,0.75),cl2=(1.0,1.0,1.0,0.75),fs=[0,0]): DrawWay(((ps1[0]+fs[0],ps1[1]+fs[1]),(ps2[0]+fs[0],ps2[1]+fs[1])),(cl1,cl2),sz)
def DrawCircleOuter(pos,rd,siz=1,col=(1.0,1.0,1.0,0.75),resolution=16):
    vtxs = []; vcol = []
    for cyc in range(resolution+1): vtxs.append((rd*cos(cyc*2*pi/resolution)+pos[0],rd*sin(cyc*2*pi/resolution)+pos[1])); vcol.append(col)
    DrawWay(vtxs,vcol,siz)
def DrawCircle(pos,rd,col=(1.0,1.0,1.0,0.75),resl=54): DrawAreaFan([(pos[0],pos[1]),*[(rd*cos(i*2*pi/resl)+pos[0],rd*sin(i*2*pi/resl)+pos[1]) for i in range(resl+1)]],col)
def DrawWidePoint(pos,rd,colfac=Vector((1,1,1,1))):
    col1 = Vector((0.5,0.5,0.5,0.4)); col2 = Vector((0.5,0.5,0.5,0.4)); col3 = Vector((1,1,1,1))
    colfac = colfac if GetDrawSettings('ClPt') else Vector((1,1,1,1)); rd = sqrt(rd*rd+10); rs = GetDrawSettings('PtRs')
    DrawCircle(pos,rd+3,col1*colfac,rs); DrawCircle(pos,rd,col2*colfac,rs); DrawCircle(pos,rd/1.5,col3*colfac,rs)
def DrawRectangle(ps1,ps2,cl): DrawAreaFan([(ps1[0],ps1[1]),(ps2[0],ps1[1]),(ps2[0],ps2[1]),(ps1[0],ps2[1])],cl)
def DrawRectangleOnSocket(context,sk,stEn,colfac=Vector((1,1,1,1))):
    if GetDrawSettings('DrAr')==False: return
    loc = RecrGetNodeFinalLoc(sk.node).copy()*uiFac[0]; pos1 = PosViewToReg(loc.x,stEn[0]*uiFac[0]); colfac = colfac if GetDrawSettings('ClAr') else Vector((1,1,1,1))
    pos2 = PosViewToReg(loc.x+sk.node.dimensions.x,stEn[1]*uiFac[0]); DrawRectangle(pos1,pos2,Vector((1.0,1.0,1.0,0.075))*colfac)
fontId = [0]; where = [None]

def RecrGetNodeFinalLoc(node): return node.location if node.parent==None else node.location+RecrGetNodeFinalLoc(node.parent)
def GetNearestNodeInRegionMouse(context):
    goalNd, goalPs, minLen = None, None, inf
    def ToSign(vec2): return Vector((copysign(1,vec2[0]),copysign(1,vec2[1])))
    mousePs = context.space_data.cursor_location; nodes = context.space_data.edit_tree.nodes
    for nd in nodes:
        if (nd.bl_idname!='NodeFrame')and((nd.hide==False)or(nd.bl_idname=='NodeReroute'))and((nd.name!='Voronoi_Anchor')or(nd.label!='Voronoi_Anchor')):
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
                    # not getOut чтобы не присасываться реальными к виртуальным при миксере (getOut=True)
                    tgl = (skOut.bl_idname=='NodeSocketVirtual')or((wh.bl_idname=='NodeSocketVirtual')and(not getOut))
                    tgl = (tgl)or((skOut.type in SkPerms)and(wh.type in SkPerms))or(skOut.bl_idname==wh.bl_idname)
                    if getOut: tgl = (tgl)and(not((skOut.bl_idname=='NodeSocketVirtual')and(wh.bl_idname=='NodeSocketVirtual'))or(skOut==wh))
                if ((getOut)and(skOut==None))or(tgl): # skOut==None чтобы учитывать влияние tgl при skOut!=None
                    fieldXY = mousePs-skLoc; fieldL = fieldXY.length
                    if fieldL<minLen: minLen = fieldL; goalSk = wh; goalPs = skLoc.copy(); skHigLigHei = (goalPs[1]-11-muv*20,goalPs[1]+11+max(len(wh.links)-2,0)*5)
                skLoc[1] += 22*(1-getOut*2)
        return goalSk, goalPs, minLen, skHigLigHei
    return MucGet(nd.outputs if getOut else reversed(nd.inputs),getOut)
def GetSkCol(Sk): return Sk.draw_color(bpy.context,Sk.node)
def Vec4Pow(vec,pw): return Vector((vec.x**pw,vec.y**pw,vec.z**pw,vec.w**pw))
def GetSkVecCol(Sk,apw): return Vec4Pow(Vector(Sk.draw_color(bpy.context,Sk.node)),1/apw)

def GetDrawSettings(txt): return getattr(bpy.context.preferences.addons['VoronoiLinker' if __name__=='__main__' else __name__].preferences,txt,None)
def SetFont(): fontId[0] = blf.load(r'C:\Windows\Fonts\consola.ttf'); fontId[0] = 0 if fontId[0]==-1 else fontId[0] #for change Blender themes

def DrawText(pos,ofs,Sk):
    if GetDrawSettings('DrTx')==False: return 0
    try: skCol = GetSkCol(Sk)
    except: skCol = (1,0,0,1)
    skCol = skCol if GetDrawSettings('ClTx') else (.9,.9,.9,1)
    txt = Sk.name if Sk.bl_idname!='NodeSocketVirtual' else 'Virtual'; pos = [pos[0]-(len(txt)*15+5)*(ofs[0]<0),pos[1]]; pw = 1/1.975
    pos1 = [pos[0]+ofs[0]-2,pos[1]+ofs[1]-9]; pos2 = [pos[0]+ofs[0]+len(txt)*15+2,pos[1]+ofs[1]+23]; list = [.4,.55,.8,.9,1]; uh = 1/len(list)*32
    if GetDrawSettings('TxSt')=='Classic':
        for cyc in range(len(list)): DrawRectangle([pos1[0],pos1[1]+cyc*uh],[pos2[0],pos1[1]+cyc*uh+uh],(skCol[0]/2,skCol[1]/2,skCol[2]/2,list[cyc]))
        col = (skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1)
        DrawLine(pos1,[pos2[0],pos1[1]],1,col,col); DrawLine([pos2[0],pos1[1]],pos2,1,col,col); DrawLine(pos2,[pos1[0],pos2[1]],1,col,col); DrawLine([pos1[0],pos2[1]],pos1,1,col,col)
        col = (col[0],col[1],col[2],.375); thS = 2
        DrawLine(pos1,[pos2[0],pos1[1]],1,col,col,[0,-thS]); DrawLine([pos2[0],pos1[1]],pos2,1,col,col,[+thS,0])
        DrawLine(pos2,[pos1[0],pos2[1]],1,col,col,[0,+thS]); DrawLine([pos1[0],pos2[1]],pos1,1,col,col,[-thS,0])
        DrawLine([pos1[0]-thS,pos1[1]],[pos1[0],pos1[1]-thS],1,col,col); DrawLine([pos2[0]+thS,pos1[1]],[pos2[0],pos1[1]-thS],1,col,col)
        DrawLine([pos2[0]+thS,pos2[1]],[pos2[0],pos2[1]+thS],1,col,col); DrawLine([pos1[0]-thS,pos2[1]],[pos1[0],pos2[1]+thS],1,col,col)
    elif GetDrawSettings('TxSt')=='Simplified':
        DrawRectangle([pos1[0],pos1[1]],[pos2[0],pos2[1]],(skCol[0]/2.4,skCol[1]/2.4,skCol[2]/2.4,.8)); col = (.1,.1,.1,.95)
        DrawLine(pos1,[pos2[0],pos1[1]],2,col,col); DrawLine([pos2[0],pos1[1]],pos2,2,col,col); DrawLine(pos2,[pos1[0],pos2[1]],2,col,col); DrawLine([pos1[0],pos2[1]],pos1,2,col,col)            
    blf.position(fontId[0],pos[0]+ofs[0],pos[1]+ofs[1],0); blf.size(fontId[0],28,72); blf.color(fontId[0],skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1.0); blf.draw(fontId[0],txt)
    return len(txt)*15
def DrawIsLinked(loc,ofsx,ofsy,skCol):
    if GetDrawSettings('DrMk')==False: return
    vec = PosViewToReg(loc.x,loc.y); gc = 0.65; col1 = (0,0,0,0.5); col2 = (gc,gc,gc,max(max(skCol[0],skCol[1]),skCol[2])*.9); col3 = (skCol[0],skCol[1],skCol[2],.925)
    DrawCircleOuter([vec[0]+ofsx+1.5,vec[1]+3.5+ofsy],9.0,3.0,col1); DrawCircleOuter([vec[0]+ofsx-3.5,vec[1]-5+ofsy],9.0,3.0,col1)
    DrawCircleOuter([vec[0]+ofsx,vec[1]+5+ofsy],9.0,3.0,col2); DrawCircleOuter([vec[0]+ofsx-5,vec[1]-3.5+ofsy],9.0,3.0,col2)
    DrawCircleOuter([vec[0]+ofsx,vec[1]+5+ofsy],9.0,1.0,col3); DrawCircleOuter([vec[0]+ofsx-5,vec[1]-3.5+ofsy],9.0,1.0,col3)
def VoronoiLinkerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]; lw = GetDrawSettings('LnWd')
    def MucGetWP(loc,offsetx):
        pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6*GetDrawSettings('PtRd'),loc.y)[0]-pos[0]; return pos,rd
    def MucDrawSk(Sk,lh):
        txtlen = DrawText(PosViewToReg(mousePos.x,mousePos.y),[-20*(Sk.is_output*2-1),-5],Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,(-txtlen-48)*(Sk.is_output*2-1),0,GetSkCol(Sk) if GetDrawSettings('ClMk') else (.9,.9,.9,1))
    if (sender.sockOutSk==None):
        if GetDrawSettings('DrPt'):
            wp1 = MucGetWP(mousePos,-GetDrawSettings('PtOX')*.75); wp2 = MucGetWP(mousePos,GetDrawSettings('PtOX')*.75); DrawWidePoint(wp1[0],wp1[1]); DrawWidePoint(wp2[0],wp2[1])
        if (GetDrawSettings('AlLn'))and(GetDrawSettings('DrLn')): DrawLine(wp1[0],wp2[0],lw,(1,1,1,1),(1,1,1,1))
    elif (sender.sockOutSk!=None)and(sender.sockInSk==None):
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        wp1 = MucGetWP(sender.sockOutPs*uiFac[0],GetDrawSettings('PtOX')); wp2 = MucGetWP(mousePos,0)
        if (GetDrawSettings('AlLn'))and(GetDrawSettings('DrLn')): DrawLine(wp1[0],wp2[0],lw,GetSkCol(sender.sockOutSk) if GetDrawSettings('ClLn') else (1,1,1,1),(1,1,1,1))
        if GetDrawSettings('DrPt'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOutSk,2.2)); DrawWidePoint(wp2[0],wp2[1])
        MucDrawSk(sender.sockOutSk,sender.sockOutLH)
    else:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        DrawRectangleOnSocket(context,sender.sockInSk,sender.sockInLH,GetSkVecCol(sender.sockInSk,2.2))
        if GetDrawSettings('ClLn'): col1 = GetSkCol(sender.sockOutSk); col2 = GetSkCol(sender.sockInSk)
        else: col1 = (1,1,1,1); col2 = (1,1,1,1)
        wp1 = MucGetWP(sender.sockOutPs*uiFac[0],GetDrawSettings('PtOX')); wp2 = MucGetWP(sender.sockInPs*uiFac[0],-GetDrawSettings('PtOX'))
        if GetDrawSettings('DrLn'): DrawLine(wp1[0],wp2[0],lw,col1,col2)
        if GetDrawSettings('DrPt'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOutSk,2.2)); DrawWidePoint(wp2[0],wp2[1],GetSkVecCol(sender.sockInSk,2.2))
        MucDrawSk(sender.sockOutSk,sender.sockOutLH); MucDrawSk(sender.sockInSk,sender.sockInLH)
class VoronoiLinker(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_linker'; bl_label = 'Voronoi Linker'; bl_options = {'UNDO'}
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
            VoronoiLinker.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data; SetFont()
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiLinkerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

def VoronoiMixerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]; mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y); lw = GetDrawSettings('LnWd')
    def MucGetWP(loc,offsetx): pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6*GetDrawSettings('PtRd'),loc.y)[0]-pos[0]; return pos,rd
    def MucDrawSk(Sk,lh,y):
        txtlen = DrawText(PosViewToReg(mousePos.x,mousePos.y),[20,y],Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,txtlen+48,y+5,GetSkCol(Sk) if GetDrawSettings('ClMk') else (.9,.9,.9,1))
    if (sender.sockOut1Sk==None):
        if GetDrawSettings('DrPt'): wp1 = MucGetWP(mousePos,-GetDrawSettings('PtOX')*.75); wp2 = MucGetWP(mousePos,GetDrawSettings('PtOX')*.75); DrawWidePoint(wp1[0],wp1[1]); DrawWidePoint(wp2[0],wp2[1])
    elif (sender.sockOut1Sk!=None)and(sender.sockOut2Sk==None):
        DrawRectangleOnSocket(context,sender.sockOut1Sk,sender.sockOut1LH,GetSkVecCol(sender.sockOut1Sk,2.2))
        wp1 = MucGetWP(sender.sockOut1Ps*uiFac[0],GetDrawSettings('PtOX')); wp2 = MucGetWP(mousePos,0); col = Vector((1,1,1,1))
        if GetDrawSettings('DrLn'): DrawLine(wp1[0],mouseRegionPs,lw,GetSkCol(sender.sockOut1Sk) if GetDrawSettings('ClLn') else col,col)
        if GetDrawSettings('DrPt'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOut1Sk,2.2)); DrawWidePoint(wp2[0],wp2[1])
        MucDrawSk(sender.sockOut1Sk,sender.sockOut1LH,-5)
    else:
        DrawRectangleOnSocket(context,sender.sockOut1Sk,sender.sockOut1LH,GetSkVecCol(sender.sockOut1Sk,2.2))
        DrawRectangleOnSocket(context,sender.sockOut2Sk,sender.sockOut2LH,GetSkVecCol(sender.sockOut2Sk,2.2))
        if GetDrawSettings('ClLn'): col1 = GetSkCol(sender.sockOut1Sk); col2 = GetSkCol(sender.sockOut2Sk)
        else: col1 = (1,1,1,1); col2 = (1,1,1,1)
        wp1 = MucGetWP(sender.sockOut1Ps*uiFac[0],GetDrawSettings('PtOX')); wp2 = MucGetWP(sender.sockOut2Ps*uiFac[0],GetDrawSettings('PtOX'))
        if GetDrawSettings('DrLn'): DrawLine(mouseRegionPs,wp2[0],lw,col2,col2); DrawLine(wp1[0],mouseRegionPs,lw,col1,col1)
        if GetDrawSettings('DrPt'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOut1Sk,2.2)); DrawWidePoint(wp2[0],wp2[1],GetSkVecCol(sender.sockOut2Sk,2.2))
        MucDrawSk(sender.sockOut1Sk,sender.sockOut1LH,-29); MucDrawSk(sender.sockOut2Sk,sender.sockOut2LH,19)
class VoronoiMixer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_mixer'; bl_label = 'Voronoi Mixer'; bl_options = {'UNDO'}
    def MucAssign(sender,context):
        muc = GetNearestSocketInRegionMouse(context,True,sender.sockOut1Sk); sender.sockOut2Sk = muc[0]; sender.sockOut2Ps = muc[1]; sender.sockOut2LH = muc[3]
        if (sender.sockOut1Sk!=None)and(sender.sockOut2Sk!=None)and(sender.sockOut1Sk==sender.sockOut2Sk): sender.sockOut2Sk = None; sender.sockOut2Ps = None
    def modal(self,context,event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE': VoronoiMixer.MucAssign(self,context)
            case 'RIGHTMOUSE'|'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOut1Sk!=None)and(self.sockOut2Sk!=None):
                    mixerSk1[0] = self.sockOut1Sk; mixerSk2[0] = self.sockOut2Sk; mixerSkTyp[0] = mixerSk1[0].type if mixerSk1[0].type!='CUSTOM' else mixerSk2[0].type
                    try:
                        dm = VMMapDictMain[context.space_data.tree_type][mixerSkTyp[0]]
                        if len(dm)!=0:
                            if GetDrawSettings('OnSp')and(len(dm)==1): DoMix(context,dm[0])
                            else:
                                if GetDrawSettings('MxMnSt')=='Pie': bpy.ops.wm.call_menu_pie(name='node.VM_MT_voronoi_mixer_menu')
                                else: bpy.ops.wm.call_menu(name='node.VM_MT_voronoi_mixer_menu')
                    except:pass
                    return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self,context,event):
        context.area.tag_redraw()
        if (context.area.type!='NODE_EDITOR')or(context.space_data.edit_tree==None): return {'CANCELLED'}
        else:
            muc = GetNearestSocketInRegionMouse(context,True,None); self.sockOut1Sk = muc[0]; self.sockOut1Ps = muc[1]; self.sockOut1LH = muc[3]
            VoronoiMixer.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data; SetFont()
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiMixerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
mixerSk1 = [None]; mixerSk2 = [None]; mixerSkTyp = [None]
VMMapDictMixersDefs = {'GeometryNodeSwitch':[-1,-1,'Switch'],'ShaderNodeMixShader':[1,2,'Mix'],'ShaderNodeAddShader':[0,1,'Add'],'ShaderNodeMixRGB':[1,2,'Mix RGB'],
        'ShaderNodeMath':[0,1,'Max'],'ShaderNodeVectorMath':[0,1,'Max'],'FunctionNodeBooleanMath':[0,1,'Or'],'FunctionNodeCompare':[-1,-1,'Compare'],
        'GeometryNodeCurveToMesh':[0,1,'Curve to Mesh'],'GeometryNodeInstanceOnPoints':[0,2,'Instance on Points'],'GeometryNodeMeshBoolean':[0,1,'Boolean'],
        'GeometryNodeStringJoin':[1,1,'Join'],'GeometryNodeJoinGeometry':[0,0,'Join'],'GeometryNodeGeometryToInstance':[0,0,'To Instance'],
        'CompositorNodeMixRGB':[1,2,'Mix'],'CompositorNodeMath':[0,1,'Max'],'CompositorNodeSwitch':[0,1,'Switch'],'CompositorNodeAlphaOver':[1,2,'Alpha Over'],
        'CompositorNodeSplitViewer':[0,1,'Split Viewer'],'CompositorNodeSwitchView':[0,1,'Switch View'],'TextureNodeMixRGB':[1,2,'Mix'],
        'TextureNodeMath':[0,1,'Max'],'TextureNodeTexture':[0,1,'Texture'],'TextureNodeDistance':[0,1,'Distance'],'ShaderNodeMix':[-1,-1,'Mix']}
VMMapDictSwitchType = {'VALUE':'FLOAT'}; VMMapDictUserSkName = {'VALUE':'Float','RGBA':'Color'}
def DoMix(context,who):
    tree = context.space_data.edit_tree
    if tree!=None:
        bpy.ops.node.add_node('INVOKE_DEFAULT',type=who,use_transform=True); aNd = tree.nodes.active; aNd.width = 140
        match aNd.bl_idname:
            case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath': aNd.operation = 'MAXIMUM'
            case 'FunctionNodeBooleanMath': aNd.operation = 'OR'
            case 'TextureNodeTexture': aNd.show_preview = False
            case 'GeometryNodeSwitch': aNd.input_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
            case 'FunctionNodeCompare':aNd.data_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0]); aNd.operation = aNd.operation if aNd.data_type!='FLOAT' else 'EQUAL'
            case 'ShaderNodeMix':aNd.data_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
        match aNd.bl_idname:
            case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix':
                tgl = aNd.bl_idname!='FunctionNodeCompare'; foundSkList = [sk for sk in (reversed(aNd.inputs) if tgl else aNd.inputs) if sk.type==mixerSkTyp[0]]
                tree.links.new(mixerSk1[0],foundSkList[tgl]); tree.links.new(mixerSk2[0],foundSkList[not tgl])
            case _:
                if aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]].is_multi_input: tree.links.new(mixerSk2[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][1]])
                tree.links.new(mixerSk1[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]])
                if aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]].is_multi_input==False: tree.links.new(mixerSk2[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][1]])
class VoronoiMixerMixer(bpy.types.Operator):
    bl_idname = 'node.voronoi_mixer_mixer'; bl_label = 'Voronoi Mixer Mixer'; bl_options = {'UNDO'}
    who: bpy.props.StringProperty()
    def execute(self,context):
        DoMix(context,self.who)
        return {'FINISHED'}
VMMapDictMain = {
        'ShaderNodeTree':{'SHADER':['ShaderNodeMixShader','ShaderNodeAddShader'],'VALUE':['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeMath'],
                'RGBA':['ShaderNodeMix','ShaderNodeMixRGB'],'VECTOR':['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeVectorMath'],'INT':['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeMath']},
        'GeometryNodeTree':{'VALUE':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare','ShaderNodeMath'],
                'RGBA':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare'],
                'VECTOR':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare','ShaderNodeVectorMath'],
                'STRING':['GeometryNodeSwitch','FunctionNodeCompare','GeometryNodeStringJoin'],
                'INT':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare','ShaderNodeMath'],
                'GEOMETRY':['GeometryNodeSwitch','GeometryNodeJoinGeometry','GeometryNodeInstanceOnPoints','GeometryNodeCurveToMesh','GeometryNodeMeshBoolean','GeometryNodeGeometryToInstance'],
                'BOOLEAN':['GeometryNodeSwitch','ShaderNodeMixRGB','ShaderNodeMath','FunctionNodeBooleanMath'],'OBJECT':['GeometryNodeSwitch'],
                'MATERIAL':['GeometryNodeSwitch'],'COLLECTION':['GeometryNodeSwitch'],'TEXTURE':['GeometryNodeSwitch'],'IMAGE':['GeometryNodeSwitch']},
        'CompositorNodeTree':{'VALUE':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeMath'],
                'RGBA':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeAlphaOver'],
                'VECTOR':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'],
                'INT':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeMath']},
        'TextureNodeTree':{'VALUE':['TextureNodeMixRGB','TextureNodeMath','TextureNodeTexture'],'RGBA':['TextureNodeMixRGB','TextureNodeTexture'],
                'VECTOR':['TextureNodeMixRGB','TextureNodeDistance'],'INT':['TextureNodeMixRGB','TextureNodeMath','TextureNodeTexture']}}
class VoronoiMixerMenu(bpy.types.Menu):
    bl_idname = 'node.VM_MT_voronoi_mixer_menu'; bl_label = ''
    def draw(self,context):
        who = self.layout.menu_pie() if GetDrawSettings('MxMnSt')=='Pie' else self.layout
        who.label(text=VMMapDictUserSkName.get(mixerSkTyp[0],mixerSkTyp[0].capitalize()))
        for li in VMMapDictMain[context.space_data.tree_type][mixerSkTyp[0]]: who.operator('node.voronoi_mixer_mixer',text=VMMapDictMixersDefs[li][2]).who=li

def VoronoiPreviewerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]; mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y); lw = GetDrawSettings('LnWd')
    def MucGetWP(loc,offsetx): pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6*GetDrawSettings('PtRd'),loc.y)[0]-pos[0]; return pos,rd
    def MucDrawSk(Sk,lh):
        txtlen = DrawText(PosViewToReg(mousePos.x,mousePos.y),[20,-5],Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,txtlen+48,0,GetSkCol(Sk) if GetDrawSettings('ClMk') else (.9,.9,.9,1))
    if (sender.sockOutSk==None):
        if GetDrawSettings('DrPt'): wp = MucGetWP(mousePos,0); DrawWidePoint(wp[0],wp[1])
    else:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        col = GetSkCol(sender.sockOutSk) if GetDrawSettings('ClLn') else (1,1,1,1); wp = MucGetWP(sender.sockOutPs*uiFac[0],GetDrawSettings('PtOX'))
        if GetDrawSettings('DrLn'): DrawLine(wp[0],mouseRegionPs,lw,col,col)
        if GetDrawSettings('DrPt'): DrawWidePoint(wp[0],wp[1],GetSkVecCol(sender.sockOutSk,2.2))
        MucDrawSk(sender.sockOutSk,sender.sockOutLH)
class VoronoiPreviewer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_previewer'; bl_label = 'Voronoi Previewer'; bl_options = {'UNDO'}
    liveprew = False
    def MucAssign(sender,context):
        muc = GetNearestSocketInRegionMouse(context,True,None); sender.sockOutSk = muc[0]; sender.sockOutPs = muc[1]; sender.sockOutLH = muc[3]
        if (sender.liveprew)and(sender.sockOutSk!=None): VoronoiPreviewer_DoPreview(context,sender.sockOutSk)
    def modal(self,context,event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE': VoronoiPreviewer.MucAssign(self,context)
            case 'LEFTMOUSE'|'RIGHTMOUSE'|'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOutSk!=None): VoronoiPreviewer_DoPreview(context,self.sockOutSk); return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self,context,event):
        if (event.type=='LEFTMOUSE')^GetDrawSettings('PrIv'):
            nodes = context.space_data.edit_tree.nodes; nnd = (nodes.get('Voronoi_Anchor') or nodes.new('NodeReroute'))
            nnd.name = 'Voronoi_Anchor'; nnd.label = 'Voronoi_Anchor'; nnd.location = context.space_data.cursor_location; nnd.select = True; return {'FINISHED'}
        elif (context.space_data.tree_type!='GeometryNodeTree')or(GetDrawSettings('PrGm')):
            context.area.tag_redraw(); self.liveprew = GetDrawSettings('LvPr')
            if (context.area.type!='NODE_EDITOR')or(context.space_data.edit_tree==None): return {'CANCELLED'}
            else:
                VoronoiPreviewer.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data; SetFont()
                self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiPreviewerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
                context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
ShaderShadersWithColor = ('BSDF_ANISOTROPIC','BSDF_DIFFUSE','EMISSION','BSDF_GLASS','BSDF_GLOSSY','BSDF_HAIR','BSDF_HAIR_PRINCIPLED','PRINCIPLED_VOLUME','BACKGROUND',
        'BSDF_REFRACTION','SUBSURFACE_SCATTERING','BSDF_TOON','BSDF_TRANSLUCENT','BSDF_TRANSPARENT','BSDF_VELVET','VOLUME_ABSORPTION','VOLUME_SCATTER')
AnchorSk = [None]
def VoronoiPreviewer_DoPreview(context,goalSk):
    def GetSocketIndex(socket): return int(socket.path_from_id().split('.')[-1].split('[')[-1][:-1])
    def GetTreesWay(context,nd):
        way = []; nds = []; treeWyc = context.space_data.node_tree; lim = 0
        while (treeWyc!=context.space_data.edit_tree)and(lim<64): way.insert(0,treeWyc); nds.insert(0,treeWyc.nodes.active); treeWyc = treeWyc.nodes.active.node_tree; lim += 1
        way.insert(0,treeWyc); nds.insert(0,nd)
        return way, nds
    for ng in bpy.data.node_groups:
        if ng.type==context.space_data.node_tree.type:
            sk = ng.outputs.get('voronoi_preview')
            if sk!=None: ng.outputs.remove(sk)
    WayTr, WayNd = GetTreesWay(context,goalSk.node); hWyLen = len(WayTr)-1; ixSkLastUsed = -1; isZeroPreviewGen = True
    for cyc in range(hWyLen+1):
        nodeIn = None; sockOut = None; sockIn = None
        #Найти принимающий нод текущего уровня
        if cyc!=hWyLen:
            for nd in WayTr[cyc].nodes:
                if nd.type in ['GROUP_OUTPUT','OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','COMPOSITE','OUTPUT']:
                    if nodeIn==None: nodeIn = nd
                    elif nodeIn.location>goalSk.node.location: nodeIn = nd
        else:
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    num = int(goalSk.node.type in ('VOLUME_ABSORPTION','VOLUME_SCATTER'))
                    for nd in WayTr[hWyLen].nodes:
                        if nd.type in ['OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT']:
                            sockIn = nd.inputs[num*(not(nd.type in ['OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT']))] if nd.is_active_output else sockIn
                case 'CompositorNodeTree':
                    for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='VIEWER') else sockIn
                    if sockIn==None:
                        for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='COMPOSITE')and(nd.is_active_output) else sockIn
                case 'GeometryNodeTree':
                    for nd in WayTr[hWyLen].nodes:
                        sockIn = nd.inputs.get('Geometry') if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output) else sockIn
                        lis = [sk for sk in nd.inputs if sk.type=='GEOMETRY']; sockIn = lis[0] if (sockIn==None)and(len(lis)!=0) else sockIn
                        if sockIn==None:
                            try: sockIn = nd.inputs[0]
                            except:pass
                case 'TextureNodeTree':
                    for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='OUTPUT')and(nd.is_active_output) else sockIn
            nodeIn = sockIn.node
        #Определить сокет отправляющего нода
        if cyc==0: sockOut = goalSk
        else: sockOut = WayNd[cyc].outputs.get('voronoi_preview'); sockOut = WayNd[cyc].outputs[ixSkLastUsed] if sockOut==None else sockOut
        #Определить сокет принимающего нода:
        for sl in sockOut.links:
            if sl.to_node==nodeIn: sockIn = sl.to_socket; ixSkLastUsed = GetSocketIndex(sockIn)
        if sockIn==None:
            sockIn = WayTr[cyc].outputs.get('voronoi_preview')
            if sockIn==None:
                WayTr[cyc].outputs.new('NodeSocketColor' if context.space_data.tree_type!='GeometryNodeTree' else 'NodeSocketGeometry','voronoi_preview')
                sockIn = nodeIn.inputs.get('voronoi_preview'); sockIn.hide_value = True; isZeroPreviewGen = False
        #Удобный сразу-в-шейдер
        if (sockOut.type in ('RGBA'))and(cyc==hWyLen)and(len(sockIn.links)!=0)and(sockIn.links[0].from_node.type in ShaderShadersWithColor)and(isZeroPreviewGen):
            if len(sockIn.links[0].from_socket.links)==1: sockIn = sockIn.links[0].from_node.inputs.get('Color')
        nd_va = WayTr[0].nodes.get('Voronoi_Anchor'); sockIn = nd_va.inputs[0] if nd_va else sockIn
        if (sockOut!=None)and(sockIn!=None)and((sockIn.name=='voronoi_preview')or(cyc==hWyLen)): WayTr[cyc].links.new(sockOut,sockIn)
    

class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = 'VoronoiLinker' if __name__=='__main__' else __name__
    LnWd:bpy.props.IntProperty(name='Line Width',default=1,min=1,max=16,subtype='FACTOR'); PtOX:bpy.props.FloatProperty(name='Point offset X',default=20,min=-50,max=50)
    PtRs:bpy.props.IntProperty(name='Point resolution',default=54,min=3,max=64); PtRd:bpy.props.FloatProperty(name='Point radius scale',default=1,min=0,max=3)
    DrTx:bpy.props.BoolProperty(name='Draw Text',default=True); ClTx:bpy.props.BoolProperty(name='Colored Text',default=True)
    DrMk:bpy.props.BoolProperty(name='Draw Marker',default=True); ClMk:bpy.props.BoolProperty(name='Colored Marker',default=True)
    DrPt:bpy.props.BoolProperty(name='Draw Points',default=True); ClPt:bpy.props.BoolProperty(name='Colored Points',default=False)
    DrLn:bpy.props.BoolProperty(name='Draw Line',default=True); ClLn:bpy.props.BoolProperty(name='Colored Line',default=False)
    DrAr:bpy.props.BoolProperty(name='Draw Socket Area',default=False); ClAr:bpy.props.BoolProperty(name='Colored Socket Area',default=False)
    TxSt:bpy.props.EnumProperty(name='Text Style',default='Classic',items={('Classic','Classic',''),('Simplified','Simplified',''),('Text','Only text','')})
    AlLn:bpy.props.BoolProperty(name='Always draw line',default=False); OnSp:bpy.props.BoolProperty(name='One Choise to skip',description='A',default=False)
    MxMnSt:bpy.props.EnumProperty(name='Mixer Menu Style',default='Pie',items={('Pie','Pie',''),('List','List','')})
    LvPr:bpy.props.BoolProperty(name='Live Preview',default=False); PrGm:bpy.props.BoolProperty(name='Preview in Geometry nodes',default=True)
    PrIv:bpy.props.BoolProperty(name='Preview key inverse',default=False)
    def draw(self,context):
        col0 = self.layout.column(); box = col0.box(); col1 = box.column(align=True); col1.label(text='Draw stiings'); row = col1.row(align=True)
        row.prop(self,'DrTx'); row.prop(self,'ClTx'); row = col1.row(align=True); row.prop(self,'DrMk'); row.prop(self,'ClMk'); row = col1.row(align=True)
        row.prop(self,'DrPt'); row.prop(self,'ClPt'); row = col1.row(align=True); row.prop(self,'DrLn'); row.prop(self,'ClLn'); row = col1.row(align=True)
        col1.prop(self,'LnWd'); col1.prop(self,'PtRd'); col1.prop(self,'PtOX'); col1.prop(self,'PtRs')
        row.prop(self,'DrAr'); row.prop(self,'ClAr'); col1.prop(self,'TxSt'); col1.prop(self,'AlLn')
        box = col0.box(); col1 = box.column(align=True); col1.label(text='Mixer stiings'); col1.prop(self,'MxMnSt'); col1.prop(self,'OnSp')
        box = col0.box(); col1 = box.column(align=True)
        col1.label(text='Preview stiings'); col1.prop(self,'LvPr'); col1.prop(self,'PrGm'); col1.prop(self,'PrIv')

addon_keymaps = []
classes = [VoronoiLinker,VoronoiMixer,VoronoiMixerMixer,VoronoiMixerMenu,VoronoiPreviewer,VoronoiAddonPrefs]
def register():
    for cl in classes: bpy.utils.register_class(cl)
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor',space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(VoronoiLinker.bl_idname,type='RIGHTMOUSE',value='PRESS',alt=True); addon_keymaps.append((km,kmi))
    kmi = km.keymap_items.new(VoronoiMixer.bl_idname,type='RIGHTMOUSE',value='PRESS',shift=True,alt=True); addon_keymaps.append((km,kmi))
    kmi = km.keymap_items.new(VoronoiPreviewer.bl_idname,type='LEFTMOUSE',value='PRESS',shift=True,ctrl=True); addon_keymaps.append((km,kmi))
    kmi = km.keymap_items.new(VoronoiPreviewer.bl_idname,type='RIGHTMOUSE',value='PRESS',shift=True,ctrl=True); addon_keymaps.append((km,kmi))
def unregister():
    for cl in reversed(classes): bpy.utils.unregister_class(cl)
    for km,kmi in addon_keymaps: km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__=='__main__': register()