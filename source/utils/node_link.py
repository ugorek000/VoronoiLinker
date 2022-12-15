import bpy, bgl, blf, gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from math import pi, sin, cos, tan, asin, acos, atan, atan2, sqrt, inf, copysign

def uiScale():
    return bpy.context.preferences.system.dpi * bpy.context.preferences.system.pixel_size / 72

def PosViewToReg(x,y):
    return bpy.context.region.view2d.view_to_region(x,y,clip=False)

shader = [None,None]
uiFac = [1.0]

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
    colfac = colfac if GetDrawSettings('colored_socket') else Vector((1,1,1,1)); rd = sqrt(rd*rd+10)
    DrawCircle(pos,rd+3,col1*colfac); DrawCircle(pos,rd,col2*colfac); DrawCircle(pos,rd/1.5,col3*colfac)

def DrawRectangle(ps1,ps2,cl): DrawAreaFan([(ps1[0],ps1[1]),(ps2[0],ps1[1]),(ps2[0],ps2[1]),(ps1[0],ps2[1])],cl)

def DrawRectangleOnSocket(context,sk,stEn,colfac=Vector((1,1,1,1))):
    if GetDrawSettings('draw_socket_area')==False: return
    loc = RecrGetNodeFinalLoc(sk.node).copy()*uiFac[0]; pos1 = PosViewToReg(loc.x,stEn[0]*uiFac[0]); colfac = colfac if GetDrawSettings('colored_socket_area') else Vector((1,1,1,1))
    pos2 = PosViewToReg(loc.x+sk.node.dimensions.x,stEn[1]*uiFac[0]); DrawRectangle(pos1,pos2,Vector((1.0,1.0,1.0,0.075))*colfac)

fontId = [0]; where = [None]

def RecrGetNodeFinalLoc(node):
    return node.location if node.parent is None else node.location + RecrGetNodeFinalLoc(node.parent)

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
    mousePs = context.space_data.cursor_location
    nd = GetNearestNodeInRegionMouse(context)[0]
    locNd = RecrGetNodeFinalLoc(nd)
    if nd.bl_idname=='NodeReroute': return nd.outputs[0] if getOut else nd.inputs[0], nd.location, Vector(mousePs-nd.location).length, (-1,-1)
    def MucGet(who,getOut):
        goalSk = None
        goalPs = None
        minLen = inf
        skHigLigHei = (0,0)
        ndDim = nd.dimensions/uiFac[0]
        if getOut:skLoc = Vector((locNd.x+ndDim[0],locNd.y-35))
        else:skLoc = Vector((locNd.x,locNd.y-ndDim[1]+16))
        for wh in who:
            if (wh.enabled)and(wh.hide==False):
                muv = 0
                tgl = False
                if (getOut==False)and(wh.type=='VECTOR')and(wh.is_linked==False)and(wh.hide_value==False):
                    if 'VectorDirection' in str(wh.bl_rna): skLoc[1] += 20*2; muv = 2
                    elif nd.type not in (
                        'BSDF_PRINCIPLED',
                        'SUBSURFACE_SCATTERING',
                    ) or wh.name not in ('Subsurface Radius', 'Radius'): skLoc[1] += 30*2; muv = 3
                if skOut!=None:
                    # not getOut чтобы не присасываться реальными к виртуальным при миксере (getOut=True)
                    tgl = (skOut.bl_idname=='NodeSocketVirtual')or((wh.bl_idname=='NodeSocketVirtual')and(not getOut))
                    tgl = (tgl)or((skOut.type in SkPerms)and(wh.type in SkPerms))or(skOut.bl_idname==wh.bl_idname)
                    if getOut:
                        tgl = tgl and (
                            skOut.bl_idname != 'NodeSocketVirtual'
                            or wh.bl_idname != 'NodeSocketVirtual'
                            or skOut == wh
                        )
                if getOut and skOut is None or tgl: # skOut==None чтобы учитывать влияние tgl при skOut!=None
                    fieldXY = mousePs-skLoc; fieldL = fieldXY.length
                    if fieldL<minLen: minLen = fieldL; goalSk = wh; goalPs = skLoc.copy(); skHigLigHei = (goalPs[1]-11-muv*20,goalPs[1]+11+max(len(wh.links)-2,0)*5)
                skLoc[1] += 22*(1-getOut*2)
        return goalSk, goalPs, minLen, skHigLigHei

    return MucGet(nd.outputs if getOut else reversed(nd.inputs),getOut)

def GetSkCol(Sk):
    return Sk.draw_color(bpy.context,Sk.node)

def Vec4Pow(vec,pw):
    return Vector((vec.x**pw,vec.y**pw,vec.z**pw,vec.w**pw))

def GetSkVecCol(Sk,apw):
    return Vec4Pow(Vector(Sk.draw_color(bpy.context,Sk.node)),1/apw)

def GetDrawSettings(txt):
    return getattr(bpy.context.preferences.addons[__package__.partition('.')[0]].preferences,txt,None)

def SetFont():
    fontId[0] = blf.load(r'C:\Windows\Fonts\consola.ttf'); fontId[0] = 0 if fontId[0]==-1 else fontId[0] #for change Blender themes

def DrawText(pos,ofs,Sk):
    if GetDrawSettings('draw_text')==False: return 0
    try: skCol = GetSkCol(Sk)
    except: skCol = (1,0,0,1)
    skCol = skCol if GetDrawSettings('color_text') else (.9,.9,.9,1)
    txt = Sk.name if Sk.bl_idname!='NodeSocketVirtual' else 'Virtual'
    pos = [pos[0]-(len(txt)*15+5)*(ofs[0]<0),pos[1]]
    pw = 1/1.975
    pos1 = [pos[0]+ofs[0]-2,pos[1]+ofs[1]-9]
    pos2 = [pos[0]+ofs[0]+len(txt)*15+2,pos[1]+ofs[1]+23]
    if GetDrawSettings('font_style')=='CLASSIC':
        _extracted_from_DrawText_7(pos1, pos2, skCol, pw)
    elif GetDrawSettings('font_style')=='SIMPLIFIED':
        DrawRectangle([pos1[0],pos1[1]],[pos2[0],pos2[1]],(skCol[0]/2.4,skCol[1]/2.4,skCol[2]/2.4,.8))
        col = (.1,.1,.1,.95)
        _extracted_from_DrawText_11(pos1, pos2, 2, col)
    blf.position(fontId[0],pos[0]+ofs[0],pos[1]+ofs[1],0)
    blf.size(fontId[0],28,72)
    blf.color(fontId[0],skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1.0)
    blf.draw(fontId[0],txt)
    return len(txt)*15


# TODO Rename this here and in `DrawText`
def _extracted_from_DrawText_7(pos1, pos2, skCol, pw):
    list = [.4,.55,.8,.9,1]
    uh = 1/len(list)*32
    for cyc in range(len(list)): DrawRectangle([pos1[0],pos1[1]+cyc*uh],[pos2[0],pos1[1]+cyc*uh+uh],(skCol[0]/2,skCol[1]/2,skCol[2]/2,list[cyc]))
    col = (skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1)
    _extracted_from_DrawText_11(pos1, pos2, 1, col)
    col = (col[0],col[1],col[2],.375)
    thS = 2
    DrawLine(pos1,[pos2[0],pos1[1]],1,col,col,[0,-thS])
    DrawLine([pos2[0],pos1[1]],pos2,1,col,col,[+thS,0])
    DrawLine(pos2,[pos1[0],pos2[1]],1,col,col,[0,+thS])
    DrawLine([pos1[0],pos2[1]],pos1,1,col,col,[-thS,0])
    DrawLine([pos1[0]-thS,pos1[1]],[pos1[0],pos1[1]-thS],1,col,col)
    DrawLine([pos2[0]+thS,pos1[1]],[pos2[0],pos1[1]-thS],1,col,col)
    DrawLine([pos2[0]+thS,pos2[1]],[pos2[0],pos2[1]+thS],1,col,col)
    DrawLine([pos1[0]-thS,pos2[1]],[pos1[0],pos2[1]+thS],1,col,col)


# TODO Rename this here and in `DrawText`
def _extracted_from_DrawText_11(pos1, pos2, arg2, col):
    DrawLine(pos1, [pos2[0],pos1[1]], arg2, col, col)
    DrawLine([pos2[0],pos1[1]], pos2, arg2, col, col)
    DrawLine(pos2, [pos1[0],pos2[1]], arg2, col, col)
    DrawLine([pos1[0],pos2[1]], pos1, arg2, col, col)

def DrawIsLinked(loc,ofsx,ofsy,skCol):
    if GetDrawSettings('draw_marker')==False: return
    vec = PosViewToReg(loc.x,loc.y); gc = 0.65; col1 = (0,0,0,0.5); col2 = (gc,gc,gc,max(max(skCol[0],skCol[1]),skCol[2])*.9); col3 = (skCol[0],skCol[1],skCol[2],.925)
    DrawCircleOuter([vec[0]+ofsx+1.5,vec[1]+3.5+ofsy],9.0,3.0,col1); DrawCircleOuter([vec[0]+ofsx-3.5,vec[1]-5+ofsy],9.0,3.0,col1)
    DrawCircleOuter([vec[0]+ofsx,vec[1]+5+ofsy],9.0,3.0,col2); DrawCircleOuter([vec[0]+ofsx-5,vec[1]-3.5+ofsy],9.0,3.0,col2)
    DrawCircleOuter([vec[0]+ofsx,vec[1]+5+ofsy],9.0,1.0,col3); DrawCircleOuter([vec[0]+ofsx-5,vec[1]-3.5+ofsy],9.0,1.0,col3)

def VoronoiLinkerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]
    def MucGetWP(loc,offsetx):
        pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6,loc.y)[0]-pos[0]; return pos,rd

    def MucDrawSk(Sk,lh):
        txtlen = DrawText(PosViewToReg(mousePos.x,mousePos.y),[-20*(Sk.is_output*2-1),-5],Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,(-txtlen-48)*(Sk.is_output*2-1),0,GetSkCol(Sk) if GetDrawSettings('colored_marker') else (.9,.9,.9,1))

    if sender.sockOutSk is None:
        if GetDrawSettings('draw_socket'):
            wp1 = MucGetWP(mousePos,-GetDrawSettings('socket_offset')*.75); wp2 = MucGetWP(mousePos,GetDrawSettings('socket_offset')*.75); DrawWidePoint(wp1[0],wp1[1]); DrawWidePoint(wp2[0],wp2[1])
        if GetDrawSettings('draw_wire'): DrawLine(wp1[0],wp2[0],1,(1,1,1,1),(1,1,1,1))
    elif sender.sockOutSk != None and sender.sockInSk is None:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        wp1 = MucGetWP(sender.sockOutPs*uiFac[0],GetDrawSettings('socket_offset')); wp2 = MucGetWP(mousePos,0)
        if GetDrawSettings('draw_wire'): DrawLine(wp1[0],wp2[0],1,GetSkCol(sender.sockOutSk) if GetDrawSettings('colored_line') else (1,1,1,1),(1,1,1,1))
        if GetDrawSettings('draw_socket'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOutSk,2.2)); DrawWidePoint(wp2[0],wp2[1])
        MucDrawSk(sender.sockOutSk,sender.sockOutLH)
    else:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        DrawRectangleOnSocket(context,sender.sockInSk,sender.sockInLH,GetSkVecCol(sender.sockInSk,2.2))
        if GetDrawSettings('colored_line'): col1 = GetSkCol(sender.sockOutSk); col2 = GetSkCol(sender.sockInSk)
        else: col1 = (1,1,1,1); col2 = (1,1,1,1)
        wp1 = MucGetWP(sender.sockOutPs*uiFac[0],GetDrawSettings('socket_offset')); wp2 = MucGetWP(sender.sockInPs*uiFac[0],-GetDrawSettings('socket_offset'))
        if GetDrawSettings('draw_line'): DrawLine(wp1[0],wp2[0],1,col1,col2)
        if GetDrawSettings('draw_socket'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOutSk,2.2)); DrawWidePoint(wp2[0],wp2[1],GetSkVecCol(sender.sockInSk,2.2))
        MucDrawSk(sender.sockOutSk,sender.sockOutLH); MucDrawSk(sender.sockInSk,sender.sockInLH)

def VoronoiMixerDrawCallback(sender,context):
    if where[0]!=context.space_data:
        return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]
    mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y)

    def MucGetWP(loc,offsetx):
        pos = PosViewToReg(loc.x+offsetx,loc.y)
        rd = PosViewToReg(loc.x+offsetx+6,loc.y)[0]-pos[0]
        return pos,rd

    def MucDrawSk(Sk,lh,y):
        txtlen = DrawText(PosViewToReg(mousePos.x,mousePos.y),[20,y],Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,txtlen+48,y+5,GetSkCol(Sk) if GetDrawSettings('colored_marker') else (.9,.9,.9,1))

    if sender.sockOut1Sk is None:
        if GetDrawSettings('draw_socket'): 
            wp1 = MucGetWP(mousePos,-GetDrawSettings('socket_offset')*.75); wp2 = MucGetWP(mousePos,GetDrawSettings('socket_offset')*.75); DrawWidePoint(wp1[0],wp1[1]); DrawWidePoint(wp2[0],wp2[1])
    elif sender.sockOut1Sk != None and sender.sockOut2Sk is None:
        DrawRectangleOnSocket(context,sender.sockOut1Sk,sender.sockOut1LH,GetSkVecCol(sender.sockOut1Sk,2.2))
        wp1 = MucGetWP(sender.sockOut1Ps*uiFac[0],GetDrawSettings('socket_offset')); wp2 = MucGetWP(mousePos,0); col = Vector((1,1,1,1))
        if GetDrawSettings('draw_line'): DrawLine(wp1[0],mouseRegionPs,1,GetSkCol(sender.sockOut1Sk) if GetDrawSettings('colored_line') else col,col)
        if GetDrawSettings('draw_socket'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOut1Sk,2.2)); DrawWidePoint(wp2[0],wp2[1])
        MucDrawSk(sender.sockOut1Sk,sender.sockOut1LH,-5)
    else:
        DrawRectangleOnSocket(context,sender.sockOut1Sk,sender.sockOut1LH,GetSkVecCol(sender.sockOut1Sk,2.2))
        DrawRectangleOnSocket(context,sender.sockOut2Sk,sender.sockOut2LH,GetSkVecCol(sender.sockOut2Sk,2.2))
        if GetDrawSettings('colored_line'): col1 = GetSkCol(sender.sockOut1Sk); col2 = GetSkCol(sender.sockOut2Sk)
        else: col1 = (1,1,1,1); col2 = (1,1,1,1)
        wp1 = MucGetWP(sender.sockOut1Ps*uiFac[0],GetDrawSettings('socket_offset')); wp2 = MucGetWP(sender.sockOut2Ps*uiFac[0],GetDrawSettings('socket_offset'))
        if GetDrawSettings('draw_line'): DrawLine(mouseRegionPs,wp2[0],1,col2,col2); DrawLine(wp1[0],mouseRegionPs,1,col1,col1)
        if GetDrawSettings('draw_socket'): DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOut1Sk,2.2)); DrawWidePoint(wp2[0],wp2[1],GetSkVecCol(sender.sockOut2Sk,2.2))
        MucDrawSk(sender.sockOut1Sk,sender.sockOut1LH,-29); MucDrawSk(sender.sockOut2Sk,sender.sockOut2LH,19)

mixerSk1 = [None]; mixerSk2 = [None]; mixerSkTyp = [None]

VMMapDictMixersDefs = {'GeometryNodeSwitch':[-1,-1,'Switch'],'ShaderNodeMixShader':[1,2,'Mix'],'ShaderNodeAddShader':[0,1,'Add'],'ShaderNodeMixRGB':[1,2,'Mix (Legacy)'],
        'ShaderNodeMath':[0,1,'Max'],'ShaderNodeVectorMath':[0,1,'Max'],'FunctionNodeBooleanMath':[0,1,'Or'],'FunctionNodeCompare':[-1,-1,'Compare'],
        'GeometryNodeCurveToMesh':[0,1,'Curve to Mesh'],'GeometryNodeInstanceOnPoints':[0,2,'Instance on Points'],'GeometryNodeMeshBoolean':[0,1,'Boolean'],
        'GeometryNodeStringJoin':[1,1,'Join'],'GeometryNodeJoinGeometry':[0,0,'Join'],'GeometryNodeGeometryToInstance':[0,0,'To Instance'],
        'CompositorNodeMixRGB':[1,2,'Mix'],'CompositorNodeMath':[0,1,'Max'],'CompositorNodeSwitch':[0,1,'Switch'],'CompositorNodeAlphaOver':[1,2,'Alpha Over'],
        'CompositorNodeSplitViewer':[0,1,'Split Viewer'],'CompositorNodeSwitchView':[0,1,'Switch View'],'TextureNodeMixRGB':[1,2,'Mix'],
        'TextureNodeMath':[0,1,'Max'],'TextureNodeTexture':[0,1,'Texture'],'TextureNodeDistance':[0,1,'Distance'],'ShaderNodeMix':[-1,-1,'Mix']}

VMMapDictSwitchType = {'VALUE':'FLOAT'}
VMMapDictUserSkName = {'VALUE':'Float','RGBA':'Color'}

def DoMix(context,who):
    tree = context.space_data.edit_tree
    if tree is not None:
        bpy.ops.node.add_node('INVOKE_DEFAULT', type=who, use_transform=True)
        aNd = tree.nodes.active
        aNd.width = 140
        if aNd.bl_idname:
            if aNd.bl_idname == {'ShaderNodeMath', 'ShaderNodeVectorMath', 'CompositorNodeMath', 'TextureNodeMath'}:
                aNd.operation = 'MAXIMUM'
            if aNd.bl_idname == 'FunctionNodeBooleanMath':
                aNd.operation = 'OR'
            elif aNd.bl_idname == 'FunctionNodeCompare':
                aNd.data_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
                aNd.operation = aNd.operation if aNd.data_type!='FLOAT' else 'EQUAL'
            elif aNd.bl_idname == 'GeometryNodeSwitch':
                aNd.input_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
            elif aNd.bl_idname == 'ShaderNodeMix':
                aNd.data_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
            elif aNd.bl_idname == 'TextureNodeTexture':
                aNd.show_preview = False
            if aNd.bl_idname in {'GeometryNodeSwitch', 'FunctionNodeCompare', 'ShaderNodeMix'}:
                tgl = aNd.bl_idname!='FunctionNodeCompare'; foundSkList = [sk for sk in (reversed(aNd.inputs) if tgl else aNd.inputs) if sk.type==mixerSkTyp[0]]
                tree.links.new(mixerSk1[0],foundSkList[tgl]); tree.links.new(mixerSk2[0],foundSkList[not tgl])
            else:
                if aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]].is_multi_input: tree.links.new(mixerSk2[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][1]])
                tree.links.new(mixerSk1[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]])
                if aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]].is_multi_input==False: tree.links.new(mixerSk2[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][1]])

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

def VoronoiPreviewerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]
    mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y)
    def MucGetWP(loc,offsetx): pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6,loc.y)[0]-pos[0]; return pos,rd

    def MucDrawSk(Sk,lh):
        txtlen = DrawText(PosViewToReg(mousePos.x,mousePos.y),[20,-5],Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,txtlen+48,0,GetSkCol(Sk) if GetDrawSettings('colored_marker') else (.9,.9,.9,1))

    if sender.sockOutSk is None:
        if GetDrawSettings('draw_socket'): wp = MucGetWP(mousePos,0); DrawWidePoint(wp[0],wp[1])
    else:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        col = GetSkCol(sender.sockOutSk) if GetDrawSettings('colored_line') else (1,1,1,1); wp = MucGetWP(sender.sockOutPs*uiFac[0],GetDrawSettings('socket_offset'))
        if GetDrawSettings('draw_line'): DrawLine(wp[0],mouseRegionPs,1,col,col)
        if GetDrawSettings('draw_socket'): DrawWidePoint(wp[0],wp[1],GetSkVecCol(sender.sockOutSk,2.2))
        MucDrawSk(sender.sockOutSk,sender.sockOutLH)

ShaderShadersWithColor = (
    'BSDF_ANISOTROPIC',
    'BSDF_DIFFUSE',
    'EMISSION',
    'BSDF_GLASS',
    'BSDF_GLOSSY',
    'BSDF_HAIR',
    'BSDF_HAIR_PRINCIPLED',
    'PRINCIPLED_VOLUME',
    'BACKGROUND',
    'BSDF_REFRACTION',
    'SUBSURFACE_SCATTERING',
    'BSDF_TOON',
    'BSDF_TRANSLUCENT',
    'BSDF_TRANSPARENT',
    'BSDF_VELVET',
    'VOLUME_ABSORPTION',
    'VOLUME_SCATTER'
)
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
    WayTr, WayNd = GetTreesWay(context,goalSk.node)
    hWyLen = len(WayTr)-1
    ixSkLastUsed = -1
    isZeroPreviewGen = True
    for cyc in range(hWyLen+1):
        nodeIn = None
        sockOut = None
        sockIn = None
        #Найти принимающий нод текущего уровня
        if cyc!=hWyLen:
            for nd in WayTr[cyc].nodes:
                if nd.type in ['GROUP_OUTPUT','OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','COMPOSITE','OUTPUT']:
                    if nodeIn is None: nodeIn = nd
                    elif nodeIn.location>goalSk.node.location: nodeIn = nd
        else:
            if context.space_data.tree_type:
                if 'ShaderNodeTree':
                    num = int(goalSk.node.type in ('VOLUME_ABSORPTION','VOLUME_SCATTER'))
                    for nd in WayTr[hWyLen].nodes:
                        if nd.type in ['OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT']:
                            sockIn = (
                                nd.inputs[
                                    num
                                    * (
                                        nd.type
                                        not in [
                                            'OUTPUT_WORLD',
                                            'OUTPUT_LIGHT',
                                            'OUTPUT',
                                        ]
                                    )
                                ]
                                if nd.is_active_output
                                else sockIn
                            )
                if 'CompositorNodeTree':
                    for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='VIEWER') else sockIn
                    if sockIn is None:
                        for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='COMPOSITE')and(nd.is_active_output) else sockIn
                if 'GeometryNodeTree':
                    for nd in WayTr[hWyLen].nodes:
                        sockIn = nd.inputs.get('Geometry') if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output) else sockIn
                        lis = [sk for sk in nd.inputs if sk.type=='GEOMETRY']
                        sockIn = lis[0] if sockIn is None and lis else sockIn
                        if sockIn is None:
                            try: sockIn = nd.inputs[0]
                            except:pass
                if 'TextureNodeTree':
                    for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='OUTPUT')and(nd.is_active_output) else sockIn
            nodeIn = sockIn.node
        #Определить сокет отправляющего нода
        sockOut = goalSk if cyc==0 else WayNd[cyc].outputs.get('voronoi_preview')
        sockOut = WayNd[cyc].outputs[ixSkLastUsed] if sockOut is None else sockOut
        #Определить сокет принимающего нода:
        for sl in sockOut.links:
            if sl.to_node==nodeIn: sockIn = sl.to_socket; ixSkLastUsed = GetSocketIndex(sockIn)
        if sockIn is None:
            sockIn = WayTr[cyc].outputs.get('voronoi_preview')
            if sockIn is None:
                WayTr[cyc].outputs.new('NodeSocketColor' if context.space_data.tree_type!='GeometryNodeTree' else 'NodeSocketGeometry','voronoi_preview')
                sockIn = nodeIn.inputs.get('voronoi_preview'); sockIn.hide_value = True; isZeroPreviewGen = False
        #Удобный сразу-в-шейдер
        if (
            (sockOut.type in ('RGBA'))
            and (cyc == hWyLen)
            and (len(sockIn.links) != 0)
            and (sockIn.links[0].from_node.type in ShaderShadersWithColor)
            and (isZeroPreviewGen)
            and len(sockIn.links[0].from_socket.links) == 1
        ):
            sockIn = sockIn.links[0].from_node.inputs.get('Color')
        nd_va = WayTr[0].nodes.get('Voronoi_Anchor')
        sockIn = nd_va.inputs[0] if nd_va else sockIn
        if (sockOut!=None)and(sockIn!=None)and((sockIn.name=='voronoi_preview')or(cyc==hWyLen)): WayTr[cyc].links.new(sockOut,sockIn)