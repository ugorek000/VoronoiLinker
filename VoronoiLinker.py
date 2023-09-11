# !!! Disclaimer: Use the contents of this file at your own risk !!!
# 100% of the content of this file contains malicious code!!1

# !!! Отказ от ответственности: Содержимое этого файла полностью является случайно сгенерированными битами, включая этот дисклеймер тоже.
# Используйте этот файл на свой страх и риск.

#Этот аддон создавался мной как самопис лично для меня и под меня; который я сделал публичным для всех желающих, ибо результат получился потрясающий. Наслаждайтесь.

#P.s. В гробу я видал шатанину с лицензиями; так что любуйтесь предупреждениями о вредоносном коде (о да он тут есть, иначе накой смысол?).

bl_info = {'name':"Voronoi Linker", 'author':"ugorek",
           'version':(3,0,3), 'blender':(3,6,2), #2023.09.11
           'description':"Various utilities for nodes connecting, based on a distance field.", 'location':"Node Editor > Alt + RMB",
           'warning':"", 'category':"Node",
           'wiki_url':"https://github.com/ugorek000/VoronoiLinker/wiki", 'tracker_url':"https://github.com/ugorek000/VoronoiLinker/issues"}

from builtins import len as length #Невозможность использования мобильной трёхбуквенной переменной с именем "len", мягко говоря.. не удобно.
import bpy, blf, gpu, gpu_extras.batch
#С модулем gpu_extras какая-то чёрная магия творится. Просто так его импортировать, чтобы использовать "gpu_extras.batch.batch_for_shader()" -- не работает.
#А с импортом 'batch' использование 'batch.batch_for_shader()' -- тоже не работает. Неведомые мне нано-технологии.
from math import pi, inf, sin, cos, copysign
import mathutils

#def Vector(*data): return mathutils.Vector(data[0] if length(data)<2 else data)
def Vector(*args): return mathutils.Vector((args)) #Очень долго я охреневал от двойных скобок 'Vector((a,b))', и только сейчас допёр так сделать. Ну наконец-то настанет наслаждение.
#def Vectorq(seq): return mathutils.Vector(seq)

voronoiAddonName = bl_info['name'].replace(" ","") #todo узнать разницу между названием аддона, именем аддона, именем файла, именем модуля; и ещё в установленных посмотреть.

#Текст ниже не переводится на другие языки. Потому что забыл. И нужно ли?.
voronoiAnchorName = "Voronoi_Anchor"
voronoiSkPreviewName = "voronoi_preview"
voronoiPreviewResultNdName = "SavePreviewResult"

list_classes = []
list_kmiDefs = []

def TranslateIface(txt):
    return bpy.app.translations.pgettext_iface(txt)
def UiScale():
    return bpy.context.preferences.system.dpi/72
def GetSkCol(sk): #Про `NodeSocketUndefined` см. |2|. Сокеты от потерянных деревьев не имеют 'draw_color()'.
    return sk.draw_color(bpy.context, sk.node) if sk.bl_idname!='NodeSocketUndefined' else (1.0, 0.2, 0.2, 1.0)

def PowerArr4ToVec(arr, pw):
    return Vector(arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)

def GetSkColPowVec(sk, pw):
    return PowerArr4ToVec(GetSkCol(sk), pw)
def GetUniformColVec(self):
    return PowerArr4ToVec(self.dsUniformColor, 1/2.2)

def VecWorldToRegScale(vec, self):
    vec = vec.copy()*self.uiScale
    return mathutils.Vector( bpy.context.region.view2d.view_to_region(vec.x, vec.y, clip=False) )

def RecrGetNodeFinalLoc(nd):
    return nd.location+RecrGetNodeFinalLoc(nd.parent) if nd.parent else nd.location

def SkBetweenCheck(sk):
    return sk.type in ('VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN')


def AddToKmiDefs(cls, keys, dict_props={}): #На вкладке "keymap" порядок отображается в обратном порядке вызовов AddToKmiDefs() с одинаковыми `cls`.
    global list_kmiDefs #Понятия не имею почему без этого не может.
    list_kmiDefs += [ (cls.bl_idname, keys[:-4], keys[-3]=="S", keys[-2]=="C", keys[-1]=="A", dict_props) ]
def AddToRegAndAddToKmiDefs(cls, keys, dict_props={}):
    global list_classes #И тут тоже.
    list_classes.append(cls)
    AddToKmiDefs(cls, keys, dict_props={})

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
def PrepareShaders(self):
    self.gpuLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    self.gpuArea = gpu.shader.from_builtin('UNIFORM_COLOR')
    #Параметры, которые не нужно устанавливать каждый раз:
    self.gpuLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
    #todo выяснить как или сделать сглаживание для полигонов тоже.
    #self.gpuLine.uniform_float('lineSmooth', True) #Нет нужды, по умолчанию True.

#"Низкоуровневое" рисование:
def DrawLine(self, pos1, pos2, siz=1, col1=(1.0, 1.0, 1.0, 0.75), col2=(1.0, 1.0, 1.0, 0.75)):
    DrawWay(self, (pos1,pos2), (col1,col2), siz)
def DrawStick(self, pos1, pos2, col1, col2):
    DrawLine(self, VecWorldToRegScale(pos1, self), VecWorldToRegScale(pos2, self), self.dsLineWidth, col1, col2)
def DrawRing(self, pos, rd, siz=1, col=(1.0, 1.0, 1.0, 0.75), rotation=0.0, resolution=16):
    vpos = [];  vcol = []
    for cyc in range(resolution+1):
        vpos.append( (rd*cos(cyc*2*pi/resolution+rotation)+pos[0], rd*sin(cyc*2*pi/resolution+rotation)+pos[1]) )
        vcol.append(col)
    DrawWay(self, vpos, vcol, siz)
def DrawCircle(self, pos, rd, col=(1.0, 1.0, 1.0, 0.75), resolution=54):
    #Первая вершина гордо в центре круга, остальные по кругу. Нужно было чтобы артефакты сглаживания были красивыми в центр, а не наклонёнными в куда-то бок.
    vpos = ( (pos[0],pos[1]), *( (rd*cos(i*2.0*pi/resolution)+pos[0], rd*sin(i*2.0*pi/resolution)+pos[1]) for i in range(resolution+1) ) )
    DrawAreaFan(self, vpos, col)
def DrawRectangle(self, pos1, pos2, col):
    DrawAreaFan(self, ( (pos1[0],pos1[1]), (pos2[0],pos1[1]), (pos2[0],pos2[1]), (pos1[0],pos2[1]) ), col)

#"Высокоуровневое" рисование:
def DrawSocketArea(self, sk, list_boxHeiBou, colfac=Vector(1.0, 1.0, 1.0, 1.0)):
    loc = RecrGetNodeFinalLoc(sk.node)
    pos1 = VecWorldToRegScale( Vector(loc.x, list_boxHeiBou[0]), self )
    pos2 = VecWorldToRegScale( Vector(loc.x+sk.node.width, list_boxHeiBou[1]), self )
    colfac = colfac if self.dsIsColoredSkArea else GetUniformColVec(self)
    DrawRectangle(self, pos1, pos2, Vector(1.0, 1.0, 1.0, self.dsSocketAreaAlpha)*colfac)
def DrawIsLinkedMarker(self, loc, ofs, skCol):
    ofs[0] += ( (20*self.dsIsDrawSkText+self.dsDistFromCursor)*1.5+self.dsFrameOffset )*copysign(1,ofs[0])+4
    vec = VecWorldToRegScale(loc, self)
    skCol = skCol if self.dsIsColoredMarker else GetUniformColVec(self)
    grayCol = 0.65
    col1 = (0.0, 0.0, 0.0, 0.5) #Тень
    col2 = (grayCol, grayCol, grayCol, max(max(skCol[0],skCol[1]),skCol[2])*0.9/2) #Прозрачная белая обводка
    col3 = (skCol[0], skCol[1], skCol[2], 0.925) #Цветная основа
    def DrawMarkerBacklight(tgl, res=16):
        rot = pi/res if tgl else 0.0
        DrawRing( self, (vec[0]+ofs[0],     vec[1]+5.0+ofs[1]), 9.0, 3, col2, rot, res )
        DrawRing( self, (vec[0]+ofs[0]-5.0, vec[1]-3.5+ofs[1]), 9.0, 3, col2, rot, res )
    DrawRing( self, (vec[0]+ofs[0]+1.5, vec[1]+3.5+ofs[1]), 9.0, 3, col1)
    DrawRing( self, (vec[0]+ofs[0]-3.5, vec[1]-5.0+ofs[1]), 9.0, 3, col1)
    DrawMarkerBacklight(True) #Маркер рисуется с артефактами "дырявых пикселей". Закостылить их дублированной отрисовкой с вращением.
    DrawMarkerBacklight(False) #Но из-за этого нужно уменьшить альфу белой обводки в два раза.
    DrawRing( self, (vec[0]+ofs[0],     vec[1]+5.0+ofs[1]), 9.0, 1, col3)
    DrawRing( self, (vec[0]+ofs[0]-5.0, vec[1]-3.5+ofs[1]), 9.0, 1, col3)
def DrawWidePoint(self, loc, colfac=Vector(1.0, 1.0, 1.0, 1.0), resolution=54, forciblyCol=False): #"forciblyCol" нужен только для DrawDebug'а.
    #Подготовка:
    pos = VecWorldToRegScale(loc, self)
    loc = Vector(loc.x+6*self.dsPointRadius*1000, loc.y) #Радиус точки вычисляется через мировое пространство. Единственный из двух, кто зависит от зума в редакторе. Второй -- коробка-подсветка сокетов.
    #Умножается и делится на 1000, чтобы радиус не прилипал к целым числам и тем самым был красивее. Конвертация в экранное пространство даёт только целочисленный результат.
    rd = (VecWorldToRegScale(loc, self)[0]-pos[0])/1000
    #Рисование:
    col1 = Vector(0.5, 0.5, 0.5, 0.4)
    col2 = col1
    col3 = Vector(1.0, 1.0, 1.0, 1.0)
    colfac = colfac if (self.dsIsColoredPoint)or(forciblyCol) else GetUniformColVec(self)
    rd = (rd*rd+10)**0.5
    DrawCircle(self, pos, rd+3.0, col1*colfac, resolution)
    DrawCircle(self, pos, rd,     col2*colfac, resolution)
    DrawCircle(self, pos, rd/1.5, col3*colfac, resolution)
def DrawText(self, pos, ofs, txt, drawCol, fontSizeOverwrite=0):
    if self.dsIsAllowTextShadow:
        blf.enable(self.fontId, blf.SHADOW)
        muv = self.dsShadowCol
        blf.shadow(self.fontId, (0, 3, 5)[self.dsShadowBlur], muv[0], muv[1], muv[2], muv[3])
        muv = self.dsShadowOffset
        blf.shadow_offset(self.fontId, muv[0], muv[1])
    else: #Большую часть времени бесполезно, но нужно использовать, когда опция рисования тени переключается.
        blf.disable(self.fontId, blf.SHADOW)
    frameOffset = self.dsFrameOffset
    blf.size(self.fontId, self.dsFontSize*(not fontSizeOverwrite)+fontSizeOverwrite)
    #От "текста по факту" не вычисляется, потому что тогда каждая рамка каждый раз будет разной высоты в зависимости от текста.
    #Спецсимвол нужен, как общий случай, чтобы покрыть максимальную высоту. Остальные символы нужны для особых шрифтов, что могут быть выше чем █.
    #Но этого недостаточно, некоторые буквы некоторых шрифтов могут вылезти за рамку. Это не чинится, ибо изначально всё было вылизано и отшлифовано для Consolas.
    #И если починить это для всех шрифтов, то тогда рамка для Consolas'а потеряет красоту.
    #P.s. Consolas -- мой самый любимый шрифт после Comic Sans.
    #Если вы хотите тру-центрирование -- сделайте это сами.
    txtDim = (blf.dimensions(self.fontId, txt)[0], blf.dimensions(self.fontId, "█GJKLPgjklp!?")[1])
    pos = VecWorldToRegScale(pos, self)
    pos = ( pos[0]-(txtDim[0]+frameOffset+10)*(ofs[0]<0)+(frameOffset+1)*(ofs[0]>-1), pos[1]+frameOffset )
    pw = 1/1.975 #Осветлить текст. Почему 1.975 -- не помню.
    placePosY = round( (txtDim[1]+frameOffset*2)*ofs[1] ) #Без округления красивость горизонтальных линий пропадет.
    pos1 = (pos[0]+ofs[0]-frameOffset,              pos[1]+placePosY-frameOffset)
    pos2 = (pos[0]+ofs[0]+10+txtDim[0]+frameOffset, pos[1]+placePosY+txtDim[1]+frameOffset)
    gradientResolution = 12
    girderHeight = 1/gradientResolution*(txtDim[1]+frameOffset*2)
    #Рамка для текста
    if self.dsDisplayStyle=='CLASSIC': #Красивая рамка
        #Прозрачный фон:
        def Fx(x, a, b):
            return ((x+b)/(b+1))**0.6*(1-a)+a
        for cyc in range(gradientResolution):
            DrawRectangle(self, (pos1[0], pos1[1]+cyc*girderHeight), (pos2[0], pos1[1]+cyc*girderHeight+girderHeight), (drawCol[0]/2, drawCol[1]/2, drawCol[2]/2, Fx(cyc/gradientResolution,0.2,0.05)) )
        #Яркая основная обводка:
        col = (drawCol[0]**pw, drawCol[1]**pw, drawCol[2]**pw, 1.0)
        DrawLine( self,       pos1,        (pos2[0],pos1[1]), 1, col, col)
        DrawLine( self, (pos2[0],pos1[1]),        pos2,       1, col, col)
        DrawLine( self,       pos2,        (pos1[0],pos2[1]), 1, col, col)
        DrawLine( self, (pos1[0],pos2[1]),        pos1,       1, col, col)
        #Мягкая дополнительная обводка, придающая красоты:
        col = (col[0], col[1], col[2], 0.375)
        lineOffset = 2.0
        DrawLine( self, (pos1[0], pos1[1]-lineOffset), (pos2[0], pos1[1]-lineOffset), 1, col, col )
        DrawLine( self, (pos2[0]+lineOffset, pos1[1]), (pos2[0]+lineOffset, pos2[1]), 1, col, col )
        DrawLine( self, (pos2[0], pos2[1]+lineOffset), (pos1[0], pos2[1]+lineOffset), 1, col, col )
        DrawLine( self, (pos1[0]-lineOffset, pos2[1]), (pos1[0]-lineOffset, pos1[1]), 1, col, col )
        #Уголки. Их маленький размер -- маскировка под тру-скругление:
        DrawLine( self, (pos1[0]-lineOffset, pos1[1]), (pos1[0], pos1[1]-lineOffset), 1, col, col )
        DrawLine( self, (pos2[0]+lineOffset, pos1[1]), (pos2[0], pos1[1]-lineOffset), 1, col, col )
        DrawLine( self, (pos2[0]+lineOffset, pos2[1]), (pos2[0], pos2[1]+lineOffset), 1, col, col )
        DrawLine( self, (pos1[0]-lineOffset, pos2[1]), (pos1[0], pos2[1]+lineOffset), 1, col, col )
    elif self.dsDisplayStyle=='SIMPLIFIED': #Упрощённая рамка. Создана ради нытиков с гипертрофированным чувством дизайнерской эстетики; я вас не понимаю.
        DrawRectangle( self, (pos1[0], pos1[1]), (pos2[0], pos2[1]), (drawCol[0]/2.4, drawCol[1]/2.4, drawCol[2]/2.4, 0.8) )
        col = (0.1, 0.1, 0.1, 0.95)
        DrawLine( self,       pos1,        (pos2[0],pos1[1]), 2, col, col)
        DrawLine( self, (pos2[0],pos1[1]),        pos2,       2, col, col)
        DrawLine( self,       pos2,        (pos1[0],pos2[1]), 2, col, col)
        DrawLine( self, (pos1[0],pos2[1]),        pos1,       2, col, col)
    #Сам текст:
    blf.position(self.fontId, pos[0]+ofs[0]+3.5, pos[1]+placePosY+txtDim[1]*0.3, 0)
    blf.color(   self.fontId, drawCol[0]**pw, drawCol[1]**pw, drawCol[2]**pw, 1.0)
    blf.draw(    self.fontId, txt)
    return (txtDim[0]+frameOffset, txtDim[1]+frameOffset*2)
def DrawSkText(self, pos, ofs, fgSk, fontSizeOverwrite=0):
    if not self.dsIsDrawSkText:
        return [1, 0] #"1" нужен для сохранения информации для направления для позиции маркеров
    skCol = GetSkCol(fgSk.tg) if self.dsIsColoredSkText else GetUniformColVec(self)
    txt = fgSk.name if fgSk.tg.bl_idname!='NodeSocketVirtual' else TranslateIface('Virtual')
    return DrawText(self, pos, ofs, txt, skCol, fontSizeOverwrite)


#Шаблоны:
def DrawDoubleNone(self, context):
    cusorPos = context.space_data.cursor_location
    col = Vector(1, 1, 1, 1) if self.dsIsColoredPoint else GetUniformColVec(self)
    vec = Vector(self.dsPointOffsetX*0.75, 0)
    if (self.dsIsDrawLine)and(self.dsIsAlwaysLine):
        DrawStick( self, cusorPos-vec, cusorPos+vec, col, col )
    if self.dsIsDrawPoint:
        DrawWidePoint(self, cusorPos-vec, col)
        DrawWidePoint(self, cusorPos+vec, col)
def CallbackDrawEditTreeIsNone(self, context): #Именно. Ибо эстетика. Вдруг пользователь потеряется; нужно подать признаки жизни.
    if StartDrawCallbackStencil(self, context):
        return
    if self.dsIsDrawPoint:
        cusorPos = context.space_data.cursor_location
        if getattr(self,'isDrawTwoPoints', False):
            DrawDoubleNone(self, context)
        else:
            DrawWidePoint(self, cusorPos)

def DrawDebug(self, context):
    def DebugTextDraw(pos, txt, r, g, b):
        blf.size(0,18);  blf.position(0, pos[0]+10,pos[1], 0);  blf.color(0, r,g,b,1.0);  blf.draw(0, txt)
    cusorPos = context.space_data.cursor_location
    DebugTextDraw(VecWorldToRegScale(cusorPos, self), "Cursor position here.", 1, 1, 1)
    if not context.space_data.edit_tree:
        return
    list_nodes = GetNearestNodes(context.space_data.edit_tree.nodes, cusorPos)
    col = Vector(1, 0.5, 0.5, 1)
    DrawStick( self, cusorPos, list_nodes[0].pos, col, col )
    sco = 0
    for li in list_nodes:
        DrawWidePoint(self, li.pos, col, 4, True)
        DebugTextDraw( VecWorldToRegScale(li.pos, self), str(sco)+" Node goal here", col.x, col.y, col.z )
        sco += 1
    list_fgSksIn, list_fgSksOut = GetNearestSockets(list_nodes[0].tg, cusorPos)
    if list_fgSksIn:
        DrawWidePoint( self, list_fgSksIn[0].pos, Vector(0.5, 1, 0.5, 1), 4, True )
        DebugTextDraw( VecWorldToRegScale(list_fgSksIn[0].pos, self), "Nearest socketIn here", 0.5, 1, 0.5)
    if list_fgSksOut:
        DrawWidePoint( self, list_fgSksOut[0].pos, Vector(0.5, 0.5, 1, 1), 4, True )
        DebugTextDraw( VecWorldToRegScale(list_fgSksOut[0].pos, self), "Nearest socketOut here", 0.75, 0.75, 1)

def DrawNodeStencil(self, cusorPos, pos):
    colNode = PowerArr4ToVec(self.dsNodeColor, 1/2.2)
    col = colNode if self.dsIsColoredLine else GetUniformColVec(self)
    if self.dsIsDrawLine:
        DrawStick( self, pos, cusorPos, col, col )
    if self.dsIsDrawPoint:
        DrawWidePoint( self, pos, colNode if self.dsIsColoredPoint else GetUniformColVec(self) )
    return colNode
def DrawTextNodeStencil(self, cusorPos, nd, drawNodeNameLabel, labelDispalySide, col=Vector(1, 1, 1, 1)):
    if not self.dsIsDrawSkText:
        return
    def DrawNodeText(txt):
        DrawText( self, cusorPos, (self.dsDistFromCursor, -0.5), txt, col)
    col = col if self.dsIsColoredSkText else GetUniformColVec(self)
    txt_label = nd.label
    match drawNodeNameLabel:
        case 'NAME':
            DrawNodeText(nd.name)
        case 'LABEL':
            #Пустой текст, а не 'None', чтобы отсутствие заголовка отображалось рамкой с ничем, и смена между нодами не пульсировала наличием рамки.
            DrawNodeText(txt_label if txt_label else "") #todo: сделать для этого опцию.
        case 'LABELNAME':
            if not txt_label:
                DrawNodeText(nd.name)
                return
            match labelDispalySide:
                case 1: tuple_side = (1, 1, 0.25)
                case 2: tuple_side = (1, 1, -1.25)
                case 3: tuple_side = (1, -1, -0.5)
                case 4: tuple_side = (-1, 1, -0.5)
            DrawText( self, cusorPos, (self.dsDistFromCursor*tuple_side[0], tuple_side[2]), nd.name, col)
            DrawText( self, cusorPos, (self.dsDistFromCursor*tuple_side[1], -tuple_side[2]-1), txt_label, col)

#Высокоуровневый шаблон рисования для сокетов; тут весь аддон про сокеты, поэтому в названии нет "Sk".
#Пользоваться этим шаблоном невероятно кайфово, после того хардкора что был в ранних версиях (даже не заглядывайте туда, там около-ад).
def DrawToolOftenStencil(self, cusorPos, list_twoTgSks, #Одинаковое со всех инструментов вынесено в этот шаблон.
                         isLineToCursor=False,
                         textSideFlip=False,
                         isDrawText=True,
                         isDrawMarkersMoreTharOne=False,
                         isDrawOnlyArea=False):
    def GetVecOffsetFromSk(sk, y=0.0):
        return Vector(self.dsPointOffsetX*((sk.is_output)*2-1), y)
    try:
        #Вся суета ради линии:
        if (self.dsIsDrawLine)and(not isDrawOnlyArea):
            len = length(list_twoTgSks)
            if self.dsIsColoredLine:
                col1 = GetSkCol(list_twoTgSks[0].tg)
                col2 = Vector(1, 1, 1, 1) if self.dsIsColoredPoint else GetUniformColVec(self)
                col2 = col2 if (isLineToCursor)or(len==1) else GetSkCol(list_twoTgSks[1].tg)
            else:
                col1 = GetUniformColVec(self)
                col2 = col1
            if len>1: #Ниже могут нарисоваться две палки одновременно. Эта ситуация вручную обрабатывается в вызывающей функции на стек выше.
                DrawStick( self, list_twoTgSks[0].pos+GetVecOffsetFromSk(list_twoTgSks[0].tg), list_twoTgSks[1].pos+GetVecOffsetFromSk(list_twoTgSks[1].tg), col1, col2 )
            if isLineToCursor:
                DrawStick( self, list_twoTgSks[0].pos+GetVecOffsetFromSk(list_twoTgSks[0].tg), cusorPos, col1, col2 )
        #Всё остальное:
        for li in list_twoTgSks:
            if self.dsIsDrawSkArea:
                DrawSocketArea( self, li.tg, li.boxHeiBound, GetSkColPowVec(li.tg, 1/2.2) )
            if (self.dsIsDrawPoint)and(not isDrawOnlyArea):
                DrawWidePoint( self, li.pos+GetVecOffsetFromSk(li.tg), GetSkColPowVec(li.tg, 1/2.2) )
        if isDrawText:
            for li in list_twoTgSks:
                side = (textSideFlip*2-1)
                txtDim = DrawSkText( self, cusorPos, (self.dsDistFromCursor*(li.tg.is_output*2-1)*side, -0.5), li )
                #В условии ".links", но не ".is_linked", потому что линки могут быть выключены (замьючены, красные)
                if (self.dsIsDrawMarker)and( (li.tg.links)and(not isDrawMarkersMoreTharOne)or(length(li.tg.links)>1) ):
                    DrawIsLinkedMarker( self, cusorPos, [txtDim[0]*(li.tg.is_output*2-1)*side, 0], GetSkCol(li.tg) )
    except Exception as ex:
        pass; print("VL DrawToolOftenStencil() --", ex)

#todo! Головная боль с "проскальзывающими" кадрами!! Debug, Collapse, Alt, и много где ещё.

def GetOpKmi(self, tuple_tar): #todo есть концепция или способ правильнее?
    #return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor'].keymap_items[getattr(bpy.types, self.bl_idname).bl_idname] #Чума (но только если без дубликатов).
    txt_toolBlId = getattr(bpy.types, self.bl_idname).bl_idname
    #Оператор может иметь несколько комбинаций вызова, все из которых будут одинаковы по ключу в `keymap_items`, от чего за константу кажись никак не распознать.
    #Поэтому перебираем всех вручную
    for li in bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor'].keymap_items:
        if li.idname==txt_toolBlId:
            #Заметка: искать и по соответствию самой клавише тоже, модификаторы тоже могут быть одинаковыми у нескольких вариантах вызова.
            if (li.type==tuple_tar[0])and(li.shift_ui==tuple_tar[1])and(li.ctrl_ui==tuple_tar[2])and(li.alt_ui==tuple_tar[3]):
                return li

class VoronoiOpPoll:
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' #Не знаю, зачем это нужно, пусть будет.


def MinFromFgs(fgSk1, fgSk2):
    if (fgSk1)or(fgSk2): #Если хотя бы один из них существует.
        if not fgSk2: #Если одного из них не существует,
            return fgSk1
        elif not fgSk1: # то остаётся однозначный выбор для второго.
            return fgSk2
        else: #Иначе выбрать ближайшего.
            return fgSk1 if fgSk1.dist<fgSk2.dist else fgSk2

def GetCanMoveOut(self):
    return not(self.dict_isMoveOutSco[0]%2)and(self.dict_isMoveOutSco[0]>1)
def SetCanMoveOut(self, event):
    #Переключать каждый раз при входе и выходе из карты.
    if self.dict_isMoveOutSco[0]==0:
        #Инверсия с "^d[5]", чтобы в случае хоткея на одну кнопку без модификаторов, можно было делать перевыбор любым из модификаторов.
        if not(event.shift or event.ctrl or event.alt)^self.dict_isMoveOutSco[5]: #|14| Но не от первого отжатия. Оно должно быть полностью никакими. Ибо эстетика, и я так захотел.
            self.dict_isMoveOutSco[0] = 1
    else:
        tgl = (event.shift==self.dict_isMoveOutSco[1])and(event.ctrl==self.dict_isMoveOutSco[2])and(event.alt==self.dict_isMoveOutSco[3])
        tgl = tgl^self.dict_isMoveOutSco[5]
        if tgl!=self.dict_isMoveOutSco[4]:
            self.dict_isMoveOutSco[4] = tgl
            self.dict_isMoveOutSco[0] += 1
    return GetCanMoveOut(self)

#Шаблоны в порядке по хронологии:

def StencilStartDrawCallback(self, context):
    if self.whereActivated!=context.space_data: #Нужно чтобы рисовалось только в активном редакторе, а не во всех у кого открыто то же самое дерево.
        return True
    PrepareShaders(self)
    if self.dsIsDrawDebug:
        DrawDebug(self, context)

def StencilRepick(cls, self, context, tgl=None): #tgl -- костыль, и лишение простора для NextAssessment().
    bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=0) #Из-за этого курсор на винде на один кадр меняется.
    if tgl is None:
        cls.NextAssessment(self, context) #Через self.NextAssessment не работает чёрт возьми, по неведомым мне причинам. Видимо я чего-то не знаю.
    else: #^v Осторожно в вызывающем уровне, чтобы не уйти в вечный цикл!
        cls.NextAssessment(self, context, tgl)

def StencilModalEsc(self, context, event):
    if event.type=='ESC': #Собственно то, что и должна делать клавиша побега.
        return {'RUNNING_MODAL'}
    if event.value!='RELEASE':
        return {'RUNNING_MODAL'}
    bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
    if not context.space_data.edit_tree:
        return {'FINISHED'}
    RestoreCollapsedNodes(context.space_data.edit_tree.nodes)
    return False

def StencilProcPassThrought(txt_prop):
    if getattr(Prefs(), txt_prop): #todo сбежавший от пайки Prefs().
        return 'FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')

#Из-за пайки в себя пришлось проложить путь self'ов во все функции рисования; благодаря чему отпала нужда хранить некоторые переменные, как глобальные.
def SolderingAllPrefsToSelf(self):
    #Меня напрягает постоянные вызовы Prefs() с его "многочленами" и одним взятием индекса; особенно в функциях рисования. Поэтому запаять их на каждый вызов инструмента.
    prefs = Prefs() #Можно было бы сделать так, но тогда пришлось бы делать на каждую функцию, поэтому нет. Уж гулять, так по-просторному.
    for li in VoronoiAddonPrefs.bl_rna.properties:
        if (not li.is_readonly)and(li.identifier.startswith(('ds', 'v'))): #Важна только проверка is_readonly.
            setattr(self, li.identifier, getattr(prefs, li.identifier))
def StencilToolInvokePrepare(self, context, event, Func):
    kmi = GetOpKmi(self, (event.type, event.shift, event.ctrl, event.alt))
    self.keyType = kmi.type
    #"0" -- количество хитов, 1..3 -- карта проверки, 4 -- предыдущее состояние переключателя, 5 -- метка активации без модификаторов.
    self.dict_isMoveOutSco = {0:0, 1:kmi.shift_ui, 2:kmi.ctrl_ui, 3:kmi.alt_ui, 4:False, 5:not(kmi.shift_ui or kmi.ctrl_ui or kmi.alt_ui)} #4:False потому что см. |14|
    ##
    SolderingAllPrefsToSelf(self)
    self.uiScale = UiScale()
    self.whereActivated = context.space_data #CallBack'и рисуются во всех редакторах. Но в тех, у кого нет целевого сокета -- выдаёт ошибку и тем самым ничего не рисуется.
    self.fontId = blf.load(self.dsFontFile) #Постоянная установка шрифта нужна чтобы шрифт не исчезал при смене темы оформления.
    context.area.tag_redraw() #Не нужно в основном, но тогда в кастомных деревьях с нодами без сокетов точка при активации (VMT) не появляется сразу.
    ##
    SaveCollapsedNodes(context.space_data.edit_tree.nodes)
    tgl = not not context.space_data.edit_tree
    Func = Func if tgl else CallbackDrawEditTreeIsNone
    self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(Func, (self,context), 'WINDOW', 'POST_PIXEL')
    context.window_manager.modal_handler_add(self)
    return tgl

#todo проверить все инструменты на никакие деревья и поломанные деревья.

#Обеспечивает поддержку свёрнутых нодов:
#Дождались таки. Конечно же не "честную поддержку", ибо см. вики. Мне противны свёрнутые ноды, и я не мазохист, чтобы шататься с округлостью, и соответствующе изменённым рисованием.
#Так что до введения api на позицию сокета, это лучшее что есть. Ждём и надеемся.
dict_collapsedNodes = {}
def SaveCollapsedNodes(nodes):
    dict_collapsedNodes.clear()
    for nd in nodes:
        dict_collapsedNodes[nd] = nd.hide
#Я не стал показывать развёрнутым только ближайший нод, а сделал этакий "след"
#Чтобы всё это не превращалось в хаос с постоянным "дёрганьем", и чтобы можно было провести, раскрыть, успокоиться, увидеть "местную картинку" и спокойно соединить что нужно.
def RestoreCollapsedNodes(nodes):
    for nd in nodes:
        if dict_collapsedNodes.get(nd, False): #Инструменты могут создавать ноды в процессе; например сохранение результата в Preview'е.
            nd.hide = dict_collapsedNodes[nd]

def StencilUnCollapseNode(self, isInverse, nd, tar=""):
    if type(tar)==str:
        tar = isInverse
    #if (self.vtAlwaysUnhideCursorNode)or(tar)and( (not isInverse)or(not self.vtAlwaysUnhideCursorNode) ): #Запаянная версия.
    if ( ((not self.vtAlwaysUnhideCursorNode)and(tar)) if isInverse else ((self.vtAlwaysUnhideCursorNode)or(tar)) ):
        result = nd.hide
        nd.hide = False
        return result
    return False

class FoundTarget: #Создан для замены списка и повышения читабельности.
    def __init__(self, tg=None, dist=0.0, pos=Vector(0.0, 0.0), boxHeiBound=(0.0, 0.0), txt=''):
        self.tg = tg
        self.dist = dist
        self.pos = pos
        #Далее нужно только для сокетов
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
def GetNearestNodes(nodes, callPos, skipPoorNodes=True): #Выдаёт список ближайших нод. Честное поле расстояний.
    #Почти честное. Скруглённые уголки не высчитываются. Их отсутствие не мешает, а вычисление требует больше телодвижений. Поэтому выпендриваться нет нужды.
    #С другой стороны скруглённость актуальна для свёрнутых нод, но я их презираю, так что...
    list_foundNodes = [] #todo париться с питоновскими и вообще ускорениями буду ещё не скоро.
    for nd in nodes:
        if nd.type=='FRAME': #Рамки пропускаются, ибо ни одному инструменту они не нужны.
            continue
        if (skipPoorNodes)and(not nd.inputs)and(not nd.outputs): #Ноды вообще без ничего -- как рамки. Почему бы их тоже не игнорировать ещё на этапе поиска?
            continue
        ndLoс = RecrGetNodeFinalLoc(nd) #Расчехлить иерархию родителей и получить итоговую позицию нода. Проклятые рамки, чтоб их.
        isReroute = nd.bl_idname=='NodeReroute'
        #Технический размер рероута явно перезаписан в 4 раза меньше, чем он есть.
        #Насколько я смог выяснить, рероут в отличие от остальных нодов свои размеры при изменении UiScale() не меняет. Так что ему не нужно делиться на 'UiScale()'.
        ndSize = Vector(4,4) if isReroute else nd.dimensions/UiScale()
        #Для нода позицию в центр нода. Для рероута позиция уже в его визуальном центре
        ndCenter = ndLoс if isReroute else ndLoс+ndSize/2*Vector(1,-1)
        if nd.hide: #Для VHT, "шустрый костыль" из имеющихся возможностей.
            ndCenter.y += ndSize.y/2
        #Сконструировать поле расстояний
        vec = DistanceField(callPos-ndCenter, ndSize)
        #Добавить в список отработанный нод
        list_foundNodes.append( FoundTarget(nd, vec.length, callPos-vec) )
    list_foundNodes.sort(key=lambda a: a.dist)
    return list_foundNodes

#Уж было я хотел добавить велосипедную структуру ускорения, но внезапно осознал, что ещё нужна информация об "вторых ближайших". Так что кажись без полной обработки никуда.
#Если вы знаете, как можно это ускорить с сохранением информации, поделитесь со мной.
#С другой стороны, за всё время существования аддона не было ни одной стычки с производительностью, так что... только ради эстетики.
#А ещё нужно учесть свёрнутые ноды, пропади они пропадом, которые могут раскрыться в процессе, наворачивая всю прелесть кеширования.

def GetFromIoPuts(nd, side, callPos): #Вынесено для Preview Tool его опции 'vpRvEeSksHighlighting'.
    def SkIsLinkedVisible(sk): #'is_linked' может быть выключенным линком, поэтому нужно заглядывать в содержимое.
        if not sk.is_linked:
            return True
        #Заметка: здесь только сокеты вектора.
        return (sk.links)and(sk.links[0].is_muted)
    list_result = []
    ndLoc = RecrGetNodeFinalLoc(nd)
    #"nd.dimensions" уже содержат в себе корректировку на масштаб интерфейса, поэтому вернуть его обратно в мир делением
    ndDim = mathutils.Vector(nd.dimensions/UiScale())
    #Установить "каретку" в первый сокет своей стороны. Верхний если выход, нижний если вход
    skLocCarriage = Vector(ndLoc.x+ndDim.x, ndLoc.y-35) if side==1 else Vector(ndLoc.x, ndLoc.y-ndDim.y+16)
    for sk in nd.outputs if side==1 else reversed(nd.inputs):
        #Игнорировать выключенные и спрятанные
        if (sk.enabled)and(not sk.hide):
            muv = 0 #Для высоты варпа от векторов-сокетов-не-в-одну-строчку.
            #Если текущий сокет -- входящий вектор, и он же свободный и не спрятан в одну строчку
            if (side==-1)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                #Ручками вычисляем занимаемую высоту сокета. Да да. Api на позицию сокета?. Размечтались.
                #Для сферы направления у ShaderNodeNormal и таких же у групп
                if str(sk.bl_rna).find("VectorDirection")!=-1:
                    skLocCarriage.y += 20*2
                    muv = 2
                #И для особо-отличившихся нод с векторами, которые могут быть в одну строчку. Существует всего два нода, у которых к сокету в исходниках применён `.compact()`
                #Создавать такое через api никак, но и доступа к этому через api тоже нет. Поэтому обрабатываем по именам явным образом
                elif ( not(nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING')) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    skLocCarriage.y += 30*2
                    muv = 3
            goalPos = skLocCarriage.copy()
            #Высота Box-Socket-Area так же учитывает текущую высоту мульти-инпута подсчётом количества соединений, но только для входов (чтобы у выходов не рисовалось словно они мультиинпуты).
            list_result.append(FoundTarget( sk,
                                            (callPos-skLocCarriage).length,
                                            goalPos,
                                            (goalPos.y-11-muv*20, goalPos.y+11+max(length(sk.links)-2,0)*5*(side==-1)),
                                            TranslateIface(sk.name) ))
            #Сдвинуть до следующего на своё направление
            fix = bpy.context.preferences.view.ui_scale
            fix = -sin(pi*fix)**2 #Что-то тут не число. Замаскировал кривым костылём. У меня нет идей.
            skLocCarriage.y -= 22*side-fix*1.35
    return list_result
def GetNearestSockets(nd, callPos): #Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного. Да, да, аддон назван именно из-за этого.
    list_fgSksIn = []
    list_fgSksOut = []
    if not nd: #Если искать не у кого
        return list_fgSksIn, list_fgSksOut
    #Если рероут, то имеем тривиальный вариант, не требующий вычисления; вход и выход всего одни, позиции сокетов -- он сам
    if nd.bl_idname=='NodeReroute':
        ndLoc = RecrGetNodeFinalLoc(nd)
        len = (callPos-ndLoc).length
        L = lambda who: FoundTarget(who[0], len, ndLoc, (-1,-1), TranslateIface(who[0].name))
        return [L(nd.inputs)], [L(nd.outputs)]
    list_fgSksIn = GetFromIoPuts(nd, -1, callPos)
    list_fgSksOut = GetFromIoPuts(nd, 1, callPos)
    list_fgSksIn.sort(key=lambda a: a.dist)
    list_fgSksOut.sort(key=lambda a: a.dist)
    return list_fgSksIn, list_fgSksOut

def CallbackDrawVoronoiLinker(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if not self.foundGoalSkOut:
        DrawDoubleNone(self, context)
    elif (self.foundGoalSkOut)and(not self.foundGoalSkIn):
        DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkOut], isLineToCursor=self.dsIsAlwaysLine )
        if self.dsIsDrawPoint: #Точка под курсором шаблоном выше не обрабатывается, поэтому вручную.
            DrawWidePoint(self, cusorPos)
    else:
        DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkOut, self.foundGoalSkIn] )
#На самых истоках весь аддон создавался только ради этого инструмента. А то-то вы думаете названия одинаковые.
#Но потом я под-ахренел от обузданных возможностей, и меня понесло... понесло на создание троицы. Но этого оказалось мало, и теперь инструментов больше семи. Чума!
#Дублирующие комментарии есть только здесь (и в целом по убыванию). При спорных ситуациях обращаться к VLT, как к примеру.
class VoronoiLinkerTool(bpy.types.Operator, VoronoiOpPoll): #То ради чего. Самый первый. Босс всех инструментов. Во славу полю расстояния!
    bl_idname = 'node.voronoi_linker'
    bl_label = "Voronoi Linker"
    bl_options = {'UNDO'}
    def NextAssessment(self, context, isBoth):
        if not context.space_data.edit_tree: #Из `modal()` перенесено сюда.
            return
        #В случае не найденного подходящего предыдущий выбор остаётся, отчего не получится вернуть курсор обратно и "отменить" выбор, что очень неудобно.
        self.foundGoalSkIn = None #Поэтому обнуляется каждый раз перед поиском.
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            #Для выключенного vtAlwaysUnhideCursorNode нод сокета активации в любом случае нужно разворачивать.
            #Свёрнутость для рероутов работает, хоть и не отображается визуально; но теперь нет нужды обрабатывать,
            if StencilUnCollapseNode(self, False, nd, isBoth): # ибо поддержка свёрнутости введена.
                #Нужно перерисовывать, если соединилось во вход свёрнутого нода.
                StencilRepick(VoronoiLinkerTool, self, context, False) #todo проверить сделать и для остальных инструментов.
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos)
            #Этот инструмент триггерится на любой выход
            if isBoth:
                self.foundGoalSkOut = list_fgSksOut[0] if list_fgSksOut else []
            #Получить вход по условиям:
            skOut = self.foundGoalSkOut.tg if self.foundGoalSkOut else None
            if skOut: #Первый заход всегда isBoth=True, однако нод может не иметь выходов.
                #На этом этапе условия для отрицания просто найдут другой результат. "Присосётся не к этому, так к другому".
                for li in list_fgSksIn:
                    skIn = li.tg
                    #Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет с обеих сторон, минуя различные типы
                    tgl = (SkBetweenCheck(skIn))and(SkBetweenCheck(skOut))or( (skOut.node.type=='REROUTE')or(skIn.node.type=='REROUTE') )and(self.vlReroutesCanInAnyType)
                    #Любой сокет для виртуального выхода; разрешить в виртуальный для любого сокета; обоим в себя запретить
                    tgl |= (skIn.bl_idname=='NodeSocketVirtual')^(skOut.bl_idname=='NodeSocketVirtual') #|1|
                    #В версии 3.5 новый сокет автоматически не создаётся. Поэтому добавляются новые возможности по соединению
                    tgl |= (skIn.node.type=='REROUTE')and(skIn.bl_idname=='NodeSocketVirtual')
                    #Если имена типов одинаковые, но не виртуальные
                    tgl |= (skIn.bl_idname==skOut.bl_idname)and( not( (skIn.bl_idname=='NodeSocketVirtual')and(skOut.bl_idname=='NodeSocketVirtual') ) )
                    if tgl:
                        self.foundGoalSkIn = li
                        break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
                #На этом этапе условия для отрицания сделают результат никаким. Типа "Ничего не нашлось"; и будет обрабатываться соответствующим рисованием.
                if self.foundGoalSkIn:
                    if self.foundGoalSkIn.tg.node.type=='GROUP_OUTPUT': #Моя личная хотелка. См. |13|. Находится здесь, чтобы триггериться на один сокет выше, а не сразу на него.
                        self.foundGoalSkIn.tg.node.inputs[-1].hide = False
                    if self.foundGoalSkOut.tg.node==self.foundGoalSkIn.tg.node: #Если для выхода ближайший вход -- его же нод.
                        self.foundGoalSkIn = None
                    elif self.foundGoalSkOut.tg.links: #Если выход уже куда-то подсоединён, даже если это выключенные линки.
                        for lk in self.foundGoalSkOut.tg.links:
                            if lk.to_socket==self.foundGoalSkIn.tg: #Если ближайший вход -- один из подсоединений выхода, то обнулить => "желаемое" соединение уже имеется.
                                self.foundGoalSkIn = None
                                #Используемый в проверке выше "self.foundGoalSkIn" обнуляется, поэтому нужно выходить, иначе будет попытка чтения из несуществующего элемента следующей итерацией.
                                break
                    if StencilUnCollapseNode(self, True, nd): #Обработка свёрнутости.
                        StencilRepick(VoronoiLinkerTool, self, context, False)
            break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
        if (self.foundGoalSkOut)and(self.foundGoalSkOut.tg.node.type=='GROUP_INPUT'): #См. |13|.
            self.foundGoalSkOut.tg.node.outputs[-1].hide = False
    def modal(self, context, event):
        context.area.tag_redraw() #Неожиданно, но кажется теперь оно перерисовывается само по себе. Но только при каких-то обстоятельствах. Ибо для некоторых инструментов
        # в кастомных деревьях если у нод нет сокетов, что-то не работает.
        isCanNext = True
        if SetCanMoveOut(self, event): #Должно обрабатываться не только от движения курсора.
            isCanNext = False #Но не делать двойную обработку.
            self.foundGoalSkOut = None
            self.foundGoalSkIn = None #todo: выяснить картину
            VoronoiLinkerTool.NextAssessment(self, context, True)
        match event.type:
            case 'MOUSEMOVE':
                if isCanNext:
                    VoronoiLinkerTool.NextAssessment(self, context, False)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                tree = context.space_data.edit_tree
                for nd in tree.nodes: #См. |13|.
                    if nd.type=='GROUP_INPUT':
                        nd.outputs[-1].hide = self.dict_hideVirtualGpInNodes[nd]
                    if nd.type=='GROUP_OUTPUT':
                        nd.inputs[-1].hide = self.dict_hideVirtualGpOutNodes[nd]
                if not( (self.foundGoalSkOut)and(self.foundGoalSkIn) ):
                    return {'CANCELLED'}
                #|2| Если дерево нодов от к.-н. аддона исчезло, то останки имеют NodeUndefined и NodeSocketUndefined.
                #Достаточно проверить только один из них, потому что они там все такие
                if self.foundGoalSkOut.tg.bl_idname=='NodeSocketUndefined':
                    return {'CANCELLED'} #Через api линки на SocketUndefined строчкой ниже не создаются, поэтому выходим.
                #Чтобы можно было брать тип с рероута, который сам меняется под тип при соединении, типы сокетов перед соединением нужно запомнить
                blIdSkOut, blIdSkIn = self.foundGoalSkOut.tg.bl_idname, self.foundGoalSkIn.tg.bl_idname
                #См. |9| ...а его там неоткуда взять, ибо информация уже утеряна. Поэтому сохранить её здесь
                headache = self.foundGoalSkOut.tg.node.inputs[0].bl_idname if self.foundGoalSkOut.tg.node.type=='REROUTE' else ''
                #Самая важная строчка.
                lk = tree.links.new(self.foundGoalSkOut.tg, self.foundGoalSkIn.tg)
                #Виртуальный инпут может принимать в себя прям как мультиинпут. Они даже могут между собой одним и тем же линком по нескольку раз соединяться, ну офигеть.
                #Теперь под всё это придётся подстраиваться.
                #Проверяем, если линк соединился на виртуальные, но "ничего не произошло".
                #Но так же важно проверить, что этот виртуальный сокет не является рероутом
                num = (blIdSkOut=='NodeSocketVirtual')*(lk.from_node.type!='REROUTE')+(blIdSkIn=='NodeSocketVirtual')*(lk.to_node.type!='REROUTE')*2
                #Рероуты тоже могут быть виртуальными, поэтому нужно отличить их. "0" если io групп не найдено.
                num *= (lk.from_node.bl_idname=='NodeGroupInput')or(lk.to_node.bl_idname=='NodeGroupOutput')
                #Ситуация "виртуальный в виртуальный из группы в группу" исключена в |1| с помощью xor, от чего её не нужно обрабатывать.
                def FullCopySkToSi(where, txt1, sk): #Вручную переносим значения из сокета в интерфейсный сокет.
                    si = getattr(tree, where).new(txt1, sk.name)
                    if getattr(si,'default_value',False):
                        si.default_value = sk.default_value #todo: Не совершенно. Жаль я не знаю, как имитировать тру-соединение виртуального через api.
                    si.hide_value = sk.hide_value
                    if sk.bl_idname.find('Factor')!=-1:
                        si.min_value = 0.0
                        si.max_value = 1.0
                num = 0 #Выключено. Нужно всё это нахрен переосмыслить. Ибо костыль; ибо соединение виртуального из вывода симуляции в вывод группы. Todo.
                match num:
                    case 1:
                        FullCopySkToSi('inputs', blIdSkIn, lk.to_socket) #Ручками добавляем новый io группы.
                        tree.links.remove(lk) #Удалить некорректный линк.
                        tree.links.new(self.foundGoalSkOut.tg.node.outputs[-2], self.foundGoalSkIn.tg) #Ручками создаём корректный линк.
                    case 2:
                        #|9| Головная боль. У новосозданных рероутов вывод всегда цвет, пока он не был подсоединён куда-н. Поэтому брать тип нужно с инпута рероута...
                        FullCopySkToSi('outputs', headache if headache else blIdSkOut, lk.from_socket)
                        tree.links.remove(lk)
                        tree.links.new(self.foundGoalSkOut.tg, self.foundGoalSkIn.tg.node.inputs[-2])
                    case 3: #Бесполезная редкая ситуация, которая обрабатывается лишь для полноты картины.
                        #Создавать новый io группы нужно только если соединение было в самый-последний-тру-виртуальный; определить это
                        if (lk.from_socket==lk.from_node.outputs[-1])and(lk.to_socket==lk.to_node.inputs[-1]): #Рероут всегда "-1"
                            tgl = lk.to_node.type=='REROUTE'
                            if tgl:
                                nd = lk.from_node
                                tree.inputs.new('NodeSocketVirtual', lk.to_socket.name)
                            else:
                                nd = lk.to_node
                                tree.outputs.new('NodeSocketVirtual', lk.from_socket.name)
                            tree.links.remove(lk)
                            if tgl: #Я не помню, для чего добавил tgl. Забыл написать комментарий об этом.
                                tree.links.new(nd.outputs[-2], self.foundGoalSkIn.tg)
                            else:
                                tree.links.new(self.foundGoalSkOut.tg, nd.inputs[-2])
                #Моя личная хотелка, которая чинит странное поведение, и делает его логически-корректно-ожидаемым. Накой смысол последние соединённые через api лепятся в начало?
                if self.foundGoalSkIn.tg.is_multi_input: #Если мультиинпут, то реализовать адекватный порядок подключения.
                    list_skLinks = []
                    for lk in self.foundGoalSkIn.tg.links: #Запомнить все имеющиеся линки по сокетам, и удалить их.
                        list_skLinks.append((lk.from_socket, lk.to_socket))
                        tree.links.remove(lk)
                    #До версии 3.5 обработка ниже нужна была, чтобы новый io группы дважды не создавался.
                    #Теперь без этой обработки Блендер или крашнется, или линк из виртуального в мультиинпут будет подсвечен красным как "некорректный"
                    if self.foundGoalSkOut.tg.bl_idname=='NodeSocketVirtual':
                        self.foundGoalSkOut.tg = self.foundGoalSkOut.tg.node.outputs[-2]
                    tree.links.new(self.foundGoalSkOut.tg, self.foundGoalSkIn.tg) #Соединить очередной первым.
                    for cyc in range(length(list_skLinks)-1): #Восстановить запомненные. "-1", потому что последний в списке является желанным, что уже соединён строчкой выше.
                        tree.links.new(list_skLinks[cyc][0], list_skLinks[cyc][1])
                return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        prefs = Prefs() #todo сбежавшие разрастаются.
        if StencilProcPassThrought('vlPassThrought'):
            return {'PASS_THROUGH'}
        else:
            if (prefs.vlDeselectAll=='WHEN_PT')and(prefs.vlPassThrought):
                bpy.ops.node.select_all(action='DESELECT')
        if (prefs.vlDeselectAll=='ALWAYS'):
            bpy.ops.node.select_all(action='DESELECT')
        ##
        self.foundGoalSkOut = None
        self.foundGoalSkIn = None
        self.isDrawTwoPoints = True
        self.dict_hideVirtualGpInNodes = {}
        self.dict_hideVirtualGpOutNodes = {}
        #|13| К тусовке обработки свёрнутости добавляется моя личная хотелка; ибо виртуальные сокеты я всегда держу скрытыми.
        for nd in context.space_data.edit_tree.nodes:
            if nd.type=='GROUP_INPUT':
                self.dict_hideVirtualGpInNodes[nd] = nd.outputs[-1].hide
            if nd.type=='GROUP_OUTPUT':
                self.dict_hideVirtualGpOutNodes[nd] = nd.inputs[-1].hide
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiLinker):
            VoronoiLinkerTool.NextAssessment(self, context, True)
        return {'RUNNING_MODAL'}

AddToRegAndAddToKmiDefs(VoronoiLinkerTool, "RIGHTMOUSE_scA") #LEFTMOUSE_sca

def CallbackDrawVoronoiPreview(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkOut:
        if self.vpRvEeSksHighlighting: #Помощь в реверс-инженеринге, подсвечивать места соединения, и отображать имя этих сокетов, одновременно.
            #Определить масштаб для надписей:
            pos = VecWorldToRegScale(cusorPos, self)
            loc = Vector(cusorPos.x+6*1000, cusorPos.y)
            rd = (VecWorldToRegScale(loc, self)[0]-pos[0])/1000
            #Нарисовать:
            ndTar = self.foundGoalSkOut.tg.node
            for side in [False, True]:
                for skTar in ndTar.outputs if side else ndTar.inputs:
                    for lk in skTar.links:
                        if not lk.is_muted:
                            sk = lk.to_socket if side else lk.from_socket
                            nd = sk.node
                            nd.hide = False #Запись во время рисования. По крайней мере не так как сильно, как в MassLinker Tool.
                            if nd.type!='REROUTE': #if (not nd.hide)and(nd.type!='REROUTE'): #Отображать у тех, кто не свёрнут и не рероут.
                                list_fgSks = GetFromIoPuts(nd, 1-(side*2), context.space_data.cursor_location)
                                for li in list_fgSks:
                                    if li.tg==sk:
                                        DrawToolOftenStencil( self, cusorPos, [li], isDrawText=False, isDrawOnlyArea=True )
                                        DrawSkText( self, li.pos, ((li.tg.is_output*2-1), -0.5), li, min(rd*4,25) )
                                        break
        #Порядок рисования важен, главное над реверс-инженерингом.
        DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkOut], isLineToCursor=True, textSideFlip=True, isDrawText=True, isDrawMarkersMoreTharOne=True )
    elif self.dsIsDrawPoint:
        DrawWidePoint(self, cusorPos)
class VoronoiPreviewTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_preview'
    bl_label = "Voronoi Preview"
    bl_options = {'UNDO'}
    isPlaceAnAnchor: bpy.props.BoolProperty()
    def NextAssessment(self, context):
        if not context.space_data.edit_tree:
            return
        isAncohorExist = context.space_data.edit_tree.nodes.get(voronoiAnchorName) #Если в геонодах есть якорь, то триггериться не только на геосокеты.
        #Некоторые пользователи в "начале знакомства" с аддоном захотят переименовать якорь.
        #Каждый призыв якоря одинаков по заголовку, а при повторном призыве заголовок всё равно меняется обратно на стандартный.
        #После чего пользователи поймут, что переименовывать якорь бесполезно.
        if isAncohorExist: #Эта проверка с установкой лишь ускоряет процесс осознания.
            isAncohorExist.label = voronoiAnchorName
        isAncohorExist = not not isAncohorExist
        self.foundGoalSkOut = None #Нет нужды, но сбрасывается для ясности картины. Было полезно для отладки.
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            StencilUnCollapseNode(self, False, nd)
            if self.vpRvEeIsSavePreviewResults:
                #Игнорировать готовый нод для переименования и тем самым сохраняя результаты предпросмотра.
                if nd.name==voronoiPreviewResultNdName:
                    continue
            #Если в геометрических нодах, то игнорировать ноды без выходов геометрии
            if (context.space_data.tree_type=='GeometryNodeTree')and(not isAncohorExist):
                if not [sk for sk in nd.outputs if (sk.type=='GEOMETRY')and(not sk.hide)and(sk.enabled)]: #Искать сокеты геометрии, которые видимы.
                    continue
            #Пропускать ноды если визуально нет сокетов; или есть, но только виртуальные
            if not [sk for sk in nd.outputs if (not sk.hide)and(sk.enabled)and(sk.bl_idname!='NodeSocketVirtual')]:
                continue
            #Всё выше нужно было для того, чтобы точка не висела просто так и нод не мешал для удобного использования инструмента. По ощущениям получаются как "прозрачные" ноды.
            #Игнорировать свой собственный спец-рероут-якорь (проверка на тип и имя)
            if ( (nd.type=='REROUTE')and(nd.name==voronoiAnchorName) ):
                continue
            #В случае успеха переходить к сокетам:
            list_fgSksOut = GetNearestSockets(nd, callPos)[1]
            for li in list_fgSksOut:
                #Этот инструмент триггерится на любой выход кроме виртуального. В геометрических нодах искать только выходы геометрии.
                #Якорь притягивает на себя превиев; рероут может принимать любой тип; следовательно -- при наличии якоря отключать триггер только на геосокеты
                if (li.tg.bl_idname!='NodeSocketVirtual')and( (context.space_data.tree_type!='GeometryNodeTree')or(li.tg.type=='GEOMETRY')or(isAncohorExist) ):
                    if (not(self.vpRvEeTriggerOnlyOnLink))or(li.tg.is_linked): #Помощь в реверс-инженеринге, триггериться только на существующие линки. Ускоряет процесс "считывания/понимания" дерева.
                        self.foundGoalSkOut = li
                        break
            if (not(self.vpRvEeTriggerOnlyOnLink))or(self.foundGoalSkOut):
                break #Искать до тех пор, пока не будет сокет с линком.
        if self.foundGoalSkOut:
            if self.vpIsLivePreview:
                self.foundGoalSkOut.tg = DoPreview(self, context, self.foundGoalSkOut.tg) #Повторное присваивание нужно если в процессе сокет потеряется. См. |3|
            if self.vpRvEeIsColorOnionNodes: #Помощь в реверс-инженеринге, вместо поиска глазами тоненьких линий, быстрое визуальное считывание связанных нод топологией.
                for nd in context.space_data.edit_tree.nodes:
                    nd.use_custom_color = False #Не париться с запоминанием последних и тупо выключать у всех каждый раз. Дёшево и сердито.
                for sk in self.foundGoalSkOut.tg.node.inputs:
                    for lk in sk.links:
                        nd = lk.from_socket.node
                        nd.use_custom_color = True
                        if nd.name!=voronoiPreviewResultNdName:
                            nd.color = (0.55, 0.188, 0.188)
                        nd.hide = False #А так же раскрывать их.
                for sk in self.foundGoalSkOut.tg.node.outputs:
                    for lk in sk.links:
                        nd = lk.to_socket.node
                        nd.use_custom_color = True
                        if nd.name!=voronoiPreviewResultNdName: #Нод для сохранения результата не перекрашивать
                            nd.color = (0.188, 0.188, 0.5)
                        nd.hide = False #А так же раскрывать их.
            StencilUnCollapseNode(self, True, nd)
    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiPreviewTool.NextAssessment(self, context)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if not self.foundGoalSkOut:
                    return {'CANCELLED'}
                DoPreview(self, context, self.foundGoalSkOut.tg)
                if self.vpRvEeIsColorOnionNodes:
                    for nd in context.space_data.edit_tree.nodes:
                        dv = self.dict_saveRestoreNodeColors.get(nd, None) #Так же, как и в восстановлении свёрнутости.
                        if dv is not None:
                            nd.use_custom_color = dv[0]
                            nd.color = dv[1]
                return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if StencilProcPassThrought('vpPassThrought'):
            return {'PASS_THROUGH'}
        if ('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): #Если симуляция выделения прошла успешно => что-то было выделено.
            #Если использование классического viewer'а разрешено, завершить оператор с меткой пропуска, "передавая эстафету" оригинальному виеверу.
            #Здесь нет разделения на 'isPlaceAnAnchor'.
            match context.space_data.tree_type:
                case 'CompositorNodeTree':
                    if Prefs().vpAllowClassicCompositorViewer:
                        return {'PASS_THROUGH'}
                case 'GeometryNodeTree':
                    if Prefs().vpAllowClassicGeoViewer:
                        return {'PASS_THROUGH'}
        if self.isPlaceAnAnchor: #Если установка якоря
            if not context.space_data.edit_tree:
                return {'FINISHED'}
            tree = context.space_data.edit_tree
            for nd in tree.nodes:
                nd.select = False
            ndAnch = tree.nodes.get(voronoiAnchorName)
            tgl = not ndAnch #Метка для обработки при первом появлении.
            ndAnch = ndAnch or tree.nodes.new('NodeReroute')
            tree.nodes.active = ndAnch
            ndAnch.name = voronoiAnchorName
            ndAnch.label = ndAnch.name
            ndAnch.location = context.space_data.cursor_location
            ndAnch.select = True
            if tgl:
                #Почему бы и нет. Зато красивый.
                #ndAnch.inputs[0].type = 'CUSTOM' #Установка напрямую не работает, поэтому идём на пролом:
                nd = tree.nodes.new('NodeGroupInput')
                tree.links.new(nd.outputs[-1], ndAnch.inputs[0])
                tree.nodes.remove(nd)
            return {'FINISHED'}
        else: #Иначе активация предпросмотра
            self.foundGoalSkOut = None
            if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiPreview):
                VoronoiPreviewTool.NextAssessment(self, context)
            if self.vpRvEeIsColorOnionNodes: #После шаблона, чтобы читать из пайки.
                self.dict_saveRestoreNodeColors = {}
                for nd in context.space_data.edit_tree.nodes:
                    self.dict_saveRestoreNodeColors[nd] = (nd.use_custom_color, nd.color.copy())
                    nd.use_custom_color = False
        return {'RUNNING_MODAL'}

list_classes += [VoronoiPreviewTool]
AddToKmiDefs(VoronoiPreviewTool, "RIGHTMOUSE_SCa", {'isPlaceAnAnchor': True })
AddToKmiDefs(VoronoiPreviewTool, "LEFTMOUSE_SCa", {'isPlaceAnAnchor': False })

tuple_shaderNodesWithColor = ('BSDF_ANISOTROPIC','BSDF_DIFFUSE',         'BSDF_GLASS',       'BSDF_GLOSSY',
                              'BSDF_HAIR',       'BSDF_HAIR_PRINCIPLED', 'PRINCIPLED_VOLUME','BACKGROUND',
                              'BSDF_REFRACTION' ,'SUBSURFACE_SCATTERING','BSDF_TOON',        'BSDF_TRANSLUCENT',
                              'BSDF_TRANSPARENT','BSDF_VELVET',          'VOLUME_ABSORPTION','VOLUME_SCATTER',
                              'BSDF_PRINCIPLED', 'EEVEE_SPECULAR',       'EMISSION')
def GetSocketIndex(sk):
    return int(sk.path_from_id().split(".")[-1].split("[")[-1][:-1])
def DoPreview(self, context, goalSk):
    if not goalSk: #Для |3|, и просто общая проверка.
        return None
    context.space_data.edit_tree.nodes.active = goalSk.node #Для стабильности и ясности, а также для |6|
    def GetTrueTreeWay(context, nd):
        #NodeWrangler находил путь рекурсивно через активный нод дерева, используя "while tree.nodes.active != context.active_node:" (строка 613 в версии 3.43).
        #Этот способ имеет недостатки, ибо активным нодом может оказаться не нод-группа, банально тем, что можно открыть два окна редактора и спокойно нарушить этот "путь".
        #Погрузившись в документацию и исходный код я обнаружил простой api -- ".space_data.path". См. https://docs.blender.org/api/current/bpy.types.SpaceNodeEditorPath.html
        #Это "честный" api, дающий доступ для редактора узлов к пути от базы до финального дерева, отображаемого прямо сейчас.
        list_wayTreeNd = [ [ph.node_tree, ph.node_tree.nodes.active] for ph in reversed(context.space_data.path) ] #Путь реверсирован. 0-й -- целевой, последний -- корень
        #Как я могу судить, сама суть реализации редактора узлов не хранит >нод<, через который пользователь зашёл в группу (но это не точно).
        #Поэтому если активным оказалась не нод-группа, то заменить на первый найденный-по-группе нод (или ничего, если не найдено)
        for cyc in range(1, length(list_wayTreeNd)):
            li = list_wayTreeNd[cyc]
            if (not li[1])or(li[1].type!='GROUP')or(li[1].node_tree!=list_wayTreeNd[cyc-1][0]): #Определить некорректного.
                li[1] = None #Если ниже не найден, то останется имеющийся неправильный. Поэтому обнулить его.
                for nd in li[0].nodes:
                    if (nd.type=='GROUP')and(nd.node_tree==list_wayTreeNd[cyc-1][0]): #Если в текущей глубине с неправильным нодом имеется нод группы с правильной группой.
                        li[1] = nd
                        break #Починка этой глубины произошла успешно.
        return list_wayTreeNd
    curTree = context.space_data.edit_tree
    #|12| Если в текущем дереве есть якорь, то никаких voronoiSkPreviewName не удалять; благодаря чему становится доступным ещё одно особое использование инструмента.
    #Должно было стать логическим продолжением после "завершение после напарывания", но допёр до этого только сейчас.
    if not curTree.nodes.get(voronoiAnchorName):
        #Удалить все свои следы предыдущего использования для всех нод-групп, чей тип текущего редактора такой же.
        for ng in bpy.data.node_groups:
            if ng.bl_idname==context.space_data.tree_type:
                sk = True
                while sk: #Ищется по имени. Пользователь может сделать дубликат, от чего без while они будут исчезать по одному каждое движение мыши.
                    sk = ng.outputs.get(voronoiSkPreviewName)
                    if sk:
                        ng.outputs.remove(sk)
    #|3| Переполучить сокет. Нужен в ситуациях присасывания к своим сокетам предпросмотра, которые исчезли.
    #todo: подробнее описать и осознать проблему повторно с |3|.
    if GetSocketIndex(goalSk)==-1:
        return None #Если сокет был удалён, вернуться.
    #Выстроить путь:
    list_wayTreeNd = GetTrueTreeWay(context, goalSk.node)
    higWay = length(list_wayTreeNd)-1
    ixSkLastUsed = -1 #См. |4|
    isZeroPreviewGen = True #См. |5|
    for cyc in range(higWay+1):
        ndIn = None
        skOut = None
        skIn = None
        #Проверка по той же причине, по которой мне не нравится способ от NW. #todo описать подробнее
        isPrecipice = (list_wayTreeNd[cyc][1]==None)and(cyc>0) #Обрыв обрабатывается на очередной глубине, ибо случай тривиален. Но не обрабатывается у корня, ибо догадайтесь сами.
        #Найти принимающий нод текущего уровня
        if (cyc!=higWay)and(not isPrecipice): #"not isPrecipice" -- в случае обрыва найти принимающий нод в коре, (а потом продолжить обработку обрыва).
            for nd in list_wayTreeNd[cyc][0].nodes:
                if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                    ndIn = nd
        else:
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    for nd in list_wayTreeNd[higWay][0].nodes:
                        if nd.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT_LINESTYLE','OUTPUT'}:
                            if nd.is_active_output:
                                #Соединять в сокет объёма, если предпросматриваемый сокет имеет имя "Объём" и тип принимающего нода имеет вход для объёма
                                skIn = nd.inputs[ (goalSk.name=="Volume")*(nd.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD'}) ]
                case 'GeometryNodeTree':
                    for nd in list_wayTreeNd[higWay][0].nodes:
                        if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output):
                            for sk in nd.inputs:
                                if sk.type=='GEOMETRY':
                                    skIn = sk
                                    break #Важно найти самый первый сверху. #todo: почему? и подробнее закоментить
                case 'CompositorNodeTree':
                    for nd in list_wayTreeNd[higWay][0].nodes:
                        if nd.type=='VIEWER':
                            skIn = nd.inputs[0]
                    if not skIn: #Если не нашёлся композитный виевер, искать основной нод вывода.
                        for nd in list_wayTreeNd[higWay][0].nodes:
                            if (nd.type=='COMPOSITE'):
                                skIn = nd.inputs[0]
                case 'TextureNodeTree':
                    for nd in list_wayTreeNd[higWay][0].nodes:
                        if nd.type=='OUTPUT':
                            skIn = nd.inputs[0]
            if skIn: #Если найдено успешно, то установить нод из найденного сокета.
                ndIn = skIn.node
        if isPrecipice: #Если активный нод на пути удалился, то продолжать путь не от кого.
            #Можно просто выйти, а можно создать "группу перед обрывом" в корне и соединить.
            if skIn: #Наличие обрыва не означает, что корень точно будет. Он тоже может потеряться.
                tree = list_wayTreeNd[higWay][0]
                ndOut = None #Для того, чтобы найти имеющийся или иначе создать.
                for nd in tree.nodes:
                    nd.select = False
                    if (nd.type=='GROUP')and(nd.node_tree==list_wayTreeNd[cyc-1][0]):
                        ndOut = nd
                        break
                #todo: закоментить
                ndOut = ndOut or tree.nodes.new(tree.bl_idname.replace("Tree", "Group"))
                ndOut.node_tree = list_wayTreeNd[cyc-1][0]
                tree.links.new(ndOut.outputs.get(voronoiSkPreviewName), skIn)
                ndOut.location = ndIn.location-Vector(ndOut.width+20, 0)
            return goalSk
        #Определить сокет отправляющего нода
        if cyc==0:
            skOut = goalSk
        else:
            skOut = list_wayTreeNd[cyc][1].outputs.get(voronoiSkPreviewName) #Получить по имени на очередной глубине.
            if (not skOut)and(ixSkLastUsed in range(length(list_wayTreeNd[cyc][1].outputs))): #Если нет своего превиева, то получить от |4|.
                skOut = list_wayTreeNd[cyc][1].outputs[ixSkLastUsed]
        #Определить сокет принимающего нода:
        #|4| Моё улучшающее изобретение -- если соединение уже имеется, то зачем создавать рядом такое же?.
        #Это эстетически комфортно, а так же помогает отчистить последствия предпросмотра не выходя из целевой глубины.
        for lk in skOut.links: #Если этот сокет соединён куда-то.
            if lk.to_node==ndIn: #Если соединён с нодом для соединения.
                skIn = lk.to_socket #Выбрать его сокет => соединять с voronoiSkPreviewName не придётся, оно уже.
                ixSkLastUsed = GetSocketIndex(skIn) # И так может продолжаться до самого корня.
        #Если не удобный |4|, то создать очередной новый сокет для вывода
        if (not skIn)and(cyc!=higWay): #Вторая проверка нужна для ситуации если корень потерял вывод. В геонодах не страшно, но в других будет обработка "как есть".
            if context.space_data.tree_type=='GeometryNodeTree':
                txt = "NodeSocketGeometry"
            elif skOut.type=='SHADER':
                txt = "NodeSocketShader"
            else:
                #Почему цвет, а не шейдер, как у NW'а? Потому что иногда есть нужда вставить нод куда-то в пути превиева.
                #Но если линки шейдерные -- готовьтесь к разочарованию. Поэтому цвет; кой и был изначально у NW.
                txt = "NodeSocketColor"
            #Скрыть отображение значения у NodeSocketInterface, а не у конкретного нода в который соединяется
            if not list_wayTreeNd[cyc][0].outputs.get(voronoiSkPreviewName): #См. |12|
                list_wayTreeNd[cyc][0].outputs.new(txt, voronoiSkPreviewName).hide_value = True #Не путать интерфейс и сокет у конкретного нода.
            if not ndIn: #Если выводы групп куда-то потерялись, то создать его самостоятельно, вместо того чтобы остановиться, и не знать что делать.
                ndIn = list_wayTreeNd[cyc][0].nodes.new('NodeGroupOutput')
                #|6| Если потеря в целевой глубине, то нодом должен быть нод целевого сокета, а его там может не оказаться, ибо в пути содержится дерево и его активный нод.
                #todo: понять повторно.
                ndIn.location = list_wayTreeNd[cyc][1].location
                ndIn.location.x += list_wayTreeNd[cyc][1].width*2
            skIn = ndIn.inputs.get(voronoiSkPreviewName)
            isZeroPreviewGen = False
        #Удобный сразу-в-шейдер. (Такое же изобретение, как и |4|, только чуть менее удобное. Мб стоит избавиться от такой возможности)
        #Основной приём для шейдеров -- цвет, поэтому проверять нужно только для сокетов цвета.
        #Продолжить проверку если у корня есть вывод, и он куда-то подсоединён (может быть это окажется шейдер).
        if (self.vpIsAutoShader)and(skOut.type=='RGBA')and(skIn)and(length(skIn.links)>0):
            #Мультиинпутов у корней не бывает, так что проверяется первый линк сокета. И если его нод находится в группе с "шейдерами что имеют цвет", то продолжить.
            #|5| isZeroPreviewGen нужен, чтобы если просмотр из группы, то не соединятся в шейдер; но если это был "тру" путь без создания voronoiSkPreviewName, то из групп соединяться можно
            if (skIn.links[0].from_node.type in tuple_shaderNodesWithColor)and(isZeroPreviewGen):
                #Если сокет шейдера подсоединён только в корень
                if length(skIn.links[0].from_socket.links)==1:
                    #То тогда однозначный вариант определён, сменить сокет вывода с корня на сокет цвета шейдера. Повезло, что у всех шейдеров цвет именуется одинаково (почти у всех).
                    skIn = skIn.links[0].from_node.inputs.get("Color") or skIn.links[0].from_node.inputs.get("Base Color")
        #Соединить:
        ndAnch = list_wayTreeNd[cyc][0].nodes.get(voronoiAnchorName)
        if ndAnch: #Якорь делает "планы изменились", и пересасывает поток на себя.
            list_wayTreeNd[cyc][0].links.new(skOut, ndAnch.inputs[0])
            #list_wayTreeNd[cyc][0].links.new(ndAnch.outputs[0], skIn) #todo: какое-то робкое ответвление? или удалить, или удалить.
            break #Завершение после напарывания повышает возможности использования якоря, делая его ещё круче. Если у вас течка от Voronoi_Anchor, то я вас понимаю. У меня тоже.
            #Завершение позволяет иметь пользовательское соединение от глубины с якорем и до корня, не разрушая их (но сокеты предпросмотра всё равно создаются).
        #todo переосмыслить якори и глубины, или по крайней мере скомпилировать всё это у себя в голове.
        elif (skOut)and(skIn): #Иначе обычное соединение маршрута.
            if self.vpRvEeIsSavePreviewResults: #Помощь в реверс-инженеринге, сохранять вычленённые промежуточные результаты для последующего "менеджмента".
                def GetTypeOfNodeSave(sk):
                    match sk.type:
                        case 'GEOMETRY': return 2
                        case 'SHADER': return 1
                        case _: return 0
                tree = list_wayTreeNd[cyc][0]
                #Создать:
                typ = GetTypeOfNodeSave(skOut)
                vec = skIn.node.location
                vec = [vec[0]+skIn.node.width+40, vec[1]]
                nd = tree.nodes.get(voronoiPreviewResultNdName)
                if nd:
                    if nd.label!=voronoiPreviewResultNdName:
                        nd.name += "_"+nd.label
                        nd = None
                    elif GetTypeOfNodeSave(nd.outputs[0])!=typ:
                        vec = nd.location
                        tree.nodes.remove(nd)
                        nd = None
                if not nd:
                    match typ:
                        case 0: txt = "MixRGB" #"MixRGB" потому что он есть во всех редакторах, а ещё Shift+G > Type.
                        case 1: txt = "AddShader"
                        case 2: txt = "SeparateGeometry"
                    nd = tree.nodes.new(tree.bl_idname.replace("Tree","")+txt)
                    #Поставить:
                    nd.location = vec
                nd.name = voronoiPreviewResultNdName
                nd.label = nd.name
                nd.use_custom_color = True
                match typ:
                    case 0:
                        nd.color = (0.42968, 0.42968, 0.113725)
                        nd.show_options = False
                        nd.blend_type = 'ADD'
                        nd.inputs[0].default_value = 0
                        nd.inputs[1].default_value = (0.155927, 0.155927, 0.012286, 1.0)
                        nd.inputs[0].hide = True
                        nd.inputs[1].name = "Color"
                        nd.inputs[2].hide = True
                        inx = 1
                    case 1:
                        nd.color = (0.168627, 0.395780, 0.168627)
                        nd.inputs[1].hide = True
                        inx = 0
                    case 2:
                        nd.color = (0.113725, 0.447058, 0.368627)
                        nd.show_options = False
                        nd.inputs[1].hide = True
                        nd.outputs[0].name = "Geometry"
                        nd.outputs[1].hide = True
                        inx = 0
                #Соединить:
                list_wayTreeNd[cyc][0].links.new(skOut, nd.inputs[inx])
                list_wayTreeNd[cyc][0].links.new(nd.outputs[0], skIn)
            else:
                list_wayTreeNd[cyc][0].links.new(skOut, skIn)
    if self.vpIsSelectPreviewedNode:
        #Выделить предпросматриваемый нод:
        for nd in curTree.nodes:
            nd.select = False
        curTree.nodes.active = goalSk.node #Важно не только то, что только один он выделяется, но ещё и то, что он становится активным.
        goalSk.node.select = True
    return goalSk #Вернуть сокет. Нужно для |3|.

class MixerData:
    sk0 = None
    sk1 = None
    skType = ""
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
mxData = MixerData()

txt_noMixingOptions = "No mixing options"
def DrawMixerSkText(self, cusorPos, fg, ofsY, facY): #Вынесено во вне, чтобы этим мог воспользоваться Swaper Tool.
    txtDim = DrawSkText( self, cusorPos, (self.dsDistFromCursor*(fg.tg.is_output*2-1), ofsY), fg )
    if (fg.tg.links)and(self.dsIsDrawMarker):
        DrawIsLinkedMarker( self, cusorPos, [txtDim[0]*(fg.tg.is_output*2-1), txtDim[1]*facY*0.75], GetSkCol(fg.tg) )
def CallbackDrawVoronoiMixer(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkOut0:
        DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkOut0], isLineToCursor=True, isDrawText=False )
        tgl = not not self.foundGoalSkOut1
        DrawMixerSkText(self, cusorPos, self.foundGoalSkOut0, -0.5+0.75*tgl, int(tgl))
        if tgl:
            DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkOut1], isLineToCursor=True, isDrawText=False )
            DrawMixerSkText(self, cusorPos, self.foundGoalSkOut1, -1.25, -1)
    elif self.dsIsDrawPoint:
        DrawWidePoint(self, cusorPos)
class VoronoiMixerTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    bl_options = {'UNDO'}
    def NextAssessment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        self.foundGoalSkOut1 = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            StencilUnCollapseNode(self, False, nd, isBoth)
            list_fgSksOut = GetNearestSockets(nd, callPos)[1]
            if not list_fgSksOut:
                continue
            #В фильтре нод нет нужды.
            #Этот инструмент триггерится на любой выход (ныне кроме виртуальных) для первого.
            if isBoth:
                for li in list_fgSksOut:
                    if li.tg.bl_idname!='NodeSocketVirtual':
                        self.foundGoalSkOut0 = li
                        break
            #Для второго по условиям:
            skOut0 = self.foundGoalSkOut0.tg if self.foundGoalSkOut0 else None
            if skOut0:
                for li in list_fgSksOut:
                    skOut1 = li.tg
                    #Критерии были такие же, как и у Линкера. Но из-за того, что через api сокеты на виртуальные теперь не создаются, использование виртуальных для миксера выключено.
                    if (skOut1.bl_idname=='NodeSocketVirtual')or(skOut0.bl_idname=='NodeSocketVirtual'):
                        continue
                    tgl = (SkBetweenCheck(skOut1))and(SkBetweenCheck(skOut0))or(skOut1.bl_idname==skOut0.bl_idname)
                    tgl |= ( (skOut0.node.type=='REROUTE')or(skOut1.node.type=='REROUTE') )and(self.vmReroutesCanInAnyType)
                    if tgl:
                        self.foundGoalSkOut1 = li
                        break
                if (self.foundGoalSkOut1)and(skOut0==self.foundGoalSkOut1.tg): #Проверка на самокопию.
                    self.foundGoalSkOut1 = None
                StencilUnCollapseNode(self, True, nd, self.foundGoalSkOut1)
            break
    def modal(self, context, event):
        context.area.tag_redraw()
        isCanNext = True
        if SetCanMoveOut(self, event):
            isCanNext = False
            self.foundGoalSkOut0 = None
            self.foundGoalSkOut1 = None
            VoronoiMixerTool.NextAssessment(self, context, True)
        match event.type:
            case 'MOUSEMOVE':
                if isCanNext:
                    VoronoiMixerTool.NextAssessment(self, context, False)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if self.foundGoalSkOut0: #Теперь можно и с одним.
                    mxData.sk0 = self.foundGoalSkOut0.tg
                    mxData.sk1 = self.foundGoalSkOut1.tg if self.foundGoalSkOut1 else None
                    #Поддержка виртуальных выключена; читается только из первого
                    mxData.skType = mxData.sk0.type# if mxData.sk0.bl_idname!='NodeSocketVirtual' else mxData.sk1.type
                    mxData.isSpeedPie = self.vmPieType=='SPEED'
                    mxData.pieScale = self.vmPieScale
                    mxData.pieDisplaySocketTypeInfo = self.vmPieSocketDisplayType
                    di = dict_dictTupleMixerMain.get(context.space_data.tree_type, False)
                    if not di: #Если место действия не в классических редакторах, то просто выйти. Ибо классические редакторы у всех одинаковые, а аддонских есть бесчисленное множество.
                        return {'CANCELLED'}
                    di = di.get(mxData.skType, None)
                    if di:
                        if length(di)==1: #Если выбор всего один, то пропустить его и сразу переходить к смешиванию.
                            DoMix(context, di[0])
                        else: #Иначе предоставить выбор
                            bpy.ops.wm.call_menu_pie(name=MixerPie.bl_idname)
                    else: #Иначе для типа сокета не определено. Например шейдер в геонодах.
                        def PopupMessage(self, context):
                            self.layout.label(text=txt_noMixingOptions, icon='RADIOBUT_OFF')
                        bpy.context.window_manager.popup_menu(PopupMessage, title="")
                return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if StencilProcPassThrought('vmPassThrought'):
            return {'PASS_THROUGH'}
        self.foundGoalSkOut0 = None
        self.foundGoalSkOut1 = None
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiMixer):
            VoronoiMixerTool.NextAssessment(self, context, True)
        return {'RUNNING_MODAL'}

AddToRegAndAddToKmiDefs(VoronoiMixerTool, "LEFTMOUSE_ScA") #Миксер перенесён на левую, чтобы освободить нагрузку для QMT.

dict_dictTupleMixerMain = { #Порядок важен, самые частые(в этом списке) идут первее (кроме MixRGB).
        'ShaderNodeTree':     {'SHADER':     ('ShaderNodeMixShader','ShaderNodeAddShader'),
                               'VALUE':      ('ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath'),
                               'RGBA':       ('ShaderNodeMixRGB',  'ShaderNodeMix'),
                               'VECTOR':     ('ShaderNodeMixRGB',  'ShaderNodeMix',                                       'ShaderNodeVectorMath'),
                               'INT':        ('ShaderNodeMixRGB',  'ShaderNodeMix',                      'ShaderNodeMath')},

        'GeometryNodeTree':   {'VALUE':      ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath'),
                               'RGBA':       ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare'),
                               'VECTOR':     ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare',                 'ShaderNodeVectorMath'),
                               'STRING':     ('GeometryNodeSwitch',                'FunctionNodeCompare',                                         'GeometryNodeStringJoin'),
                               'INT':        ('GeometryNodeSwitch','ShaderNodeMix','FunctionNodeCompare','ShaderNodeMath'),
                               'BOOLEAN':    ('GeometryNodeSwitch','ShaderNodeMix',                      'ShaderNodeMath',                        'FunctionNodeBooleanMath'),
                               'OBJECT':     ('GeometryNodeSwitch',),
                               'MATERIAL':   ('GeometryNodeSwitch',),
                               'COLLECTION': ('GeometryNodeSwitch',),
                               'TEXTURE':    ('GeometryNodeSwitch',),
                               'IMAGE':      ('GeometryNodeSwitch',),
                               'GEOMETRY':   ('GeometryNodeSwitch','GeometryNodeJoinGeometry','GeometryNodeInstanceOnPoints','GeometryNodeCurveToMesh','GeometryNodeMeshBoolean','GeometryNodeGeometryToInstance')},

        'CompositorNodeTree': {'VALUE':      ('CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeMath'),
                               'RGBA':       ('CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView',                      'CompositorNodeAlphaOver'),
                               'VECTOR':     ('CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'),
                               'INT':        ('CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeMath')},

        'TextureNodeTree':    {'VALUE':      ('TextureNodeMixRGB','TextureNodeTexture','TextureNodeMath'),
                               'RGBA':       ('TextureNodeMixRGB','TextureNodeTexture'),
                               'VECTOR':     ('TextureNodeMixRGB',                                        'TextureNodeDistance'),
                               'INT':        ('TextureNodeMixRGB','TextureNodeTexture','TextureNodeMath')}}
dict_tupleMixerNodesDefs = { #"-1" означает визуальную здесь метку, что их подключения высчитываются автоматически (См. |8|), а не указаны явно в этом списке.
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
def DoMix(context, txt_node):
    tree = context.space_data.edit_tree
    if not tree:
        return
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt_node, use_transform=True)
    aNd = tree.nodes.active
    aNd.width = 140
    txt = {'VALUE':'FLOAT'}.get(mxData.skType, mxData.skType)
    #Дважды switch case -- для комфортного кода и немножко экономии.
    match aNd.bl_idname:
        case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath':
            aNd.operation = 'MAXIMUM'
        case 'FunctionNodeBooleanMath':
            aNd.operation = 'OR'
        case 'TextureNodeTexture':
            aNd.show_preview = False
        case 'GeometryNodeSwitch':
            aNd.input_type = txt
        case 'FunctionNodeCompare':
            aNd.data_type = {'BOOLEAN':'INT'}.get(txt, txt)
            aNd.operation = 'EQUAL'
        case 'ShaderNodeMix':
            aNd.data_type = {'INT':'FLOAT', 'BOOLEAN':'FLOAT'}.get(txt, txt)
    match aNd.bl_idname:
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|8|
            tgl = aNd.bl_idname!='FunctionNodeCompare'
            match aNd.bl_idname:
                case 'GeometryNodeSwitch':  L = lambda a: a
                case 'FunctionNodeCompare': L = lambda a: {'BOOLEAN':'INT'}.get(a, a) #Не используется в dict_dictTupleMixerMain.
                case 'ShaderNodeMix':       L = lambda a: {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(a, a)
            #Для микса и переключателя искать с конца, потому что их сокеты для переключения имеют тип некоторых искомых. У нода сравнения всё наоборот.
            list_foundSk = [sk for sk in (reversed(aNd.inputs) if tgl else aNd.inputs) if sk.type==L(mxData.skType)]
            tree.links.new(mxData.sk0, list_foundSk[tgl]) #Из-за направления поиска, нужно выбирать их из списка так же с учётом направления.
            if mxData.sk1:
                tree.links.new(mxData.sk1, list_foundSk[not tgl])
        case _:
            #Такая плотная суета ради мультиинпута -- для него нужно изменить порядок подключения.
            if (mxData.sk1)and(aNd.inputs[dict_tupleMixerNodesDefs[aNd.bl_idname][0]].is_multi_input):
                tree.links.new( mxData.sk1, aNd.inputs[dict_tupleMixerNodesDefs[aNd.bl_idname][1]] )
            tree.links.new( mxData.sk0, aNd.inputs[dict_tupleMixerNodesDefs[aNd.bl_idname][0]] )
            if (mxData.sk1)and(not aNd.inputs[dict_tupleMixerNodesDefs[aNd.bl_idname][0]].is_multi_input):
                tree.links.new( mxData.sk1, aNd.inputs[dict_tupleMixerNodesDefs[aNd.bl_idname][1]] )
class MixerMixer(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = "Mixer Mixer"
    bl_options = {'UNDO'}
    txt: bpy.props.StringProperty()
    def execute(self, context):
        DoMix(context, self.txt)
        return {'FINISHED'}
class MixerPie(bpy.types.Menu):
    bl_idname = 'VL_MT_voronoi_mixer_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, context):
        pie = self.layout.menu_pie()
        def AddOp(where, txt):
            where.operator(MixerMixer.bl_idname, text=dict_tupleMixerNodesDefs[txt][2], translate=False).txt = txt
        dict_items = dict_dictTupleMixerMain[context.space_data.tree_type][mxData.skType]
        if mxData.isSpeedPie:
            for li in dict_items:
                AddOp(pie, li)
        else:
            def GetPieCol(where):
                box = where.box()
                col = box.column()
                col.ui_units_x = 6*((mxData.pieScale-1)/2+1)
                col.scale_y = mxData.pieScale
                return col
            colLeft = GetPieCol(pie)
            colRight = GetPieCol(pie)
            if mxData.pieDisplaySocketTypeInfo>0:
                GetPieCol(pie)
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    row2 = colLeft.row()
                    row2.enabled = False
                    AddOp(row2, 'ShaderNodeMix')
                case 'GeometryNodeTree':
                    row1 = colLeft.row()
                    row2 = colLeft.row()
                    row3 = colLeft.row()
                    row1.enabled = False
                    row2.enabled = False
                    row3.enabled = False
                    AddOp(row1, 'GeometryNodeSwitch')
                    AddOp(row2, 'ShaderNodeMix')
                    AddOp(row3, 'FunctionNodeCompare')
            for li in dict_items:
                match li:
                    case 'GeometryNodeSwitch':  row1.enabled = True
                    case 'ShaderNodeMix':       row2.enabled = True
                    case 'FunctionNodeCompare': row3.enabled = True
                    case _:
                        AddOp(colRight, li)
            if mxData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=GetSkCol(mxData.sk0))
                row.label(text=mxData.sk0.bl_label)

list_classes += [MixerMixer, MixerPie]

class QuickMathData:
    list_displayItems = []
    sk0 = None
    sk1 = None
    depth = 0
    isVec = False
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
qmData = QuickMathData()

set_skFieldTypes = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN'}
set_skFieldArrTypes = {'VECTOR', 'RGBA'}

class VoronoiQuickMathTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_quick_math'
    bl_label = "Voronoi Quick Math"
    bl_options = {'UNDO'}
    def NextAssessment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        self.foundGoalSkOut1 = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            StencilUnCollapseNode(self, False, nd)
            list_fgSksOut = GetNearestSockets(nd, callPos)[1]
            if not list_fgSksOut:
                continue
            #Этот инструмент триггерится только на выходы поля.
            if isBoth:
                tgl = True
                for li in list_fgSksOut:
                    if li.tg.type in set_skFieldTypes:
                        self.foundGoalSkOut0 = li
                        tgl = False
                        break
                if tgl:
                    continue #Искать нод, у которого попадёт на сокет поля.
                nd.hide = False #После чего в любом случае развернуть его.
            #Для второго по условиям:
            skOut0 = self.foundGoalSkOut0.tg if self.foundGoalSkOut0 else None
            if skOut0:
                tgl = True
                for li in list_fgSksOut:
                    if li.tg.type in set_skFieldTypes: #Так же, как и для первого.
                        self.foundGoalSkOut1 = li
                        tgl = False
                        break
                if tgl:
                    continue
                if (self.foundGoalSkOut1)and(skOut0==self.foundGoalSkOut1.tg): #Проверка на самокопию.
                    self.foundGoalSkOut1 = None
                StencilUnCollapseNode(self, True, nd, self.foundGoalSkOut1)
            break
    def modal(self, context, event):
        context.area.tag_redraw()
        isCanNext = True
        if SetCanMoveOut(self, event):
            isCanNext = False
            self.foundGoalSkOut0 = None
            VoronoiQuickMathTool.NextAssessment(self, context, True)
        match event.type:
            case 'MOUSEMOVE':
                if isCanNext:
                    VoronoiQuickMathTool.NextAssessment(self, context, False)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if self.foundGoalSkOut0:
                    qmData.sk0 = self.foundGoalSkOut0.tg
                    qmData.sk1 = self.foundGoalSkOut1.tg if self.foundGoalSkOut1 else None
                    qmData.depth = 0
                    qmData.isSpeedPie = self.vqmPieType=='SPEED'
                    qmData.pieScale = self.vqmPieScale
                    qmData.pieDisplaySocketTypeInfo = self.vqmPieSocketDisplayType
                    #Наличие только сокетов поля -- забота на уровень выше.
                    isVec1 = qmData.sk0.type in set_skFieldArrTypes
                    if not qmData.sk1:
                        qmData.isVec = isVec1
                    else:
                        isVec2 = qmData.sk1.type in set_skFieldArrTypes
                        if isVec1==isVec2:
                            qmData.isVec = isVec1
                        else:
                            match self.vqmDimensionConflictPriority:
                                case 'FIRST':  qmData.isVec = isVec1
                                case 'LAST':   qmData.isVec = isVec2
                                case 'VECTOR': qmData.isVec = True
                                case 'FLOAT':  qmData.isVec = False
                    bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
                return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if StencilProcPassThrought('vqmPassThrought'):
            return {'PASS_THROUGH'}
        self.foundGoalSkOut0 = None
        self.foundGoalSkOut1 = None
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiMixer): #Каллбак от Миксера! Потому что одинаковы.
            VoronoiQuickMathTool.NextAssessment(self, context, True)
        return {'RUNNING_MODAL'}

AddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "RIGHTMOUSE_ScA") #Осталось на правой, чтобы не охреневать от тройного клика левой при 'Speed Pie' типе пирога.

#Быстрая математика.
#Заполучить нод с нужной операцией и автоматическим соединением в сокеты, благодаря мощностям VL'а.
#Неожиданно для меня оказалось, что пирог может рисовать обычный layout. От чего добавил дополнительный тип пирога "для контроля".
#А так же сам буду пользоваться им, потому что за то время, которое экономится при двойном пироге, отдохнуть как-то всё равно не получается.

#Важная эстетическая ценность двойного пирога -- визуальная неперегруженность вариантами. Вместо того, чтобы вываливать всё сразу, показываются только по 8 штук максимум.
tuple_tupleTubpleQuickMathMap = ( (
        #Было бы бездумно разбросать их как попало, поэтому я пытался соблюсти некоторую логическую последовательность. Например, расставляя пары по смыслу диаметрально противоположными.
        #Пирог Блендера располагает в себе элементы следующим образом: лево, право, низ, верх, после чего классическое построчное заполнение.
        #"Compatible..." -- чтобы у векторов и у математики одинаковые операции были на одинаковых местах (кроме тригонометрических).
        ("Advanced",              ('SQRT',       'POWER',        'EXPONENT',   'LOGARITHM',   'INVERSE_SQRT','PINGPONG')),
        ("Compatible Primitives", ('SUBTRACT',   'ADD',          'DIVIDE'   ,  'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD')),
        ("Rounding",              ('SMOOTH_MIN', 'SMOOTH_MAX',   'LESS_THAN',  'GREATER_THAN','SIGN',        'COMPARE',     'TRUNC',  'ROUND')),
        ("Compatible Vector",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACT',        'CEIL',       'MODULO',      'SNAP',   'WRAP')),
        ("", ()), #Важны дубликаты и порядок, поэтому не словарь а список.
        ("", ()),
        ("Other",                 ('COSH',       'RADIANS',      'DEGREES',    'SINH',        'TANH')),
        ("Trigonometric",         ('SINE',       'COSINE',       'TANGENT',    'ARCTANGENT',  'ARCSINE',     'ARCCOSINE',   'ARCTAN2'))
        ), (
        #За исключением примитивов, где прослеживается супер очевидная логика (право -- плюс -- add, лево -- минус -- sub; всё как на числовой оси),
        # лево и низ у меня более просты, чем обратная сторона.
        #Например, length проще, чем distance. Всем же остальным не очевидным и не осе-ориентированным досталось как получится.
        ("Advanced",              ('SCALE',      'NORMALIZE',    'LENGTH',     'DISTANCE',    'SINE',        'COSINE',      'TANGENT')),
        ("Compatible Primitives", ('SUBTRACT',   'ADD',          'DIVIDE',     'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD')),
        ("Rays",                  ('DOT_PRODUCT','CROSS_PRODUCT','PROJECT',    'FACEFORWARD', 'REFRACT',     'REFLECT')),
        ("Compatible Vector",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACTION',    'CEIL',        'MODULO',      'SNAP',   'WRAP')),
        ("", ()),
        ("", ()),
        ("", ()),
        ("", ()) ) )
#Ассоциация типа нода математики для типа редактируемого дерева
tuple_dictEditorMathNodes = ( {'ShaderNodeTree':     'ShaderNodeMath',
                               'GeometryNodeTree':   'ShaderNodeMath',
                               'CompositorNodeTree': 'CompositorNodeMath',
                               'TextureNodeTree':    'TextureNodeMath'},
                              {'ShaderNodeTree':   'ShaderNodeVectorMath',
                               'GeometryNodeTree': 'ShaderNodeVectorMath'} )
class QuickMathMain(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_quick_math_main'
    bl_label = "Quick Math"
    bl_options = {'UNDO'}
    operation: bpy.props.StringProperty()
    def modal(self, context, event):
        #Раньше нужно было отчищать мост вручную, потому что он оставался равным последней записи. Сейчас уже не нужно.
        return {'FINISHED'}
    def invoke(self, context, event):
        tree = context.space_data.edit_tree
        if not tree:
            return {'CANCELLED'}
        match qmData.depth:
            case 0:
                if qmData.isSpeedPie:
                    qmData.list_displayItems = [ti[0] for ti in tuple_tupleTubpleQuickMathMap[qmData.isVec]]
                else:
                    qmData.depth += 1
            case 1:
                if qmData.isSpeedPie:
                    qmData.list_displayItems = [ti[1] for ti in tuple_tupleTubpleQuickMathMap[qmData.isVec] if ti[0]==self.operation][0] #И вычленить кортеж из этого генератора.
            case 2:
                txt = tuple_dictEditorMathNodes[qmData.isVec].get(context.space_data.tree_type, "")
                if not txt: #Если нет в списке, то этот нод отсутствует в типе редактора => "смешивать" нечем.
                    return {'CANCELLED'}
                #Ядро быстрой математики, добавить нод и создать линки:
                bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt, use_transform=True)
                aNd = tree.nodes.active
                aNd.operation = self.operation
                tree.links.new(qmData.sk0, aNd.inputs[0])
                if qmData.sk1:
                    #Второй ищется "визуально"; чтобы операция 'SCALE' корректно соединялась.
                    for sk in aNd.inputs: #Ищется сверху вниз. Потому что ещё 'MulAdd'
                        if (sk.enabled)and(not sk.links):
                            tree.links.new(qmData.sk1, sk)
                            break #Нужно соединить только в первый попавшийся, иначе будет соединено во все (например у 'MulAdd')
                #Обнулить содержимое второго сокета. Нужно для красоты; и вообще это математика.
                if not qmData.isVec: #Теперь нод вектора уже создаётся по нулям, так что для него обнулять без нужды.
                    for sk in aNd.inputs:
                        sk.default_value = 0.0
                return {'FINISHED'}
        qmData.depth += 1
        bpy.ops.wm.call_menu_pie(name=QuickMathPie.bl_idname)
        return {'RUNNING_MODAL'}
class QuickMathPie(bpy.types.Menu):
    bl_idname = 'VL_MT_voronoi_quick_math_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, context):
        def AddOp(where, txt, ico='NONE'):
            #if qmData.pieDisplaySocketTypeInfo==2:  #|15| todo после того как придумаю, как забинарить два цвета, добавить их сюда; а так же todо ниже.
                #where = where.row(); where.template_node_socket(color=GetSkCol(qmData.sk0))
            #Автоматический перевод выключен, ибо оригинальные операции у нода математики тоже не переводятся.
            where.operator(QuickMathMain.bl_idname, text=txt.capitalize() if qmData.depth else txt, icon=ico, translate=False).operation = txt
        pie = self.layout.menu_pie()
        if qmData.isSpeedPie:
            for li in qmData.list_displayItems:
                if not li:
                    row = pie.row()
                    continue
                AddOp(pie, li)
        else:
            def GetPieCol(where):
                col = where.column()
                col.ui_units_x = 5.5*((qmData.pieScale-1)/2+1)
                col.scale_y = qmData.pieScale
                return col
            colLeft = GetPieCol(pie)
            colRight = GetPieCol(pie)
            colCenter = GetPieCol(pie)
            if qmData.pieDisplaySocketTypeInfo==1:
                colLabel = pie.column()
                box = colLabel.box()
                row = box.row(align=True)
                #todo: Должно быть только двух цветов, для вектора и для флоата, но чувствую, будет много костылей. Сейчас лень грамотно реализовывать.
                row.template_node_socket(color=GetSkCol(qmData.sk0))
                row.label(text=("Vector" if qmData.isVec else "Float")+" Fast Math")
                row.alignment = 'CENTER'
            AddOp(colRight,'ADD',     'ADD')
            AddOp(colRight,'SUBTRACT','REMOVE')
            AddOp(colRight,'MULTIPLY','SORTBYEXT')
            AddOp(colRight,'DIVIDE',  'ITALIC') #ITALIC  FIXED_SIZE  DECORATE_LINKED
            colRight.separator()
            AddOp(colRight, 'MULTIPLY_ADD')
            AddOp(colRight, 'ABSOLUTE')
            colRight.separator()
            for li in ('SINE','COSINE','TANGENT'):
                AddOp(colCenter, li, 'FORCE_HARMONIC')
            if not qmData.isVec:
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
            for li in ('MODULO', 'SNAP', 'WRAP'):
                AddOp(colLeft, li)
            colLeft.separator()
            if not qmData.isVec:
                for li in ('GREATER_THAN','LESS_THAN','TRUNC','SIGN','SMOOTH_MAX','SMOOTH_MIN','ROUND','COMPARE'):
                    AddOp(colLeft, li)
            else:
                AddOp(colLeft,'DOT_PRODUCT',  'LAYER_ACTIVE')
                AddOp(colLeft,'CROSS_PRODUCT','ORIENTATION_LOCAL') #OUTLINER_DATA_EMPTY  ORIENTATION_LOCAL  EMPTY_ARROWS
                AddOp(colLeft,'PROJECT',      'CURVE_PATH') #SNAP_OFF  SNAP_ON  MOD_SIMPLIFY  CURVE_PATH
                AddOp(colLeft,'FACEFORWARD',  'ORIENTATION_NORMAL')
                AddOp(colLeft,'REFRACT',      'NODE_MATERIAL') #MOD_OFFSET  NODE_MATERIAL
                AddOp(colLeft,'REFLECT',      'INDIRECT_ONLY_OFF') #INDIRECT_ONLY_OFF  INDIRECT_ONLY_ON

list_classes += [QuickMathMain, QuickMathPie]

def CallbackDrawVoronoiSwapper(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkIo0:
        DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkIo0], isLineToCursor=True, isDrawText=False )
        tgl = not not self.foundGoalSkIo1
        DrawMixerSkText(self, cusorPos, self.foundGoalSkIo0, -0.5+0.75*tgl, int(tgl))
        if tgl:
            DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkIo1], isLineToCursor=True, isDrawText=False )
            DrawMixerSkText(self, cusorPos, self.foundGoalSkIo1, -1.25, -1)
    elif self.dsIsDrawPoint:
        DrawWidePoint(self, cusorPos)
class VoronoiSwapperTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_swaper'
    bl_label = "Voronoi Swapper"
    bl_options = {'UNDO'}
    isAddMode: bpy.props.BoolProperty()
    def NextAssessment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        self.foundGoalSkIo1 = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            if StencilUnCollapseNode(self, False, nd, isBoth):
                #|16| Чтобы начать отсчёт снизу, туда нужно переместиться на высоту нода. А нод-то свёрнут! Поэтому его нужно развернуть перед вычислением сокетов с перерисовкой.
                bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=0)
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos)
            #За основу взяты критерии от Миксера.
            if isBoth:
                fgSkOut, fgSkIn = None, None
                for li in list_fgSksOut:
                    if li.tg.bl_idname!='NodeSocketVirtual':
                        fgSkOut = li
                        break
                for li in list_fgSksIn:
                    if li.tg.bl_idname!='NodeSocketVirtual':
                        fgSkIn = li
                        break
                #Разрешить возможность "добавлять" и для входов тоже, но только для мультиинпутов, ибо очевидное
                if (self.isAddMode)and(fgSkIn):
                    #Проверка по типу, но не по `is_multi_input`, чтобы из обычного в мультиинпут можно было добавлять.
                    if (fgSkIn.tg.bl_idname not in ('NodeSocketGeometry','NodeSocketString')):#or(not fgSkIn.tg.is_multi_input): #Без второго условия больше возможностей.
                        fgSkIn = None
                self.foundGoalSkIo0 = MinFromFgs(fgSkOut, fgSkIn)
                #Здесь вокруг аккумулировалось много странных проверок с None и т.п. -- результат соединения вместе многих "типа высокоуровневых" функций, что я тут понаизобретал.
            skOut0 = self.foundGoalSkIo0.tg if self.foundGoalSkIo0 else None
            if skOut0:
                for li in list_fgSksOut if skOut0.is_output else list_fgSksIn:
                    if li.tg.bl_idname=='NodeSocketVirtual':
                        continue
                    if not self.vsCanTriggerToAnyType: #Типа мини-оптимизация.
                        tgl = SkBetweenCheck(skOut0)
                    if (self.vsCanTriggerToAnyType)or(skOut0.type==li.tg.type)or( (tgl)and(tgl==SkBetweenCheck(li.tg)) ):
                        self.foundGoalSkIo1 = li
                    if self.foundGoalSkIo1: #В случае успеха прекращать поиск.
                        break
                if (self.foundGoalSkIo1)and(skOut0==self.foundGoalSkIo1.tg): #Проверка на самокопию.
                    self.foundGoalSkIo1 = None
                    break #Ломать для vsCanTriggerToAnyType, когда isBoth==False и сокет оказался самокопией; чтобы не находил сразу два нода.
                if not self.vsCanTriggerToAnyType:
                    if not self.foundGoalSkIo1: #Если нет результата, продолжать искать.
                        continue
                StencilUnCollapseNode(self, True, nd, self.foundGoalSkIo1)
            break
    def modal(self, context, event):
        context.area.tag_redraw()
        isCanNext = True
        if SetCanMoveOut(self, event):
            isCanNext = False
            self.foundGoalSkIo0 = None
            self.foundGoalSkIo1 = None
            VoronoiSwapperTool.NextAssessment(self, context, True)
        match event.type:
            case 'MOUSEMOVE':
                if isCanNext:
                    VoronoiSwapperTool.NextAssessment(self, context, False)
            case self.keyType|'ESC':
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
                        if skIo0.is_output: #Проверка одинаковости is_output -- забота для NextAssessment.
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
                    return {'FINISHED'}
                return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if StencilProcPassThrought('vsPassThrought'):
            return {'PASS_THROUGH'}
        self.foundGoalSkIo0 = None
        self.foundGoalSkIo1 = None
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiSwapper):
            VoronoiSwapperTool.NextAssessment(self, context, True)
        return {'RUNNING_MODAL'}

list_classes += [VoronoiSwapperTool]
AddToKmiDefs(VoronoiSwapperTool, "S_scA", {'isAddMode': True })
AddToKmiDefs(VoronoiSwapperTool, "S_Sca", {'isAddMode': False })

#Нужен только для наведения порядка и эстетики в дереве.
#Для тех, кого (например меня) напрягают "торчащие без дела" пустые сокеты выхода, или нулевые (чьё значение 0.0, чёрный, и т.п.) незадействованные сокеты входа.
def CallbackDrawVoronoiHider(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if self.isHideSocket:
        if self.foundGoalTg:
            DrawToolOftenStencil( self, cusorPos, [self.foundGoalTg], isLineToCursor=True, textSideFlip=True )
        elif self.dsIsDrawPoint:
            DrawWidePoint(self, cusorPos)
    else:
        if self.foundGoalTg:
            #Нод не имеет цвета (в этом аддоне вся тусовка ради сокетов, так что нод не имеет цвета, ок да?.)
            #Поэтому, для нода всё одноцветное -- пользовательское для нода, или пользовательское постоянной перезаписи.
            colNode = DrawNodeStencil(self, cusorPos, self.foundGoalTg.pos)
            DrawTextNodeStencil(self, cusorPos, self.foundGoalTg.tg, self.vhDrawNodeNameLabel, self.vhLabelDispalySide, colNode)
        elif self.dsIsDrawPoint:
            DrawWidePoint(self, cusorPos)
class VoronoiHiderTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_hider'
    bl_label = "Voronoi Hider"
    bl_options = {'UNDO'}
    isHideSocket: bpy.props.IntProperty()
    def NextAssessment(self, context):
        if not context.space_data.edit_tree:
            return
        self.foundGoalTg = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            if (not self.vhTriggerOnCollapsedNodes)and(nd.hide):
                continue
            #Для этого инструмента рероуты пропускаются, по очевидным причинам.
            if nd.type=='REROUTE':
                continue
            self.foundGoalTg = li
            if self.isHideSocket:
                #Для режима сокетов обработка свёрнутости так же как у всех.
                tgl = StencilUnCollapseNode(self, False, nd)
                list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos)
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
                tgl |= StencilUnCollapseNode(self, True, nd, self.foundGoalTg)
                if (tgl)and(self.vhRedrawAfterChange):
                    StencilRepick(VoronoiHiderTool, self, context) #Для режима сокетов тоже нужно перерисовывать. todo: я забыл почему.
            else:
                #Для режима нод нет разницы, раскрывать все подряд под курсором, или нет.
                if self.vtAlwaysUnhideCursorNode: #Благодаря этому можно выбрать, разворачивать нод при обработке, или нет.
                    # К тому же логически совпадает со всем остальным. Только при ^ False никого не разворачивает.
                    # aucn: False    True
                    # Все:  Частично Все
                    # VHT:  Никто    Все
                    nd.hide = False
                if self.vhIsToggleNodesOnDrag:
                    if self.firstResult is None:
                        self.firstResult = HideFromNode(self.foundGoalTg.tg, True) #todo: вспомнить, почему `self.foundGoalTg.tg`.
                    if HideFromNode(nd, self.firstResult, True)and(self.vhRedrawAfterChange):
                        #Ну наконец-то смог починить. С одной стороны нет проскальзывающего кадра, с другой стороны нет "визуального" контакта с только что изменённым нодом,
                        # если после изменения ближайшим оказался другой нод. По крайней мере такие ситуации редки.
                        #Есть ещё вариант сделать изменение нода после отрисовки одного кадра, но наверное окажется тоже не очень.
                        StencilRepick(VoronoiHiderTool, self, context)
            break
    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiHiderTool.NextAssessment(self, context)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if self.foundGoalTg:
                    match self.isHideSocket:
                        case 0: #Обработка нода.
                            if not self.vhIsToggleNodesOnDrag:
                                #Во время сокрытия сокета нужно иметь информацию обо всех, поэтому выполняется дважды. В первый заход собирается, во второй выполняется.
                                HideFromNode(self.foundGoalTg.tg, HideFromNode(self.foundGoalTg.tg, True), True)
                        case 1: #Скрытие сокета.
                            self.foundGoalTg.tg.hide = True
                        case 2: #Переключение видимости значения сокета.
                            self.foundGoalTg.tg.hide_value = not self.foundGoalTg.tg.hide_value
                return {'FINISHED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if StencilProcPassThrought('vhPassThrought'):
            return {'PASS_THROUGH'}
        self.foundGoalTg = []
        self.firstResult = None #Получить действие "свернуть" или "развернуть" у первого нода, а потом транслировать его на все остальные попавшиеся.
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiHider):
            VoronoiHiderTool.NextAssessment(self, context)
        return {'RUNNING_MODAL'}

list_classes += [VoronoiHiderTool]
AddToKmiDefs(VoronoiHiderTool, "E_scA", {'isHideSocket': 2})
AddToKmiDefs(VoronoiHiderTool, "E_Sca", {'isHideSocket': 1})
AddToKmiDefs(VoronoiHiderTool, "E_sCa", {'isHideSocket': 0})

#todo: учитывая, что есть моя хотелка для виртуальных в VLT, нужно ли вообще рскрывать последние виртуальные?
def HideFromNode(nd, lastResult, isCanDo=False): #Изначально лично моя утилита, была создана ещё до VL.
    def CheckSkZeroDefaultValue(sk): #Shader, Geometry и Virtual всегда True.
        match sk.type:
            case 'VALUE'|'INT':
                return sk.default_value==0
            case 'VECTOR'|'RGBA':
                return(sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0)
            case 'STRING':
                return sk.default_value==''
            case 'OBJECT'|'MATERIAL'|'COLLECTION'|'TEXTURE'|'IMAGE':
                return not sk.default_value
            case 'BOOLEAN':
                if not sk.hide_value: #Лень паять, всё обрабатывается в прямом виде.
                    match vhHideBoolSocket:
                        case 'ALWAYS': return True
                        case 'NEVER': return False
                        case 'IF_TRUE': return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
                else:
                    match vhHideHiddenBoolSocket:
                        case 'ALWAYS': return True
                        case 'NEVER': return False
                        case 'IF_TRUE': return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
            case _:
                return True
    prefs = Prefs()
    vhHideBoolSocket = prefs.vhHideBoolSocket
    vhHideHiddenBoolSocket = prefs.vhHideHiddenBoolSocket
    if lastResult: #Результат предыдущего анализа, есть ли сокеты чьё состояние изменилось бы. Нужно для 'isCanDo'.
        def CheckAndDoForIo(where, L):
            success = False
            for sk in where:
                if (sk.enabled)and(not sk.links)and(L(sk)):
                    success = (success)or(not sk.hide)
                    if isCanDo:
                        sk.hide = True
            return success
        tgl = False
        #todo: повторно осознать что здесь происходит (от сюда и до конца), и закоментить подробнее.
        if nd.type=='GROUP_INPUT': #Эта проверка для эстетики оптимизации; строчка ниже нужна для LCheckOver.
            tgl = length([nd for nd in nd.id_data.nodes if nd.type=='GROUP_INPUT'])>1
        #Если виртуальные были созданы вручную, то у nd io групп не скрывать их. Потому что.
        LCheckOver = lambda sk: not( (sk.bl_idname=='NodeSocketVirtual')and
                                     (not tgl)and #Но если nd i групп больше одного, то всё равно скрывать.
                                     (nd.type in {'GROUP_INPUT','GROUP_OUTPUT'})and #Возможно стоило оставить `sk.node.type` эстетики ради.
                                     (GetSocketIndex(sk)!=length(sk.node.outputs if sk.is_output else sk.node.inputs)-1) )
        success = CheckAndDoForIo(nd.inputs, lambda sk: CheckSkZeroDefaultValue(sk)and(LCheckOver(sk)) )
        if [sk for sk in nd.outputs if (sk.enabled)and(sk.links)]: #Если хотя бы один сокет подсоединён во вне.
            success |= CheckAndDoForIo(nd.outputs, lambda sk: LCheckOver(sk) ) #Здесь наоборот, чтобы функция гарантированно выполнилась. #todo: о чём наоборот?
        else:
            if nd.type in {'GROUP_INPUT','GROUP_OUTPUT','SIMULATION_INPUT','SIMULATION_OUTPUT'}: #Всё равно переключать последний виртуальный, даже если нет соединений во вне.
                if nd.outputs:
                    sk = nd.outputs[-1]
                    if sk.bl_idname=='NodeSocketVirtual':
                        success |= not sk.hide
                        if isCanDo:
                            sk.hide = True
        return success
    elif isCanDo: #Иначе раскрыть всё.
        success = False
        for ndio in (nd.inputs, nd.outputs):
            for sk in ndio:
                success = success or sk.hide
                sk.hide = False
        return success #todo: вспомнить, зачем нужен успех при раскрытии. Наверное для Repick'а.

#"Массовый линкер" -- как линкер, только много за раз (ваш кэп). Наверное, самое редко-бесполезное что только можно было придумать здесь.
#Этот инструмент -- "из пушки по редким птичкам", крупица удобного наслаждения один раз в сто лет.
#См. вики на гитхабе, что бы посмотреть 4 примера использования массового линкера. Дайте мне знать, если обнаружите ещё одно необычное применение этому инструменту.

#Здесь нарушается местная концепция чтения-записи, и CallbackDraw ищет и записывает найденные сокеты вместо того, чтобы просто читать и рисовать. Пологаю, так инструмент проще реализовывать.
def CallbackDrawVoronoiMassLinker(self, context):
    try:
        if StencilStartDrawCallback(self, context):
            return
        cusorPos = context.space_data.cursor_location
        if not self.ndGoalOut:
            DrawDoubleNone(self, context)
        elif (self.ndGoalOut)and(not self.ndGoalIn):
            list_fgSksOut = GetNearestSockets(self.ndGoalOut, cusorPos)[1]
            if not list_fgSksOut:
                DrawDoubleNone(self, context)
            for li in list_fgSksOut: #Не известно, к кому это будет подсоединено и к кому получится => рисовать от всех сокетов.
                DrawToolOftenStencil( self, cusorPos, [li], isLineToCursor=self.dsIsAlwaysLine, isDrawText=False ) #Всем к курсору!
        else:
            self.list_equalFgSks = [] #Отчищать каждый раз.
            list_fgSksOut = GetNearestSockets(self.ndGoalOut, cusorPos)[1]
            list_fgSksIn =  GetNearestSockets(self.ndGoalIn,  cusorPos)[0]
            for liSko in list_fgSksOut:
                for liSki in list_fgSksIn:
                    #Т.к. "массовый" -- критерии приходится автоматизировать и сделать их едиными для всех.
                    #Соединяться только с одинаковыми по именам сокетами
                    if (liSko.tg.name==liSki.tg.name):
                        tgl = False
                        if self.vmlIsIgnoreExistingLinks: #Если соединяться без разбору, то исключить уже имеющиеся "желанные" связи. Нужно только для эстетики.
                            for lk in liSki.tg.links:
                                #Проверка is_linked нужна, чтобы можно было включить выключенные линки, перезаменив их.
                                if (lk.from_socket.is_linked)and(lk.from_socket==liSko.tg):
                                    tgl = True
                            tgl = not tgl
                        else: #Иначе не трогать уже соединённых.
                            tgl = not liSki.tg.links
                        if tgl:
                            self.list_equalFgSks.append( (liSko,liSki) )
                        continue
            if not self.list_equalFgSks:
                DrawWidePoint(self, cusorPos)
            for li in self.list_equalFgSks:
                #Т.к. поиск по именам, рисоваться здесь и подсоединяться ниже, возможно из двух (и больше) сокетов в один и тот же одновременно. Типа "конфликт" одинаковых имён.
                DrawToolOftenStencil( self, cusorPos, [li[0],li[1]], isDrawText=False )
    except Exception as ex:
        pass; print("VL CallbackDrawVoronoiMassLinker() --", ex)
class VoronoiMassLinkerTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_mass_linker'
    bl_label = "Voronoi MassLinker"
    bl_options = {'UNDO'}
    #MassLinker
    vmlIsIgnoreExistingLinks: bpy.props.BoolProperty()
    def NextAssessment(self, context, isBoth):
        if not context.space_data.edit_tree:
            return
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            StencilUnCollapseNode(self, False, nd, isBoth)
            #Помимо свёрнутых так же игнорируются и рероуты, потому что у них инпуты всегда одни и с одинаковыми названиями.
            if nd.type=='REROUTE':
                continue
            self.ndGoalIn = nd
            if isBoth:
                self.ndGoalOut = nd #Здесь нод-вывод устанавливается один раз.
            break
        if self.ndGoalOut==self.ndGoalIn: #Проверка на самокопию.
            self.ndGoalIn = None #Здесь нод-вход обнуляется каждый раз в случае неудачи.
        StencilUnCollapseNode(self, True, nd, self.ndGoalIn)
    def modal(self, context, event):
        context.area.tag_redraw()
        isCanNext = True
        if SetCanMoveOut(self, event):
            isCanNext = False
            self.foundGoalSkOut0 = None
            self.foundGoalSkOut1 = None
            VoronoiMassLinkerTool.NextAssessment(self, context, True)
        match event.type:
            case 'MOUSEMOVE':
                if isCanNext:
                    VoronoiMassLinkerTool.NextAssessment(self, context, False)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if (self.ndGoalOut)and(self.ndGoalIn):
                    tree = context.space_data.edit_tree
                    #Проверка на потерянный редактор
                    if (self.list_equalFgSks)and(self.list_equalFgSks[0][0].tg.bl_idname=='NodeSocketUndefined'):
                        return {'CANCELLED'}
                    #Соединить всех!
                    for li in self.list_equalFgSks:
                        tree.links.new(li[0].tg, li[1].tg)
                    return {'FINISHED'}
                return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if StencilProcPassThrought('vmlPassThrought'):
            return {'PASS_THROUGH'}
        self.ndGoalOut = None
        self.ndGoalIn = None
        self.list_equalFgSks = [] #Однажды необычным странным образом, modal() не смог найти этот атрибут в себе. Поэтому продублировал сюда.
        self.isDrawTwoPoints = True
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiMassLinker):
            VoronoiMassLinkerTool.NextAssessment(self, context, True)
        return {'RUNNING_MODAL'}

list_classes += [VoronoiMassLinkerTool]
AddToKmiDefs(VoronoiMassLinkerTool, "RIGHTMOUSE_SCA", {'vmlIsIgnoreExistingLinks': True })
AddToKmiDefs(VoronoiMassLinkerTool, "LEFTMOUSE_SCA", {'vmlIsIgnoreExistingLinks': False })

class EnumSelectorData:
    list_enumProps = [] #Для пайки, и проверка перед вызовом, есть ли вообще что.
    nd = None
    boxScale = 1.0 #Если забыть установить, то хотя бы коробка не сколлапсируется в ноль.
    isDarkStyle = False
    isDisplayLabels = False
    isOneChoise = False
esData = EnumSelectorData()

def GetListOfNdEnums(nd):
    return [li for li in nd.bl_rna.properties if not(li.is_readonly or li.is_registered)and(li.type=='ENUM')]

def CallbackDrawVoronoiEnumSelector(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalNd:
        #Так же, как и для VHT.
        colNode = DrawNodeStencil(self, cusorPos, self.foundGoalNd.pos)
        if self.vesIsDrawEnumNames: #Именно поэтому шаблон рисования для нода был разделён на два шаблона.
            sco = -0.5
            col = colNode if self.dsIsColoredSkText else GetUniformColVec(self)
            for li in self.foundGoalNd.tg.bl_rna.properties:
                if not(li.is_readonly or li.is_registered):
                    if li.type=='ENUM':
                        DrawText( self, cusorPos, (self.dsDistFromCursor, sco), TranslateIface(li.name), col)
                        sco -= 1.5
        else:
            DrawTextNodeStencil(self, cusorPos, self.foundGoalNd.tg, self.vesDrawNodeNameLabel, self.vesLabelDispalySide, colNode)
    elif self.dsIsDrawPoint:
        DrawWidePoint(self, cusorPos)
class VoronoiEnumSelectorTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_enum_selector'
    bl_label = "Voronoi Enum Selector"
    bl_options = {'UNDO'}
    isToggleOptions: bpy.props.BoolProperty()
    isOneChoise:     bpy.props.BoolProperty()
    def NextAssessment(self, context):
        self.foundGoalNd = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos, skipPoorNodes=False):
            nd = li.tg
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            if self.isToggleOptions:
                self.foundGoalNd = li
                #Так же, как и в VHT:
                if self.vesIsToggleNodesOnDrag:
                    if self.firstResult is None:
                        self.firstResult = ToggleOptionsFromNode(nd, True)
                    if ToggleOptionsFromNode(nd, self.firstResult, True)and(self.vesRedrawAfterChange):
                        StencilRepick(VoronoiEnumSelectorTool, self, context)
                break
            else:
                #Почему бы не игнорировать ноды без енум свойств?.
                if GetListOfNdEnums(nd):
                    self.foundGoalNd = li
                    break
    def DoActivation(self): #Для моментальной активации, сразу из invoke().
        if self.foundGoalNd:
            esData.list_enumProps = GetListOfNdEnums(self.foundGoalNd.tg)
            #Если ничего нет, то вызов коробки всё равно обрабатывается, словно она есть, и от чего повторый вызов инструмента не работает без движения курсора.
            if esData.list_enumProps: #Поэтому если пусто, то ничего не делаем.
                esData.nd = self.foundGoalNd.tg
                esData.boxScale = self.vesBoxScale
                esData.isDarkStyle = self.vesDarkStyle
                esData.isDisplayLabels = self.vesDisplayLabels
                esData.isOneChoise = self.isOneChoise
                if self.isOneChoise:
                    bpy.ops.wm.call_menu_pie(name=EnumSelectorBox.bl_idname)
                else:
                    bpy.ops.node.voronoi_enum_selector_box('INVOKE_DEFAULT')
                return True #Для modal(), чтобы вернуть успех.
    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiEnumSelectorTool.NextAssessment(self, context)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if self.isToggleOptions:
                    if not self.vesIsToggleNodesOnDrag: #И снова, так же как и в VHT.
                        ToggleOptionsFromNode(self.foundGoalNd.tg, ToggleOptionsFromNode(self.foundGoalNd.tg, True), True)
                    return {'FINISHED'}
                else:
                    if VoronoiEnumSelectorTool.DoActivation(self):
                        return {'FINISHED'}
                return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        if (Prefs().vesIsInstantActivation)and(not self.isToggleOptions):
            #Изначально хотел оставить нарисованную к ноду линию до момента __del__'a OpEnumSelectorBox'a, но оказалось некоторая головная боль;
            # и коробка может полностью закрыть нод вместе с линией к нему. Так что пока пусть будет так.
            VoronoiEnumSelectorTool.NextAssessment(self, context)
            SolderingAllPrefsToSelf(self)
            VoronoiEnumSelectorTool.DoActivation(self)
            return {'FINISHED'}
        self.foundGoalNd = None
        self.firstResult = None
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiEnumSelector):
            VoronoiEnumSelectorTool.NextAssessment(self, context)
        return {'RUNNING_MODAL'}

list_classes += [VoronoiEnumSelectorTool]
AddToKmiDefs(VoronoiEnumSelectorTool, "F_scA", {'isToggleOptions': True})
#Изначально хотел 'V_Sca', но слишком далеко тянуться пальцем до 'V'. И вообще, учитывая этот инструмент, нужно минимизировать сложность вызова.
AddToKmiDefs(VoronoiEnumSelectorTool, "F_Sca", {'isToggleOptions': False, 'isOneChoise': False})
AddToKmiDefs(VoronoiEnumSelectorTool, "F_sca", {'isToggleOptions': False, 'isOneChoise': True})

def DrawEnumSelectorBox(where):
    colMaster = where.column()
    nd = esData.nd
    #Нод математики имеет высокоуровневое разбиение на категории для .prop(), но как показать их вручную простым перечислением я не знаю. И вообще, VQMT.
    #Игнорировать их не стал, пусть обрабатываются как есть. И с ними даже очень удобно выбирать операцию векторной математики (обычная не влезает).
    sco = 0
    for li in esData.list_enumProps:
        if sco:
            colProp.separator()
        colProp = colMaster.column(align=True)
        if esData.isDisplayLabels:
            rowLabel = colProp.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(text=li.name)
            #rowLabel.active = not esData.isOneChoise #Для пирога рамка прозрачная, от чего текст может сливаться. Так что выключено.
        elif sco:
            colProp.separator()
        colEnum = colProp.column(align=True)
        colEnum.scale_y = esData.boxScale
        if esData.isDarkStyle:
            colEnum.prop_tabs_enum(nd, li.identifier)
        else:
            colEnum.prop(nd, li.identifier, expand=True)
        sco += 1
    if not sco: #Для отладки.
        colMaster.label(text="`list_enums` is empty") #Во всю ширину не влезает.
    #В самой первой задумке я неправильно назвал этот инструмент -- "Prop Selector";
    # нужно придумать как отличить общие свойства нода от тех, которые рисуются у него в опциях. Повезло, что у каждого нода енумов нет разных...
    #for li in [li for li in nd.bl_rna.properties if not(li.is_readonly or li.is_registered)and(li.type!='ENUM')]: colMaster.prop(nd, li.identifier)
class OpEnumSelectorBox(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def execute(self, context): #Для draw() ниже, иначе не отобразится.
        pass
    def draw(self, context):
        DrawEnumSelectorBox(self.layout)
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=int(128*esData.boxScale))
class EnumSelectorBox(bpy.types.Menu):
    bl_idname = 'VL_MT_voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def draw(self, context):
        pie = self.layout.menu_pie()
        pie.column()
        col = pie.box().column()
        col.ui_units_x = 7*((esData.boxScale-1)/2+1)
        DrawEnumSelectorBox(col)

list_classes += [OpEnumSelectorBox, EnumSelectorBox]

def ToggleOptionsFromNode(nd, lastResult, isCanDo=False): #Копия логики с VHT HideFromNode'a().
    if lastResult:
        success = nd.show_options
        if isCanDo:
            nd.show_options = False
        return success
    elif isCanDo:
        success = not nd.show_options
        nd.show_options = True
        return success

#Шаблон для быстрого и удобного добавления нового инструмента:
def CallbackDrawVoronoiDummy(self, context):
    if StencilStartDrawCallback(self, context):
        return
    cusorPos = context.space_data.cursor_location
    if self.foundGoalSkIo:
        DrawToolOftenStencil( self, cusorPos, [self.foundGoalSkIo], isLineToCursor=True, textSideFlip=True )
    elif self.dsIsDrawPoint:
        DrawWidePoint(self, cusorPos)
class VoronoiDummyTool(bpy.types.Operator, VoronoiOpPoll):
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    bl_options = {'UNDO'}
    def NextAssessment(self, context):
        self.foundGoalSkIo = None
        callPos = context.space_data.cursor_location
        for li in GetNearestNodes(context.space_data.edit_tree.nodes, callPos):
            nd = li.tg
            if nd.type=='REROUTE':
                continue
            list_fgSksIn, list_fgSksOut = GetNearestSockets(nd, callPos)
            fgSkIn = list_fgSksIn[0] if list_fgSksIn else None
            fgSkOut = list_fgSksOut[0] if list_fgSksOut else None
            self.foundGoalSkIo = MinFromFgs(fgSkOut, fgSkIn)
            break
    def modal(self, context, event):
        context.area.tag_redraw()
        isCanNext = True
        if SetCanMoveOut(self, event):
            isCanNext = False
            self.foundGoalSkOut0 = None
            self.foundGoalSkOut1 = None
            VoronoiDummyTool.NextAssessment(self, context)
        match event.type:
            case 'MOUSEMOVE':
                if isCanNext:
                    VoronoiDummyTool.NextAssessment(self, context)
            case self.keyType|'ESC':
                if result:=StencilModalEsc(self, context, event):
                    return result
                if self.foundGoalSkIo:
                    self.foundGoalSkIo.tg.name = "hi. i am a vdt!"
                    self.foundGoalSkIo.tg.node.label = self.foundGoalSkIo.tg.name
                    return {'FINISHED'}
                return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self, context, event):
        self.foundGoalSkIo = None
        if StencilToolInvokePrepare(self, context, event, CallbackDrawVoronoiDummy):
            VoronoiDummyTool.NextAssessment(self, context)
        return {'RUNNING_MODAL'}

list_classes += []
#AddToRegAndAddToKmiDefs(VoronoiDummyTool, "D_sca", {})
#AddToKmiDefs(VoronoiDummyTool, "D_sca", {'': False })

def Prefs():
    return bpy.context.preferences.addons[voronoiAddonName].preferences

voronoiTextToolSettings = " Tool settings:"
txt_onlyFontFormat = "Only .ttf or .otf format"
txt_copySettAsPyScript = "Copy addon settings as .py script"

class VoronoiAddonTabs(bpy.types.Operator): #См. |11|
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "Addon Tabs"
    opt: bpy.props.StringProperty()
    def invoke(self, context, event):
        if self.opt=='GetPySett':
            txt = "import bpy\n\n"+f"prefs = bpy.context.preferences.addons['{voronoiAddonName}'].preferences"+"\n\n"
            prefs = Prefs()
            for li in prefs.rna_type.properties:
                if not li.is_readonly:
                    #'vaUiTabs' нужны для `event.shift`
                    #'_BoxDiscl'ы не стал игнорировать, пусть будут; для эстетики.
                    if li.identifier not in {'bl_idname', 'vaUiTabs', 'vaShowOtherOptions', 'vaShowRvEeOptions'}:
                        isArray = getattr(li,'is_array', False)
                        if isArray:
                            isDiff = not not [li for li in zip(li.default_array, getattr(prefs, li.identifier)) if li[0]!=li[1]]
                        else:
                            isDiff = li.default!=getattr(prefs, li.identifier)
                        if (isDiff)or(event.shift):
                            if isArray:
                                #txt += f"prefs.{li.identifier} = ({' '.join([str(li)+',' for li in arr])})\n"
                                list_vals = [str(li)+"," for li in getattr(prefs, li.identifier)]
                                list_vals[-1] = list_vals[-1][:-1]
                                txt += f"prefs.{li.identifier} = ("+" ".join(list_vals)+")\n"
                            else:
                                match li.type:
                                    case 'STRING': txt += f"prefs.{li.identifier} = \"{getattr(prefs, li.identifier)}\""+"\n"
                                    case 'ENUM':   txt += f"prefs.{li.identifier} = '{getattr(prefs, li.identifier)}'"+"\n"
                                    case _:        txt += f"prefs.{li.identifier} = {getattr(prefs, li.identifier)}"+"\n"
            context.window_manager.clipboard = txt
        else:
            Prefs().vaUiTabs = self.opt
        return {'FINISHED'}
class TogglerOfTool(bpy.types.PropertyGroup):
    tgl: bpy.props.BoolProperty(name="Tgl", default=False)
class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = voronoiAddonName if __name__=="__main__" else __name__
    #AddonPrefs
    vaUiTabs: bpy.props.EnumProperty(name="Addon Prefs Tabs", default='SETTINGS', items=( ('SETTINGS',"Settings",""),
                                                                                          ('DRAW',    "Draw",    ""),
                                                                                          ('KEYMAP',  "Keymap",  "") ))
    vaShowOtherOptions: bpy.props.BoolProperty(name="Other options:", default=False) #todo Добавить двоеточия к не-инструментным дисклосурам?
    vaShowRvEeOptions: bpy.props.BoolProperty(name="Visual assistance in reverse engineering", default=False)
    vaShowPassThroughtNodeSelectingMap: bpy.props.BoolProperty(name="Map of pass throught from node selecting",default=False)
    #Box disclosures:
    vlBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vpBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vmBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vqmBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vsBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vhBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    vesBoxDiscl: bpy.props.BoolProperty(name="", default=True)
    #Заметка: префиксы "ds" и инструментальные "v_" теперь имеют значение. См.`SolderingAllPrefsToSelf()`
    #Draw
    dsIsDrawSkText: bpy.props.BoolProperty(name="Text",        default=True) #Учитывая VHT и VEST, это уже больше просто для текста в рамке, чем для текста от сокетов. #todo: переименовать все.
    dsIsDrawMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsDrawPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsDrawLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsDrawSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    ##
    dsIsColoredSkText: bpy.props.BoolProperty(name="Text",        default=True)
    dsIsColoredMarker: bpy.props.BoolProperty(name="Markers",     default=True)
    dsIsColoredPoint:  bpy.props.BoolProperty(name="Points",      default=True)
    dsIsColoredLine:   bpy.props.BoolProperty(name="Line",        default=True)
    dsIsColoredSkArea: bpy.props.BoolProperty(name="Socket area", default=True)
    ##
    dsIsAlwaysLine: bpy.props.BoolProperty(name="Always draw line for VoronoiLinker Tool", default=False)
    dsSocketAreaAlpha: bpy.props.FloatProperty(name="Socket area alpha", default=0.075, min=0, max=1, subtype="FACTOR")
    dsUniformColor: bpy.props.FloatVectorProperty(name="Alternative uniform color", default=(0.632502, 0.408091, 0.174378, 0.9), min=0, max=1, size=4, subtype='COLOR') #(0.65, 0.65, 0.65, 1.0)
    dsNodeColor: bpy.props.FloatVectorProperty(name="To-Node draw color", default=(1.0, 1.0, 1.0, 0.9), min=0, max=1, size=4, subtype='COLOR')
    ##
    dsDisplayStyle: bpy.props.EnumProperty(name="Display frame style", default='CLASSIC', items=( ('CLASSIC',   "Classic",   "1"), #Если существует способ указать порядок
                                                                                                  ('SIMPLIFIED',"Simplified","2"), # и чтобы работало -- дайте знать.
                                                                                                  ('ONLYTEXT',  "Only text", "3") ))
    dsFontFile: bpy.props.StringProperty(name="Font file", default='C:\Windows\Fonts\consola.ttf', subtype='FILE_PATH')
    dsLineWidth:      bpy.props.IntProperty(  name="Line Width",                default=1,  min=1, max=16, subtype="FACTOR")
    dsPointRadius:    bpy.props.FloatProperty(name="Point size",                default=1,  min=0, max=3)
    dsFontSize:     bpy.props.IntProperty(name=  "Font size",           default=28, min=10,  max=48)
    ##
    dsPointOffsetX: bpy.props.FloatProperty(name="Point offset X axis", default=20, min=-50, max=50)
    dsFrameOffset:  bpy.props.IntProperty(name=  "Frame size",          default=0,  min=0,   max=24, subtype='FACTOR')
    dsDistFromCursor: bpy.props.FloatProperty(name="Text distance from cursor", default=25, min=5, max=50)
    ##
    dsIsAllowTextShadow: bpy.props.BoolProperty(       name="Enable text shadow", default=True)
    dsShadowCol:         bpy.props.FloatVectorProperty(name="Shadow color",       default=[0.0, 0.0, 0.0, 0.5], size=4, min=0,   max=1, subtype='COLOR')
    dsShadowOffset:      bpy.props.IntVectorProperty(  name="Shadow offset",      default=[2,-2],               size=2, min=-20, max=20)
    dsShadowBlur:        bpy.props.IntProperty(        name="Shadow blur",        default=2,                            min=0,   max=2)
    ##
    dsIsDrawDebug:  bpy.props.BoolProperty(name="Display debugging", default=False)
    # =====================================================================================================================================================
    #Pass through map:
    vlPassThrought: bpy.props.BoolProperty(name="", default=False)
    vpPassThrought: bpy.props.BoolProperty(name="", default=False)
    vmPassThrought: bpy.props.BoolProperty(name="", default=False)
    vqmPassThrought: bpy.props.BoolProperty(name="", default=False)
    vsPassThrought: bpy.props.BoolProperty(name="", default=False)
    vhPassThrought: bpy.props.BoolProperty(name="", default=False)
    vmlPassThrought: bpy.props.BoolProperty(name="", default=False)
    vesPassThrought: bpy.props.BoolProperty(name="", default=False)
    #Main:
    #Уж было я хотел добавить это, но потом мне стало таак лень. Это же нужно всё менять под "только сокеты", и критерии для нод неведомо как получать.
    #И выгода неизвестно какая, кроме эстетики. Так что ну его нахрен. Работает -- не трогай.
    #А ещё см. |16|, реализация "только сокеты" грозит потенциальной кроличьей норой.
    vtSearchMethod: bpy.props.EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET', "Nearest node > Nearest socket", ""), #Нигде не используется.
                                                                                           ('SOCKET',      "Only nearest socket",           "") )) #И кажется, никогда не будет.
    vtAlwaysUnhideCursorNode: bpy.props.BoolProperty(name="Always unhide node under cursor", default=False)
    #Linker:
    vlReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be connected to any type", default=True)
    vlDeselectAll: bpy.props.EnumProperty(name="Deselect all on activate", default='NEVER', items=( ('NEVER',  "Never",            ""),
                                                                                                    ('WHEN_PT',"When pass through",""),
                                                                                                    ('ALWAYS', "Always",           "") ))
    #Preview:
    vpAllowClassicCompositorViewer: bpy.props.BoolProperty(name="Allow classic Compositor Viewer", default=False)
    vpAllowClassicGeoViewer:        bpy.props.BoolProperty(name="Allow classic GeoNodes Viewer",   default=True)
    ##
    vpIsLivePreview:         bpy.props.BoolProperty(name="Live preview",                        default=True)
    vpIsSelectPreviewedNode: bpy.props.BoolProperty(name="Select previewed node",               default=True)
    vpIsAutoShader:          bpy.props.BoolProperty(name="Color Socket directly into a shader", default=True)
    ##
    vpRvEeTriggerOnlyOnLink:    bpy.props.BoolProperty(name="Trigger only on linked",          default=False)
    vpRvEeIsColorOnionNodes:    bpy.props.BoolProperty(name="Node onion colors",               default=False)
    vpRvEeSksHighlighting:      bpy.props.BoolProperty(name="Topology connected highlighting", default=False)
    vpRvEeIsSavePreviewResults: bpy.props.BoolProperty(name="Save preview results",            default=False)
    #Mixer:
    vmReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be mixed to any type", default=True)
    vmPieType: bpy.props.EnumProperty(name="Pie Type", default='CONTROL', items=( ('SPEED',  "Speed",  ""),
                                                                                  ('CONTROL',"Control","") ))
    vmPieScale: bpy.props.FloatProperty(name="Pie scale", default=1.5, min=1, max=2, subtype="FACTOR")
    vmPieSocketDisplayType: bpy.props.IntProperty(name="Display socket type info", default=1, min=-1, max=1)
    #Quick math:
    vqmDimensionConflictPriority: bpy.props.EnumProperty(name="Dimension conflict", default='FIRST', items=( ('FIRST', "Read from the first", ""),
                                                                                                             ('LAST',  "Read from the second",""),
                                                                                                             ('VECTOR',"Vector has priority", ""),
                                                                                                             ('FLOAT', "Float has priority",  "") ))
    vqmPieType: bpy.props.EnumProperty(name="Pie Type", default='CONTROL', items=( ('SPEED',  "Speed",  ""),
                                                                                   ('CONTROL',"Control","") ))
    vqmPieScale:             bpy.props.FloatProperty(name="Pie scale",              default=1.5, min=1, max=2, subtype="FACTOR")
    vqmPieSocketDisplayType: bpy.props.IntProperty(name="Display socket type info", default=1,   min=0, max=1) #См. |15|.
    #Swapper:
    vsCanTriggerToAnyType: bpy.props.BoolProperty(name="Can swap with any type", default=False)
    #Hider:
    vhHideBoolSocket: bpy.props.EnumProperty(name="Hide boolean sockets", default='IF_FALSE', items=( ('ALWAYS',  "Always",  ""),
                                                                                                      ('IF_FALSE',"If false",""),
                                                                                                      ('NEVER',   "Never",   ""),
                                                                                                      ('IF_TRUE', "If true", "") ))
    vhHideHiddenBoolSocket: bpy.props.EnumProperty(name="Hide hidden boolean sockets", default='ALWAYS', items=( ('ALWAYS',  "Always",  ""),
                                                                                                                 ('IF_FALSE',"If false",""),
                                                                                                                 ('NEVER',   "Never",   ""),
                                                                                                                 ('IF_TRUE', "If true", "") ))
    vhIsToggleNodesOnDrag:     bpy.props.BoolProperty(name="Toggle nodes on drag",       default=True)
    vhRedrawAfterChange:       bpy.props.BoolProperty(name="Redraw after change",        default=True)
    vhTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)
    vhDrawNodeNameLabel: bpy.props.EnumProperty(name="Display text for node", default='NONE', items=( ('NONE',     "None",          ""),
                                                                                                      ('NAME',     "Only name",     ""),
                                                                                                      ('LABEL',    "Only label",    ""),
                                                                                                      ('LABELNAME',"Name and label","") ))
    vhLabelDispalySide: bpy.props.IntProperty(name="Label Dispaly Side", default=3, min=1, max=4) #Настройка выше и так какая-то бесполезная, а эта прям ваще.
    #Enum selector:
    vesIsToggleNodesOnDrag: bpy.props.BoolProperty(name="Toggle nodes on drag", default=True)
    vesRedrawAfterChange:   bpy.props.BoolProperty(name="Redraw after change",  default=True)
    vesIsInstantActivation: bpy.props.BoolProperty(name="Instant activation",   default=True) #Эту, исключающую всё остальноё, опцию я добавил в самом конце. Накой черт я ниже всё это делал?.
    vesIsDrawEnumNames: bpy.props.BoolProperty(name="Draw enum names", default=False)
    vesDrawNodeNameLabel: bpy.props.EnumProperty(name="Display text for node", default='NONE', items=( ('NONE',     "None",          ""),
                                                                                                       ('NAME',     "Only name",     ""),
                                                                                                       ('LABEL',    "Only label",    ""),
                                                                                                       ('LABELNAME',"Name and label","") ))
    vesLabelDispalySide: bpy.props.IntProperty(name="Label Dispaly Side",  default=3,   min=1, max=4) #Так же, как и для VHT.
    vesBoxScale:         bpy.props.FloatProperty(name="Box scale",         default=1.5, min=1, max=2, subtype="FACTOR")
    vesDisplayLabels:    bpy.props.BoolProperty(name="Display enum names", default=True)
    vesDarkStyle:        bpy.props.BoolProperty(name="Dark style",         default=False)
    ##
    def AddHandSplitProp(self, where, txt_prop, tgl=True):
        spl = where.row().split(factor=0.38, align=True)
        spl.active = tgl
        row = spl.row(align=True)
        row.alignment = 'RIGHT'
        prop = self.bl_rna.properties[txt_prop]
        isNotBool = prop.type!='BOOLEAN'
        row.label(text=prop.name*isNotBool)
        if (not tgl)and(prop.type=='FLOAT')and(prop.subtype=='COLOR'):
            box = spl.box()
            box.label()
            box.scale_y = 0.5
            row.active = False
        else:
            spl.prop(self, txt_prop, text="" if isNotBool else None)
    def DrawTabSettings(self, context, where):
        AddHandSplitProp = self.AddHandSplitProp
        def FastBox(where):
            return where.box().column(align=True)
        def AddDisclosureProp(where, who, txt_prop, txt=None, isActive=False): #Не может на всю ширину, если where -- row().
            tgl = getattr(who, txt_prop)
            row = where.row(align=True)
            row.alignment = 'LEFT'
            row.prop(who, txt_prop, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=False)
            row.active = isActive
            return tgl
        def AddSelfBoxDiscl(where, txt_prop, cls=None):
            colBox = FastBox(where)
            if AddDisclosureProp(colBox, self, txt_prop, txt=(cls.bl_label+voronoiTextToolSettings) if cls else None):
                rowTool = colBox.row()
                rowTool.separator()
                colTool = rowTool.column(align=True)
                return colTool
            else:
                return None
        colMaster = where.column()
        try:
            if colTool:=AddSelfBoxDiscl(colMaster,'vlBoxDiscl', VoronoiLinkerTool):
                colTool.prop(self,'vlReroutesCanInAnyType')
                colTool.separator()
                AddHandSplitProp(colTool,'vlDeselectAll')
            if colTool:=AddSelfBoxDiscl(colMaster,'vpBoxDiscl', VoronoiPreviewTool):
                colProps = FastBox(colTool)
                colProps.prop(self,'vpAllowClassicCompositorViewer')
                colProps.prop(self,'vpAllowClassicGeoViewer')
                colProps = FastBox(colTool.row())
                colProps.prop(self,'vpIsLivePreview')
                colProps.prop(self,'vpIsSelectPreviewedNode')
                colProps.prop(self,'vpIsAutoShader')
                colProps = FastBox(colTool)
                tgl = self.vpRvEeIsColorOnionNodes or self.vpRvEeTriggerOnlyOnLink or self.vpRvEeSksHighlighting or self.vpRvEeIsSavePreviewResults
                if AddDisclosureProp(colProps, self,'vaShowRvEeOptions', isActive=tgl):
                    colProps.prop(self,'vpRvEeTriggerOnlyOnLink')
                    colProps.prop(self,'vpRvEeIsColorOnionNodes')
                    colProps.prop(self,'vpRvEeSksHighlighting')
                    colProps.prop(self,'vpRvEeIsSavePreviewResults')
            if colTool:=AddSelfBoxDiscl(colMaster,'vmBoxDiscl', VoronoiMixerTool):
                colTool.prop(self,'vmReroutesCanInAnyType') #AddHandSplitProp(colTool,'vmReroutesCanInAnyType')
                colTool.separator()
                AddHandSplitProp(colTool,'vmPieType')
                colProp = colTool.column(align=True)
                AddHandSplitProp(colProp,'vmPieScale')
                AddHandSplitProp(colProp,'vmPieSocketDisplayType')
                colProp.active = self.vmPieType=='CONTROL'
            if colTool:=AddSelfBoxDiscl(colMaster,'vqmBoxDiscl', VoronoiQuickMathTool):
                #Джинсы-для-собаки конфликт: может быть слева, как все булевы, ибо не-настройки-пирога, +одинаково с Mixer
                # либо может быть справа, как енумы и удобная установка проперти посередине.
                #colTool.prop(self,'vqmDimensionConflictPriority') #Но для первого варианта текст весь не влезает.
                AddHandSplitProp(colTool,'vqmDimensionConflictPriority')
                colTool.separator()
                AddHandSplitProp(colTool,'vqmPieType')
                colProp = colTool.column(align=True)
                AddHandSplitProp(colProp,'vqmPieScale')
                AddHandSplitProp(colProp,'vqmPieSocketDisplayType')
                colProp.active = self.vqmPieType=='CONTROL'
            if colTool:=AddSelfBoxDiscl(colMaster,'vsBoxDiscl', VoronoiSwapperTool):
                colTool.prop(self,'vsCanTriggerToAnyType')
            if colTool:=AddSelfBoxDiscl(colMaster,'vhBoxDiscl', VoronoiHiderTool):
                AddHandSplitProp(colTool,'vhHideBoolSocket')
                AddHandSplitProp(colTool,'vhHideHiddenBoolSocket')
                colTool.prop(self,'vhIsToggleNodesOnDrag')
                colProp = colTool.column(align=True)
                colProp.prop(self,'vhRedrawAfterChange')
                colProp.active = self.vhIsToggleNodesOnDrag
                colTool.prop(self,'vhTriggerOnCollapsedNodes')
                colTool.separator()
                AddHandSplitProp(colTool,'vhDrawNodeNameLabel')
                colProp = colTool.column(align=True)
                AddHandSplitProp(colProp,'vhLabelDispalySide')
                colProp.active = self.vhDrawNodeNameLabel=='LABELNAME'
            if colTool:=AddSelfBoxDiscl(colMaster,'vesBoxDiscl', VoronoiEnumSelectorTool):
                colTool.prop(self,'vesIsToggleNodesOnDrag')
                colProp = colTool.column(align=True)
                colProp.prop(self,'vesRedrawAfterChange')
                colProp.active = self.vesIsToggleNodesOnDrag
                AddHandSplitProp(colTool,'vesBoxScale')
                AddHandSplitProp(colTool,'vesDisplayLabels')
                AddHandSplitProp(colTool,'vesDarkStyle')
                colTool.prop(self,'vesIsInstantActivation')
                colBox = colTool.column(align=True)
                colBox.active = not self.vesIsInstantActivation #todo: придумать как помечать выбранный нод при моментальной активации.
                AddHandSplitProp(colBox,'vesIsDrawEnumNames')
                colProp = colBox.column(align=True)
                colProp.active = not self.vesIsDrawEnumNames
                AddHandSplitProp(colProp,'vesDrawNodeNameLabel')
                colProp = colProp.column(align=True)
                AddHandSplitProp(colProp,'vesLabelDispalySide')
                colProp.active = self.vesDrawNodeNameLabel=='LABELNAME'
            if colTool:=AddSelfBoxDiscl(colMaster,'vaShowOtherOptions'):
                #colTool.prop(self,'vtSearchMethod')
                colTool.prop(self,'vtAlwaysUnhideCursorNode')
                colTool.separator()
                if colMap:=AddSelfBoxDiscl(colTool,'vaShowPassThroughtNodeSelectingMap'):
                    #todo: забагрепортить дублирование выше и раскрытие второго. `colMap.prop(self,'vaShowPassThroughtNodeSelectingMap')`
                    colMap.prop(self,'vlPassThrought',  text=VoronoiLinkerTool.bl_label)
                    colMap.prop(self,'vpPassThrought',  text=VoronoiPreviewTool.bl_label)
                    colMap.prop(self,'vmPassThrought',  text=VoronoiMixerTool.bl_label)
                    colMap.prop(self,'vqmPassThrought', text=VoronoiQuickMathTool.bl_label)
                    colMap.prop(self,'vsPassThrought',  text=VoronoiSwapperTool.bl_label)
                    colMap.prop(self,'vhPassThrought',  text=VoronoiHiderTool.bl_label)
                    colMap.prop(self,'vmlPassThrought', text=VoronoiMassLinkerTool.bl_label)
                    colMap.prop(self,'vesPassThrought', text=VoronoiEnumSelectorTool.bl_label)
                colTool.separator()
                colTool.operator(VoronoiAddonTabs.bl_idname, text=txt_copySettAsPyScript).opt = 'GetPySett'
        except Exception as ex:
            colMaster.label(text=str(ex), icon='ERROR')
    def DrawTabDraw(self, context, where):
        AddHandSplitProp = self.AddHandSplitProp
        colMaster = where.column()
        try:
            rowDrawColor = colMaster.row(align=True)
            rowDrawColor.use_property_split = True
            colDraw = rowDrawColor.column(align=True, heading='Draw')
            colDraw.prop(self,'dsIsDrawSkText')
            colDraw.prop(self,'dsIsDrawMarker')
            colDraw.prop(self,'dsIsDrawPoint')
            colDraw.prop(self,'dsIsDrawLine')
            colDraw.prop(self,'dsIsDrawSkArea')
            colCol = rowDrawColor.column(align=True, heading='Colored')
            def AddColoredProp(where, txt):
                row = where.row(align=True)
                row.prop(self, txt)
                row.active = getattr(self, txt.replace("Colored","Draw"))
            AddColoredProp(colCol,'dsIsColoredSkText')
            AddColoredProp(colCol,'dsIsColoredMarker')
            AddColoredProp(colCol,'dsIsColoredPoint')
            AddColoredProp(colCol,'dsIsColoredLine')
            AddColoredProp(colCol,'dsIsColoredSkArea')
            colProps = colMaster.column()
            AddHandSplitProp(colProps, 'dsIsAlwaysLine')
            AddHandSplitProp(colProps, 'dsSocketAreaAlpha')
            tgl = ( (self.dsIsDrawSkText and not self.dsIsColoredSkText)or
                    (self.dsIsDrawMarker and not self.dsIsColoredMarker)or
                    (self.dsIsDrawPoint  and not self.dsIsColoredPoint )or
                    (self.dsIsDrawLine   and not self.dsIsColoredLine  )or
                    (self.dsIsDrawSkArea and not self.dsIsColoredSkArea) )
            AddHandSplitProp(colProps, 'dsUniformColor', tgl)
            tgl = ( (self.dsIsDrawSkText and self.dsIsColoredSkText)or
                    (self.dsIsDrawPoint  and self.dsIsColoredPoint )or
                    (self.dsIsDrawLine   and self.dsIsColoredLine  ) )
            AddHandSplitProp(colProps, 'dsNodeColor', tgl)
            AddHandSplitProp(colProps, 'dsDisplayStyle')
            AddHandSplitProp(colProps, 'dsFontFile')
            import os
            if not os.path.splitext(self.dsFontFile)[1] in (".ttf",".otf"):
                spl = colProps.split(factor=0.4, align=True)
                spl.label(text="")
                spl.label(text=txt_onlyFontFormat, icon='ERROR')
            colGroup = colProps.column(align=True)
            AddHandSplitProp(colGroup, 'dsLineWidth')
            AddHandSplitProp(colGroup.row(), 'dsPointRadius')
            AddHandSplitProp(colGroup, 'dsFontSize')
            row = colProps.row(align=True)
            row.separator()
            row.scale_x = .333
            colGroup = colProps.column(align=True)
            AddHandSplitProp(colGroup, 'dsPointOffsetX')
            AddHandSplitProp(colGroup.row(), 'dsFrameOffset')
            AddHandSplitProp(colGroup, 'dsDistFromCursor')
            AddHandSplitProp(colProps, 'dsIsAllowTextShadow')
            colShadow = colProps.column(align=True)
            AddHandSplitProp(colShadow, 'dsShadowCol', self.dsIsAllowTextShadow)
            AddHandSplitProp(colShadow.row(), 'dsShadowOffset')
            AddHandSplitProp(colShadow, 'dsShadowBlur')
            colShadow.active = self.dsIsAllowTextShadow
            AddHandSplitProp(colProps, 'dsIsDrawDebug')
        except Exception as ex:
            colMaster.label(text=str(ex), icon='ERROR')
    def DrawTabKeymaps(self, context, where):
        colMaster = where.column()
        try:
            colMaster.separator()
            rowLabel = colMaster.row(align=True)
            rowLabel.label(text=TranslateIface("Node Editor"), icon='DOT')
            colList = colMaster.column(align=True)
            kmNe = bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']
            list_getKmi = []
            for li in list_addonKeymaps:
                for kmiCon in kmNe.keymap_items:
                    if (li.idname==kmiCon.idname)and(li.name==kmiCon.name):
                        list_getKmi.append(kmiCon)
            if kmNe.is_user_modified:
                rowLabel.label()
                rowLabel.context_pointer_set('keymap', kmNe)
                rowLabel.operator('preferences.keymap_restore', text=TranslateIface("Restore"))
            import rna_keymap_ui
            for li in sorted(set(list_getKmi), key=list_getKmi.index):
                colList.context_pointer_set('keymap', kmNe)
                rna_keymap_ui.draw_kmi([], context.window_manager.keyconfigs.user, kmNe, li, colList, 0)
        except Exception as ex:
            colMaster.label(text=str(ex), icon='ERROR')
    #Спасибо пользователю с ником "atticus-lv" за потрясную идею по компактной упаковке настроек. Сам-то я до вкладок ещё не скоро бы допёр.
    def draw(self, context):
        colMaster = self.layout.column()
        colMain = colMaster.column(align=True)
        rowTabs = colMain.row(align=True)
        #|11| Переключение вкладок через оператор создано, чтобы случайно не сменить вкладку при ведении зажатой мышки, кой есть особый соблазн с таким большим количеством "isColored".
        if True:
            for li in [e for e in self.bl_rna.properties['vaUiTabs'].enum_items]:
                rowTabs.operator(VoronoiAddonTabs.bl_idname, text=TranslateIface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
        else:
            rowTabs.prop(self,'vaUiTabs', expand=True)
        match self.vaUiTabs:
            case 'SETTINGS': self.DrawTabSettings(context, colMaster)
            case 'DRAW':     self.DrawTabDraw    (context, colMaster)
            case 'KEYMAP':   self.DrawTabKeymaps (context, colMaster)

list_classes += [VoronoiAddonTabs, TogglerOfTool, VoronoiAddonPrefs]

#todo теперь есть пара пар инструментов с одинаковыми по смыслу опциями. Нужно бы это как-то вылизать и/или зашаблонить.

list_helpClasses = []

class TranslationHelper():
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


def GetAddonPropName(txt, inx=-1):
    tar = VoronoiAddonPrefs.bl_rna.properties[txt]
    if inx>-1:
        tar = getattr(tar,'enum_items')[inx]
    return tar.name
def GclToolSet(cls):
    return cls.bl_label+voronoiTextToolSettings

dict_translations = {}

Gapn = GetAddonPropName
def CollectTranslationDict(): #Превращено в функцию ради `Gapn()`, который требует регистрации 'VoronoiAddonPrefs'.
    dict_translations['ru_RU'] = {
            bl_info['description']:                     "Разнообразные помогалочки для соединения нод, основанные на поле расстояний",
            "Virtual":                                  "Виртуальный",
            "Restore":                                  "Восстановить",
            txt_noMixingOptions:                        "Варианты смешивания отсутствуют",
            txt_copySettAsPyScript:                     "Скопировать настройки аддона как '.py' скрипт",
            #Tools:
            GclToolSet(VoronoiLinkerTool):              f"Настройки инструмента {VoronoiLinkerTool.bl_label}:",
            GclToolSet(VoronoiPreviewTool):             f"Настройки инструмента {VoronoiPreviewTool.bl_label}:",
            GclToolSet(VoronoiMixerTool):               f"Настройки инструмента {VoronoiMixerTool.bl_label}:",
            GclToolSet(VoronoiQuickMathTool):           f"Настройки инструмента {VoronoiQuickMathTool.bl_label}:",
            GclToolSet(VoronoiSwapperTool):             f"Настройки инструмента {VoronoiSwapperTool.bl_label}:",
            GclToolSet(VoronoiHiderTool):               f"Настройки инструмента {VoronoiHiderTool.bl_label}:",
            GclToolSet(VoronoiEnumSelectorTool):        f"Настройки инструмента {VoronoiEnumSelectorTool.bl_label}:",
            Gapn('vaShowOtherOptions'):                 "Другие настройки:",
            Gapn('vaShowPassThroughtNodeSelectingMap'): "Карта пропусков выделения нода",
            #Draw:
            "Colored":                                  "Цветной",
            Gapn('dsUniformColor'):                     "Альтернативный постоянный цвет",
            Gapn('dsNodeColor'):                        "Цвет рисования к ноду",
            Gapn('dsSocketAreaAlpha'):                  "Прозрачность области сокета",
            Gapn('dsFontFile'):                         "Файл шрифта",
            txt_onlyFontFormat:                         "Только .ttf или .otf формат",
            Gapn('dsPointOffsetX'):                     "Смещение точки по оси X",
            Gapn('dsFrameOffset'):                      "Размер рамки",
            Gapn('dsFontSize'):                         "Размер шрифта",
            Gapn('dsIsDrawSkArea'):                     "Область сокета",
            Gapn('dsDisplayStyle'):                     "Стиль отображения рамки",
                Gapn('dsDisplayStyle',0):                   "Классический",
                Gapn('dsDisplayStyle',1):                   "Упрощённый",
                Gapn('dsDisplayStyle',2):                   "Только текст",
            Gapn('dsPointRadius'):                      "Размер точки",
            Gapn('dsDistFromCursor'):                   "Расстояние до текста от курсора",
            Gapn('dsIsAllowTextShadow'):                "Включить тень текста",
            Gapn('dsShadowCol'):                        "Цвет тени",
            Gapn('dsShadowOffset'):                     "Смещение тени",
            Gapn('dsShadowBlur'):                       "Размытие тени",
            Gapn('dsIsAlwaysLine'):                     "Всегда рисовать линию для Voronoi Linker Tool",
            Gapn('dsIsDrawDebug'):                      "Отображать отладку",
            #Settings:
            Gapn('vlReroutesCanInAnyType'):             "Рероуты могут подключаться в любой тип",
            Gapn('vlDeselectAll'):                      "Снимать выделение со всех при активации",
                Gapn('vlDeselectAll',1):                    "Когда пропущен через выделение нода",
            Gapn('vpAllowClassicCompositorViewer'):     "Разрешить классический Viewer Композитора",
            Gapn('vpAllowClassicGeoViewer'):            "Разрешить классический Viewer Геометрических нодов",
            Gapn('vpIsLivePreview'):                    "Предпросмотр в реальном времени",
            Gapn('vpIsSelectPreviewedNode'):            "Выделять предпросматриваемый нод",
            Gapn('vpIsAutoShader'):                     "Сокет цвета сразу в шейдер",
            Gapn('vaShowRvEeOptions'):                  "Визуальный помощник при реверс-инженеринге",
            Gapn('vpRvEeTriggerOnlyOnLink'):            "Триггериться только на связанные",
            Gapn('vpRvEeIsColorOnionNodes'):            "Луковичные цвета нод",
            Gapn('vpRvEeSksHighlighting'):              "Подсветка топологических соединений",
            Gapn('vpRvEeIsSavePreviewResults'):         "Сохранять результаты предпросмотра",
            Gapn('vmReroutesCanInAnyType'):             "Рероуты могут смешиваться с любым типом",
            Gapn('vmPieType'):                          "Тип пирога",
                Gapn('vmPieType',0):                        "Скорость",
                Gapn('vmPieType',1):                        "Контроль",
            Gapn('vmPieScale'):                         "Размер пирога",
            Gapn('vmPieSocketDisplayType'):             "Отображение типа сокета",
            Gapn('vqmDimensionConflictPriority'):       "Конфликт размерностей",
                Gapn('vqmDimensionConflictPriority',0):     "Читать из первого",
                Gapn('vqmDimensionConflictPriority',1):     "Читать из второго",
                Gapn('vqmDimensionConflictPriority',2):     "Вектор приоритетнее",
                Gapn('vqmDimensionConflictPriority',3):     "Скаляр приоритетнее",
            Gapn('vsCanTriggerToAnyType'):              "Может меняться с любым типом",
            Gapn('vhHideBoolSocket'):                   "Скрывать Boolean сокеты",
            Gapn('vhHideHiddenBoolSocket'):             "Скрывать скрытые Boolean сокеты",
                Gapn('vhHideBoolSocket',1):                 "Если True",
                Gapn('vhHideBoolSocket',3):                 "Если False",
            Gapn('vhIsToggleNodesOnDrag'):              "Переключать ноды при ведении курсора",
            Gapn('vhRedrawAfterChange'):                "Перерисовывать после изменения",
            Gapn('vhTriggerOnCollapsedNodes'):          "Триггериться на свёрнутые ноды",
            Gapn('vhDrawNodeNameLabel'):                "Показывать текст для нода",
                Gapn('vhDrawNodeNameLabel',1):              "Только имя",
                Gapn('vhDrawNodeNameLabel',2):              "Только заголовок",
                Gapn('vhDrawNodeNameLabel',3):              "Имя и заголовок",
            Gapn('vhLabelDispalySide'):                 "Сторона отображения заголовка",
            Gapn('vesIsInstantActivation'):             "Моментальная активация",
            Gapn('vesIsDrawEnumNames'):                 "Рисовать имена свойств перечисления",
            Gapn('vesBoxScale'):                        "Масштаб панели",
            Gapn('vesDisplayLabels'):                   "Отображать имена свойств перечислений",
            Gapn('vesDarkStyle'):                       "Тёмный стиль",
            Gapn('vtAlwaysUnhideCursorNode'):           "Всегда раскрывать узел под курсором"}
    return
    dict_translations['aa_AA'] = {
            bl_info['description']:                     "",
            "Virtual":                                  "",
            "Restore":                                  "",
            #...
            #Ждёт своего часа.
            }

list_addonKeymaps = []

newKeyMapNodeEditor = None

def register():
    for li in list_classes:
        bpy.utils.register_class(li)
    ##
    global newKeyMapNodeEditor
    newKeyMapNodeEditor = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for blId, key, shift, ctrl, alt, dict_props in list_kmiDefs:
        kmi = newKeyMapNodeEditor.keymap_items.new(idname=blId, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt)
        list_addonKeymaps.append(kmi)
        if dict_props:
            for di in dict_props:
                setattr(kmi.properties, di, dict_props[di])
    ##
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
    UnregisterTranslations()


def DisableKmis(): #Для повторных запусков скрипта. Работает до первого "Restore".
    kmNe = bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']
    for ti, *ot in list_kmiDefs:
        for kmiCon in kmNe.keymap_items:
            if ti==kmiCon.idname:
                kmiCon.active = False #Это удаляет дубликаты. Хак?
                kmiCon.active = True #Вернуть обратно, если оригинал.
if __name__=="__main__":
    DisableKmis() #Кажется не важно в какой очерёдности вызывать, перед или после добавления хоткеев.
    register()
