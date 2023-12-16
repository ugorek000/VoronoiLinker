# !!! Disclaimer: Use the contents of this file at your own risk !!!
# 100% of the content of this file contains malicious code!!1

# !!! Отказ от ответственности: Содержимое этого файла является полностью случайно сгенерированными битами, включая этот дисклеймер тоже.
# Используйте этот файл на свой страх и риск.
#P.s. Использование этого файла полностью безопасно, продлевает жизнь вашего компьютера, и вообще избавляет от вирусов.

#Этот аддон создавался мной как самопис лично для меня и под меня; который я по доброте душевной, сделал публичным для всех желающих. Ибо результат получился потрясающий. Наслаждайтесь.
#P.s. Меня напрягают шатанины с лицензиями, так что лучше полюбуйтесь на предупреждения о вредоносном коде (о да он тут есть, иначе накой смысол?).

bl_info = {'name':"Voronoi Linker", 'author':"ugorek", #Так же спасибо "Oxicid" за большую для VL'а помощь.
           'version':(4,0,1), 'blender':(4,0,2), #2023.12.16
           'description':"Various utilities for nodes connecting, based on distance field.", 'location':"Node Editor", #Раньше здесь была запись 'Node Editor > Alt + RMB' в честь того, ради чего всё, но теперь VL "повсюду"!
           'warning':"", #Надеюсь не настанет тот момент, когда у VL будет предупреждение. Неработоспособность в Linux'е была очень близко к этому.
           'category':"Node",
           'wiki_url':"https://github.com/ugorek000/VoronoiLinker/wiki", 'tracker_url':"https://github.com/ugorek000/VoronoiLinker/issues"}

from builtins import len as length #Невозможность использования мобильной трёхбуквенной переменной с именем "len", мягко говоря... не удобно.
import bpy, blf, gpu, gpu_extras.batch
#С модулем gpu_extras чёрная магия творится. Просто так его импортировать, чтобы использовать "gpu_extras.batch.batch_for_shader()" -- не работает.
#А с импортом 'batch' использование 'batch.batch_for_shader()' -- тоже не работает. Неведомые мне нано-технологии.
import math, mathutils

import platform
isWin = platform.system()=='Windows'
#isLinux = platform.system()=='Linux'

isBlender4 = bpy.app.version[0]==4 #Для поддержки работы в предыдущих версиях. Нужно для комфортного осознания отсутствия напрягов при вынужденных переходах на старые версии,
# и получения дополнительной порции эндорфинов от возможности работы в разных версиях с разными версиями api.
#todo1 опуститься с поддержкой как можно ниже по версиям. Сейчас с гарантией: 3.6?, 4.0 и 4.1.

#def Vector(*data): return mathutils.Vector(data[0] if length(data)<2 else data)
def Vector(*args): return mathutils.Vector((args)) #Очень долго я охреневал от двойных скобок 'Vector((a,b))', и только сейчас допёр так сделать. Ну наконец-то настанет наслаждение.

voronoiAddonName = bl_info['name'].replace(" ","") #todo1 узнать разницу между названием аддона, именем аддона, именем файла, именем модуля, (мб ещё пакета); и ещё в установленных посмотреть.

#Текст ниже не переводится на другие языки. Потому что забыл. И нужно ли?.
voronoiAnchorClName = "Voronoi_Anchor"
voronoiAnchorDtName = "Voronoi_Anchor_Dist"
voronoiSkPreviewName = "voronoi_preview"
voronoiPreviewResultNdName = "SavePreviewResult"

#Где-то в комментариях могут использоваться словосочетание "тип редактора" -- то же самое что и "тип дерева"; имеются в виду 4 классических встроенных редактора, и они же, типы деревьев.

#У некоторых инструментов есть некоторые, одинаковые между собой константы, но со своими префиксами; разнесено для удобства, чтобы не "арендовать" у других инструментов.

list_classes = []
list_clsToAddon = []

class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = voronoiAddonName if __name__=="__main__" else __name__

list_kmiDefs = []
dict_setKmiCats = {'grt':set(), 'oth':set(), 'spc':set(), 'qqm':set(), 'cus':set()}

def TranslateIface(txt):
    return bpy.app.translations.pgettext_iface(txt)
def UiScale():
    return bpy.context.preferences.system.dpi/72

#Может быть стоит когда-нибудь добавить в свойства инструмента клавишу для модифицирования в процессе самого инструмента, например вариант Alt при Alt D для VQDT. Теперь ещё больше актуально для VWT.

def PowerArr4ToVec(arr, pw=1/2.2):
    return Vector(arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)

def GetUniformColVec(prefs):
    return PowerArr4ToVec(prefs.dsUniformColor)

def VecWorldToRegScale(vec, self):
    vec = vec*self.uiScale
    return mathutils.Vector( bpy.context.region.view2d.view_to_region(vec.x, vec.y, clip=False) )

def RecrGetNodeFinalLoc(nd):
    return nd.location+RecrGetNodeFinalLoc(nd.parent) if nd.parent else nd.location

def DisplayMessage(title, text, icon='NONE'):
    def PopupMessage(self, context):
        self.layout.label(text=text, icon=icon)
    bpy.context.window_manager.popup_menu(PopupMessage, title=title, icon='NONE')

#Актуальные нужды для VL, доступные на данный момент только через ОПА:
# 1. Является ли GeoViewer активным (по заголовку) и/или активно-просматривающим прямо сейчас?
# 2. Однозначное определение для контекста редактора, через какой именно нод на уровень выше, пользователь зашёл в текущую группу?
# 3. Как отличить общие классовые enum от уникальных enum для данного нода?
# наверняка есть ещё что, но я забыл.


dict_numToKey = {"1":'ONE', "2":'TWO', "3":'THREE', "4":'FOUR', "5":'FIVE', "6":'SIX', "7":'SEVEN', "8":'EIGHT', "9":'NINE', "0":'ZERO'}
def SmartAddToRegAndAddToKmiDefs(cls, txt, dict_props={}):
    global list_classes, list_kmiDefs
    if cls not in list_classes: #Благодаря этому назван как "Smart", и регистрация инструментов стала чуть проще.
        list_classes.append(cls)
    list_kmiDefs += [ (cls.bl_idname, dict_numToKey.get(txt[4:], txt[4:]), txt[0]=="S", txt[1]=="C", txt[2]=="A", txt[3]=="+", dict_props) ] #Тоже "Smart".

def GetUserKmNe():
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']


class PieData:
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
    pieAlignment = 0

def SetPieData(toolData, prefs):
    toolData.isSpeedPie = prefs.vPieType=='SPEED'
    toolData.pieScale = prefs.vPieScale
    toolData.pieDisplaySocketTypeInfo = prefs.vPieSocketDisplayType
    toolData.pieAlignment = prefs.vPieAlignment


def GetSkCol(sk):
    if sk.bl_idname=='NodeSocketUndefined':
        col = (1.0, 0.2, 0.2, 1.0)
    elif hasattr(sk,'draw_color'):
        col = sk.draw_color(bpy.context, sk.node)
    elif hasattr(sk,'draw_color_simple'): #Так вот оно как, магии стало меньше.
        col = sk.draw_color_simple()
    else:
        col = (1, 0, 1, 1)
    #Не брать прозрачность от сокетов.
    #Избавляться от отрицательных значений, что могут быть от аддонских сокетов.
    return (max(col[0], 0), max(col[1], 0), max(col[2], 0), 1.0)
    #todo1 придумать, как сделать более читаемый чёрный текст от чёрных аддонских сокетов.


class VlrtLinkRepeatingData: #См. VRT.
    #Сокет с нодом может удалиться, включая само дерево. Поэтому всё что не сокет -- нужно для проверки этого.
    tree = None #Если дерево удалится, то tree будет `<bpy_struct, GeometryNodeTree invalid>`, спасибо что не краш.
    lastNd1name = ""
    lastNd1Id = None
    lastNd2name = ""
    lastNd2Id = None
    lastSk1 = None #Для повторения, Out.
    lastSk2 = None #Для авто-повторения, In.
vlrtData = VlrtLinkRepeatingData()

def VlrtRememberLastSockets(sko, ski):
    #Это не высокоуровневая функция, так что тут нет проверки на существование обоих sko и ski.
    vlrtData.tree = (sko or ski).id_data
    if sko:
        vlrtData.lastNd1name = sko.node.name
        vlrtData.lastNd1Id = sko.node.as_pointer()
        vlrtData.lastSk1 = sko
        if ski: #ski без sko для VRT бесполезен; а ещё через две строчки ниже.
            vlrtData.lastNd2name = ski.node.name
            vlrtData.lastNd2Id = ski.node.as_pointer()
            vlrtData.lastSk2 = ski if ski.id_data==sko.id_data else None
def NewLinkAndRemember(sko, ski):
    DoLinkHH(sko, ski) #sko.id_data.links.new(sko, ski)
    VlrtRememberLastSockets(sko, ski)


def GetSkLabelName(sk):
    return sk.label if sk.label else sk.name

def NdSelectAndActive(ndTar):
    for nd in ndTar.id_data.nodes:
        nd.select = False
    ndTar.id_data.nodes.active = ndTar #Важно не только то, что только один он выделяется, но ещё и то, что он становится активным.
    ndTar.select = True

#Таблица полезности инструментов в аддонских деревьях (по умолчанию -- полезно):
# VLT
# VPT   Нет
# VPAT  Мб?
# VMT   Нет
# VQMT  Нет
# VRT
# VST
# VHT
# VMLT
# VEST  ?
# VLRT
# VQDT  Нет
# VICT  Нет
# VLTT
# VWT
# VLNST Нет
# VRNT

dict_typeToSkfBlid = {
    'SHADER':    'NodeSocketShader',
    'RGB':       'NodeSocketColor', #Для VLNST. #todo3 исследовать подробнее.
    'RGBA':      'NodeSocketColor',
    'VECTOR':    'NodeSocketVector',
    'VALUE':     'NodeSocketFloat',
    'STRING':    'NodeSocketString',
    'INT':       'NodeSocketInt',
    'BOOLEAN':   'NodeSocketBool',
    'ROTATION':  'NodeSocketRotation',
    'GEOMETRY':  'NodeSocketGeometry',
    'OBJECT':    'NodeSocketObject',
    'COLLECTION':'NodeSocketCollection',
    'MATERIAL':  'NodeSocketMaterial',
    'TEXTURE':   'NodeSocketTexture',
    'IMAGE':     'NodeSocketImage',
    'CUSTOM':    'NodeSocketVirtual'}
def CollapseSkTypeToBlid(sk):
    return dict_typeToSkfBlid.get(sk.type, "Vl_Unknow")

set_classicSocketsBlid = {'NodeSocketShader',  'NodeSocketColor',   'NodeSocketVector','NodeSocketFloat',     'NodeSocketString',  'NodeSocketInt',    'NodeSocketBool',
                          'NodeSocketRotation','NodeSocketGeometry','NodeSocketObject','NodeSocketCollection','NodeSocketMaterial','NodeSocketTexture','NodeSocketImage'}
def IsClassicSk(sk):
    if sk.bl_idname=='NodeSocketVirtual':
        return True
    else:
        return CollapseSkTypeToBlid(sk) in set_classicSocketsBlid

#Инструменты с одинаковыми callback'ами по топологии:
# VRT VRNT
# VWT VDT
# VMT VST VQDT
#Инструменты с одинаковыми callback'ами по идеи:
# VHT VLRT

#todo3 стоит паять дерево в self.tree

def AddThinSep(where, scaleY=0.25, scaleX=1.0):
    row = where.row(align=True)
    row.separator()
    row.scale_x = scaleX
    row.scale_y = scaleY

def LeftProp(where, who, prop):
    if True:
        row = where.row()
        row.alignment = 'LEFT'
        row.prop(who, prop)
    else:
        where.prop(who, prop)

def AddNiceColorProp(where, who, prop, align=False, txt="", ico='NONE', decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else TranslateIface(who.bl_rna.properties[prop].name)+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, prop, text="", icon=ico)
    rowProp.active = decor//2%2

def AddDisclosureProp(where, who, prop, txt=None, isActive=False, isWide=False): #Заметка: не может на всю ширину, если where -- row.
    tgl = getattr(who, prop)
    rowMain = where.row(align=True)
    rowProp = rowMain.row(align=True)
    rowProp.alignment = 'LEFT'
    txt = txt if txt else None #+":"*tgl
    rowProp.prop(who, prop, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=False)
    rowProp.active = isActive
    if isWide:
        rowPad = rowMain.row(align=True)
        rowPad.prop(who, prop, text=" ", emboss=False)
    return tgl
def AddClsBoxDiscl(where, who, prop, cls=None, isWide=False):
    colBox = where.box().column(align=True)
    if AddDisclosureProp(colBox, who, prop, txt=(cls.bl_label+voronoiTextToolSettings) if cls else None, isWide=isWide):
        rowTool = colBox.row()
        rowTool.separator()
        colTool = rowTool.column(align=True)
        return colTool
    return None

def AddHandSplitProp(where, who, txt, tgl=True, isReturnLy=False):
    spl = where.row().split(factor=0.38, align=True)
    spl.active = tgl
    row = spl.row(align=True)
    row.alignment = 'RIGHT'
    prop = who.rna_type.properties[txt]
    isNotBool = prop.type!='BOOLEAN'
    row.label(text=prop.name*isNotBool)
    if (not tgl)and(prop.type=='FLOAT')and(prop.subtype=='COLOR'):
        box = spl.box()
        box.label()
        box.scale_y = 0.5
        row.active = False
    else:
        if not isReturnLy:
            spl.prop(who, txt, text="" if isNotBool else None)
        else:
            return spl

def AddStencilKeyProp(where, prefs, prop):
    rowProp = where.row()
    AddNiceColorProp(rowProp, prefs, prop)
    #return #todo3 я так и не врубился как пользоваться вашими prop event'ами, жуть какая-то. Помощь извне не помешала бы.
    rowUrl = rowProp.row()
    rowUrl.operator('wm.url_open', text="", icon='URL').url="https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text="+getattr(prefs, prop)
    rowUrl.active = False

def PrepareShaders(self):
    self.gpuLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    self.gpuArea = gpu.shader.from_builtin('UNIFORM_COLOR')
    #Параметры, которые не нужно устанавливать каждый раз:
    self.gpuLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
    #todo1 выяснить как или сделать сглаживание для полигонов тоже.
    #self.gpuLine.uniform_float('lineSmooth', True) #Нет нужды, по умолчанию True.
def DrawWay(self, vpos, vcol, wid):
    gpu.state.blend_set('ALPHA') #Рисование текста сбрасывает метку об альфе, поэтому устанавливается каждый раз.
    self.gpuLine.bind()
    self.gpuLine.uniform_float('lineWidth', wid)
    gpu_extras.batch.batch_for_shader(self.gpuLine, 'LINE_STRIP', {'pos':vpos, 'color':vcol}).draw(self.gpuLine)
def DrawAreaFan(self, vpos, col):
    gpu.state.blend_set('ALPHA')
    self.gpuArea.bind()
    self.gpuArea.uniform_float('color', col)
    gpu_extras.batch.batch_for_shader(self.gpuArea, 'TRI_FAN', {'pos':vpos}).draw(self.gpuArea)

#"Низкоуровневое" рисование:
def DrawLine(self, pos1, pos2, siz=1, col1=(1.0, 1.0, 1.0, 0.75), col2=(1.0, 1.0, 1.0, 0.75)):
    DrawWay(self, (pos1,pos2), (col1,col2), siz)
def DrawStick(self, prefs, pos1, pos2, col1, col2):
    rd = 1.0#(VecWorldToRegScale(Vector(pos1.x+prefs.dsPointRadius*1000, pos1.y), self)[0]-VecWorldToRegScale(pos1, self)[0])/1000
    DrawLine(self, VecWorldToRegScale(pos1, self), VecWorldToRegScale(pos2, self), prefs.dsLineWidth*rd, col1, col2) 
def DrawRing(self, pos, rd, siz=1, col=(1.0, 1.0, 1.0, 0.75), rotation=0.0, resolution=16):
    vpos = [];  vcol = []
    for cyc in range(resolution+1):
        vpos.append( (rd*math.cos(cyc*2*math.pi/resolution+rotation)+pos[0], rd*math.sin(cyc*2*math.pi/resolution+rotation)+pos[1]) )
        vcol.append(col)
    DrawWay(self, vpos, vcol, siz)
def DrawCircle(self, pos, rd, col=(1.0, 1.0, 1.0, 0.75), resolution=54):
    #Первая вершина гордо в центре круга, остальные по кругу. Нужно было чтобы артефакты сглаживания были красивыми в центр, а не наклонёнными в куда-то бок.
    vpos = ( (pos[0],pos[1]), *( (rd*math.cos(cyc*2.0*math.pi/resolution)+pos[0], rd*math.sin(cyc*2.0*math.pi/resolution)+pos[1]) for cyc in range(resolution+1) ) )
    DrawAreaFan(self, vpos, col)
def DrawRectangle(self, pos1, pos2, col):
    DrawAreaFan(self, ( (pos1[0],pos1[1]), (pos2[0],pos1[1]), (pos2[0],pos2[1]), (pos1[0],pos2[1]) ), col)

#"Высокоуровневое" рисование:
def DrawSocketArea(self, prefs, sk, list_boxHeiBou, colfac=Vector(1.0, 1.0, 1.0, 1.0)):
    loc = RecrGetNodeFinalLoc(sk.node)
    pos1 = VecWorldToRegScale(Vector(loc.x, list_boxHeiBou[0]), self)
    pos2 = VecWorldToRegScale(Vector(loc.x+sk.node.width, list_boxHeiBou[1]), self)
    colfac = colfac if prefs.dsIsColoredSkArea else GetUniformColVec(prefs)
    DrawRectangle(self, pos1, pos2, Vector(1.0, 1.0, 1.0, prefs.dsSocketAreaAlpha)*colfac)
def DrawIsLinkedMarker(self, prefs, loc, ofs, skCol):
    ofs[0] += ( (20*prefs.dsIsDrawText+prefs.dsDistFromCursor)*1.5+prefs.dsFrameOffset )*math.copysign(1,ofs[0])+4
    vec = VecWorldToRegScale(loc, self)
    skCol = skCol if prefs.dsIsColoredMarker else GetUniformColVec(prefs)
    grayCol = 0.65
    col1 = (0.0, 0.0, 0.0, 0.5) #Тень
    col2 = (grayCol, grayCol, grayCol, max(max(skCol[0],skCol[1]),skCol[2])*0.9/2) #Прозрачная белая обводка
    col3 = (skCol[0], skCol[1], skCol[2], 0.925) #Цветная основа
    def DrawMarkerBacklight(tgl, res=16):
        rot = math.pi/res if tgl else 0.0
        DrawRing(self, (vec[0]+ofs[0],     vec[1]+5.0+ofs[1]), 9.0, 3, col2, rot, res)
        DrawRing(self, (vec[0]+ofs[0]-5.0, vec[1]-3.5+ofs[1]), 9.0, 3, col2, rot, res)
    DrawRing(self, (vec[0]+ofs[0]+1.5, vec[1]+3.5+ofs[1]), 9.0, 3, col1)
    DrawRing(self, (vec[0]+ofs[0]-3.5, vec[1]-5.0+ofs[1]), 9.0, 3, col1)
    DrawMarkerBacklight(True) #Маркер рисуется с артефактами "дырявых пикселей". Закостылить их дублированной отрисовкой с вращением.
    DrawMarkerBacklight(False) #Но из-за этого нужно уменьшить альфу белой обводки в два раза.
    DrawRing(self, (vec[0]+ofs[0],     vec[1]+5.0+ofs[1]), 9.0, 1, col3)
    DrawRing(self, (vec[0]+ofs[0]-5.0, vec[1]-3.5+ofs[1]), 9.0, 1, col3)
def DrawWidePoint(self, prefs, loc, colfac=Vector(1.0, 1.0, 1.0, 1.0), resolution=54, forciblyCol=False): #"forciblyCol" нужен только для DrawDebug'а.
    #Подготовка:
    pos = VecWorldToRegScale(loc, self)
    loc = Vector(loc.x+6*prefs.dsPointRadius*1000, loc.y) #Радиус точки вычисляется через мировое пространство. Единственный из двух, кто зависит от зума в редакторе. Второй -- коробка-подсветка сокетов.
    #Умножается и делится на 1000, чтобы радиус не прилипал к целым числам и тем самым был красивее. Конвертация в экранное пространство даёт только целочисленный результат.
    rd = (VecWorldToRegScale(loc, self)[0]-pos[0])/1000 #todo1 теперь настало очередь и это сделать более адекватным и "легальным" образом.
    #Рисование:
    col1 = Vector(0.5, 0.5, 0.5, 0.4)
    col2 = col1
    col3 = Vector(1.0, 1.0, 1.0, 1.0)
    colfac = colfac if (prefs.dsIsColoredPoint)or(forciblyCol) else GetUniformColVec(prefs)
    rd = (rd*rd+10)**0.5
    DrawCircle(self, pos, rd+3.0, col1*colfac, resolution)
    DrawCircle(self, pos, rd,     col2*colfac, resolution)
    DrawCircle(self, pos, rd/1.5, col3*colfac, resolution)
def DrawText(self, prefs, pos, ofs, txt, drawCol, fontSizeOverwrite=0):
    if prefs.dsIsAllowTextShadow:
        blf.enable(self.fontId, blf.SHADOW)
        muv = prefs.dsShadowCol
        blf.shadow(self.fontId, (0, 3, 5)[prefs.dsShadowBlur], muv[0], muv[1], muv[2], muv[3])
        muv = prefs.dsShadowOffset
        blf.shadow_offset(self.fontId, muv[0], muv[1])
    else: #Большую часть времени бесполезно, но нужно использовать, когда опция рисования тени переключается.
        blf.disable(self.fontId, blf.SHADOW)
    frameOffset = prefs.dsFrameOffset
    blf.size(self.fontId, prefs.dsFontSize*(not fontSizeOverwrite)+fontSizeOverwrite)
    #От "текста по факту" не вычисляется, потому что тогда каждая рамка каждый раз будет разной высоты в зависимости от текста.
    #Спецсимвол нужен, как общий случай, чтобы покрыть максимальную высоту. Остальные символы нужны для особых шрифтов, что могут быть выше чем █.
    #Но этого недостаточно, некоторые буквы некоторых шрифтов могут вылезти за рамку. Это не чинится, ибо изначально всё было вылизано и отшлифовано для Consolas.
    #И если починить это для всех шрифтов, то тогда рамка для Consolas'а потеряет красоту.
    #P.s. Consolas -- мой самый любимый шрифт после Comic Sans.
    #Если вы хотите тру-центрирование -- сделайте это сами.
    txtDim = (blf.dimensions(self.fontId, txt)[0], blf.dimensions(self.fontId, "█GJKLPgjklp!?")[1])
    pos = VecWorldToRegScale(pos, self)
    pos = (pos[0]-(txtDim[0]+frameOffset+10)*(ofs[0]<0)+(frameOffset+1)*(ofs[0]>-1), pos[1]+frameOffset)
    pw = 1/1.975 #Осветлить текст. Почему 1.975 -- не помню.
    placePosY = round( (txtDim[1]+frameOffset*2)*ofs[1] ) #Без округления красивость горизонтальных линий пропадет.
    pos1 = (pos[0]+ofs[0]-frameOffset,              pos[1]+placePosY-frameOffset)
    pos2 = (pos[0]+ofs[0]+10+txtDim[0]+frameOffset, pos[1]+placePosY+txtDim[1]+frameOffset)
    gradientResolution = 12
    girderHeight = 1/gradientResolution*(txtDim[1]+frameOffset*2)
    #Рамка для текста
    if prefs.dsDisplayStyle=='CLASSIC': #Красивая рамка
        #Прозрачный фон:
        def Fx(x, a, b):
            return ((x+b)/(b+1))**0.6*(1-a)+a
        for cyc in range(gradientResolution):
            DrawRectangle(self, (pos1[0], pos1[1]+cyc*girderHeight), (pos2[0], pos1[1]+cyc*girderHeight+girderHeight), (drawCol[0]/2, drawCol[1]/2, drawCol[2]/2, Fx(cyc/gradientResolution,0.2,0.05)) )
        #Яркая основная обводка:
        col = (drawCol[0]**pw, drawCol[1]**pw, drawCol[2]**pw, 1.0)
        DrawLine(self,       pos1,        (pos2[0],pos1[1]), 1, col, col)
        DrawLine(self, (pos2[0],pos1[1]),        pos2,       1, col, col)
        DrawLine(self,       pos2,        (pos1[0],pos2[1]), 1, col, col)
        DrawLine(self, (pos1[0],pos2[1]),        pos1,       1, col, col)
        #Мягкая дополнительная обводка, придающая красоты:
        col = (col[0], col[1], col[2], 0.375)
        lineOffset = 2.0
        DrawLine(self, (pos1[0], pos1[1]-lineOffset), (pos2[0], pos1[1]-lineOffset), 1, col, col)
        DrawLine(self, (pos2[0]+lineOffset, pos1[1]), (pos2[0]+lineOffset, pos2[1]), 1, col, col)
        DrawLine(self, (pos2[0], pos2[1]+lineOffset), (pos1[0], pos2[1]+lineOffset), 1, col, col)
        DrawLine(self, (pos1[0]-lineOffset, pos2[1]), (pos1[0]-lineOffset, pos1[1]), 1, col, col)
        #Уголки. Их маленький размер -- маскировка под тру-скругление:
        DrawLine(self, (pos1[0]-lineOffset, pos1[1]), (pos1[0], pos1[1]-lineOffset), 1, col, col)
        DrawLine(self, (pos2[0]+lineOffset, pos1[1]), (pos2[0], pos1[1]-lineOffset), 1, col, col)
        DrawLine(self, (pos2[0]+lineOffset, pos2[1]), (pos2[0], pos2[1]+lineOffset), 1, col, col)
        DrawLine(self, (pos1[0]-lineOffset, pos2[1]), (pos1[0], pos2[1]+lineOffset), 1, col, col)
    elif prefs.dsDisplayStyle=='SIMPLIFIED': #Для тех, кому не нравится красивая рамка; и чем им красивая не понравилась?.
        DrawRectangle( self, (pos1[0], pos1[1]), (pos2[0], pos2[1]), (drawCol[0]/2.4, drawCol[1]/2.4, drawCol[2]/2.4, 0.8) )
        col = (0.1, 0.1, 0.1, 0.95)
        DrawLine(self,       pos1,        (pos2[0],pos1[1]), 2, col, col)
        DrawLine(self, (pos2[0],pos1[1]),        pos2,       2, col, col)
        DrawLine(self,       pos2,        (pos1[0],pos2[1]), 2, col, col)
        DrawLine(self, (pos1[0],pos2[1]),        pos1,       2, col, col)
    #Сам текст:
    blf.position(self.fontId, pos[0]+ofs[0]+3.5, pos[1]+placePosY+txtDim[1]*0.3, 0)
    blf.color(   self.fontId, drawCol[0]**pw, drawCol[1]**pw, drawCol[2]**pw, 1.0)
    blf.draw(    self.fontId, txt)
    return (txtDim[0]+frameOffset, txtDim[1]+frameOffset*2)
def DrawSkText(self, prefs, pos, ofs, fgSk, fontSizeOverwrite=0):
    if not prefs.dsIsDrawText:
        return [1, 0] #'1' нужен для сохранения информации для направления для позиции маркеров.
    skCol = GetSkCol(fgSk.tg) if prefs.dsIsColoredText else GetUniformColVec(prefs)
    txt = fgSk.name if fgSk.tg.bl_idname!='NodeSocketVirtual' else TranslateIface('Virtual')
    return DrawText(self, prefs, pos, ofs, txt, skCol, fontSizeOverwrite)

#Шаблоны:

def StencilStartDrawCallback(self, context):
    if self.whereActivated!=context.space_data: #Нужно, чтобы рисовалось только в активном редакторе, а не во всех у кого открыто то же самое дерево.
        return None
    PrepareShaders(self)
    prefs = self.prefs
    if prefs.dsIsDrawDebug:
        DrawDebug(self, prefs, context)
    return prefs

def DrawDoubleNone(self, prefs, context):
    cusorPos = context.space_data.cursor_location
    col = Vector(1, 1, 1, 1) if prefs.dsIsColoredPoint else GetUniformColVec(prefs)
    vec = Vector(prefs.dsPointOffsetX*0.75, 0)
    if (prefs.dsIsDrawLine)and(prefs.dsIsAlwaysLine):
        DrawStick(self, prefs, cusorPos-vec, cusorPos+vec, col, col)
    if prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos-vec, col)
        DrawWidePoint(self, prefs, cusorPos+vec, col)
def CallbackDrawEditTreeIsNone(self, context): #Именно. Ибо эстетика. Вдруг пользователь потеряется; нужно подать признаки жизни.
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    if prefs.dsIsDrawPoint:
        cusorPos = context.space_data.cursor_location
        if getattr(self,'isDrawDoubleNone', False):
            DrawDoubleNone(self, prefs, context)
        else:
            DrawWidePoint(self, prefs, cusorPos)

def DrawDebug(self, prefs, context):
    def DebugTextDraw(pos, txt, r, g, b):
        blf.size(0,18);  blf.position(0, pos[0]+10,pos[1], 0);  blf.color(0, r,g,b,1.0);  blf.draw(0, txt)
    cusorPos = context.space_data.cursor_location
    DebugTextDraw(VecWorldToRegScale(cusorPos, self), "Cursor position here.", 1, 1, 1)
    if not context.space_data.edit_tree:
        return
    col = Vector(1, 0.5, 0.5, 1)
    list_nodes = GetNearestNodes(context.space_data.edit_tree.nodes, cusorPos, self.uiScale)
    if not list_nodes:
        return
    DrawStick(self, prefs, cusorPos, list_nodes[0].pos, col, col)
    sco = 0
    for li in list_nodes:
        DrawWidePoint(self, prefs, li.pos, col, 4, True)
        DebugTextDraw(VecWorldToRegScale(li.pos, self), str(sco)+" Node goal here", col.x, col.y, col.z)
        sco += 1
    list_fgSksIn, list_fgSksOut = GetNearestSockets(list_nodes[0].tg, cusorPos, self.uiScale)
    if list_fgSksIn:
        DrawWidePoint(self, prefs, list_fgSksIn[0].pos, Vector(0.5, 1, 0.5, 1), 4, True)
        DebugTextDraw(VecWorldToRegScale(list_fgSksIn[0].pos, self), "Nearest socketIn here", 0.5, 1, 0.5)
    if list_fgSksOut:
        DrawWidePoint(self, prefs, list_fgSksOut[0].pos, Vector(0.5, 0.5, 1, 1), 4, True)
        DebugTextDraw(VecWorldToRegScale(list_fgSksOut[0].pos, self), "Nearest socketOut here", 0.75, 0.75, 1)

def DrawNodeStencil(self, prefs, cusorPos, pos):
    colNode = PowerArr4ToVec(prefs.dsNodeColor)
    col = colNode if prefs.dsIsColoredLine else GetUniformColVec(prefs)
    if prefs.dsIsDrawLine:
        DrawStick(self, prefs, pos, cusorPos, col, col)
    if prefs.dsIsDrawPoint:
        DrawWidePoint( self, prefs, pos, colNode if prefs.dsIsColoredPoint else GetUniformColVec(prefs) )
    return colNode
def DrawTextNodeStencil(self, prefs, cusorPos, nd, col=Vector(1, 1, 1, 1), ofs=0.0):
    if not prefs.dsIsDrawText:
        return
    def DrawNodeText(txt, side=1.0, ofs=0.0):
        if txt:
            DrawText(self, prefs, cusorPos, (prefs.dsDistFromCursor*side, -0.5+ofs), txt, col)
    col = col if prefs.dsIsColoredText else GetUniformColVec(prefs)
    txt_label = nd.label
    side = prefs.vdsLabelSideRight*2-1
    match prefs.vdsDrawNodeNameLabel:
        case 'NAME':
            DrawNodeText(nd.name, side=-side, ofs=ofs)
        case 'LABEL':
            DrawNodeText(txt_label if txt_label else None, side=side, ofs=ofs)
        case 'LABELNAME':
            if not txt_label:
                DrawNodeText(nd.name, side=-side, ofs=ofs)
                return
            DrawText(self, prefs, cusorPos, (prefs.dsDistFromCursor*-side, -0.5+ofs), nd.name, col)
            DrawText(self, prefs, cusorPos, (prefs.dsDistFromCursor*side, -0.5+ofs), txt_label, col)
def DrawNodeStencilFull(self, prefs, cusorPos, fg, isCanText=True, ofs=0.0):
    if fg:
        #Нод не имеет цвета (в этом аддоне вся тусовка ради сокетов, так что нод не имеет цвета, ок да?.)
        #Поэтому, для нода всё одноцветное -- пользовательское для нода, или пользовательское постоянной альтернативы.
        colNode = DrawNodeStencil(self, prefs, cusorPos, fg.pos)
        if isCanText:
            DrawTextNodeStencil(self, prefs, cusorPos, fg.tg, col=colNode, ofs=ofs)
        else:
            return colNode #Для VEST.
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
    return False

def GetSkColPowVec(sk, pw=1/2.2):
    return PowerArr4ToVec(GetSkCol(sk), pw=pw)

#Высокоуровневый шаблон рисования для сокетов; тут весь аддон про сокеты, поэтому в названии нет "Sk".
#Пользоваться этим шаблоном невероятно кайфово, после того хардкора что был в ранних версиях (даже не заглядывайте туда, там около-ад).
def DrawToolOftenStencil(self, prefs, cusorPos, list_twoTgSks, #Одинаковое со всех инструментов вынесено в этот шаблон.
                         isLineToCursor=False,
                         textSideFlip=False,
                         isDrawText=True,
                         isDrawMarkersMoreTharOne=False,
                         isDrawOnlyArea=False):
    def GetVecOffsetFromSk(sk, y=0.0):
        return Vector(prefs.dsPointOffsetX*((sk.is_output)*2-1), y)
    #Вся суета ради линии:
    if (prefs.dsIsDrawLine)and(not isDrawOnlyArea):
        len = length(list_twoTgSks)
        if prefs.dsIsColoredLine:
            col1 = GetSkCol(list_twoTgSks[0].tg)
            col2 = Vector(1, 1, 1, 1) if prefs.dsIsColoredPoint else GetUniformColVec(prefs)
            col2 = col2 if (isLineToCursor)or(len==1) else GetSkCol(list_twoTgSks[1].tg)
        else:
            col1 = GetUniformColVec(prefs)
            col2 = col1
        if len>1: #Ниже могут нарисоваться две палки одновременно. Эта забота для вызывающей стороны.
            DrawStick(self, prefs, list_twoTgSks[0].pos+GetVecOffsetFromSk(list_twoTgSks[0].tg), list_twoTgSks[1].pos+GetVecOffsetFromSk(list_twoTgSks[1].tg), col1, col2)
        if isLineToCursor:
            DrawStick(self, prefs, list_twoTgSks[0].pos+GetVecOffsetFromSk(list_twoTgSks[0].tg), cusorPos, col1, col2)
    #Всё остальное:
    for li in list_twoTgSks:
        if prefs.dsIsDrawSkArea:
            DrawSocketArea( self, prefs, li.tg, li.boxHeiBound, GetSkColPowVec(li.tg) )
        if (prefs.dsIsDrawPoint)and(not isDrawOnlyArea):
            DrawWidePoint( self, prefs, li.pos+GetVecOffsetFromSk(li.tg), GetSkColPowVec(li.tg) )
    if isDrawText:
        for li in list_twoTgSks:
            side = (textSideFlip*2-1)
            txtDim = DrawSkText(self, prefs, cusorPos, (prefs.dsDistFromCursor*(li.tg.is_output*2-1)*side, -0.5), li)
            #В условии ".links", но не ".is_linked", потому что линки могут быть выключены (замьючены, красные)
            if (prefs.dsIsDrawMarker)and( (li.tg.links)and(not isDrawMarkersMoreTharOne)or(length(li.tg.links)>1) ):
                DrawIsLinkedMarker( self, prefs, cusorPos, [txtDim[0]*(li.tg.is_output*2-1)*side, 0], GetSkCol(li.tg) )

#Todo1 Головная боль с "проскальзывающими" кадрами!! Debug, Collapse, Alt, и вообще везде.

def DrawSidedSkText(self, prefs, cusorPos, fg, ofsY, facY):
    txtDim = DrawSkText(self, prefs, cusorPos, (prefs.dsDistFromCursor*(fg.tg.is_output*2-1), ofsY), fg)
    if (fg.tg.links)and(prefs.dsIsDrawMarker):
        DrawIsLinkedMarker( self, prefs, cusorPos, [txtDim[0]*(fg.tg.is_output*2-1), txtDim[1]*facY*0.75], GetSkCol(fg.tg) )

def GetOpKmi(self, event): #todo0 есть ли концепция или способ правильнее?
    tuple_tar = (event.type, event.shift, event.ctrl, event.alt)
    txt_toolBlId = getattr(bpy.types, self.bl_idname).bl_idname
    #Оператор может иметь несколько комбинаций вызова, все из которых будут одинаковы по ключу в `keymap_items`, поэтому перебираем всех вручную
    for li in GetUserKmNe().keymap_items:
        if li.idname==txt_toolBlId:
            #Заметка: искать и по соответствию самой клавише тоже, модификаторы тоже могут быть одинаковыми у нескольких вариантах вызова.
            if (li.type==tuple_tar[0])and(li.shift_ui==tuple_tar[1])and(li.ctrl_ui==tuple_tar[2])and(li.alt_ui==tuple_tar[3]):
                #Заметка: могут быть и два идентичных хоткеев вызова, но Blender будет выполнять только один из них (по крайней мере для VL), тот, который будет первее в списке.
                return li # Эта функция также выдаёт первого в списке.
def ForseSetSelfNonePropToDefault(kmi, self):
    if not kmi:
        return
    #Если в keymap в вызове оператора не указаны его свойства, они читаются от последнего вызова. Эта функция призвана устанавливать их обратно по умолчанию.
    for li in self.rna_type.properties:
        if li.identifier!='rna_type':
            #Заметка: определить установленность в kmi -- наличие `kmi.properties[li.identifier]`.
            setattr(self, li.identifier, getattr(kmi.properties, li.identifier)) #Ради этого мне пришлось реверсинженерить Blender с отладкой. А ларчик просто открывался...

class VoronoiOp(bpy.types.Operator):
    bl_options = {'UNDO'} #Вручную созданные линки undo'тся, так что и в VL ожидаемо тоже. И вообще для всех.
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' #Не знаю, зачем это нужно, но пусть будет.
class VoronoiTool(VoronoiOp): #Корень для инструментов.
    #Всегда неизбежно происходит кликанье в дереве, где обитают ноды, поэтому для всех инструментов
    isPassThrough: bpy.props.BoolProperty(name="Pass through node selecting", description="Clicking over a node activates selection, not the tool", default=False)
    #Заметка: NextAssignment имеется у всех; и теперь он одинаков по количеству параметров, чтобы проще обрабатываться шаблонами.
    def __del__(self): #Для EdgePan.
        #todo3 Опять запары, _del_ не вызывается, если отпустить за пределами региона. И хрен с ним. Потом что-нибудь придумаю. См. StopEdpePanBug()
        edgePanData.isWorking = False
class VoronoiToolSk(VoronoiTool):
    pass
class VoronoiToolDblSk(VoronoiToolSk):
    isCanBetweenFields: bpy.props.BoolProperty(name="Can between fields", description="Tools can connecting between different field types", default=True)
class VoronoiToolNd(VoronoiTool):
    pass
class VoronoiToolSkNd(VoronoiToolSk, VoronoiToolNd):
    pass


set_skTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}
def SkBetweenFieldsCheck(self, sk1, sk2):
    #Заметка: учитывая предназначение и название этой функции, sk1 и sk2 в любом случае должны быть из полей, и только из них.
    return (sk1.type in set_skTypeFields)and( (self.isCanBetweenFields)and(sk2.type in set_skTypeFields)or(sk1.type==sk2.type) )

def MinFromFgs(fgSk1, fgSk2):
    if (fgSk1)or(fgSk2): #Если хотя бы один из них существует.
        if not fgSk2: #Если одного из них не существует,
            return fgSk1
        elif not fgSk1: # то остаётся однозначный выбор для второго.
            return fgSk2
        else: #Иначе выбрать ближайшего.
            return fgSk1 if fgSk1.dist<fgSk2.dist else fgSk2
    return None


#Мейнстримные шаблоны, отсортированные в порядке по нахождению в коде:

def StencilUnCollapseNode(nd, tar=True):
    if tar: #Стало проще, но избавляться от этой функции не стоит, потому что количество вызовов особо не изменилось, ибо 'isBoth'.
        result = nd.hide
        nd.hide = False
        return result
    return False

def StencilReNext(self, context, *naArgs):
    #Алерт! 'DRAW_WIN' вызывает краш для некоторых редких деревьев со свёрнутыми нодами! Было бы неплохо забагрепортить бы это, если бы ещё знать как это отловить.
    bpy.ops.wm.redraw_timer(type='DRAW', iterations=0) #Заставляет курсор меняться на мгновенье (по крайней мере на винде).
    #Заметка: осторожно с вызовом StencilReNext() в NextAssignment(), чтобы не уйти в вечный цикл!
    self.NextAssignment(context, *naArgs) #Заметка: не забывать разворачивать.

class EdgePanData:
    rect = None
    #Накостылил по-быстрому:
    isWorking = False
    area = None
    view2d = None
    curPos = Vector(0,0)
    uiScale = 1.0
    regionCenter = Vector(0,0)
    delta = 0.0 #Ох уж эти ваши дельты.
    izoomFac = 0.5
edgePanData = EdgePanData()
import time
def TimerEdgePan():
    delta = time.time()-edgePanData.delta
    vec = edgePanData.curPos*edgePanData.uiScale
    field0 = mathutils.Vector( edgePanData.view2d.view_to_region(vec.x, vec.y, clip=False) )
    #Ещё немного реймарчинга:
    field1 = field0-edgePanData.regionCenter
    field2 = Vector(abs(field1.x), abs(field1.y))
    field2 = field2-edgePanData.regionCenter+Vector(5,5) #Слегка уменьшить для курсора, находящегося вплотную к краю экрана.
    field2 = Vector(max(field2.x, 0), max(field2.y, 0))
    field3 = Vector(math.copysign(field2.x, field1.x), math.copysign(field2.y, field1.y))
    ##
    xi, yi, xa, ya = edgePanData.rect.GetRaw()
    speedZoomSize = Vector(xa-xi, ya-yi)/2.5*delta #125 без дельты.
    edgePanData.rect.TranslateScaleFac((math.copysign(speedZoomSize.x, field3.x) if field3.x else 0.0, math.copysign(speedZoomSize.y, field3.y) if field3.y else 0.0), edgePanData.izoomFac)
    edgePanData.delta = time.time() #"Отправляется в неизвестность" перед следующим заходом.
    edgePanData.area.tag_redraw()
    return 0.0 if edgePanData.isWorking else None
def StencilInitEdgePan(context, prefs, uiScale):
    edgePanData.rect = View2D.get_rect(context.region.view2d)
    edgePanData.isWorking = True
    edgePanData.area = context.area
    edgePanData.curPos = context.space_data.cursor_location
    edgePanData.uiScale = uiScale
    edgePanData.view2d = context.region.view2d
    edgePanData.regionCenter = Vector(context.region.width/2, context.region.height/2)
    edgePanData.delta = time.time() #..А ещё есть "слегка-границы".
    edgePanData.izoomFac = 1.0-prefs.vEdgePanFac
    bpy.app.timers.register(TimerEdgePan, first_interval=0.0)

def StencilMouseNext(self, context, event, *naArgs):
    context.area.tag_redraw()
    match event.type:
        case 'MOUSEMOVE':
            self.NextAssignment(context, *naArgs)
        case self.kmi.type|'ESC': #Раньше было `self.keyType` и `.. = kmi.type`, теперь имеется полный kmi.
            return True
    return False
def StencilMouseNextAndRepick(self, context, event, keyRepick, *naArgsDouble):
    context.area.tag_redraw()
    half = length(naArgsDouble)//2
    if event.type==keyRepick:
        self.repickState = event.value=='PRESS'
        if self.repickState: #Дублирование от ниже. Не знаю как придумать это за один заход.
            self.NextAssignment(context, *naArgsDouble[half:])
    else:
        match event.type:
            case 'MOUSEMOVE':
                if self.repickState: #Требует существования, забота вызывающей стороны.
                    self.NextAssignment(context, *naArgsDouble[half:])
                else:
                    self.NextAssignment(context, *naArgsDouble[:half])
            case self.kmi.type|'ESC':
                return True
    return False

#todo1 обработать все комбинации в n^3: space_data.tree_type и space_data.edit_tree.bl_idname; классическое, потерянное, и аддонское; привязанное и не привязанное к редактору.
#todo1 И потом работоспособность всех инструментов в них. А потом проверить в существующем дереве взаимодействие потерянного сокета у потерянного нода для инструментов.
#todo1 выяснить подробнее для VLT: #context.area.tag_redraw(), перерисовывается само по себе, но для некоторых инструментов в кастомных деревьях если у нодов нет сокетов.. что-то не работает.

set_quartetClassicTreeBlids = {'ShaderNodeTree','GeometryNodeTree','CompositorNodeTree','TextureNodeTree'}
def UselessForCustomUndefTrees(context, isForCustom=True, isForUndef=True): #'isForCustom' ради VPAT. Второй для компании.
    tree = context.space_data.edit_tree
    if not tree:
        if context.space_data.tree_type not in set_quartetClassicTreeBlids: #"Но если в аддонском дереве, то пусть теряется))00)0"; см. CallbackDrawEditTreeIsNone().
            return {'FINISHED'} #CANCELLED
        else:
            return {}
    idname = tree.bl_idname
    if (isForUndef)and(idname=='NodeTreeUndefined'): #Для поломанного дерева space_data.tree_type==''. А я то думал это просто ссылка.
        return {'CANCELLED'} #В отличие от StencilModalEsc(), здесь покидается для не-рисования.
    elif (isForCustom)and(idname not in set_quartetClassicTreeBlids):
        return {'PASS_THROUGH'} #CANCELLED
    return {}

def StencilModalEsc(self, context, event):
    def StopEdpePanBug():
        edgePanData.isWorking = False
    if event.type=='ESC': #Собственно то, что и должна делать клавиша побега.
        StopEdpePanBug()
        return {'CANCELLED'}
    if event.value!='RELEASE':
        return {'RUNNING_MODAL'}
    try: #См. draw_handler_remove в StencilToolWorkPrepare.
        bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
    except:
        pass
    if not context.space_data.edit_tree:
        StopEdpePanBug()
        return {'FINISHED'}
    RestoreCollapsedNodes(context.space_data.edit_tree.nodes)
    #В потерянном дереве любому инструменту нечего-то особо делать, поэтому принесено сюда в шаблон.
    tree = context.space_data.edit_tree #Для проверки на существование, чтобы наверняка.
    if (tree)and(tree.bl_idname=='NodeTreeUndefined'): #Если дерево нодов от к.-н. аддона исчезло, то остатки имеют NodeUndefined и NodeSocketUndefined.
        StopEdpePanBug()
        return {'CANCELLED'} #Через api линки на SocketUndefined всё равно не создаются, да и делать в этом дереве особо нечего, поэтому выходим.
    StopEdpePanBug()
    return False

def StencilBeginToolInvoke(self, context, event):
    #Одинаковая для всех инструментов обработка пропуска выделения
    tree = context.space_data.edit_tree
    if (self.isPassThrough)and(tree)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): #Проверка на дерево вторым, для эстетической оптимизации.
        #Если хоткей вызова инструмента совпадает со снятием выделения, то выделенный строчкой выше нод будет де-выделен обратно после передачи эстафеты (но останется активным).
        #Поэтому для таких ситуаций нужно снимать выделение, чтобы снова произошло переключение обратно на выделенный.
        tree.nodes.active.select = False #Но без условий, для всех подряд. Ибо ^иначе будет всегда выделение без переключения; и у меня нет идей, как бы я парился с распознаванием таких ситуаций.
        return {'PASS_THROUGH'}
    self.kmi = GetOpKmi(self, event)
    self.prefs = Prefs() #А ларчик просто открывался.
    self.uiScale = UiScale()
    ForseSetSelfNonePropToDefault(self.kmi, self) #Имеет смысл как можно раньше. Актуально для VQMT и VEST (и из-за них это переехало сюда).
    return {}

def StencilToolWorkPrepare(self, prefs, context, Func, *naArgs):
    #Здесь были self.kmi, ForseSetSelfNonePropToDefault() и self.uiScale, переехали в StencilBeginToolInvoke.
    self.whereActivated = context.space_data #CallBack'и рисуются во всех редакторах. Но в тех, у кого нет целевого сокета -- выдаёт ошибку и тем самым ничего не рисуется.
    self.fontId = blf.load(prefs.dsFontFile) #Постоянная установка шрифта нужна чтобы шрифт не исчезал при смене темы оформления.
    context.area.tag_redraw() #Не нужно в основном, но тогда в кастомных деревьях с нодами без сокетов точка при активации (VMT) не появляется сразу.
    #Финальная подготовка к работе:
    tree = context.space_data.edit_tree
    if tree:
        SaveCollapsedNodes(tree.nodes)
    Func = Func if tree else CallbackDrawEditTreeIsNone
    self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(Func, (self,context), 'WINDOW', 'POST_PIXEL')
    try:
        self.NextAssignment(context, *naArgs) #А всего-то нужно было перенести перед modal_handler_add(). #projects.blender.org/blender/blender/issues/113479
    except Exception as ex:
        DisplayMessage(voronoiAddonName+" StencilToolWorkPrepare()", str(ex), icon='ERROR')
        edgePanData.isWorking = False
        bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
    context.window_manager.modal_handler_add(self)

skf4sucess = -1

#P.s. не знаю, что значит "ViaVer", просто прикольный набор букф.

def ViaVerNewSkf(tree, side, skType, name):
    isSk = type(skType)!=str
    if isBlender4:
        global skf4sucess
        if skf4sucess==-1:
            skf4sucess = 1+hasattr(tree.interface,'items_tree')
        match skf4sucess:
            case 1: skf = tree.interface.new_socket(name, in_out={'OUTPUT' if side else 'INPUT'}, socket_type=CollapseSkTypeToBlid(skType) if isSk else skType)
            case 2: skf = tree.interface.new_socket(name, in_out='OUTPUT' if side else 'INPUT', socket_type=CollapseSkTypeToBlid(skType) if isSk else skType)
    else:
        skf = (tree.outputs if side else tree.inputs).new(skType.bl_idname if isSk else skType, name)
    return skf
def ViaVerGetSkfi(tree, side):
    if isBlender4:
        global skf4sucess
        if skf4sucess==-1:
            skf4sucess = 1+hasattr(tree.interface,'items_tree')
        match skf4sucess:
            case 1: return tree.interface.ui_items
            case 2: return tree.interface.items_tree
    else:
        return (tree.outputs if side else tree.inputs)
def ViaVerGetSkf(tree, side, name):
    return ViaVerGetSkfi(tree, side).get(name)
def NewSkfFromSk(tree, side, sk):
    def FixDefaultSkf(tree, idf, val):
        def FixTree(tr):
            for nd in tr.nodes:
                if (nd.type=='GROUP')and(nd.node_tree==tree):
                    for sk in nd.inputs:
                        if sk.identifier==idf:
                            sk.default_value = val
        for ng in bpy.data.node_groups:
            FixTree(ng)
        for mt in bpy.data.materials:
            if mt.node_tree: #На основе багрепорта; я так и не понял, каким образом оно может быть None.
                FixTree(mt.node_tree)
        #Остальные (например свет или композитинг) обделены. Ибо костыль.
    skf = ViaVerNewSkf(tree, side, sk, GetSkLabelName(sk))
    skf.hide_value = sk.hide_value
    if hasattr(skf,'default_value'):
        skf.default_value = sk.default_value
        #todo1 нужно придумать как внедриться до создания, чтобы у всех групп появился сокет со значением сразу же от sfk default.
        FixDefaultSkf(tree, skf.identifier, sk.default_value)
        if hasattr(skf,'min_value'):
            nd = sk.node
            if (nd.type=='GROUP')and(nd.node_tree): #Если сокет от другой группы нодов, то полная копия.
                ng = nd.node_tree
                skfiNg = ViaVerGetSkfi(ng, sk.is_output)
                for skfNg in skfiNg:
                    if skfNg.identifier==sk.identifier:
                        #skf.min_value = skfNg.min_value
                        #skf.max_value = skfNg.max_value
                        for pr in skf.rna_type.properties:
                            if not(pr.is_readonly or pr.is_registered):
                                setattr(skf, pr.identifier, getattr(skfNg, pr.identifier))
                        break
    return skf
def ViaVerSkfRemove(tree, side, name):
    if isBlender4:
        tree.interface.remove(name)
    else:
        (tree.outputs if side else tree.inputs).remove(name)

import ctypes

#Аааа, я просто сделалъ на досуге VLT на 157 строчки; чёрт возьми, что тут происходит??

class StructBase(ctypes.Structure):
    _subclasses = []
    __annotations__ = {}
    def __init_subclass__(cls):
        cls._subclasses.append(cls)
    @staticmethod
    def _init_structs():
        """Initialize subclasses, converting annotations to fields."""
        functype = type(lambda:None)
        for cls in StructBase._subclasses:
            fields = []
            for field, value in cls.__annotations__.items():
                if isinstance(value, functype):
                    value = value()
                fields.append((field, value))
            if fields:
                cls._fields_ = fields
            cls.__annotations__.clear()
        StructBase._subclasses.clear()
class ListBase(ctypes.Structure):
    _fields_ = (("first", ctypes.c_void_p), ("last",  ctypes.c_void_p))
    _cache = {}
    def __new__(cls, c_type=None):
        if c_type in cls._cache:
            return cls._cache[c_type]
        elif c_type is None:
            ListBase = cls
        else:
            class ListBase(ctypes.Structure):
                __name__ = __qualname__ = f"ListBase{cls.__qualname__}"
                _fields_ = (("first", ctypes.POINTER(c_type)), ("last",  ctypes.POINTER(c_type)))
                __iter__    = cls.__iter__
                __bool__    = cls.__bool__
                __getitem__ = cls.__getitem__
        return cls._cache.setdefault(c_type, ListBase)
    def __iter__(self):
        links_p = []
        elem_n = self.first or self.last
        elem_p = elem_n and elem_n.contents.prev
        if elem_p:
            while elem_p:
                links_p.append(elem_p.contents)
                elem_p = elem_p.contents.prev
            yield from reversed(links_p)
        while elem_n:
            yield elem_n.contents
            elem_n = elem_n.contents.next
    def __getitem__(self, i):
        return list(self)[i]
    def __bool__(self):
        return bool(self.first or self.last)

class BVector(StructBase):
    begin:        ctypes.c_void_p
    end:          ctypes.c_void_p
    capacity_end: ctypes.c_void_p
    _pad:         ctypes.c_char*32
#../source/blender/makesdna/DNA_node_types.h
class BNodeSocketRuntimeHandle(StructBase):
    if isWin:
        _pad0:                            ctypes.c_char*8
    declaration:                      ctypes.c_void_p
    changed_flag:                     ctypes.c_uint32
    total_inputs:                     ctypes.c_short
    _pad1:                            ctypes.c_char*2
    location:                         ctypes.c_float*2
    directly_linked_links:            BVector
    directly_linked_sockets:          BVector
    logically_linked_sockets:         BVector
    logically_linked_skipped_sockets: BVector
    owner_node:                       ctypes.c_void_p
    internal_link_input:              ctypes.c_void_p
    index_in_node:                    ctypes.c_int
    index_in_all_sockets:             ctypes.c_int
    index_in_inout_sockets:           ctypes.c_int
class BNodeStack(StructBase):
    vec:        ctypes.c_float*4
    min:        ctypes.c_float
    max:        ctypes.c_float
    data:       ctypes.c_void_p
    hasinput:   ctypes.c_short
    hasoutput:  ctypes.c_short
    datatype:   ctypes.c_short
    sockettype: ctypes.c_short
    is_copy:    ctypes.c_short
    external:   ctypes.c_short
    _pad:       ctypes.c_char*4
class BNodeSocket(StructBase):
    next:           lambda: ctypes.POINTER(BNodeSocket)
    prev:           lambda: ctypes.POINTER(BNodeSocket)
    prop:                   ctypes.c_void_p
    identifier:             ctypes.c_char*64
    name:                   ctypes.c_char*64
    storage:                ctypes.c_void_p
    in_out:                 ctypes.c_short
    typeinfo:               ctypes.c_void_p
    idname:                 ctypes.c_char*64
    default_value:          ctypes.c_void_p
    _pad:                   ctypes.c_char*4
    label:                  ctypes.c_char*64
    description:            ctypes.c_char*64
    if (isBlender4)and(bpy.app.version_string!='4.0.0 Alpha'):
        short_label:            ctypes.c_char*64
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    to_index:               ctypes.c_int
    link:                   ctypes.c_void_p
    ns:                     BNodeStack
    runtime:                ctypes.POINTER(BNodeSocketRuntimeHandle)
    @classmethod
    def GetLocation(cls, so):
        return cls.from_address(so.as_pointer()).runtime.contents.location[:]
class BNode(StructBase): #Для VRT.
    next:    lambda: ctypes.POINTER(BNode)
    prev:    lambda: ctypes.POINTER(BNode)
    inputs:  lambda: ListBase(BNodeSocket)
    outputs: lambda: ListBase(BNodeSocket)
    name:       ctypes.c_char*64
    identifier: ctypes.c_int
    flag:       ctypes.c_int
    idname:     ctypes.c_char*64
    typeinfo:   ctypes.c_void_p
    type:       ctypes.c_int16
    ui_order:   ctypes.c_int16
    custom1:    ctypes.c_int16
    custom2:    ctypes.c_int16
    custom3:    ctypes.c_float
    custom4:    ctypes.c_float
    id:         ctypes.c_void_p
    storage:    ctypes.c_void_p
    prop:       ctypes.c_void_p
    parent:     ctypes.c_void_p
    locx:       ctypes.c_float
    locy:       ctypes.c_float
    width:      ctypes.c_float
    height:     ctypes.c_float
    offsetx:    ctypes.c_float
    offsety:    ctypes.c_float
    label:      ctypes.c_char*64
    color:      ctypes.c_float*3
    @classmethod
    def get_fields(cls, so):
        return cls.from_address(so.as_pointer())
#Спасибо пользователю с ником "Oxicid", за этот кусок кода по части ctypes. "А что, так можно было?".
#Ох уж эти разрабы; пришлось самому добавлять возможность получать позиции сокетов. Месево от Blender 4.0 прижало к стенке и вынудило.
#Это получилось сделать аш на питоне, неужели так сложно было пронести api?

def GetSkLocVec(sk):
    if (sk.enabled)and(not sk.hide):
        return mathutils.Vector(BNodeSocket.GetLocation(sk))
    else:
        return Vector(0, 0)
#Что ж, самое сложное пройдено. До технической возможности поддерживать свёрнутые ноды осталось всего ничего.
#Жаждущие это припрутся сюда по-быстрому на покерфейсе, возьмут что нужно, и модифицируют себе.
#Тот первый, кто это сделает, моё тебе послание: "Что ж, молодец. Теперь ты можешь цепляться к сокетам свёрнутого нода. Надеюсь у тебя счастья полные штаны".

import typing

class rectBase(StructBase):
    def GetRaw(self):
        return self.xmin, self.ymin, self.xmax, self.ymax
    def Translate(self, xy: typing.Sequence[float]):
        self.xmin += xy[0]
        self.ymin += xy[1]
        self.xmax += xy[0]
        self.ymax += xy[1]
    def TranslateScaleFac(self, xy: typing.Sequence[float], fac=0.5):
        if xy[0]>0:
            self.xmax += xy[0]
            self.xmin += xy[0]*fac
        elif xy[0]<0:
            self.xmin += xy[0]
            self.xmax += xy[0]*fac
        if xy[1]>0:
            self.ymax += xy[1]
            self.ymin += xy[1]*fac
        elif xy[1]<0:
            self.ymin += xy[1]
            self.ymax += xy[1]*fac
class rctf(rectBase):
    xmin:   ctypes.c_float
    xmax:   ctypes.c_float
    ymin:   ctypes.c_float
    ymax:   ctypes.c_float
class rcti(rectBase):
    xmin:   ctypes.c_int
    xmax:   ctypes.c_int
    ymin:   ctypes.c_int
    ymax:   ctypes.c_int
class View2D(StructBase):
    tot:            rctf
    cur:            rctf
    vert:           rcti
    hor:            rcti
    mask:           rcti
    min:            ctypes.c_float*2
    max:            ctypes.c_float*2
    minzoom:        ctypes.c_float
    maxzoom:        ctypes.c_float
    scroll:         ctypes.c_short
    scroll_ui:      ctypes.c_short
    keeptot:        ctypes.c_short
    keepzoom:       ctypes.c_short
    keepofs:        ctypes.c_short
    flag:           ctypes.c_short
    align:          ctypes.c_short
    winx:           ctypes.c_short
    winy:           ctypes.c_short
    oldwinx:        ctypes.c_short
    oldwiny:        ctypes.c_short
    around:         ctypes.c_short
    if bpy.app.version<(2, 91):
        tab_offset:     ctypes.POINTER(c_float)
        tab_num:        ctypes.c_int
        tab_cur:        ctypes.c_int
    alpha_vert:     ctypes.c_char
    alpha_hor:      ctypes.c_char
    if bpy.app.version>(2, 92):
        _pad6:          ctypes.c_char*6
    sms:            ctypes.c_void_p #SmoothView2DStore
    smooth_timer:   ctypes.c_void_p #wmTimer
    @classmethod
    def get_rect(cls, view):
        return cls.from_address(view.as_pointer()).cur

StructBase._init_structs()

#Обеспечивает поддержку свёрнутых нодов:
#Дождались таки. Конечно же не "честную поддержку". Я презираю свёрнутые ноды, и у меня нет желания шататься с округлостью, и соответствующе изменённым рисованием.
#Так что до введения api на позицию сокета, это лучшее что есть. Ждём и надеемся.
dict_collapsedNodes = {}
def SaveCollapsedNodes(nodes):
    dict_collapsedNodes.clear()
    for nd in nodes:
        dict_collapsedNodes[nd] = nd.hide
#Я не стал показывать развёрнутым только ближайший нод, а сделал этакий "след".
#Чтобы всё это не превращалось в хаос с постоянным "дёрганьем", и чтобы можно было провести, раскрыть, успокоиться, увидеть "местную картину", и спокойно соединить что нужно.
def RestoreCollapsedNodes(nodes):
    for nd in nodes:
        if dict_collapsedNodes.get(nd, False): #Инструменты могут создавать ноды в процессе; например, сохранение результата в Preview'е.
            nd.hide = dict_collapsedNodes[nd]

class FoundTarget:
    def __init__(self, tg=None, dist=0.0, pos=Vector(0.0, 0.0), boxHeiBound=(0.0, 0.0), txt=''):
        self.tg = tg
        self.dist = dist
        self.pos = pos
        #Далее нужно только для сокетов.
        self.boxHeiBound = boxHeiBound
        self.name = txt #Нужен для поддержки перевода на другие языки. Получать перевод каждый раз при рисовании слишком не комильфо, поэтому вычисляется в заранее.

def DistanceField(field0, boxbou): #Спасибо RayMarching'у, без него я бы до такого не допёр.
    #Все vec2:
    field1 = Vector((field0.x>0)*2-1, (field0.y>0)*2-1)
    field0 = Vector(abs(field0.x), abs(field0.y))-boxbou/2
    field2 = Vector(max(field0.x, 0), max(field0.y, 0))
    field3 = Vector(abs(field0.x), abs(field0.y))
    field3 = field3*Vector(field3.x<=field3.y, field3.x>field3.y)
    field3 = field3*-( (field2.x+field2.y)==0 )
    return (field2+field3)*field1
def GetNearestNode(nd, pos, uiScale): #Вычленено из GetNearestNodes(), без нужды, но VLTT вынудил.
    ndLoс = RecrGetNodeFinalLoc(nd) #Расчехлить иерархию родителей и получить итоговую позицию нода. Проклятые рамки, чтоб их.
    isReroute = nd.bl_idname=='NodeReroute'
    #Технический размер рероута явно перезаписан в 4 раза меньше, чем он есть.
    #Насколько я смог выяснить, рероут в отличие от остальных нодов свои размеры при изменении uiScale не меняет. Так что ему не нужно делиться на 'uiScale'.
    ndSize = Vector(4,4) if isReroute else nd.dimensions/uiScale
    #Для нода позицию в центр нода. Для рероута позиция уже в его визуальном центре
    ndCenter = ndLoс.copy() if isReroute else ndLoс+ndSize/2*Vector(1,-1)
    if nd.hide: #Для VHT, "шустрый костыль" из имеющихся возможностей.
        ndCenter.y += ndSize.y/2-10 #Нужно быть аккуратнее с этой записью(write), ибо оно может оказаться указателем напрямую, если выше нодом является рероут.
    #Сконструировать поле расстояний
    vec = DistanceField(pos-ndCenter, ndSize)
    #Добавить в список отработанный нод
    return FoundTarget(nd, vec.length, pos-vec)
def GetNearestNodes(nodes, callPos, uiScale, skipPoorNodes=True): #Выдаёт список ближайших нод. Честное поле расстояний.
    #Почти честное. Скруглённые уголки не высчитываются. Их отсутствие не мешает, а вычисление требует больше телодвижений. Поэтому выпендриваться нет нужды.
    #С другой стороны скруглённость актуальна для свёрнутых нод, но я их презираю, так что...
    list_foundNodes = [] #todo0 париться с питоновскими и вообще ускорениями буду ещё не скоро.
    for nd in nodes:
        if nd.type=='FRAME': #Рамки пропускаются, ибо ни одному инструменту они не нужны.
            continue
        if (skipPoorNodes)and(not nd.inputs)and(not nd.outputs): #Ноды вообще без ничего -- как рамки. Почему бы их тоже не игнорировать ещё на этапе поиска?
            continue
        list_foundNodes.append( GetNearestNode(nd, callPos, uiScale) )
    list_foundNodes.sort(key=lambda a:a.dist)
    return list_foundNodes

#Уж было я хотел добавить велосипедную структуру ускорения, но потом внезапно осознал, что ещё нужна информация об "вторых ближайших". Так что кажись без полной обработки никуда.
#Если вы знаете, как можно это ускорить с сохранением информации, поделитесь со мной.
#С другой стороны, за всё время существования аддона не было ни одной стычки с производительностью, так что... только ради эстетики.
#А ещё нужно учитывать свёрнутые ноды, пропади они пропадом, которые могут раскрыться в процессе, наворачивая всю прелесть кеширования.

def GetFromIoPuts(nd, side, callPos, uiScale): #Вынесено для Preview Tool для 'vpRvEeSksHighlighting'.
    def SkIsLinkedVisible(sk):
        if not sk.is_linked:
            return True
        return (sk.links)and(sk.links[0].is_muted)
    list_result = []
    ndLoc = RecrGetNodeFinalLoc(nd)
    ndDim = mathutils.Vector(nd.dimensions/uiScale) #"nd.dimensions" уже содержат в себе корректировку на масштаб интерфейса, поэтому вернуть их обратно в мир.
    for sk in nd.outputs if side else reversed(nd.inputs):
        #Игнорировать выключенные и спрятанные
        if (sk.enabled)and(not sk.hide):
            posSk = GetSkLocVec(sk)/uiScale #Чорт возьми, это офигенно. Долой велосипедный кринж прошлых версий.
            #Api на высоту макета у сокета тем более нет, остаётся точечно-костылить; пока не придумается что-то ещё.
            muv = 0
            if (not side)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                if str(sk.rna_type).find("VectorDirection")!=-1:
                    muv = 2
                elif ( not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not isBlender4) ) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    muv = 3
            list_result.append(FoundTarget( sk,
                                            (callPos-posSk).length,
                                            posSk,
                                            (posSk.y-11-muv*20, posSk.y+11+max(length(sk.links)-2,0)*5*(not side)),
                                            TranslateIface(GetSkLabelName(sk)) ))
    return list_result
def GetNearestSockets(nd, callPos, uiScale): #Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного. Всё верно, аддон назван именно из-за этого.
    list_fgSksIn = []
    list_fgSksOut = []
    if not nd: #Если искать не у кого
        return list_fgSksIn, list_fgSksOut
    #Если рероут, то имеем тривиальный вариант, не требующий вычисления; вход и выход всего одни, позиции сокетов -- он сам
    if nd.bl_idname=='NodeReroute':
        ndLoc = RecrGetNodeFinalLoc(nd)
        len = (callPos-ndLoc).length
        L = lambda a: FoundTarget(a[0], len, ndLoc, (-1,-1), TranslateIface(a[0].name))
        return [L(nd.inputs)], [L(nd.outputs)]
    list_fgSksIn = GetFromIoPuts(nd, False, callPos, uiScale)
    list_fgSksOut = GetFromIoPuts(nd, True, callPos, uiScale)
    list_fgSksIn.sort(key=lambda a:a.dist)
    list_fgSksOut.sort(key=lambda a:a.dist)
    return list_fgSksIn, list_fgSksOut

#Возможно когда-нибудь придётся добавить "область активации", возвращение курсора в которую намеренно делает результат работы инструмента никаким. Актуально для VST с 'isIgnoreLinked'.

#На самых истоках весь аддон создавался только ради этого инструмента. А то-то вы думаете названия одинаковые.
#Но потом я подахренел от обузданных возможностей, и меня понесло... понесло на создание мейнстримной тройицы. Но этого оказалось мало, и теперь инструментов больше чем 7. Чума!
#Дублирующие комментарии есть только здесь (и в целом по убыванию). При спорных ситуациях обращаться к VLT для подражания, как к истине в последней инстанции.
def CallbackDrawVoronoiLinker(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if not self.foundGoalSkOut:
        DrawDoubleNone(self, prefs, context)
    elif (self.foundGoalSkOut)and(not self.foundGoalSkIn):
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut], isLineToCursor=prefs.dsIsAlwaysLine)
        if prefs.dsIsDrawPoint: #Точка под курсором шаблоном не обрабатывается, поэтому вручную.
            DrawWidePoint(self, prefs, cusorPos)
    else:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut, self.foundGoalSkIn])
class VoronoiLinkerTool(VoronoiToolDblSk): #Святая святых. То ради чего. Самый первый. Босс всех инструментов. Во славу великому полю расстояния!
    bl_idname = 'node.voronoi_linker'
    bl_label = "Voronoi Linker"
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vlBoxDiscl', self):
            AddStencilKeyProp(colTool, prefs,'vlRepickKey')
            LeftProp(colTool, prefs,'vlReroutesCanInAnyType')
            LeftProp(colTool, prefs,'vlDeselectAllNodes')
            LeftProp(colTool, prefs,'vlAnnoyingIgnoring')
            LeftProp(colTool, prefs,'vlSelectingInvolved')
    def NextAssignment(self, context, isBoth):
        prefs = self.prefs
        tree = context.space_data.edit_tree
        if not tree: #Из modal() переехало сюда.
            return
        #В случае не найденного подходящего предыдущий выбор остаётся, отчего не получится вернуть курсор обратно и "отменить" выбор, что очень неудобно.
        self.foundGoalSkIn = None #Поэтому обнуляется каждый раз перед поиском.
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(tree.nodes, callPos, self.uiScale):
            nd = li.tg
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            #Этот инструмент триггерится на любой выход
            if isBoth:
                if not prefs.vlAnnoyingIgnoring:
                    self.foundGoalSkOut = list_fgSksOut[0] if list_fgSksOut else []
                else:
                    for li in list_fgSksOut:
                        if (not self.isFirstCling)or(VltCheckAnnoyingIgnore(li.tg)):
                            self.foundGoalSkOut = li
                            break
            self.isFirstCling = False
            #Получить вход по условиям:
            skOut = self.foundGoalSkOut.tg if self.foundGoalSkOut else None
            if skOut: #Первый заход всегда isBoth=True, однако нод может не иметь выходов.
                #Заметка: нод сокета активации инструмента (isBoth) в любом случае нужно разворачивать.
                #Свёрнутость для рероутов работает, хоть и не отображается визуально; но теперь нет нужды обрабатывать, ибо поддержка свёрнутости введена.
                #Шаблон находится здесь, чтобы нод без выходов не разворачивался.
                if StencilUnCollapseNode(nd, isBoth): #Заметка: isBoth нужен, чтобы нод для SkIn не развернулся раньше, чем задумывалось.
                    #Нужно перерисовывать, если соединилось во вход свёрнутого нода.
                    StencilReNext(self, context, True)
                isClassicTree = tree.bl_idname in set_quartetClassicTreeBlids
                #На этом этапе условия для отрицания просто найдут другой результат. "Присосётся не к этому, так к другому".
                for li in list_fgSksIn:
                    #Заметка: оператор |= всё равно заставляет вычисляться правый операнд.
                    skIn = li.tg
                    #Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет с обеих сторон, минуя различные типы
                    tgl = SkBetweenFieldsCheck(self, skIn, skOut)or( (skOut.node.type=='REROUTE')or(skIn.node.type=='REROUTE') )and(prefs.vlReroutesCanInAnyType)
                    #Любой сокет для виртуального выхода; разрешить в виртуальный для любого сокета; обоим в себя запретить
                    tgl = (tgl)or( (skIn.bl_idname=='NodeSocketVirtual')^(skOut.bl_idname=='NodeSocketVirtual') )#or(skIn.bl_idname=='NodeSocketVirtual')or(skOut.bl_idname=='NodeSocketVirtual')
                    #С версии 3.5 новый сокет автоматически не создаётся. Поэтому добавляются новые возможности по соединению
                    tgl = (tgl)or(skIn.node.type=='REROUTE')and(skIn.bl_idname=='NodeSocketVirtual')
                    #Если имена типов одинаковые, но не виртуальные
                    tgl = (tgl)or(skIn.bl_idname==skOut.bl_idname)and( not( (skIn.bl_idname=='NodeSocketVirtual')and(skOut.bl_idname=='NodeSocketVirtual') ) )
                    #Если аддонские сокеты в классических деревьях -- можно к своему(см. выше) и ко всем классическим, классическим можно ко всем аддонским
                    tgl = (tgl)or(isClassicTree)and(IsClassicSk(skOut)^IsClassicSk(skIn))
                    #Заметка: SkBetweenFieldsCheck() проверяет только меж полями, поэтому явная проверка одинаковости `bl_idname`.
                    if tgl:
                        self.foundGoalSkIn = li
                        break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
                #На этом этапе условия для отрицания сделают результат никаким. Типа "Ничего не нашлось"; и будет обрабатываться соответствующим рисованием.
                if self.foundGoalSkIn:
                    if self.foundGoalSkOut.tg.node==self.foundGoalSkIn.tg.node: #Если для выхода ближайший вход -- его же нод
                        self.foundGoalSkIn = None
                    elif self.foundGoalSkOut.tg.links: #Если выход уже куда-то подсоединён, даже если это выключенные линки.
                        for lk in self.foundGoalSkOut.tg.links:
                            if lk.to_socket==self.foundGoalSkIn.tg: #Если ближайший вход -- один из подсоединений выхода, то обнулить => "желаемое" соединение уже имеется.
                                self.foundGoalSkIn = None
                                #Используемый в проверке выше "self.foundGoalSkIn" обнуляется, поэтому нужно выходить, иначе будет попытка чтения из несуществующего элемента следующей итерацией.
                                break
                    if StencilUnCollapseNode(nd): #"Мейнстримная" обработка свёрнутости.
                        StencilReNext(self, context, False)
                #К тусовке обработки свёрнутости добавляется моя личная хотелка; ибо виртуальные сокеты я всегда держу скрытыми:
                    skIn = self.foundGoalSkIn.tg if self.foundGoalSkIn else None
                    if (skIn)and(skIn.node.type=='GROUP_OUTPUT')and(skIn.node not in self.dict_hideVirtualGpOutNodes):
                        self.dict_hideVirtualGpOutNodes[skIn.node] = skIn.node.inputs[-1].hide
                        skIn.node.inputs[-1].hide = False
                if (skOut.node.type=='GROUP_INPUT')and(skOut.node not in self.dict_hideVirtualGpInNodes):
                    self.dict_hideVirtualGpInNodes[skOut.node] = skOut.node.outputs[-1].hide
                    skOut.node.outputs[-1].hide = False
            break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
    def modal(self, context, event):
        #Заметка: foundGoalSkIn и foundGoalSkOut как минимум гарантированно обнуляются в шаблоне с isBoth=True
        prefs = self.prefs
        if StencilMouseNextAndRepick(self, context, event, prefs.vlRepickKey, False, True): #Здесь упакован `match event.type:`. Возвращает true, если завершение инструмента.
            if result:=StencilModalEsc(self, context, event):
                return result
            tree = context.space_data.edit_tree
            dict_hideVirtualGpInNodes = self.dict_hideVirtualGpInNodes
            for di in dict_hideVirtualGpInNodes:
                di.outputs[-1].hide = dict_hideVirtualGpInNodes[di]
            dict_hideVirtualGpOutNodes = self.dict_hideVirtualGpOutNodes
            for di in dict_hideVirtualGpOutNodes:
                di.inputs[-1].hide = dict_hideVirtualGpOutNodes[di]
            if not( (self.foundGoalSkOut)and(self.foundGoalSkIn) ):
                return {'CANCELLED'}
            sko = self.foundGoalSkOut.tg
            ski = self.foundGoalSkIn.tg
            DoLinkHH(sko, ski) #Самая важная строчка теперь стала высокоуровневой.
            if ski.is_multi_input: #Если мультиинпут, то реализовать адекватный порядок подключения.
                #Моя личная хотелка, которая чинит странное поведение, и делает его логически-корректно-ожидаемым. Накой смысол последние соединённые через api лепятся в начало?
                list_skLinks = []
                for lk in ski.links: #Запомнить все имеющиеся линки по сокетам, и удалить их.
                    list_skLinks.append((lk.from_socket, lk.to_socket, lk.is_muted))
                    tree.links.remove(lk)
                #До версии 3.5 обработка ниже нужна была, чтобы новый io группы дважды не создавался.
                #Теперь без этой обработки Блендер или крашнется, или линк из виртуального в мультиинпут будет подсвечен красным как "некорректный"
                if sko.bl_idname=='NodeSocketVirtual':
                    sko = sko.node.outputs[-2]
                tree.links.new(sko, ski) #Соединить очередной первым.
                for cyc in range(length(list_skLinks)-1): #Восстановить запомненные. "-1", потому что последний в списке уже является желанным, что соединён строчкой выше.
                    tree.links.new(list_skLinks[cyc][0], list_skLinks[cyc][1]).is_muted = list_skLinks[cyc][2]
            VlrtRememberLastSockets(sko, ski) #Запомнить сокеты для VRT, которые теперь являются "последними использованными".
            if prefs.vlSelectingInvolved:
                for nd in tree.nodes:
                    nd.select = False
                sko.node.select = True
                ski.node.select = True
                tree.nodes.active = ski.node #P.s. не знаю, почему именно он; можно было и от sko. А делать из этого опция как-то не очень.
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        StencilInitEdgePan(context, prefs, self.uiScale)
        if prefs.vlDeselectAllNodes:
            bpy.ops.node.select_all(action='DESELECT') #Возможно так же стоит делать активный нод никаким.
        self.foundGoalSkOut = None
        self.foundGoalSkIn = None
        self.isDrawDoubleNone = True #Метка для CallbackDrawEditTreeIsNone().
        self.dict_hideVirtualGpInNodes = {}
        self.dict_hideVirtualGpOutNodes = {}
        ##
        self.isFirstCling = True #Для VltCheckAnnoyingIgnore().
        self.repickState = False
        StencilToolWorkPrepare(self, prefs, context, CallbackDrawVoronoiLinker, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiLinkerTool, "##A_RIGHTMOUSE")
dict_setKmiCats['grt'].add(VoronoiLinkerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vlRepickKey: bpy.props.StringProperty(name="Repick Key", default='LEFT_ALT')
    vlReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be connected to any type", default=True)
    vlDeselectAllNodes:     bpy.props.BoolProperty(name="Deselect all nodes on activate",        default=False)
    vlAnnoyingIgnoring:     bpy.props.BoolProperty(name="Annoying ignoring",                     default=False) #Скорее всего придётся переименовать в что-то типа "приоритетное игнорирование".
    vlSelectingInvolved:    bpy.props.BoolProperty(name="Selecting nodes involved",              default=False)
list_clsToAddon.append(VoronoiLinkerTool)

set_vltNdBlidsWithAlphaSk = {'ShaderNodeTexImage', 'GeometryNodeImageTexture', 'CompositorNodeImage', 'ShaderNodeValToRGB', 'CompositorNodeValToRGB'}
def VltCheckAnnoyingIgnore(sk): #False = игнорировать.
    if sk.node.bl_idname in set_vltNdBlidsWithAlphaSk:
        return sk.name!="Alpha"# sk!=sk.node.outputs[1]
    return True

set_vltSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}

#Blid'ы всадников. Так же использует VEST.
set_vltEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput', 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}

#"HH" типа значит "High Level", но я с буквой промахнулся D:
def DoLinkHH(sko, ski, isReroutesToAnyType=True, isCanBetweenField=True, isCanFieldToShader=True): #Какое неожиданное визуальное совпадение с порядковым номером "sk0" "sk1".
    #Коль мы теперь высокоуровневые, можем использоваться независимо, придётся суетиться с особыми случаями:
    if not(sko and ski): #Они должны быть.
        return
    if sko.id_data!=ski.id_data: #Они должны быть в одном мире.
        return
    if not(sko.is_output^ski.is_output): #Они должны быть разного гендера.
        return
    if not sko.is_output: #Вывод должен быть первым.
        sko, ski = ski, sko
    #Заметка: "высокоуровневый", но не для глупых юзеров; соединяться между виртуальными можно, чорт побери.
    tree = sko.id_data
    if tree.bl_idname=='NodeTreeUndefined': #Дерево не должно быть потерянным.
        return #В потерянном дереве сокеты вручную соединяются, а через api нет. Так что выходим.
    if sko.node==ski.node: #Для одного и того же нода всё очевидно бессмысленно, пусть и возможно. Более актуально для интерфейсов.
        return
    isSkoField = sko.type in set_vltSkTypeFields
    isSkoNdReroute = sko.node.type=='REROUTE'
    isSkiNdReroute = ski.node.type=='REROUTE'
    isSkoVirtual = (sko.bl_idname=='NodeSocketVirtual')and(not isSkoNdReroute) #Виртуальный актуален только для интерфейсов, нужно исключить "рероута-самозванца".
    isSkiVirtual = (ski.bl_idname=='NodeSocketVirtual')and(not isSkiNdReroute) #Заметка: virtual type и аддонские сокеты одинаковы.
    #Можно, если
    if not( (isReroutesToAnyType)and( (isSkoNdReroute)or(isSkiNdReroute) ) ): #Хотя бы один из них рероут
        if not( (sko.bl_idname==ski.bl_idname)or( (isCanBetweenField)and(isSkoField)and(ski.type in set_vltSkTypeFields) ) ): #Одинаковый по блидам или между полями
            if not( (isCanFieldToShader)and(isSkoField)and(ski.type=='SHADER') ): #Поле в шейдер
                if not(isSkoVirtual or isSkiVirtual): #Кто-то из них виртуальный (для интерфейсов).
                    if (tree.bl_idname not in set_quartetClassicTreeBlids)or( IsClassicSk(sko)==IsClassicSk(ski) ): #Если аддонский сокет в классических деревьях; см. VLT.
                        return None #Низя между текущими типами.
    #Отсеивание некорректных завершено. Теперь интерфейсы:
    ndo = sko.node
    ndi = ski.node
    procIface = True
    #Для суеты с интерфейсами требуется только один виртуальный. Если их нет, то обычное соединение.
    #Но если они оба виртуальные, читать информацию не от кого; от чего суета с интерфейсами бесполезна.
    if not(isSkoVirtual^isSkiVirtual): #Два условия упакованы в один xor.
        procIface = False
    elif ndo.type==ndi.type=='REROUTE': #Между рероутами гарантированно связь. Этакий мини-островок безопасности, затишье перед бурей.
        procIface = False
    elif not( (ndo.bl_idname in set_vltEquestrianPortalBlids)or(ndi.bl_idname in set_vltEquestrianPortalBlids) ): #Хотя бы один из нодов должен быть всадником.
        procIface = False
    if procIface: #Что ж, бурая оказалось не такой уж и бурей. Я ожидал больший спагетти-код. Как всё легко и ясно получается, если мозги-то включить.
        #Получить нод всадника виртуального сокета
        ndEq = ndo if isSkoVirtual else ndi #Исходим из того, что всадник вывода равновероятен со своим компаньоном.
        #Коллапсируем рамочных всадников сразу же
        ndEq = getattr(ndEq,'paired_output', ndEq)
        #Интересно, где-нибудь в параллельной вселенной существуют виртуальные мультиинпуты?.
        skTar = sko if isSkiVirtual else ski
        match ndEq.bl_idname:
            case 'NodeGroupOutput': typeEq = 0
            case 'NodeGroupInput':  typeEq = 1
            case 'GeometryNodeSimulationOutput': typeEq = 2
            case 'GeometryNodeRepeatOutput':     typeEq = 3
        #Неподдерживаемых всадником не обрабатывать
        can = True
        match typeEq:
            case 2: can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','GEOMETRY'}
            case 3: can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL'}
        if not can:
            return None
        #Создать интерфейс
        match typeEq:
            case 0|1:
                NewSkfFromSk(tree, not typeEq, skTar)
            case 2|3:
                (ndEq.state_items if typeEq==2 else ndEq.repeat_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), GetSkLabelName(skTar))
        #Перевыбрать для нового появившегося сокета
        if isSkiVirtual:
            ski = ski.node.inputs[-2]
        else:
            sko = sko.node.outputs[-2]
    #Путешествие успешно выполнено. Наконец-то переходим к самому главному:
    def DoLinkLL(tree, sko, ski):
        return tree.links.new(sko, ski) #hi.
    return DoLinkLL(tree, sko, ski)
    #Заметка: С версии Blender 3.5 виртуальные инпуты теперь могут принимать в себя прям как мультиинпуты.
    # Они даже могут между собой по нескольку раз соединяться, офигеть. Разрабы "отпустили", так сказать, в свободное плаванье.

set_omgApiNodesColor = {'FunctionNodeInputColor'} #projects.blender.org/blender/blender/issues/104909

def CallbackDrawVoronoiPreview(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkOut:
        if prefs.vpRvEeSksHighlighting: #Помощь в реверсинженеринге, подсвечивать места соединения, и отображать имя этих сокетов; одновременно.
            #Определить масштаб для надписей:
            pos = VecWorldToRegScale(cusorPos, self)
            loc = Vector(cusorPos.x+6*1000, cusorPos.y)
            rd = (VecWorldToRegScale(loc, self)[0]-pos[0])/1000
            #Нарисовать:
            ndTar = self.foundGoalSkOut.tg.node
            for side in [False, True]: #todo3 для входов не показывает, и вообще нужно переосмысление реализации.
                for skTar in ndTar.outputs if side else ndTar.inputs:
                    for lk in skTar.links:
                        if not lk.is_muted:
                            sk = lk.to_socket if side else lk.from_socket
                            nd = sk.node
                            nd.hide = False #Запись во время рисования. По крайней мере не так как сильно, как в MassLinker Tool.
                            if nd.type!='REROUTE': #if (not nd.hide)and(nd.type!='REROUTE'): #Отображать у тех, кто не свёрнут и не рероут.
                                list_fgSks = GetFromIoPuts(nd, 1-(side*2), cusorPos, self.uiScale)
                                for li in list_fgSks:
                                    if li.tg==sk:
                                        DrawToolOftenStencil(self, prefs, cusorPos, [li], isDrawText=False, isDrawOnlyArea=True)
                                        DrawSkText( self, prefs, li.pos, ((li.tg.is_output*2-1), -0.5), li, min(rd*4,25) )
                                        break
        #Порядок рисования важен, главное над хелпером.
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut], isLineToCursor=True, textSideFlip=True, isDrawText=True, isDrawMarkersMoreTharOne=True)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiPreviewTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_preview'
    bl_label = "Voronoi Preview"
    isSelectingPreviewedNode: bpy.props.BoolProperty(name="Select previewed node",  default=True)
    isTriggerOnlyOnLink:      bpy.props.BoolProperty(name="Trigger only on linked", default=False) #Изначально часть возможностей реверсинженеринга.
    isEqualAnchorType:        bpy.props.BoolProperty(name="Equal anchor type",      default=False)
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vpBoxDiscl', self):
            LeftProp(colTool, prefs,'vpAllowClassicCompositorViewer')
            LeftProp(colTool, prefs,'vpAllowClassicGeoViewer')
            LeftProp(colTool, prefs,'vpIsLivePreview')
            LeftProp(colTool, prefs,'vpRvEeIsColorOnionNodes')
            LeftProp(colTool, prefs,'vpRvEeIsSavePreviewResults')
            LeftProp(colTool, prefs,'vpRvEeSksHighlighting')
    def NextAssignment(self, context, *naArgs):
        prefs = self.prefs
        tree = context.space_data.edit_tree
        if not tree:
            return
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        if False:
            #Уж было я добавил возможность цепляться к полям для виевера, но потом понял, что нет api на смену его типа предпросмотра. Опять. Придётся хранить на низком старте.
            isGeoViewer = False #Для цепляния к полям для ГеоВиевеера.
            if isGeoTree:
                for nd in tree.nodes:
                    if nd.type=='VIEWER':
                        isGeoViewer = True
                        break
        self.foundGoalSkOut = None #Нет нужды, но сбрасывается для ясности картины. Было полезно для отладки.
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if prefs.vpRvEeIsSavePreviewResults:
                #Игнорировать готовый нод для переименования и тем самым сохраняя результаты предпросмотра.
                if nd.name==voronoiPreviewResultNdName:
                    continue
            #Если в геометрических нодах, то игнорировать ноды без выходов геометрии
            if (isGeoTree)and(not self.isAnyAncohorExist):
                if not [True for sk in nd.outputs if (sk.type=='GEOMETRY')and(not sk.hide)and(sk.enabled)]: #Искать сокеты геометрии, которые видимы.
                    continue
            #Пропускать ноды если визуально нет сокетов; или есть, но только виртуальные. Для рероутов всё бесполезно.
            if (not [True for sk in nd.outputs if (not sk.hide)and(sk.enabled)and(sk.bl_idname!='NodeSocketVirtual')])and(nd.type!='REROUTE'):
                continue
            #Всё выше нужно было для того, чтобы точка не висела просто так и нод не мешал для удобного использования инструмента. По ощущениям получаются как "прозрачные" ноды.
            #Игнорировать свой собственный спец-рероут-якорь (проверка на тип и имя)
            if ( (nd.type=='REROUTE')and(nd.name==voronoiAnchorClName) ):
                continue
            #В случае успеха переходить к сокетам:
            list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)[1]
            for li in list_fgSksOut:
                #Игнорировать свои сокеты мостов здесь. Нужно для нод нод-групп, у которых "торчит" сокет моста и к которому произойдёт прилипание без этой проверки; и после чего они будут удалены в VptPreviewFromSk().
                if li.tg.name==voronoiSkPreviewName:
                    continue
                #Этот инструмент триггерится на любой выход кроме виртуального. В геометрических нодах искать только выходы геометрии.
                #Якорь притягивает на себя превиев; рероут может принимать любой тип; следовательно -- при наличии якоря отключать триггер только на геосокеты
                if (li.tg.bl_idname!='NodeSocketVirtual')and( (not isGeoTree)or(li.tg.type=='GEOMETRY')or(self.isAnyAncohorExist) ):
                    can = True
                    if rrAnch:=tree.nodes.get(voronoiAnchorClName): #EqualAnchorType.
                        rrSkBlId = rrAnch.outputs[0].bl_idname
                        can = (not self.isEqualAnchorType)or(li.tg.bl_idname==rrSkBlId)or(rrSkBlId=='NodeSocketVirtual')
                    #todo1 для якорей близости тоже сделать выбор по типу.
                    can &= not li.tg.node.label==voronoiAnchorDtName #li.tg.node not in self.list_distAnchors
                    if can:
                        if (not(self.isTriggerOnlyOnLink))or(li.tg.is_linked): #Помощь в реверсинженеринге, триггериться только на существующие линки. Ускоряет процесс "считывания/понимания" дерева.
                            self.foundGoalSkOut = li
                            break
            if self.foundGoalSkOut: #Завершать в случае успеха. Иначе, например для игнорирования своих сокетов моста, если у нода только они -- остановится рядом и не найдёт других.
                break
        if self.foundGoalSkOut:
            if prefs.vpIsLivePreview:
                VptPreviewFromSk(self, prefs, context, self.foundGoalSkOut.tg)
            if prefs.vpRvEeIsColorOnionNodes: #Помощь в реверсинженеринге, вместо поиска глазами тоненьких линий, быстрое визуальное считывание связанных нод топологией.
                ndRoot = self.foundGoalSkOut.tg.node
                for nd in tree.nodes:
                    if nd.name!=voronoiPreviewResultNdName:
                        nd.use_custom_color = False #Не париться с запоминанием последних и тупо выключать у всех каждый раз. Дёшево и сердито.
                #todo3 с приходом RANTO запаять все вызовы `sk.links` и обобщить нужды наподобие RerouteWalker'a.
                dict_vptSoldSkoLinks = {}
                dict_vptSoldSkiLinks = {}
                for lk in tree.links:
                    if (lk.is_valid)and(not lk.is_hidden or lk.is_muted):
                        dict_vptSoldSkoLinks.setdefault(lk.from_socket, [])
                        dict_vptSoldSkoLinks[lk.from_socket].append(lk)
                        dict_vptSoldSkiLinks.setdefault(lk.to_socket, [])
                        dict_vptSoldSkiLinks[lk.to_socket].append(lk)
                def RecrRerouteWalker(sk, col):
                    for lk in (dict_vptSoldSkoLinks if sk.is_output else dict_vptSoldSkiLinks).get(sk, []):
                        nd = lk.to_node if sk.is_output else lk.from_node
                        if nd.type=='REROUTE':
                            RecrRerouteWalker(nd.outputs[0] if sk.is_output else nd.inputs[0], col)
                        else:
                            nd.use_custom_color = True
                            if nd.name!=voronoiPreviewResultNdName: #Нод для сохранения результата не перекрашивать
                                if nd.bl_idname in set_omgApiNodesColor:
                                    bn = BNode.get_fields(nd)
                                    bn.color[0] = col[0]
                                    bn.color[1] = col[1]
                                    bn.color[2] = col[2]
                                else:
                                    nd.color = col
                            nd.hide = False #А также раскрывать их.
                for sk in ndRoot.outputs:
                    RecrRerouteWalker(sk, (0.188, 0.188, 0.5)) #todo1 сделать из цветов опцию; лучше после того, как что-то из этого будет переосмыслено.
                for sk in ndRoot.inputs:
                    RecrRerouteWalker(sk, (0.55, 0.188, 0.188))
            StencilUnCollapseNode(self.foundGoalSkOut.tg.node)
    def modal(self, context, event):
        prefs = self.prefs
        if StencilMouseNext(self, context, event):
            if result:=StencilModalEsc(self, context, event):
                return result
            if not self.foundGoalSkOut:
                return {'CANCELLED'}
            VptPreviewFromSk(self, prefs, context, self.foundGoalSkOut.tg)
            VlrtRememberLastSockets(self.foundGoalSkOut.tg, None)
            if prefs.vpRvEeIsColorOnionNodes:
                for nd in context.space_data.edit_tree.nodes:
                    dv = self.dict_saveRestoreNodeColors.get(nd, None) #Так же, как и в восстановлении свёрнутости.
                    if dv is not None:
                        nd.use_custom_color = dv[0]
                        col = dv[1]
                        if nd.bl_idname in set_omgApiNodesColor:
                            bn = BNode.get_fields(nd)
                            bn.color[0] = col[0]
                            bn.color[1] = col[1]
                            bn.color[2] = col[2]
                        else:
                            nd.color = col
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=UselessForCustomUndefTrees(context):
            return result
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        #Если использование классического viewer'а разрешено, завершить инструмент с меткой пропуска, "передавая эстафету" оригинальному виеверу.
        match context.space_data.tree_type:
            case 'CompositorNodeTree':
                if (prefs.vpAllowClassicCompositorViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
            case 'GeometryNodeTree':
                if (prefs.vpAllowClassicGeoViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
        self.foundGoalSkOut = None
        tree = context.space_data.edit_tree
        if tree:
            if prefs.vpRvEeIsColorOnionNodes:
                #Запомнить все цвета, и обнулить их всех.
                self.dict_saveRestoreNodeColors = {}
                for nd in tree.nodes:
                    if nd.bl_idname in set_omgApiNodesColor:
                        col = BNode.get_fields(nd).color
                        col = (col[0], col[1], col[2])
                    else:
                        col = nd.color.copy()
                    self.dict_saveRestoreNodeColors[nd] = (nd.use_custom_color, col)
                    nd.use_custom_color = False
                #Заметка: ноды сохранения результата с луковичными цветами обрабатываются как есть. Дублированный нод не будет оставаться не затрагиваемым.
            #Пайка:
            list_distAnchors = []
            for nd in tree.nodes:
                if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                    list_distAnchors.append(nd)
                    nd.label = voronoiAnchorDtName #А так же используется для проверки на свои рероуты.
            self.list_distAnchors = list_distAnchors
            #Пайка:
            rrAnch = tree.nodes.get(voronoiAnchorClName)
            #Некоторые пользователи в "начале знакомства" с инструментом захотят переименовать якорь.
            #Каждый призыв якоря одинаков по заголовку, а при повторном призыве заголовок всё равно меняется обратно на стандартный.
            #После чего пользователи поймут, что переименовывать якорь бесполезно.
            if rrAnch:
                rrAnch.label = voronoiAnchorClName #Эта установка лишь ускоряет процесс осознания.
            self.isAnyAncohorExist = not not (rrAnch or list_distAnchors) #Для геонод; если в них есть якорь, то триггериться не только на геосокеты.
        StencilToolWorkPrepare(self, prefs, context, CallbackDrawVoronoiPreview)
        return {'RUNNING_MODAL'}
class VoronoiPreviewAnchorTool(VoronoiTool): #Вынесено в отдельный инструмент, потому что уж больно слишком разные.
    #Да и ныне несуществующий isPlaceAnAnchor мозолил глаза своим True-наличием и => бесполезностью всех остальных.
    #А так же задел на будущее для потенциальных мультиякорей, чтобы всё это не превращалось в спагетти-код.
    bl_idname = 'node.voronoi_preview_anchor'
    bl_label = "Voronoi Preview Anchor"
    isActiveAnchor: bpy.props.BoolProperty(name="Active anchor", default=True)
    isSelectAnchor: bpy.props.BoolProperty(name="Select anchor", default=True)
    anchorType: bpy.props.IntProperty(name="Anchor type", default=0, min=-1, max=1)
    def invoke(self, context, event):
        if result:=UselessForCustomUndefTrees(context, isForCustom=False):
            return result
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        tree = context.space_data.edit_tree
        if not tree:
            return {'CANCELLED'}
        anType = self.anchorType
        if anType==-1:
            for nd in reversed(tree.nodes):
                if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                    tree.nodes.remove(nd)
            if False: #Пока так, а потом посмотрим.
                if nd:=tree.nodes.get(voronoiAnchorClName):
                    tree.nodes.remove(nd)
            return {'FINISHED'}
        for nd in tree.nodes:
            nd.select = False
        if not anType:
            rrAnch = tree.nodes.get(voronoiAnchorClName)
            isFirstApr = not rrAnch #Метка для обработки при первом появлении.
            rrAnch = rrAnch or tree.nodes.new('NodeReroute')
            rrAnch.name = voronoiAnchorClName
            rrAnch.label = voronoiAnchorClName
        else:
            sco = 0
            tgl = True
            while tgl:
                sco += 1
                name = voronoiAnchorDtName+str(sco)
                tgl = tree.nodes.get(name, False)
            isFirstApr = True
            rrAnch = tree.nodes.new('NodeReroute')
            rrAnch.name = name
            rrAnch.label = voronoiAnchorDtName
        if self.isActiveAnchor:
            tree.nodes.active = rrAnch
        rrAnch.location = context.space_data.cursor_location
        rrAnch.select = self.isSelectAnchor
        if isFirstApr:
            #Почему бы и нет. Зато красивый.
            rrAnch.inputs[0].type = 'COLLECTION' if anType else 'MATERIAL' #Для аддонских деревьев, потому что в них "напролом" ниже не работает.
            rrAnch.outputs[0].type = rrAnch.inputs[0].type #Чтобы цвет выхода у линка был таким же.
            if not anType:
                #Выше установка напрямую 'CUSTOM' не работает, поэтому идём напролом; спасибо обновлению Blender 3.5:
                nd = tree.nodes.new('NodeGroupInput')
                tree.links.new(nd.outputs[-1], rrAnch.inputs[0])
                tree.nodes.remove(nd)
        return {'FINISHED'}

SmartAddToRegAndAddToKmiDefs(VoronoiPreviewTool,       "SC#_LEFTMOUSE")
SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_RIGHTMOUSE")
SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_2", {'anchorType':1})
SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_1", {'anchorType':-1})
dict_setKmiCats['grt'].add(VoronoiPreviewTool.bl_idname)
dict_setKmiCats['oth'].add(VoronoiPreviewAnchorTool.bl_idname) #  spc

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vpBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vpAllowClassicCompositorViewer: bpy.props.BoolProperty(name="Allow classic Compositor Viewer", default=False)
    vpAllowClassicGeoViewer:        bpy.props.BoolProperty(name="Allow classic GeoNodes Viewer",   default=True)
    vpIsLivePreview:                bpy.props.BoolProperty(name="Live preview",                    default=True)
    vpRvEeIsColorOnionNodes:        bpy.props.BoolProperty(name="Node onion colors",               default=False)
    vpRvEeSksHighlighting:          bpy.props.BoolProperty(name="Topology connected highlighting", default=False) #Ну и словечко. Три трио комбо. Выглядит как случайные удары по клавиатуре.
    vpRvEeIsSavePreviewResults:     bpy.props.BoolProperty(name="Save preview results",            default=False)
list_clsToAddon.append(VoronoiPreviewTool)

class VptWayTree:
    def __init__(self, tree=None, nd=None):
        self.tree = tree
        self.nd = nd
        self.isCorrect = None #Целевой глубине не с кем сравнивать.
        self.isUseExtAndSkPr = None #Оптимизация для чистки.
        self.prLink = None #Для более адекватной организации для RvEe.
def VptGetTreesPath(context, nd):
    list_path = [ VptWayTree(pt.node_tree, pt.node_tree.nodes.active) for pt in context.space_data.path ]
    #Как я могу судить, сама суть реализации редактора узлов не хранит >нод<, через который пользователь зашёл в группу (но это не точно).
    #Поэтому если активным оказалась не нод-группа, то заменить на первый найденный-по-группе нод (или ничего, если не найдено)
    for curWy, upWy in zip(list_path, list_path[1:]):
        if (not curWy.nd)or(curWy.nd.type!='GROUP')or(curWy.nd.node_tree!=upWy.tree): #Определить отсутствие связи между глубинами.
            curWy.nd = None #Избавиться от текущего неправильного. Уж лучше останется никакой.
            for nd in curWy.tree.nodes:
                if (nd.type=='GROUP')and(nd.node_tree==upWy.tree): #Если в текущей глубине с неправильным нодом имеется нод группы с правильной группой.
                    curWy.nd = nd
                    break #Починка этой глубины успешно завершена.
        curWy.isCorrect = curWy.nd==upWy.tree #По факту.
    return list_path

def VptGetRootNd(tree):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            for nd in tree.nodes:
                if (nd.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT_LINESTYLE','OUTPUT'})and(nd.is_active_output):
                    return nd
        case 'GeometryNodeTree':
            if False:
                #Для очередных глубин тоже актуально получать перецепление сразу в виевер, но см. |3|; текущий конвейер логически не приспособлен для этого.
                #Поэтому больше не поддерживается, ибо "решено" только на половину. Так что старый добрый якорь в помощь.
                for nd in reversed(tree.nodes): #Активный виевер будет в конце списка, так что искать с конца.
                    if nd.type=='VIEWER':
                        if [True for sk in nd.inputs[1:] if sk.links]: #Выбирать виевер только если у него есть линк для просмотра поля.
                            return nd
                        break #Обрабатывать только первый попавшийся ! виевер; он же активный. Потому что иначе будет некомфортное поведение для нескольких виеверов.
            for nd in tree.nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    for sk in nd.inputs:
                        if sk.type=='GEOMETRY':
                            return nd
        case 'CompositorNodeTree':
            for nd in tree.nodes:
                if nd.type=='VIEWER':
                    return nd
            for nd in tree.nodes:
                if nd.type=='COMPOSITE':
                    return nd
        case 'TextureNodeTree':
            for nd in tree.nodes:
                if nd.type=='OUTPUT':
                    return nd
    return None
def VptGetRootSk(tree, ndRoot, targetSk):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            return ndRoot.inputs[ (targetSk.name=="Volume")*(ndRoot.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD'}) ]
        case 'GeometryNodeTree':
            for sk in ndRoot.inputs:
                if sk.type=='GEOMETRY':
                    return sk
    return ndRoot.inputs[0] #Заметка: здесь так же окажется неудачный от GeometryNodeTree выше.

vptFeatureUsingExistingPath = True
#Заметка: интерфейсы симуляции и зоны повторения не рассматривать, их обработка потребует поиска по каждому ноду в дереве, отчего будет Big(O) алерт.
def DoPreviewCore(context, targetSk, list_distAnchors):
    def NewLostNode(txt_type, ndTar=None):
        ndNew = tree.nodes.new(txt_type)
        if ndTar:
            ndNew.location = ndTar.location
            ndNew.location.x += ndTar.width*2
        return ndNew
    def GetSkFromIdf(io, idf):
        for sk in io:
            if sk.identifier==idf:
                return sk
        return None
    list_way = VptGetTreesPath(context, targetSk.node)
    higWay = length(list_way)-1
    list_way[higWay].nd = targetSk.node #Подразумеваемым гарантией-конвейером глубин заходов целевой не обрабатывается, поэтому указывать явно. (не забыть перевести с эльфийского на русский)
    ##
    previewSkType = "RGBA" #Цвет, а не шейдер -- потому что иногда есть нужда вставить нод куда-то на пути предпросмотра.
    #Но если линки шейдерные -- готовьтесь к разочарованию. Поэтому цвет (кой и был изначально у NW).
    isGeoTree = list_way[0].tree.bl_idname=='GeometryNodeTree'
    if isGeoTree:
        previewSkType = "GEOMETRY"
    elif targetSk.type=='SHADER':
        previewSkType = "SHADER"
    idLastSkEx = '' #Для vptFeatureUsingExistingPath.
    def GetBridgeSk(puts):
        sk = puts.get(voronoiSkPreviewName)
        if (sk)and(sk.type!=previewSkType):
            ViaVerSkfRemove(tree, True, ViaVerGetSkf(tree, True, voronoiSkPreviewName))
            return None
        return sk
    def GetTypeSkfBridge():
        match previewSkType:
            case 'GEOMETRY': return "NodeSocketGeometry"
            case 'SHADER':   return "NodeSocketShader"
            case 'RGBA':     return "NodeSocketColor"
    for cyc in reversed(range(higWay+1)):
        curWay = list_way[cyc]
        tree = curWay.tree
        #Определить отправляющий нод:
        portalNdFrom = curWay.nd #targetSk.node уже включён в путь для cyc==higWay.
        isCreatedNgOut = False
        if not portalNdFrom:
            portalNdFrom = tree.nodes.new(tree.bl_idname.replace("Tree","Group"))
            portalNdFrom.node_tree = list_way[cyc+1].tree
            isCreatedNgOut = True #Чтобы установить позицию нода от принимающего нода, который сейчас неизвестен.
        #Определить принимающий нод:
        portalNdTo = None
        if not cyc: #Корень.
            portalNdTo = VptGetRootNd(tree)
            if not portalNdTo:
                #"Визуальное оповещение", что соединяться некуда. Можно было бы и вручную добавить, но лень шататься с принимающими нодами ShaderNodeTree'а.
                portalNdTo = NewLostNode('NodeReroute', portalNdFrom)
        else: #Очередная глубина.
            for nd in tree.nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    portalNdTo = nd
                    break
            if not portalNdTo:
                #Создать вывод группы самостоятельно, вместо того чтобы остановиться и не знать что делать.
                portalNdTo = NewLostNode('NodeGroupOutput', portalNdFrom)
        if isGeoTree:
            #Теперь поведение наличия виевера похоже на якорь.
            for nd in tree.nodes:
                if nd.type=='VIEWER':
                    portalNdTo = nd
                    break
        if isCreatedNgOut:
            portalNdFrom.location = portalNdTo.location-Vector(portalNdFrom.width+40, 0)
        #Определить отправляющий сокет:
        portalSkFrom = None
        if (vptFeatureUsingExistingPath)and(idLastSkEx):
            portalSkFrom = GetSkFromIdf(portalNdFrom.outputs, idLastSkEx)
            idLastSkEx = '' #Важно обнулять. Выбранный сокет может не иметь линков или связи до следующего портала, отчего на следующей глубине будут несоответствия.
        if not portalSkFrom:
            portalSkFrom = targetSk if cyc==higWay else GetBridgeSk(portalNdFrom.outputs)
        #Определить принимающий сокет:
        portalSkTo = None
        if (isGeoTree)and(portalNdTo.type=='VIEWER'):
            portalSkTo = portalNdTo.inputs[0]
        if (not portalSkTo)and(vptFeatureUsingExistingPath)and(cyc): #Имеет смысл записывать для не-корня.
            #Моё улучшающее изобретение -- если соединение уже имеется, то зачем создавать рядом такое же?.
            #Это эстетически комфортно, а также помогает очистить последствия предпросмотра не выходя из целевой глубины (добавлены условия, см. чистку).
            for lk in portalSkFrom.links:
                #Поскольку интерфейсы не удаляются, вместо мейнстрима ниже он заполучится отсюда (и результат будет таким же), поэтому вторая проверка для isUseExtAndSkPr.
                if (lk.to_node==portalNdTo)and(lk.to_socket.name!=voronoiSkPreviewName):
                    portalSkTo = lk.to_socket
                    idLastSkEx = portalSkTo.identifier #Выходы нода нод-группы и входы выхода группы совпадают. Сохранить информацию для следующей глубины продолжения.
                    curWay.isUseExtAndSkPr = GetBridgeSk(portalNdTo.inputs) #Для чистки. Если будет без линков, то удалять. При чистке они не ищутся по факту, потому что Big(O).
        if not portalSkTo: #Основной мейнстрим получения.
            portalSkTo = VptGetRootSk(tree, portalNdTo, targetSk) if not cyc else GetBridgeSk(portalNdTo.inputs) #|3|.
        if (not portalSkTo)and(cyc): #Очередные глубины -- всегда группы, для них и нужно генерировать skf. Проверка на cyc не обязательна, сокет с корнем (из-за рероута) всегда будет.
            #Если выше не смог получить сокет от входов нода нод группы, то и интерфейса-то тоже нет. Поэтому проверка `not tree.outputs.get(voronoiSkPreviewName)` без нужды.
            ViaVerNewSkf(tree, True, GetTypeSkfBridge(), voronoiSkPreviewName).hide_value = True
            portalSkTo = GetBridgeSk(portalNdTo.inputs) #Перевыбрать новосозданный.
        #Соединить:
        ndAnchor = tree.nodes.get(voronoiAnchorClName)
        if (cyc==higWay)and(not ndAnchor)and(list_distAnchors): #Ближайший ищется от курсора; где-же взять курсор для не-целевый глубин?
            curPos = context.space_data.cursor_location
            min = 32768
            for nd in list_distAnchors:
                len = (nd.location-curPos).length
                if min>len:
                    min = len
                    ndAnchor = nd
        if ndAnchor: #Якорь делает "планы изменились", и пересасывает поток на себя.
            lk = tree.links.new(portalSkFrom, ndAnchor.inputs[0])
            #tree.links.new(ndAnchor.outputs[0], portalSkTo)
            curWay.prLink = lk
            break #Завершение после напарывания повышает возможности использования якоря, делая его ещё круче. Если у вас течка от Voronoi_Anchor, то я вас понимаю. У меня тоже.
            #Завершение позволяет иметь пользовательское соединение от глубины с якорем и до корня, не разрушая их.
        elif (portalSkFrom)and(portalSkTo): #Иначе обычное соединение маршрута.
            lk = tree.links.new(portalSkFrom, portalSkTo)
            curWay.prLink = lk
    return list_way
def VptPreviewFromSk(self, prefs, context, targetSk):
    if (not targetSk)or(not targetSk.is_output):
        return
    list_way = DoPreviewCore(context, targetSk, self.list_distAnchors)
    #Гениально я придумал удалять интерфейсы после предпросмотра; стало возможным благодаря не-удалению в контекстных путях. Теперь ими можно будет пользоваться более свободно.
    tree = context.space_data.edit_tree
    if (True)or(not tree.nodes.get(voronoiAnchorClName)): #'True' -- см. ниже.
        #Если в текущем дереве есть якорь, то никаких voronoiSkPreviewName не удалять; благодаря чему становится доступным ещё одно особое использование инструмента.
        #Должно было стать логическим продолжением после "завершение после напарывания", но допёр до этого только сейчас.
        #P.s. Я забыл нахрен какое. А теперь они не удаляются от контекстных путей, так что информация уже утеряна D:
        dict_treeNExt = dict({(wy.tree, wy.isUseExtAndSkPr) for wy in list_way})
        dict_treeOrder = dict({(wy.tree, cyc) for cyc, wy in enumerate(reversed(list_way))}) #Путь имеет линки, середине не узнать о хвосте, поэтому из текущей глубины до корня, чтобы "каскадом" корректно обработалось.
        for ng in sorted(bpy.data.node_groups, key=lambda a: dict_treeOrder.get(a,-1)):
            #Удалить все свои следы предыдущего использования инструмента для всех нод-групп, чей тип текущего редактора такой же.
            if ng.bl_idname==tree.bl_idname:
                #Но не удалять мосты для деревьев контекстного пути (удалять, если их сокеты пустые).
                sk = dict_treeNExt.get(ng, None) #Для Ctrl-F: isUseExtAndSkPr используется здесь.
                if (ng not in dict_treeNExt)or((not sk.links) if sk else None)or( (ng==tree)and(sk) ):
                    sk = True
                    while sk: #Ищется по имени. Пользователь может сделать дубликат, от чего без while они будут исчезать по одному каждую активацию предпросмотра.
                        sk = ViaVerGetSkf(ng, True, voronoiSkPreviewName)
                        if sk:
                            ViaVerSkfRemove(ng, True, sk)
    if self.isSelectingPreviewedNode:
        NdSelectAndActive(targetSk.node)
    if (prefs.vpRvEeIsSavePreviewResults)and(not self.isAnyAncohorExist): #Помощь в реверсинженеринге, сохранять текущий сокет просмотра для последующего "менеджмента".
        def GetTypeOfNodeSave(sk):
            match sk.type:
                case 'GEOMETRY': return 2
                case 'SHADER': return 1
                case _: return 0
        prLink = list_way[-1].prLink
        idSkSave = GetTypeOfNodeSave(prLink.from_socket)
        vec = prLink.to_node.location
        vec = [vec[0]+prLink.to_node.width+40, vec[1]]
        ndReSave = tree.nodes.get(voronoiPreviewResultNdName)
        if ndReSave:
            if ndReSave.label!=voronoiPreviewResultNdName:
                ndReSave.name += "_"+ndReSave.label
                ndReSave = None
            elif GetTypeOfNodeSave(ndReSave.outputs[0])!=idSkSave: #Если это нод от другого типа сохранения
                vec = ndReSave.location.copy() #При смене типа сохранять позицию "активного" нода-сохранения. Заметка: не забывать про .copy(), потому что далее нод удаляется.
                tree.nodes.remove(ndReSave)
                ndReSave = None
        if not ndReSave:
            match idSkSave:
                case 0: txt = "MixRGB" #"MixRGB" потому что он есть во всех редакторах; а ещё Shift+G > Type.
                case 1: txt = "AddShader"
                case 2: txt = "SeparateGeometry"
            ndReSave = tree.nodes.new(tree.bl_idname.replace("Tree","")+txt)
            ndReSave.location = vec
        ndReSave.name = voronoiPreviewResultNdName
        ndReSave.select = False
        ndReSave.label = ndReSave.name
        ndReSave.use_custom_color = True
        def MixThCol(col1, col2, fac=0.4): #/source/blender/editors/space_node/node_draw.cc  node_draw_basis()  /* Header. */
            return col1*(1-fac)+col2*fac
            # (col2**(1/1.9))*0.5
        neTheme = bpy.context.preferences.themes[0].node_editor
        colBg = mathutils.Color(neTheme.node_backdrop[:3])
        match idSkSave: #Разукрасить нод сохранения.
            case 0:
                ndReSave.color = MixThCol(colBg, neTheme.color_node)
                ndReSave.show_options = False
                ndReSave.blend_type = 'ADD'
                ndReSave.inputs[0].default_value = 0
                ndReSave.inputs[1].default_value = PowerArr4ToVec(list(ndReSave.color)[:]+[1], 2.2)
                ndReSave.inputs[2].default_value = ndReSave.inputs[1].default_value #Немного лишнее.
                ndReSave.inputs[0].hide = True
                ndReSave.inputs[1].name = "Color"
                ndReSave.inputs[2].hide = True
                inx = 1
            case 1:
                ndReSave.color = MixThCol(colBg, neTheme.shader_node)
                ndReSave.inputs[1].hide = True
                inx = 0
            case 2:
                ndReSave.color = MixThCol(colBg, neTheme.geometry_node)
                ndReSave.show_options = False
                ndReSave.inputs[1].hide = True
                ndReSave.outputs[0].name = "Geometry"
                ndReSave.outputs[1].hide = True
                inx = 0
        tree.links.new(prLink.from_socket, ndReSave.inputs[inx])
        tree.links.new(ndReSave.outputs[0], prLink.to_socket)

class VmtMixerData(PieData):
    sk0 = None
    sk1 = None
    skType = ""
    isHideOptions = False
    isPlaceImmediately = False
vmtData = VmtMixerData()

txt_vmtNoMixingOptions = "No mixing options"
def CallbackDrawVoronoiMixer(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkOut0:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut0], isLineToCursor=True, isDrawText=False)
        tgl = not not self.foundGoalSkOut1
        DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut0, -0.5+0.75*tgl, int(tgl))
        if tgl:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut1], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut1, -1.25, -1)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiMixerTool(VoronoiToolDblSk):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True) #Стоит первым, чтобы быть похожим на VQMT в kmi.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False) #todo3 возможно стоит добавить промежуточный вариант, где отмена приведёт не к удалению, а к отмене перемещения, (но это не точно).
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vmBoxDiscl', self):
            LeftProp(colTool, prefs,'vmReroutesCanInAnyType')
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        if isBoth:
            self.foundGoalSkOut0 = None #Нужно обнулять из-за наличия двух continue ниже.
        self.foundGoalSkOut1 = None
        callPos = context.space_data.cursor_location
        isBothSucessTgl = True #Изначально был создан в VQMT. Нужен, чтобы повторно не перевыбирать уже успешный isBoth, если далее для второго сокета была лажа и цикл по нодам продолжился..
        vmReroutesCanInAnyType = self.prefs.vmReroutesCanInAnyType
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            StencilUnCollapseNode(nd, isBoth)
            list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)[1]
            if not list_fgSksOut:
                continue
            #В фильтре нод нет нужды.
            #Этот инструмент триггерится на любой выход (теперь кроме виртуальных) для первого.
            if (isBoth)and(isBothSucessTgl):
                for li in list_fgSksOut:
                    self.foundGoalSkOut0 = li
                    break
            isBothSucessTgl = not self.foundGoalSkOut0 #Чтобы не раскрывал все ноды в дереве.
            #Для второго по условиям:
            skOut0 = self.foundGoalSkOut0.tg if self.foundGoalSkOut0 else None
            if skOut0:
                for li in list_fgSksOut:
                    skOut1 = li.tg
                    orV = (skOut1.bl_idname=='NodeSocketVirtual')or(skOut0.bl_idname=='NodeSocketVirtual')
                    #Заметка: к VQMT такие возможности не относятся. Ибо он только по полям. Было бы странно цепляться ещё и к виртуальным.
                    tgl = (skOut1.bl_idname=='NodeSocketVirtual')^(skOut0.bl_idname=='NodeSocketVirtual')
                    tgl = (tgl)or( SkBetweenFieldsCheck(self, skOut0, skOut1)or( (skOut1.bl_idname==skOut0.bl_idname)and(not orV) ) )
                    tgl = (tgl)or( (skOut0.node.type=='REROUTE')or(skOut1.node.type=='REROUTE') )and(vmReroutesCanInAnyType)
                    if tgl:
                        self.foundGoalSkOut1 = li
                        break
                if (self.foundGoalSkOut1)and(skOut0==self.foundGoalSkOut1.tg): #Проверка на самокопию.
                    self.foundGoalSkOut1 = None
                StencilUnCollapseNode(nd, self.foundGoalSkOut1)
            #Не смотря на то, что в фильтре нод нет нужды и и так прекрасно работает на первом попавшемся, всё равно нужно продолжать поиск, если первый сокет найден не был.
            #Потому что если первым(ближайшим) окажется нод с неудачным результатом поиска, цикл закончится и инструмент ничего не выберет, даже если рядом есть подходящий.
            if self.foundGoalSkOut0: #Особенно заметно с активным isCanReOut (см. isCanReOut), без этого результат будет выбираться успешно/не-успешно в зависимости от положения курсора.
                break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (self.foundGoalSkOut0)and(self.isCanFromOne or self.foundGoalSkOut1):
                vmtData.sk0 = self.foundGoalSkOut0.tg
                vmtData.sk1 = self.foundGoalSkOut1.tg if self.foundGoalSkOut1 else None
                #Поддержка виртуальных выключена; читается только из первого
                vmtData.skType = vmtData.sk0.type if vmtData.sk0.bl_idname!='NodeSocketVirtual' else vmtData.sk1.type
                vmtData.isHideOptions = self.isHideOptions
                vmtData.isPlaceImmediately = self.isPlaceImmediately
                SetPieData(vmtData, self.prefs)
                di = dict_vmtTupleMixerMain.get(context.space_data.tree_type, False)
                if not di: #Если место действия не в классических редакторах, то просто выйти. Ибо классические редакторы у всех одинаковые, а аддонских есть бесчисленное множество.
                    return {'CANCELLED'}
                di = di.get(vmtData.skType, None)
                if di:
                    if length(di)==1: #Если выбор всего один, то пропустить его и сразу переходить к смешиванию.
                        DoMix(context, False, False, di[0]) #При моментальной активации можно и не отпустить модификаторы. Поэтому DoMix() получает не event, а вручную.
                    else: #Иначе предоставить выбор
                        bpy.ops.wm.call_menu_pie(name=VmtPieMixer.bl_idname)
                else: #Иначе для типа сокета не определено. Например шейдер в геонодах.
                    DisplayMessage("", txt_vmtNoMixingOptions, icon='RADIOBUT_OFF')
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=UselessForCustomUndefTrees(context):
            return result
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalSkOut0 = None
        self.foundGoalSkOut1 = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiMixer, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiMixerTool, "S#A_LEFTMOUSE") #Миксер перенесён на левую, чтобы освободить нагрузку для VQMT.
dict_setKmiCats['grt'].add(VoronoiMixerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vmBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vmReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be mixed to any type", default=True)
list_clsToAddon.append(VoronoiMixerTool)

vmtSep = 'MixerItemsSeparator'
dict_vmtTupleMixerMain = { #Порядок важен; самые частые (в этом списке) идут первее (кроме MixRGB).
        'ShaderNodeTree':     {'SHADER':     ('ShaderNodeMixShader','ShaderNodeAddShader'),
                               'VALUE':      ('ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath'),
                               'RGBA':       ('ShaderNodeMixRGB',  'ShaderNodeMix'),
                               'VECTOR':     ('ShaderNodeMixRGB',  'ShaderNodeMix',                                       'ShaderNodeVectorMath'),
                               'INT':        ('ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath')},
                               ##
        'GeometryNodeTree':   {'VALUE':      ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath'),
                               'RGBA':       ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare'),
                               'VECTOR':     ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare',                 'ShaderNodeVectorMath'),
                               'STRING':     ('GeometryNodeSwitch',                'FunctionNodeCompare',                                        'GeometryNodeStringJoin'),
                               'INT':        ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath'),
                               'BOOLEAN':    ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath',                       'FunctionNodeBooleanMath'),
                               'ROTATION':   ('GeometryNodeSwitch','ShaderNodeMix'),
                               'OBJECT':     ('GeometryNodeSwitch',),
                               'MATERIAL':   ('GeometryNodeSwitch',),
                               'COLLECTION': ('GeometryNodeSwitch',),
                               'TEXTURE':    ('GeometryNodeSwitch',),
                               'IMAGE':      ('GeometryNodeSwitch',),
                               'GEOMETRY':   ('GeometryNodeSwitch','GeometryNodeJoinGeometry','GeometryNodeInstanceOnPoints','GeometryNodeCurveToMesh','GeometryNodeMeshBoolean','GeometryNodeGeometryToInstance')},
                               ##
        'CompositorNodeTree': {'VALUE':      ('CompositorNodeMath',     vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'RGBA':       ('CompositorNodeAlphaOver',vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'VECTOR':     (                          vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'INT':        ('CompositorNodeMath',     vmtSep,'CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView')},
                               ##
        'TextureNodeTree':    {'VALUE':      ('TextureNodeMixRGB','TextureNodeTexture','TextureNodeMath'),
                               'RGBA':       ('TextureNodeMixRGB','TextureNodeTexture'),
                               'VECTOR':     ('TextureNodeMixRGB',                                        'TextureNodeDistance'),
                               'INT':        ('TextureNodeMixRGB','TextureNodeTexture','TextureNodeMath')}}
dict_vmtMixerNodesDefs = { #'-1' означают визуальную здесь метку, что их сокеты подключения высчитываются автоматически (см. |1|), а не указаны явно в этом списке
        #Отсортировано по количеству в "базе данных" выше.
        'GeometryNodeSwitch':             (-1, -1, "Switch"),
        'ShaderNodeMix':                  (-1, -1, "Mix"),
        'FunctionNodeCompare':            (-1, -1, "Compare"),
        'ShaderNodeMath':                 (0, 1, "Max Float"),
        'ShaderNodeMixRGB':               (1, 2, "Mix RGB"),
        'CompositorNodeMixRGB':           (1, 2, "Mix Col"),
        'CompositorNodeSwitch':           (0, 1, "Switch"),
        'CompositorNodeSplitViewer':      (0, 1, "Split Viewer"),
        'CompositorNodeSwitchView':       (0, 1, "Switch View"),
        'TextureNodeMixRGB':              (1, 2, "Mix Col"),
        'TextureNodeTexture':             (0, 1, "Texture"),
        'ShaderNodeVectorMath':           (0, 1, "Max Vector"),
        'CompositorNodeMath':             (0, 1, "Max Float"),
        'TextureNodeMath':                (0, 1, "Max Float"),
        'ShaderNodeMixShader':            (1, 2, "Mix Shader"),
        'ShaderNodeAddShader':            (0, 1, "Add Shader"),
        'GeometryNodeStringJoin':         (1, 1, "Join String"),
        'FunctionNodeBooleanMath':        (0, 1, "Or"),
        'CompositorNodeAlphaOver':        (1, 2, "Alpha Over"),
        'TextureNodeDistance':            (0, 1, "Distance"),
        'GeometryNodeJoinGeometry':       (0, 0, "Join"),
        'GeometryNodeInstanceOnPoints':   (0, 2, "Instance on Points"),
        'GeometryNodeCurveToMesh':        (0, 1, "Curve to Mesh"),
        'GeometryNodeMeshBoolean':        (0, 1, "Boolean"),
        'GeometryNodeGeometryToInstance': (0, 0, "To Instance")}
def DoMix(context, isS, isA, txt_node):
    tree = context.space_data.edit_tree
    if not tree:
        return
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt_node, use_transform=not vmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    aNd.width = 140
    txtFix = {'VALUE':'FLOAT'}.get(vmtData.skType, vmtData.skType)
    #Дважды switch case -- для комфортного кода и немножко экономии.
    match aNd.bl_idname:
        case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath':
            aNd.operation = 'MAXIMUM'
        case 'FunctionNodeBooleanMath':
            aNd.operation = 'OR'
        case 'TextureNodeTexture':
            aNd.show_preview = False
        case 'GeometryNodeSwitch':
            aNd.input_type = txtFix
        case 'FunctionNodeCompare':
            aNd.data_type = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
            aNd.operation = 'EQUAL'
        case 'ShaderNodeMix':
            aNd.data_type = {'INT':'FLOAT', 'BOOLEAN':'FLOAT'}.get(txtFix, txtFix)
    match aNd.bl_idname:
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|1|.
            tgl = aNd.bl_idname!='FunctionNodeCompare'
            txtFix = vmtData.skType
            match aNd.bl_idname:
                case 'FunctionNodeCompare': txtFix = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
                case 'ShaderNodeMix':       txtFix = {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(txtFix, txtFix)
            #Для микса и переключателя искать с конца, потому что их сокеты для переключения имеют тип некоторых искомых. У нода сравнения всё наоборот.
            list_foundSk = [sk for sk in ( reversed(aNd.inputs) if tgl else aNd.inputs ) if sk.type==txtFix]
            NewLinkAndRemember(vmtData.sk0, list_foundSk[tgl^isS]) #Из-за направления поиска, нужно выбирать их из списка также с учётом направления.
            if vmtData.sk1:
                NewLinkAndRemember(vmtData.sk1, list_foundSk[(not tgl)^isS])
        case _:
            #Такая плотная суета ради мультиинпута -- для него нужно изменить порядок подключения.
            if (vmtData.sk1)and(aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][0]].is_multi_input): #`0` здесь в основном из-за того, что в dict_vmtMixerNodesDefs у "нодов-мультиинпутов" всё по нулям.
                NewLinkAndRemember( vmtData.sk1, aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][1^isS]] )
            DoLinkHH( vmtData.sk0, aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][0^isS]] ) #Это не NewLinkAndRemember(), чтобы визуальный второй мультиинпута был последним в vlrtData.
            if (vmtData.sk1)and(not aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][0]].is_multi_input):
                NewLinkAndRemember( vmtData.sk1, aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][1^isS]] )
    if vmtData.isHideOptions:
        aNd.show_options = False
    #Далее так же, как и в vqmt. У него первично; здесь дублировано для интуитивного соответствия.
    if isA:
        for sk in aNd.inputs:
            sk.hide = True

class VmtOpMixer(VoronoiOp):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = "Mixer Mixer"
    txt: bpy.props.StringProperty()
    def invoke(self, context, event):
        DoMix(context, event.shift, event.alt, self.txt)
        return {'FINISHED'}
class VmtPieMixer(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_mixer_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, context):
        pie = self.layout.menu_pie()
        def AddOp(where, txt):
            if (not vmtData.isSpeedPie)and(vmtData.pieAlignment==1):
                where = where.row()
            where.operator(VmtOpMixer.bl_idname, text=dict_vmtMixerNodesDefs[txt][2], translate=False).txt = txt
        dict_items = dict_vmtTupleMixerMain[context.space_data.tree_type][vmtData.skType]
        if vmtData.isSpeedPie:
            for li in dict_items:
                if li!=vmtSep:
                    AddOp(pie, li)
        else:
            #Если при выполнении колонка окажется пустой, то в ней будет отображаться только пустая точка-коробка. Два списка ниже нужны, чтобы починить это.
            list_cols = [pie.row(), pie.row(), pie.row() if vmtData.pieDisplaySocketTypeInfo>0 else None]
            list_done = [False, False, False]
            def PieCol(inx):
                if list_done[inx]:
                    return list_cols[inx]
                box = list_cols[inx].box()
                col = box.column(align=vmtData.pieAlignment<2)
                col.ui_units_x = 6*((vmtData.pieScale-1)/2+1)
                col.scale_y = vmtData.pieScale
                list_cols[inx] = col
                list_done[inx] = True
                return col
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    row2 = PieCol(0).row(align=vmtData.pieAlignment==0)
                    row2.enabled = False
                    AddOp(row2, 'ShaderNodeMix')
                case 'GeometryNodeTree':
                    row1 = PieCol(0).row(align=vmtData.pieAlignment==0)
                    row2 = PieCol(0).row(align=vmtData.pieAlignment==0)
                    row3 = PieCol(0).row(align=vmtData.pieAlignment==0)
                    row1.enabled = False
                    row2.enabled = False
                    row3.enabled = False
                    AddOp(row1, 'GeometryNodeSwitch')
                    AddOp(row2, 'ShaderNodeMix')
                    AddOp(row3, 'FunctionNodeCompare')
            sco = 0
            for li in dict_items:
                match li:
                    case 'GeometryNodeSwitch':  row1.enabled = True
                    case 'ShaderNodeMix':       row2.enabled = True
                    case 'FunctionNodeCompare': row3.enabled = True
                    case _:
                        if li==vmtSep:
                            if sco:
                                PieCol(1).separator()
                        else:
                            AddOp(PieCol(1), li)
                            sco += 1
            if vmtData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=GetSkCol(vmtData.sk0))
                row.label(text=vmtData.sk0.bl_label)

list_classes += [VmtOpMixer, VmtPieMixer]

class VqmtQuickMathData(PieData):
    list_displayItems = []
    sk0 = None
    sk1 = None
    depth = 0
    qmSkType = ''
    qmTrueSkType = ''
    isHideOptions = False
    isPlaceImmediately = False
    isJustPie = False
    canProcHideSks = True
    dict_lastOperation = {}
    isFirstDone = False #github.com/ugorek000/VoronoiLinker/issues/20
vqmtData = VqmtQuickMathData()

set_vqmtSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}

def CallbackDrawVoronoiQuickMath(self, context): #Поскольку теперь у vqmt три сокета, callback от vmt использовать уже не получится.
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkOut0:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut0], isLineToCursor=True, isDrawText=False)
        tgl = not not self.foundGoalSkOut1
        DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut0, -0.5+0.75*tgl, int(tgl))
        if tgl:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut1], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut1, -1.25, -1)
        if self.foundGoalSkOut2:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut2], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut2, -0.5, 0)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiQuickMathTool(VoronoiToolDblSk):
    bl_idname = 'node.voronoi_quick_math'
    bl_label = "Voronoi Quick Math"
    quickOprFloat:  bpy.props.StringProperty(name="Float (quick)",  default="") #Они в начале, чтобы в kmi отображалось выровненным.
    quickOprVector: bpy.props.StringProperty(name="Vector (quick)", default="") #quick вторым, чтобы при нехватке места отображалось первое слово, от чего пришлось заключить в скобки.
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True)
    isRepeatLastOperation: bpy.props.BoolProperty(name="Repeat last operation", default=False) #Что ж, квартет qqm теперь вынуждает их постоянно выравнивать.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    quickOprBool:   bpy.props.StringProperty(name="Bool (quick)",   default="")
    quickOprColor:  bpy.props.StringProperty(name="Color (quick)",  default="")
    justCallPie:           bpy.props.IntProperty(name="Just call pie", default=0, min=0, max=4)
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vqmBoxDiscl', self):
            LeftProp(colTool, prefs,'vqmIncludeThirdSk')
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        if isBoth:
            self.foundGoalSkOut0 = None
        isNotPickThird = not self.canPickThirdSk
        if isNotPickThird:
            self.foundGoalSkOut1 = None
        callPos = context.space_data.cursor_location
        isBothSucessTgl = True
        sco = 0
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            sco += 1
            nd = li.tg
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            if not list_fgSksOut:
                continue
            #Этот инструмент триггерится только на выходы поля.
            if (isBoth)and(isBothSucessTgl):
                isSucessOut = False
                for li in list_fgSksOut:
                    if not self.isRepeatLastOperation:
                        if not self.isQuickQuickMath:
                            if li.tg.type in set_vqmtSkTypeFields:
                                self.foundGoalSkOut0 = li
                                isSucessOut = True
                                break
                        else: #Для isQuickQuickMath цепляться только к типам сокетов от явно указанных операций.
                            match li.tg.type:
                                case 'VALUE'|'INT':     isSucessOut = self.quickOprFloat
                                case 'VECTOR':          isSucessOut = self.quickOprVector
                                case 'BOOLEAN':         isSucessOut = self.quickOprBool
                                case 'RGBA'|'ROTATION': isSucessOut = self.quickOprColor
                            if isSucessOut:
                                self.foundGoalSkOut0 = li
                                break
                    else:
                        isSucessOut = vqmtData.dict_lastOperation.get(li.tg.type, '')
                        if isSucessOut:
                            self.foundGoalSkOut0 = li
                            break
                if not isSucessOut:
                    continue #Искать нод, у которого попадёт на сокет поля.
                    #Если так ничего и не найдёт, то мб isBothSucessTgl стоит равным как в VMT; слишком дебри, моих навыков не хватает.
                nd.hide = False #После чего в любом случае развернуть его.
            isBothSucessTgl = False #Для следующего `continue`, ибо если далее будет неудача с последующей активацией continue, то произойдёт перевыбор isBoth.
            skOut0 = self.foundGoalSkOut0.tg if self.foundGoalSkOut0 else None
            if isNotPickThird:
                #Для второго по условиям:
                if skOut0:
                    isSucessIn = False
                    for li in list_fgSksOut:
                        if SkBetweenFieldsCheck(self, skOut0, li.tg):
                            self.foundGoalSkOut1 = li
                            isSucessIn = True
                            break
                    if not isSucessIn:
                        continue
                    if (self.foundGoalSkOut1)and(skOut0==self.foundGoalSkOut1.tg): #Проверка на самокопию.
                        self.foundGoalSkOut1 = None
                    StencilUnCollapseNode(nd, self.foundGoalSkOut1) #Заметка: нод isBoth'а разворачивается здесь.
            else:
                self.foundGoalSkOut2 = None #Обнулять для удобства высокоуровневой отмены.
                #Для третьего, если не ноды двух предыдущих.
                skOut1 = self.foundGoalSkOut1.tg if self.foundGoalSkOut1 else None
                for li in list_fgSksIn:
                    skIn = li.tg
                    if skIn.type in set_vqmtSkTypeFields:
                        tgl0 = (not skOut0)or(skOut0.node!=skIn.node)
                        tgl1 = (not skOut1)or(skOut1.node!=skIn.node)
                        if (tgl0)and(tgl1):
                            self.foundGoalSkOut2 = li
                            break
            break
    def modal(self, context, event):
        prefs = self.prefs
        if (prefs.vqmIncludeThirdSk)and(self.isStartWithModf)and(not self.canPickThirdSk):
            self.canPickThirdSk = not(event.shift or event.ctrl or event.alt)
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (self.foundGoalSkOut0)and(self.isCanFromOne or self.foundGoalSkOut1):
                vqmtData.sk0 = self.foundGoalSkOut0.tg
                vqmtData.sk1 = self.foundGoalSkOut1.tg if self.foundGoalSkOut1 else None
                vqmtData.sk2 = self.foundGoalSkOut2.tg if self.foundGoalSkOut2 else None
                vqmtData.isHideOptions = self.isHideOptions
                vqmtData.isPlaceImmediately = self.isPlaceImmediately
                vqmtData.qmSkType = vqmtData.sk0.type #Заметка: наличие только сокетов поля -- забота на уровень выше.
                vqmtData.qmTrueSkType = vqmtData.qmSkType #Эта информация нужна для "последней операции".
                match vqmtData.sk0.type:
                    case 'INT':      vqmtData.qmSkType = 'VALUE' #И только целочисленный обделён своим нодом математики. Может его добавят когда-нибудь?.
                    case 'ROTATION': vqmtData.qmSkType = 'RGBA' #Больше шансов, что для математика для кватерниона будет первее.
                    #case 'ROTATION': return {'FINISHED'} #Однако странно, почему с RGBA линки отмечаются не корректными, ведь оба Arr4... Зачем тогда цвету альфа?
                match context.space_data.tree_type:
                    case 'ShaderNodeTree':     vqmtData.qmSkType = {'BOOLEAN':'VALUE'}.get(vqmtData.qmSkType, vqmtData.qmSkType)
                    case 'GeometryNodeTree':   pass
                    case 'CompositorNodeTree': vqmtData.qmSkType = {'BOOLEAN':'VALUE', 'VECTOR':'RGBA'}.get(vqmtData.qmSkType, vqmtData.qmSkType)
                    case 'TextureNodeTree':    vqmtData.qmSkType = {'BOOLEAN':'VALUE', 'VECTOR':'RGBA'}.get(vqmtData.qmSkType, vqmtData.qmSkType)
                if self.isRepeatLastOperation:
                    return DoQuickMath(event, context.space_data.edit_tree, vqmtData.dict_lastOperation[vqmtData.qmTrueSkType])
                if self.isQuickQuickMath:
                    match vqmtData.qmSkType:
                        case 'VALUE':   txt_opr = self.quickOprFloat
                        case 'VECTOR':  txt_opr = self.quickOprVector
                        case 'BOOLEAN': txt_opr = self.quickOprBool
                        case 'RGBA':    txt_opr = self.quickOprColor
                    return DoQuickMath(event, context.space_data.edit_tree, txt_opr)
                vqmtData.depth = 0
                SetPieData(vqmtData, prefs)
                vqmtData.isJustPie = False
                vqmtData.isFirstDone = False
                vqmtData.canProcHideSks = True
                bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=UselessForCustomUndefTrees(context):
            return result
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        vqmtData.canProcHideSks = False #Сразу для двух DoQuickMath выше и оператора ниже.
        if self.justCallPie:
            match context.space_data.tree_type:
                case 'ShaderNodeTree': can = self.justCallPie in {1,2,4}
                case 'GeometryNodeTree': can = True
                case 'CompositorNodeTree'|'TextureNodeTree': can = self.justCallPie in {1,4}
            if not can:
                DisplayMessage("", "There is nothing") #"Ничего нет".
                return {'CANCELLED'}
            vqmtData.sk0 = None #Обнулять для полноты картины и для GetSkCol().
            vqmtData.sk1 = None
            vqmtData.sk2 = None
            vqmtData.isHideOptions = self.isHideOptions
            vqmtData.isPlaceImmediately = self.isPlaceImmediately
            vqmtData.qmSkType = ('VALUE','VECTOR','BOOLEAN','RGBA')[self.justCallPie-1]
            vqmtData.depth = 0
            SetPieData(vqmtData, prefs)
            vqmtData.isJustPie = True
            vqmtData.isFirstDone = False
            bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
            return {'FINISHED'}
        self.foundGoalSkOut0 = None
        self.foundGoalSkOut1 = None
        self.foundGoalSkOut2 = None #Охренеть идея.
        self.isQuickQuickMath = not not( (self.quickOprFloat)or(self.quickOprVector)or(self.quickOprBool)or(self.quickOprColor) )
        self.isStartWithModf = (event.shift)or(event.ctrl)or(event.alt)
        self.canPickThirdSk = False
        StencilToolWorkPrepare(self, prefs, context, CallbackDrawVoronoiQuickMath, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_RIGHTMOUSE") #Осталось на правой, чтобы не охреневать от тройного клика левой при 'Speed Pie' типе пирога.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_ACCENT_GRAVE", {'isRepeatLastOperation':True})
#Список быстрых операций для быстрой математики ("x2 комбо"):
#Дилемма с логическим на "3", там может быть вычитание, как все на этой клавише, или отрицание, как логическое продолжение первых двух. Во втором случае булеан на 4 скорее всего придётся делать никаким.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_1", {'quickOprFloat':'ADD',      'quickOprVector':'ADD',      'quickOprBool':'OR',     'quickOprColor':'ADD'     })
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_2", {'quickOprFloat':'SUBTRACT', 'quickOprVector':'SUBTRACT', 'quickOprBool':'NIMPLY', 'quickOprColor':'SUBTRACT'})
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_3", {'quickOprFloat':'MULTIPLY', 'quickOprVector':'MULTIPLY', 'quickOprBool':'AND',    'quickOprColor':'MULTIPLY'})
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_4", {'quickOprFloat':'DIVIDE',   'quickOprVector':'DIVIDE',   'quickOprBool':'NOT',    'quickOprColor':'DIVIDE'  })
#Хотел я реализовать это для QuickMathMain, но оказалось слишком лажа превращать технический оператор в пользовательский. Основная проблема -- vqmtData настроек пирога.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_1", {'justCallPie':1}) #Неожиданно, но такой хоткей весьма приятный.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_2", {'justCallPie':2}) # Из-за двух модификаторов приходится держать нажатым,
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_3", {'justCallPie':3}) # от чего приходится выбирать позицией курсора, а не кликом.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_4", {'justCallPie':4}) # Я думал это будет неудобно, а оказалось даже приятно.
dict_setKmiCats['grt'].add(VoronoiQuickMathTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vqmBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vqmIncludeThirdSk: bpy.props.BoolProperty(name="Include third socket", default=True)
list_clsToAddon.append(VoronoiQuickMathTool)

#Быстрая математика.
#Заполучить нод с нужной операцией и автоматическим соединением в сокеты, благодаря мощностям VL'а.
#Неожиданно для меня оказалось, что пирог может рисовать обычный layout. От чего добавил дополнительный тип пирога "для контроля".
#А также сам буду пользоваться им, потому что за то время, которое экономится при двойном пироге, отдохнуть как-то всё равно не получается.
#Важная эстетическая ценность двойного пирога -- визуальная неперегруженность вариантами. Вместо того, чтобы вываливать всё сразу, показываются только по 8 штук за раз.

#todo0 с приходом популярности, посмотреть кто использует быстрый пирог, а потом аннигилировать его за ненадобностью; настолько распинаться о нём было бессмысленно.
#Заметка для меня: сохранять поддержку двойного пирога чёрт возьми, ибо эстетика. Но выпилить его с каждым разом хочется всё больше D:

#Было бы бездумно разбросать их как попало, поэтому я пытался соблюсти некоторую логическую последовательность. Например, расставляя пары по смыслу диаметрально противоположными.
#Пирог Блендера располагает в себе элементы следующим образом: лево, право, низ, верх, после чего классическое построчное заполнение.
#"Compatible..." -- чтобы у векторов и у математики одинаковые операции были на одинаковых местах (кроме тригонометрических).
#За исключением примитивов, где прослеживается супер очевидная логика (право -- плюс -- add, лево -- минус -- sub; всё как на числовой оси), лево и низ у меня более простые, чем обратная сторона.
#Например, length проще, чем distance. Всем же остальным не очевидным и не осе-ориентированным досталось как получится.

tuple_vqmtQuickMathMapValue = (
        ("Advanced",              ('SQRT',       'POWER',        'EXPONENT',   'LOGARITHM',   'INVERSE_SQRT','PINGPONG',    'FLOORED_MODULO' )),
        ("Compatible Primitives", ('SUBTRACT',   'ADD',          'DIVIDE'   ,  'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ("Rounding",              ('SMOOTH_MIN', 'SMOOTH_MAX',   'LESS_THAN',  'GREATER_THAN','SIGN',        'COMPARE',     'TRUNC',  'ROUND')),
        ("Compatible Vector",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACT',       'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ("", ()), #Важны дубликаты и порядок, поэтому не словарь а список.
        ("", ()),
        ("Other",                 ('COSH',       'RADIANS',      'DEGREES',    'SINH',        'TANH'                                         )),
        ("Trigonometric",         ('SINE',       'COSINE',       'TANGENT',    'ARCTANGENT',  'ARCSINE',     'ARCCOSINE',   'ARCTAN2'        )) )
tuple_vqmtQuickMathMapVector = (
        ("Advanced",              ('SCALE',      'NORMALIZE',    'LENGTH',     'DISTANCE',    'SINE',        'COSINE',      'TANGENT'       )),
        ("Compatible Primitives", ('SUBTRACT',   'ADD',          'DIVIDE',     'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                 )),
        ("Rays",                  ('DOT_PRODUCT','CROSS_PRODUCT','PROJECT',    'FACEFORWARD', 'REFRACT',     'REFLECT'                      )),
        ("Compatible Vector",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACTION',    'CEIL',        'MODULO',      'SNAP',   'WRAP')),
        ("", ()),
        ("", ()),
        ("", ()),
        ("", ()) )
tuple_vqmtQuickMathMapBoolean = (
        ("High",  ('NOR','NAND','XNOR','XOR','IMPLY','NIMPLY')),
        ("Basic", ('OR', 'AND', 'NOT'                        )) )
tuple_vqmtQuickModeMapColor = (
        #Для операции 'MIX' используйте VMT.
        ("Math", ('SUBTRACT','ADD',       'DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION'                    )), #'EXCLUSION' не влез в "Art"; и было бы неплохо узнать его предназначение.
        ("Art",  ('DARKEN',  'LIGHTEN','   DODGE', 'SCREEN',  'SOFT_LIGHT','LINEAR_LIGHT','BURN','OVERLAY')),
        ("Raw",  ('VALUE',   'SATURATION','HUE',   'COLOR'                                                )) ) #Хотел переназвать на "Overwrite", но передумал.
dict_vqmtQuickMathMain = {
        'VALUE':   tuple_vqmtQuickMathMapValue,
        'VECTOR':  tuple_vqmtQuickMathMapVector,
        'BOOLEAN': tuple_vqmtQuickMathMapBoolean,
        'RGBA':    tuple_vqmtQuickModeMapColor}
#Ассоциация нода для типа редактора и сокета
dict_vqmtEditorNodes = {
        'VALUE':   {'ShaderNodeTree':     'ShaderNodeMath',
                    'GeometryNodeTree':   'ShaderNodeMath',
                    'CompositorNodeTree': 'CompositorNodeMath',
                    'TextureNodeTree':    'TextureNodeMath'},
        ##
        'VECTOR':  {'ShaderNodeTree':     'ShaderNodeVectorMath',
                    'GeometryNodeTree':   'ShaderNodeVectorMath'},
        ##
        'BOOLEAN': {'GeometryNodeTree':   'FunctionNodeBooleanMath'},
        ##
        'RGBA':    {'ShaderNodeTree':     'ShaderNodeMix',
                    'GeometryNodeTree':   'ShaderNodeMix',
                    'CompositorNodeTree': 'CompositorNodeMixRGB',
                    'TextureNodeTree':    'TextureNodeMixRGB'} }
#Значения по умолчанию для сокетов в зависимости от операции
dict_vqmtDefaultValueOperation = {
        'VALUE': {'MULTIPLY':(1.0, 1.0, 1.0),
                  'DIVIDE':  (1.0, 1.0, 1.0),
                  'POWER':   (2.0, 1/3, 0.0),
                  'SQRT':    (2.0, 2.0, 2.0),
                  'ARCTAN2': (math.pi, math.pi, math.pi)},
        'VECTOR': {'MULTIPLY':     ( (1,1,1), (1,1,1), (1,1,1), 1.0 ),
                   'DIVIDE':       ( (1,1,1), (1,1,1), (1,1,1), 1.0 ),
                   'CROSS_PRODUCT':( (0,0,1), (0,0,1), (0,0,1), 1.0 ),
                   'SCALE':        ( (0,0,0), (0,0,0), (0,0,0), math.pi )},
        'BOOLEAN': {'AND': (True, True),
                    'NOR': (True, True),
                    'XOR': (False, True),
                    'XNOR': (False, True),
                    'IMPLY': (True, False),
                    'NIMPLY': (True, False)},
        'RGBA': {'ADD':       ( (0,0,0,1), (0,0,0,1) ),
                 'SUBTRACT':  ( (0,0,0,1), (0,0,0,1) ),
                 'MULTIPLY':  ( (1,1,1,1), (1,1,1,1) ),
                 'DIVIDE':    ( (1,1,1,1), (1,1,1,1) ),
                 'DIFFERENCE':( (0,0,0,1), (1,1,1,1) ),
                 'EXCLUSION': ( (0,0,0,1), (1,1,1,1) ),
                 'VALUE':     ( (1,1,1,1), (1,1,1,1) ),
                 'SATURATION':( (1,1,1,1), (0,0,1,1) ),
                 'HUE':       ( (1,1,1,1), (0,1,0,1) ),
                 'COLOR':     ( (1,1,1,1), (1,0,0,1) ) } }
dict_vqmtDefaultDefault = {
        #Заметка: основано на типе нода, а не на типе сокета. Повезло, что они одинаковые.
        'VALUE': (0.0, 0.0, 0.0),
        'VECTOR': ((0,0,0), (0,0,0), (0,0,0), 0.0),
        'BOOLEAN': (False, False),
        'RGBA': ( (.25,.25,.25,1), (.5,.5,.5,1) ) } #Можно было оставить без изменений, но всё равно обнуляю. Ради чего был создан VQMT?.
def DoQuickMath(event, tree, opr, isCombo=False):
    txt = dict_vqmtEditorNodes[vqmtData.qmSkType].get(tree.bl_idname, "")
    if not txt: #Если нет в списке, то этот нод не существует (по задумке списка) в этом типе редактора => "смешивать" нечем, поэтому выходим.
        return {'CANCELLED'}
    #Ядро быстрой математики, добавить нод и создать линки:
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt, use_transform=not vqmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    if vqmtData.qmSkType!='RGBA': #Ох уж этот цвет.
        aNd.operation = opr
    else:
        if aNd.bl_idname=='ShaderNodeMix':
            aNd.data_type = 'RGBA'
            aNd.clamp_factor = False
        aNd.blend_type = opr
        aNd.inputs[0].default_value = 1.0
        aNd.inputs[0].hide = opr in {'ADD','SUBTRACT','DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION','VALUE','SATURATION','HUE','COLOR'}
    #Теперь существует justCallPie, а значит пришло время скрывать значение первого сокета (но нужда в этом только для вектора).
    if vqmtData.qmSkType=='VECTOR':
        aNd.inputs[0].hide_value = True
    #Идея с event.shift гениальна. Изначально ради одиночного линка во второй сокет, но благодаря визуальному поиску ниже, может и менять местами два линка.
    bl4ofs = 2*isBlender4*(tree.bl_idname in {'ShaderNodeTree','GeometryNodeTree'})
    skInx = aNd.inputs[0] if vqmtData.qmSkType!='RGBA' else aNd.inputs[-2-bl4ofs] #"Inx", потому что пародия на int "index", но потом понял, что можно сразу в сокет для линковки далее.
    if event.shift:
        for sk in aNd.inputs:
            if (sk!=skInx)and(sk.enabled)and(not sk.links):
                if sk.type==skInx.type:
                    skInx = sk
                    break
    if vqmtData.sk0:
        NewLinkAndRemember(vqmtData.sk0, skInx)
        if vqmtData.sk1:
            #Второй ищется "визуально"; сделано ради операции 'SCALE'.
            for sk in aNd.inputs: #Ищется сверху вниз. Потому что ещё и 'MulAdd'.
                if (sk.enabled)and(not sk.links):
                    #Ох уж этот скейл; единственный с двумя сокетами разных типов.
                    if (sk.type==skInx.type)or(opr=='SCALE'): #Искать одинаковый по типу. Актуально для RGBA Mix.
                        NewLinkAndRemember(vqmtData.sk1, sk)
                        break #Нужно соединить только в первый попавшийся, иначе будет соединено во все (например у 'MulAdd').
        elif isCombo:
            for sk in aNd.inputs:
                if (sk.type==skInx.type)and(not sk.is_linked): #Можно было и проще.
                    NewLinkAndRemember(vqmtData.sk0, sk)
                    break
        if vqmtData.sk2:
            for sk in aNd.outputs:
                if (sk.enabled)and(not sk.hide):
                    NewLinkAndRemember(sk, vqmtData.sk2)
                    break
    #Установить значение по умолчанию для второго сокета (большинство нули). Нужно для красоты; и вообще это математика.
    #Заметка: нод вектора уже создаётся по нулям, так что для него обнулять без нужды.
    tuple_default = dict_vqmtDefaultDefault[vqmtData.qmSkType]
    if vqmtData.qmSkType!='RGBA':
        for cyc, sk in enumerate(aNd.inputs):
            #Здесь нет проверок на видимость и линки, пихать значение насильно. Потому что я так захотел.
            sk.default_value = dict_vqmtDefaultValueOperation[vqmtData.qmSkType].get(opr, tuple_default)[cyc]
    else: #Оптимизация для экономии в dict_vqmtDefaultValueOperation.
        tuple_col = dict_vqmtDefaultValueOperation[vqmtData.qmSkType].get(opr, tuple_default)
        aNd.inputs[-2-bl4ofs].default_value = tuple_col[0]
        aNd.inputs[-1-bl4ofs].default_value = tuple_col[1]
    #Скрыть все сокеты по запросу. На покерфейсе, ибо залинкованные сокеты всё равно не скроются; и даже без проверки 'sk.enabled'.
    if vqmtData.canProcHideSks: #Для isJustPie нет нужды и могут быть случайные нажатия, для qqm вообще не по концепции.
        if event.alt: #Удобненько получается для основного назначения, можно даже не отпускать Shift Alt.
            for sk in aNd.inputs:
                sk.hide = True
    if vqmtData.isHideOptions:
        aNd.show_options = False
    return {'FINISHED'}
class VqmtOpMain(VoronoiOp):
    bl_idname = 'node.voronoi_quick_math_main'
    bl_label = "Quick Math"
    operation: bpy.props.StringProperty()
    isCombo: bpy.props.BoolProperty(default=False)
    def modal(self, context, event):
        #Раньше нужно было очищать мост вручную, потому что он оставался равным последней записи. Сейчас уже не нужно.
        return {'FINISHED'}
    def invoke(self, context, event):
        #Заметка: здесь использование ForseSetSelfNonePropToDefault() уже не работает задуманным образом для непрямого вызова оператора.
        tree = context.space_data.edit_tree
        if not tree:
            return {'CANCELLED'}
        match vqmtData.depth:
            case 0:
                if vqmtData.isSpeedPie:
                    vqmtData.list_displayItems = [ti[0] for ti in dict_vqmtQuickMathMain[vqmtData.qmSkType]]
                else:
                    vqmtData.depth += 1
            case 1:
                if vqmtData.isSpeedPie:
                    vqmtData.list_displayItems = [ti[1] for ti in dict_vqmtQuickMathMain[vqmtData.qmSkType] if ti[0]==self.operation][0] #Заметка: вычленяется кортеж из генератора.
            case 2:
                if vqmtData.isFirstDone:
                    return {'FINISHED'}
                vqmtData.isFirstDone = True
                #Запоминать нужно только и очевидно только здесь. В Tool только qqm и rlo. Для qqm не запоминается для удобства, и следованию логики rlo.
                vqmtData.dict_lastOperation[vqmtData.qmTrueSkType] = self.operation
                return DoQuickMath(event, tree, self.operation, self.isCombo)
        vqmtData.depth += 1
        bpy.ops.wm.call_menu_pie(name=VqmtPieMath.bl_idname)
        return {'RUNNING_MODAL'}
class VqmtPieMath(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_quick_math_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, context):
        def AddOp(where, txt, ico='NONE', txt_combo=""):
            if not vqmtData.isSpeedPie:
                where = where.row(align=True)
                if (vqmtData.pieDisplaySocketTypeInfo==2)and(colCurSk):
                    col = where.column()
                    if vqmtData.pieScale>1.25:
                        row = col.column()
                        row.label()
                        row.scale_y = (vqmtData.pieScale-1.2)/2
                    row = col.column()
                    row.template_node_socket(color=colCurSk)
                rowOp = where.row(align=vqmtData.pieAlignment==0)
                #Из-за 'pieDisplaySocketTypeInfo==2' масштаб устанавливается здесь для каждого оператора, а не в GetPieCol().
                rowOp.ui_units_x = 5.5*((vqmtData.pieScale-1)/2+1)
                rowOp.scale_y = vqmtData.pieScale
                where = rowOp
            #Автоматический перевод выключен, ибо оригинальные операции у нода математики тоже не переводятся.
            op = where.operator(VqmtOpMain.bl_idname, text=txt_combo if txt_combo else (txt.capitalize().replace("_"," ") if vqmtData.depth else txt), icon=ico if not txt_combo else 'NONE', translate=False)
            op.operation = txt
            op.isCombo = not not txt_combo
        pie = self.layout.menu_pie()
        colCurSk = GetSkCol(vqmtData.sk0) if vqmtData.sk0 else None #Скорее всего есть ненулевая эстетика в том, что для justCallPie цвет сокета не отображается (по крайней мере для psdt=1).
        if vqmtData.isSpeedPie:
            for li in vqmtData.list_displayItems:
                if not li: #Для пустых записей в базе данных для быстрого пирога.
                    row = pie.row() #Ибо благодаря этому отображается никаким и занимает место.
                    continue
                AddOp(pie, li)
        else:
            def GetPieCol(where):
                col = where.column(align=vqmtData.pieAlignment<2)
                return col
            colLeft = GetPieCol(pie)
            colRight = GetPieCol(pie)
            colCenter = GetPieCol(pie)
            if vqmtData.pieDisplaySocketTypeInfo==1:
                colLabel = pie.column()
                box = colLabel.box()
                row = box.row(align=True)
                if colCurSk:
                    row.template_node_socket(color=colCurSk)
                match vqmtData.qmSkType:
                    case 'VALUE':   txt = "Float Quick Math"
                    case 'VECTOR':  txt = "Vector Quick Math"
                    case 'BOOLEAN': txt = "Boolean Quick Math"
                    case 'RGBA':    txt = "Color Quick Mode"
                row.label(text=txt)
                row.alignment = 'CENTER'
            isNotJustPie= not vqmtData.isJustPie
            def DrawForValVec(isVec):
                row = colRight.row(align=True)
                row.scale_x = 0.5
                AddOp(row,'ADD','ADD')
                row = row.row(align=True)
                canDouble = (isNotJustPie)and(not vqmtData.sk1)
                if canDouble:
                    AddOp(row,'ADD','ADD', txt_combo='x2')
                    row.scale_x = 0.25
                AddOp(colRight,'SUBTRACT','REMOVE')
                ##
                row = colRight.row(align=True)
                row.scale_x = 0.5
                AddOp(row,'MULTIPLY','SORTBYEXT')
                row = row.row(align=True)
                if canDouble:
                    AddOp(row,'MULTIPLY','SORTBYEXT', txt_combo='x2')
                    row.scale_x = 0.25
                AddOp(colRight,'DIVIDE','FIXED_SIZE') #ITALIC  FIXED_SIZE
                ##
                colRight.separator()
                AddOp(colRight, 'MULTIPLY_ADD')
                AddOp(colRight, 'ABSOLUTE')
                colRight.separator()
                for li in ('SINE','COSINE','TANGENT'):
                    AddOp(colCenter, li, 'FORCE_HARMONIC')
                if not isVec:
                    for li in ('POWER','SQRT','EXPONENT','LOGARITHM','INVERSE_SQRT','PINGPONG'):
                        AddOp(colRight, li)
                    colRight.separator()
                    AddOp(colRight, 'RADIANS')
                    AddOp(colRight, 'DEGREES')
                    AddOp(colLeft, 'FRACT', 'IPO_LINEAR')
                    for li in ('ARCTANGENT','ARCSINE','ARCCOSINE'):
                        AddOp(colCenter, li, 'RNA')
                    for li in ('ARCTAN2','SINH','COSH','TANH'):
                        AddOp(colCenter, li)
                else:
                    for li in ('SCALE','NORMALIZE','LENGTH','DISTANCE'):
                        AddOp(colRight, li)
                    colRight.separator()
                    AddOp(colLeft, 'FRACTION', 'IPO_LINEAR')
                AddOp(colLeft,'FLOOR','IPO_CONSTANT')
                AddOp(colLeft,'CEIL')
                AddOp(colLeft,'MAXIMUM','NONE') #SORT_DESC  TRIA_UP_BAR
                AddOp(colLeft,'MINIMUM','NONE') #SORT_ASC  TRIA_DOWN_BAR
                for li in ('MODULO', 'FLOORED_MODULO', 'SNAP', 'WRAP'):
                    AddOp(colLeft, li)
                colLeft.separator()
                if not isVec:
                    for li in ('GREATER_THAN','LESS_THAN','TRUNC','SIGN','SMOOTH_MAX','SMOOTH_MIN','ROUND','COMPARE'):
                        AddOp(colLeft, li)
                else:
                    AddOp(colLeft,'DOT_PRODUCT',  'LAYER_ACTIVE')
                    AddOp(colLeft,'CROSS_PRODUCT','ORIENTATION_LOCAL') #OUTLINER_DATA_EMPTY  ORIENTATION_LOCAL  EMPTY_ARROWS
                    AddOp(colLeft,'PROJECT',      'CURVE_PATH') #SNAP_OFF  SNAP_ON  MOD_SIMPLIFY  CURVE_PATH
                    AddOp(colLeft,'FACEFORWARD',  'ORIENTATION_NORMAL')
                    AddOp(colLeft,'REFRACT',      'NODE_MATERIAL') #MOD_OFFSET  NODE_MATERIAL
                    AddOp(colLeft,'REFLECT',      'INDIRECT_ONLY_OFF') #INDIRECT_ONLY_OFF  INDIRECT_ONLY_ON
            def DrawForBool():
                AddOp(colRight,'AND')
                AddOp(colRight,'OR')
                AddOp(colRight,'NOT')
                AddOp(colLeft,'NAND')
                AddOp(colLeft,'NOR')
                AddOp(colLeft,'XOR')
                AddOp(colLeft,'XNOR')
                AddOp(colCenter,'IMPLY')
                AddOp(colCenter,'NIMPLY')
            def DrawForCol():
                for li in ('LIGHTEN','DARKEN','SCREEN','DODGE','LINEAR_LIGHT','SOFT_LIGHT','OVERLAY','BURN'):
                    AddOp(colRight, li)
                for li in ('ADD','SUBTRACT','MULTIPLY','DIVIDE','DIFFERENCE','EXCLUSION'):
                    AddOp(colLeft, li)
                for li in ('VALUE','SATURATION','HUE','COLOR'):
                    AddOp(colCenter, li)
            match vqmtData.qmSkType:
                case 'VALUE'|'VECTOR': DrawForValVec(vqmtData.qmSkType=='VECTOR')
                case 'BOOLEAN': DrawForBool()
                case 'RGBA': DrawForCol()

list_classes += [VqmtOpMain, VqmtPieMath]

def CallbackDrawVoronoiRanto(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalNd:
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalNd)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiRantoTool(VoronoiToolNd): #Свершится.
    bl_idname = 'node.voronoi_ranto'
    bl_label = "Voronoi RANTO"
    isUniWid: bpy.props.BoolProperty(name="Uniform width", default=False)
    isOnlySelected: bpy.props.BoolProperty(name="Only selected", default=False)
    isUncollapseNodes: bpy.props.BoolProperty(name="Uncollapse nodes", default=False)
    isSelectNodes: bpy.props.BoolProperty(name="Select nodes", default=True)
    ndWidth: bpy.props.IntProperty(name="Node width", default=140, soft_min=100, soft_max=180, subtype='FACTOR')
    indentX: bpy.props.IntProperty(name="Indent x", default=40, soft_min=0, soft_max=80, subtype='FACTOR')
    indentY: bpy.props.IntProperty(name="Indent y", default=30, soft_min=0, soft_max=60, subtype='FACTOR')
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vrBoxDiscl', self):
            LeftProp(colTool, prefs,'vrIsLiveRanto')
            LeftProp(colTool, prefs,'vrIsIgnoreMuted')
            colProp = colTool.column(align=True)
            LeftProp(colProp, prefs,'vrIsRestoreMuted')
            colProp.active = not prefs.vrIsIgnoreMuted
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        self.foundGoalNd = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if nd.type=='REROUTE':
                continue
            self.foundGoalNd = li
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.foundGoalNd:
                ndTar = self.foundGoalNd.tg
                tree = context.space_data.edit_tree
                if self.isUncollapseNodes: #Запомнить и обнулить.
                    dict_ndHide = {}
                    for nd in tree.nodes:
                        dict_ndHide[nd] = nd.hide
                        nd.hide = False
                    bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=0)
                dict_nodes = RecursiveAutomaticNodeTopologyOrganization(ndTar, self.isOnlySelected, self.ndWidth, self.isUniWid, self.indentX, self.indentY)
                isUncollapseNodes = self.isUncollapseNodes
                isSelectNodes = self.isSelectNodes
                for nd in tree.nodes:
                    tgl = nd in dict_nodes
                    if isSelectNodes:
                        nd.select = tgl
                    if (isUncollapseNodes)and(not tgl): #Восстановить у незадействованных.
                        nd.hide = dict_ndHide[nd]
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalNd = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiRanto, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiRantoTool, "###_R")
dict_setKmiCats['grt'].add(VoronoiRantoTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vrBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vrIsLiveRanto:       bpy.props.BoolProperty(name="Live Ranto",            default=True)
    vrIsIgnoreMuted:     bpy.props.BoolProperty(name="Ignore muted links",    default=True)
    vrIsRestoreMuted:    bpy.props.BoolProperty(name="Restore muted links",   default=False)
list_clsToAddon.append(VoronoiRantoTool)

#===RANTO===
#Теперь RANTO интегрирован в VL. Неожиданно даже для меня.
#См. оригинал: https://github.com/ugorek000/RANTO

#Заметка: префиксы не нужны, чтобы пайками могли пользоваться всё инструменты.
#todo3 с приходом RANTO вынести пайки во вне в начало файла для всех.

dict_ndWidth = {}
dict_ndWidcol = {}
dict_listSkLinks = {}
dict_listNdSockets = {}
dict_listNdDimY = {}
##
dict_links3 = {}
dict_links2 = {}
dict_links0 = {}
dict_ndTopoWorking = {}
dict_ndMaxDeepDepth = {}
##
dict_listColNodes = {}

def StartDicts():
    dict_ndWidcol.clear()
    dict_listSkLinks.clear()
    dict_listNdSockets.clear()
    dict_listNdDimY.clear()
    dict_ndWidth.clear()
    dict_links3.clear()
    dict_links2.clear()
    dict_links0.clear()
    dict_ndTopoWorking.clear()
    dict_ndMaxDeepDepth.clear()
    dict_listColNodes.clear()

vrtSoldIsIgnoreMuted = False
vrtSoldIsRestoreMuted = False

set_vrtOmgApiNodesWidth = {'CompositorNodeBoxMask', 'CompositorNodeEllipseMask'}

vrtFeatureFixIslands = True

def GenSolderingNdWidth(kapibara):
    pass
def GenSolderingNdWidcol(kapibara):
    pass
def GenSolderingSkLinks(kapibara):
    pass
def GenSolderingNdSockets(kapibara):
    pass
def GenSolderingNdDimY(kapibara):
    pass
def UpdateSoldSkLinks():
    pass
def ParseTrueLk3(kapibara):
    pass
def ParseTrueLk2(kapibara):
    pass
def GenMarkNodesMaxDeepDepth(kapibara):
    pass
def CoreOrganization(kapibara):
    pass
def RecursiveAutomaticNodeTopologyOrganization(ndRoot, isOnlySelected=False, ndWidth=140, isUniWid=False, indentX=40, indentY=30):
    if not ndRoot: return
    DisplayMessage("RANTO", "Этот инструмент пуст ¯\_(ツ)_/¯")
    StartDicts()
    Kapibara = 'Kapibara'
    return dict_ndTopoWorking
def GenColumnedNodes(kapibara):
    pass
def FixIslands(kapibara):
    pass

#===End RANTO===

def CallbackDrawVoronoiSwapper(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkIo0:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkIo0], isLineToCursor=True, isDrawText=False)
        tgl = not not self.foundGoalSkIo1
        DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkIo0, -0.5+0.75*tgl, int(tgl))
        if tgl:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkIo1], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkIo1, -1.25, -1)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiSwapperTool(VoronoiToolDblSk):
    bl_idname = 'node.voronoi_swaper'
    bl_label = "Voronoi Swapper"
    isAddMode:      bpy.props.BoolProperty(name="Add mode",               default=False)
    isIgnoreLinked: bpy.props.BoolProperty(name="Ignore linked",          default=False)
    isCanAnyType:   bpy.props.BoolProperty(name="Can swap with any type", default=False)
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        if isBoth:
            self.foundGoalSkIo0 = None
        self.foundGoalSkIo1 = None
        callPos = context.space_data.cursor_location
        isBothSucessTgl = True
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if StencilUnCollapseNode(nd, isBoth):
                bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=0)
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            #За основу были взяты критерии от Миксера.
            if (isBoth)and(isBothSucessTgl):
                fgSkOut, fgSkIn = None, None
                for li in list_fgSksOut:
                    if li.tg.bl_idname!='NodeSocketVirtual':
                        if (not self.isIgnoreLinked)or(li.tg.is_linked):
                            fgSkOut = li
                            break
                for li in list_fgSksIn:
                    if li.tg.bl_idname!='NodeSocketVirtual':
                        if (not self.isIgnoreLinked)or(li.tg.is_linked):
                            fgSkIn = li
                            break
                #Разрешить возможность "добавлять" и для входов тоже, но только для мультиинпутов, ибо очевидное
                if (self.isAddMode)and(fgSkIn):
                    #Проверка по типу, но не по 'is_multi_input', чтобы из обычного в мультиинпут можно было добавлять.
                    if (fgSkIn.tg.bl_idname not in ('NodeSocketGeometry','NodeSocketString')):#or(not fgSkIn.tg.is_multi_input): #Без второго условия больше возможностей.
                        fgSkIn = None
                self.foundGoalSkIo0 = MinFromFgs(fgSkOut, fgSkIn)
                if (self.isIgnoreLinked)and(self.foundGoalSkIo0)and(not self.foundGoalSkIo0.tg.is_linked):
                    self.foundGoalSkIo0 = None
                    #Заметка: важно продолжать искать сокет с линком, ибо ради повышения удобства было создано isIgnoreLinked.
            isBothSucessTgl = not self.foundGoalSkIo0
            #Здесь вокруг аккумулировалось много странных проверок с None и т.п. -- результат соединения вместе многих типа высокоуровневых функций, что я понаизобретал.
            skOut0 = self.foundGoalSkIo0.tg if self.foundGoalSkIo0 else None
            if skOut0:
                for li in list_fgSksOut if skOut0.is_output else list_fgSksIn:
                    if li.tg.bl_idname=='NodeSocketVirtual':
                        continue
                    if (self.isCanAnyType)or(skOut0.type==li.tg.type)or( SkBetweenFieldsCheck(self, skOut0, li.tg) ):
                        #Последнее условие нужно для ломания цикла самокопией, чтобы при активации VST isIgnoreLinked не находил сразу два сокета.
                        if (not(self.isIgnoreLinked and li.tg.is_linked))or(li.tg==skOut0):
                            self.foundGoalSkIo1 = li
                    if self.foundGoalSkIo1: #В случае успеха прекращать поиск.
                        break
                if (self.foundGoalSkIo1)and(skOut0==self.foundGoalSkIo1.tg): #Проверка на самокопию.
                    self.foundGoalSkIo1 = None
                    break #Ломать для isCanAnyType, когда isBoth==False и сокет оказался самокопией; чтобы не находил сразу два нода.
                if not self.isCanAnyType:
                    if not(self.foundGoalSkIo1 or isBoth): #Если нет результата, продолжаем искать.
                        continue
                StencilUnCollapseNode(nd, self.foundGoalSkIo1)
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (self.foundGoalSkIo0)and(self.foundGoalSkIo1):
                skIo0 = self.foundGoalSkIo0.tg
                skIo1 = self.foundGoalSkIo1.tg
                tree = context.space_data.edit_tree
                if self.isAddMode:
                    #Просто добавить линки с первого сокета на второй. Aka объединение, добавление.
                    if skIo0.is_output:
                        for lk in skIo0.links:
                            if lk.to_node!=skIo1.node: # T 1  Чтобы линк от нода не создался сам в себя. Проверять нужно у всех и таковые не обрабатывать.
                                tree.links.new(skIo1, lk.to_socket)
                                if lk.to_socket.is_multi_input: #Без этого lk всё равно указывает на "добавленный" линк, от чего удаляется. Поэтому явная проверка для мультиинпутов.
                                    tree.links.remove(lk)
                    else: #Добавлено ради мультиинпутов.
                        for lk in skIo0.links:
                            if lk.from_node!=skIo1.node: # F 1  ^
                                tree.links.new(lk.from_socket, skIo1)
                                tree.links.remove(lk)
                else:
                    #Поменять местами все соединения у первого и у второго сокета:
                    list_memSks = []
                    if skIo0.is_output: #Проверка одинаковости is_output -- забота для NextAssignment().
                        for lk in skIo0.links:
                            if lk.to_node!=skIo1.node: # T 1  Чтобы линк от нода не создался сам в себя. Проверять нужно у всех и таковые не обрабатывать.
                                list_memSks.append(lk.to_socket)
                                tree.links.remove(lk)
                        for lk in skIo1.links:
                            if lk.to_node!=skIo0.node: # T 0  ^
                                tree.links.new(skIo0, lk.to_socket)
                                if lk.to_socket.is_multi_input: #Для мультиинпутов удалить.
                                    tree.links.remove(lk)
                        for li in list_memSks:
                            tree.links.new(skIo1, li)
                    else:
                        for lk in skIo0.links:
                            if lk.from_node!=skIo1.node: # F 1  ^
                                list_memSks.append(lk.from_socket)
                                tree.links.remove(lk)
                        for lk in skIo1.links:
                            if lk.from_node!=skIo0.node: # F 0  ^
                                tree.links.new(lk.from_socket, skIo0)
                                tree.links.remove(lk)
                        for li in list_memSks:
                            tree.links.new(li, skIo1)
                #VST VRT же без нужды, да?
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalSkIo0 = None
        self.foundGoalSkIo1 = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiSwapper, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "S##_S")
SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "##A_S", {'isAddMode':True})
SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "#CA_S", {'isAddMode':False, 'isIgnoreLinked':True})
dict_setKmiCats['oth'].add(VoronoiSwapperTool.bl_idname)

#Нужен только для наведения порядка и эстетики в дереве.
#Для тех, кого (например меня) напрягают "торчащие без дела" пустые сокеты выхода, или нулевые (чьё значение 0.0, чёрный, и т.п.) незадействованные сокеты входа.
def CallbackDrawVoronoiHider(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.isHideSocket:
        if self.foundGoalTg:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalTg], isLineToCursor=True, textSideFlip=True)
        elif prefs.dsIsDrawPoint:
            DrawWidePoint(self, prefs, cusorPos)
    else:
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalTg)
class VoronoiHiderTool(VoronoiToolSkNd):
    bl_idname = 'node.voronoi_hider'
    bl_label = "Voronoi Hider"
    isHideSocket: bpy.props.IntProperty(name="Hide mode", min=0, max=2)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vhBoxDiscl', self):
            AddHandSplitProp(colTool, prefs,'vhHideBoolSocket')
            AddHandSplitProp(colTool, prefs,'vhHideHiddenBoolSocket')
            AddHandSplitProp(colTool, prefs,'vhNeverHideGeometry')
            LeftProp(colTool, prefs,'vhIsUnhideVirtual')
            LeftProp(colTool, prefs,'vhIsToggleNodesOnDrag')
            colProp = colTool.column(align=True)
            colProp.active = prefs.vhIsToggleNodesOnDrag
    def NextAssignment(self, context, *naArgs):
        prefs = self.prefs
        if not context.space_data.edit_tree:
            return
        self.foundGoalTg = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                continue
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            self.foundGoalTg = li
            if self.isHideSocket:
                #Для режима сокетов обработка свёрнутости так же как у всех.
                list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
                def GetNotLinked(list_sks): #Выдать первого, кто не имеет линков.
                    for li in list_sks:
                        if not li.tg.links: #Выключенный сокет всё равно учитывается.
                            return li
                fgSkIn = GetNotLinked(list_fgSksIn)
                fgSkOut = GetNotLinked(list_fgSksOut)
                if self.isHideSocket==1:
                    self.foundGoalTg = MinFromFgs(fgSkOut, fgSkIn)
                else:
                    self.foundGoalTg = fgSkIn
                if StencilUnCollapseNode(nd, self.foundGoalTg):
                    StencilReNext(self, context) #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.
            else:
                #Для режима нод нет разницы, раскрывать все подряд под курсором, или нет.
                if prefs.vhIsToggleNodesOnDrag:
                    if self.firstResult is None:
                        #Если активация для нода ничего не изменила, то для остальных хочется иметь сокрытие, а не раскрытие. Но текущая концепция не позволяет,
                        # информации об этом тупо нет. Поэтому реализовал это точечно вовне (здесь), а не модификацией самой реализации.
                        LGetVisSide = lambda a: [sk for sk in a if sk.enabled and not sk.hide]
                        list_visibleSks = [LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]
                        self.firstResult = HideFromNode(self, prefs, nd, True)
                        HideFromNode(self, prefs, nd, self.firstResult, True) #Заметка: изменить для нода (для проверки ниже), но не трогать 'self.firstResult'.
                        if list_visibleSks==[LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]:
                            self.firstResult = True
                    HideFromNode(self, prefs, nd, self.firstResult, True)
                    #См. в вики, почему isReDrawAfterChange опция была удалена.
                    #todo1 Единственное возможное решение, так это сделать изменение нода после отрисовки одного кадра.
                    # Т.е. цепляться к новому ноду на один кадр, а потом уже обработать его сразу с поиском нового нода и рисовки к нему (как для примера в вики).
            break
    def modal(self, context, event):
        prefs = self.prefs
        if StencilMouseNext(self, context, event):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.foundGoalTg:
                match self.isHideSocket:
                    case 0: #Обработка нода.
                        if not prefs.vhIsToggleNodesOnDrag:
                            #Во время сокрытия сокета нужно иметь информацию обо всех, поэтому выполняется дважды. В первый заход собирается, во второй выполняется.
                            HideFromNode(self, prefs, self.foundGoalTg.tg, HideFromNode(self, prefs, self.foundGoalTg.tg, True), True)
                    case 1: #Сокрытие сокета.
                        self.foundGoalTg.tg.hide = True
                    case 2: #Переключение видимости значения сокета.
                        self.foundGoalTg.tg.hide_value = not self.foundGoalTg.tg.hide_value
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalTg = []
        self.firstResult = None #Получить действие у первого нода "свернуть" или "развернуть", а потом транслировать его на все остальные попавшиеся.
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiHider)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "S##_E", {'isHideSocket':1})
SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "##A_E", {'isHideSocket':2})
SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "#C#_E", {'isHideSocket':0})
dict_setKmiCats['oth'].add(VoronoiHiderTool.bl_idname)

list_itemsProcBoolSocket = [('ALWAYS',"Always",""), ('IF_FALSE',"If false",""), ('NEVER',"Never",""), ('IF_TRUE',"If true","")]

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vhBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vhHideBoolSocket:       bpy.props.EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=list_itemsProcBoolSocket)
    vhHideHiddenBoolSocket: bpy.props.EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=list_itemsProcBoolSocket)
    vhNeverHideGeometry:    bpy.props.EnumProperty(name="Never hide geometry input socket", default='FALSE',    items=( ('FALSE',"False",""), ('ONLY_FIRST',"Only first",""), ('TRUE',"True","") ))
    vhIsUnhideVirtual:      bpy.props.BoolProperty(name="Unhide virtual",                   default=False)
    vhIsToggleNodesOnDrag:  bpy.props.BoolProperty(name="Toggle nodes on drag",             default=True)
list_clsToAddon.append(VoronoiHiderTool)

def HideFromNode(self, prefs, ndTarget, lastResult, isCanDo=False): #Изначально лично моя утилита, была создана ещё до VL.
    set_equestrianHideVirtual = {'GROUP_INPUT','SIMULATION_INPUT','SIMULATION_OUTPUT','REPEAT_INPUT','REPEAT_OUTPUT'}
    scoGeoSks = 0 #Для CheckSkZeroDefaultValue().
    def CheckSkZeroDefaultValue(sk): #Shader и Virtual всегда True, Geometry от настроек аддона.
        match sk.type: #Отсортированы в порядке убывания сложности.
            case 'GEOMETRY':
                match prefs.vhNeverHideGeometry: #Задумывалось и для out тоже, но как-то леновато, а ещё `GeometryNodeBoundBox`, так что...
                    case 'FALSE': return True
                    case 'TRUE': return False
                    case 'ONLY_FIRST':
                        nonlocal scoGeoSks
                        scoGeoSks += 1
                        return scoGeoSks!=1
            case 'VALUE':
                if (GetSkLabelName(sk) in {'Alpha', 'Factor'})and(sk.default_value==1): #Для некоторых float сокетов тоже было бы неплохо иметь точечную проверку.
                    return True #todo1 изобрести как-то как-нибудь список настраиваемых точечных сокрытий.
                return sk.default_value==0
            case 'VECTOR':
                if (GetSkLabelName(sk)=='Scale')and(sk.default_value[0]==1)and(sk.default_value[1]==1)and(sk.default_value[2]==1):
                    return True #Меня переодически напрягал 'GeometryNodeTransform', и в один прекрасной момент накопилось..
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #Заметка: `sk.default_value==(0,0,0)` не прокатит.
            case 'BOOLEAN':
                if not sk.hide_value: #Лень паять, всё обрабатывается в прямом виде.
                    match prefs.vhHideBoolSocket: #Заметка: `.self` всего один, но зато каждый NextAssignment() инструмента, причём по несколько за раз. Так что маршрут self(prefs)'ов имел смысл.
                        case 'ALWAYS': return True
                        case 'NEVER': return False
                        case 'IF_TRUE': return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
                else:
                    match prefs.vhHideHiddenBoolSocket:
                        case 'ALWAYS': return True
                        case 'NEVER': return False
                        case 'IF_TRUE': return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
            case 'RGBA':
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #4-й компонент игнорируются, может быть любым.
            case 'INT':
                return sk.default_value==0
            case 'STRING'|'OBJECT'|'MATERIAL'|'COLLECTION'|'TEXTURE'|'IMAGE': #Заметка: STRING не такой же, как и остальные, но имеет одинаковую обработку.
                return not sk.default_value
            case _:
                return True
    if lastResult: #Результат предыдущего анализа, есть ли сокеты чьё состояние изменилось бы. Нужно для 'isCanDo'.
        def CheckAndDoForIo(puts, LMainCheck):
            success = False
            for sk in puts:
                if (sk.enabled)and(not sk.hide)and(not sk.links)and(LMainCheck(sk)): #Ядро сокрытия находится здесь, в первых двух проверках.
                    success |= not sk.hide #Здесь success означает будет ли оно скрыто.
                    if isCanDo:
                        sk.hide = True
            return success
        #Если виртуальные были созданы вручную, то не скрывать их. Потому что. Но если входов групп больше одного, то всё равно скрывать.
        #Изначальный смысл LVirtual -- "LCheckOver" -- проверка "над", точечные дополнительные условия. Но в ней скопились только для виртуальных, поэтому переназвал.
        isMoreNgInputs = False if ndTarget.type!='GROUP_INPUT' else ( length([True for nd in ndTarget.id_data.nodes if nd.type=='GROUP_INPUT'])>1 )
        LVirtual = lambda sk: not( (sk.bl_idname=='NodeSocketVirtual')and #Смысл этой Labmda -- точечное не-сокрытие для тех, которые виртуальные,
                                   (sk.node.type in {'GROUP_INPUT','GROUP_OUTPUT'})and # у io-всадников,
                                   (sk!=(sk.node.outputs if sk.is_output else sk.node.inputs)[-1])and # и не последние (то ради чего),
                                   (not isMoreNgInputs) ) # и GROUP_INPUT в дереве всего один.
        #Ядро в трёх строчках ниже:
        success = CheckAndDoForIo(ndTarget.inputs, lambda sk: CheckSkZeroDefaultValue(sk)and(LVirtual(sk)) ) #Для входов мейнстримная проверка их значений, и дополнительно виртуальные.
        if [True for sk in ndTarget.outputs if (sk.enabled)and(sk.links)]: #Если хотя бы один сокет подсоединён вовне
            success |= CheckAndDoForIo(ndTarget.outputs, lambda sk: LVirtual(sk) ) #Для выводов актуально только проверка виртуальных, если их нодом оказался всадник.
        else:
            #Всё равно переключать последний виртуальный, даже если нет соединений вовне.
            if ndTarget.type in set_equestrianHideVirtual: #Заметка: 'GROUP_OUTPUT' бесполезен, у него всё прячется по значению.
                if ndTarget.outputs: #Вместо for, чтобы читать из последнего.
                    sk = ndTarget.outputs[-1]
                    if sk.bl_idname=='NodeSocketVirtual':
                        success |= not sk.hide #Так же, как и в CheckAndDoForIo().
                        if isCanDo:
                            sk.hide = True
        return success #Урожай от двух CheckAndDoForIo() изнутри.
    elif isCanDo: #Иначе раскрыть всё.
        success = False
        for puts in [ndTarget.inputs, ndTarget.outputs]:
            for sk in puts:
                success |= sk.hide #Здесь success означает будет ли оно раскрыто.
                sk.hide = (sk.bl_idname=='NodeSocketVirtual')and(not prefs.vhIsUnhideVirtual)
        return success

def VmltCompareSkLabelName(sk1, sk2, isIgnoreCase=False):
    if isIgnoreCase:
        return GetSkLabelName(sk1).lower()==GetSkLabelName(sk2).lower()
    else:
        return GetSkLabelName(sk1)==GetSkLabelName(sk2)

#"Массовый линкер" -- как линкер, только много за раз (ваш кэп).
#См. вики на гитхабе, чтобы посмотреть 4 примера использования массового линкера. Дайте мне знать, если обнаружите ещё одно необычное применение этому инструменту.

def CallbackDrawVoronoiMassLinker(self, context):
    #Здесь нарушается местная концепция чтения-записи, и CallbackDraw ищет и записывает найденные сокеты вместо того, чтобы просто читать и рисовать. Полагаю, так инструмент реализовывать проще.
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    uiScale = self.uiScale
    if not self.ndGoalOut:
        DrawDoubleNone(self, prefs, context)
    elif (self.ndGoalOut)and(not self.ndGoalIn):
        list_fgSksOut = GetNearestSockets(self.ndGoalOut, cusorPos, uiScale)[1]
        if not list_fgSksOut:
            DrawDoubleNone(self, prefs, context)
        for li in list_fgSksOut: #Не известно, к кому это будет подсоединено и к кому получится => рисовать от всех сокетов.
            DrawToolOftenStencil(self, prefs, cusorPos, [li], isLineToCursor=prefs.dsIsAlwaysLine, isDrawText=False) #Всем к курсору!
    else:
        self.list_equalFgSks = [] #Очищать каждый раз.
        list_fgSksOut = GetNearestSockets(self.ndGoalOut, cusorPos, uiScale)[1]
        list_fgSksIn =  GetNearestSockets(self.ndGoalIn,  cusorPos, uiScale)[0]
        for liSko in list_fgSksOut:
            for liSki in list_fgSksIn:
                #Т.к. "массовый" -- критерии приходится автоматизировать и сделать их едиными для всех.
                if VmltCompareSkLabelName(liSko.tg, liSki.tg, prefs.vmlIgnoreCase): #Соединяться только с одинаковыми по именам сокетами.
                    tgl = False
                    if self.isIgnoreExistingLinks: #Если соединяться без разбору, то исключить уже имеющиеся "желанные" связи. Нужно только для эстетики.
                        for lk in liSki.tg.links:
                            #Проверка is_linked нужна, чтобы можно было включить выключенные линки, перезаменив их.
                            if (lk.from_socket.is_linked)and(lk.from_socket==liSko.tg):
                                tgl = True
                        tgl = not tgl
                    else: #Иначе не трогать уже соединённых.
                        tgl = not liSki.tg.links
                    if tgl:
                        self.list_equalFgSks.append( (liSko,liSki) )
        if not self.list_equalFgSks:
            DrawWidePoint(self, prefs, cusorPos)
        for li in self.list_equalFgSks:
            #Т.к. поиск по именам, рисоваться здесь и подсоединяться ниже, возможно из двух (и больше) сокетов в один и тот же одновременно. Типа "конфликт" одинаковых имён.
            DrawToolOftenStencil(self, prefs, cusorPos, [li[0],li[1]], isDrawText=False)
class VoronoiMassLinkerTool(VoronoiTool): #"Малыш котопёс", не ноды, не сокеты.
    bl_idname = 'node.voronoi_mass_linker'
    bl_label = "Voronoi MassLinker" #Единственный, у кого нет пробела. Потому что слишком котопёсный))00)0
    # А если серьёзно, то он действительно самый странный. Пародирует VLT с его dsIsAlwaysLine. SocketArea стакаются, если из нескольких в одного. Пишет в функции рисования...
    # А ещё именно он есть/будет на превью аддона, ибо обладает самой большой степенью визуальности из всех инструментов (причем без верхнего предела).
    isIgnoreExistingLinks: bpy.props.BoolProperty(name="Ignore existing links", default=False)
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vmlBoxDiscl', self):
            colProp = colTool.column(align=True)
            LeftProp(colTool, prefs,'vmlIgnoreCase')
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            StencilUnCollapseNode(nd, isBoth)
            #Помимо свёрнутых также игнорируются и рероуты, потому что у них инпуты всегда одни и с одинаковыми названиями.
            if nd.type=='REROUTE':
                continue
            self.ndGoalIn = nd
            if isBoth:
                self.ndGoalOut = nd #Здесь нод-вывод устанавливается один раз.
            if self.ndGoalOut==self.ndGoalIn: #Проверка на самокопию.
                self.ndGoalIn = None #Здесь нод-вход обнуляется каждый раз в случае неудачи.
            #Заметка: первое нахождение ndGoalIn, list_equalFgSks == [].
            if StencilUnCollapseNode(nd, self.ndGoalIn):
                StencilReNext(self, context, False)
            break
    def modal(self, context, event):
        #Заметка: ndGoalIn обнулится через самокопию если isCanReOut (см. isCanReOut).
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (self.ndGoalOut)and(self.ndGoalIn):
                tree = context.space_data.edit_tree
                #for li in self.list_equalFgSks: tree.links.new(li[0].tg, li[1].tg) #Соединить всех!
                #Если выходы нода и входы другого нода имеют в сумме 4 одинаковых сокета по названию, то происходит не ожидаемое от инструмента поведение.
                #Поэтому соединяется только один линк на входной сокет (мультиинпуты не в счёт).
                set_alreadyDone = set()
                list_skipToEndEq = []
                list_skipToEndSk = []
                for li in self.list_equalFgSks:
                    sko = li[0].tg
                    ski = li[1].tg
                    if ski in set_alreadyDone:
                        continue
                    if sko in list_skipToEndSk: #Заметка: достаточно и линейного чтения, но пока оставлю так, чтоб наверняка.
                        list_skipToEndEq.append(li)
                        continue
                    tree.links.new(sko, ski) #Заметка: наверное лучше оставить безопасное "сырое" соединение, учитывая массовость соединения и неограниченность количества.
                    VlrtRememberLastSockets(sko, ski) #Заметка: эта и далее -- "последнее всегда последнее", эффективно-ниже проверками уже не опуститься; ну или по крайней мере на моём уровне знаний.
                    if not ski.is_multi_input: #Мультиинпуты бездонны!
                        set_alreadyDone.add(ski)
                    list_skipToEndSk.append(sko)
                #Далее обрабатываются пропущенные на предыдущем цикле.
                for li in list_skipToEndEq:
                    sko = li[0].tg
                    ski = li[1].tg
                    if ski in set_alreadyDone:
                        continue
                    set_alreadyDone.add(ski)
                    tree.links.new(sko, ski)
                    VlrtRememberLastSockets(sko, ski)
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.ndGoalOut = None
        self.ndGoalIn = None
        self.list_equalFgSks = [] #Однажды необычным странным образом, modal() не смог найти этот атрибут в себе. Поэтому продублировал сюда.
        self.isDrawDoubleNone = True
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiMassLinker, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiMassLinkerTool, "SCA_LEFTMOUSE")
SmartAddToRegAndAddToKmiDefs(VoronoiMassLinkerTool, "SCA_RIGHTMOUSE", {'isIgnoreExistingLinks':True})
dict_setKmiCats['oth'].add(VoronoiMassLinkerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vmlBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vmlIgnoreCase: bpy.props.BoolProperty(name="Ignore case", default=True)
list_clsToAddon.append(VoronoiMassLinkerTool)

class VestEnumSelectorData:
    list_enumProps = [] #Для пайки, и проверка перед вызовом, есть ли вообще что.
    nd = None
    boxScale = 1.0 #Если забыть установить, то хотя бы коробка не сколлапсируется в ноль.
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False
vestData = VestEnumSelectorData()

set_vestEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput', 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}

def VestGetListOfNdEnums(nd):
    return [li for li in nd.rna_type.properties if not(li.is_readonly or li.is_registered)and(li.type=='ENUM')]

def CallbackDrawVoronoiEnumSelector(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if colNode:=DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalNd, isCanText=not prefs.vesIsDrawEnumNames):
        sco = -0.5
        col = colNode if prefs.dsIsColoredText else GetUniformColVec(prefs)
        for li in VestGetListOfNdEnums(self.foundGoalNd.tg):
            DrawText(self, prefs, cusorPos, (prefs.dsDistFromCursor, sco), TranslateIface(li.name), col)
            sco -= 1.5
def CallbackDrawVoronoiEnumSelectorNode(self, context): #Тут вся тусовка про... о нет.
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    nd = self.foundGoalNd.tg
    colNd = PowerArr4ToVec(prefs.dsNodeColor) #ToNodeCol и NodeCol -- это разное; второй опции нет, поэтому читать с первой.
    col = Vector(colNd.x, colNd.y, colNd.z, prefs.dsSocketAreaAlpha) #Vector не обязателен.
    loc = RecrGetNodeFinalLoc(nd)
    hh = nd.dimensions[1]/2-10 if nd.hide else 0 #Всё равно криво рисуется. Ну и хрен с ними.
    #Вычленёнка-алерт, DrawWidePoint().
    loc0 = VecWorldToRegScale(loc, self)
    loc1 = Vector(loc.x+6*1000, loc.y)
    sz = (VecWorldToRegScale(loc1, self)[0]-loc0[0])/1000
    #Вычленёнка-алерт, DrawSocketArea().
    pos1 = VecWorldToRegScale( Vector(loc.x, loc.y+1+hh), self ) #'+1' потому что не стыкуется ровно и наслаивается тонкой полоской. Ниже тоже.
    pos2 = VecWorldToRegScale( Vector(loc.x+nd.dimensions[0]+1, loc.y-nd.dimensions[1]+hh), self ) #Офигеть, 'nd.width' и 'nd.dimensions[0]' для свёрнутого нода -- оказывается разное.
    pos3 = Vector(pos1.x, pos2.y)
    pos4 = Vector(pos2.x, pos1.y)
    DrawRectangle(self, pos1+Vector(-sz, sz), pos3+Vector(0, -sz), col)
    DrawRectangle(self, pos4+Vector(sz, sz), pos2+Vector(0, -sz), col)
    DrawRectangle(self, pos1+Vector(0, sz), pos4, col)
    DrawRectangle(self, pos3+Vector(0, -sz), pos2, col)
class VoronoiEnumSelectorTool(VoronoiToolNd):
    bl_idname = 'node.voronoi_enum_selector'
    bl_label = "Voronoi Enum Selector"
    isToggleOptions: bpy.props.BoolProperty(name="Toggle node options mode", default=False)
    isPieChoice:     bpy.props.BoolProperty(name="Pie choice",               default=False)
    isSelectNode:    bpy.props.BoolProperty(name="Select target node",       default=True)
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vesBoxDiscl', self):
            LeftProp(colTool, prefs,'vesIsToggleNodesOnDrag')
            colProp = colTool.column(align=True)
            colProp.active = prefs.vesIsToggleNodesOnDrag
            AddHandSplitProp(colTool, prefs,'vesBoxScale')
            AddHandSplitProp(colTool, prefs,'vesDisplayLabels')
            AddHandSplitProp(colTool, prefs,'vesDarkStyle')
            LeftProp(colTool, prefs,'vesIsInstantActivation')
            colToolBox = colTool.column(align=True)
            #colToolBox.active = not prefs.vesIsInstantActivation #Я забыл что у VEST есть isToggleOptions, который рисует к нодам.
            AddHandSplitProp(colToolBox, prefs,'vesIsDrawEnumNames')
            colProp = colToolBox.column(align=True)
            colProp.active = not prefs.vesIsDrawEnumNames
    def NextAssignment(self, context, *naArgs):
        if not context.space_data.edit_tree:
            return
        self.foundGoalNd = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale, skipPoorNodes=False):
            nd = li.tg
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            if nd.bl_idname in set_vestEquestrianPortalBlids: #Игнорировать всех всадников.
                continue
            if nd.hide: #У свёрнутых нод результат переключения не увидеть, поэтому игнорировать.
                continue
            if self.isToggleOptions:
                self.foundGoalNd = li
                #Так же, как и в VHT:
                if self.prefs.vesIsToggleNodesOnDrag:
                    if self.firstResult is None:
                        self.firstResult = VestToggleOptionsFromNode(nd, True)
                    VestToggleOptionsFromNode(nd, self.firstResult, True)
                break
            else:
                #Почему бы не игнорировать ноды без енум свойств?.
                if VestGetListOfNdEnums(nd):
                    self.foundGoalNd = li
                    break
    def DoActivation(self, prefs): #Для моментальной активации, сразу из invoke().
        if self.foundGoalNd:
            vestData.list_enumProps = VestGetListOfNdEnums(self.foundGoalNd.tg)
            #Если ничего нет, то вызов коробки всё равно обрабатывается, словно она есть, и от чего повторный вызов инструмента не работает без движения курсора.
            if vestData.list_enumProps: #Поэтому если пусто, то ничего не делаем.
                vestData.nd = self.foundGoalNd.tg
                vestData.boxScale = prefs.vesBoxScale
                vestData.isDarkStyle = prefs.vesDarkStyle
                vestData.isDisplayLabels = prefs.vesDisplayLabels
                vestData.isPieChoice = self.isPieChoice
                if self.isSelectNode:
                    NdSelectAndActive(vestData.nd)
                if self.isPieChoice:
                    bpy.ops.wm.call_menu_pie(name=VestPieBox.bl_idname)
                else:
                    bpy.ops.node.voronoi_enum_selector_box('INVOKE_DEFAULT')
                return True #Для modal(), чтобы вернуть успех.
    def modal(self, context, event):
        prefs = self.prefs
        if StencilMouseNext(self, context, event):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.isToggleOptions:
                if not prefs.vesIsToggleNodesOnDrag: #И снова, так же как и в VHT.
                    VestToggleOptionsFromNode(self.foundGoalNd.tg, VestToggleOptionsFromNode(self.foundGoalNd.tg, True), True)
                return {'FINISHED'}
            else:
                if (not prefs.vesIsInstantActivation)and(VoronoiEnumSelectorTool.DoActivation(self, prefs)):
                    return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        self.foundGoalNd = None
        if (prefs.vesIsInstantActivation)and(not self.isToggleOptions):
            #Заметка: коробка может полностью закрыть нод вместе с линией к нему.
            VoronoiEnumSelectorTool.NextAssignment(self, context)
            VoronoiEnumSelectorTool.DoActivation(self, prefs)
            #Вычленёнка-алерт, StencilToolWorkPrepare().
            self.whereActivated = context.space_data
            self.handleNode = bpy.types.SpaceNodeEditor.draw_handler_add(CallbackDrawVoronoiEnumSelectorNode, (self,context), 'WINDOW', 'POST_PIXEL')
            #Гениально! Оно работает. Спасибо Blender'у, что не перерисовывает каждый раз, а только по запросу.
            #Но если isSelectNode, то рамка не остаётся. Ну.. и так сойдёт.
            bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=0)
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handleNode, 'WINDOW')
            return {'FINISHED'} #Рисуется, но не позволяет использовать пирог при отжатии. Поэтому не нужно активировать modal() далее. Также см. vesIsInstantActivation в modal().
        self.firstResult = None #В идеале тоже перед выше, но не обязательно, см. топологию isToggleOptions.
        StencilToolWorkPrepare(self, prefs, context, CallbackDrawVoronoiEnumSelector)
        return {'RUNNING_MODAL'}

#Изначально хотел 'V_Sca', но слишком далеко тянуться пальцем до V. И вообще, учитывая причину создания этого инструмента, нужно минимизировать сложность вызова.
SmartAddToRegAndAddToKmiDefs(VoronoiEnumSelectorTool, "###_F", {'isPieChoice':True})
SmartAddToRegAndAddToKmiDefs(VoronoiEnumSelectorTool, "S##_F")
SmartAddToRegAndAddToKmiDefs(VoronoiEnumSelectorTool, "##A_F", {'isToggleOptions':True})
dict_setKmiCats['oth'].add(VoronoiEnumSelectorTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vesBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vesIsToggleNodesOnDrag: bpy.props.BoolProperty( name="Toggle nodes on drag",  default=True)
    vesIsInstantActivation: bpy.props.BoolProperty( name="Instant activation",    default=True)
    vesIsDrawEnumNames:     bpy.props.BoolProperty( name="Draw enum names",       default=False)
    vesBoxScale:            bpy.props.FloatProperty(name="Box scale",             default=1.5, min=1, max=2, subtype="FACTOR")
    vesDisplayLabels:       bpy.props.BoolProperty( name="Display enum names",    default=True)
    vesDarkStyle:           bpy.props.BoolProperty( name="Dark style",            default=False)
list_clsToAddon.append(VoronoiEnumSelectorTool)

def VestAddEnumSelectorBox(where, lyDomain=None):
    colMain = where.column()
    colDomain = lyDomain.column() if lyDomain else None
    nd = vestData.nd
    #Нод математики имеет высокоуровневое разбиение на категории для .prop(), но как показать их вручную простым перечислением я не знаю. И вообще, VQMT.
    #Игнорировать их не стал, пусть обрабатываются как есть. И с ними даже очень удобно выбирать операцию векторной математики (обычная не влезает).
    sco = 0
    #Домен всегда первым. Например, StoreNamedAttribute и FieldAtIndex имеют одинаковые енумы, но в разном порядке; интересно почему?.
    for li in sorted(vestData.list_enumProps, key=lambda a:a.identifier!='domain'):
        if (sco)and(colWhere!=colDomain):
            colProp.separator()
        colWhere = (colDomain if (lyDomain)and(li.identifier=='domain') else colMain)
        colProp = colWhere.column(align=True)
        if vestData.isDisplayLabels:
            rowLabel = colProp.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(text=li.name)
            #rowLabel.active = not vestData.isPieChoice #Для пирога рамка прозрачная, от чего текст может сливаться с яркими нодами на фоне. Так что выключено.
            rowLabel.active = not(vestData.isDarkStyle and vestData.isPieChoice) #Но для тёмного пирога всё-таки отобразить их тёмными.
        elif sco:
            colProp.separator()
        colEnum = colProp.column(align=True)
        colEnum.scale_y = vestData.boxScale
        if vestData.isDarkStyle:
            colEnum.prop_tabs_enum(nd, li.identifier)
        else:
            colEnum.prop(nd, li.identifier, expand=True)
        sco += 1
    if not sco: #Для отладки.
        colMain.label(text="`list_enums` is empty") #Во всю ширину не влезает.
    #В самой первой задумке я неправильно назвал этот инструмент -- "Prop Selector". Нужно придумать как отличить общие свойства нода от тех, которые рисуются у него в опциях.
    #Повезло, что у каждого нода енумов нет разных...
    #for li in [li for li in nd.rna_type.properties if not(li.is_readonly or li.is_registered)and(li.type!='ENUM')]: colMain.prop(nd, li.identifier)
class VestOpBox(VoronoiOp):
    bl_idname = 'node.voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def execute(self, context): #Для draw() ниже, иначе не отобразится.
        pass
    def draw(self, context):
        VestAddEnumSelectorBox(self.layout)
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=int(128*vestData.boxScale))
class VestPieBox(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def draw(self, context):
        pie = self.layout.menu_pie()
        def GetCol(where, tgl=True):
            col = (where.box() if tgl else where) . column()
            col.ui_units_x = 7*((vestData.boxScale-1)/2+1)
            return col
        colDom = GetCol(pie, [True for li in vestData.list_enumProps if li.identifier=='domain'])
        colAll = GetCol(pie, [True for li in vestData.list_enumProps if li.identifier!='domain'])
        VestAddEnumSelectorBox(colAll, colDom)

list_classes += [VestOpBox, VestPieBox]

def VestToggleOptionsFromNode(nd, lastResult, isCanDo=False): #Паттерн логики скопирован с VHT HideFromNode()'a.
    if lastResult:
        success = nd.show_options
        if isCanDo:
            nd.show_options = False
        return success
    elif isCanDo:
        success = not nd.show_options
        nd.show_options = True
        return success

#См.: VlrtLinkRepeatingData, VlrtRememberLastSockets() и NewLinkAndRemember().

def VlrtCompareSkLabelName(sk1, sk2, isIgnoreCase=False):
    if isIgnoreCase:
        return GetSkLabelName(sk1).lower()==GetSkLabelName(sk2).lower()
    else:
        return GetSkLabelName(sk1)==GetSkLabelName(sk2)

def CallbackDrawVoronoiLinkRepeating(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.isAutoRepeatMode:
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalTg)
    else:
        if self.foundGoalTg:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalTg])
        else:
            DrawWidePoint(self, prefs, cusorPos)
class VoronoiLinkRepeatingTool(VoronoiToolSkNd): #Вынесено в отдельный инструмент, чтобы не осквернять святая святых спагетти-кодом (изначально был только для VLT).
    bl_idname = 'node.voronoi_link_repeating'
    bl_label = "Voronoi Link Repeating"
    isAutoRepeatMode: bpy.props.BoolProperty(name="Is auto repeat mode", default=False)
    isFromOut:        bpy.props.BoolProperty(name="From out",            default=False)
    def NextAssignment(self, context, *naArgs):
        if not context.space_data.edit_tree:
            return
        lSkO = vlrtData.lastSk1
        if (not lSkO)or(lSkO.id_data!=context.space_data.edit_tree): #Перенесено в начало, чтобы не делать бесполезные вычисления.
            return
        self.foundGoalTg = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if nd==lSkO.node: #Исключить само-нод.
                break# continue
            if self.isAutoRepeatMode:
                lSkI = vlrtData.lastSk2
                if (self.isFromOut)or(lSkI):
                    if nd.inputs:
                        self.foundGoalTg = li
                    for sk in nd.inputs:
                        if VlrtCompareSkLabelName(sk, lSkO if self.isFromOut else lSkI):
                            if (sk.enabled)and(not sk.hide):
                                context.space_data.edit_tree.links.new(lSkO, sk) #Заметка: не высокоуровневый; зачем isAutoRepeatMode'у интерфейсы?.
            else:
                list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
                if vlrtData.lastSk1:
                    for li in list_fgSksIn:
                        can = True
                        for lk in li.tg.links:
                            if lk.from_socket==lSkO:
                                can = False
                        if can:
                            self.foundGoalTg = li
                            break
                if StencilUnCollapseNode(nd, self.foundGoalTg):
                    StencilReNext(self, context)
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.foundGoalTg:
                if not self.isAutoRepeatMode:
                    #Здесь нет нужды проверять на одинаковость дерева сокетов, проверка на это уже есть в NextAssignment().
                    #Также нет нужды проверять существование lastSk1, см. его топологию в NextAssignment().
                    # if (vlrtData.lastSk1)and(vlrtData.lastSk1.id_data!=self.foundGoalTg.tg.id_data): return {'CANCELLED'}
                    #Заметка: нет нужды проверять существование дерева, потому что если прицепившийся сокет тут существует, то уже где-то.
                    DoLinkHH(vlrtData.lastSk1, self.foundGoalTg.tg)
                    VlrtRememberLastSockets(vlrtData.lastSk1, self.foundGoalTg.tg) #Потому что. И вообще.. "саморекурсия"?.
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalTg = None
        #Проверить актуальность сокетов:
        tree = vlrtData.tree
        if not(tree is None):
            try: #Узнать, существует ли дерево.
                getattr(tree, 'rna_type') #hasattr() всё равно выдаёт ошибку.
            except:
                vlrtData.lastSk1 = None
                vlrtData.lastSk2 = None
            try:
                #Оказывается, Ctrl Z делает ссылку на tree `ReferenceError: StructRNA of type ShaderNodeTree has been removed`.
                #Пока у меня нет идей, как сохранить гарантированную "долгоиграющую" ссылку. Лепить vlrtData.lastNd1name в свойства каждого дерева не очень хочется.
                #Поэтому обработка через try, если неудача -- забыть всё текущее.
                nd = tree.nodes.get(vlrtData.lastNd1name)
                if (not nd)or(nd.as_pointer()!=vlrtData.lastNd1Id):
                    vlrtData.lastSk1 = None
                nd = tree.nodes.get(vlrtData.lastNd2name)
                if (not nd)or(nd.as_pointer()!=vlrtData.lastNd2Id):
                    vlrtData.lastSk2 = None
                #Можно было бы хранить все по именам, но тогда в разных деревьях могут оказаться одинаковые ноды и сокеты, благодаря чему будет не ожидаемое поведение от инструмента.
            except:
                vlrtData.tree = None
                #Заметка: остальные у vlrtData не удаляются, потому что топология 'vlrtData.tree' перекрывает.
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiLinkRepeating)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiLinkRepeatingTool, "###_V")
SmartAddToRegAndAddToKmiDefs(VoronoiLinkRepeatingTool, "S##_V", {'isAutoRepeatMode':True})
SmartAddToRegAndAddToKmiDefs(VoronoiLinkRepeatingTool, "##A_V", {'isAutoRepeatMode':True, 'isFromOut':True})
dict_setKmiCats['oth'].add(VoronoiLinkRepeatingTool.bl_idname)

set_vqdtSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}
set_vqdtSkTypeArrFields = {'VECTOR', 'RGBA', 'ROTATION'}

dict_vqdtQuickDimensionsMain = {
        'ShaderNodeTree':    {'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('ShaderNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ','ShaderNodeCombineColor'),
                              'INT':      ('ShaderNodeCombineXYZ',)},
        'GeometryNodeTree':  {'VECTOR':   ('ShaderNodeSeparateXYZ',),
                              'RGBA':     ('FunctionNodeSeparateColor',),
                              'VALUE':    ('ShaderNodeCombineXYZ','FunctionNodeCombineColor','FunctionNodeQuaternionToRotation'),
                              'INT':      ('ShaderNodeCombineXYZ',),
                              'BOOLEAN':  ('ShaderNodeCombineXYZ',),
                              'ROTATION': ('FunctionNodeRotationToQuaternion',),
                              'GEOMETRY': ('GeometryNodeSeparateComponents',)}, #Зато одинаковый по смыслу. Воспринимать как мини-рофл.
        'CompositorNodeTree':{'VECTOR':   ('CompositorNodeSeparateXYZ',),
                              'RGBA':     ('CompositorNodeSeparateColor',),
                              'VALUE':    ('CompositorNodeCombineXYZ','CompositorNodeCombineColor'),
                              'INT':      ('CompositorNodeCombineXYZ',)},
        'TextureNodeTree':   {'VECTOR':   ('TextureNodeSeparateColor',),
                              'RGBA':     ('TextureNodeSeparateColor',),
                              'VALUE':    ('TextureNodeCombineColor',''), #Нет обработок отсутствия второго, поэтому пусто; см. |2|.
                              'INT':      ('TextureNodeCombineColor',)}}

def VqdtGetListOfNdEnums(nd):
    return [li for li in nd.rna_type.properties if not(li.is_readonly or li.is_registered)and(li.type=='ENUM')]

def CallbackDrawVoronoiQuickDimensions(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkOut0:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut0], isLineToCursor=True, isDrawText=False)
        tgl = not not self.foundGoalSkOut1
        DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut0, -0.5+0.75*tgl, int(tgl))
        if tgl:
            DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkOut1], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkOut1, -1.25, -1)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiQuickDimensionsTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_quick_dimensions'
    bl_label = "Voronoi Quick Dimensions"
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        if isBoth:
            self.foundGoalSkOut0 = None
        self.foundGoalSkOut1 = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)[1]
            if not list_fgSksOut:
                continue
            if isBoth:
                for li in list_fgSksOut:
                    if (li.tg.type in set_vqdtSkTypeFields)or(li.tg.type=='GEOMETRY'):
                        self.foundGoalSkOut0 = li
                        break
                StencilUnCollapseNode(nd, self.foundGoalSkOut0)
                break
            StencilUnCollapseNode(nd, self.foundGoalSkOut1)
            skOut0 = self.foundGoalSkOut0.tg if self.foundGoalSkOut0 else None
            if skOut0:
                if skOut0.type not in {'VALUE','INT','BOOLEAN'}:
                    break
                for li in list_fgSksOut:
                    if skOut0.type==li.tg.type:
                            self.foundGoalSkOut1 = li
                    if self.foundGoalSkOut1:
                        break
                if (self.foundGoalSkOut1)and(skOut0==self.foundGoalSkOut1.tg):
                    self.foundGoalSkOut1 = None
                    break
            if self.foundGoalSkOut1:
                break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.foundGoalSkOut0:
                skOut0 = self.foundGoalSkOut0.tg
                tree = context.space_data.edit_tree
                dict_qDM = dict_vqdtQuickDimensionsMain.get(tree.bl_idname, None)
                if not dict_qDM:
                    return {'CANCELLED'}
                isOutNdCol = skOut0.node.bl_idname==dict_qDM['RGBA'][0] #Заметка: нод разделения; на выходе всегда флоаты.
                isGeoTree = tree.bl_idname=='GeometryNodeTree'
                isOutNdQuat = (isGeoTree)and(skOut0.node.bl_idname==dict_qDM['ROTATION'][0])
                txt_node = dict_qDM[skOut0.type][isOutNdCol if not isOutNdQuat else 2]
                #Добавить:
                bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt_node, use_transform=not self.isPlaceImmediately)
                aNd = tree.nodes.active
                aNd.width = 140
                if aNd.bl_idname in {dict_qDM['RGBA'][0], dict_qDM['VALUE'][1]}: #|2|.
                    aNd.show_options = False #Слишком неэстетично прятать без разбору, поэтому проверка выше.
                if skOut0.type in set_vqdtSkTypeArrFields: #Зато экономия явных определений для каждого типа.
                    aNd.inputs[0].hide_value = True
                #Установить одинаковость модов (например, RGB и HSV):
                for li in VqdtGetListOfNdEnums(aNd):
                    if hasattr(skOut0.node, li.identifier):
                        setattr(aNd, li.identifier, getattr(skOut0.node, li.identifier))
                #Соединить:
                skIn = aNd.inputs[0]
                for ski in aNd.inputs:
                    if skOut0.name==ski.name:
                        skIn = ski
                        break
                NewLinkAndRemember(skOut0, skIn)
                if self.foundGoalSkOut1:
                    NewLinkAndRemember(self.foundGoalSkOut1.tg, aNd.inputs[1])
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=UselessForCustomUndefTrees(context):
            return result
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalSkOut0 = None
        self.foundGoalSkOut1 = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiQuickDimensions, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiQuickDimensionsTool, "##A_D")
dict_setKmiCats['spc'].add(VoronoiQuickDimensionsTool.bl_idname)

txt_victName = ""

set_vitEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput', 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}

def CallbackDrawVoronoiInterfacer(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    fgSkSwap = self.foundGoalSkSwap
    fgSkTar = self.foundGoalSkTar
    count = (not not fgSkTar)+(not not fgSkSwap)
    if count:
        isTwo = count==2
        if fgSkSwap:
            DrawToolOftenStencil(self, prefs, cusorPos, [fgSkSwap], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, fgSkSwap, -0.5+0.75*isTwo, isTwo)
        if fgSkTar:
            DrawToolOftenStencil(self, prefs, cusorPos, [fgSkTar], isLineToCursor=True, isDrawText=False)
            DrawSidedSkText(self, prefs, cusorPos, fgSkTar, -0.5-0.75*isTwo, -isTwo)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiInterfacerTool(VoronoiToolSkNd):
    bl_idname = 'node.voronoi_interface_copier'
    bl_label = "Voronoi Interfacer"
    mode: bpy.props.IntProperty(name="Mode", default=0)
    def NextAssignment(self, context, isBoth):
        def FindAnySk():
            fgSkOut, fgSkIn = None, None
            for li in list_fgSksOut:
                if li.tg.bl_idname!='NodeSocketVirtual':
                    fgSkOut = li
                    break
            for li in list_fgSksIn:
                if li.tg.bl_idname!='NodeSocketVirtual':
                    fgSkIn = li
                    break
            return MinFromFgs(fgSkOut, fgSkIn)
        if not context.space_data.edit_tree:
            return
        if isBoth:
            self.foundGoalSkSwap = None
        self.foundGoalSkTar = None
        if (not txt_victName)and(self.mode==1): #Ожидаемо; а ещё #projects.blender.org/blender/blender/issues/113860
            return
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if nd.type=='REROUTE':
                continue
            if (self.foundGoalSkSwap)and(self.foundGoalSkSwap.tg.node!=nd):
                continue
            if (self.mode==1)and(nd.bl_idname not in set_vitEquestrianPortalBlids):
                break #Курсор должен быть рядом со всадником. А ещё с `continue` не будет высокоуровневой отмены.
            if StencilUnCollapseNode(nd, isBoth):
                StencilReNext(self, context, True)
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            if self.mode<2:
                self.foundGoalSkTar = FindAnySk()
            else:
                if isBoth:
                    self.foundGoalSkSwap = FindAnySk()
                skSwap = self.foundGoalSkSwap.tg if self.foundGoalSkSwap else None
                if skSwap:
                    for li in list_fgSksOut if skSwap.is_output else list_fgSksIn:
                        if li.tg.bl_idname=='NodeSocketVirtual':
                            continue
                        self.foundGoalSkTar = li
                        break
                    if (self.foundGoalSkTar)and(skSwap==self.foundGoalSkTar.tg):
                        self.foundGoalSkTar = None
            if StencilUnCollapseNode(nd, self.foundGoalSkTar):
                StencilReNext(self, context, True)
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (self.mode<2)and(not(self.foundGoalSkSwap or self.foundGoalSkTar))or(self.mode>1)and(not(self.foundGoalSkSwap and self.foundGoalSkTar)):
                return {'CANCELLED'}
            skTar = self.foundGoalSkTar.tg
            global txt_victName
            if not self.mode:
                txt_victName = skTar.name
            else:
                #Такой же паттерн, как и в DoLinkHH.
                ndEq = getattr(skTar.node,'paired_output', skTar.node)
                match ndEq.bl_idname:
                    case 'NodeGroupOutput': typeEq = 0
                    case 'NodeGroupInput':  typeEq = 1
                    case 'GeometryNodeSimulationOutput': typeEq = 2
                    case 'GeometryNodeRepeatOutput':     typeEq = 3
                    case x if x.endswith('NodeGroup'): typeEq = 4
                match typeEq:
                    case 0|1:
                        skfi = ViaVerGetSkfi(context.space_data.edit_tree, not typeEq)
                    case 2:
                        skfi = ndEq.state_items
                    case 3:
                        skfi = ndEq.repeat_items
                    case 4:
                        if not ndEq.node_tree:
                            return {'CANCELLED'}
                        skfi = ViaVerGetSkfi(ndEq.node_tree, skTar.is_output)
                match self.mode:
                    case 1:
                        for skf in skfi:
                            if skf.identifier==skTar.identifier: #Искать не по имени, а по identifier; ожидаемо почему.
                                skf.name = txt_victName
                                break
                    case 2|3:
                        skSwap = self.foundGoalSkSwap.tg
                        skfFrom = None
                        skfTo = None
                        for skf in skfi:
                            if skf.identifier==skSwap.identifier:
                                skfFrom = skf
                            if skf.identifier==skTar.identifier:
                                skfTo = skf
                        #todo3 сделать смену и для старых версий.
                        isDir = skfTo.index>skfFrom.index
                        inxTo = skfTo.index
                        inxFrom = skfFrom.index
                        skfi.data.move(skfFrom, inxTo+isDir)
                        if self.mode==2:
                            skfi.data.move(skfi[inxTo+(1-isDir*2)], inxFrom)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=UselessForCustomUndefTrees(context):
            return result
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalSkTar = None
        self.foundGoalSkSwap = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiInterfacer, self.mode>1)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_C", {'mode':0})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_V", {'mode':1})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_X", {'mode':2})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_Z", {'mode':3})
dict_setKmiCats['spc'].add(VoronoiInterfacerTool.bl_idname)

def CallbackDrawVoronoiLinksTransfer(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    #Паттерн VLT.
    if not self.foundGoalNdFrom:
        DrawDoubleNone(self, prefs, context)
    elif (self.foundGoalNdFrom)and(not self.foundGoalNdTo):
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalNdFrom)
        if prefs.dsIsDrawPoint:
            DrawWidePoint(self, prefs, cusorPos)
    else:
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalNdFrom, ofs=.75)
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalNdTo,   ofs=-.75)
class VoronoiLinksTransferTool(VoronoiToolDblSk):
    bl_idname = 'node.voronoi_links_transfer'
    bl_label = "Voronoi Links Transfer"
    isByOrder: bpy.props.BoolProperty(name="Transfer by indexes", default=False)
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        if isBoth:
            self.foundGoalNdFrom = None
        self.foundGoalNdTo = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if nd.type=='REROUTE':
                continue
            if isBoth:
                self.foundGoalNdFrom = li
            self.foundGoalNdTo = li
            if self.foundGoalNdFrom.tg==self.foundGoalNdTo.tg:
                self.foundGoalNdTo = None
            #Свершилось. Теперь у VL есть два нода.
            #Внезапно оказалось, что позиция "попадания" для нода буквально прилипает к нему, что весьма необычно наблюдать, когда тут вся тусовка ради сокетов.
            # Должна ли она скользить вместо прилипания?. Скорее всего нет, ведь иначе неизбежны осе-ориентированные проекции, визуально "затирающие" информацию.
            # А так же они оба будут изменяться, от чего не будет интуитивно понятно, кто первый, а кто второй; в отличие от прилипания, когда точно понятно, что "вот этот первый".
            # Что особенно актуально для этого инструмента, где важно, какой нод был выбран первым.
            if self.prefs.dsIsSlideOnNodes: #Не приспичило, но пусть будет.
                if self.foundGoalNdFrom:
                    self.foundGoalNdFrom.pos = GetNearestNode(self.foundGoalNdFrom.tg, callPos, self.uiScale).pos
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (self.foundGoalNdFrom)and(self.foundGoalNdTo):
                tree = context.space_data.edit_tree
                ndFrom = self.foundGoalNdFrom.tg
                ndTo = self.foundGoalNdTo.tg
                #todo1 в будущем возможно стоит инкапсулировать поведение VLTT в VST.
                def NewLink(sk, lk):
                    if sk.is_output:
                        tree.links.new(sk, lk.to_socket)
                        if lk.to_socket.is_multi_input:
                            tree.links.remove(lk)
                    else:
                        tree.links.new(lk.from_socket, sk)
                        tree.links.remove(lk)
                if not self.isByOrder:
                    for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                        for sk in putsFrom:
                            for lk in sk.links:
                                if not lk.is_muted:
                                    skTar = putsTo.get(GetSkLabelName(sk))
                                    if skTar:
                                        NewLink(skTar, lk)
                else:
                    LOnlyVisual = lambda a: [sk for sk in a if sk.enabled and not sk.hide]
                    for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                        for zp in zip(LOnlyVisual(putsFrom), LOnlyVisual(putsTo)):
                            for lk in zp[0].links:
                                if not lk.is_muted:
                                    NewLink(zp[1], lk)
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalNdFrom = None
        self.foundGoalNdTo = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiLinksTransfer, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiLinksTransferTool, "#C#_T")
SmartAddToRegAndAddToKmiDefs(VoronoiLinksTransferTool, "SC#_T", {'isByOrder':True})
dict_setKmiCats['spc'].add(VoronoiLinksTransferTool.bl_idname)

def CallbackDrawVoronoiWarper(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSk:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSk], isLineToCursor=True, textSideFlip=True)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiWarperTool(VoronoiToolSkNd):
    bl_idname = 'node.voronoi_warper'
    bl_label = "Voronoi Warper"
    isZoomedTo: bpy.props.BoolProperty(name="Zoom to", default=True)
    isSelectReroutes: bpy.props.BoolProperty(name="Select reroutes", default=True)
    #todo1 сделать цвет, any() которого будет окрашивать ноды; и придумать как потом очищать.
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vwBoxDiscl', self):
            AddStencilKeyProp(colTool, prefs,'vwSelectTargetKey')
    def NextAssignment(self, context, *naArgs):
        def FindAnySk(): #todo3 обобщить как-то или я не знаю.
            fgSkOut, fgSkIn = None, None
            for li in list_fgSksOut:
                if (li.tg.links)and(li.tg.bl_idname!='NodeSocketVirtual'):
                    fgSkOut = li
                    break
            for li in list_fgSksIn:
                if (li.tg.links)and(li.tg.bl_idname!='NodeSocketVirtual'):
                    fgSkIn = li
                    break
            return MinFromFgs(fgSkOut, fgSkIn)
        if not context.space_data.edit_tree:
            return
        self.foundGoalSk = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if StencilUnCollapseNode(nd):
                StencilReNext(self, context, True)
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            self.foundGoalSk = FindAnySk()
            if self.foundGoalSk:
                break
        if self.foundGoalSk:
            if StencilUnCollapseNode(self.foundGoalSk.tg.node):
                StencilReNext(self, context, True)
    def modal(self, context, event):
        if event.type==self.prefs.vwSelectTargetKey:
            self.isSelectTargetKey = event.value=='PRESS'
        if StencilMouseNext(self, context, event):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.foundGoalSk:
                sk = self.foundGoalSk.tg
                bpy.ops.node.select_all(action='DESELECT')
                if sk.links:
                    tree = context.space_data.edit_tree
                    dict_vptSoldSkoLinks = {}
                    dict_vptSoldSkiLinks = {}
                    for lk in tree.links:
                        if (lk.is_valid)and(not lk.is_hidden or lk.is_muted):
                            dict_vptSoldSkoLinks.setdefault(lk.from_socket, [])
                            dict_vptSoldSkoLinks[lk.from_socket].append(lk)
                            dict_vptSoldSkiLinks.setdefault(lk.to_socket, [])
                            dict_vptSoldSkiLinks[lk.to_socket].append(lk)
                    def RecrRerouteWalker(sk):
                        for lk in (dict_vptSoldSkoLinks if sk.is_output else dict_vptSoldSkiLinks).get(sk, []):
                            nd = lk.to_node if sk.is_output else lk.from_node
                            if nd.type=='REROUTE':
                                if self.isSelectReroutes:
                                    nd.select = True
                                RecrRerouteWalker(nd.outputs[0] if sk.is_output else nd.inputs[0])
                            else:
                                nd.select = True
                    RecrRerouteWalker(sk)
                    if self.isSelectTargetKey:
                        sk.node.select = True
                    tree.nodes.active = sk.node
                    if self.isZoomedTo:
                        bpy.ops.node.view_selected('INVOKE_DEFAULT')
                else:
                    sk.node.select = True
                    if self.isZoomedTo:
                        bpy.ops.node.view_selected('INVOKE_DEFAULT')
                    sk.node.select = False #Огонь хак.
                    #Изначально я ещё хотел максимально зумиться на сокет, но наверное это будет слишком странно; так что не стал.
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        self.foundGoalSk = None
        self.isSelectTargetKey = event.type_prev==prefs.vwSelectTargetKey #Повезло-повезло.
        StencilToolWorkPrepare(self, prefs, context, CallbackDrawVoronoiWarper, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiWarperTool, "##A_W")
SmartAddToRegAndAddToKmiDefs(VoronoiWarperTool, "S#A_W", {'isZoomedTo':False})
dict_setKmiCats['spc'].add(VoronoiWarperTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vwBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vwSelectTargetKey: bpy.props.StringProperty(name="Select target Key", default='LEFT_ALT')
list_clsToAddon.append(VoronoiWarperTool)

#Первый инструмент, созданный по запросам извне, а не по моим личным хотелкам.
def CallbackDrawVoronoiLazyNodeStencils(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if not self.foundGoalSkFirst:
        DrawDoubleNone(self, prefs, context)
    elif (self.foundGoalSkFirst)and(not self.foundGoalSkSecond):
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkFirst], isLineToCursor=True, textSideFlip=True)
        if prefs.dsIsDrawPoint:
            DrawWidePoint(self, prefs, cusorPos)
    else:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkFirst], isLineToCursor=True, isDrawText=False)
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSkSecond], isLineToCursor=True, isDrawText=False)
        if self.foundGoalSkFirst.tg.is_output^self.foundGoalSkSecond.tg.is_output:
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkFirst, -0.5, 0) #Не очевидное соответствие стороне текста гендеру сокета, придётся смириться.
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkSecond, -0.5, 0)
        else:
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkFirst, 0.25, -1)
            DrawSidedSkText(self, prefs, cusorPos, self.foundGoalSkSecond, -1.25, -1)
class VoronoiLazyNodeStencilsTool(VoronoiToolDblSk):
    bl_idname = 'node.voronoi_lazy_node_stencils'
    bl_label = "Voronoi Lazy Node Stencils" #Три буквы на инструмент, дожили.
    def DrawInAddon(self, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vlnsBoxDiscl', self):
            AddNiceColorProp(colTool, prefs,'vlnsNonColorName')
            AddNiceColorProp(colTool, prefs,'vlnsLastExecError', ico='ERROR' if prefs.vlnsLastExecError else 'NONE', decor=0)
    def NextAssignment(self, context, isBoth):
        def FindAnySk():
            fgSkOut, fgSkIn = None, None
            for li in list_fgSksOut:
                fgSkOut = li
                break
            for li in list_fgSksIn:
                fgSkIn = li
                break
            return MinFromFgs(fgSkOut, fgSkIn)
        if not context.space_data.edit_tree:
            return
        self.foundGoalSkSecond = None
        callPos = context.space_data.cursor_location
        #Из-за своего предназначения, этот инструмент гарантированно получает первый попавшийся сокет.
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            if isBoth:
                self.foundGoalSkFirst = FindAnySk()
            skFirst = self.foundGoalSkFirst.tg if self.foundGoalSkFirst else None
            if skFirst:
                if StencilUnCollapseNode(nd, isBoth):
                    StencilReNext(self, context, True)
                self.foundGoalSkSecond = FindAnySk()
                if self.foundGoalSkSecond:
                    if skFirst==self.foundGoalSkSecond.tg:
                        self.foundGoalSkSecond = None
                    if StencilUnCollapseNode(nd):
                        StencilReNext(self, context, False)
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if not(self.foundGoalSkFirst):
                return {'CANCELLED'}
            tree = context.space_data.edit_tree
            skFirst = self.foundGoalSkFirst.tg if self.foundGoalSkFirst else None
            skSecond = self.foundGoalSkSecond.tg if self.foundGoalSkSecond else None
            VlnstLazyStencil(context, self.prefs, tree, skFirst, skSecond)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalSkFirst = None
        self.foundGoalSkSecond = None
        self.isDrawDoubleNone = True
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiLazyNodeStencils, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiLazyNodeStencilsTool, "##A_Q")
dict_setKmiCats['spc'].add(VoronoiLazyNodeStencilsTool.bl_idname)

vlnstLastLastExecError = "" #Для пользовательского редактирования vlnsLastExecError, низя добавить или изменить, но можно удалить.
vlnstUpdateIsWorking = False
def VlnstUpdateLastExecError(self, context):
    global vlnstLastLastExecError, vlnstUpdateIsWorking
    if vlnstUpdateIsWorking:
        return
    vlnstUpdateIsWorking = True
    if not vlnstLastLastExecError:
        self.vlnsLastExecError = ""
    elif self.vlnsLastExecError:
        if self.vlnsLastExecError!=vlnstLastLastExecError: #Заметка: остерегаться переполнения стека.
            self.vlnsLastExecError = vlnstLastLastExecError
    else:
        vlnstLastLastExecError = ""
    vlnstUpdateIsWorking = False

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlnsBoxDiscl: bpy.props.BoolProperty(name="", default=False)
    vlnsNonColorName:  bpy.props.StringProperty(name="Non-Color name",  default="Non-Color")
    vlnsLastExecError: bpy.props.StringProperty(name="Last exec error", default="", update=VlnstUpdateLastExecError)
list_clsToAddon.append(VoronoiLazyNodeStencilsTool)

#Внезапно оказалось, что моя когда-то идея для инструмента "Ленивое Продолжение" инкапсулировалось в этом инструменте. Вот так неожиданность.
#Этот инструмент, то же самое, как и ^ (где сокет и нод однозначно определял следующий нод), только для двух сокетов; и возможностей больше.

lzAny = '!any'
class LazyKey:
    def __init__(self, fnb, fst, fsn, fsg, snb=lzAny, sst=lzAny, ssn=lzAny, ssg=lzAny):
        self.firstNdBlid = fnb
        self.firstSkBlid = dict_typeToSkfBlid.get(fst, fst)
        self.firstSkName = fsn
        self.firstSkGend = fsg
        self.secondNdBlid = snb
        self.secondSkBlid = dict_typeToSkfBlid.get(sst, sst)
        self.secondSkName = ssn
        self.secondSkGend = ssg
class LazyNode:
    #Чёрная магия. Если в __init__(list_props=[]), то указание в одном nd.list_props += [..] меняет вообще у всех в lzSt. Нереально чёрная магия; ночные кошмары обеспечены.
    def __init__(self, blid, list_props, ofs=(0,0), hhoSk=0, hhiSk=0):
        self.blid = blid
        #list_props Содержит в себе обработку и сокетов тоже.
        #Указание на сокеты (в list_props и lzHh_Sk) -- +1 от индекса, а знак указывает сторону; => 0 не используется.
        self.list_props = list_props
        self.lzHhOutSk = hhoSk
        self.lzHhInSk = hhiSk
        self.locloc = ofs #"Local location"; и offset от центра мира.
class LazyStencil:
    def __init__(self, key, csn=2, name="", prior=0.0):
        self.lzkey = key
        self.prior = prior #Чем выше, тем важнее.
        self.name = name
        self.trees = {} #Это также похоже на часть ключа.
        self.isTwoSkNeeded = csn==2
        self.list_nodes = []
        self.list_links = [] #Порядковый нод / сокет, и такое же на вход.
        self.isSameLink = False
        self.txt_exec = ""

list_vlnstDataPool = []

import copy
#Database:
lzSt = LazyStencil(LazyKey(lzAny,'RGB','Color',True,lzAny,'VECTOR','Normal',False), 2, "Fast Color NormapMap")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeNormalMap', [], hhiSk=-2, hhoSk=1) )
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnsNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGB','Color',True,lzAny,'VALUE',lzAny,False), 2, "Lazy Non-Color data to float socket")
lzSt.trees = {'ShaderNodeTree'}
lzSt.isSameLink = True
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnsNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGB','Color',False), 1, "NW TexCord Parody")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexImage', [(2,'hide',True)], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofs=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofs=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,0,1,0) ]
list_vlnstDataPool.append(lzSt)
lzSt = copy.deepcopy(lzSt)
lzSt.lzkey.firstSkName = "Base Color"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'VECTOR','Vector',False), 1, "NW TexCord Parody Half")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], hhoSk=-1, ofs=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofs=(-360,0)) )
lzSt.list_links += [ (1,0,0,0) ]
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGB',lzAny,True,lzAny,'SHADER',lzAny,False), 2, "Insert Emission")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeEmission', [], hhiSk=-1, hhoSk=1) )
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey('ShaderNodeBackground','RGB','Color',False), 1, "World env texture", prior=1.0)
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexEnvironment', [], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofs=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeTexCoord', [('show_options',False)], ofs=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,3,1,0) ]
list_vlnstDataPool.append(lzSt)
##

list_vlnstDataPool.sort(key=lambda a:a.prior, reverse=True)

#Для одного нода ещё и сгодилось бы, но учитывая большое разнообразие и гибкость, наверное лучше без NewLinkAndRemember(), соединять в сыром виде.
def DoLazyStencil(tree, skFirst, skSecond, lzSten):
    list_result = []
    firstCenter = None
    for li in lzSten.list_nodes:
        nd = tree.nodes.new(li.blid)
        nd.location += mathutils.Vector(li.locloc)
        list_result.append(nd)
        for pr in li.list_props:
            if length(pr)==2:
                setattr(nd, pr[0], pr[1])
            else:
                setattr( (nd.outputs if pr[0]>0 else nd.inputs)[abs(pr[0])-1], pr[1], pr[2] )
        if li.lzHhOutSk:
            tree.links.new(nd.outputs[abs(li.lzHhOutSk)-1], skFirst if li.lzHhOutSk<0 else skSecond)
        if li.lzHhInSk:
            tree.links.new(skFirst if li.lzHhInSk<0 else skSecond, nd.inputs[abs(li.lzHhInSk)-1])
    for li in lzSten.list_links:
        tree.links.new(list_result[li[0]].outputs[li[1]], list_result[li[2]].inputs[li[3]])
    if lzSten.isSameLink:
        tree.links.new(skFirst, skSecond)
    return list_result
def LzCompare(a, b):
    return (a==b)or(a==lzAny)
def LzNodeDoubleCheck(zk, a, b): return LzCompare(zk.firstNdBlid,             a.bl_idname if a else "") and LzCompare(zk.secondNdBlid,             b.bl_idname if b else "")
def LzTypeDoubleCheck(zk, a, b): return LzCompare(zk.firstSkBlid, CollapseSkTypeToBlid(a) if a else "") and LzCompare(zk.secondSkBlid, CollapseSkTypeToBlid(b) if b else "") #Не 'type', а blid'ы; для аддонских деревьев.
def LzNameDoubleCheck(zk, a, b): return LzCompare(zk.firstSkName,       GetSkLabelName(a) if a else "") and LzCompare(zk.secondSkName,       GetSkLabelName(b) if b else "")
def LzGendDoubleCheck(zk, a, b): return LzCompare(zk.firstSkGend,             a.is_output if a else "") and LzCompare(zk.secondSkGend,             b.is_output if b else "")
def LzLazyStencil(prefs, tree, skFirst, skSecond):
    if not skFirst:
        return []
    ndOut = skFirst.node
    ndIn = skSecond.node if skSecond else None
    for li in list_vlnstDataPool:
        if (li.isTwoSkNeeded)^(not skSecond): #Должен не иметь второго для одного, или иметь для двух.
            if (not li.trees)or(tree.bl_idname in li.trees): #Должен поддерживать тип дерева.
                zk = li.lzkey
                if LzNodeDoubleCheck(zk, ndOut, ndIn): #Совпадение нод.
                    for cyc in (False, True):
                        skF = skFirst
                        skS = skSecond
                        if cyc: #Оба выхода и оба входа, но разные гендеры могут быть в разном порядке. Всё равно для них перестановка не имеет значения, да ведь?.
                            skF, skS = skSecond, skFirst
                        if LzTypeDoubleCheck(zk, skF, skS): #Совпадение Blid'ов сокетов.
                            if LzNameDoubleCheck(zk, skF, skS): #Имён/меток сокетов.
                                if LzGendDoubleCheck(zk, skF, skS): #Гендеров.
                                    result = DoLazyStencil(tree, skF, skS, li)
                                    if li.txt_exec:
                                        try:
                                            exec(li.txt_exec) #Тревога!1, А нет.. без паники, это внутреннее. Всё ещё всё в безопасности.
                                        except Exception as ex:
                                            global vlnstLastLastExecError
                                            vlnstLastLastExecError = str(ex)
                                            prefs.vlnsLastExecError = vlnstLastLastExecError
                                    return result
def VlnstLazyStencil(context, prefs, tree, skFirst, skSecond):
    cusorPos = context.space_data.cursor_location
    list_nodes = LzLazyStencil(prefs, tree, skFirst, skSecond)
    if list_nodes:
        bpy.ops.node.select_all(action='DESELECT')
        firstOffset = cusorPos-list_nodes[0].location
        for nd in list_nodes:
            nd.select = True
            nd.location += firstOffset
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')

def CallbackDrawVoronoiResetNode(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalNd:
        DrawNodeStencilFull(self, prefs, cusorPos, self.foundGoalNd)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiResetNodeTool(VoronoiToolSkNd):
    bl_idname = 'node.voronoi_reset_node'
    bl_label = "Voronoi Reset Node"
    isResetEnums: bpy.props.BoolProperty(name="Reset enums", default=False)
    isResetOnDrag: bpy.props.BoolProperty(name="Reset on grag", default=False)
    isSelectResetedNode: bpy.props.BoolProperty(name="Select reseted node", default=True)
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        self.foundGoalNd = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale, skipPoorNodes=False):
            nd = li.tg
            if nd.type=='REROUTE': #"Вы что, хотите пересоздавать рероуты?".
                continue
            self.foundGoalNd = li
            if self.isResetOnDrag:
                VrntDoResetNode(self, self.foundGoalNd.tg)
            break
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if (not self.isResetOnDrag)and(self.foundGoalNd):
                ndTar = self.foundGoalNd.tg
                VrntDoResetNode(self, ndTar)
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        self.foundGoalNd = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiResetNode, True)
        return {'RUNNING_MODAL'}

SmartAddToRegAndAddToKmiDefs(VoronoiResetNodeTool, "###_BACK_SPACE")
SmartAddToRegAndAddToKmiDefs(VoronoiResetNodeTool, "S##_BACK_SPACE", {'isResetEnums':True})
dict_setKmiCats['spc'].add(VoronoiResetNodeTool.bl_idname)

def VrntDoResetNode(self, ndTar):
    tree = ndTar.id_data
    nd = tree.nodes.new(ndTar.bl_idname)
    nd.location = ndTar.location
    if nd.type=='GROUP':
        nd.node_tree = ndTar.node_tree
    for cyc, sk in enumerate(ndTar.outputs):
        for lk in sk.links:
            tree.links.new(nd.outputs[cyc], lk.to_socket)
    for cyc, sk in enumerate(ndTar.inputs):
        for lk in sk.links:
            tree.links.new(lk.from_socket, nd.inputs[cyc])
    if not self.isResetEnums:
        for li in nd.bl_rna.properties.items():
            if (not li[1].is_readonly)and(getattr(li[1],'enum_items', None)):
                setattr(nd, li[0], getattr(ndTar, li[0]))
    tree.nodes.remove(ndTar)
    tree.nodes.active = nd
    nd.select = self.isSelectResetedNode

#Шаблон для быстрого добавления нового инструмента:
def CallbackDrawVoronoiDummy(self, context):
    if not(prefs:=StencilStartDrawCallback(self, context)):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSk:
        DrawToolOftenStencil(self, prefs, cusorPos, [self.foundGoalSk], isLineToCursor=True, textSideFlip=True)
    elif prefs.dsIsDrawPoint:
        DrawWidePoint(self, prefs, cusorPos)
class VoronoiDummyTool(VoronoiToolSkNd):
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    isDummy: bpy.props.BoolProperty(name="Dummy", default=False)
    def DrawInAddon(self, context, where, prefs):
        if colTool:=AddClsBoxDiscl(where, prefs,'vdBoxDiscl', self):
            AddNiceColorProp(colTool, prefs,'vdDummy')
    def NextAssignment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        self.foundGoalSk = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, self.uiScale):
            nd = li.tg
            if StencilUnCollapseNode(nd, isBoth):
                StencilReNext(self, context, True)
            if nd.type=='REROUTE':
                continue
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos, self.uiScale)
            fgSkIn = list_fgSksIn[0] if list_fgSksIn else None
            fgSkOut = list_fgSksOut[0] if list_fgSksOut else None
            self.foundGoalSk = MinFromFgs(fgSkOut, fgSkIn)
            break
        #todo2 CallbackDraw'ы тоже нужно стандартизировать и зашаблонить, причём более актуально; (VQDT от VST).
        #Todo1 Оно работает, но в идеале требуется полное переосмысление всего конвейера рисования и алгоритмов выбора сокетов у инструментов.
        # А так же см. NA() в VoronoiQuickDimensionsTool, высокий паттерн для стандартизации.
        #todo1 возможно стоит иметь два NextAssignment()'а вместо isBoth'а; но это не точно.
        #todo1 а также обновить комментарии топологии с `isCanReOut`.
        #todo1 Ещё нужно что-то придумать с концепцией, когда имеются разные критерии от isBoth'а, и второй находится сразу рядом после первого моментально.
        if self.foundGoalSk:
            if StencilUnCollapseNode(self.foundGoalSk.tg.node):
                StencilReNext(self, context, True)
    def modal(self, context, event):
        if StencilMouseNext(self, context, event, False):
            if result:=StencilModalEsc(self, context, event):
                return result
            if self.foundGoalSk:
                sk = self.foundGoalSk.tg
                sk.name = "hi. i am a vdt!"
                sk.node.label = "see source code"
                VlrtRememberLastSockets(sk if sk.is_output else None, sk if not sk.is_output else None)
                return {'FINISHED'}
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if result:=StencilBeginToolInvoke(self, context, event):
            return result
        prefs = self.prefs
        self.foundGoalSk = None
        StencilToolWorkPrepare(self, self.prefs, context, CallbackDrawVoronoiDummy, True)
        return {'RUNNING_MODAL'}

#SmartAddToRegAndAddToKmiDefs(VoronoiDummyTool, "###_D", {'isDummy':True})
dict_setKmiCats['grt'].add(VoronoiDummyTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vdBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vdDummy: bpy.props.StringProperty(name="Dummy", default="Dummy")
#list_clsToAddon.append(VoronoiDummyTool)

def AddonVer():
    return "v"+".".join([str(v) for v in bl_info['version']])

def GetVlKeyconfigAsPy(): #Взято из `bl_keymap_utils.io`. Понятия не имею, как оно работает.
    import bl_keymap_utils
    def Ind(num):
        return " "*num
    def keyconfig_merge(kc1, kc2):
        kc1_names = {km.name for km in kc1.keymaps}
        merged_keymaps = [(km, kc1) for km in kc1.keymaps]
        if kc1 != kc2:
            merged_keymaps.extend(
                (km, kc2)
                for km in kc2.keymaps
                if km.name not in kc1_names)
        return merged_keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.active
    class FakeKeyConfig:
        keymaps = []
    edited_kc = FakeKeyConfig()
    edited_kc.keymaps.append(GetUserKmNe())
    if kc!=wm.keyconfigs.default:
        export_keymaps = keyconfig_merge(edited_kc, kc)
    else:
        export_keymaps = keyconfig_merge(edited_kc, edited_kc)
    ##
    result = ""
    result += "list_keyconfigData = \\\n["
    sco = 0
    for km, _kc_x in export_keymaps:
        km = km.active()
        result += "("
        result += f"\"{km.name:s}\","+"\n"
        result += f"{Ind(2)}" "{"
        result += f"\"space_type\": '{km.space_type:s}'"
        result += f", \"region_type\": '{km.region_type:s}'"
        isModal = km.is_modal
        if isModal:
            result += ", \"modal\": True"
        result += "},"+"\n"
        result += f"{Ind(2)}" "{"
        result += f"\"items\":"+"\n"
        result += f"{Ind(3)}["
        for kmi in km.keymap_items:
            if not kmi.idname.startswith("node.voronoi_"):
                continue
            sco += 1
            if isModal:
                kmi_id = kmi.propvalue
            else:
                kmi_id = kmi.idname
            result += f"("
            kmi_args = bl_keymap_utils.io.kmi_args_as_data(kmi)
            kmi_data = bl_keymap_utils.io._kmi_attrs_or_none(4, kmi)
            result += f"\"{kmi_id:s}\""
            if kmi_data is None:
                result += f", "
            else:
                result += ",\n" f"{Ind(5)}"
            result += kmi_args
            if kmi_data is None:
                result += ", None),"+"\n"
            else:
                result += ","+"\n"
                result += f"{Ind(5)}" "{"
                result += kmi_data
                result += f"{Ind(6)}"
                result += "},\n" f"{Ind(5)}"
                result += "),"+"\n"
            result += f"{Ind(4)}"
        result += "],\n" f"{Ind(3)}"
        result += "},\n" f"{Ind(2)}"
        result += "),\n" f"{Ind(1)}"
    result += "]"+" #km count: "+str(sco)+"\n"
    result += "\n"
    result += "if True:"+"\n"
    result += "    import bl_keymap_utils"+"\n"
    result += "    import bl_keymap_utils.versioning"+"\n" #Чёрная магия; кажется, такая же как и с "gpu_extras".
    result += "    kc = bpy.context.window_manager.keyconfigs.active"+"\n"
    from bpy.app import version_file
    result += f"    kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {version_file!r})"+"\n"
    del version_file
    result += "    bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)"
    return result

set_ignoredAddonPrefs = {'bl_idname', 'vaUiTabs', 'vaInfoRestore', 'vaGeneralBoxDiscl', 'vaAddonBoxDiscl',
                         'vaKmiMainstreamBoxDiscl', 'vaKmiOtjersBoxDiscl', 'vaKmiSpecialBoxDiscl', 'vaKmiQqmBoxDiscl', 'vaKmiCustomBoxDiscl'}
def GetVaSettAsPy():
    txt_vasp = ""
    import datetime
    txt_vasp += f"#Exported/Importing addon settings for Voronoi Linker {AddonVer()}\n"
    txt_vasp += f"#Generated "+datetime.datetime.now().strftime("%Y.%m.%d")+"\n"
    txt_vasp += "\n"
    txt_vasp += "import bpy\n"
    #Сконструировать изменённые настройки аддона:
    txt_vasp += "\n"
    txt_vasp += "#Addon prefs:\n"
    txt_vasp += f"prefs = bpy.context.preferences.addons['{voronoiAddonName}'].preferences"+"\n\n"
    txt_vasp += "def SetProp(attr, val):"+"\n"
    txt_vasp += "    if hasattr(prefs, attr):"+"\n"
    txt_vasp += "        setattr(prefs, attr, val)"+"\n\n"
    prefs = Prefs()
    def AddAndProc(txt):
        nonlocal txt_vasp
        len = txt.find(",")
        txt_vasp += txt.replace(", ",","+" "*(42-len), count=1)
    for li in prefs.rna_type.properties:
        if not li.is_readonly:
            #'_BoxDiscl'ы не стал игнорировать, пусть будут.
            if li.identifier not in set_ignoredAddonPrefs:
                isArray = getattr(li,'is_array', False)
                if isArray:
                    isDiff = not not [li for li in zip(li.default_array, getattr(prefs, li.identifier)) if li[0]!=li[1]]
                else:
                    isDiff = li.default!=getattr(prefs, li.identifier)
                if (True)or(isDiff): #Наверное сохранять только разницу не безопасно, вдруг несохранённые свойства изменят своё значение по умолчанию.
                    if isArray:
                        #txt_vasp += f"prefs.{li.identifier} = ({' '.join([str(li)+',' for li in arr])})\n"
                        list_vals = [str(li)+"," for li in getattr(prefs, li.identifier)]
                        list_vals[-1] = list_vals[-1][:-1]
                        AddAndProc(f"SetProp('{li.identifier}', ("+" ".join(list_vals)+"))\n")
                    else:
                        match li.type:
                            case 'STRING': AddAndProc(f"SetProp('{li.identifier}', \"{getattr(prefs, li.identifier)}\")"+"\n")
                            case 'ENUM':   AddAndProc(f"SetProp('{li.identifier}', '{getattr(prefs, li.identifier)}')"+"\n")
                            case _:        AddAndProc(f"SetProp('{li.identifier}', {getattr(prefs, li.identifier)})"+"\n")
    #Сконструировать все VL хоткеи:
    txt_vasp += "\n"
    txt_vasp += "#Addon keymaps:\n"
    #P.s. я не знаю, как обрабатывать только изменённые хоткеи; это выглядит слишком головной болью и дремучим лесом.
    # Лень реверсинженерить '..\scripts\modules\bl_keymap_utils\io.py', поэтому просто сохранять всех.
    txt_vasp += GetVlKeyconfigAsPy() #Оно нахрен не работает; та часть, которая восстанавливает, ничего не сохраняется.
    #Придётся ждать того героя, что придёт и починит всё это.
    #todo1 нужно придумать другой способ сохранения хоткеев.
    return txt_vasp

#Здесь оставлю мой маленький список моих личных "хотелок" (по хронологии интеграции), которые перекочевали из других моих личных аддонов в VL:
#Hider
#QuckMath и JustMathPie
#Warper
#RANTO

def Prefs():
    return bpy.context.preferences.addons[voronoiAddonName].preferences

voronoiTextToolSettings = " Tool settings"
txt_onlyFontFormat = "Only .ttf or .otf format"
txt_copySettAsPyScript = "Copy addon settings as .py script"

class VoronoiAddonTabs(bpy.types.Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    opt: bpy.props.StringProperty()
    def invoke(self, context, event):
        #if not self.opt: return {'CANCELLED'}
        match self.opt:
            case 'GetPySett':
                context.window_manager.clipboard = GetVaSettAsPy()
            case 'AddNewKmi':
                GetUserKmNe().keymap_items.new("node.voronoi_",'D','PRESS').show_expanded = True
            case _:
                Prefs().vaUiTabs = self.opt
        return {'FINISHED'}

class KmiCat:
    def __init__(self, txt_prop='', label="", set_kmis=set(), sco=0, set_idn=set()):
        self.txt_prop = txt_prop
        self.set_kmis = set_kmis
        self.set_idn = set_idn
        self.label = label
        self.sco = sco
class KmiCats:
    pass

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaUiTabs: bpy.props.EnumProperty(name="Addon Prefs Tabs", default='SETTINGS', items=( ('SETTINGS',"Settings",""), ('DRAW',"Draw",""), ('KEYMAP',"Keymap","") ))
    vaGeneralBoxDiscl: bpy.props.BoolProperty(name="General settings", default=False)
    vaAddonBoxDiscl: bpy.props.BoolProperty(name="Addon", default=False)
    vaInfoRestore: bpy.props.BoolProperty(name="", description="This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon")
    #Box disclosures:
    vaKmiMainstreamBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vaKmiOtjersBoxDiscl:     bpy.props.BoolProperty(name="", default=False)
    vaKmiSpecialBoxDiscl:    bpy.props.BoolProperty(name="", default=False)
    vaKmiQqmBoxDiscl:        bpy.props.BoolProperty(name="", default=False)
    vaKmiCustomBoxDiscl:     bpy.props.BoolProperty(name="", default=True)
    #Draw
    dsIsDrawText:   bpy.props.BoolProperty(name="Text",        default=True) #Учитывая VHT и VEST, это уже больше просто для текста в рамке, чем для текста от сокетов.
    dsIsDrawMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsDrawPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsDrawLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsDrawSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    ##
    dsIsColoredText:   bpy.props.BoolProperty(name="Text",        default=True)
    dsIsColoredMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsColoredPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsColoredLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsColoredSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    ##
    dsIsAlwaysLine:    bpy.props.BoolProperty(       name="Always draw line",          default=False)
    dsSocketAreaAlpha: bpy.props.FloatProperty(      name="Socket area alpha",         default=0.075,                               min=0, max=1,         subtype="FACTOR")
    dsUniformColor:    bpy.props.FloatVectorProperty(name="Alternative uniform color", default=(0.632502, 0.408091, 0.174378, 0.9), min=0, max=1, size=4, subtype='COLOR') #(0.65, 0.65, 0.65, 1.0)
    dsNodeColor:       bpy.props.FloatVectorProperty(name="To-Node draw color",        default=(1.0, 1.0, 1.0, 0.9),                min=0, max=1, size=4, subtype='COLOR')
    ##
    dsDisplayStyle: bpy.props.EnumProperty(name="Display frame style", default='CLASSIC', items=( ('CLASSIC',"Classic",""), ('SIMPLIFIED',"Simplified",""), ('ONLY_TEXT',"Only text","") ))
    dsFontFile:    bpy.props.StringProperty(name="Font file",  default='C:\Windows\Fonts\consola.ttf', subtype='FILE_PATH') #"Пользователи Линукса негодуют".
    dsLineWidth:   bpy.props.FloatProperty( name="Line Width", default=1.5, min=0.5, max=8, subtype="FACTOR")
    dsPointRadius: bpy.props.FloatProperty( name="Point size", default=1,   min=0,   max=3)
    dsFontSize:    bpy.props.IntProperty(   name="Font size",  default=28,   min=10,  max=48)
    ##
    dsPointOffsetX:   bpy.props.FloatProperty(name="Point offset X axis",       default=20, min=-50, max=50)
    dsFrameOffset:    bpy.props.IntProperty(  name="Frame size",                default=0,  min=0,   max=24, subtype='FACTOR')
    dsDistFromCursor: bpy.props.FloatProperty(name="Text distance from cursor", default=25, min=5,   max=50)
    ##
    dsIsSlideOnNodes: bpy.props.BoolProperty(name="Slide on a nodes", default=False)
    ##
    dsIsAllowTextShadow: bpy.props.BoolProperty(       name="Enable text shadow", default=True)
    dsShadowCol:         bpy.props.FloatVectorProperty(name="Shadow color",       default=[0.0, 0.0, 0.0, 0.5], size=4, min=0,   max=1, subtype='COLOR')
    dsShadowOffset:      bpy.props.IntVectorProperty(  name="Shadow offset",      default=[2,-2],               size=2, min=-20, max=20)
    dsShadowBlur:        bpy.props.IntProperty(        name="Shadow blur",        default=2,                            min=0,   max=2)
    ##
    dsIsDrawDebug:  bpy.props.BoolProperty(name="Display debugging", default=False)
    #Main:
    #Уж было я хотел добавить это, но потом мне стало таак лень. Это же нужно всё менять под "только сокеты", и критерии для нод неведомо как получать.
    #И выгода неизвестно какая, кроме эстетики. Так что ну его нахрен. "Работает -- не трогай".
    #А ещё реализация "только сокеты" может грозить кроличьей норой.
    vSearchMethod: bpy.props.EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET',"Nearest node > nearest socket",""), ('SOCKET',"Only nearest socket","") )) #Нигде не используется; и кажется, никогда не будет.
    vEdgePanFac: bpy.props.FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0)
    #All tool:
    vPieType:              bpy.props.EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vPieScale:             bpy.props.FloatProperty(name="Pie scale",                  default=1.5, min=1,  max=2, subtype="FACTOR")
    vPieSocketDisplayType: bpy.props.IntProperty(  name="Display socket type info",   default=1,   min=-1, max=1)
    vPieAlignment:         bpy.props.IntProperty(  name="Alignment between elements", default=1,   min=0,  max=2)
    ##
    vdsDrawNodeNameLabel: bpy.props.EnumProperty(name="Display text for node", default='NONE', items=( ('NONE',"None",""), ('NAME',"Only name",""), ('LABEL',"Only label",""), ('LABELNAME',"Name and label","") ))
    vdsLabelSideRight:    bpy.props.BoolProperty(name="Label side on right", default=False)
    def DrawTabSettings(self, context, where):
        colMain = where.column()
        try:
            if colTool:=AddClsBoxDiscl(colMain, self,'vaGeneralBoxDiscl'):
                #AddHandSplitProp(colTool, self,'vSearchMethod')
                AddHandSplitProp(colTool, self,'vEdgePanFac')
                AddThinSep(colTool, 2)
                AddHandSplitProp(colTool, self,'vPieType')
                colProp = colTool.column(align=True)
                AddHandSplitProp(colProp, self,'vPieScale')
                AddHandSplitProp(colProp, self,'vPieSocketDisplayType')
                AddHandSplitProp(colProp, self,'vPieAlignment')
                colProp.active = self.vPieType=='CONTROL'
                AddThinSep(colTool, 2)
                AddHandSplitProp(colTool, self,'vdsDrawNodeNameLabel')
                colProp = colTool.column(align=True)
                AddHandSplitProp(colProp, self,'vdsLabelSideRight')
                colProp.active = self.vdsDrawNodeNameLabel!='NONE'
            for cls in list_clsToAddon:
                cls.DrawInAddon(cls, colMain, self)
            if colTool:=AddClsBoxDiscl(colMain, self,'vaAddonBoxDiscl', isWide=True):
                colProp = colTool.column(align=True)
                colProp.alignment = 'CENTER' #Всё равно 'LEFT'.
                colProp.scale_x = 1.15
                colProp.operator(VoronoiAddonTabs.bl_idname, text=txt_copySettAsPyScript).opt = 'GetPySett'
        except Exception as ex:
            colMain.label(text=str(ex), icon='ERROR')
    def DrawTabDraw(self, context, where):
        colMain = where.column()
        try:
            rowDrawColor = colMain.row(align=True)
            rowDrawColor.use_property_split = True
            colDraw = rowDrawColor.column(align=True, heading='Draw')
            colDraw.prop(self,'dsIsDrawText')
            colDraw.prop(self,'dsIsDrawMarker')
            colDraw.prop(self,'dsIsDrawPoint')
            colDraw.prop(self,'dsIsDrawLine')
            colDraw.prop(self,'dsIsDrawSkArea')
            colCol = rowDrawColor.column(align=True, heading='Colored')
            def AddColoredProp(where, txt):
                row = where.row(align=True)
                row.prop(self, txt)
                row.active = getattr(self, txt.replace("Colored","Draw"))
            AddColoredProp(colCol,'dsIsColoredText')
            AddColoredProp(colCol,'dsIsColoredMarker')
            AddColoredProp(colCol,'dsIsColoredPoint')
            AddColoredProp(colCol,'dsIsColoredLine')
            AddColoredProp(colCol,'dsIsColoredSkArea')
            colProps = colMain.column()
            AddHandSplitProp(colProps, self,'dsSocketAreaAlpha')
            tgl = ( (self.dsIsDrawText and not self.dsIsColoredText)or
                    (self.dsIsDrawMarker and not self.dsIsColoredMarker)or
                    (self.dsIsDrawPoint  and not self.dsIsColoredPoint )or
                    (self.dsIsDrawLine   and not self.dsIsColoredLine  )or
                    (self.dsIsDrawSkArea and not self.dsIsColoredSkArea) )
            AddHandSplitProp(colProps, self,'dsUniformColor', tgl)
            tgl = ( (self.dsIsDrawText and self.dsIsColoredText)or
                    (self.dsIsDrawPoint  and self.dsIsColoredPoint )or
                    (self.dsIsDrawLine   and self.dsIsColoredLine  ) )
            AddHandSplitProp(colProps, self,'dsNodeColor', tgl)
            AddHandSplitProp(colProps, self,'dsDisplayStyle')
            AddHandSplitProp(colProps, self,'dsFontFile')
            import os
            if not os.path.splitext(self.dsFontFile)[1] in (".ttf",".otf"):
                spl = colProps.split(factor=0.4, align=True)
                spl.label(text="")
                spl.label(text=txt_onlyFontFormat, icon='ERROR')
            colGroup = colProps.column(align=True)
            AddHandSplitProp(colGroup, self,'dsLineWidth')
            AddHandSplitProp(colGroup.row(), self,'dsPointRadius')
            AddHandSplitProp(colGroup, self,'dsFontSize')
            row = colProps.row(align=True)
            row.separator()
            row.scale_x = .333
            colGroup = colProps.column(align=True)
            AddHandSplitProp(colGroup, self,'dsPointOffsetX')
            AddHandSplitProp(colGroup.row(), self,'dsFrameOffset')
            AddHandSplitProp(colGroup, self,'dsDistFromCursor')
            AddThinSep(colProps) #Межгалкоевые отступы складываются, поэтому дополнительный отступ для равновесия.
            AddHandSplitProp(colProps, self,'dsIsAlwaysLine')
            AddHandSplitProp(colProps, self,'dsIsSlideOnNodes')
            AddHandSplitProp(colProps, self,'dsIsAllowTextShadow')
            colShadow = colProps.column(align=True)
            AddHandSplitProp(colShadow, self,'dsShadowCol', self.dsIsAllowTextShadow)
            AddHandSplitProp(colShadow, self,'dsShadowBlur') #Размытие тени разделяет их, чтобы не сливались вместе по середине.
            row = AddHandSplitProp(colShadow, self,'dsShadowOffset', isReturnLy=True).row(align=True)
            row.row().prop(self,'dsShadowOffset', text="X  ", index=0, icon_only=True)
            row.row().prop(self,'dsShadowOffset', text="Y  ", index=1, icon_only=True)
            colShadow.active = self.dsIsAllowTextShadow
            AddHandSplitProp(colProps, self,'dsIsDrawDebug')
        except Exception as ex:
            colMain.label(text=str(ex), icon='ERROR')
    def DrawTabKeymaps(self, context, where):
        colMain = where.column()
        try:
            colMain.separator()
            rowLabelMain = colMain.row(align=True)
            rowLabel = rowLabelMain.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(icon='DOT')
            rowLabel.label(text=TranslateIface("Node Editor"))
            rowLabelPost = rowLabelMain.row(align=True)
            #rowLabelPost.active = False
            colList = colMain.column(align=True)
            kmUNe = GetUserKmNe()
            ##
            kmiCats = KmiCats()
            kmiCats.grt = KmiCat('vaKmiMainstreamBoxDiscl', "The Great Trio",   set(), 0, dict_setKmiCats['grt'] )
            kmiCats.oth = KmiCat('vaKmiOtjersBoxDiscl',     "Others",           set(), 0, dict_setKmiCats['oth'] )
            kmiCats.spc = KmiCat('vaKmiSpecialBoxDiscl',    "Specials",         set(), 0, dict_setKmiCats['spc'] )
            kmiCats.qqm = KmiCat('vaKmiQqmBoxDiscl',        "Quick quick math", set(), 0, dict_setKmiCats['qqm'] )
            kmiCats.cus = KmiCat('vaKmiCustomBoxDiscl',     "Custom",           set(), 0)
            #В старых версиях аддона с другим методом поиска, на вкладке "keymap" порядок отображался в обратном порядке вызовов регистрации kmidef с одинаковыми `cls`.
            #Теперь сделал так. Как работал предыдущий метод -- для меня загадка.
            scoAll = 0
            for li in kmUNe.keymap_items:
                if li.idname.startswith("node.voronoi_"):
                    #todo1 мб стоит выпендриться, и упаковать условия через lambda.
                    if li.id<0: #Отрицательный ид для кастомных? Ну ладно. Пусть будет идентифицирующим критерием.
                        kmiCats.cus.set_kmis.add(li)
                        kmiCats.cus.sco += 1
                    elif [True for pr in {'quickOprFloat','quickOprVector','quickOprBool','quickOprColor','justCallPie','isRepeatLastOperation'} if getattr(li.properties, pr, None)]:
                        kmiCats.qqm.set_kmis.add(li)
                        kmiCats.qqm.sco += 1
                    elif li.idname in kmiCats.grt.set_idn:
                        kmiCats.grt.set_kmis.add(li)
                        kmiCats.grt.sco += 1
                    elif li.idname in kmiCats.oth.set_idn:
                        kmiCats.oth.set_kmis.add(li)
                        kmiCats.oth.sco += 1
                    else:
                        kmiCats.spc.set_kmis.add(li)
                        kmiCats.spc.sco += 1
                    scoAll += 1 #Хоткеев теперь стало тааак много, что неплохо было бы узнать их количество.
            if kmUNe.is_user_modified:
                rowRestore = rowLabelMain.row(align=True)
                rowInfo = rowRestore.row()
                rowInfo.prop(self,'vaInfoRestore', icon='INFO', emboss=False)
                rowInfo.active = False #True, но от постоянного горения рискует мозги прожечь.
                rowRestore.context_pointer_set('keymap', kmUNe)
                rowRestore.operator('preferences.keymap_restore', text=TranslateIface("Restore"))
            else:
                rowLabelMain.label()
            rowAddNew = rowLabelMain.row(align=True)
            rowAddNew.ui_units_x = 12
            rowAddNew.separator()
            rowAddNew.operator(VoronoiAddonTabs.bl_idname, text="Add New", icon='ADD').opt = 'AddNewKmi' # NONE  ADD
            import rna_keymap_ui
            def AddKmisCategory(where, cat):
                if not cat.set_kmis:
                    return
                colListCat = where.row().column(align=True)
                rowDiscl = colListCat.row(align=True)
                rowDiscl.active = False
                tgl = AddDisclosureProp(rowDiscl, self, cat.txt_prop, cat.label+f" ({cat.sco})", isWide=True)
                if not tgl:
                    return
                for li in sorted(cat.set_kmis, key=lambda a:a.id):
                    colListCat.context_pointer_set('keymap', kmUNe)
                    rna_keymap_ui.draw_kmi([], context.window_manager.keyconfigs.user, kmUNe, li, colListCat, 0) #Заметка: если colListCat будет не colListCat, то возможность удаления kmi станет недоступной.
            AddKmisCategory(colList, kmiCats.cus)
            AddKmisCategory(colList, kmiCats.grt)
            AddKmisCategory(colList, kmiCats.oth)
            AddKmisCategory(colList, kmiCats.spc)
            AddKmisCategory(colList, kmiCats.qqm)
            rowLabelPost.label(text=f"({scoAll})")
        except Exception as ex:
            colMain.label(text=str(ex), icon='ERROR')
    def draw(self, context):
        colLy = self.layout.column()
        rowTabs = colLy.row(align=True)
        #Переключение вкладок создано через оператор, чтобы случайно не сменить вкладку при ведении зажатой мышки, кой есть особый соблазн с таким большим количеством "isColored".
        #А так же теперь они задекорены ещё больше под "вкладки", чего нельзя сделать с обычным макетом prop'а с 'expand=True'.
        for li in [en for en in self.rna_type.properties['vaUiTabs'].enum_items]:
            col = rowTabs.row().column(align=True)
            col.operator(VoronoiAddonTabs.bl_idname, text=TranslateIface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
            #Теперь ещё больше похожи на вкладки:
            row = col.row(align=True)
            row.operator(VoronoiAddonTabs.bl_idname, text="", emboss=False)
            row.enabled = False
            row.scale_y = 0.05 #Если меньше, то ряд исчезнет (?), и угловатость пропадает.
        match self.vaUiTabs:
            case 'SETTINGS': self.DrawTabSettings(context, colLy)
            case 'DRAW':     self.DrawTabDraw    (context, colLy)
            case 'KEYMAP':   self.DrawTabKeymaps (context, colLy)

list_classes += [VoronoiAddonTabs, VoronoiAddonPrefs]

list_helpClasses = []

class TranslationHelper(): #Спасибо пользователю с ником "atticus-lv" за код для переводов на другие языки.
    def __init__(self, data={}, lang=''):
        self.name = voronoiAddonName+lang
        self.translations_dict = dict()
        for src, src_trans in data.items():
            self.translations_dict.setdefault(lang, {})[ ('Operator', src) ] = src_trans
            self.translations_dict.setdefault(lang, {})[ ('*',        src) ] = src_trans
    def register(self):
        try:
            bpy.app.translations.register(self.name, self.translations_dict)
        except:
            try:
                bpy.app.translations.unregister(self.name)
                bpy.app.translations.register(self.name, self.translations_dict)
            except:
                pass
    def unregister(self):
        bpy.app.translations.unregister(self.name)

def RegisterTranslations():
    for di in dict_translations:
        list_helpClasses.append(TranslationHelper( dict_translations[di], di ))
    for li in list_helpClasses:
        li.register()
def UnregisterTranslations():
    for li in list_helpClasses:
        li.unregister()

gapPrefs = None
def GetAddonProp(txt, inx=-1):
    tar = gapPrefs.bl_rna.properties[txt]
    if inx>-1:
        tar = getattr(tar,'enum_items')[inx]
    return tar
def GetAddonPropName(txt, inx=-1):
    return GetAddonProp(txt, inx).name
def GclToolSet(cls):
    return cls.bl_label+voronoiTextToolSettings
def GetAnnotNameFromClass(pcls, txt, kw=0):
    return pcls.__annotations__[txt].keywords['name' if kw==0 else 'description'] #Так вот где они прятались, в аннотациях. А я то уж потерял надежду; думал, вручную придётся.

dict_translations = {}

#todo0 когда настанет день X популярности, нужно будет переделать всю систему перевода VL, чтобы обслужить поток и повысить удобство. Что-то вроде словарь{свойство: словарь{язык:перевод, язык:перевод, ..}, ..}.

Gapn = GetAddonPropName
Ganfc = GetAnnotNameFromClass
def CollectTranslationDict(): #Превращено в функцию ради `Gapn()`, который требует регистрации 'VoronoiAddonPrefs'.
    global gapPrefs
    gapPrefs = Prefs()
    dict_translations['ru_RU'] = { #Последнее обновление для VL 4.0.0  #Автор перевода: автор аддона.
            bl_info['description']: "Разнообразные помогалочки для соединения нод, основанные на поле расстояний.",
            #Заметка для переводчиков: слова ниже в вашем языке уже могут быть переведены.
            #Заметка: оставить их для поддержки версий без них.
            "Virtual": "Виртуальный",
            "Restore": "Восстановить",
            "Add New": "Добавить", #Без слова "новый"; оно не влезает, слишком тесно.
            txt_vmtNoMixingOptions:                    "Варианты смешивания отсутствуют",
            txt_copySettAsPyScript:                    "Скопировать настройки аддона как '.py' скрипт",
            GetAddonProp('vaInfoRestore').description: "Этот список лишь копия из настроек. \"Восстановление\" восстановит всё, а не только аддон",
            #Tools:
            Gapn('vaGeneralBoxDiscl'):               "Настройки для всех инструментов:",
            GclToolSet(VoronoiLinkerTool):           f"Настройки инструмента {VoronoiLinkerTool.bl_label}:",
            GclToolSet(VoronoiPreviewTool):          f"Настройки инструмента {VoronoiPreviewTool.bl_label}:",
            GclToolSet(VoronoiMixerTool):            f"Настройки инструмента {VoronoiMixerTool.bl_label}:",
            GclToolSet(VoronoiQuickMathTool):        f"Настройки инструмента {VoronoiQuickMathTool.bl_label}:",
            GclToolSet(VoronoiRantoTool):            f"Настройки инструмента {VoronoiRantoTool.bl_label}:",
            GclToolSet(VoronoiHiderTool):            f"Настройки инструмента {VoronoiHiderTool.bl_label}:",
            GclToolSet(VoronoiMassLinkerTool):       f"Настройки инструмента {VoronoiMassLinkerTool.bl_label}:",
            GclToolSet(VoronoiEnumSelectorTool):     f"Настройки инструмента {VoronoiEnumSelectorTool.bl_label}:",
            GclToolSet(VoronoiLazyNodeStencilsTool): f"Настройки инструмента {VoronoiLazyNodeStencilsTool.bl_label}:",
            Gapn('vaAddonBoxDiscl'):                 "Аддон",
            #Draw:
            "Colored":                    "Цветной",
            Gapn('dsUniformColor'):       "Альтернативный постоянный цвет",
            Gapn('dsNodeColor'):          "Цвет рисования к ноду",
            Gapn('dsSocketAreaAlpha'):    "Прозрачность области сокета",
            Gapn('dsFontFile'):           "Файл шрифта",
            txt_onlyFontFormat:           "Только .ttf или .otf формат",
            Gapn('dsPointOffsetX'):       "Смещение точки по оси X",
            Gapn('dsFrameOffset'):        "Размер рамки",
            Gapn('dsFontSize'):           "Размер шрифта",
            Gapn('dsIsDrawSkArea'):       "Область сокета",
            Gapn('dsDisplayStyle'):       "Стиль отображения рамки",
                Gapn('dsDisplayStyle',0):     "Классический",
                Gapn('dsDisplayStyle',1):     "Упрощённый",
                Gapn('dsDisplayStyle',2):     "Только текст",
            Gapn('dsPointRadius'):        "Размер точки",
            Gapn('dsDistFromCursor'):     "Расстояние до текста от курсора",
            Gapn('dsIsAlwaysLine'):       "Всегда рисовать линию",
            Gapn('dsIsSlideOnNodes'):     "Скользить по нодам",
            Gapn('dsIsAllowTextShadow'):  "Включить тень текста",
            Gapn('dsShadowCol'):          "Цвет тени",
            Gapn('dsShadowOffset'):       "Смещение тени",
            Gapn('dsShadowBlur'):         "Размытие тени",
            Gapn('dsIsDrawDebug'):        "Отображать отладку",
            #Settings:
            Gapn('vEdgePanFac'):                    "Фактор панарамирования масштаба",
            Gapn('vPieType'):                       "Тип пирога",
                Gapn('vPieType',0):                     "Контроль",
                Gapn('vPieType',1):                     "Скорость",
            Gapn('vPieScale'):                      "Размер пирога",
            Gapn('vPieSocketDisplayType'):          "Отображение типа сокета",
            Gapn('vPieAlignment'):                  "Выравнивание между элементами",
            Gapn('vdsDrawNodeNameLabel'):           "Показывать текст для нода",
                Gapn('vdsDrawNodeNameLabel',1):          "Только имя",
                Gapn('vdsDrawNodeNameLabel',2):          "Только заголовок",
                Gapn('vdsDrawNodeNameLabel',3):          "Имя и заголовок",
            Gapn('vdsLabelSideRight'):              "Заголовок слева",
            ##
            Gapn('vlRepickKey'):                    "Клавиша перевыбора",
            Gapn('vlReroutesCanInAnyType'):         "Рероуты могут подключаться в любой тип",
            Gapn('vlDeselectAllNodes'):             "Снимать выделение со всех нодов при активации",
            Gapn('vlAnnoyingIgnoring'):             "Надоедливое игнорирование",
            Gapn('vlSelectingInvolved'):            "Вылелять задействованные ноды",
            Gapn('vpAllowClassicCompositorViewer'): "Разрешить классический Viewer Композитора",
            Gapn('vpAllowClassicGeoViewer'):        "Разрешить классический Viewer Геометрических узлов",
            Gapn('vpIsLivePreview'):                "Предпросмотр в реальном времени",
            Gapn('vpRvEeIsColorOnionNodes'):        "Луковичные цвета нод",
            Gapn('vpRvEeSksHighlighting'):          "Подсветка топологических соединений",
            Gapn('vpRvEeIsSavePreviewResults'):     "Сохранять результаты предпросмотра",
            Gapn('vmReroutesCanInAnyType'):         "Рероуты могут смешиваться с любым типом",
            Gapn('vqmIncludeThirdSk'):              "Разрешить третий сокет",
            Gapn('vrIsLiveRanto'):                  "Ranto в реальном времени",
            Gapn('vrIsIgnoreMuted'):                "Игнорировать выключенные линки",
            Gapn('vrIsRestoreMuted'):               "Восстанавливать выключенные линки",
            Gapn('vhHideBoolSocket'):               "Скрывать Boolean сокеты",
            Gapn('vhHideHiddenBoolSocket'):         "Скрывать скрытые Boolean сокеты",
                Gapn('vhHideBoolSocket',1):             "Если True",
                Gapn('vhHideBoolSocket',3):             "Если False",
            Gapn('vhNeverHideGeometry'):            "Никогда не скрывать входные сокеты геометрии",
                Gapn('vhNeverHideGeometry',1):          "Только первый",
            Gapn('vhIsUnhideVirtual'):              "Показывать виртуальные",
            Gapn('vhIsToggleNodesOnDrag'):          "Переключать ноды при ведении курсора",
            Gapn('vmlIgnoreCase'):                  "Игнорировать регистр",
            Gapn('vesIsInstantActivation'):         "Моментальная активация",
            Gapn('vesIsDrawEnumNames'):             "Рисовать имена свойств перечисления",
            Gapn('vesBoxScale'):                    "Масштаб панели",
            Gapn('vesDisplayLabels'):               "Отображать имена свойств перечислений",
            Gapn('vesDarkStyle'):                   "Тёмный стиль",
            Gapn('vwSelectTargetKey'):              "Клавиша выделения цели",
            Gapn('vlnsNonColorName'):               "Название \"Не-цветовых данных\"",
            Gapn('vlnsLastExecError'):              "Последняя ошибка выполнения",
            #Tool settings:
            Ganfc(VoronoiTool,'isPassThrough'):                   "Пропускать через выделение нода",
            Ganfc(VoronoiTool,'isPassThrough',1):                 "Клик над нодом активирует выделение, а не инструмент",
            Ganfc(VoronoiToolDblSk,'isCanBetweenFields'):         "Может между полями",
            Ganfc(VoronoiToolDblSk,'isCanBetweenFields',1):       "Инструменты могут соединяться между разными типами полей",
            Ganfc(VoronoiPreviewTool,'isSelectingPreviewedNode'): "Выделять предпросматриваемый нод",
            Ganfc(VoronoiPreviewTool,'isTriggerOnlyOnLink'):      "Триггериться только на связанные",
            Ganfc(VoronoiPreviewTool,'isEqualAnchorType'):        "Равный тип якоря",
            Ganfc(VoronoiPreviewAnchorTool,'isActiveAnchor'):     "Делать якорь активным",
            Ganfc(VoronoiPreviewAnchorTool,'isSelectAnchor'):     "Выделять якорь",
            Ganfc(VoronoiPreviewAnchorTool,'anchorType'):         "Тип якоря",
            Ganfc(VoronoiMixerTool,'isCanFromOne'):               "Может от одного сокета",
            Ganfc(VoronoiMixerTool,'isPlaceImmediately'):         "Размещать моментально",
            Ganfc(VoronoiQuickMathTool,'isHideOptions'):          "Скрывать опции нода",
            Ganfc(VoronoiQuickMathTool,'justCallPie'):            "Просто вызвать пирог",
            Ganfc(VoronoiQuickMathTool,'isRepeatLastOperation'):  "Повторить последнюю операцию",
            Ganfc(VoronoiQuickMathTool,'quickOprFloat'):          "Скаляр (быстро)",
            Ganfc(VoronoiQuickMathTool,'quickOprVector'):         "Вектор (быстро)",
            Ganfc(VoronoiQuickMathTool,'quickOprBool'):           "Логический (быстро)",
            Ganfc(VoronoiQuickMathTool,'quickOprColor'):          "Цвет (быстро)",
            Ganfc(VoronoiRantoTool,'isUniWid'):                   "Постоянная ширина",
            Ganfc(VoronoiRantoTool,'isOnlySelected'):             "Только выделенные",
            Ganfc(VoronoiRantoTool,'isUncollapseNodes'):          "Разворачивать ноды",
            Ganfc(VoronoiRantoTool,'isSelectNodes'):              "Выделять ноды",
            Ganfc(VoronoiRantoTool,'ndWidth'):                    "Ширина нод",
            Ganfc(VoronoiRantoTool,'indentX'):                    "Отступ по X",
            Ganfc(VoronoiRantoTool,'indentY'):                    "Отступ по Y",
            Ganfc(VoronoiSwapperTool,'isAddMode'):                "Режим добавления",
            Ganfc(VoronoiSwapperTool,'isIgnoreLinked'):           "Игнорировать связанные сокеты",
            Ganfc(VoronoiSwapperTool,'isCanAnyType'):             "Может меняться с любым типом",
            Ganfc(VoronoiHiderTool,'isHideSocket'):               "Режим сокрытия",
            Ganfc(VoronoiHiderTool,'isTriggerOnCollapsedNodes'):  "Триггериться на свёрнутые ноды",
            Ganfc(VoronoiMassLinkerTool,'isIgnoreExistingLinks'): "Игнорировать существующие связи",
            Ganfc(VoronoiEnumSelectorTool,'isToggleOptions'):     "Режим переключения опций нода",
            Ganfc(VoronoiEnumSelectorTool,'isPieChoice'):         "Выбор пирогом",
            Ganfc(VoronoiEnumSelectorTool,'isSelectNode'):        "Выделять целевой нод",
            Ganfc(VoronoiLinkRepeatingTool,'isAutoRepeatMode'):   "Режим авто-повторения",
            Ganfc(VoronoiLinkRepeatingTool,'isFromOut'):          "Из выхода",
            Ganfc(VoronoiLinksTransferTool,'isByOrder'):          "Переносить по порядку",
            Ganfc(VoronoiInterfacerTool,'mode'):                  "Режим",
            Ganfc(VoronoiWarperTool,'isZoomedTo'):                "Центрировать",
            Ganfc(VoronoiWarperTool,'isSelectReroutes'):          "Выделять рероуты",
            Ganfc(VoronoiResetNodeTool,'isResetEnums'):           "Восстанавливать перечисляемые свойства",
            Ganfc(VoronoiResetNodeTool,'isResetOnDrag'):          "Восстанавливать при ведении курсора",
            Ganfc(VoronoiResetNodeTool,'isSelectResetedNode'):    "Выделять восстановленный нод",
            }
    dict_translations['zh_CN'] = { #VL 4.0.0  #https://github.com/ugorek000/VoronoiLinker/issues/21
            bl_info['description']: "基于距离场的多种节点连接辅助工具。",
            "Virtual": "虚拟",
            "Restore": "恢复",
            "Add New": "添加",
            txt_vmtNoMixingOptions:                    "无混合选项",
            txt_copySettAsPyScript:                    "将插件设置复制为'.py'脚本,复制到粘贴板里",
            GetAddonProp('vaInfoRestore').description: "危险:“恢复”按钮将恢复整个快捷键里“节点编辑器”类中的所有设置,而不仅仅是恢复此插件!下面只显示本插件的快捷键。",
            #工具:
            Gapn('vaGeneralBoxDiscl'):               "通用设置:",
            GclToolSet(VoronoiLinkerTool):           f"{VoronoiLinkerTool.bl_label}快速连接设置:",
            GclToolSet(VoronoiPreviewTool):          f"{VoronoiPreviewTool.bl_label}快速预览设置:",
            GclToolSet(VoronoiMixerTool):            f"{VoronoiMixerTool.bl_label}快速混合设置:",
            GclToolSet(VoronoiQuickMathTool):        f"{VoronoiQuickMathTool.bl_label}快速数学运算设置:",
            GclToolSet(VoronoiRantoTool):            f"{VoronoiRantoTool.bl_label}节点自动排布对齐工具设置:",
            GclToolSet(VoronoiHiderTool):            f"{VoronoiHiderTool.bl_label}快速隐藏端口设置:",
            GclToolSet(VoronoiMassLinkerTool):       f"{VoronoiMassLinkerTool.bl_label}根据端口名批量连接设置:",
            GclToolSet(VoronoiEnumSelectorTool):     f"{VoronoiEnumSelectorTool.bl_label}快速显示节点里下拉列表设置:",
            GclToolSet(VoronoiLazyNodeStencilsTool): f"{VoronoiLazyNodeStencilsTool.bl_label}快速添加纹理设置:(代替NodeWrangler的ctrl+t):",
            Gapn('vaAddonBoxDiscl'):                 "插件",
            #绘制:
            "Colored": "根据端点类型自动设置颜色:",
            Gapn('dsUniformColor'):       "自定义轮选时端口的颜色",
            Gapn('dsNodeColor'):          "动态选择节点时标识的颜色(显示下拉列表时)",
            Gapn('dsSocketAreaAlpha'):    "端口区域的透明度",
            Gapn('dsFontFile'):           "字体文件",
            txt_onlyFontFormat:           "只支持.ttf或.otf格式",
            Gapn('dsPointOffsetX'):       "X轴上的点偏移",
            Gapn('dsFrameOffset'):        "边框大小",
            Gapn('dsFontSize'):           "字体大小",
            Gapn('dsIsDrawSkArea'):       "高亮显示选中端口",
            Gapn('dsDisplayStyle'):       "边框显示样式",
                Gapn('dsDisplayStyle',0):     "经典",
                Gapn('dsDisplayStyle',1):     "简化",
                Gapn('dsDisplayStyle',2):     "仅文本",
            Gapn('dsPointRadius'):        "点的大小",
            Gapn('dsDistFromCursor'):     "到文本的距离",
            Gapn('dsIsAlwaysLine'):       "始终绘制线条(在鼠标移动到移动到已有连接端口的时是否还显示连线)",
            Gapn('dsIsSlideOnNodes'):     "在节点上滑动",
            Gapn('dsIsAllowTextShadow'):  "启用文本阴影",
            Gapn('dsShadowCol'):          "阴影颜色",
            Gapn('dsShadowOffset'):       "阴影偏移",
            Gapn('dsShadowBlur'):         "阴影模糊",
            Gapn('dsIsDrawDebug'):        "显示调试信息",
            #设置:
            Gapn('vEdgePanFac'):                    "边缘平移缩放系数",
            Gapn('vPieType'):                       "饼菜单类型",
                Gapn('vPieType',0):                     "控制(自定义)",
                Gapn('vPieType',1):                     "速度型(多层菜单)",
            Gapn('vPieScale'):                      "饼菜单大小",
            Gapn('vPieSocketDisplayType'):          "显示端口类型",
            Gapn('vPieAlignment'):                  "元素对齐方式",
            Gapn('vdsDrawNodeNameLabel'):           "显示节点标签",
                Gapn('vdsDrawNodeNameLabel',1):         "仅名称",
                Gapn('vdsDrawNodeNameLabel',2):         "仅标题",
                Gapn('vdsDrawNodeNameLabel',3):         "名称和标题",
            Gapn('vdsLabelSideRight'):              "标签显示在右边",
            ##
            Gapn('vlRepickKey'):                    "重选快捷键",
            Gapn('vlReroutesCanInAnyType'):         "重新定向节点可以连接到任何类型的节点",
            Gapn('vlDeselectAllNodes'):             "快速连接时取消选择所有节点",
            Gapn('vlAnnoyingIgnoring'):             "烦人的忽略",
            Gapn('vlSelectingInvolved'):            "快速连接后自动选择连接的节点",
            Gapn('vpAllowClassicCompositorViewer'): "合成器里使用默认预览方式(默认是按顺序轮选输出接口端无法直选第N个通道接口)",
            Gapn('vpAllowClassicGeoViewer'):        "几何节点里使用默认预览方式",
            Gapn('vpIsLivePreview'):                "实时预览(即使没松开鼠标也能观察预览结果)",
            Gapn('vpRvEeIsColorOnionNodes'):        "快速预览时将与预览的节点有连接关系的节点全部着色显示",
            Gapn('vpRvEeSksHighlighting'):          "快速预览时高亮显示连接到预览的节点的上级节点的输出端口",
            Gapn('vpRvEeIsSavePreviewResults'):     "保存预览结果,通过新建一个预览节点连接预览",
            Gapn('vmReroutesCanInAnyType'):         "快速混合不限定端口类型",
            Gapn('vqmIncludeThirdSk'):              "包括第三个端口",
            Gapn('vrIsLiveRanto'):                  "实时对齐",#？？工具还没完成
            Gapn('vrIsIgnoreMuted'):                "忽略禁用的链接",#？？工具还没完成
            Gapn('vrIsRestoreMuted'):               "恢复禁用的链接",#？？工具还没完成
            Gapn('vhHideBoolSocket'):               "隐藏布尔端口",
            Gapn('vhHideHiddenBoolSocket'):         "隐藏已隐藏的布尔端口",
                Gapn('vhHideBoolSocket',1):             "如果为True",
                Gapn('vhHideBoolSocket',3):             "如果为False",
            Gapn('vhNeverHideGeometry'):            "永不隐藏几何输入端口",
                Gapn('vhNeverHideGeometry',1):          "仅第一个端口",
            Gapn('vhIsUnhideVirtual'):              "显示虚拟端口",
            Gapn('vhIsToggleNodesOnDrag'):          "移动光标时切换节点",
            Gapn('vmlIgnoreCase'):                  "忽略端口名称的大小写",
            Gapn('vesIsInstantActivation'):         "直接打开饼菜单(不勾选可以先根据鼠标位置动态选择节点)",
            Gapn('vesIsDrawEnumNames'):             "动态选择节点时显示节点里下拉列表属性名称",
            Gapn('vesBoxScale'):                    "下拉列表面板大小",
            Gapn('vesDisplayLabels'):               "显示下拉列表属性名称",
            Gapn('vesDarkStyle'):                   "暗色风格",
            Gapn('vwSelectTargetKey'):              "选择目标快捷键",
            Gapn('vlnsNonColorName'):               "图片纹理色彩空间名称",
            Gapn('vlnsLastExecError'):              "上次运行时错误",
            #工具设置:
            Ganfc(VoronoiTool,'isPassThrough'):                   "单击输出端口预览(而不是自动根据鼠标位置自动预览)",
            Ganfc(VoronoiTool,'isPassThrough',1):                 "单击输出端口才连接预览而不是根据鼠标位置动态预览",#上面一个选项的说明翻译
            Ganfc(VoronoiToolDblSk,'isCanBetweenFields'):         "端口类型可以不一样",
            Ganfc(VoronoiToolDblSk,'isCanBetweenFields',1):       "工具可以连接不同类型的端口",
            Ganfc(VoronoiPreviewTool,'isSelectingPreviewedNode'): "自动选择被预览的节点",
            Ganfc(VoronoiPreviewTool,'isTriggerOnlyOnLink'):      "只预览已有连接的输出端口",
            Ganfc(VoronoiPreviewTool,'isEqualAnchorType'):        "切换Voronoi_Anchor转接点预览时,只有类型和当前预览的端口类型一样才能被预览连接",
            Ganfc(VoronoiPreviewAnchorTool,'isActiveAnchor'):     "转接点设置为活动项",
            Ganfc(VoronoiPreviewAnchorTool,'isSelectAnchor'):     "转接点高亮显示",
            Ganfc(VoronoiPreviewAnchorTool,'anchorType'):         "转接点的类型",#Voronoi_Anchor转接点显示类型，0和1是两种显示类型，-1是删除所有Voronoi_Anchor转接点转接点
            Ganfc(VoronoiMixerTool,'isCanFromOne'):               "从一个端口连接",
            Ganfc(VoronoiMixerTool,'isPlaceImmediately'):         "立即添加节点到鼠标位置",
            Ganfc(VoronoiQuickMathTool,'isHideOptions'):          "隐藏节点选项",
            Ganfc(VoronoiQuickMathTool,'justCallPie'):            "仅调用饼图",
            Ganfc(VoronoiQuickMathTool,'isRepeatLastOperation'):  "重复上一操作",
            Ganfc(VoronoiQuickMathTool,'quickOprFloat'):          "浮点（快速）",
            Ganfc(VoronoiQuickMathTool,'quickOprVector'):         "矢量（快速）",
            Ganfc(VoronoiQuickMathTool,'quickOprBool'):           "布尔（快速）",
            Ganfc(VoronoiQuickMathTool,'quickOprColor'):          "颜色（快速）",
            Ganfc(VoronoiRantoTool,'isUniWid'):                   "统一宽度",
            Ganfc(VoronoiRantoTool,'isOnlySelected'):             "仅选定的",
            Ganfc(VoronoiRantoTool,'isUncollapseNodes'):          "展开节点",
            Ganfc(VoronoiRantoTool,'isSelectNodes'):              "选择节点",
            Ganfc(VoronoiRantoTool,'ndWidth'):                    "节点宽度",
            Ganfc(VoronoiRantoTool,'indentX'):                    "X缩进",
            Ganfc(VoronoiRantoTool,'indentY'):                    "Y缩进",
            Ganfc(VoronoiSwapperTool,'isAddMode'):                "添加模式(不修改新端口已有的连接)",
            Ganfc(VoronoiSwapperTool,'isIgnoreLinked'):           "忽略已连接的端口",
            Ganfc(VoronoiSwapperTool,'isCanAnyType'):             "可以与任何类型交换",
            Ganfc(VoronoiHiderTool,'isHideSocket'):               "端口隐藏模式",
            Ganfc(VoronoiHiderTool,'isTriggerOnCollapsedNodes'):  "仅触发已折叠节点",
            Ganfc(VoronoiMassLinkerTool,'isIgnoreExistingLinks'): "忽略现有链接",
            Ganfc(VoronoiEnumSelectorTool,'isToggleOptions'):     "隐藏节点里的下拉列表",
            Ganfc(VoronoiEnumSelectorTool,'isPieChoice'):         "饼菜单选择",
            Ganfc(VoronoiEnumSelectorTool,'isSelectNode'):        "选择目标节点",
            Ganfc(VoronoiLinkRepeatingTool,'isAutoRepeatMode'):   "自动恢复连接模式(鼠标移动到节点旁自动恢复节点的连接)",
            Ganfc(VoronoiLinkRepeatingTool,'isFromOut'):          "从输出端处",#？？？
            Ganfc(VoronoiLinksTransferTool,'isByOrder'):          "按顺序传输",
            Ganfc(VoronoiInterfacerTool,'mode'):                  "模式",
            Ganfc(VoronoiWarperTool,'isZoomedTo'):                "自动最大化显示",
            Ganfc(VoronoiWarperTool,'isSelectReroutes'):          "选择更改路线",
            Ganfc(VoronoiResetNodeTool,'isResetEnums'):           "恢复下拉列表里的选择",
            Ganfc(VoronoiResetNodeTool,'isResetOnDrag'):          "悬停时恢复",
            Ganfc(VoronoiResetNodeTool,'isSelectResetedNode'):    "选择重置的节点",
            #Quick Mix and Math Pie Menu Titles快速混合和运算饼菜单上的标题
            "Float Quick Math":                                  "快速浮点运算",
            "Vector Quick Math":                                 "快速矢量运算",
            "Boolean Quick Math":                                "快速布尔运算",
            "Color Quick Mode":                                  "快速颜色运算",
            #Translation shortcut key setting page设置快捷键页面名称
            "Voronoi Linker":                                    "Voronoi快速连接",
            "Voronoi Preview":                                   "Voronoi快速预览",
            "Voronoi Mixer":                                     "Voronoi快速混合",
            "Voronoi Quick Math":                                "Voronoi快速数学运算",
            "Voronoi RANTO":                                     "Voronoi节点自动排布对齐",
            "Voronoi Preview Anchor":                            "Voronoi新建预览转接点",
            "Voronoi Swapper":                                   "Voronoi快速替换端口(Alt是批量替换输出端口,Shift是互换端口)",
            "Voronoi Hider":                                     "Voronoi快速隐藏(Shift是自动隐藏数值为0/颜色纯黑/未连接的端口,Ctrl是单个隐藏端口)",
            "Voronoi MassLinker":                                "Voronoi根据端口名批量快速连接",
            "Voronoi Enum Selector":                             "Voronoi快速切换节点内部下拉列表",
            "Voronoi Link Repeating":                            "Voronoi快速恢复连接",
            "Voronoi Repeating":                                 "Voronoi重复连接到上次用快速连接到的输出端",
            "Voronoi Quick Dimensions":                          "Voronoi快速分离/合并 矢量/颜色",
#            "Voronoi Interfacer":                                "Voronoi在节点组里快速复制粘贴端口名给节点组输入输出端",
            "Voronoi Links Transfer":                            "Voronoi链接按输入端类型切换到别的端口",
            "Voronoi Warper":                                    "Voronoi快速聚焦某条连接",
            "Voronoi Lazy Node Stencils":                        "Voronoi在输入端快速节点(代替NodeWrangler的ctrl+t)",
            "Voronoi Reset Node":                                "Voronoi快速恢复节点默认参数",
            }
    dict_translations['zh_HANS'] = dict_translations['zh_CN']
    return
    #Ждёт своего часа. Кто же будет вторым?
    dict_translations['aa_AA'] = { #Последнее обновление для VL _._._  #Автор перевода: .
            bl_info['description']:  "",
            "Virtual":               "",
            "Restore":               "",
            #...
            }

list_addonKeymaps = []

newKeyMapNodeEditor = None

avaiTran = 'CollectTranslationDict' in globals() #Дебагное.
avaiKmiDis = 'VoronoiRantoTool' in globals()

def register():
    for li in list_classes:
        bpy.utils.register_class(li)
    ##
    prefs = Prefs()
    prefs.vlnsLastExecError = ""
    ##
    global newKeyMapNodeEditor
    newKeyMapNodeEditor = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for blId, key, shift, ctrl, alt, isRep, dict_props in list_kmiDefs:
        kmi = newKeyMapNodeEditor.keymap_items.new(idname=blId, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=isRep)
        if avaiKmiDis:
            kmi.active = blId!=VoronoiRantoTool.bl_idname
        if dict_props:
            for di in dict_props:
                setattr(kmi.properties, di, dict_props[di])
        list_addonKeymaps.append(kmi)
    ##
    if avaiTran:
        CollectTranslationDict()
        RegisterTranslations()
def unregister():
    for li in reversed(list_classes):
        bpy.utils.unregister_class(li)
    ##
    global newKeyMapNodeEditor
    for li in list_addonKeymaps:
        newKeyMapNodeEditor.keymap_items.remove(li)
    list_addonKeymaps.clear()
    ##
    if avaiTran:
        UnregisterTranslations()


#Мой гит в bl_info, это конечно же, круто, однако было бы неплохо иметь ещё и явно указанные способы связи:
#  coaltangle@gmail.com
#  ^ Моя почта. Если вдруг случится апокалипсис, или эта VL-археологическая-находка сможет решить не-полиномиальную задачу, то писать туда.
# Для более реалтаймового общения (предпочтительно) и по вопросам о VL и его коде пишите на мой дискорд 'ugorek#6434' (https://discordapp.com/users/275627322424688651).

def DisableKmis(): #Для повторных запусков скрипта. Работает до первого "Restore".
    kmUNe = GetUserKmNe()
    for li, *oi in list_kmiDefs:
        for kmiCon in kmUNe.keymap_items:
            if li==kmiCon.idname:
                kmiCon.active = False #Это удаляет дубликаты. Хак?
                kmiCon.active = True #Вернуть обратно, если оригинал.
if __name__=="__main__":
    DisableKmis() #Кажется не важно в какой очерёдности вызывать, перед или после добавления хоткеев.
    register()
