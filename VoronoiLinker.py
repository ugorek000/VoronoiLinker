# !!! Disclaimer: Use the contents of this file at your own risk !!!
# 100% of the content of this file contains malicious code!!1

# !!! Отказ от ответственности: Содержимое этого файла является полностью случайно сгенерированными битами, включая этот дисклеймер тоже.
# Используйте этот файл на свой страх и риск.
#P.s. Использование этого файла полностью безопасно, оно продлевает жизнь вашего компьютера, и вообще избавляет от вирусов (но это не точно).

#Этот аддон создавался мной как самопис лично для меня и под меня; который я по доброте душевной, сделал публичным для всех желающих. Ибо результат получился потрясающий. Наслаждайтесь.
#P.s. Меня напрягают шатанины с лицензиями, так что лучше полюбуйтесь на предупреждения о вредоносном коде (о да он тут есть, иначе накой смысол?).

bl_info = {'name':"Voronoi Linker", 'author':"ugorek", #Так же спасибо "Oxicid" за важную для VL'а помощь.
           'version':(5,0,0), 'blender':(4,0,2), 'created':"2024.02.26", #Ключ 'created' для внутренних нужд.
           'info_supported_blvers': "b4.0.2 – b4.0.2", #Тоже внутреннее.
           'description':"Various utilities for nodes connecting, based on distance field.", 'location':"Node Editor", #Раньше была надпись 'Node Editor > Alt + RMB' в честь того, ради чего всё; но теперь VL "повсюду"!
           'warning':"", #Надеюсь не настанет тот момент, когда у VL будет предупреждение. Неработоспособность в Linux'е была очень близко к этому.
           'category':"Node",
           'wiki_url':"https://github.com/ugorek000/VoronoiLinker/wiki", 'tracker_url':"https://github.com/ugorek000/VoronoiLinker/issues"}

from builtins import len as length #Я обожаю трёхбуквенные имена переменных. А без такого имени, как "len" -- мне очень грустно и одиноко... А ещё 'Vector.length'.
import bpy, ctypes, rna_keymap_ui, bl_keymap_utils
import blf, gpu, gpu_extras.batch

from math import pi, cos, sin
from mathutils import Vector as Vec
import random

import platform
from time import perf_counter
import copy #VLNST

Vec2 = Col4 = Vec

list_classes = []
list_toolClasses = []

voronoiAddonName = bl_info['name'].replace(" ","") #todo0 узнать разницу между названием аддона, именем аддона, именем файла, именем модуля, (мб ещё пакета); и ещё в установленных посмотреть.
class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = voronoiAddonName if __name__=="__main__" else __name__

list_kmiDefs = []
dict_setKmiCats = {'grt':set(), 'oth':set(), 'spc':set(), 'qqm':set(), 'cus':set()}

def SmartAddToRegAndAddToKmiDefs(cls, txt, dict_props={}):
    dict_numToKey = {"1":'ONE', "2":'TWO', "3":'THREE', "4":'FOUR', "5":'FIVE', "6":'SIX', "7":'SEVEN', "8":'EIGHT', "9":'NINE', "0":'ZERO'}
    if cls not in list_classes: #Благодаря этому назван как "Smart", и регистрация инструментов стала чуть проще.
        list_classes.append(cls)
        list_toolClasses.append(cls)
    list_kmiDefs.append( (cls.bl_idname, dict_numToKey.get(txt[4:], txt[4:]), txt[0]=="S", txt[1]=="C", txt[2]=="A", txt[3]=="+", dict_props) ) #Тоже Smart.

isWin = platform.system()=='Windows'
#isLinux = platform.system()=='Linux'

viaverIsBlender4 = bpy.app.version[0]==4 #Для поддержки работы в предыдущих версиях. Нужно для комфортного осознания отсутствия напрягов при вынужденных переходах на старые версии,
# и получения дополнительной порции эндорфинов от возможности работы в разных версиях с разными api.
#Todo0VV опуститься с поддержкой как можно ниже по версиям. Сейчас с гарантией: b4.0 и b4.1?

voronoiAnchorCnName = "Voronoi_Anchor" #Перевод не поддерживается, за компанию.
voronoiAnchorDtName = "Voronoi_Anchor_Dist" #Перевод не поддерживается! См. связанную топологию.
voronoiSkPreviewName = "voronoi_preview" #Перевод не поддерживается, нет желания каждое чтение обрамлять TranslateIface().
voronoiPreviewResultNdName = "SavePreviewResult" #Перевод не поддерживается за компанию.

def GetUserKmNe():
    return bpy.context.window_manager.keyconfigs.user.keymaps['Node Editor']

#Может быть стоит когда-нибудь добавить в свойства инструмента клавишу для модифицирования в процессе самого инструмента, например вариант Alt при Alt D для VQDT. Теперь ещё больше актуально для VWT.

#Где-то в комментариях могут использоваться словосочетание "тип редактора" -- то же самое что и "тип дерева"; имеются в виду 4 классических встроенных редактора, и они же, типы деревьев.

#Для некоторых инструментов есть одинаковые между собой константы, но со своими префиксами; разнесено для удобства, чтобы не "арендовать" у других инструментов.

#Актуальные нужды для VL, доступные на данный момент только(?) через ОПА:
# 1. Является ли GeoViewer активным (по заголовку) и/или активно-просматривающим прямо сейчас? (На низком уровне, а не чтение из spreadsheet)
# 2. Однозначное определение для контекста редактора, через какой именно нод на уровень выше, пользователь зашёл в текущую группу.
# 3. Как отличить общие классовые enum'ы от уникальных enum для данного нода?
# 4. Сменить для гео-Viewer'а тип поля, который он предпросматривает.
# 5. Высота макета сокета.
# 6. Новосозданному интерфейсу через api теперь приходиться проходить по всем существующим деревьям, и искать его "экземпляры", чтобы установить ему `default_value`; имитируя классический не-api-шный способ.
# 7. Фулл-доступ на интерфейсные панели со всеми плюшками. См. |4|.

#Таблица (теоретической) полезности инструментов в аддонских деревьях (по умолчанию -- полезно):
# VLT
# VPT    Частично
# VPAT   ??
# VMT    Нет?
# VQMT   Нет
# VRT
# VST
# VHT
# VMLT
# VEST
# VLRT
# VQDT   Нет
# VICT   Нет!
# VLTT
# VWT
# VLNST  Нет?
# VRNT

#Todo0VV обработать все комбинации в n^3: space_data.tree_type и space_data.edit_tree.bl_idname; классическое, потерянное, и аддонское; привязанное и не привязанное к редактору.
# ^ и потом работоспособность всех инструментов в них. А потом проверить в существующем дереве взаимодействие потерянного сокета у потерянного нода для всех инструментов.

class TryAndPass():
    def __enter__(self):
        pass
    def __exit__(self, *_):
        return True

#Именования в рамках кода этого аддона:
#sk -- сокет
#skf -- сокет-интерфейс
#skin -- входной сокет (ski)
#skout -- выходной сокет (sko)
#skfin -- входной сокет-интерфейс
#skfout -- выходной сокет-интерфейс
#skfa -- коллекция интерфейсов дерева (tree.interface.items_tree), включая simrep'ы
#skft -- основа интерфейсов дерева (tree.interface)
#nd -- нод
#rr -- рероут
##
#blid -- bl_idname
#blab -- bl_label
#dnf -- identifier
##
#Неиспользуемые переменные названы с "_подчёркиванием".

dict_timeAvg = {}
dict_timeOutside = {}
#    with ToTimeNs("aaa"):
class ToTimeNs(): #Сдаюсь. Я не знаю, почему так лагает на больших деревьях. Но судя по замерам, это где-то за пределами VL.
    def __init__(self, name):
        from time import perf_counter_ns
        self.name = name
        tpcn = perf_counter_ns()
        dict_timeOutside[name] = tpcn-dict_timeOutside.setdefault(name, 0)
        dict_timeAvg.setdefault(name, [0, 0])
        self.tmn = tpcn
    def __enter__(self):
        pass
    def __exit__(self, *_):
        from time import perf_counter_ns
        tpcn = perf_counter_ns()
        nsExec = tpcn-self.tmn
        list_avg = dict_timeAvg[self.name]
        list_avg[0] += 1
        list_avg[1] += nsExec
        txt1 = "{:,}".format(nsExec).rjust(13)
        txt2 = "{:,}".format(dict_timeOutside[self.name]).rjust(13)
        txt3 = "{:,}".format(int(list_avg[1]/list_avg[0]))
        txt = " ".join(("", self.name, txt1, "~~~", txt2, "===", txt3))
        dict_timeOutside[self.name] = tpcn

#todo1v6 при активном инструменте нажатие PrtScr спамит в консоли `WARN ... pyrna_enum_to_py: ... '171' matches no enum in 'Event'`.

from bpy.app.translations import pgettext_iface as TranslateIface

dict_vlHhTranslations = {}

dict_vlHhTranslations['ru_RU'] = {'author':"ugorek",    'vl':(5,0,0), 'created':"2024.02.25", 'trans':{'a':{}, 'Op':{}}} #self
dict_vlHhTranslations['zh_CN'] = {'author':"chenpaner", 'vl':(4,0,0), 'created':"2023.12.15", 'trans':{'a':{}, 'Op':{}}} #https://github.com/ugorek000/VoronoiLinker/issues/21
#dict_vlHhTranslations['aa_AA'] = #Кто же будет вторым?. И как скоро?

for dk in dict_vlHhTranslations:
    exec(dk+f" = '{dk}'") #Когда будут языки с @variantcode (наверное никогда), тогда и можно будет париться.

class VlTrMapForKey():
    def __init__(self, key, *, tc='a'):
        self.key = key
        self.data = {}
        self.tc = tc
    def __enter__(self):
        return self.data
    def __exit__(self, *_):
        for dk, dv in self.data.items():
            dict_vlHhTranslations[dk]['trans'][self.tc][self.key] = dv

def TxtClsBlabToolSett(cls):
    return cls.bl_label+" tool settings"

class TranslationHelper():
    def __init__(self, dict_trans={}, lang=''):
        self.name = voronoiAddonName+"-"+lang
        self.dict_translations = dict()
        for cyc, dict_data in enumerate(dict_trans.values()):
            for dk, dv in dict_data.items():
                if cyc:
                    self.dict_translations.setdefault(lang, {})[ ('Operator', dk) ] = dv
                self.dict_translations.setdefault(lang, {})[ ('*', dk) ] = dv
    def register(self):
        if self.dict_translations:
            try:
                bpy.app.translations.register(self.name, self.dict_translations)
            except:
                with TryAndPass():
                    bpy.app.translations.unregister(self.name)
                    bpy.app.translations.register(self.name, self.dict_translations)
    def unregister(self):
        bpy.app.translations.unregister(self.name)

list_translationClasses = []

def RegisterTranslations():
    CollectTranslationDict()
    for dk in dict_vlHhTranslations:
        list_translationClasses.append(TranslationHelper(dict_vlHhTranslations[dk]['trans'], dk))
    for li in list_translationClasses:
        li.register()
def UnregisterTranslations():
    for li in list_translationClasses:
        li.unregister()


with VlTrMapForKey(bl_info['description']) as dm:
    dm[ru_RU] = "Разнообразные помогалочки для соединения нодов, основанные на поле расстояний."
    dm[zh_CN] = "基于距离场的多种节点连接辅助工具。"

txtAddonVer = ".".join([str(v) for v in bl_info['version']])
txt_addonVerDateCreated = f"Version {txtAddonVer} created {bl_info['created']}"
with VlTrMapForKey(txt_addonVerDateCreated) as dm:
    dm[ru_RU] = f"Версия {txtAddonVer} создана {bl_info['created']}"
#    dm[zh_CN] = f" {txtAddonVer}  {bl_info['created']}"
txt_addonBlVerSupporting = f"For Blender versions: {bl_info['info_supported_blvers']}"
with VlTrMapForKey(txt_addonBlVerSupporting) as dm:
    dm[ru_RU] = f"Для версий Блендера: {bl_info['info_supported_blvers']}"
#    dm[zh_CN] = f" {bl_info['info_supported_blvers']}"

txt_onlyFontFormat = "Only .ttf or .otf format"
with VlTrMapForKey(txt_onlyFontFormat) as dm:
    dm[ru_RU] = "Только .ttf или .otf формат"
    dm[zh_CN] = "只支持.ttf或.otf格式"

txt_copySettAsPyScript = "Copy addon settings as .py script"
with VlTrMapForKey(txt_copySettAsPyScript, tc='Op') as dm:
    dm[ru_RU] = "Скопировать настройки аддона как '.py' скрипт"
    dm[zh_CN] = "将插件设置复制为'.py'脚本,复制到粘贴板里"

txt_сheckForUpdatesYourself = "Check for updates yourself"
with VlTrMapForKey(txt_сheckForUpdatesYourself, tc='Op') as dm:
    dm[ru_RU] = "Проверяйте обновления самостоятельно"
#    dm[zh_CN] = ""

txt_vmtNoMixingOptions = "No mixing options"
with VlTrMapForKey(txt_vmtNoMixingOptions) as dm:
    dm[ru_RU] = "Варианты смешивания отсутствуют"
    dm[zh_CN] = "无混合选项"

txt_vqmtThereIsNothing = "There is nothing"
with VlTrMapForKey(txt_vqmtThereIsNothing) as dm:
    dm[ru_RU] = "Ничего нет"

txt_FloatQuickMath = "Float Quick Math"
with VlTrMapForKey(txt_FloatQuickMath) as dm:
    dm[zh_CN] = "快速浮点运算"

txt_VectorQuickMath = "Vector Quick Math"
with VlTrMapForKey(txt_VectorQuickMath) as dm:
    dm[zh_CN] = "快速矢量运算"

txt_BooleanQuickMath = "Boolean Quick Math"
with VlTrMapForKey(txt_BooleanQuickMath) as dm:
    dm[zh_CN] = "快速布尔运算"

txt_ColorQuickMode = "Color Quick Mode"
with VlTrMapForKey(txt_ColorQuickMode) as dm:
    dm[zh_CN] = "快速颜色运算"

#Заметка для переводчиков: слова ниже в вашем языке уже могут быть переведены.
#Заметка: Оставить их для поддержки версий без них.
with VlTrMapForKey("Virtual") as dm:
    dm[ru_RU] = "Виртуальный"
    dm[zh_CN] = "虚拟"
with VlTrMapForKey("Restore", tc='Op') as dm:
    dm[ru_RU] = "Восстановить"
    dm[zh_CN] = "恢复"
with VlTrMapForKey("Add New", tc='Op') as dm:
    dm[ru_RU] = "Добавить" #Без слова "новый"; оно не влезает, слишком тесно.
    dm[zh_CN] = "添加"
with VlTrMapForKey("Mode") as dm:
    dm[ru_RU] = "Режим"
    dm[zh_CN] = "模式"
with VlTrMapForKey("Colored") as dm:
    dm[ru_RU] = "Цветной"
    dm[zh_CN] = "根据端点类型自动设置颜色:"
with VlTrMapForKey("Edge pan") as dm:
    dm[ru_RU] = "Краевое панорамирование"
with VlTrMapForKey("Pie") as dm:
    dm[ru_RU] = "Пирог"
with VlTrMapForKey("Special") as dm:
    dm[ru_RU] = "Специальное"
with VlTrMapForKey("Customization") as dm:
    dm[ru_RU] = "Кастомизация"

prefsTran = None

class TranClsItemsUtil():
    def __init__(self, tup_items):
        if type(tup_items[0])==tuple:
            self.data = dict([(li[0], li[1:]) for li in tup_items])
        else:
            self.data = tup_items
    def __getattr__(self, att):
        if type(self.data)==tuple:
            match att:
                case 'name':
                    return self.data[0]
                case 'description':
                    return self.data[1]
            assert False
        else:
            return TranClsItemsUtil(self.data[att]) #`toolProp.ENUM1.name`
    def __getitem__(self, key):
        return TranClsItemsUtil(self.data[key]) #`toolProp['ENUM1'].name`
class TranAnnotFromCls():
    def __init__(self, annot):
        self.annot = annot
    def __getattr__(self, att):
        result = self.annot.keywords[att]
        return result if att!='items' else TranClsItemsUtil(result)
def GetAnnotFromCls(cls, key): #Так вот где они прятались, в аннотациях. А я то уж потерял надежду, думал вручную придётся.
    return TranAnnotFromCls(cls.__annotations__[key])

def GetPrefsRnaProp(att, inx=-1):
    prop = prefsTran.rna_type.properties[att]
    return prop if inx==-1 else getattr(prop,'enum_items')[inx]

def CollectTranslationDict(): #Для удобства переводов, которые требуют регистрации свойств. См. BringTranslations'ы.
    global prefsTran
    prefsTran = Prefs()
    ##
    for cls in list_toolClasses:
        cls.BringTranslations()
    VoronoiAddonPrefs.BringTranslations()
    ##
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolRoot,'isPassThrough').name) as dm:
        dm[ru_RU] = "Пропускать через выделение нода"
        dm[zh_CN] = "单击输出端口预览(而不是自动根据鼠标位置自动预览)"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolRoot,'isPassThrough').description) as dm:
        dm[ru_RU] = "Клик над нодом активирует выделение, а не инструмент"
        dm[zh_CN] = "单击输出端口才连接预览而不是根据鼠标位置动态预览"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolPairSk,'isCanBetweenFields').name) as dm:
        dm[ru_RU] = "Может между полями"
        dm[zh_CN] = "端口类型可以不一样"
    with VlTrMapForKey(GetAnnotFromCls(VoronoiToolPairSk,'isCanBetweenFields').description) as dm:
        dm[ru_RU] = "Инструмент может искать сокеты между различными типами полей"
#        dm[zh_CN] = "工具可以连接不同类型的端口"?
    ##
    dict_vlHhTranslations['zh_HANS'] = dict_vlHhTranslations['zh_CN']
    for cls in list_toolClasses:
        if (cls, 'zh_CN') in dict_toolLangSpecifDataPool:
            dict_toolLangSpecifDataPool[cls, 'zh_HANS'] = dict_toolLangSpecifDataPool[cls, 'zh_CN']

dict_toolLangSpecifDataPool = {}

def DisplayMessage(title, text, icon='NONE'):
    def PopupMessage(self, _context):
        self.layout.label(text=text, icon=icon, translate=False)
    bpy.context.window_manager.popup_menu(PopupMessage, title=title, icon='NONE')

def GetSkLabelName(sk):
    return sk.label if sk.label else sk.name
def CompareSkLabelName(sk1, sk2, isIgnoreCase=False):
    if isIgnoreCase:
        return GetSkLabelName(sk1).upper()==GetSkLabelName(sk2).upper()
    else:
        return GetSkLabelName(sk1)==GetSkLabelName(sk2)

def RecrGetNodeFinalLoc(nd):
    return nd.location+RecrGetNodeFinalLoc(nd.parent) if nd.parent else nd.location

def GetListOfNdEnums(nd):
    return [pr for pr in nd.rna_type.properties if not(pr.is_readonly or pr.is_registered)and(pr.type=='ENUM')]

def SelectAndActiveNdOnly(ndTar):
    for nd in ndTar.id_data.nodes:
        nd.select = False
    ndTar.id_data.nodes.active = ndTar
    ndTar.select = True

dict_typeSkToBlid = {
        'SHADER':    'NodeSocketShader',
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
def SkConvertTypeToBlid(sk):
    return dict_typeSkToBlid.get(sk.type, "Vl_Unknow")

set_utilTypeSkFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}

def IsClassicSk(sk):
    set_classicSocketsBlid = {'NodeSocketShader',  'NodeSocketColor',   'NodeSocketVector','NodeSocketFloat',     'NodeSocketString',  'NodeSocketInt',    'NodeSocketBool',
                              'NodeSocketRotation','NodeSocketGeometry','NodeSocketObject','NodeSocketCollection','NodeSocketMaterial','NodeSocketTexture','NodeSocketImage'}
    if sk.bl_idname=='NodeSocketVirtual':
        return True
    else:
        return SkConvertTypeToBlid(sk) in set_classicSocketsBlid

set_utilEquestrianPortalBlids = {'NodeGroupInput', 'NodeGroupOutput', 'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}

def IsClassicTreeBlid(blid):
    set_quartetClassicTreeBlids = {'ShaderNodeTree','GeometryNodeTree','CompositorNodeTree','TextureNodeTree'}
    return blid in set_quartetClassicTreeBlids


class PieRootData:
    isSpeedPie = False
    pieScale = 0
    pieDisplaySocketTypeInfo = 0
    pieDisplaySocketColor = 0
    pieAlignment = 0
    uiScale = 1.0
def SetPieData(self, toolData, prefs, col):
    def GetPiePref(name):
        return getattr(prefs, self.vlTripleName.lower()+name)
    toolData.isSpeedPie = GetPiePref("PieType")=='SPEED'
    toolData.pieScale = GetPiePref("PieScale") #todo1v6 уже есть toolData.prefs, так что можно аннигилировать; и перевозюкать всё это пограмотнее. А ещё комментарий в SolderClsToolNames().
    toolData.pieDisplaySocketTypeInfo = GetPiePref("PieSocketDisplayType")
    toolData.pieDisplaySocketColor = GetPiePref("PieDisplaySocketColor")
    toolData.pieAlignment = GetPiePref("PieAlignment")
    toolData.uiScale = self.uiScale
    toolData.prefs = prefs
    prefs.vaDecorColSkBack = col #Важно перед vaDecorColSk; см. VaUpdateDecorColSk().
    prefs.vaDecorColSk = col

class VlrtData:
    reprLastSkOut = ""
    reprLastSkIn = ""

def VlrtRememberLastSockets(sko, ski):
    if sko:
        VlrtData.reprLastSkOut = repr(sko)
        #ski без sko для VLRT бесполезен
        if (ski)and(ski.id_data==sko.id_data):
            VlrtData.reprLastSkIn = repr(ski)
def NewLinkHhAndRemember(sko, ski):
    DoLinkHh(sko, ski) #sko.id_data.links.new(sko, ski)
    VlrtRememberLastSockets(sko, ski)


def GetOpKmi(self, event): #Todo00 есть ли концепция или способ правильнее?
    #Оператор может иметь несколько комбинаций вызова, все из которых будут одинаковы по ключу в `keymap_items`, поэтому перебираем всех вручную
    blid = getattr(bpy.types, self.bl_idname).bl_idname
    for li in GetUserKmNe().keymap_items:
        if li.idname==blid:
            #Заметка: Искать и по соответствию самой клавише тоже, модификаторы тоже могут быть одинаковыми у нескольких вариантах вызова.
            if (li.type==event.type)and(li.shift_ui==event.shift)and(li.ctrl_ui==event.ctrl)and(li.alt_ui==event.alt):
                #Заметка: Могут быть и два идентичных хоткеев вызова, но Blender будет выполнять только один из них (по крайней мере для VL), тот, который будет первее в списке.
                return li # Эта функция также выдаёт только первого в списке.
def GetSetOfKeysFromEvent(event, isSide=False):
    set_keys = {event.type}
    if event.shift:
        set_keys.add('RIGHT_SHIFT' if isSide else 'LEFT_SHIFT')
    if event.ctrl:
        set_keys.add('RIGHT_CTRL' if isSide else 'LEFT_CTRL')
    if event.alt:
        set_keys.add('RIGHT_ALT' if isSide else 'LEFT_ALT')
    if event.oskey:
        set_keys.add('OSKEY' if isSide else 'OSKEY')
    return set_keys


def FtgGetTargetOrNone(ftg):
    return ftg.tar if ftg else None

def MinFromFtgs(ftg1, ftg2):
    if (ftg1)or(ftg2): #Если хотя бы один из них существует.
        if not ftg2: #Если одного из них не существует,
            return ftg1
        elif not ftg1: # то остаётся однозначный выбор для второго.
            return ftg2
        else: #Иначе выбрать ближайшего.
            return ftg1 if ftg1.dist<ftg2.dist else ftg2
    return None

def CheckUncollapseNodeAndReNext(nd, self, *, cond, flag=None): #Как же я презираю свёрнутые ноды.
    if (nd.hide)and(cond):
        nd.hide = False #Заметка: Осторожнее с вечным циклом в топологии NextAssignmentTool.
        #Алерт! type='DRAW_WIN' вызывает краш для некоторых редких деревьев со свёрнутыми нодами! Было бы неплохо забагрепортить бы это, если бы ещё знать как это отловить.
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        #todo0 стоит перерисовывать только один раз, если было раскрыто несколько нодов подряд; но без нужды. Если таковое случилось, то у этого инструмента хреновая топология поиска.
        self.NextAssignmentRoot(flag)

class LyAddQuickInactiveCol():
    def __init__(self, where, att='row', align=True, active=False):
        self.ly = getattr(where, att)(align=align)
        self.ly.active = active
    def __enter__(self):
        return self.ly
    def __exit__(self, *_):
        pass

def LyAddLeftProp(where, who, att, active=True):
    #where.prop(who, att); return
    row = where.row()
    row.alignment = 'LEFT'
    row.prop(who, att)
    row.active = active

def LyAddDisclosureProp(where, who, att, *, txt=None, active=True, isWide=False): #Заметка: Не может на всю ширину, если where -- row.
    tgl = getattr(who, att)
    rowMain = where.row(align=True)
    rowProp = rowMain.row(align=True)
    rowProp.alignment = 'LEFT'
    txt = txt if txt else None #+":"*tgl
    rowProp.prop(who, att, text=txt, icon='DISCLOSURE_TRI_DOWN' if tgl else 'DISCLOSURE_TRI_RIGHT', emboss=False)
    rowProp.active = active
    if isWide:
        rowPad = rowMain.row(align=True)
        rowPad.prop(who, att, text=" ", emboss=False)
    return tgl

def LyAddNoneBox(where):
    box = where.box()
    box.label()
    box.scale_y = 0.5
def LyAddHandSplitProp(where, who, att, *, text=None, active=True, returnAsLy=False, forceBoolean=0):
    spl = where.row().split(factor=0.42, align=True)
    spl.active = active
    row = spl.row(align=True)
    row.alignment = 'RIGHT'
    pr = who.rna_type.properties[att]
    isNotBool = pr.type!='BOOLEAN'
    isForceBoolean = not not forceBoolean
    row.label(text=pr.name*(isNotBool^isForceBoolean) if not text else text)
    if (not active)and(pr.type=='FLOAT')and(pr.subtype=='COLOR'):
        LyAddNoneBox(spl)
    else:
        if not returnAsLy:
            txt = "" if forceBoolean!=2 else ("True" if getattr(who, att) else "False")
            spl.prop(who, att, text=txt if isNotBool^isForceBoolean else None)
        else:
            return spl

def LyAddNiceColorProp(where, who, att, align=False, txt="", ico='NONE', decor=3):
    rowCol = where.row(align=align)
    rowLabel = rowCol.row()
    rowLabel.alignment = 'LEFT'
    rowLabel.label(text=txt if txt else TranslateIface(who.rna_type.properties[att].name)+":")
    rowLabel.active = decor%2
    rowProp = rowCol.row()
    rowProp.alignment = 'EXPAND'
    rowProp.prop(who, att, text="", icon=ico)
    rowProp.active = decor//2%2

def LyAddKeyTxtProp(where, prefs, att):
    rowProp = where.row(align=True)
    LyAddNiceColorProp(rowProp, prefs, att)
    #Todo0 я так и не врубился как пользоваться вашими prop event'ами, жуть какая-то. Помощь извне не помешала бы.
    with LyAddQuickInactiveCol(rowProp) as row:
        row.operator('wm.url_open', text="", icon='URL').url="https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html#:~:text="+getattr(prefs, att)

def LyAddLabeledBoxCol(where, *, text="", active=False, scale=1.0, align=True):
    colMain = where.column(align=True)
    box = colMain.box()
    box.scale_y = 0.5
    row = box.row(align=True)
    row.alignment = 'CENTER'
    row.label(text=text)
    row.active = active
    box = colMain.box()
    box.scale_y = scale
    return box.column(align=align)

def LyAddTxtAsEtb(where, txt):
    row = where.row(align=True)
    row.label(icon='ERROR')
    col = row.column(align=True)
    for li in txt.split("\n")[:-1]:
        col.label(text=li, translate=False)
def LyAddEtb(where): #"Вы дебагов фиксите? Нет, только нахожу."
    import traceback
    LyAddTxtAsEtb(where, traceback.format_exc())

def PowerArr4(arr, *, pw=1/2.2): #def PowerArrToVec(arr, *, pw=1/2.2): return Vec(map(lambda a: a**pw, arr))
    return (arr[0]**pw, arr[1]**pw, arr[2]**pw, arr[3]**pw)

def OpaqueCol3Tup4(col, *, al=1.0):
    return (col[0], col[1], col[2], al)
def MaxCol4Tup4(col):
    return (max(col[0], 0), max(col[1], 0), max(col[2], 0), max(col[3], 0))
def GetSkColorRaw(sk):
    if sk.bl_idname=='NodeSocketUndefined':
        return (1.0, 0.2, 0.2, 1.0)
    elif hasattr(sk,'draw_color'):
        return sk.draw_color(bpy.context, sk.node) #Заметка: Если нужно будет избавиться от всех `bpy.` и пронести честный путь всех context'ов, то сначала подумать об этом.
    elif hasattr(sk,'draw_color_simple'):
        return sk.draw_color_simple()
    else:
        return (1, 0, 1, 1)
def GetSkColSafeTup4(sk): #Не брать прозрачность от сокетов; и избавляться от отрицательных значений, что могут быть у аддонских сокетов.
    return OpaqueCol3Tup4(MaxCol4Tup4(GetSkColorRaw(sk)))
dict_skTypeHandSolderingColor = { #Для VQMT.
    'BOOLEAN':    (0.800000011920929,   0.6499999761581421,  0.8399999737739563,  1.0),
    'COLLECTION': (0.9599999785423279,  0.9599999785423279,  0.9599999785423279,  1.0),
    'RGBA':       (0.7799999713897705,  0.7799999713897705,  0.1599999964237213,  1.0),
    'VALUE':      (0.6299999952316284,  0.6299999952316284,  0.6299999952316284,  1.0),
    'GEOMETRY':   (0.0,                 0.8399999737739563,  0.6399999856948853,  1.0),
    'IMAGE':      (0.38999998569488525, 0.2199999988079071,  0.38999998569488525, 1.0),
    'INT':        (0.3499999940395355,  0.550000011920929,   0.36000001430511475, 1.0),
    'MATERIAL':   (0.9200000166893005,  0.46000000834465027, 0.5099999904632568,  1.0),
    'OBJECT':     (0.9300000071525574,  0.6200000047683716,  0.36000001430511475, 1.0),
    'ROTATION':   (0.6499999761581421,  0.38999998569488525, 0.7799999713897705,  1.0),
    'SHADER':     (0.38999998569488525, 0.7799999713897705,  0.38999998569488525, 1.0),
    'STRING':     (0.4399999976158142,  0.699999988079071,   1.0,                 1.0),
    'TEXTURE':    (0.6200000047683716,  0.3100000023841858,  0.6399999856948853,  1.0),
    'VECTOR':     (0.38999998569488525, 0.38999998569488525, 0.7799999713897705,  1.0),
    'CUSTOM':     (0.20000000298023224, 0.20000000298023224, 0.20000000298023224, 1.0) }
for dk, dv in dict_skTypeHandSolderingColor.items():
    dict_skTypeHandSolderingColor[dk] = PowerArr4(dv, pw=2.2)

class SoldThemeCols:
    dict_mapNcAtt = {0: 'input_node',        1:  'output_node',  3: 'color_node',
                     4: 'vector_node',       5:  'filter_node',  6: 'group_node',
                     8: 'converter_node',    9:  'matte_node',   10:'distor_node',
                     12:'pattern_node',      13: 'texture_node', 32:'script_node',
                     33:'group_socket_node', 40: 'shader_node',  41:'geometry_node',
                     42:'attribute_node',    100:'layout_node'}
def SolderThemeCols(themeNe):
    def GetNiceColNone(col4):
        return Col4(PowerArr4(col4, pw=1/1.75))
        #return Col4(col4)*1.5
    def MixThCol(col1, col2, fac=0.4): #\source\blender\editors\space_node\node_draw.cc : node_draw_basis() : "Header"
        return col1*(1-fac)+col2*fac
    SoldThemeCols.node_backdrop4 = Col4(themeNe.node_backdrop)
    SoldThemeCols.node_backdrop4pw = GetNiceColNone(SoldThemeCols.node_backdrop4) #Для Ctrl-F: оно используется, см ниже `+"4pw"`.
    for pr in themeNe.bl_rna.properties:
        dnf = pr.identifier
        if dnf.endswith("_node"):
            col4 = MixThCol(SoldThemeCols.node_backdrop4, Col4(OpaqueCol3Tup4(getattr(themeNe, dnf))))
            setattr(SoldThemeCols, dnf+"4", col4)
            setattr(SoldThemeCols, dnf+"4pw", GetNiceColNone(col4))
            setattr(SoldThemeCols, dnf+"3", Vec(col4[:3])) #Для vptRvEeIsSavePreviewResults.
def GetNdThemeNclassCol(ndTar):
    if ndTar.bl_idname=='ShaderNodeMix':
        match ndTar.data_type:
            case 'RGBA':   return SoldThemeCols.color_node4pw
            case 'VECTOR': return SoldThemeCols.vector_node4pw
            case _:        return SoldThemeCols.converter_node4pw
    else:
        return getattr(SoldThemeCols, SoldThemeCols.dict_mapNcAtt.get(BNode.GetFields(ndTar).typeinfo.contents.nclass, 'node_backdrop')+"4pw")

def GetBlackAlphaFromCol(col, *, pw):
    return ( 1.0-max(max(col[0], col[1]), col[2]) )**pw

tup_whiteCol4 = (1.0, 1.0, 1.0, 1.0)

class VlDrawData():
    shaderLine = None
    shaderArea = None
    worldZoom = -1.0
    def DrawPathLL(self, vpos, vcol, *, wid):
        gpu.state.blend_set('ALPHA') #Рисование текста сбрасывает метку об альфе, поэтому устанавливается каждый раз.
        self.shaderLine.bind()
        self.shaderLine.uniform_float('lineWidth', wid)
        self.shaderLine.uniform_float('viewportSize', gpu.state.viewport_get()[2:4])
        gpu_extras.batch.batch_for_shader(self.shaderLine, type='LINE_STRIP', content={'pos':vpos, 'color':vcol}).draw(self.shaderLine)
    def DrawAreaFanLL(self, vpos, col):
        gpu.state.blend_set('ALPHA')
        self.shaderArea.bind()
        self.shaderArea.uniform_float('color', col)
        #todo2v6 выяснить как или сделать сглаживание для полигонов тоже.
        gpu_extras.batch.batch_for_shader(self.shaderArea, type='TRI_FAN', content={'pos':vpos}).draw(self.shaderArea)
    def VecUiViewToReg(self, vec):
        vec = vec*self.uiScale
        return Vec2( self.view_to_region(vec.x, vec.y, clip=False) )
    ##
    def DrawRectangle(self, bou1, bou2, col):
        self.DrawAreaFanLL(( (bou1[0],bou1[1]), (bou2[0],bou1[1]), (bou2[0],bou2[1]), (bou1[0],bou2[1]) ), col)
    def DrawCircle(self, loc, rad, *, resl=54, col=tup_whiteCol4):
        #Первая вершина гордо в центре, остальные по кругу. Нужно чтобы артефакты сглаживания были красивыми в центр, а не наклонёнными в куда-то бок
        self.DrawAreaFanLL(( (loc[0],loc[1]), *[ (loc[0]+rad*cos(cyc*2.0*pi/resl), loc[1]+rad*sin(cyc*2.0*pi/resl)) for cyc in range(resl+1) ] ), col)
    def DrawRing(self, pos, rad, *, wid, resl=16, col=tup_whiteCol4, spin=0.0):
        vpos = tuple( ( rad*cos(cyc*2*pi/resl+spin)+pos[0], rad*sin(cyc*2*pi/resl+spin)+pos[1] ) for cyc in range(resl+1) )
        self.DrawPathLL(vpos, (col,)*(resl+1), wid=wid)
    def DrawWidePoint(self, loc, *, radHh, col1=Col4(tup_whiteCol4), col2=tup_whiteCol4, resl=54):
        colFacOut = Col4((0.5, 0.5, 0.5, 0.4))
        self.DrawCircle(loc, radHh+3.0, resl=resl, col=col1*colFacOut)
        self.DrawCircle(loc, radHh,     resl=resl, col=col1*colFacOut)
        self.DrawCircle(loc, radHh/1.5, resl=resl, col=col2)
    def __init__(self, context, cursorLoc, uiScale, prefs):
        self.shaderLine = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        self.shaderArea = gpu.shader.from_builtin('UNIFORM_COLOR')
        #self.shaderLine.uniform_float('lineSmooth', True) #Нет нужды, по умолчанию True.
        self.fontId = blf.load(prefs.dsFontFile) #Постоянная установка шрифта нужна чтобы шрифт не исчезал при смене темы оформления.
        ##
        self.whereActivated = context.space_data
        self.uiScale = uiScale
        self.view_to_region = context.region.view2d.view_to_region
        self.cursorLoc = cursorLoc
        ##
        for pr in prefs.bl_rna.properties:
            if pr.identifier.startswith("ds"):
                setattr(self, pr.identifier, getattr(prefs, pr.identifier))
        match prefs.dsDisplayStyle:
            case 'CLASSIC':    self.dsFrameDisplayType = 2
            case 'SIMPLIFIED': self.dsFrameDisplayType = 1
            case 'ONLY_TEXT':  self.dsFrameDisplayType = 0
        ##
        self.dsUniformColor = Col4(PowerArr4(self.dsUniformColor))
        self.dsUniformNodeColor = Col4(PowerArr4(self.dsUniformNodeColor))
        self.dsCursorColor = Col4(PowerArr4(self.dsCursorColor))

def DrawWorldStick(drata, pos1, pos2, col1, col2):
    drata.DrawPathLL( (drata.VecUiViewToReg(pos1), drata.VecUiViewToReg(pos2)), (col1, col2), wid=drata.dsLineWidth )
def DrawVlSocketArea(drata, sk, bou, col):
    loc = RecrGetNodeFinalLoc(sk.node)
    pos1 = drata.VecUiViewToReg(Vec2( (loc.x,               bou[0]) ))
    pos2 = drata.VecUiViewToReg(Vec2( (loc.x+sk.node.width, bou[1]) ))
    if drata.dsIsColoredSkArea:
        col[3] = drata.dsSocketAreaAlpha #Заметка: Сюда всегда приходит плотный цвет; так что можно не домножать, а перезаписывать.
    else:
        col = drata.dsUniformColor
    drata.DrawRectangle(pos1, pos2, col)
def DrawVlWidePoint(drata, loc, *, col1=Col4(tup_whiteCol4), col2=tup_whiteCol4, resl=54, forciblyCol=False): #"forciblyCol" нужен только для DrawDebug'а.
    if not(drata.dsIsColoredPoint or forciblyCol):
        col1 = col2 = drata.dsUniformColor
    drata.DrawWidePoint(drata.VecUiViewToReg(loc), radHh=( (6*drata.dsPointScale*drata.worldZoom)**2+10 )**0.5, col1=col1, col2=col2, resl=resl)

def DrawMarker(drata, loc, col, *, style):
    fac = GetBlackAlphaFromCol(col, pw=1.5)*0.625 #todo1v6 неэстетично выглядящие цвета маркера между ярким и чёрным; нужно что-нибудь с этим придумать.
    colSh = (fac, fac, fac, 0.5) #Тень
    colHl = (0.65, 0.65, 0.65, max(max(col[0],col[1]),col[2])*0.9/(3.5, 5.75, 4.5)[style]) #Прозрачная белая обводка
    colMt = (col[0], col[1], col[2], 0.925) #Цветная основа
    resl = (16, 16, 5)[style]
    ##
    drata.DrawRing((loc[0]+1.5, loc[1]+3.5), 9.0, wid=3.0, resl=resl, col=colSh)
    drata.DrawRing((loc[0]-3.5, loc[1]-5.0), 9.0, wid=3.0, resl=resl, col=colSh)
    def DrawMarkerBacklight(spin, col):
        resl = (16, 4, 16)[style]
        drata.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
        drata.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=3.0, resl=resl, col=col, spin=spin)
    DrawMarkerBacklight(pi/resl, colHl) #Маркер рисуется с артефактами "дырявых пикселей". Закостылить их дублированной отрисовкой с вращением.
    DrawMarkerBacklight(0.0,     colHl) #Но из-за этого нужно уменьшать альфу белой обводки в два раза.
    drata.DrawRing((loc[0],     loc[1]+5.0), 9.0, wid=1.0, resl=resl, col=colMt)
    drata.DrawRing((loc[0]-5.0, loc[1]-3.5), 9.0, wid=1.0, resl=resl, col=colMt)
def DrawVlMarker(drata, loc, *, ofsHh, col):
    vec = drata.VecUiViewToReg(loc)
    dir = 1 if ofsHh[0]>0 else -1
    ofsX = dir*( (20*drata.dsIsDrawText+drata.dsDistFromCursor)*1.5+drata.dsFrameOffset )+4
    col = col if drata.dsIsColoredMarker else drata.dsUniformColor
    DrawMarker(drata, (vec[0]+ofsHh[0]+ofsX, vec[1]+ofsHh[1]), col, style=drata.dsMarkerStyle)

def DrawFramedText(drata, pos1, pos2, txt, *, siz, adj, colTx, colFr, colBg):
    pos1x = ps1x = pos1[0]
    pos1y = ps1y = pos1[1]
    pos2x = ps2x = pos2[0]
    pos2y = ps2y = pos2[1]
    blur = 5
    #Рамка для текста:
    match drata.dsFrameDisplayType:
        case 2: #Красивая рамка
            gradResl = 12
            gradStripHei = (pos2y-pos1y)/gradResl
            #Градиентный прозрачностью фон:
            LFx = lambda x,a,b: ((x+b)/(b+1))**0.6*(1-a)+a
            for cyc in range(gradResl):
                drata.DrawRectangle( (pos1x, pos1y+cyc*gradStripHei),
                                     (pos2x, pos1y+cyc*gradStripHei+gradStripHei),
                                     (colBg[0]/2, colBg[1]/2, colBg[2]/2, LFx(cyc/gradResl,0.2,0.05)*colBg[3]) )
            #Яркая основная обводка:
            drata.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), (colFr,)*5, wid=1.0) #Омг, если colFr[0]==-1, то результат будет содержать комплексные числа. Чзх там происходит?
            #Дополнительная мягкая обводка (вместе с уголками), придающая красоты:
            ps1x += .25
            ps1y += .25
            ps2x -= .25
            ps2y -= .25
            ofs = 2.0
            vpos = (  (ps1x, ps1y-ofs),  (ps2x, ps1y-ofs),  (ps2x+ofs, ps1y),  (ps2x+ofs, ps2y),
                      (ps2x, ps2y+ofs),  (ps1x, ps2y+ofs),  (ps1x-ofs, ps2y),  (ps1x-ofs, ps1y),  (ps1x, ps1y-ofs)  )
            drata.DrawPathLL( vpos, ((colFr[0], colFr[1], colFr[2], 0.375),)*9, wid=1.0)
        case 1: #Для тех, кому не нравится красивая рамка. И чем им она не понравилась?.
            drata.DrawRectangle( (pos1x, pos1y), (pos2x, pos2y), (colBg[0]/2.4, colBg[1]/2.4, colBg[2]/2.4, 0.8*colBg[3]) )
            drata.DrawPathLL((pos1, (pos2x,pos1y), pos2, (pos1x,pos2y), pos1), ((0.1, 0.1, 0.1, 0.95),)*5, wid=1.0)
    #Текст:
    fontId = drata.fontId
    blf.size(fontId, siz)
    dim = blf.dimensions(fontId, txt)
    cen = ( (pos1x+pos2x)/2, (pos1y+pos2y)/2 )
    blf.position(fontId, cen[0]-dim[0]/2, cen[1]+adj, 0)
    blf.enable(fontId, blf.SHADOW)
    #Подсветка для тёмных сокетов:
    blf.shadow_offset(fontId, 1, -1)
    blf.shadow(fontId, blur, 1.0, 1.0, 1.0, GetBlackAlphaFromCol(colTx, pw=3.0)*0.75)
    blf.color(fontId, 0.0, 0.0, 0.0, 0.0)
    blf.draw(fontId, txt)
    #Сам текст:
    if drata.dsIsAllowTextShadow:
        col = drata.dsShadowCol
        blf.shadow_offset(fontId, drata.dsShadowOffset[0], drata.dsShadowOffset[1])
        blf.shadow(fontId, (0, 3, 5)[drata.dsShadowBlur], col[0], col[1], col[2], col[3])
    else:
        blf.disable(fontId, blf.SHADOW)
    blf.color(fontId, colTx[0], colTx[1], colTx[2], 1.0)
    blf.draw(fontId, txt)
    return (pos2x-pos1x, pos2y-pos1y)

def DrawWorldText(drata, pos, ofsHh, text, *, colText, colBg, fontSizeOverwrite=0): #fontSizeOverwrite нужен только для vptRvEeSksHighlighting.
    siz = drata.dsFontSize*(not fontSizeOverwrite)+fontSizeOverwrite
    blf.size(drata.fontId, siz)
    #Высота от "текста по факту" не вычисляется, потому что тогда каждая рамка каждый раз будет разной высоты.
    #Спецсимвол нужен, как "общий случай", чтобы покрыть максимальную высоту. Остальные символы нужны для особых шрифтов, что могут быть выше чем "█".
    dim = (blf.dimensions(drata.fontId, text)[0], blf.dimensions(drata.fontId, "█GJKLPgjklp!?")[1])
    pos = drata.VecUiViewToReg(pos)
    frameOffset = drata.dsFrameOffset
    ofsGap = 10
    pos = (pos[0]-(dim[0]+frameOffset+ofsGap)*(ofsHh[0]<0)+(frameOffset+1)*(ofsHh[0]>-1), pos[1]+frameOffset)
    #Я уже нахрен забыл, что я намудрил и как оно работает; но оно работает -- вот и славно, "работает -- не трогай":
    placePosY = round( (dim[1]+frameOffset*2)*ofsHh[1] ) #Без округления красивость горизонтальных линий пропадет.
    pos1 = (pos[0]+ofsHh[0]-frameOffset,               pos[1]+placePosY-frameOffset)
    pos2 = (pos[0]+ofsHh[0]+ofsGap+dim[0]+frameOffset, pos[1]+placePosY+dim[1]+frameOffset)
    ##
    return DrawFramedText(drata, pos1, pos2, text, siz=siz, adj=dim[1]*drata.dsManualAdjustment, colTx=PowerArr4(colText, pw=1/1.975), colFr=PowerArr4(colBg, pw=1/1.5), colBg=colBg)

def DrawVlSkText(drata, pos, ofsHh, ftg, *, fontSizeOverwrite=0): #Заметка: `pos` всегда ради drata.cursorLoc, но см. vptRvEeSksHighlighting.
    if not drata.dsIsDrawText:
        return (1, 0) #'1' нужен для сохранения информации направления для позиции маркеров.
    if drata.dsIsColoredText:
        colText = GetSkColSafeTup4(ftg.tar)
        colBg = MaxCol4Tup4(GetSkColorRaw(ftg.tar))
    else:
        colText = colBg = drata.dsUniformColor
    return DrawWorldText(drata, pos, ofsHh, ftg.soldText, colText=colText, colBg=colBg, fontSizeOverwrite=fontSizeOverwrite)

def DrawDebug(self, drata):
    def DebugTextDraw(pos, txt, r, g, b):
        blf.size(0,18)
        blf.position(0, pos[0]+10,pos[1], 0)
        blf.color(0, r,g,b,1.0)
        blf.draw(0, txt)
    DebugTextDraw(drata.VecUiViewToReg(drata.cursorLoc), "Cursor position here.", 1, 1, 1)
    if not self.tree:
        return
    col = Col4((1.0, 0.5, 0.5, 1.0))
    list_ftgNodes = self.ToolGetNearestNodes()
    if not list_ftgNodes:
        return
    DrawWorldStick(drata, drata.cursorLoc, list_ftgNodes[0].pos, col, col)
    for cyc, li in enumerate(list_ftgNodes):
        DrawVlWidePoint(drata, li.pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(li.pos), str(cyc)+" Node goal here", col.x, col.y, col.z)
    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(list_ftgNodes[0].tar)
    if list_ftgSksIn:
        col = Col4((0.5, 1, 0.5, 1))
        DrawVlWidePoint(drata, list_ftgSksIn[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(list_ftgSksIn[0].pos), "Nearest socketIn here", 0.5, 1, 0.5)
    if list_ftgSksOut:
        col = Col4((0.5, 0.5, 1, 1))
        DrawVlWidePoint(drata, list_ftgSksOut[0].pos, col1=col, col2=col, resl=4, forciblyCol=True)
        DebugTextDraw(drata.VecUiViewToReg(list_ftgSksOut[0].pos), "Nearest socketOut here", 0.75, 0.75, 1)

def TemplateDrawNodeFull(drata, ftgNd, *, side=1): #Шаблон переосмыслен; ура. Теперь он стал похожим на все остальные.. По крайней мере нет спагетти-кода из прошлых версий.
    #todo1v6 шаблон только по одному ftg, нет разбивки по слоям, два вызова будут рисовать точку с палкой от одного над текстом другого.
    if ftgNd:
        ndTar = ftgNd.tar
        if drata.dsIsColoredNodes: #Что ж.. всё-таки теперь у нода есть цвет; благодаря ctypes.
            colLn = GetNdThemeNclassCol(ndTar)
            colPt = colLn
            colTx = colLn
        else:
            colUnc = drata.dsUniformNodeColor
            colLn = colUnc if drata.dsIsColoredLine else drata.dsUniformColor
            colPt = colUnc if drata.dsIsColoredPoint else drata.dsUniformColor
            colTx = colUnc if drata.dsIsColoredText else drata.dsUniformColor
        if drata.dsIsDrawLine:
            DrawWorldStick(drata, drata.cursorLoc, ftgNd.pos, colLn, colLn)
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, ftgNd.pos, col1=colPt, col2=colPt)
        if (drata.dsIsDrawText)and(drata.dsIsDrawNodeNameLabel):
            txt = ndTar.label if ndTar.label else ndTar.bl_rna.name
            DrawWorldText(drata, drata.cursorLoc, (drata.dsDistFromCursor*side, -0.5), txt, colText=colTx, colBg=colTx)
    elif drata.dsIsDrawPoint:
        col = tup_whiteCol4 #Единственный оставшийся неопределённый цвет. 'dsCursorColor' здесь по задумке не подходит (весь аддон ради сокетов, ок да?.).
        DrawVlWidePoint(drata, drata.cursorLoc, col1=Col4(col), col2=col)

#Высокоуровневый шаблон рисования для сокетов. Теперь в названии есть "Sk", поскольку ноды полноценно вошли в VL.
#Пользоваться этим шаблоном невероятно кайфово, после того хардкора что был в старых версиях (даже не заглядывайте туда, там около-ад).
def TemplateDrawSksToolHh(drata, *args_ftgSks, isFlipSide=False, isDrawText=True, isClassicFlow=False, isDrawMarkersMoreTharOne=False): #Ура, шаблон переосмыслен. По ощущениям, лучше не стало.
    def GetPosFromFtg(ftg):
        return ftg.pos+Vec2((drata.dsPointOffsetX*ftg.dir, 0.0))
    list_ftgSks = [ar for ar in args_ftgSks if ar]
    cursorLoc = drata.cursorLoc
    #Отсутствие целей
    if not list_ftgSks: #Удобно получается использовать шаблон только ради ныне несуществующего DrawDoubleNone() путём отправки в args_ftgSks `None, None`.
        col = drata.dsCursorColor if drata.dsIsColoredPoint else drata.dsUniformColor
        isPair = length(args_ftgSks)==2
        vec = Vec2((drata.dsPointOffsetX*0.75, 0)) if (isPair)and(isClassicFlow) else Vec2((0.0, 0.0))
        if (isPair)and(drata.dsIsDrawLine)and(drata.dsIsAlwaysLine):
            DrawWorldStick(drata, cursorLoc-vec, cursorLoc+vec, col, col)
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, cursorLoc-vec, col1=col, col2=col)
            if (isPair)and(isClassicFlow):
                DrawVlWidePoint(drata, cursorLoc+vec, col1=col, col2=col)
        return
    #Линия классического потока
    if (isClassicFlow)and(drata.dsIsDrawLine)and(length(list_ftgSks)==2):
        ftg1 = list_ftgSks[0]
        ftg2 = list_ftgSks[1]
        if ftg1.dir*ftg2.dir<0: #Для VMLT, чтобы не рисовать для двух его сокетов, что оказались с одной стороны.
            if drata.dsIsColoredLine:
                col1 = GetSkColSafeTup4(ftg1.tar)
                col2 = GetSkColSafeTup4(ftg2.tar)
            else:
                col1 = col2 = drata.dsUniformColor
            DrawWorldStick(drata, GetPosFromFtg(ftg1), GetPosFromFtg(ftg2), col1, col2)
    #Основное:
    isOne = length(list_ftgSks)==1
    for ftg in list_ftgSks:
        if (drata.dsIsDrawLine)and( (not isClassicFlow)or(isOne and drata.dsIsAlwaysLine) ):
            if drata.dsIsColoredLine:
                col1 = GetSkColSafeTup4(ftg.tar)
                col2 = drata.dsCursorColor if (isOne+(drata.dsCursorColorAvailability-1))>0 else col1
            else:
                col1 = col2 = drata.dsUniformColor
            DrawWorldStick(drata, GetPosFromFtg(ftg), cursorLoc, col1, col2)
        if drata.dsIsDrawSkArea:
            DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Col4(GetSkColSafeTup4(ftg.tar)))
        if drata.dsIsDrawPoint:
            DrawVlWidePoint(drata, GetPosFromFtg(ftg), col1=Col4(MaxCol4Tup4(GetSkColorRaw(ftg.tar))), col2=Col4(GetSkColSafeTup4(ftg.tar)))
    #Текст
    if isDrawText: #Текст должен быть над всеми остальными ^.
        list_ftgSksIn = [ftg for ftg in list_ftgSks if ftg.dir<0]
        list_ftgSksOut = [ftg for ftg in list_ftgSks if ftg.dir>0]
        for list_ftgs in list_ftgSksIn, list_ftgSksOut: #"Накапливать", гениально! Головная боль со спагетти-кодом исчезла.
            hig = length(list_ftgs)-1
            for cyc, ftg in enumerate(list_ftgs):
                ofsY = 0.75*hig-1.5*cyc
                dir = ftg.dir*(1-isFlipSide*2)
                frameDim = DrawVlSkText(drata, cursorLoc, (drata.dsDistFromCursor*dir, ofsY-0.5), ftg)
                if (drata.dsIsDrawMarker)and( (ftg.tar.vl_sold_is_final_linked_cou)and(not isDrawMarkersMoreTharOne)or(ftg.tar.vl_sold_is_final_linked_cou>1) ):
                    DrawVlMarker(drata, cursorLoc, ofsHh=(frameDim[0]*dir, frameDim[1]*ofsY), col=GetSkColSafeTup4(ftg.tar))
    #Точка под курсором для классического потока
    if (isClassicFlow and isOne)and(drata.dsIsDrawPoint):
        DrawVlWidePoint(drata, cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor)

#Todo0SF Головная боль с "проскальзывающими кадрами"!! Debug, Collapse, Alt, и вообще везде.

class TestDraw:
    handle = None
    @classmethod
    def GetNoise(cls, w):
        from mathutils.noise import noise
        return noise((cls.time, w, cls.rand))
    @classmethod
    def Toggle(cls, context, tgl):
        if tgl:
            cls.rand = random.random()*32.0
            cls.time = 0.0
            cls.state = [0.5, 0.5, 0.5, 0.5]
            prefs = Prefs()
            cls.dev = prefs.dev
            cls.ctView2d = View2D.GetFields(context.region.view2d)
            cls.handle = bpy.types.SpaceNodeEditor.draw_handler_add(cls.CallbackDrawTest, (cls.dev, context, prefs), 'WINDOW', 'POST_PIXEL')
        else:
            bpy.types.SpaceNodeEditor.draw_handler_remove(cls.handle, 'WINDOW')
    @classmethod
    def CallbackDrawTest(cls, dev, context, prefs):
        from math import atan2
        if dev!=Prefs().dev:
            Prefs().dsIsTestDrawing = False
            bpy.types.SpaceNodeEditor.draw_handler_remove(cls.handle, 'WINDOW')
            return
        drata = VlDrawData(context, context.space_data.cursor_location, context.preferences.system.dpi/72, prefs)
        drata.worldZoom = cls.ctView2d.GetZoom()
        ##
        for cyc in range(4):
            noise = cls.GetNoise(cyc)
            fac = 1.0# if cyc<4 else (1.0 if noise>0 else cls.state[cyc])
            cls.state[cyc] = min(max(cls.state[cyc]+noise, 0.0), 1.0)*fac
        ##
        drata.DrawPathLL(( (0,0),(1000,1000) ), (tup_whiteCol4, tup_whiteCol4), wid=0.0)
        for cycWid in range(9):
            ofsWid = cycWid*45
            for cycAl in range(4):
                col = (1,1,1,.25*(1+cycAl))
                ofsAl = cycAl*8
                for cyc5 in range(2):
                    ofs5x = 65*cyc5
                    ofs5y = 0.5*cyc5
                    drata.DrawPathLL(( (100+ofs5x,100+ofsWid+ofsAl+ofs5y),(165+ofs5x,100+ofsWid+ofsAl+ofs5y) ), (col, col), wid=0.5*(1+cycWid))
        ##
        col = Col4(cls.state)
        drata.cursorLoc = context.space_data.cursor_location
        cursorReg = drata.VecUiViewToReg(drata.cursorLoc)
        vec = cursorReg-Vec2((500,500))
        drata.DrawRing((500,500), vec.length, wid=cursorReg.x/200, resl=max(3, int(cursorReg.y/20)), col=tup_whiteCol4, spin=pi/2-atan2(vec.x, vec.y))
        #Бардак:
        center = Vec2((context.region.width/2, context.region.height/2))
        txt = "a.¯\_(- _-)_/¯"
        DrawFramedText(drata, (300,300), (490,330), txt, siz=24, adj=(555-525)*-.2, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        txt = "a."
        DrawFramedText(drata, (375,170), (400,280), txt, siz=24, adj=0, colTx=tup_whiteCol4, colFr=tup_whiteCol4, colBg=tup_whiteCol4)
        txt = "GJKLPgjklp!? "
        loc = context.space_data.edit_tree.view_center
        col2 = col.copy()
        col2.w = max(0, (cursorReg.y-center.y/2)/150)
        DrawWorldText(drata, loc, (0, -.33), txt, colText=col2, colBg=col2)
        txt = "█GJKLPgjklp!?"
        col1 = col.copy()
        col1.w = 1.0
        DrawWorldText(drata, loc, (-1, .33), txt, colText=col1, colBg=col1)
        txt = "абф"
        DrawWorldText(drata, loc, (256, 0), txt, colText=col, colBg=col)
        DrawMarker(drata, center+Vec2((-50,-60)), col, style=0)
        DrawMarker(drata, center+Vec2((-100,-60)), col, style=1)
        DrawMarker(drata, center+Vec2((-150,-60)), col, style=2)
        drata.DrawPathLL( (center+Vec2((0,-60)), center+Vec2((100,-60))), (OpaqueCol3Tup4(col), OpaqueCol3Tup4(col)), wid=drata.dsLineWidth )
        drata.DrawPathLL( (center+Vec2((100,-60)), center+Vec2((200,-60))), (OpaqueCol3Tup4(col), OpaqueCol3Tup4(col, al=0.0)), wid=drata.dsLineWidth )
        drata.DrawWidePoint(center+Vec2((0,-60)), radHh=( (6*drata.dsPointScale+1)**2+10 )**0.5, col1=col, col2=Col4(OpaqueCol3Tup4(col)))
        drata.DrawWidePoint(center+Vec2((100,-60)), radHh=( (6*drata.dsPointScale+1)**2+10 )**0.5, col1=col, col2=Col4(OpaqueCol3Tup4(col)))
        import gpu_extras.presets; gpu_extras.presets.draw_circle_2d((256,256),(1,1,1,1),10)
        ##
        cls.time += 0.01
        bpy.context.space_data.backdrop_zoom = bpy.context.space_data.backdrop_zoom #Огонь. Но есть ли более "прямой" способ? Хвалёный area.tag_redraw() что-то не работает.

class VoronoiOpTool(bpy.types.Operator):
    bl_options = {'UNDO'} #Вручную созданные линки undo'тся, так что и в VL ожидаемо тоже. И вообще для всех.
    @classmethod
    def poll(cls, context):
        return context.area.type=='NODE_EDITOR' #Не знаю, зачем это нужно, но пусть будет.

class VoronoiToolPads: #-1
    usefulnessForCustomTree = None
    usefulnessForUndefTree = None
    usefulnessForNoneTree = None
    canDrawInAddonDiscl = None
    canDrawInAppearance = None
    def CallbackDrawTool(self, drata): pass
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): pass
    def ModalTool(self, event, prefs): pass
    #def MatterPurposePoll(self): return None
    def MatterPurposeTool(self, event, prefs, tree): pass
    def InitToolPre(self, event): return {}
    def InitTool(self, event, prefs, tree): return {}
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs): pass
    @classmethod
    def BringTranslations(cls): pass
class VoronoiToolRoot(VoronoiOpTool, VoronoiToolPads): #0
    usefulnessForUndefTree = False
    usefulnessForNoneTree = False
    canDrawInAddonDiscl = True
    canDrawInAppearance = False
    #Всегда неизбежно происходит кликанье в редакторе деревьев, где обитают ноды, поэтому для всех инструментов
    isPassThrough: bpy.props.BoolProperty(name="Pass through node selecting", default=False, description="Clicking over a node activates selection, not the tool")
    def CallbackDrawRoot(self, drata, context):
        if drata.whereActivated!=context.space_data: #Нужно, чтобы рисовалось только в активном редакторе, а не во всех у кого открыто то же самое дерево.
            return
        drata.worldZoom = self.ctView2d.GetZoom() #Получает каждый раз из-за EdgePan'а и колеса мыши. Раньше можно было бы обойтись и одноразовой пайкой.
        if self.prefs.dsIsFieldDebug:
            DrawDebug(self, drata)
        if self.tree: #Теперь для никакого дерева признаки жизни можно не подавать; выключено в связи с головной болью топологии, и пропуска инструмента для передачи хоткея в аддонских деревьях (?).
            self.CallbackDrawTool(drata)
    def ToolGetNearestNodes(self, includePoorNodes=False):
        return GetNearestNodesFtg(self.tree.nodes[:], self.cursorLoc, self.uiScale, includePoorNodes)
    def ToolGetNearestSockets(self, nd):
        return GetNearestSocketsFtg(nd, self.cursorLoc, self.uiScale)
    def NextAssignmentRoot(self, flag):
        if self.tree:
            try:
                self.NextAssignmentTool(flag, self.prefs, self.tree)
            except:
                EdgePanData.isWorking = False #Сейчас актуально только для VLT. Возможно стоит сделать ~self.ErrorToolProc, и в VLT "давать заднюю".
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
                raise
    def ModalMouseNext(self, event, prefs):
        match event.type:
            case 'MOUSEMOVE':
                self.NextAssignmentRoot(False)
            case self.kmi.type|'ESC':
                if event.value=='RELEASE':
                    return True
        return False
    def modal(self, context, event):
        context.area.tag_redraw()
        if num:=(event.type=='WHEELUPMOUSE')-(event.type=='WHEELDOWNMOUSE'):
            self.ctView2d.cur.Zooming(self.cursorLoc, 1.0-num*0.15)
        self.ModalTool(event, self.prefs)
        if not self.ModalMouseNext(event, self.prefs):
            return {'RUNNING_MODAL'}
        #* Здесь начинается завершение инструмента *
        EdgePanData.isWorking = False
        if event.type=='ESC': #Собственно то, что и должна делать клавиша побега.
            return {'CANCELLED'}
        with TryAndPass(): #Он может оказаться уже удалённым, см. второй такой.
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
        tree = self.tree
        if not tree:
            return {'FINISHED'}
        RestoreCollapsedNodes(tree.nodes)
        if (tree)and(tree.bl_idname=='NodeTreeUndefined'): #Если дерево нодов от к.-н. аддона исчезло, то остатки имеют NodeUndefined и NodeSocketUndefined.
            return {'CANCELLED'} #Через api линки на SocketUndefined всё равно не создаются, да и делать в этом дереве особо нечего; поэтому выходим.
        ##
        if not self.MatterPurposePoll():
            return {'CANCELLED'}
        if result:=self.MatterPurposeTool(event, self.prefs, tree):
            return result
        return {'FINISHED'}
    def invoke(self, context, event):
        tree = context.space_data.edit_tree
        self.tree = tree
        editorBlid = context.space_data.tree_type #Без нужды для `self.`?.
        self.isInvokeInClassicTree = IsClassicTreeBlid(editorBlid)
        if not(self.usefulnessForCustomTree or self.isInvokeInClassicTree):
            return {'PASS_THROUGH'} #'CANCELLED'?.
        if (not self.usefulnessForUndefTree)and(editorBlid=='NodeTreeUndefined'):
            return {'CANCELLED'} #Покидается с целью не-рисования.
        if not(self.usefulnessForNoneTree or tree):
            return {'FINISHED'}
        #Одинаковая для всех инструментов обработка пропуска выделения
        if (self.isPassThrough)and(tree)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): #Проверка на дерево вторым, для эстетической оптимизации.
            #Если хоткей вызова инструмента совпадает со снятием выделения, то выделенный строчкой выше нод будет де-выделен обратно после передачи эстафеты (но останется активным).
            #Поэтому для таких ситуаций нужно снять выделение, чтобы снова произошло переключение обратно на выделенный.
            tree.nodes.active.select = False #Но без условий, для всех подряд. Ибо ^иначе будет всегда выделение без переключения; и у меня нет идей, как бы я парился с распознаванием таких ситуаций.
            return {'PASS_THROUGH'}
        ##
        self.kmi = GetOpKmi(self, event)
        if not self.kmi:
            return {'CANCELLED'} #Если в целом что-то пошло не так, или оператор был вызван через кнопку макета.
        #Если в keymap в вызове оператора не указаны его свойства, они читаются от последнего вызова; поэтому их нужно устанавливать обратно по умолчанию.
        #Имеет смысл делать это как можно раньше; актуально для VQMT и VEST.
        for li in self.rna_type.properties:
            if li.identifier!='rna_type':
                #Заметка: Определить установленность в kmi -- наличие `kmi.properties[li.identifier]`.
                setattr(self, li.identifier, getattr(self.kmi.properties, li.identifier)) #Ради этого мне пришлось реверсинженерить Blender с отладкой. А ларчик просто открывался..
        ##
        self.prefs = Prefs() #"А ларчик просто открывался".
        self.uiScale = context.preferences.system.dpi/72
        self.cursorLoc = context.space_data.cursor_location #Это class Vector, копируется по ссылке; так что можно установить (привязать) один раз здесь и не париться.
        self.drata = VlDrawData(context, self.cursorLoc, self.uiScale, self.prefs)
        SolderThemeCols(context.preferences.themes[0].node_editor) #Так же, как и с fontId; хоть и в большинстве случаев тема не будет меняться во время всего сеанса.
        self.region = context.region
        self.ctView2d = View2D.GetFields(context.region.view2d)
        if self.prefs.vIsOverwriteZoomLimits:
            self.ctView2d.minzoom = self.prefs.vOwZoomMin
            self.ctView2d.maxzoom = self.prefs.vOwZoomMax
        ##
        if result:=self.InitToolPre(event): #Для 'Pre' менее актуально что-то возвращать.
            return result
        if result:=self.InitTool(event, self.prefs, tree): #Заметка: См. топологию: возвращение ничего равносильно возвращению `{'RUNNING_MODAL'}`.
            return result
        EdgePanInit(self, context.area)
        ##
        self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(self.CallbackDrawRoot, (self.drata, context,), 'WINDOW', 'POST_PIXEL')
        if tree: #Заметка: См. местную топологию, сам инструмент могёт, но каждый из них явно выключен для отсутствующих деревьев.
            SolderSkLinks(self.tree)
            SaveCollapsedNodes(tree.nodes)
            self.NextAssignmentRoot(True) #А всего-то нужно было перенести перед modal_handler_add(). #https://projects.blender.org/blender/blender/issues/113479
        ##
        context.area.tag_redraw() #Нужно, чтобы нарисовать при активации найденного при активации; при этом местный порядок не важен.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class VoronoiToolSk(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def InitToolPre(self, event):
        self.fotagoSk = None

class VoronoiToolPairSk(VoronoiToolSk): #2
    isCanBetweenFields: bpy.props.BoolProperty(name="Can between fields", default=True, description="Tool can connecting between different field types")
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1)
    def SkBetweenFieldsCheck(self, sk1, sk2):
        #Заметка: Учитывая предназначение и название этой функции, sk1 и sk2 в любом случае должны быть из полей, и только из них.
        return (sk1.type in set_utilTypeSkFields)and( (self.isCanBetweenFields)and(sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
    def InitToolPre(self, event):
        self.fotagoSk0 = None
        self.fotagoSk1 = None

class VoronoiToolTripleSk(VoronoiToolPairSk): #3
    def ModalTool(self, event, prefs):
        if (self.isStartWithModf)and(not self.canPickThird): #Кто будет всерьёз переключаться на выбор третьего сокета путём нажатия и отжатия к-н. модификатора?.
            # Ибо это адски дорого; коль уж выбрали хоткей без модификаторов, довольствуйтесь обрезанными возможностями. Или сделайте это себе сами.
            self.canPickThird = not(event.shift or event.ctrl or event.alt)
    def InitToolPre(self, event):
        self.fotagoSk2 = None
        self.canPickThird = False
        self.isStartWithModf = (event.shift)or(event.ctrl)or(event.alt)

class VoronoiToolNd(VoronoiToolRoot): #1
    def CallbackDrawTool(self, drata):
        TemplateDrawNodeFull(drata, self.fotagoNd)
    def MatterPurposePoll(self):
        return not not self.fotagoNd
    def InitToolPre(self, event):
        self.fotagoNd = None

class VoronoiToolPairNd(VoronoiToolSk): #2
    def MatterPurposePoll(self):
        return self.fotagoNd0 and self.fotagoNd1
    def InitToolPre(self, event):
        self.fotagoNd0 = None
        self.fotagoNd1 = None

class VoronoiToolAny(VoronoiToolSk, VoronoiToolNd): #2
    @staticmethod
    def TemplateDrawAny(drata, ftg, *, cond):
        if cond:
            TemplateDrawNodeFull(drata, ftg)
        else:
            TemplateDrawSksToolHh(drata, ftg)
    def MatterPurposePoll(self):
        return self.fotagoAny
    def InitToolPre(self, event):
        self.fotagoAny = None

class EdgePanData:
    area = None #Должен был быть 'context', но он всё время None.
    ctCur = None
    #Накостылил по-быстрому:
    isWorking = False
    view2d = None
    cursorPos = Vec2((0,0))
    uiScale = 1.0
    center = Vec2((0,0))
    delta = 0.0 #Ох уж эти ваши дельты.
    zoomFac = 0.5
    speed = 1.0

def EdgePanTimer():
    delta = perf_counter()-EdgePanData.delta
    vec = EdgePanData.cursorPos*EdgePanData.uiScale
    field0 = Vec2(EdgePanData.view2d.view_to_region(vec.x, vec.y, clip=False))
    zoomWorld = (EdgePanData.view2d.view_to_region(vec.x+1000, vec.y, clip=False)[0]-field0.x)/1000
    #Ещё немного реймарчинга:
    field1 = field0-EdgePanData.center
    field2 = Vec2(( abs(field1.x), abs(field1.y) ))
    field2 = field2-EdgePanData.center+Vec2((10, 10)) #Слегка уменьшить границы для курсора, находящегося вплотную к краю экрана.
    field2 = Vec2(( max(field2.x, 0), max(field2.y, 0) ))
    ##
    xi, yi, xa, ya = EdgePanData.ctCur.GetRaw()
    speedZoomSize = Vec2((xa-xi, ya-yi))/2.5*delta #125 без дельты.
    field1 = field1.normalized()*speedZoomSize*((zoomWorld-1)/1.5+1)*EdgePanData.speed*EdgePanData.uiScale
    if (field2.x!=0)or(field2.y!=0):
        EdgePanData.ctCur.TranslateScaleFac((field1.x, field1.y), fac=EdgePanData.zoomFac)
    EdgePanData.delta = perf_counter() #"Отправляется в неизвестность" перед следующим заходом.
    EdgePanData.area.tag_redraw()
    return 0.0 if EdgePanData.isWorking else None
def EdgePanInit(self, area):
    EdgePanData.area = area
    EdgePanData.ctCur = self.ctView2d.cur
    EdgePanData.isWorking = True
    EdgePanData.cursorPos = self.cursorLoc
    EdgePanData.uiScale = self.uiScale
    EdgePanData.view2d = self.region.view2d
    EdgePanData.center = Vec2((self.region.width/2, self.region.height/2))
    EdgePanData.delta = perf_counter() #..А ещё есть "слегка-границы".
    EdgePanData.zoomFac = 1.0-self.prefs.vEdgePanFac
    EdgePanData.speed = self.prefs.vEdgePanSpeed
    bpy.app.timers.register(EdgePanTimer, first_interval=0.0)

# *Я в конце 2022*: Уу, какой мимимишный аддончик у меня получился на 157 строчки кода.
# *Я в конце 2023*: ААаа чёрт возьми, что тут происходит??

class StructBase(ctypes.Structure):
    _subclasses = []
    __annotations__ = {}
    def __init_subclass__(cls):
        cls._subclasses.append(cls)
    @staticmethod
    def _init_structs():
        functype = type(lambda: None)
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
    @classmethod
    def GetFields(cls, tar):
        return cls.from_address(tar.as_pointer())

class BNodeSocketRuntimeHandle(StructBase): #\source\blender\makesdna\DNA_node_types.h
    if isWin:
        _pad0:        ctypes.c_char*8
    declaration:  ctypes.c_void_p
    changed_flag: ctypes.c_uint32
    total_inputs: ctypes.c_short
    _pad1:        ctypes.c_char*2
    location:     ctypes.c_float*2
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
    next:                   ctypes.c_void_p #lambda: ctypes.POINTER(BNodeSocket)
    prev:                   ctypes.c_void_p #lambda: ctypes.POINTER(BNodeSocket)
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
    if (viaverIsBlender4)and(bpy.app.version_string!='4.0.0 Alpha'):
        short_label:            ctypes.c_char*64
    default_attribute_name: ctypes.POINTER(ctypes.c_char)
    to_index:               ctypes.c_int
    link:                   ctypes.c_void_p
    ns:                     BNodeStack
    runtime:                ctypes.POINTER(BNodeSocketRuntimeHandle)

class BNodeType(StructBase): #\source\blender\blenkernel\BKE_node.h
    idname:         ctypes.c_char*64
    type:           ctypes.c_int
    ui_name:        ctypes.c_char*64
    ui_description: ctypes.c_char*256
    ui_icon:        ctypes.c_int
    if bpy.app.version>=(4,0,0):
        char:           ctypes.c_void_p
    width:          ctypes.c_float
    minwidth:       ctypes.c_float
    maxwidth:       ctypes.c_float
    height:         ctypes.c_float
    minheight:      ctypes.c_float
    maxheight:      ctypes.c_float
    nclass:         ctypes.c_int16 #https://github.com/ugorek000/ManagersNodeTree
class BNode(StructBase): #Для VRT.
    next:    lambda: ctypes.POINTER(BNode)
    prev:    lambda: ctypes.POINTER(BNode)
    inputs:     ctypes.c_void_p*2
    outputs:    ctypes.c_void_p*2
    name:       ctypes.c_char*64
    identifier: ctypes.c_int
    flag:       ctypes.c_int
    idname:     ctypes.c_char*64
    typeinfo:   ctypes.POINTER(BNodeType)
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
#Спасибо пользователю с ником "Oxicid", за этот кусок кода по части ctypes. "А что, так можно было?".
#Ох уж эти разрабы; пришлось самому добавлять возможность получать позиции сокетов. Месево от 'Blender 4.0 alpha' прижало к стенке и вынудило.
#..Это получилось сделать аш на питоне, неужели так сложно было пронести api?
#P.s. минута молчания в честь павших героев, https://projects.blender.org/blender/blender/pulls/117809.

def SkGetLocVec(sk):
    return Vec2(BNodeSocket.GetFields(sk).runtime.contents.location[:]) if (sk.enabled)and(not sk.hide) else Vec2((0, 0))
#Что ж, самое сложное пройдено. До технической возможности поддерживать свёрнутые ноды осталось всего ничего.
#Жаждущие это припрутся сюда по-быстрому с покерфейсом, возьмут что нужно, и модифицируют себе.
#Тот первый, кто это сделает, моё тебе послание: "Что ж, молодец. Теперь ты можешь сосаться к сокетам свёрнутого нода. Надеюсь у тебя счастья полные штаны".

class RectBase(StructBase):
    def GetRaw(self):
        return self.xmin, self.ymin, self.xmax, self.ymax
    def TranslateRaw(self, xy):
        self.xmin += xy[0]
        self.xmax += xy[0]
        self.ymin += xy[1]
        self.ymax += xy[1]
    def TranslateScaleFac(self, xy, fac=0.5):
        if xy[0]>0:
            self.xmin += xy[0]*fac
            self.xmax += xy[0]
        elif xy[0]<0:
            self.xmin += xy[0]
            self.xmax += xy[0]*fac
        ##
        if xy[1]>0:
            self.ymin += xy[1]*fac
            self.ymax += xy[1]
        elif xy[1]<0:
            self.ymin += xy[1]
            self.ymax += xy[1]*fac
    def Zooming(self, center=None, fac=1.0):
        if center:
            centerX = center[0]
            centerY = center[1]
        else:
            centerX = (self.xmax+self.xmin)/2
            centerY = (self.ymax+self.ymin)/2
        self.xmax = (self.xmax-centerX)*fac+centerX
        self.xmin = (self.xmin-centerX)*fac+centerX
        self.ymax = (self.ymax-centerY)*fac+centerY
        self.ymin = (self.ymin-centerY)*fac+centerY
class Rctf(RectBase):
    xmin: ctypes.c_float
    xmax: ctypes.c_float
    ymin: ctypes.c_float
    ymax: ctypes.c_float
class Rcti(RectBase):
    xmin: ctypes.c_int
    xmax: ctypes.c_int
    ymin: ctypes.c_int
    ymax: ctypes.c_int
class View2D(StructBase): #\source\blender\makesdna\DNA_view2d_types.h
    tot:       Rctf
    cur:       Rctf
    vert:      Rcti
    hor:       Rcti
    mask:      Rcti
    min:       ctypes.c_float*2
    max:       ctypes.c_float*2
    minzoom:   ctypes.c_float
    maxzoom:   ctypes.c_float
    scroll:    ctypes.c_short
    scroll_ui: ctypes.c_short
    keeptot:   ctypes.c_short
    keepzoom:  ctypes.c_short
    def GetZoom(self):
        return (self.mask.xmax-self.mask.xmin)/(self.cur.xmax-self.cur.xmin) #Благодаря keepzoom==3, можно читать только с одной оси.

StructBase._init_structs()

viaverSkfMethod = -1 #Переключатель-пайка под успешный способ взаимодействия. Можно было и распределить по карте с версиями, но у попытки "по факту" есть свои эстетические прелести.

#Заметка: ViaVer'ы не обновлялись.
def ViaVerNewSkf(tree, isSide, ess, name):
    if viaverIsBlender4: #Todo1VV переосмыслить топологию; глобальные функции с методами и глобальная переменная, указывающая на успешную из них; с "полной пайкой защёлкиванием".
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        socketType = ess if type(ess)==str else SkConvertTypeToBlid(ess)
        match viaverSkfMethod:
            case 1: skf = tree.interface.new_socket(name, in_out={'OUTPUT' if isSide else 'INPUT'}, socket_type=socketType)
            case 2: skf = tree.interface.new_socket(name, in_out='OUTPUT' if isSide else 'INPUT', socket_type=socketType)
    else:
        skf = (tree.outputs if isSide else tree.inputs).new(ess if type(ess)==str else ess.bl_idname, name)
    return skf
def ViaVerGetSkfa(tree, isSide):
    if viaverIsBlender4:
        global viaverSkfMethod
        if viaverSkfMethod==-1:
            viaverSkfMethod = 1+hasattr(tree.interface,'items_tree')
        match viaverSkfMethod:
            case 1: return tree.interface.ui_items
            case 2: return tree.interface.items_tree
    else:
        return (tree.outputs if isSide else tree.inputs)
def ViaVerGetSkf(tree, isSide, name):
    return ViaVerGetSkfa(tree, isSide).get(name)
def ViaVerSkfRemove(tree, isSide, name):
    if viaverIsBlender4:
        tree.interface.remove(name)
    else:
        (tree.outputs if isSide else tree.inputs).remove(name)

class Equestrian():
    set_equestrianNodeTypes = {'GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT', 'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT'}
    is_simrep = property(lambda a: a.type in ('SIM','REP'))
    @staticmethod
    def IsSocketDefinitely(ess):
        base = ess.bl_rna
        while base:
            dnf = base.identifier
            base = base.base
        if dnf=='NodeSocket':
            return True
        if dnf=='Node':
            return False
        return None
    @staticmethod
    def IsSimRepCorrectSk(node, skTar):
        if (skTar.bl_idname=='NodeSocketVirtual')and(node.type in {'SIMULATION_INPUT', 'SIMULATION_OUTPUT', 'REPEAT_INPUT', 'REPEAT_OUTPUT'}):
            return False
        match node.type:
            case 'SIMULATION_INPUT':
                return skTar!=node.outputs[0]
            case 'SIMULATION_OUTPUT'|'REPEAT_INPUT':
                return skTar!=node.inputs[0]
            case _:
                return True #raise Exception("IsSimRepCorrectSk() was called not for SimRep")
    def IsContainsSkf(self, skfTar):
        for skf in self.skfa: #На это нет api (или по крайней мере я не нашёл), поэтому пришлось проверять соответствие "по факту".
            if skf==skfTar:
                return True
        return False
    def GetSkfFromSk(self, skTar):
        if skTar.node!=self.node:
            raise Exception(f"Equestrian node is not equal `{skTar.path_from_id()}`")
        match self.type:
            case 'SIM'|'REP':
                match self.type: #Проверить, если сокет является "встроенным" для SimRep'а.
                    case 'SIM':
                        if self.node.type=='SIMULATION_INPUT':
                            if skTar==self.node.outputs[0]:
                                raise Exception("Socket \"Delta Time\" does not have interface.")
                        else:
                            if skTar==self.node.inputs[0]:
                                raise Exception("Socket \"Skip\" does not have interface.")
                    case 'REP':
                        if self.node.type=='REPEAT_INPUT':
                            if skTar==self.node.inputs[0]:
                                raise Exception("Socket \"Iterations\" does not have interface.")
                for skf in self.skfa:
                    if skf.name==skTar.name:
                        return skf
                raise Exception(f"Interface not found from `{skTar.path_from_id()}`") #Если сокет был как-то переименован у нода напрямую, а не через интерфейсы.
            case 'CLASSIC'|'GROUP':
                for skf in self.skfa:
                    if (skf.item_type=='SOCKET')and(skf.identifier==skTar.identifier):
                        return skf
    def GetSkFromSkf(self, skfTar, *, isOut):
        if not self.IsContainsSkf(skfTar):
            raise Exception(f"Equestrian items does not contain `{skfTar}`")
        match self.type:
            case 'SIM'|'REP':
                for sk in (self.node.outputs if isOut else self.node.inputs):
                    if sk.name==skfTar.name:
                        return sk
                raise Exception(f"Not found socket for `{skfTar}`")
            case 'CLASSIC'|'GROUP':
                if skfTar.item_type=='PANEL':
                    raise Exception(f"`Panel cannot be used for search: {skfTar}`")
                for sk in (self.node.outputs if isOut else self.node.inputs):
                    if sk.identifier==skfTar.identifier:
                        return sk
                raise Exception(f"`Socket for node side not found: {skfTar}`")
    def NewSkfFromSk(self, skTar, isFlipSide=False):
        newName = GetSkLabelName(skTar)
        match self.type:
            case 'SIM':
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','GEOMETRY'}: #todo1v6 неплохо было бы отреветь где они находятся, а не хардкодить.
                    raise Exception(f"Socket type is not supported by Simulation: `{skTar.path_from_id()}`")
                return self.skfa.new(skTar.type, newName)
            case 'REP':
                if skTar.type not in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL'}:
                    raise Exception(f"Socket type is not supported by Repeating: `{skTar.path_from_id()}`")
                return self.skfa.new(skTar.type, newName)
            case 'CLASSIC'|'GROUP':
                skfNew = self.skfa.data.new_socket(newName, socket_type=skTar.bl_idname, in_out='OUTPUT' if (skTar.is_output^isFlipSide) else 'INPUT')
                skfNew.hide_value = skTar.hide_value
                if hasattr(skfNew,'default_value'):
                    skfNew.default_value = skTar.default_value
                    if hasattr(skfNew,'min_value'):
                        nd = skTar.node
                        if (nd.type in {'GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT'})and(nd.node_tree): #Если сокет от другой группы нодов, то полная копия.
                            skf = Equestrian(nd).GetSkfFromSk(skTar)
                            for pr in skfNew.rna_type.properties:
                                if not(pr.is_readonly or pr.is_registered):
                                    setattr(skfNew, pr.identifier, getattr(skf, pr.identifier))
                    #Todo0 нужно придумать как внедриться до создания, чтобы у всех групп появился сокет со значением сразу же от sfk default. Как это делает сам Blender?
                    def FixInTree(tree):
                        for nd in tree.nodes:
                            if (nd.type=='GROUP')and(nd.node_tree==self.tree):
                                for sk in nd.inputs:
                                    if sk.identifier==skfNew.identifier:
                                        sk.default_value = skTar.default_value
                    for ng in bpy.data.node_groups:
                        if IsClassicTreeBlid(ng.bl_idname):
                            FixInTree(ng)
                    for mt in bpy.data.materials:
                        if mt.node_tree: #https://github.com/ugorek000/VoronoiLinker/issues/19; Я так и не понял, каким образом оно может быть None.
                            FixInTree(mt.node_tree)
                    for att in ('scenes','worlds','textures','lights','linestyles'): #Это все или я кого-то забыл?
                        for dt in getattr(bpy.data, att):
                            if dt.node_tree:
                                FixInTree(dt.node_tree)
                return skfNew
    def MoveBySkfs(self, skfFrom, skfTo, *, isSwap=False): #Можно было бы и взять на себя запары с "BySks", но это уже забота вызывающей стороны.
        match self.type:
            case 'SIM'|'REP':
                inxFrom = -1
                inxTo = -1
                #См. проверку наличия skf в GetSkFromSkf().
                for cyc, skf in enumerate(self.skfa):
                    if skf==skfFrom:
                        inxFrom = cyc
                    if skf==skfTo:
                        inxTo = cyc
                if inxFrom==-1:
                    raise Exception(f"Index not found from `{skfFrom}`")
                if inxTo==-1:
                    raise Exception(f"Index not found from `{skfTo}`")
                self.skfa.move(inxFrom, inxTo)
                if isSwap:
                    self.skfa.move(inxTo+(1-(inxTo>inxFrom)*2), inxFrom)
            case 'CLASSIC'|'GROUP':
                if not self.IsContainsSkf(skfFrom):
                    raise Exception(f"Equestrian tree is not equal for `{skfFrom}`")
                if not self.IsContainsSkf(skfTo):
                    raise Exception(f"Equestrian tree is not equal for `{skfTo}`")
                #Я не знаю способа, как по-нормальному(?) это реализовать честным образом без пересоединения от/к панелям. Хотя что-то мне подсказывает, что это единственный способ.
                list_panels = [ [None, None, None, None, ()] ]
                skfa = self.skfa
                #Запомнить панели:
                scos = {False:0, True:0}
                for skf in skfa:
                    if skf.item_type=='PANEL':
                        list_panels[-1][4] = (scos[False], scos[True])
                        list_panels.append( [None, skf.name, skf.description, skf.default_closed, (0, 0)] )
                        scos = {False:0, True:0}
                    else:
                        scos[skf.in_out=='OUTPUT'] += 1
                list_panels[-1][4] = (scos[False], scos[True])
                #Удалить панели:
                skft = skfa.data
                tgl = True
                while tgl:
                    tgl = False
                    for skf in skfa:
                        if skf.item_type=='PANEL':
                            skft.remove(skf)
                            tgl = True
                            break
                #Сделать перемещение:
                inxFrom = skfFrom.index
                inxTo = skfTo.index
                isDir = inxTo>inxFrom
                skft.move(skfa[inxFrom], inxTo+isDir)
                if isSwap:
                    skft.move(skfa[inxTo+(1-isDir*2)], inxFrom+(not isDir))
                #Восстановить панели:
                for li in list_panels[1:]:
                    li[0] = skft.new_panel(li[1], description=li[2], default_closed=li[3])
                scoSkf = 0
                scoPanel = length(list_panels)-1
                tgl = False
                for skf in reversed(skfa): #С конца, иначе по перемещённым в панели будет проходиться больше одного раза.
                    if skf.item_type=='SOCKET':
                        if (skf.in_out=='OUTPUT')and(not tgl):
                            tgl = True
                            scoSkf = 0
                            scoPanel = length(list_panels)-1
                        if scoSkf==list_panels[scoPanel][4][tgl]:
                            scoPanel -= 1
                            while (scoPanel>0)and(not list_panels[scoPanel][4][tgl]): #Панель может содержать ноль сокетов своей стороны.
                                scoPanel -= 1
                            scoSkf = 0
                        if scoPanel>0:
                            skft.move_to_parent(skf, list_panels[scoPanel][0], 0) #Из-за 'reversed(skfa)' отпала головная боль с позицией, и тут просто '0'; потрясающе удобное совпадение.
                        scoSkf += 1
    def __init__(self, snkd): #"snkd" = sk или nd.
        isSk = hasattr(snkd,'link_limit') #self.IsSocketDefinitely(snkd)
        ndEq = snkd.node if isSk else snkd
        if ndEq.type not in self.set_equestrianNodeTypes:
            raise Exception(f"Equestrian not found from `{snkd.path_from_id()}`")
        self.tree = snkd.id_data
        self.node = ndEq
        ndEq = getattr(ndEq,'paired_output', ndEq)
        match ndEq.type:
            case 'GROUP_OUTPUT'|'GROUP_INPUT':
                self.type = 'CLASSIC'
                self.skfa = ndEq.id_data.interface.items_tree
            case 'SIMULATION_OUTPUT':
                self.type = 'SIM'
                self.skfa = ndEq.state_items
            case 'REPEAT_OUTPUT':
                self.type = 'REP'
                self.skfa = ndEq.repeat_items
            case 'GROUP':
                self.type = 'GROUP'
                if not ndEq.node_tree:
                    raise Exception(f"Tree for nodegroup `{ndEq.path_from_id()}` not found, from `{snkd.path_from_id()}`")
                self.skfa = ndEq.node_tree.interface.items_tree

#dict_solderedSkLinksRaw = {}
#def SkGetSolderedLinksRaw(self): #.vl_sold_links_raw
#    return dict_solderedSkLinksRaw.get(self, [])

dict_solderedSkLinksFinal = {}
def SkGetSolderedLinksFinal(self): #.vl_sold_links_final
    return dict_solderedSkLinksFinal.get(self, [])

dict_solderedSkIsFinalLinkedCount = {}
def SkGetSolderedIsFinalLinkedCount(self): #.vl_sold_is_final_linked_cou
    return dict_solderedSkIsFinalLinkedCount.get(self, 0)

def SolderSkLinks(tree):
    def Update(dict_data, lk):
        dict_data.setdefault(lk.from_socket, []).append(lk)
        dict_data.setdefault(lk.to_socket, []).append(lk)
    #dict_solderedSkLinksRaw.clear()
    dict_solderedSkLinksFinal.clear()
    dict_solderedSkIsFinalLinkedCount.clear()
    for lk in tree.links:
        #Update(dict_solderedSkLinksRaw, lk)
        if (lk.is_valid)and not(lk.is_muted or lk.is_hidden):
            Update(dict_solderedSkLinksFinal, lk)
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.from_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.from_socket] += 1
            dict_solderedSkIsFinalLinkedCount.setdefault(lk.to_socket, 0)
            dict_solderedSkIsFinalLinkedCount[lk.to_socket] += 1

def RegisterSolderings():
    txtDoc = "Property from and only for VoronoiLinker addon."
    #bpy.types.NodeSocket.vl_sold_links_raw = property(SkGetSolderedLinksRaw)
    bpy.types.NodeSocket.vl_sold_links_final = property(SkGetSolderedLinksFinal)
    bpy.types.NodeSocket.vl_sold_is_final_linked_cou = property(SkGetSolderedIsFinalLinkedCount)
    #bpy.types.NodeSocket.vl_sold_links_raw.__doc__ = txtDoc
    bpy.types.NodeSocket.vl_sold_links_final.__doc__ = txtDoc
    bpy.types.NodeSocket.vl_sold_is_final_linked_cou.__doc__ = txtDoc
def UnregisterSolderings():
    #del bpy.types.NodeSocket.vl_sold_links_raw
    del bpy.types.NodeSocket.vl_sold_links_final
    del bpy.types.NodeSocket.vl_sold_is_final_linked_cou

#Обеспечивает поддержку свёрнутых нодов:
#Дождались таки... Конечно же не "честную поддержку". Я презираю свёрнутые ноды; и у меня нет желания шататься с округлостью, и соответствующе изменённым рисованием.
#Так что до введения api на позицию сокета, это лучшее что есть. Ждём и надеемся.
dict_collapsedNodes = {}
def SaveCollapsedNodes(nodes):
    dict_collapsedNodes.clear()
    for nd in nodes:
        dict_collapsedNodes[nd] = nd.hide
#Я не стал показывать развёрнутым только ближайший нод, а сделал этакий "след".
#Чтобы всё это не превращалось в хаос с постоянным "дёрганьем", и чтобы можно было провести, раскрыть, успокоиться, увидеть "текущую обстановку", проанализировать, и спокойно соединить что нужно.
def RestoreCollapsedNodes(nodes):
    for nd in nodes:
        if dict_collapsedNodes.get(nd, None): #Инструменты могут создавать ноды в процессе; например vptRvEeIsSavePreviewResults.
            nd.hide = dict_collapsedNodes[nd]

class Fotago(): #Found Target Goal, "а там дальше сами разберётесь".
    #def __getattr__(self, att): #Гениально. Второе после '(*args): return Vector((args))'.
    #    return getattr(self.target, att) #Но осторожнее, оно в ~5 раз медленнее.
    def __init__(self, target, *, dist=0.0, pos=Vec2((0.0, 0.0)), dir=0, boxHeiBound=(0.0, 0.0), text=""):
        #self.target = target
        self.tar = target
        #self.sk = target #Fotago.sk = property(lambda a:a.target)
        #self.nd = target #Fotago.nd = property(lambda a:a.target)
        self.blid = target.bl_idname #Fotago.blid = property(lambda a:a.target.bl_idname)
        self.dist = dist
        self.pos = pos
        #Далее нужно только для сокетов.
        self.dir = dir
        self.boxHeiBound = boxHeiBound
        self.soldText = text #Нужен для поддержки перевода на другие языки. Получать перевод каждый раз при рисовании слишком не комильфо, поэтому паяется.

def GenFtgFromNd(nd, pos, uiScale): #Вычленено из GetNearestNodesFtg, изначально без нужды, но VLTT вынудил.
    def DistanceField(field0, boxbou): #Спасибо RayMarching'у, без него я бы до такого не допёр.
        field1 = Vec2(( (field0.x>0)*2-1, (field0.y>0)*2-1 ))
        field0 = Vec2(( abs(field0.x), abs(field0.y) ))-boxbou/2
        field2 = Vec2(( max(field0.x, 0.0), max(field0.y, 0.0) ))
        field3 = Vec2(( abs(field0.x), abs(field0.y) ))
        field3 = field3*Vec2((field3.x<=field3.y, field3.x>field3.y))
        field3 = field3*-( (field2.x+field2.y)==0.0 )
        return (field2+field3)*field1
    isReroute = nd.type=='REROUTE'
    #Технический размер рероута явно перезаписан в 4 раза меньше, чем он есть.
    #Насколько я смог выяснить, рероут в отличие от остальных нодов свои размеры при изменении uiScale не меняет. Так что ему не нужно делиться на 'uiScale'.
    ndSize = Vec2((4, 4)) if isReroute else nd.dimensions/uiScale
    #Для нода позицию в центр нода. Для рероута позиция уже в его визуальном центре
    ndCenter = RecrGetNodeFinalLoc(nd).copy() if isReroute else RecrGetNodeFinalLoc(nd)+ndSize/2*Vec2((1.0, -1.0))
    if nd.hide: #Для VHT, "шустрый костыль" из имеющихся возможностей.
        ndCenter.y += ndSize.y/2-10 #Нужно быть аккуратнее с этой записью(write), ибо оно может оказаться указателем напрямую, если выше нодом является рероут, (https://github.com/ugorek000/VoronoiLinker/issues/16).
    #Сконструировать поле расстояний
    vec = DistanceField(pos-ndCenter, ndSize)
    #Добавить в список отработанный нод
    return Fotago(nd, dist=vec.length, pos=pos-vec)
def GetNearestNodesFtg(nodes, samplePos, uiScale, includePoorNodes=True): #Выдаёт список ближайших нод. Честное поле расстояний.
    #Почти честное. Скруглённые уголки не высчитываются. Их отсутствие не мешает, а вычисление требует больше телодвижений. Поэтому выпендриваться нет нужды.
    #С другой стороны скруглённость актуальна для свёрнутых нод, но я их презираю, так что...
    ##
    #Рамки пропускаются, ибо ни одному инструменту они не нужны.
    #Ноды без сокетов -- как рамки; поэтому можно игнорировать их ещё на этапе поиска.
    return sorted([GenFtgFromNd(nd, samplePos, uiScale) for nd in nodes if (nd.type!='FRAME')and( (nd.inputs)or(nd.outputs)or(includePoorNodes) )], key=lambda a:a.dist)

#Уж было я хотел добавить велосипедную структуру ускорения, но потом внезапно осознал, что ещё нужна информация и о "вторых ближайших". Так что кажись без полной обработки никуда.
#Если вы знаете, как можно это ускорить с сохранением информации, поделитесь со мной.
#С другой стороны, за всё время существования аддона не было ни одной стычки с производительностью, так что... только ради эстетики.
#А ещё нужно учитывать свёрнутые ноды, пропади они пропадом, которые могут раскрыться в процессе, наворачивая всю прелесть кеширования.

def GenFtgsFromPuts(nd, isSide, samplePos, uiScale): #Вынесено для vptRvEeSksHighlighting.
    #Заметка: Эта функция сама должна получить сторону от метки, ибо `reversed(nd.inputs)`.
    def SkIsLinkedVisible(sk):
        if not sk.is_linked:
            return True
        return (sk.vl_sold_is_final_linked_cou)and(sk.vl_sold_links_final[0].is_muted)
    list_result = []
    ndDim = Vec2(nd.dimensions/uiScale) #"nd.dimensions" уже содержат в себе корректировку на масштаб интерфейса, поэтому вернуть их обратно в мир.
    for sk in nd.outputs if isSide else reversed(nd.inputs):
        #Игнорировать выключенные и спрятанные
        if (sk.enabled)and(not sk.hide):
            pos = SkGetLocVec(sk)/uiScale #Чорт возьми, это офигенно. Долой велосипедный кринж прошлых версий.
            #Но api на высоту макета у сокета тем более нет, так что остаётся только точечно-костылить; пока не придумается что-то ещё.
            hei = 0
            if (not isSide)and(sk.type=='VECTOR')and(SkIsLinkedVisible(sk))and(not sk.hide_value):
                if "VectorDirection" in str(sk.rna_type):
                    hei = 2
                elif not( (nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))and(not viaverIsBlender4) )or( not(sk.name in ("Subsurface Radius","Radius"))):
                    hei = 3
            boxHeiBound = (pos.y-11-hei*20,  pos.y+11+max(sk.vl_sold_is_final_linked_cou-2,0)*5*(not isSide))
            txt = TranslateIface(GetSkLabelName(sk)) if sk.bl_idname!='NodeSocketVirtual' else TranslateIface("Virtual" if not sk.name else GetSkLabelName(sk))
            list_result.append(Fotago(sk, dist=(samplePos-pos).length, pos=pos, dir= 1 if sk.is_output else -1 , boxHeiBound=boxHeiBound, text=txt))
    return list_result
def GetNearestSocketsFtg(nd, samplePos, uiScale): #Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного. Всё верно, аддон назван именно из-за этого.
    #Если рероут, то имеем тривиальный вариант, не требующий вычисления; вход и выход всего одни, позиции сокетов -- он сам
    if nd.type=='REROUTE':
        loc = RecrGetNodeFinalLoc(nd)
        L = lambda a: Fotago(a, dist=(samplePos-loc).length, pos=loc, dir=1 if a.is_output else -1, boxHeiBound=(-1, -1), text=nd.label if nd.label else TranslateIface(a.name))
        return [L(nd.inputs[0])], [L(nd.outputs[0])]
    list_ftgSksIn = GenFtgsFromPuts(nd, False, samplePos, uiScale)
    list_ftgSksOut = GenFtgsFromPuts(nd, True, samplePos, uiScale)
    list_ftgSksIn.sort(key=lambda a:a.dist)
    list_ftgSksOut.sort(key=lambda a:a.dist)
    return list_ftgSksIn, list_ftgSksOut

#На самых истоках весь аддон создавался только ради этого инструмента. А то-то вы думаете названия одинаковые.
#Но потом я подахренел от обузданных возможностей, и меня понесло... понесло на создание мейнстримной троицы. Но этого оказалось мало, и теперь инструментов больше чем 7. Чума!
#Дублирующие комментарии есть только здесь (и в целом по убыванию). При спорных ситуациях обращаться к VLT для подражания, как к истине в последней инстанции.
class VoronoiLinkerTool(VoronoiToolPairSk): #Святая святых. То ради чего. Самый первый. Босс всех инструментов. Во славу великому полю расстояния!
    bl_idname = 'node.voronoi_linker'
    bl_label = "Voronoi Linker"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSkOut, self.fotagoSkIn, isFlipSide=True, isClassicFlow=True)
    @staticmethod
    def SkPriorityIgnoreCheck(sk): #False -- игнорировать.
        #Эта функция была добавлена по запросам извне (как и VLNST).
        set_ndBlidsWithAlphaSk = {'ShaderNodeTexImage', 'GeometryNodeImageTexture', 'CompositorNodeImage', 'ShaderNodeValToRGB', 'CompositorNodeValToRGB'}
        if sk.node.bl_idname in set_ndBlidsWithAlphaSk:
            return sk.name!="Alpha" #sk!=sk.node.outputs[1]
        return True
    def NextAssignmentTool(self, isFirstActivation, prefs, tree): #Todo0NA ToolAssignmentFirst, Next, /^Root/; несколько NA(), нод сокет на первый, нод сокет на второй.
        #В случае не найденного подходящего предыдущий выбор остаётся, отчего не получится вернуть курсор обратно и "отменить" выбор, что очень неудобно.
        self.fotagoSkIn = None #Поэтому обнуляется каждый раз перед поиском.
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    if (self.isFirstCling)or(ftg.blid!='NodeSocketVirtual')and( (not prefs.vltPriorityIgnoring)or(self.SkPriorityIgnoreCheck(ftg.tar)) ):
                        self.fotagoSkOut = ftg
                        break
            self.isFirstCling = True
            #Получить вход по условиям:
            skOut = FtgGetTargetOrNone(self.fotagoSkOut)
            if skOut: #Первый заход всегда isFirstActivation==True, однако нод может не иметь выходов.
                #Заметка: Нод сокета активации инструмента (isFirstActivation==True) в любом случае нужно разворачивать.
                #Свёрнутость для рероутов работает, хоть и не отображается визуально; но теперь нет нужды обрабатывать, ибо поддержка свёрнутости введена.
                CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
                #На этом этапе условия для отрицания просто найдут другой результат. "Прицепится не к этому, так к другому".
                for ftg in list_ftgSksIn:
                    #Заметка: Оператор `|=` всё равно заставляет вычисляться правый операнд.
                    skIn = ftg.tar
                    #Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет с обеих сторон, минуя различные типы
                    tgl = self.SkBetweenFieldsCheck(skIn, skOut)or( (skOut.node.type=='REROUTE')or(skIn.node.type=='REROUTE') )and(prefs.vltReroutesCanInAnyType)
                    #Работа с интерфейсами переехала в VIT, теперь только между виртуальными
                    tgl = (tgl)or( (skIn.bl_idname=='NodeSocketVirtual')and(skOut.bl_idname=='NodeSocketVirtual') )
                    #Если имена типов одинаковые
                    tgl = (tgl)or(skIn.bl_idname==skOut.bl_idname) #Заметка: Включая аддонские сокеты.
                    #Если аддонские сокеты в классических деревьях -- можно и ко всем классическим, классическим можно ко всем аддонским
                    tgl = (tgl)or(self.isInvokeInClassicTree)and(IsClassicSk(skOut)^IsClassicSk(skIn))
                    #Заметка: SkBetweenFieldsCheck() проверяет только меж полями, поэтому явная проверка одинаковости `bl_idname`.
                    if tgl:
                        self.fotagoSkIn = ftg
                        break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
                #На этом этапе условия для отрицания сделают результат никаким. Типа "Ничего не нашлось"; и будет обрабатываться соответствующим рисованием.
                if self.fotagoSkIn:
                    if self.fotagoSkOut.tar.node==self.fotagoSkIn.tar.node: #Если для выхода ближайший вход -- его же нод
                        self.fotagoSkIn = None
                    elif self.fotagoSkOut.tar.vl_sold_is_final_linked_cou: #Если выход уже куда-то подсоединён, даже если это выключенные линки (но из-за пайки их там нет).
                        for lk in self.fotagoSkOut.tar.vl_sold_links_final:
                            if lk.to_socket==self.fotagoSkIn.tar: #Если ближайший вход -- один из подсоединений выхода, то обнулить => "желаемое" соединение уже имеется.
                                self.fotagoSkIn = None
                                #Используемый в проверке выше "self.fotagoSkIn" обнуляется, поэтому нужно выходить, иначе будет попытка чтения из несуществующего элемента следующей итерацией.
                                break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkIn, flag=False) #"Мейнстримная" обработка свёрнутости.
            break #Обработать нужно только первый ближайший, удовлетворяющий условиям. Иначе результатом будет самый дальний.
    def ModalMouseNext(self, event, prefs):
        if event.type==prefs.vltRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState: #Дублирование от ниже. Не знаю как придумать это за один заход.
                self.NextAssignmentRoot(True)
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState: #Заметка: Требует существования, забота вызывающей стороны.
                        self.NextAssignmentRoot(True)
                    else:
                        self.NextAssignmentRoot(False)
                case self.kmi.type|'ESC':
                    return True
        return False
    def MatterPurposePoll(self):
        return self.fotagoSkOut and self.fotagoSkIn
    def MatterPurposeTool(self, event, prefs, tree):
        sko = self.fotagoSkOut.tar
        ski = self.fotagoSkIn.tar
        ##
        tree.links.new(sko, ski) #Самая важная строчка снова стала низкоуровневой.
        ##
        if ski.is_multi_input: #Если мультиинпут, то реализовать адекватный порядок подключения.
            #Моя личная хотелка, которая чинит странное поведение, и делает его логически-корректно-ожидаемым. Накой смысол последние соединённые через api лепятся в начало?
            list_skLinks = []
            for lk in ski.vl_sold_links_final:
                #Запомнить все имеющиеся линки по сокетам, и удалить их:
                list_skLinks.append((lk.from_socket, lk.to_socket, lk.is_muted))
                tree.links.remove(lk)
            #До версии b3.5 обработка ниже нужна была, чтобы новый io группы дважды не создавался.
            #Теперь без этой обработки Блендер или крашнется, или линк из виртуального в мультиинпут будет невалидным
            if sko.bl_idname=='NodeSocketVirtual':
                sko = sko.node.outputs[-2]
            tree.links.new(sko, ski) #Соединить очередной первым.
            for li in list_skLinks: #Восстановить запомненные. #todo0VV для поддержки старых версий: раньше было [:-1], потому что последний в списке уже являлся желанным, что был соединён строчкой выше.
                tree.links.new(li[0], li[1]).is_muted = li[2]
        VlrtRememberLastSockets(sko, ski) #Запомнить сокеты для VLRT, которые теперь являются "последними использованными".
        if prefs.vltSelectingInvolved:
            for nd in tree.nodes:
                nd.select = False
            sko.node.select = True
            ski.node.select = True
            tree.nodes.active = sko.node #P.s. не знаю, почему именно он; можно было и от ski. А делать из этого опцию как-то так себе.
    def InitTool(self, event, prefs, tree):
        self.fotagoSkOut = None
        self.fotagoSkIn = None
        self.repickState = False
        self.isFirstCling = False #Для SkPriorityIgnoreCheck и перевобора на виртуальные.
        if prefs.vltDeselectAllNodes:
            bpy.ops.node.select_all(action='DESELECT')
            tree.nodes.active = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddKeyTxtProp(col, prefs,'vltRepickKey')
        LyAddLeftProp(col, prefs,'vltReroutesCanInAnyType')
        LyAddLeftProp(col, prefs,'vltDeselectAllNodes')
        LyAddLeftProp(col, prefs,'vltPriorityIgnoring')
        LyAddLeftProp(col, prefs,'vltSelectingInvolved')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetPrefsRnaProp('vltRepickKey').name) as dm:
            dm[ru_RU] = "Клавиша перевыбора"
            dm[zh_CN] = "重选快捷键"
        with VlTrMapForKey(GetPrefsRnaProp('vltReroutesCanInAnyType').name) as dm:
            dm[ru_RU] = "Рероуты могут подключаться в любой тип"
            dm[zh_CN] = "重新定向节点可以连接到任何类型的节点"
        with VlTrMapForKey(GetPrefsRnaProp('vltDeselectAllNodes').name) as dm:
            dm[ru_RU] = "Снять выделение со всех нодов при активации"
            dm[zh_CN] = "快速连接时取消选择所有节点"
        with VlTrMapForKey(GetPrefsRnaProp('vltPriorityIgnoring').name) as dm:
            dm[ru_RU] = "Приоритетное игнорирование"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vltPriorityIgnoring').description) as dm:
            dm[ru_RU] = "Высокоуровневое игнорирование \"надоедливых\" сокетов при первом поиске.\n(Сейчас только \"Alpha\"-сокет у нод изображений)"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vltSelectingInvolved').name) as dm:
            dm[ru_RU] = "Выделять задействованные ноды"
            dm[zh_CN] = "快速连接后自动选择连接的节点"

SmartAddToRegAndAddToKmiDefs(VoronoiLinkerTool, "###_RIGHTMOUSE") #"##A_RIGHTMOUSE"?
dict_setKmiCats['grt'].add(VoronoiLinkerTool.bl_idname)

fitVltPiDescr = "High-level ignoring of \"annoying\" sockets during first search. (Currently, only the \"Alpha\" socket of the image nodes)"
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vltRepickKey: bpy.props.StringProperty(name="Repick Key", default='LEFT_ALT')
    vltReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be connected to any type", default=True)
    vltDeselectAllNodes:     bpy.props.BoolProperty(name="Deselect all nodes on activate",        default=False)
    vltPriorityIgnoring:     bpy.props.BoolProperty(name="Priority ignoring",                     default=False, description=fitVltPiDescr)
    vltSelectingInvolved:    bpy.props.BoolProperty(name="Selecting involved nodes",              default=False)

with VlTrMapForKey(VoronoiLinkerTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速连接"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiLinkerTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiLinkerTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiLinkerTool.bl_label}快速连接设置:"

dict_toolLangSpecifDataPool[VoronoiLinkerTool, ru_RU] = "Священный инструмент. Ради этого был создан весь аддон.\nМинута молчания в честь NodeWrangler'a-прародителя-первоисточника."

#Заметка: У DoLinkHh теперь слишком много других зависимостей, просто так его выдернуть уже будет сложнее.
#P.s. "HH" -- типа "High Level", но я с буквой промахнулся D:
def DoLinkHh(sko, ski, *, isReroutesToAnyType=True, isCanBetweenField=True, isCanFieldToShader=True): #Какое неожиданное визуальное совпадение с порядковым номером "sk0" и "sk1".
    #Коль мы теперь высокоуровневые, придётся суетиться с особыми ситуациями:
    if not(sko and ski): #Они должны быть.
        raise Exception("One of the sockets is none")
    if sko.id_data!=ski.id_data: #Они должны быть в одном мире.
        raise Exception("Socket trees vary")
    if not(sko.is_output^ski.is_output): #Они должны быть разного гендера.
        raise Exception("Sockets `is_output` is same")
    if not sko.is_output: #Выход должен быть первым.
        sko, ski = ski, sko
    #Заметка: "высокоуровневый", но не для глупых юзеров; соединяться между виртуальными можно, чорт побери.
    tree = sko.id_data
    if tree.bl_idname=='NodeTreeUndefined': #Дерево не должно быть потерянным.
        return #В потерянном дереве линки вручную создаются, а через api нет; так что выходим.
    if sko.node==ski.node: #Для одного и того же нода всё очевидно бессмысленно, пусть и возможно. Более актуально для интерфейсов.
        return
    isSkoField = sko.type in set_utilTypeSkFields
    isSkoNdReroute = sko.node.type=='REROUTE'
    isSkiNdReroute = ski.node.type=='REROUTE'
    isSkoVirtual = (sko.bl_idname=='NodeSocketVirtual')and(not isSkoNdReroute) #Виртуальный актуален только для интерфейсов, нужно исключить "рероута-самозванца".
    isSkiVirtual = (ski.bl_idname=='NodeSocketVirtual')and(not isSkiNdReroute) #Заметка: У виртуального и у аддонских сокетов sk.type=='CUSTOM'.
    #Можно, если
    if not( (isReroutesToAnyType)and( (isSkoNdReroute)or(isSkiNdReroute) ) ): #Хотя бы один из них рероут.
        if not( (sko.bl_idname==ski.bl_idname)or( (isCanBetweenField)and(isSkoField)and(ski.type in set_utilTypeSkFields) ) ): #Одинаковый по блидам или между полями.
            if not( (isCanFieldToShader)and(isSkoField)and(ski.type=='SHADER') ): #Поле в шейдер.
                if not(isSkoVirtual or isSkiVirtual): #Кто-то из них виртуальный (для интерфейсов).
                    if (not IsClassicTreeBlid(tree.bl_idname))or( IsClassicSk(sko)==IsClassicSk(ski) ): #Аддонский сокет в классических деревьях; см. VLT.
                        return None #Низя между текущими типами.
    #Отсеивание некорректных завершено. Теперь интерфейсы:
    ndo = sko.node
    ndi = ski.node
    isProcSkfs = True
    #Для суеты с интерфейсами требуется только один виртуальный. Если их нет, то обычное соединение.
    #Но если они оба виртуальные, читать информацию не от кого; от чего суета с интерфейсами бесполезна.
    if not(isSkoVirtual^isSkiVirtual): #Два условия упакованы в один xor.
        isProcSkfs = False
    elif ndo.type==ndi.type=='REROUTE': #Между рероутами гарантированно связь. Этакий мини-островок безопасности, затишье перед бурей.
        isProcSkfs = False
    elif not( (ndo.bl_idname in set_utilEquestrianPortalBlids)or(ndi.bl_idname in set_utilEquestrianPortalBlids) ): #Хотя бы один из нодов должен быть всадником.
        isProcSkfs = False
    if isProcSkfs: #Что ж, буря оказалось не такой уж и бурей. Я ожидал больший спагетти-код. Как всё легко и ясно получается, если мозги-то включить.
        #Получить нод всадника виртуального сокета
        ndEq = ndo if isSkoVirtual else ndi #Исходим из того, что всадник вывода равновероятен со своим компаньоном.
        #Коллапсируем компаньнов
        ndEq = getattr(ndEq,'paired_output', ndEq)
        #Интересно, где-нибудь в параллельной вселенной существуют виртуальные мультиинпуты?.
        skTar = sko if isSkiVirtual else ski
        match ndEq.bl_idname:
            case 'NodeGroupInput':  typeEq = 0
            case 'NodeGroupOutput': typeEq = 1
            case 'GeometryNodeSimulationOutput': typeEq = 2
            case 'GeometryNodeRepeatOutput':     typeEq = 3
        #Неподдерживаемых всадником типы не обрабатывать:
        can = True
        match typeEq:
            case 2: can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','GEOMETRY'}
            case 3: can = skTar.type in {'VALUE','INT','BOOLEAN','VECTOR','ROTATION','STRING','RGBA','OBJECT','IMAGE','GEOMETRY','COLLECTION','MATERIAL'}
        if not can:
            return None
        #Создать интерфейс
        match typeEq:
            case 0|1:
                equr = Equestrian(ski if isSkiVirtual else sko)
                skf = equr.NewSkfFromSk(skTar)
                skNew = equr.GetSkFromSkf(skf, isOut=skf.in_out!='OUTPUT') #* звуки страданий *
            case 2|3:
                _skf = (ndEq.state_items if typeEq==2 else ndEq.repeat_items).new({'VALUE':'FLOAT'}.get(skTar.type,skTar.type), GetSkLabelName(skTar))
                if True: #Перевыбор для SimRep'а тривиален; ибо у них нет панелей, и все новые сокеты появляются снизу.
                    skNew = ski.node.inputs[-2] if isSkiVirtual else sko.node.outputs[-2]
                else:
                    skNew = Equestrian(ski if isSkiVirtual else sko).GetSkFromSkf(_skf, isOut=isSkoVirtual)
        #Перевыбрать новый появившийся сокет
        if isSkiVirtual:
            ski = skNew
        else:
            sko = skNew
    #Путешествие успешно выполнено. Наконец-то переходим к самому главному:
    def DoLinkLL(tree, sko, ski):
        return tree.links.new(sko, ski) #hi.
    return DoLinkLL(tree, sko, ski)
    #Заметка: С версии b3.5 виртуальные инпуты теперь могут принимать в себя прям как мультиинпуты.
    # Они даже могут между собой по нескольку раз соединяться, офигеть. Разрабы "отпустили", так сказать, в свободное плаванье.

class VoronoiPreviewTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_preview'
    bl_label = "Voronoi Preview"
    usefulnessForCustomTree = True
    isSelectingPreviewedNode: bpy.props.BoolProperty(name="Select previewed node", default=True)
    isTriggerOnlyOnLink:      bpy.props.BoolProperty(name="Only linked",           default=False, description="Trigger only on linked socket") #Изначально было в prefs.
    isEqualAnchorType:        bpy.props.BoolProperty(name="Equal anchor type",     default=False, description="Trigger only on anchor type sockets")
    def CallbackDrawTool(self, drata):
        if (self.prefs.vptRvEeSksHighlighting)and(self.fotagoSk): #Помощь в реверс-инженеринге -- подсвечивать места соединения, и отображать имена этих сокетов, одновременно.
            SolderSkLinks(self.tree) #Иначе крашится на `ftg.tar==sk:`.
            #Определить масштаб для надписей:
            soldCursorLoc = drata.cursorLoc
            #Нарисовать:
            ndTar = self.fotagoSk.tar.node
            for isSide in (False, True):
                for skTar in ndTar.outputs if isSide else ndTar.inputs:
                    for lk in skTar.vl_sold_links_final:
                        sk = lk.to_socket if isSide else lk.from_socket
                        nd = sk.node
                        if (nd.type!='REROUTE')and(not nd.hide):
                            list_ftgSks = GenFtgsFromPuts(nd, not isSide, soldCursorLoc, drata.uiScale)
                            for ftg in list_ftgSks:
                                if ftg.tar==sk:
                                    #Хождение по рероутом не поддерживается. Потому что лень, и лень переделывать под это код.
                                    if drata.dsIsDrawSkArea:
                                        DrawVlSocketArea(drata, ftg.tar, ftg.boxHeiBound, Col4(GetSkColSafeTup4(ftg.tar)))
                                    DrawVlSkText(drata, ftg.pos, (1-isSide*2, -0.5), ftg, fontSizeOverwrite=min(24*drata.worldZoom*self.prefs.vptHlTextScale, 25))
                                    break
                        nd.hide = False #Запись во время рисования. По крайней мере, не так как сильно как в VMLT.
                        #todo0SF: использование bpy.ops.wm.redraw_timer вызывает зависание намертво. Так что из-за этого здесь имеется ещё один "проскальзывающий кадр".
        TemplateDrawSksToolHh(drata, self.fotagoSk, isDrawMarkersMoreTharOne=True)
    @staticmethod
    def OmgNodeColor(nd, col=None):
        set_omgApiNodesColor = {'FunctionNodeInputColor'} #https://projects.blender.org/blender/blender/issues/104909
        if nd.bl_idname in set_omgApiNodesColor:
            bn = BNode.GetFields(nd)
            if col:
                bn.color[0] = col[0]
                bn.color[1] = col[1]
                bn.color[2] = col[2]
            else:
                return (bn.color[0], bn.color[1], bn.color[2])
        else:
            if col:
                nd.color = col
            else:
                return nd.color.copy()
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        SolderSkLinks(tree) #Иначе крашится.
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        if False:
            #Уж было я добавил возможность цепляться к полям для виевера, но потом понял, что нет api на смену его типа предпросмотра. Опять. Придётся хранить на низком старте.
            isGeoViewer = False #Для цепляния к полям для гео-Viewer'a.
            if isGeoTree:
                for nd in tree.nodes:
                    if nd.type=='VIEWER':
                        isGeoViewer = True
                        break
        self.fotagoSk = None #Нет нужды, но сбрасывается для ясности картины. Было полезно для отладки.
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if (prefs.vptRvEeIsSavePreviewResults)and(nd.name==voronoiPreviewResultNdName): #Игнорировать готовый нод для переименования и тем самым сохраняя результаты предпросмотра.
                continue
            #Если в геометрических нодах, то игнорировать ноды без выходов геометрии
            if (isGeoTree)and(not self.isAnyAncohorExist):
                if not any(True for sk in nd.outputs if (sk.type=='GEOMETRY')and(not sk.hide)and(sk.enabled)): #Искать сокеты геометрии, которые видимы.
                    continue
            #Пропускать ноды если визуально нет сокетов; или есть, но только виртуальные. Для рероутов всё бесполезно.
            if (not any(True for sk in nd.outputs if (not sk.hide)and(sk.enabled)and(sk.bl_idname!='NodeSocketVirtual')))and(nd.type!='REROUTE'):
                continue
            #Всё выше нужно было для того, чтобы точка не висела просто так и нод не мешал для удобного использования инструмента. По ощущениям получаются как "прозрачные" ноды.
            #Игнорировать свой собственный спец-рероут-якорь (проверка на тип и имя)
            if ( (nd.type=='REROUTE')and(nd.name==voronoiAnchorCnName) ):
                continue
            #В случае успеха переходить к сокетам:
            list_ftgSksOut = self.ToolGetNearestSockets(nd)[1]
            for ftg in list_ftgSksOut:
                #Игнорировать свои сокеты мостов здесь. Нужно для нод нод-групп, у которых "торчит" сокет моста и к которому произойдёт прилипание без этой проверки; и после чего они будут удалены в VptPreviewFromSk().
                if ftg.tar.name==voronoiSkPreviewName:
                    continue
                #Этот инструмент триггерится на любой выход кроме виртуального. В геометрических нодах искать только выходы геометрии.
                #Якорь притягивает на себя превиев; рероут может принимать любой тип; следовательно -- при наличии якоря отключать триггер только на геосокеты
                if (ftg.blid!='NodeSocketVirtual')and( (not isGeoTree)or(ftg.tar.type=='GEOMETRY')or(self.isAnyAncohorExist) ):
                    can = True
                    if rrAnch:=tree.nodes.get(voronoiAnchorCnName): #EqualAnchorType.
                        rrSkBlId = rrAnch.outputs[0].bl_idname
                        can = (not self.isEqualAnchorType)or(ftg.blid==rrSkBlId)or(rrSkBlId=='NodeSocketVirtual')
                    #todo1v6 для якорей близости тоже сделать выбор по типу?
                    can = (can)and(not ftg.tar.node.label==voronoiAnchorDtName) #ftg.tar.node not in self.list_distanceAnchors
                    if can:
                        if (not self.isTriggerOnlyOnLink)or(ftg.tar.vl_sold_is_final_linked_cou): #Помощь в реверс-инженеринге -- триггериться только на существующие линки; ускоряет процесс "чтения/понимания" дерева.
                            self.fotagoSk = ftg
                            break
            if self.fotagoSk: #Завершать в случае успеха. Иначе, например для игнорирования своих сокетов моста, если у нода только они -- остановится рядом и не найдёт других.
                break
        if self.fotagoSk:
            CheckUncollapseNodeAndReNext(nd, self, cond=True)
            if prefs.vptIsLivePreview:
                VptPreviewFromSk(self, prefs, self.fotagoSk.tar)
            if prefs.vptRvEeIsColorOnionNodes: #Помощь в реверс-инженеринге -- вместо поиска глазами тоненьких линий, быстрое визуальное считывание связанных топологией нодов.
                SolderSkLinks(tree) #Без этого придётся окрашивать принимающий нод вручную, чтобы не "моргал".
                ndTar = self.fotagoSk.tar.node
                #Не париться с запоминанием последних и тупо выключать у всех каждый раз. Дёшево и сердито
                for nd in tree.nodes:
                    nd.use_custom_color = False
                def RecrRerouteWalkerPainter(sk, col):
                    for lk in sk.vl_sold_links_final:
                        nd = lk.to_node if sk.is_output else lk.from_node
                        if nd.type=='REROUTE':
                            RecrRerouteWalkerPainter(nd.outputs[0] if sk.is_output else nd.inputs[0], col)
                        else:
                            nd.use_custom_color = True
                            if (not prefs.vptRvEeIsSavePreviewResults)or(nd.name!=voronoiPreviewResultNdName): #Нод для сохранения результата не перекрашивать
                                self.OmgNodeColor(nd, col)
                            nd.hide = False #А также раскрывать их.
                for sk in ndTar.outputs:
                    RecrRerouteWalkerPainter(sk, prefs.vptOnionColorOut)
                for sk in ndTar.inputs:
                    RecrRerouteWalkerPainter(sk, prefs.vptOnionColorIn)
    def MatterPurposeTool(self, event, prefs, tree):
        SolderSkLinks(tree) #Иначе крашится.
        VptPreviewFromSk(self, prefs, self.fotagoSk.tar)
        VlrtRememberLastSockets(self.fotagoSk.tar, None)
        if prefs.vptRvEeIsColorOnionNodes:
            for nd in tree.nodes:
                dv = self.dict_saveRestoreNodeColors.get(nd, None) #Точно так же, как и в RestoreCollapsedNodes.
                if dv:
                    nd.use_custom_color = dv[0]
                    self.OmgNodeColor(nd, dv[1])
    def InitTool(self, event, prefs, tree):
        #Если использование классического viewer'а разрешено, завершить инструмент с меткой пропуска, "передавая эстафету" оригинальному виеверу.
        match tree.bl_idname:
            case 'GeometryNodeTree':
                if (prefs.vptAllowClassicGeoViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
            case 'CompositorNodeTree':
                if (prefs.vptAllowClassicCompositorViewer)and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
                    return {'PASS_THROUGH'}
        if prefs.vptRvEeIsColorOnionNodes:
            #Запомнить все цвета, и обнулить их всех:
            self.dict_saveRestoreNodeColors = {}
            for nd in tree.nodes:
                self.dict_saveRestoreNodeColors[nd] = (nd.use_custom_color, self.OmgNodeColor(nd))
                nd.use_custom_color = False
            #Заметка: Ноды сохранения результата с луковичными цветами обрабатываются как есть. Дублированный нод не будет оставаться незатрагиваемым.
        #Пайка:
        list_distAnchs = []
        for nd in tree.nodes:
            if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                list_distAnchs.append(nd)
                nd.label = voronoiAnchorDtName #А также используется для проверки на свои рероуты.
        self.list_distanceAnchors = list_distAnchs
        #Пайка:
        rrAnch = tree.nodes.get(voronoiAnchorCnName)
        #Некоторые пользователи в "начале знакомства" с инструментом захотят переименовать якорь.
        #Каждый призыв якоря одинаков по заголовку, а при повторном призыве заголовок всё равно меняется обратно на стандартный.
        #После чего пользователи поймут, что переименовывать якорь бесполезно.
        if rrAnch:
            rrAnch.label = voronoiAnchorCnName #Эта установка лишь ускоряет процесс осознания.
        self.isAnyAncohorExist = not not (rrAnch or list_distAnchs) #Для геонод; если в них есть якорь, то триггериться не только на геосокеты.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vptAllowClassicGeoViewer')
        LyAddLeftProp(col, prefs,'vptAllowClassicCompositorViewer')
        LyAddLeftProp(col, prefs,'vptIsLivePreview')
        row = col.row(align=True)
        LyAddLeftProp(row, prefs,'vptRvEeIsColorOnionNodes')
        if prefs.vptRvEeIsColorOnionNodes:
            row.prop(prefs,'vptOnionColorIn', text="")
            row.prop(prefs,'vptOnionColorOut', text="")
        else:
            LyAddNoneBox(row)
            LyAddNoneBox(row)
        row = col.row().row(align=True)
        LyAddLeftProp(row, prefs,'vptRvEeSksHighlighting')
        if True:#prefs.vptRvEeSksHighlighting:
            row = row.row(align=True)
            row.prop(prefs,'vptHlTextScale', text="Scale")
            row.active = prefs.vptRvEeSksHighlighting
        LyAddLeftProp(col, prefs,'vptRvEeIsSavePreviewResults')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectingPreviewedNode').name) as dm:
            dm[ru_RU] = "Выделять предпросматриваемый нод"
            dm[zh_CN] = "自动选择被预览的节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnlyOnLink').name) as dm:
            dm[ru_RU] = "Только подключённые"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnlyOnLink').description) as dm:
            dm[ru_RU] = "Цепляться только на подключённые сокеты"
            dm[zh_CN] = "只预览已有连接的输出端口"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').name) as dm:
            dm[ru_RU] = "Равный тип якоря"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isEqualAnchorType').description) as dm:
            dm[ru_RU] = "Цепляться только к сокетам типа якоря"
            dm[zh_CN] = "切换Voronoi_Anchor转接点预览时,只有类型和当前预览的端口类型一样才能被预览连接"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicGeoViewer').name) as dm:
            dm[ru_RU] = "Разрешить классический Viewer Геометрических узлов"
            dm[zh_CN] = "几何节点里使用默认预览方式"
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicGeoViewer').description) as dm:
            dm[ru_RU] = "Разрешить использование классического Viewer'а геометрических нодов путём клика по ноду"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicCompositorViewer').name) as dm:
            dm[ru_RU] = "Разрешить классический Viewer Композитора"
            dm[zh_CN] = "合成器里使用默认预览方式"
        with VlTrMapForKey(GetPrefsRnaProp('vptAllowClassicCompositorViewer').description) as dm:
            dm[ru_RU] = "Разрешить использование классического Viewer'а композиторных нодов путём клика по ноду"
            dm[zh_CN] = "默认是按顺序轮选输出接口端无法直选第N个通道接口"
        with VlTrMapForKey(GetPrefsRnaProp('vptIsLivePreview').name) as dm:
            dm[ru_RU] = "Предварительный просмотр в реальном времени"
            dm[zh_CN] = "实时预览"
        with VlTrMapForKey(GetPrefsRnaProp('vptIsLivePreview').description) as dm:
            dm[ru_RU] = "Предпросмотр в реальном времени"
            dm[zh_CN] = "即使没松开鼠标也能观察预览结果"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsColorOnionNodes').name) as dm:
            dm[ru_RU] = "Луковичные цвета нод"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsColorOnionNodes').description) as dm:
            dm[ru_RU] = "Окрашивать топологически соединённые ноды"
            dm[zh_CN] = "快速预览时将与预览的节点有连接关系的节点全部着色显示"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeSksHighlighting').name) as dm:
            dm[ru_RU] = "Подсветка топологических соединений"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeSksHighlighting').description) as dm:
            dm[ru_RU] = "Отображать имена сокетов, чьи линки подсоединены к ноду"
            dm[zh_CN] = "快速预览时高亮显示连接到预览的节点的上级节点的输出端口"
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsSavePreviewResults').name) as dm:
            dm[ru_RU] = "Сохранять результаты предпросмотра"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptRvEeIsSavePreviewResults').description) as dm:
            dm[ru_RU] = "Создавать предпросмотр через дополнительный нод, удобный для последующего копирования"
            dm[zh_CN] = "保存预览结果,通过新建一个预览节点连接预览"
        with VlTrMapForKey(GetPrefsRnaProp('vptOnionColorIn').name) as dm:
            dm[ru_RU] = "Луковичный цвет входа"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptOnionColorOut').name) as dm:
            dm[ru_RU] = "Луковичный цвет выхода"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vptHlTextScale').name) as dm:
            dm[ru_RU] = "Масштаб текста"
#            dm[zh_CN] = ""


SmartAddToRegAndAddToKmiDefs(VoronoiPreviewTool, "SC#_LEFTMOUSE")
dict_setKmiCats['grt'].add(VoronoiPreviewTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vptAllowClassicGeoViewer:        bpy.props.BoolProperty(name="Allow classic GeoNodes Viewer",   default=True,  description="Allow use of classic GeoNodes Viewer by clicking on node")
    vptAllowClassicCompositorViewer: bpy.props.BoolProperty(name="Allow classic Compositor Viewer", default=False, description="Allow use of classic Compositor Viewer by clicking on node")
    vptIsLivePreview:                bpy.props.BoolProperty(name="Live Preview",                    default=True,  description="Real-time preview")
    vptRvEeIsColorOnionNodes:        bpy.props.BoolProperty(name="Node onion colors",               default=False, description="Coloring topologically connected nodes")
    vptRvEeSksHighlighting:          bpy.props.BoolProperty(name="Topology connected highlighting", default=False, description="Display names of sockets whose links are connected to a node")
    vptRvEeIsSavePreviewResults:     bpy.props.BoolProperty(name="Save preview results",            default=False, description="Create a preview through an additional node, convenient for copying")
    vptOnionColorIn:  bpy.props.FloatVectorProperty(name="Onion color entrance", default=(0.55,  0.188, 0.188), min=0, max=1, size=3, subtype='COLOR')
    vptOnionColorOut: bpy.props.FloatVectorProperty(name="Onion color exit",     default=(0.188, 0.188, 0.5),   min=0, max=1, size=3, subtype='COLOR')
    vptHlTextScale:   bpy.props.FloatProperty(name="Text scale", default=1.0, min=0.5, max=5.0)

with VlTrMapForKey(VoronoiPreviewTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速预览"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiPreviewTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiPreviewTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiPreviewTool.bl_label}快速预览设置:"

dict_toolLangSpecifDataPool[VoronoiPreviewTool, ru_RU] = "Канонический инструмент для мгновенного перенаправления явного вывода дерева.\nЕщё более полезен при использовании совместно с VPAT."

class VptData:
    reprSkAnchor = ""

class VoronoiPreviewAnchorTool(VoronoiToolSk): #Что ж, теперь это полноценный инструмент; для которого даже есть нужда в новой отдельной категории в раскладке, наверное.
    bl_idname = 'node.voronoi_preview_anchor'
    bl_label = "Voronoi Preview Anchor"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    anchorType: bpy.props.IntProperty(name="Anchor type", default=0, min=0, max=2)
    isActiveAnchor: bpy.props.BoolProperty(name="Active anchor", default=True)
    isSelectAnchor: bpy.props.BoolProperty(name="Select anchor", default=True)
    isDeleteNonCanonAnchors: bpy.props.IntProperty(name="Clear anchors", default=0, min=0, max=2)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksOut = self.ToolGetNearestSockets(nd)[0]
            for ftg in list_ftgSksOut:
                if ftg.blid!='NodeSocketVirtual':
                    self.fotagoSk = ftg
                    break
            if self.fotagoSk:
                break
    def MatterPurposeTool(self, event, prefs, tree):
        VptData.reprSkAnchor = repr(self.fotagoSk.tar)
    def InitTool(self, event, prefs, tree):
        if self.isDeleteNonCanonAnchors:
            for nd in tree.nodes:
                if (nd.type=='REROUTE')and(nd.name.startswith(voronoiAnchorDtName)):
                    tree.nodes.remove(nd)
            if self.isDeleteNonCanonAnchors==2:
                if nd:=tree.nodes.get(voronoiAnchorCnName):
                    tree.nodes.remove(nd)
            return {'FINISHED'}
        if self.anchorType:
            for nd in tree.nodes:
                nd.select = False
            match self.anchorType:
                case 1:
                    rrAnch = tree.nodes.get(voronoiAnchorCnName)
                    isFirstApr = not rrAnch #Метка для обработки при первом появлении.
                    rrAnch = rrAnch or tree.nodes.new('NodeReroute')
                    rrAnch.name = voronoiAnchorCnName
                    rrAnch.label = voronoiAnchorCnName
                case 2:
                    sco = 0
                    tgl = True
                    while tgl:
                        sco += 1
                        name = voronoiAnchorDtName+str(sco)
                        tgl = not not tree.nodes.get(name, None)
                    isFirstApr = True
                    rrAnch = tree.nodes.new('NodeReroute')
                    rrAnch.name = name
                    rrAnch.label = voronoiAnchorDtName
            if self.isActiveAnchor:
                tree.nodes.active = rrAnch
            rrAnch.location = self.cursorLoc
            rrAnch.select = self.isSelectAnchor
            if isFirstApr:
                #Почему бы и нет. Зато красивый.
                rrAnch.inputs[0].type = 'COLLECTION' if self.anchorType==2 else 'MATERIAL' #Для аддонских деревьев, потому что в них "напролом" ниже не работает.
                rrAnch.outputs[0].type = rrAnch.inputs[0].type #Чтобы цвет выхода у линка был таким же.
                if self.anchorType==1:
                    #Установка напрямую `.type = 'CUSTOM'` не работает, поэтому идём напролом; спасибо обновлению Blender 3.5:
                    nd = tree.nodes.new('NodeGroupInput')
                    tree.links.new(nd.outputs[-1], rrAnch.inputs[0])
                    tree.nodes.remove(nd)
            return {'FINISHED'}
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'anchorType').name) as dm:
            dm[ru_RU] = "Тип якоря"
            dm[zh_CN] = "转接点的类型"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isActiveAnchor').name) as dm:
            dm[ru_RU] = "Делать якорь активным"
            dm[zh_CN] = "转接点设置为活动项"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectAnchor').name) as dm:
            dm[ru_RU] = "Выделять якорь"
            dm[zh_CN] = "转接点高亮显示"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isDeleteNonCanonAnchors').name) as dm:
            dm[ru_RU] = "Удалить имеющиеся якори"
#            dm[zh_CN] = ""

SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_RIGHTMOUSE")
SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_1", {'anchorType':1})
SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_2", {'anchorType':2})
SmartAddToRegAndAddToKmiDefs(VoronoiPreviewAnchorTool, "SC#_ACCENT_GRAVE", {'isDeleteNonCanonAnchors':2})
dict_setKmiCats['oth'].add(VoronoiPreviewAnchorTool.bl_idname) #spc?

with VlTrMapForKey(VoronoiPreviewAnchorTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi新建预览转接点"

dict_toolLangSpecifDataPool[VoronoiPreviewAnchorTool, ru_RU] = "Вынужденное отделение от VPT, своеобразный \"менеджер-компаньон\" для VPT.\nЯвное указание сокета и создание рероут-якорей."

class VptWayTree():
    def __init__(self, tree=None, nd=None):
        self.tree = tree
        self.nd = nd
        self.isUseExtAndSkPr = None #Оптимизация для чистки.
        self.finalLink = None #Для более адекватной организации в RvEe.
def VptGetTreesPath(nd):
    list_path = [VptWayTree(pt.node_tree, pt.node_tree.nodes.active) for pt in bpy.context.space_data.path]
    #Как я могу судить, сама суть реализации редактора узлов не хранит >нод<, через который пользователь зашёл в группу (но это не точно).
    #Поэтому если активным оказалась не нод-группа, то заменить на первый найденный-по-группе нод (или ничего, если не найдено)
    for curWy, upWy in zip(list_path, list_path[1:]):
        if (not curWy.nd)or(curWy.nd.type!='GROUP')or(curWy.nd.node_tree!=upWy.tree): #Определить отсутствие связи между глубинами.
            curWy.nd = None #Избавиться от текущего неправильного. Уж лучше останется никакой.
            for nd in curWy.tree.nodes:
                if (nd.type=='GROUP')and(nd.node_tree==upWy.tree): #Если в текущей глубине с неправильным нодом имеется нод группы с правильной группой.
                    curWy.nd = nd
                    break #Починка этой глубины успешно завершена.
    return list_path

def VptGetGeoViewerFromTree(tree):
    #Todo1PR Для очередных глубин тоже актуально получать перецепление сразу в виевер, но см. |1|, текущий конвейер логически не приспособлен для этого.
    #Поэтому больше не поддерживается, ибо "решено" только на половину. Так что старый добрый якорь в помощь.
    nameView = ""
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='SPREADSHEET':
                for space in area.spaces:
                    if space.type=='SPREADSHEET':
                        nameView = space.viewer_path.path[-1].ui_name #todo0VV
                        break
    if nameView:
        nd = tree.nodes.get(nameView)
    else:
        for nd in reversed(tree.nodes):
            if nd.type=='VIEWER':
                break #Нужен только первый попавшийся виевер, иначе будет неудобное поведение.
    if nd:
        if any(True for sk in nd.inputs[1:] if sk.vl_sold_is_final_linked_cou): #Todo1PR возможно для этого нужна опция. И в целом здесь бардак с этим виевером.
            return nd #Выбирать виевер только если у него есть линк для просмотра поля.
    return None

def VptGetRootNd(tree):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            for nd in tree.nodes:
                if (nd.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT_LINESTYLE','OUTPUT'})and(nd.is_active_output):
                    return nd
        case 'GeometryNodeTree':
            if nd:=VptGetGeoViewerFromTree(tree):
                return nd
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
def VptGetRootSk(tree, ndRoot, skTar):
    match tree.bl_idname:
        case 'ShaderNodeTree':
            inx = 0
            if ndRoot.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD'}:
                inx =  (skTar.name=="Volume")or(ndRoot.inputs[0].hide)
            return ndRoot.inputs[inx]
        case 'GeometryNodeTree':
            for sk in ndRoot.inputs:
                if sk.type=='GEOMETRY':
                    return sk
    return ndRoot.inputs[0] #Заметка: Здесь также окажется неудачный от GeometryNodeTree выше.

vptFeatureUsingExistingPath = True
#Заметка: Интерфейсы симуляции и зоны повторения не рассматривать, их обработка потребует поиска по каждому ноду в дереве, отчего будет BigO алерт.
#Todo1PR нужно всё снова перелизать; но прежде сделать тесты на все возможные комбинации глубин, якорей, геовиевера, отсутствия нод, "уже-путей", и прочих прелестей (а ещё аддонские деревья), и ещё местные BigO.
def DoPreviewCore(skTar, list_distAnchs, cursorLoc):
    def NewLostNode(type, ndTar=None):
        ndNew = tree.nodes.new(type)
        if ndTar:
            ndNew.location = ndTar.location
            ndNew.location.x += ndTar.width*2
        return ndNew
    list_way = VptGetTreesPath(skTar.node)
    higWay = length(list_way)-1
    list_way[higWay].nd = skTar.node #Подразумеваемым гарантией-конвейером глубин заходов целевой не обрабатывается, поэтому указывать явно. (не забыть перевести с эльфийского на русский)
    ##
    previewSkType = "RGBA" #Цвет, а не шейдер -- потому что иногда есть нужда вставить нод куда-то на пути предпросмотра.
    #Но если линки шейдерные -- готовьтесь к разочарованию. Поэтому цвет (кой и был изначально у NW).
    isGeoTree = list_way[0].tree.bl_idname=='GeometryNodeTree'
    if isGeoTree:
        previewSkType = "GEOMETRY"
    elif skTar.type=='SHADER':
        previewSkType = "SHADER"
    dnfLastSkEx = '' #Для vptFeatureUsingExistingPath.
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
    ##
    isInClassicTrees = IsClassicTreeBlid(skTar.id_data.bl_idname)
    for cyc in reversed(range(higWay+1)):
        curWay = list_way[cyc]
        tree = curWay.tree
        #Определить отправляющий нод:
        portalNdFrom = curWay.nd #skTar.node уже включён в путь для cyc==higWay.
        isCreatedNgOut = False
        if not portalNdFrom:
            portalNdFrom = tree.nodes.new(tree.bl_idname.replace("Tree","Group"))
            portalNdFrom.node_tree = list_way[cyc+1].tree
            isCreatedNgOut = True #Чтобы установить позицию нода от принимающего нода, который сейчас неизвестен.
        assert portalNdFrom
        #Определить принимающий нод:
        portalNdTo = None
        if not cyc: #Корень.
            portalNdTo = VptGetRootNd(tree)
            if (not portalNdTo)and(isInClassicTrees):
                #"Визуальное оповещение", что соединяться некуда. Можно было бы и вручную добавить, но лень шататься с принимающими нодами ShaderNodeTree'а.
                portalNdTo = NewLostNode('NodeReroute', portalNdFrom) #"У меня лапки".
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
                if nd:=VptGetGeoViewerFromTree(tree):
                    portalNdTo = nd
        if isCreatedNgOut:
            portalNdFrom.location = portalNdTo.location-Vec2((portalNdFrom.width+40, 0))
        assert portalNdTo or not isInClassicTrees
        #Определить отправляющий сокет:
        portalSkFrom = None
        if (vptFeatureUsingExistingPath)and(dnfLastSkEx):
            for sk in portalNdFrom.outputs:
                if sk.identifier==dnfLastSkEx:
                    portalSkFrom = sk
                    break
            dnfLastSkEx = '' #Важно обнулять. Выбранный сокет может не иметь линков или связи до следующего портала, отчего на следующей глубине будут несоответствия.
        if not portalSkFrom:
            if cyc==higWay:
                portalSkFrom = skTar
            else:
                if not cyc: #assert cyc
                    return list_way
                portalSkFrom = GetBridgeSk(portalNdFrom.outputs)
        assert portalSkFrom
        #Определить принимающий сокет:
        portalSkTo = None
        if (isGeoTree)and(portalNdTo.type=='VIEWER'):
            portalSkTo = portalNdTo.inputs[0]
        if (not portalSkTo)and(vptFeatureUsingExistingPath)and(cyc): #Имеет смысл записывать для не-корня.
            #Моё улучшающее изобретение -- если соединение уже имеется, то зачем создавать рядом такое же?.
            #Это эстетически комфортно, а также помогает очистить последствия предпросмотра не выходя из целевой глубины (добавлены условия, см. чистку).
            for lk in portalSkFrom.vl_sold_links_final:
                #Поскольку интерфейсы не удаляются, вместо мейнстрима ниже он заполучится отсюда (и результат будет таким же), поэтому вторая проверка для isUseExtAndSkPr.
                if (lk.to_node==portalNdTo)and(lk.to_socket.name!=voronoiSkPreviewName):
                    portalSkTo = lk.to_socket
                    dnfLastSkEx = portalSkTo.identifier #Выходы нода нод-группы и входы выхода группы совпадают. Сохранить информацию для следующей глубины продолжения.
                    curWay.isUseExtAndSkPr = GetBridgeSk(portalNdTo.inputs) #Для чистки. Если будет без линков, то удалять. При чистке они не ищутся по факту, потому что BigO.
        if (not portalSkTo)and(isInClassicTrees): #Основной мейнстрим получения.
            portalSkTo = VptGetRootSk(tree, portalNdTo, skTar) if not cyc else GetBridgeSk(portalNdTo.inputs) #|1|.
        if (not portalSkTo)and(cyc): #Очередные глубины -- всегда группы, для них и нужно генерировать skf. Проверка на `cyc` не обязательна, сокет с корнем (из-за рероута) всегда будет.
            #Если выше не смог получить сокет от входов нода нод группы, то и интерфейса-то тоже нет. Поэтому проверка `not tree.outputs.get(voronoiSkPreviewName)` без нужды.
            ViaVerNewSkf(tree, True, GetTypeSkfBridge(), voronoiSkPreviewName).hide_value = True
            portalSkTo = GetBridgeSk(portalNdTo.inputs) #Перевыбрать новосозданный.
        #Обработка якоря, мимикрирующего под явное указание канонического вывода:
        if (cyc==higWay)and(VptData.reprSkAnchor):
            skAnchor = None
            try:
                skAnchor = eval(VptData.reprSkAnchor)
                if skAnchor.id_data!=skTar.id_data:
                    skAnchor = None
                    VptData.reprSkAnchor = ""
            except:
                VptData.reprSkAnchor = ""
            if (skAnchor):#and(skAnchor.node!=skTar.node):
                portalSkTo = skAnchor
        assert portalSkTo or not isInClassicTrees
        #Соединить:
        ndAnchor = tree.nodes.get(voronoiAnchorCnName)
        if (cyc==higWay)and(not ndAnchor)and(list_distAnchs): #Ближайший ищется от курсора; где-же взять курсор для нецелевых глубин?.
            min = 32768
            for nd in list_distAnchs:
                len = (nd.location-cursorLoc).length
                if min>len:
                    min = len
                    ndAnchor = nd
        if ndAnchor: #Якорь делает "планы изменились", и пересасывает поток на себя.
            lk = tree.links.new(portalSkFrom, ndAnchor.inputs[0])
            #tree.links.new(ndAnchor.outputs[0], portalSkTo)
            curWay.finalLink = lk
            break #Завершение после напарывания повышает возможности использования якоря, делая его ещё круче. Если у вас течка от Voronoi_Anchor, то я вас понимаю. У меня тоже.
            #Завершение позволяет иметь пользовательское соединение от глубины с якорем и до корня, не разрушая их.
        elif (portalSkFrom)and(portalSkTo): #assert portalSkFrom and portalSkTo #Иначе обычное соединение маршрута.
            lk = tree.links.new(portalSkFrom, portalSkTo)
            curWay.finalLink = lk
    return list_way
def VptPreviewFromSk(self, prefs, skTar):
    if not(skTar and skTar.is_output):
        return
    list_way = DoPreviewCore(skTar, self.list_distanceAnchors, self.cursorLoc)
    if self.isSelectingPreviewedNode:
        SelectAndActiveNdOnly(skTar.node) #Важно не только то, что только один он выделяется, но ещё и то, что он становится активным.
    if not self.isInvokeInClassicTree:
        return
    #Гениально я придумал удалять интерфейсы после предпросмотра; стало возможным благодаря не-удалению в контекстных путях. Теперь ими можно будет пользоваться более свободно.
    if (True)or(not self.tree.nodes.get(voronoiAnchorCnName)): #Про 'True' читать ниже.
        #Если в текущем дереве есть якорь, то никаких voronoiSkPreviewName не удалять; благодаря чему становится доступным ещё одно особое использование инструмента.
        #Должно было стать логическим продолжением после "завершение после напарывания", но допёр до этого только сейчас.
        #P.s. Я забыл нахрен какое. А теперь они не удаляются от контекстных путей, так что теперь информация утеряна D:
        dict_treeNext = dict({(wy.tree, wy.isUseExtAndSkPr) for wy in list_way})
        dict_treeOrder = dict({(wy.tree, cyc) for cyc, wy in enumerate(reversed(list_way))}) #Путь имеет линки, середине не узнать о хвосте, поэтому из текущей глубины до корня, чтобы "каскадом" корректно обработалось.
        for ng in sorted(bpy.data.node_groups, key=lambda a: dict_treeOrder.get(a,-1)):
            #Удалить все свои следы предыдущего использования инструмента для всех нод-групп, чей тип текущего редактора такой же.
            if ng.bl_idname==self.tree.bl_idname:
                #Но не удалять мосты для деревьев контекстного пути (удалять, если их сокеты пустые).
                sk = dict_treeNext.get(ng, None) #Для Ctrl-F: isUseExtAndSkPr используется здесь.
                if (ng not in dict_treeNext)or((not sk.vl_sold_is_final_linked_cou) if sk else None)or( (ng==self.tree)and(sk) ):
                    sk = True
                    while sk: #Ищется по имени. Пользователь может сделать дубликат, от чего без while они будут исчезать по одному каждую активацию предпросмотра.
                        sk = ViaVerGetSkf(ng, True, voronoiSkPreviewName)
                        if sk:
                            ViaVerSkfRemove(ng, True, sk)
    if (prefs.vptRvEeIsSavePreviewResults)and(not self.isAnyAncohorExist): #Помощь в реверс-инженеринге -- сохранять текущий сокет просмотра для последующего "менеджмента".
        def GetTypeOfNodeSave(sk):
            match sk.type:
                case 'GEOMETRY': return 2
                case 'SHADER': return 1
                case _: return 0
        finalLink = list_way[-1].finalLink
        idSave = GetTypeOfNodeSave(finalLink.from_socket)
        pos = finalLink.to_node.location
        pos = (pos[0]+finalLink.to_node.width+40, pos[1])
        ndRvSave = self.tree.nodes.get(voronoiPreviewResultNdName)
        if ndRvSave:
            if ndRvSave.label!=voronoiPreviewResultNdName:
                ndRvSave.name += "_"+ndRvSave.label
                ndRvSave = None
            elif GetTypeOfNodeSave(ndRvSave.outputs[0])!=idSave: #Если это нод от другого типа сохранения.
                pos = ndRvSave.location.copy() #При смене типа сохранять позицию "активного" нода-сохранения. Заметка: Не забывать про .copy(), потому что далее нод удаляется.
                self.tree.nodes.remove(ndRvSave)
                ndRvSave = None
        if not ndRvSave:
            match idSave:
                case 0: txt = "MixRGB" #Потому что он может быть во всех редакторах; а ещё Shift+G > Type.
                case 1: txt = "AddShader"
                case 2: txt = "SeparateGeometry" #Нужен нод с минимальным влияем (нагрузкой) и поддерживающим все типы геометрии, (и без мультиинпутов).
            ndRvSave = self.tree.nodes.new(self.tree.bl_idname.replace("Tree","")+txt)
            ndRvSave.location = pos
        ndRvSave.name = voronoiPreviewResultNdName
        ndRvSave.select = False
        ndRvSave.label = ndRvSave.name
        ndRvSave.use_custom_color = True
        #Разукрасить нод сохранения
        match idSave:
            case 0:
                ndRvSave.color = SoldThemeCols.color_node3
                ndRvSave.show_options = False
                ndRvSave.blend_type = 'ADD'
                ndRvSave.inputs[0].default_value = 0
                ndRvSave.inputs[1].default_value = PowerArr4(SoldThemeCols.color_node4, pw=2.2)
                ndRvSave.inputs[2].default_value = ndRvSave.inputs[1].default_value #Немного лишнее.
                ndRvSave.inputs[0].hide = True
                ndRvSave.inputs[1].name = "Color"
                ndRvSave.inputs[2].hide = True
            case 1:
                ndRvSave.color = SoldThemeCols.shader_node3
                ndRvSave.inputs[1].hide = True
            case 2:
                ndRvSave.color = SoldThemeCols.geometry_node3
                ndRvSave.show_options = False
                ndRvSave.inputs[1].hide = True
                ndRvSave.outputs[0].name = "Geometry"
                ndRvSave.outputs[1].hide = True
        self.tree.links.new(finalLink.from_socket, ndRvSave.inputs[not idSave])
        self.tree.links.new(ndRvSave.outputs[0], finalLink.to_socket)

class VmtData(PieRootData):
    sk0 = None
    sk1 = None
    skType = ""
    isHideOptions = False
    isPlaceImmediately = False

class VoronoiMixerTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_mixer'
    bl_label = "Voronoi Mixer"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True) #Стоит первым, чтобы быть похожим на VQMT в kmi.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None #Нужно обнулять из-за наличия двух continue ниже.
        self.fotagoSk1 = None
        soldReroutesCanInAnyType = prefs.vmtReroutesCanInAnyType
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksOut = self.ToolGetNearestSockets(nd)[1]
            if not list_ftgSksOut:
                continue
            #В фильтре нод нет нужды.
            #Этот инструмент триггерится на любой выход (теперь кроме виртуальных) для первого.
            if isFirstActivation:
                self.fotagoSk0 = list_ftgSksOut[0] if list_ftgSksOut else None
            #Для второго по условиям:
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut:
                    skOut1 = ftg.tar
                    if skOut0==skOut1:
                        break
                    orV = (skOut1.bl_idname=='NodeSocketVirtual')or(skOut0.bl_idname=='NodeSocketVirtual')
                    #Теперь VMT к виртуальным снова может
                    tgl = (skOut1.bl_idname=='NodeSocketVirtual')^(skOut0.bl_idname=='NodeSocketVirtual')
                    tgl = (tgl)or( self.SkBetweenFieldsCheck(skOut0, skOut1)or( (skOut1.bl_idname==skOut0.bl_idname)and(not orV) ) )
                    tgl = (tgl)or( (skOut0.node.type=='REROUTE')or(skOut1.node.type=='REROUTE') )and(soldReroutesCanInAnyType)
                    if tgl:
                        self.fotagoSk1 = ftg
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                    self.fotagoSk1 = None
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            #Не смотря на то, что в фильтре нод нет нужды и и так прекрасно работает на первом попавшемся, всё равно нужно продолжать поиск, если первый сокет найден не был.
            #Потому что если первым(ближайшим) окажется нод с неудачным результатом поиска, цикл закончится и инструмент ничего не выберет, даже если рядом есть подходящий.
            if self.fotagoSk0: #Особенно заметно с активным ныне несуществующим isCanReOut; без этого результат будет выбираться успешно/неуспешно в зависимости от положения курсора.
                break
    def MatterPurposePoll(self):
        if not self.fotagoSk0:
            return False
        if self.isCanFromOne:
            return (self.fotagoSk0.blid!='NodeSocketVirtual')or(self.fotagoSk1)
        else:
            return self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        VmtData.sk0 = self.fotagoSk0.tar
        VmtData.sk1 = FtgGetTargetOrNone(self.fotagoSk1)
        #Поддержка виртуальных выключена; читается только из первого
        VmtData.skType = VmtData.sk0.type if VmtData.sk0.bl_idname!='NodeSocketVirtual' else VmtData.sk1.type
        VmtData.isHideOptions = self.isHideOptions
        VmtData.isPlaceImmediately = self.isPlaceImmediately
        SetPieData(self, VmtData, prefs, PowerArr4(GetSkColSafeTup4(VmtData.sk0), pw=2.2))
        if not self.isInvokeInClassicTree: #В связи с usefulnessForCustomTree, бесполезная проверка.
            return {'CANCELLED'} #Если место действия не в классических редакторах, то просто выйти. Ибо классические редакторы у всех одинаковые, а аддонских есть бесчисленное множество.
        tup_nodes = dict_vmtTupleMixerMain.get(tree.bl_idname, False).get(VmtData.skType, None)
        if tup_nodes:
            if length(tup_nodes)==1: #Если выбор всего один, то пропустить его и сразу переходить к смешиванию.
                DoMix(tree, False, False, tup_nodes[0]) #При моментальной активации можно и не отпустить модификаторы. Поэтому DoMix() получает не event, а вручную.
            else: #Иначе предоставить выбор
                bpy.ops.wm.call_menu_pie(name=VmtPieMixer.bl_idname)
        else: #Иначе для типа сокета не определено (например шейдер в геонодах).
            DisplayMessage(self.bl_label, txt_vmtNoMixingOptions, icon='RADIOBUT_OFF')
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vmtReroutesCanInAnyType')
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Pie")+f" ({cls.vlTripleName})")
        tlw = cls.vlTripleName.lower()
        LyAddHandSplitProp(colBox, prefs,f'{tlw}PieType')
        colProps = colBox.column(align=True)
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieScale')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieAlignment')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieSocketDisplayType')
        LyAddHandSplitProp(colProps, prefs,f'{tlw}PieDisplaySocketColor')
        colProps.active = getattr(prefs,f'{tlw}PieType')=='CONTROL'
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isCanFromOne').name) as dm:
            dm[ru_RU] = "Может от одного сокета"
            dm[zh_CN] = "从一个端口连接"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPlaceImmediately').name) as dm:
            dm[ru_RU] = "Размещать моментально"
            dm[zh_CN] = "立即添加节点到鼠标位置"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vmtReroutesCanInAnyType').name) as dm:
            dm[ru_RU] = "Рероуты могут смешиваться с любым типом"
            dm[zh_CN] = "快速混合不限定端口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType').name) as dm:
            dm[ru_RU] = "Тип пирога"
            dm[zh_CN] = "饼菜单类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType',0).name) as dm:
            dm[ru_RU] = "Контроль"
            dm[zh_CN] = "控制(自定义)"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieType',1).name) as dm:
            dm[ru_RU] = "Скорость"
            dm[zh_CN] = "速度型(多层菜单)"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieScale').name) as dm:
            dm[ru_RU] = "Размер пирога"
            dm[zh_CN] = "饼菜单大小"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').name) as dm:
            dm[ru_RU] = "Выравнивание между элементами"
#            dm[zh_CN] = "元素对齐方式"?
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieAlignment').description) as dm:
            dm[ru_RU] = "0 – Гладко.\n1 – Скруглённые состыкованные.\n2 – Зазор"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').name) as dm:
            dm[ru_RU] = "Отображение типа сокета"
            dm[zh_CN] = "显示端口类型"
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieSocketDisplayType').description) as dm:
            dm[ru_RU] = "0 – Выключено.\n1 – Сверху.\n-1 – Снизу (VMT)"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').name) as dm:
            dm[ru_RU] = "Отображение цвета сокета"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vmtPieDisplaySocketColor').description) as dm:
            dm[ru_RU] = "Знак – сторона цвета. Значение – ширина цвета"
#            dm[zh_CN] = ""

SmartAddToRegAndAddToKmiDefs(VoronoiMixerTool, "S#A_LEFTMOUSE") #Миксер перенесён на левую, чтобы освободить нагрузку для VQMT.
dict_setKmiCats['grt'].add(VoronoiMixerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vmtReroutesCanInAnyType: bpy.props.BoolProperty(name="Reroutes can be mixed to any type", default=True)
    ##
    vmtPieType:               bpy.props.EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vmtPieScale:              bpy.props.FloatProperty(name="Pie scale",                default=1.5, min=1.0, max=2.0, subtype="FACTOR")
    vmtPieAlignment:          bpy.props.IntProperty(  name="Alignment between items",  default=1,   min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vmtPieSocketDisplayType:  bpy.props.IntProperty(  name="Display socket type info", default=1,   min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vmtPieDisplaySocketColor: bpy.props.IntProperty(  name="Display socket color",     default=-1,  min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")

with VlTrMapForKey(VoronoiMixerTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速混合"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiMixerTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiMixerTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiMixerTool.bl_label}快速混合设置:"

dict_toolLangSpecifDataPool[VoronoiMixerTool, ru_RU] = "Канонический инструмент для частых нужд смешивания.\nСкорее всего 70% уйдёт на использование \"Instance on Points\"."

vmtSep = 'MixerItemsSeparator123'
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
dict_vmtMixerNodesDefs = { #'-1' означают визуальную здесь метку, что их сокеты подключения высчитываются автоматически (см. |2|), а не указаны явно в этом списке
        #Отсортировано по количеству в "базе данных" выше.
        'GeometryNodeSwitch':             (-1, -1, "Switch  "),
        'ShaderNodeMix':                  (-1, -1, "Mix  "),
        'FunctionNodeCompare':            (-1, -1, "Compare  "),
        'ShaderNodeMath':                 (0, 1, "Max Float "),
        'ShaderNodeMixRGB':               (1, 2, "Mix RGB "),
        'CompositorNodeMixRGB':           (1, 2, "Mix Col "),
        'CompositorNodeSwitch':           (0, 1, "Switch "),
        'CompositorNodeSplitViewer':      (0, 1, "Split Viewer "),
        'CompositorNodeSwitchView':       (0, 1, "Switch View "),
        'TextureNodeMixRGB':              (1, 2, "Mix Col "),
        'TextureNodeTexture':             (0, 1, "Texture "),
        'ShaderNodeVectorMath':           (0, 1, "Max Vector "),
        'CompositorNodeMath':             (0, 1, "Max Float "),
        'TextureNodeMath':                (0, 1, "Max Float "),
        'ShaderNodeMixShader':            (1, 2, "Mix Shader "),
        'ShaderNodeAddShader':            (0, 1, "Add Shader "),
        'GeometryNodeStringJoin':         (1, 1, "Join String "),
        'FunctionNodeBooleanMath':        (0, 1, "Or "),
        'CompositorNodeAlphaOver':        (1, 2, "Alpha Over "),
        'TextureNodeDistance':            (0, 1, "Distance "),
        'GeometryNodeJoinGeometry':       (0, 0, "Join "),
        'GeometryNodeInstanceOnPoints':   (0, 2, "Instance on Points "),
        'GeometryNodeCurveToMesh':        (0, 1, "Curve to Mesh "),
        'GeometryNodeMeshBoolean':        (0, 1, "Boolean "),
        'GeometryNodeGeometryToInstance': (0, 0, "To Instance ")}
with VlTrMapForKey("Switch  ") as dm:
    dm[ru_RU] = "Переключение"
with VlTrMapForKey("Mix  ") as dm:
    dm[ru_RU] = "Смешивание"
with VlTrMapForKey("Compare  ") as dm:
    dm[ru_RU] = "Сравнение"

def DoMix(tree, isShift, isAlt, type):
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=type, use_transform=not VmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    aNd.width = 140
    txtFix = {'VALUE':'FLOAT'}.get(VmtData.skType, VmtData.skType)
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
        case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix': #|2|.
            tgl = aNd.bl_idname!='FunctionNodeCompare'
            txtFix = VmtData.skType
            match aNd.bl_idname:
                case 'FunctionNodeCompare': txtFix = {'BOOLEAN':'INT'}.get(txtFix, txtFix)
                case 'ShaderNodeMix':       txtFix = {'INT':'VALUE', 'BOOLEAN':'VALUE'}.get(txtFix, txtFix)
            #Для микса и переключателя искать с конца, потому что их сокеты для переключения имеют тип некоторых искомых. У нода сравнения всё наоборот.
            list_foundSk = [sk for sk in ( reversed(aNd.inputs) if tgl else aNd.inputs ) if sk.type==txtFix]
            NewLinkHhAndRemember(VmtData.sk0, list_foundSk[tgl^isShift]) #Из-за направления поиска, нужно выбирать их из списка также с учётом направления.
            if VmtData.sk1:
                NewLinkHhAndRemember(VmtData.sk1, list_foundSk[(not tgl)^isShift])
        case _:
            #Такая плотная суета ради мультиинпута -- для него нужно изменить порядок подключения.
            if (VmtData.sk1)and(aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][0]].is_multi_input): #`0` здесь в основном из-за того, что в dict_vmtMixerNodesDefs у "нодов-мультиинпутов" всё по нулям.
                NewLinkHhAndRemember( VmtData.sk1, aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][1^isShift]] )
            DoLinkHh( VmtData.sk0, aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][0^isShift]] ) #Заметка: Это не NewLinkHhAndRemember(), чтобы визуальный второй мультиинпута был последним в VlrtData.
            if (VmtData.sk1)and(not aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][0]].is_multi_input):
                NewLinkHhAndRemember( VmtData.sk1, aNd.inputs[dict_vmtMixerNodesDefs[aNd.bl_idname][1^isShift]] )
    aNd.show_options = not VmtData.isHideOptions
    #Далее так же, как и в vqmt. У него первично; здесь дублировано для интуитивного соответствия.
    if isAlt:
        for sk in aNd.inputs:
            sk.hide = True

class VmtOpMixer(VoronoiOpTool):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = "Mixer Mixer"
    operation: bpy.props.StringProperty()
    def invoke(self, context, event):
        DoMix(context.space_data.edit_tree, event.shift, event.alt, self.operation)
        return {'FINISHED'}
class VmtPieMixer(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_mixer_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, context):
        def LyVmAddOp(where, txt):
            where.operator(VmtOpMixer.bl_idname, text=TranslateIface(dict_vmtMixerNodesDefs[txt][2])).operation = txt
        def LyVmAddItem(where, txt):
            ly = where.row(align=VmtData.pieAlignment==0)
            soldPdsc = VmtData.pieDisplaySocketColor
            if soldPdsc:
                ly = ly.split(factor=( abs( (soldPdsc>0)-.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VmtData.uiScale, align=True)
            if soldPdsc<0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
            LyVmAddOp(ly, txt)
            if soldPdsc>0:
                ly.prop(VmtData.prefs,'vaDecorColSk', text="")
        pie = self.layout.menu_pie()
        editorBlid = context.space_data.tree_type
        tup_nodes = dict_vmtTupleMixerMain[editorBlid][VmtData.skType]
        if VmtData.isSpeedPie:
            for ti in tup_nodes:
                if ti!=vmtSep:
                    LyVmAddOp(pie, ti)
        else:
            #Если при выполнении колонка окажется пустой, то в ней будет отображаться только пустая точка-коробка. Два списка ниже нужны, чтобы починить это.
            list_cols = [pie.row(), pie.row(), pie.row() if VmtData.pieDisplaySocketTypeInfo>0 else None]
            list_done = [False, False, False]
            def LyGetPieCol(inx):
                if list_done[inx]:
                    return list_cols[inx]
                box = list_cols[inx].box()
                col = box.column(align=VmtData.pieAlignment<2)
                col.ui_units_x = 6*((VmtData.pieScale-1)/2+1)
                col.scale_y = VmtData.pieScale
                list_cols[inx] = col
                list_done[inx] = True
                return col
            match editorBlid:
                case 'ShaderNodeTree':
                    row2 = LyGetPieCol(0).row(align=VmtData.pieAlignment==0)
                    row2.enabled = False
                    LyVmAddItem(row2, 'ShaderNodeMix')
                case 'GeometryNodeTree':
                    col = LyGetPieCol(0)
                    row1 = col.row(align=VmtData.pieAlignment==0)
                    row2 = col.row(align=VmtData.pieAlignment==0)
                    row3 = col.row(align=VmtData.pieAlignment==0)
                    row1.enabled = False
                    row2.enabled = False
                    row3.enabled = False
                    LyVmAddItem(row1, 'GeometryNodeSwitch')
                    LyVmAddItem(row2, 'ShaderNodeMix')
                    LyVmAddItem(row3, 'FunctionNodeCompare')
            sco = 0
            for ti in tup_nodes:
                match ti:
                    case 'GeometryNodeSwitch':  row1.enabled = True
                    case 'ShaderNodeMix':       row2.enabled = True
                    case 'FunctionNodeCompare': row3.enabled = True
                    case _:
                        col = LyGetPieCol(1)
                        if ti==vmtSep:
                            if sco:
                                col.separator()
                        else:
                            LyVmAddItem(col, ti)
                            sco += 1
            if VmtData.pieDisplaySocketTypeInfo:
                box = pie.box()
                row = box.row(align=True)
                row.template_node_socket(color=GetSkColorRaw(VmtData.sk0))
                row.label(text=VmtData.sk0.bl_label)

list_classes += [VmtOpMixer, VmtPieMixer]

class VqmtData(PieRootData):
    list_speedPieDisplayItems = []
    sk0 = None
    sk1 = None
    depth = 0
    qmSkType = ''
    qmTrueSkType = ''
    isHideOptions = False
    isPlaceImmediately = False
    isJustPie = False #Без нужды.
    canProcHideSks = True
    dict_lastOperation = {}
    isFirstDone = False #https://github.com/ugorek000/VoronoiLinker/issues/20
    list_existingValues = []

set_vqmtSkTypeFields = {'VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN', 'ROTATION'}

fitVqmtRloDescr = "Bypassing the pie call, activates the last used operation for the selected socket type.\n"+\
                  "Searches for sockets only from an available previous operations that were performed for the socket type.\n"+\
                  "Just a pie call, and the fast fast math is not remembered as the last operations"
class VoronoiQuickMathTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_math'
    bl_label = "Voronoi Quick Math"
    usefulnessForCustomTree = False
    canDrawInAppearance = True
    quickOprFloat:  bpy.props.StringProperty(name="Float (quick)",  default="") #Они в начале, чтобы в kmi отображалось выровненным.
    quickOprVector: bpy.props.StringProperty(name="Vector (quick)", default="") #quick вторым, чтобы при нехватке места отображалось первое слово, от чего пришлось заключить в скобки.
    isCanFromOne:       bpy.props.BoolProperty(name="Can from one socket", default=True)
    isRepeatLastOperation: bpy.props.BoolProperty(name="Repeat last operation", default=False, description=fitVqmtRloDescr) #Что ж, квартет qqm теперь вынуждает их постоянно выравнивать.
    isHideOptions:      bpy.props.BoolProperty(name="Hide node options",   default=False)
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately",   default=False)
    quickOprBool:   bpy.props.StringProperty(name="Bool (quick)",   default="")
    quickOprColor:  bpy.props.StringProperty(name="Color (quick)",  default="")
    justPieCall:           bpy.props.IntProperty(name="Just call pie", default=0, min=0, max=4, description="Call pie to add a node, bypassing the sockets selection.\n0 – Disable.\n1 – Float.\n2 – Vector.\n3 – Boolean.\n4 – Color")
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        isNotCanPickThird = not self.canPickThird if prefs.vqmtIncludeThirdSk else True
        if isNotCanPickThird:
            self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            if not list_ftgSksOut:
                continue
            #Этот инструмент триггерится только на выходы поля.
            if isFirstActivation:
                isSucessOut = False
                for ftg in list_ftgSksOut:
                    if not self.isRepeatLastOperation:
                        if not self.isQuickQuickMath:
                            if ftg.tar.type in set_vqmtSkTypeFields:
                                self.fotagoSk0 = ftg
                                isSucessOut = True
                                break
                        else: #Для isQuickQuickMath цепляться только к типам сокетов от явно указанных операций.
                            match ftg.tar.type:
                                case 'VALUE'|'INT':     isSucessOut = self.quickOprFloat
                                case 'VECTOR':          isSucessOut = self.quickOprVector
                                case 'BOOLEAN':         isSucessOut = self.quickOprBool
                                case 'RGBA'|'ROTATION': isSucessOut = self.quickOprColor
                            if isSucessOut:
                                self.fotagoSk0 = ftg
                                break
                    else:
                        isSucessOut = VqmtData.dict_lastOperation.get(ftg.tar.type, '')
                        if isSucessOut:
                            self.fotagoSk0 = ftg
                            break
                if not isSucessOut:
                    continue #Искать нод для isFirstActivation'а, у которого попадёт на сокет поля.
                #Для следующего `continue`, ибо если далее будет неудача с последующей активацией continue, то произойдёт перевыбор isFirstActivation
                isFirstActivation = False #Но в связи с текущей топологией выбора, это без нужды.
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk0, flag=True) #todo0NA см. строчку выше, этот 'cond' должен быть не от isFirstActivation.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if isNotCanPickThird:
                #Для второго по условиям:
                if skOut0:
                    for ftg in list_ftgSksOut:
                        if self.SkBetweenFieldsCheck(skOut0, ftg.tar):
                            self.fotagoSk1 = ftg
                            break
                    if not self.fotagoSk1:
                        continue #Чтобы ноды без сокетов полей были прозрачными.
                    if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                        self.fotagoSk1 = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            else:
                self.fotagoSk2 = None #Обнулять для удобства высокоуровневой отмены.
                #Для третьего, если не ноды двух предыдущих.
                skOut1 = FtgGetTargetOrNone(self.fotagoSk1)
                for ftg in list_ftgSksIn:
                    skIn = ftg.tar
                    if skIn.type in set_vqmtSkTypeFields:
                        tgl0 = (not skOut0)or(skOut0.node!=skIn.node)
                        tgl1 = (not skOut1)or(skOut1.node!=skIn.node)
                        if (tgl0)and(tgl1):
                            self.fotagoSk2 = ftg
                            break
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
            break
    def VqmSetPieData(self, prefs, col):
        SetPieData(self, VqmtData, prefs, col)
        VqmtData.isHideOptions = self.isHideOptions
        VqmtData.isPlaceImmediately = self.isPlaceImmediately
        VqmtData.depth = 0
        VqmtData.isFirstDone = False
    def ModalMouseNext(self, event, prefs): #Копия-алерт, у VLT такое же.
        if event.type==prefs.vqmtRepickKey:
            self.repickState = event.value=='PRESS'
            if self.repickState:
                self.NextAssignmentRoot(True)
                self.canPickThird = False #В целом хреновая идея добавить возможность перевыбора для инструмента, у которого есть третий сокет; управление инструментом стало сложно-контролируемее.
        else:
            match event.type:
                case 'MOUSEMOVE':
                    if self.repickState:
                        self.NextAssignmentRoot(True)
                    else:
                        self.NextAssignmentRoot(False)
                case self.kmi.type|'ESC':
                    return True
        return False
    def MatterPurposePoll(self):
        return (self.fotagoSk0)and(self.isCanFromOne or self.fotagoSk1)
    def MatterPurposeTool(self, event, prefs, tree):
        VqmtData.sk0 = self.fotagoSk0.tar
        VqmtData.sk1 = FtgGetTargetOrNone(self.fotagoSk1)
        VqmtData.sk2 = FtgGetTargetOrNone(self.fotagoSk2)
        VqmtData.qmSkType = VqmtData.sk0.type #Заметка: Наличие только сокетов поля -- забота на уровень выше.
        VqmtData.qmTrueSkType = VqmtData.qmSkType #Эта информация нужна для "последней операции".
        match VqmtData.sk0.type:
            case 'INT':      VqmtData.qmSkType = 'VALUE' #И только целочисленный обделён своим нодом математики. Может его добавят когда-нибудь?.
            case 'ROTATION': VqmtData.qmSkType = 'RGBA' #Больше шансов, что для математика для кватерниона будет первее.
            #case 'ROTATION': return {'FINISHED'} #Однако странно, почему с RGBA линки отмечаются некорректными, ведь оба Arr4... Зачем тогда цвету альфа?
        match tree.bl_idname:
            case 'ShaderNodeTree':     VqmtData.qmSkType = {'BOOLEAN':'VALUE'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
            case 'GeometryNodeTree':   pass
            case 'CompositorNodeTree': VqmtData.qmSkType = {'BOOLEAN':'VALUE', 'VECTOR':'RGBA'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
            case 'TextureNodeTree':    VqmtData.qmSkType = {'BOOLEAN':'VALUE', 'VECTOR':'RGBA'}.get(VqmtData.qmSkType, VqmtData.qmSkType)
        if self.isRepeatLastOperation:
            return DoQuickMath(event, tree, VqmtData.dict_lastOperation[VqmtData.qmTrueSkType])
        if self.isQuickQuickMath:
            match VqmtData.qmSkType:
                case 'VALUE':   opr = self.quickOprFloat
                case 'VECTOR':  opr = self.quickOprVector
                case 'BOOLEAN': opr = self.quickOprBool
                case 'RGBA':    opr = self.quickOprColor
            return DoQuickMath(event, tree, opr)
        self.VqmSetPieData(prefs, PowerArr4(GetSkColSafeTup4(VqmtData.sk0), pw=2.2))
        VqmtData.isJustPie = False
        VqmtData.canProcHideSks = True
        bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
    def InitTool(self, event, prefs, tree):
        self.repickState = False
        VqmtData.canProcHideSks = False #Сразу для двух DoQuickMath выше и оператора ниже.
        if self.justPieCall:
            match tree.bl_idname:
                case 'ShaderNodeTree': can = self.justPieCall in {1,2,4}
                case 'GeometryNodeTree': can = True
                case 'CompositorNodeTree'|'TextureNodeTree': can = self.justPieCall in {1,4}
            if not can:
                DisplayMessage(self.bl_label, txt_vqmtThereIsNothing)
                return {'CANCELLED'}
            VqmtData.sk0 = None #Обнулять для полноты картины и для GetSkCol.
            VqmtData.sk1 = None
            VqmtData.sk2 = None
            VqmtData.qmSkType = ('VALUE','VECTOR','BOOLEAN','RGBA')[self.justPieCall-1]
            self.VqmSetPieData(prefs, dict_skTypeHandSolderingColor[VqmtData.qmSkType])
            VqmtData.isJustPie = True
            bpy.ops.node.voronoi_quick_math_main('INVOKE_DEFAULT')
            return {'FINISHED'}
        self.isQuickQuickMath = not not( (self.quickOprFloat)or(self.quickOprVector)or(self.quickOprBool)or(self.quickOprColor) )
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vqmtIncludeThirdSk')
        tgl = prefs.vqmtPieType=='CONTROL'
        LyAddLeftProp(col, prefs,'vqmtIncludeQuickPresets', active=tgl)
        LyAddLeftProp(col, prefs,'vqmtIncludeExistingValues', active=tgl)
        LyAddKeyTxtProp(col, prefs,'vqmtRepickKey')
    @classmethod
    def LyDrawInAppearance(cls, colLy, prefs):
        #VoronoiMixerTool.__dict__['LyDrawInAppearance'].__func__(cls, colLy, prefs) #Чума. Обход из-за @classmethod. Но теперь без нужды, потому что появился vqmtPieScaleExtra.
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Pie")+" (VQMT)")
        LyAddHandSplitProp(colBox, prefs,'vqmtPieType')
        colProps = colBox.column(align=True)
        LyAddHandSplitProp(colProps, prefs,'vqmtPieScale')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieScaleExtra')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieAlignment')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieSocketDisplayType')
        LyAddHandSplitProp(colProps, prefs,'vqmtPieDisplaySocketColor')
        colProps.active = getattr(prefs,'vqmtPieType')=='CONTROL'
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isHideOptions').name) as dm:
            dm[ru_RU] = "Скрывать опции нода"
            dm[zh_CN] = "隐藏节点选项"
        #* Перевод isPlaceImmediately уже есть в VMT *
        with VlTrMapForKey(GetAnnotFromCls(cls,'justPieCall').name) as dm:
            dm[ru_RU] = "Просто вызвать пирог"
            dm[zh_CN] = "仅调用饼图"
        with VlTrMapForKey(GetAnnotFromCls(cls,'justPieCall').description) as dm:
            dm[ru_RU] = "Вызвать пирог для добавления нода, минуя выбор сокетов.\n0 – Выключено.\n1 – Float.\n2 – Vector.\n3 – Boolean.\n4 – Color"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isRepeatLastOperation').name) as dm:
            dm[ru_RU] = "Повторить последнюю операцию"
            dm[zh_CN] = "重复上一操作"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isRepeatLastOperation').description) as dm:
            dm[ru_RU] = "Минуя вызов пирога, активирует последнюю использованную операцию для выбранного типа сокета.\n"+\
                        "Ищет сокеты только из доступных предыдущих операций, которые были свершены для типа сокета.\n"+\
                        "Просто вызов пирога и быстрая быстрая математика, не запоминаются как последние операции"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprFloat').name) as dm:
            dm[ru_RU] = "Скаляр (быстро)"
            dm[zh_CN] = "浮点（快速）"
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprVector').name) as dm:
            dm[ru_RU] = "Вектор (быстро)"
            dm[zh_CN] = "矢量（快速）"
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprBool').name) as dm:
            dm[ru_RU] = "Логический (быстро)"
            dm[zh_CN] = "布尔（快速）"
        with VlTrMapForKey(GetAnnotFromCls(cls,'quickOprColor').name) as dm:
            dm[ru_RU] = "Цвет (быстро)"
            dm[zh_CN] = "颜色（快速）"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vqmtIncludeThirdSk').name) as dm:
            dm[ru_RU] = "Разрешить третий сокет"
            dm[zh_CN] = "包括第三个端口"
        with VlTrMapForKey(GetPrefsRnaProp('vqmtIncludeQuickPresets').name) as dm:
            dm[ru_RU] = "Включить быстрые пресеты"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vqmtIncludeExistingValues').name) as dm:
            dm[ru_RU] = "Включить существующие значения"
#            dm[zh_CN] = ""
        #См. перевод vqmtRepickKey в VLT.
        #Переводы vqmtPie такие же, как и в VMT.

SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_RIGHTMOUSE") #Осталось на правой, чтобы не охреневать от тройного клика левой при 'Speed Pie' типе пирога.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_ACCENT_GRAVE", {'isRepeatLastOperation':True})
#Список быстрых операций для быстрой математики ("x2 комбо"):
#Дилемма с логическим на "3", там может быть вычитание, как все на этой клавише, или отрицание, как логическое продолжение первых двух. Во втором случае булеан на 4 скорее всего придётся делать никаким.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_1", {'quickOprFloat':'ADD',      'quickOprVector':'ADD',      'quickOprBool':'OR',     'quickOprColor':'ADD'     })
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_2", {'quickOprFloat':'SUBTRACT', 'quickOprVector':'SUBTRACT', 'quickOprBool':'NIMPLY', 'quickOprColor':'SUBTRACT'})
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_3", {'quickOprFloat':'MULTIPLY', 'quickOprVector':'MULTIPLY', 'quickOprBool':'AND',    'quickOprColor':'MULTIPLY'})
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "##A_4", {'quickOprFloat':'DIVIDE',   'quickOprVector':'DIVIDE',   'quickOprBool':'NOT',    'quickOprColor':'DIVIDE'  })
#Хотел я реализовать это для QuickMathMain, но оказалось слишком лажа превращать технический оператор в пользовательский. Основная проблема -- VqmtData настроек пирога.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_1", {'justPieCall':1}) #Неожиданно, но такой хоткей весьма приятный в использовании.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_2", {'justPieCall':2}) # Из-за наличия двух модификаторов приходится держать нажатым,
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_3", {'justPieCall':3}) # от чего приходится выбирать позицией курсора, а не кликом.
SmartAddToRegAndAddToKmiDefs(VoronoiQuickMathTool, "S#A_4", {'justPieCall':4}) # Я думал это будет неудобно, а оказалось даже приятно.
dict_setKmiCats['grt'].add(VoronoiQuickMathTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vqmtIncludeThirdSk:        bpy.props.BoolProperty(name="Include third socket", default=True)
    vqmtIncludeQuickPresets:   bpy.props.BoolProperty(name="Include quick presets", default=True)
    vqmtIncludeExistingValues: bpy.props.BoolProperty(name="Include existing values", default=True)
    vqmtRepickKey: bpy.props.StringProperty(name="Repick Key", default='LEFT_ALT')
    ##
    vqmtPieType:               bpy.props.EnumProperty( name="Pie Type", default='CONTROL', items=( ('CONTROL',"Control",""), ('SPEED',"Speed","") ))
    vqmtPieScale:              bpy.props.FloatProperty(name="Pie scale",                default=1.5,  min=1.0, max=2.0, subtype="FACTOR")
    vqmtPieScaleExtra:         bpy.props.FloatProperty(name="Pie scale extra",          default=1.25, min=1.0, max=2.0, subtype="FACTOR")
    vqmtPieAlignment:          bpy.props.IntProperty(  name="Alignment between items",  default=1,    min=0,   max=2, description="0 – Flat.\n1 – Rounded docked.\n2 – Gap")
    vqmtPieSocketDisplayType:  bpy.props.IntProperty(  name="Display socket type info", default=1,    min=-1,  max=1, description="0 – Disable.\n1 – From above.\n-1 – From below (VMT)")
    vqmtPieDisplaySocketColor: bpy.props.IntProperty(  name="Display socket color",     default=-1,   min=-4,  max=4, description="The sign is side of a color. The magnitude is width of a color")

with VlTrMapForKey(VoronoiQuickMathTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速数学运算"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiQuickMathTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiQuickMathTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiQuickMathTool.bl_label}快速数学运算设置:"

dict_toolLangSpecifDataPool[VoronoiQuickMathTool, ru_RU] = """Полноценное ответвление от VMT. Быстрая и быстрая быстрая математика на спидах.
Имеет дополнительный мини-функционал. Также см. \"Quick quick math\" в раскладе."""

#Быстрая математика.
#Заполучить нод с нужной операцией и автоматическим соединением в сокеты, благодаря мощностям VL'а.
#Неожиданно для меня оказалось, что пирог может рисовать обычный layout. От чего добавил дополнительный тип пирога "для контроля".
#А также сам буду пользоваться им, потому что за то время, которое экономится при двойном пироге, отдохнуть как-то всё равно не получается.

#Важная эстетическая ценность двойного пирога -- визуальная неперегруженность вариантами. Вместо того, чтобы вываливать всё сразу, показываются только по 8 штук за раз.

#todo00 с приходом популярности, посмотреть кто использует быстрый пирог, а потом аннигилировать его за ненадобностью; настолько распинаться о нём было бессмысленно. Мб опрос(голосование) сделать на BA.
#Заметка для меня: сохранять поддержку двойного пирога чёрт возьми, ибо эстетика. Но выпилить его с каждым разом хочется всё больше D:

#Было бы бездумно разбросать их как попало, поэтому я пытался соблюсти некоторую логическую последовательность. Например, расставляя пары по смыслу диаметрально противоположными.
#Пирог Блендера располагает в себе элементы следующим образом: лево, право, низ, верх, после чего классическое построчное заполнение.
#"Compatible..." -- чтобы у векторов и у математики одинаковые операции были на одинаковых местах (кроме тригонометрических).
#За исключением примитивов, где прослеживается супер очевидная логика (право -- плюс -- add, лево -- минус -- sub; всё как на числовой оси), лево и низ у меня более простые, чем обратная сторона.
#Например, length проще, чем distance. Всем же остальным не очевидным и не осе-ориентированным досталось как получится.

tup_vqmtQuickMathMapValue = (
        ("Advanced ",              ('SQRT',       'POWER',        'EXPONENT',   'LOGARITHM',   'INVERSE_SQRT','PINGPONG',    'FLOORED_MODULO' )),
        ("Compatible Primitives ", ('SUBTRACT',   'ADD',          'DIVIDE'   ,  'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ("Rounding ",              ('SMOOTH_MIN', 'SMOOTH_MAX',   'LESS_THAN',  'GREATER_THAN','SIGN',        'COMPARE',     'TRUNC',  'ROUND')),
        ("Compatible Vector ",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACT',       'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ("", ()), #Важны дубликаты и порядок, поэтому не словарь а список.
        ("", ()),
        ("Other ",                 ('COSH',       'RADIANS',      'DEGREES',    'SINH',        'TANH'                                         )),
        ("Trigonometric ",         ('SINE',       'COSINE',       'TANGENT',    'ARCTANGENT',  'ARCSINE',     'ARCCOSINE',   'ARCTAN2'        )) )
tup_vqmtQuickMathMapVector = (
        ("Advanced ",              ('SCALE',      'NORMALIZE',    'LENGTH',     'DISTANCE',    'SINE',        'COSINE',      'TANGENT'        )),
        ("Compatible Primitives ", ('SUBTRACT',   'ADD',          'DIVIDE',     'MULTIPLY',    'ABSOLUTE',    'MULTIPLY_ADD'                  )),
        ("Rays ",                  ('DOT_PRODUCT','CROSS_PRODUCT','PROJECT',    'FACEFORWARD', 'REFRACT',     'REFLECT'                       )),
        ("Compatible Vector ",     ('MINIMUM',    'MAXIMUM',      'FLOOR',      'FRACTION',    'CEIL',        'MODULO',      'SNAP',   'WRAP' )),
        ("", ()),
        ("", ()),
        ("", ()),
        ("", ()) )
tup_vqmtQuickMathMapBoolean = (
        ("High ",  ('NOR','NAND','XNOR','XOR','IMPLY','NIMPLY')),
        ("Basic ", ('OR', 'AND', 'NOT'                        )) )
tup_vqmtQuickModeMapColor = (
        #Для операции 'MIX' используйте VMT.
        ("Math ", ('SUBTRACT','ADD',       'DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION'                    )), #'EXCLUSION' не влез в "Art"; и было бы неплохо узнать его предназначение.
        ("Art ",  ('DARKEN',  'LIGHTEN','   DODGE', 'SCREEN',  'SOFT_LIGHT','LINEAR_LIGHT','BURN','OVERLAY')),
        ("Raw ",  ('VALUE',   'SATURATION','HUE',   'COLOR'                                                )) ) #Хотел переназвать на "Overwrite", но передумал.
dict_vqmtQuickMathMain = {
        'VALUE':   tup_vqmtQuickMathMapValue,
        'VECTOR':  tup_vqmtQuickMathMapVector,
        'BOOLEAN': tup_vqmtQuickMathMapBoolean,
        'RGBA':    tup_vqmtQuickModeMapColor}
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
                  'ARCTAN2': (pi, pi, pi)},
        'VECTOR': {'MULTIPLY':     ( (1,1,1), (1,1,1), (1,1,1), 1.0 ),
                   'DIVIDE':       ( (1,1,1), (1,1,1), (1,1,1), 1.0 ),
                   'CROSS_PRODUCT':( (0,0,1), (0,0,1), (0,0,1), 1.0 ),
                   'SCALE':        ( (0,0,0), (0,0,0), (0,0,0), pi )},
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
                 'COLOR':     ( (1,1,1,1), (1,0,0,1) )} }
dict_vqmtDefaultDefault = { #Можно было оставить без изменений, но всё равно обнуляю. Ради чего был создан VQMT?.
        #Заметка: Основано на типе нода, а не на типе сокета. Повезло, что они одинаковые.
        'VALUE': (0.0, 0.0, 0.0),
        'VECTOR': ((0,0,0), (0,0,0), (0,0,0), 0.0),
        'BOOLEAN': (False, False),
        'RGBA': ( (.25,.25,.25,1), (.5,.5,.5,1) ) }
dict_vqmtQuickPresets = {
        'VALUE': {"ADD|x|x": "x + x",
                  "MULTIPLY|x|x": "x * x",
                  "SUBTRACT|0|x": "-x", #"x * -1"
                  "DIVIDE|1|x": "1 / x",
                  "SUBTRACT|1|x": "1 - x",
                  #"ADD|x|0.5": "x + 0.5",
                  #"SUBTRACT|x|0.5": "x - 0.5",
                  "ADD|x|6.283185307179586": "x + tau",
                  "ADD|x|3.141592653589793": "x + pi",
                  "ADD|x|1.5707963267948966": "x + pi/2"},
        'VECTOR': {"ADD|x|x": "x + x",
                   "MULTIPLY|x|x": "x * x",
                   "SUBTRACT|0,0,0|x": "-x", #"x * -1"
                   "DIVIDE|1,1,1|x": "1 / x",
                   "SUBTRACT|x|0.5,0.5,0": "x - (0.5, 0.5)",
                   "ADD|x|pi*2,pi*2,pi*2": "x + tau",
                   "ADD|x|pi,pi,pi": "x + pi",
                   "ADD|x|pi/2,pi/2,pi/2": "x + pi/2"} }

def DoQuickMath(event, tree, operation, isCombo=False):
    txt = dict_vqmtEditorNodes[VqmtData.qmSkType].get(tree.bl_idname, "")
    if not txt: #Если нет в списке, то этот нод не существует (по задумке списка) в этом типе редактора => "смешивать" нечем, поэтому выходим.
        return {'CANCELLED'}
    #Ядро быстрой математики, добавить нод и создать линки:
    bpy.ops.node.add_node('INVOKE_DEFAULT', type=txt, use_transform=not VqmtData.isPlaceImmediately)
    aNd = tree.nodes.active
    preset = operation.split("|")
    isPreset = length(preset)>1
    if isPreset:
        operation = preset[0]
    if VqmtData.qmSkType!='RGBA': #Ох уж этот цвет.
        aNd.operation = operation
    else:
        if aNd.bl_idname=='ShaderNodeMix':
            aNd.data_type = 'RGBA'
            aNd.clamp_factor = False
        aNd.blend_type = operation
        aNd.inputs[0].default_value = 1.0
        aNd.inputs[0].hide = operation in {'ADD','SUBTRACT','DIVIDE','MULTIPLY','DIFFERENCE','EXCLUSION','VALUE','SATURATION','HUE','COLOR'}
    ##
    if not isPreset:
        #Теперь существует justPieCall, а значит пришло время скрывать значение первого сокета (но нужда в этом только для вектора).
        if VqmtData.qmSkType=='VECTOR':
            aNd.inputs[0].hide_value = True
        #Идея с event.shift гениальна. Изначально ради одиночного линка во второй сокет, но благодаря визуальному поиску ниже, может и менять местами и два линка.
        bl4ofs = 2*viaverIsBlender4*(tree.bl_idname in {'ShaderNodeTree','GeometryNodeTree'})
        skInx = aNd.inputs[0] if VqmtData.qmSkType!='RGBA' else aNd.inputs[-2-bl4ofs] #"Inx", потому что пародия на int "index", но потом понял, что можно сразу в сокет для линковки далее.
        if event.shift:
            for sk in aNd.inputs:
                if (sk!=skInx)and(sk.enabled):
                    if sk.type==skInx.type:
                        skInx = sk
                        break
        if VqmtData.sk0:
            NewLinkHhAndRemember(VqmtData.sk0, skInx)
            if VqmtData.sk1:
                #Второй ищется "визуально"; сделано ради операции 'SCALE'.
                for sk in aNd.inputs: #Ищется сверху вниз. Потому что ещё и 'MulAdd'.
                    if (sk.enabled)and(not sk.is_linked): #Заметка: "aNd" новосозданный; и паек нет. Поэтому is_linked.
                        #Ох уж этот скейл; единственный с двумя сокетами разных типов.
                        if (sk.type==skInx.type)or(operation=='SCALE'): #Искать одинаковый по типу. Актуально для RGBA Mix.
                            NewLinkHhAndRemember(VqmtData.sk1, sk)
                            break #Нужно соединить только в первый попавшийся, иначе будет соединено во все (например у 'MulAdd').
            elif isCombo:
                for sk in aNd.inputs:
                    if (sk.type==skInx.type)and(not sk.is_linked):
                        NewLinkHhAndRemember(VqmtData.sk0, sk)
                        break
            if VqmtData.sk2:
                for sk in aNd.outputs:
                    if (sk.enabled)and(not sk.hide):
                        NewLinkHhAndRemember(sk, VqmtData.sk2)
                        break
    #Установить значение по умолчанию для второго сокета (большинство нули). Нужно для красоты; и вообще это математика.
    #Заметка: Нод вектора уже создаётся по нулям, так что для него обнулять без нужды.
    tup_default = dict_vqmtDefaultDefault[VqmtData.qmSkType]
    if VqmtData.qmSkType!='RGBA':
        for cyc, sk in enumerate(aNd.inputs):
            #Здесь нет проверок на видимость и линки, пихать значение насильно. Потому что я так захотел.
            sk.default_value = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)[cyc]
    else: #Оптимизация для экономии в dict_vqmtDefaultValueOperation.
        tup_col = dict_vqmtDefaultValueOperation[VqmtData.qmSkType].get(operation, tup_default)
        aNd.inputs[-2-bl4ofs].default_value = tup_col[0]
        aNd.inputs[-1-bl4ofs].default_value = tup_col[1]
    ##
    if isPreset:
        for zp in zip(aNd.inputs, preset[1:]):
            if zp[1]:
                if zp[1]=="x":
                    if VqmtData.sk0:
                        NewLinkHhAndRemember(VqmtData.sk0, zp[0])
                else:
                    zp[0].default_value = eval(f"{zp[1]}")
    #Скрыть все сокеты по запросу. На покерфейсе, ибо залинкованные сокеты всё равно не скроются; и даже без проверки 'sk.enabled'.
    if VqmtData.canProcHideSks: #Для justPieCall нет нужды и могут быть случайные нажатия, для qqm вообще не по концепции.
        if event.alt: #Удобненько получается для основного назначения, можно даже не отпускать Shift Alt.
            for sk in aNd.inputs:
                sk.hide = True
    aNd.show_options = not VqmtData.isHideOptions
    return {'FINISHED'}
class VqmtOpMain(VoronoiOpTool):
    bl_idname = 'node.voronoi_quick_math_main'
    bl_label = "Quick Math"
    operation: bpy.props.StringProperty()
    isCombo: bpy.props.BoolProperty(default=False)
    def modal(self, _context, event):
        #Раньше нужно было очищать мост вручную, потому что он оставался равным последней записи. Сейчас уже не нужно.
        return {'FINISHED'}
    def invoke(self, context, event):
        #Заметка: Здесь использование ныне несуществующего ForseSetSelfNonePropToDefault() уже не работает задуманным образом для непрямого вызова оператора.
        tree = context.space_data.edit_tree
        #if not tree: return {'CANCELLED'}
        match VqmtData.depth:
            case 0:
                if VqmtData.isSpeedPie:
                    VqmtData.list_speedPieDisplayItems = [ti[0] for ti in dict_vqmtQuickMathMain[VqmtData.qmSkType]]
                else:
                    VqmtData.depth += 1
                    VqmtData.list_existingValues.clear()
                    if VqmtData.prefs.vqmtIncludeExistingValues:
                        for nd in tree.nodes:
                            if (VqmtData.qmSkType=='VECTOR')and(nd.type=='VECT_MATH')or(VqmtData.qmSkType=='VALUE')and(nd.type=='MATH'):
                                list_sks = []
                                canLk = False
                                canSk = False
                                for sk in nd.inputs:
                                    tgl = not sk.vl_sold_is_final_linked_cou
                                    if sk.enabled:
                                        canLk |= not tgl
                                        canSk |= tgl
                                    list_sks.append((sk, tgl))
                                if (canLk and canSk)and(length(list_sks)>1):
                                    VqmtData.list_existingValues.append((nd, list_sks))
            case 1:
                assert VqmtData.isSpeedPie #См. ^ `+= 1`.
                VqmtData.list_speedPieDisplayItems = [ti[1] for ti in dict_vqmtQuickMathMain[VqmtData.qmSkType] if ti[0]==self.operation][0] #Заметка: Вычленяется кортеж из генератора.
            case 2:
                if VqmtData.isFirstDone:
                    return {'FINISHED'}
                VqmtData.isFirstDone = True
                #Запоминать нужно только и очевидно только здесь. В Tool только qqm и rlo. Для qqm не запоминается для удобства, и следованию логики rlo.
                VqmtData.dict_lastOperation[VqmtData.qmTrueSkType] = self.operation
                return DoQuickMath(event, tree, self.operation)
        VqmtData.depth += 1
        bpy.ops.wm.call_menu_pie(name=VqmtPieMath.bl_idname)
        return {'RUNNING_MODAL'}
class VqmtPieMath(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_quick_math_pie'
    bl_label = "" #Текст здесь будет отображаться в центре пирога.
    def draw(self, _context):
        def LyVqmAddOp(where, text, icon='NONE'):
            #Автоматический перевод выключен, ибо оригинальные операции у нода математики тоже не переводятся; по крайней мере для Русского.
            where.operator(VqmtOpMain.bl_idname, text=text.replace("_"," ").capitalize(), icon=icon, translate=False).operation = text
        def LyVqmAddItem(where, txt, ico='NONE'):
            ly = where.row(align=VqmtData.pieAlignment==0)
            soldPdsc = VqmtData.pieDisplaySocketColor# if not VqmtData.isJustPie else 0
            if soldPdsc:
                ly = ly.split(factor=( abs( (soldPdsc>0)-.01*abs(soldPdsc)/(1+(soldPdsc>0)) ) )/VqmtData.uiScale, align=True)
            if soldPdsc<0:
                ly.prop(VqmtData.prefs,'vaDecorColSk', text="")
            LyVqmAddOp(ly, text=txt, icon=ico)
            if soldPdsc>0:
                ly.prop(VqmtData.prefs,'vaDecorColSk', text="")
        pie = self.layout.menu_pie()
        if VqmtData.isSpeedPie:
            for li in VqmtData.list_speedPieDisplayItems:
                if not li: #Для пустых записей в базе данных для быстрого пирога.
                    row = pie.row() #Ибо благодаря этому отображается никаким, но при этом занимает место.
                    continue
                LyVqmAddOp(pie, li)
        else:
            isGap = VqmtData.pieAlignment<2
            uiUnitsX = 5.75*((VqmtData.pieScale-1)/2+1)
            def LyGetPieCol(where):
                col = where.column(align=isGap)
                col.ui_units_x = uiUnitsX
                col.scale_y = VqmtData.pieScale
                return col
            colLeft = LyGetPieCol(pie)
            colRight = LyGetPieCol(pie)
            colCenter = LyGetPieCol(pie)
            if VqmtData.pieDisplaySocketTypeInfo==1:
                colLabel = pie.column()
                box = colLabel.box()
                row = box.row(align=True)
                if VqmtData.sk0:
                    row.template_node_socket(color=GetSkColorRaw(VqmtData.sk0))
                match VqmtData.qmSkType:
                    case 'VALUE':   txt = txt_FloatQuickMath
                    case 'VECTOR':  txt = txt_VectorQuickMath
                    case 'BOOLEAN': txt = txt_BooleanQuickMath
                    case 'RGBA':    txt = txt_ColorQuickMode
                row.label(text=txt)
                row.alignment = 'CENTER'
            ##
            def DrawForValVec(isVec):
                if True:
                    nonlocal colRight
                    dict_presets = dict_vqmtQuickPresets[VqmtData.qmSkType]
                    canPreset = (VqmtData.prefs.vqmtIncludeQuickPresets)and(dict_presets)
                    if canPreset:
                        colRight.ui_units_x *= 1.55
                    rowRigth = colRight.row()
                    colRight = rowRigth.column(align=isGap)
                    colRight.ui_units_x = uiUnitsX
                    if canPreset:
                        colRightQp = rowRigth.column(align=isGap)
                        colRightQp.ui_units_x = uiUnitsX/2
                        colRightQp.scale_y = VqmtData.prefs.vqmtPieScaleExtra/VqmtData.pieScale
                        for dk, dv in dict_presets.items():
                            ly = colRightQp.row() if VqmtData.pieAlignment else colRightQp
                            ly.operator(VqmtOpMain.bl_idname, text=dv.replace(" ",""), translate=False).operation = dk
                    ##
                    nonlocal colLeft
                    canExist = (VqmtData.prefs.vqmtIncludeExistingValues)and(VqmtData.list_existingValues)
                    if canExist:
                        colLeft.ui_units_x *= 2.05
                    rowLeft = colLeft.row()
                    if canExist:
                        colLeftExt = rowLeft.column(align=isGap)
                        colLeftExt.ui_units_x = uiUnitsX
                        colLeftExt.scale_y = VqmtData.prefs.vqmtPieScaleExtra/VqmtData.pieScale
                        for nd, list_sks in VqmtData.list_existingValues[-16:]:
                            ly = colLeftExt.row() if VqmtData.pieAlignment else colLeftExt
                            rowItem = ly.row(align=True)
                            rowAdd = rowItem.row(align=True)
                            rowAdd.scale_x = 1.5
                            rowItem.separator()
                            rowVal = rowItem.row(align=True)
                            #rowVal.enabled = False
                            txt = ""
                            for sk, tgl in list_sks:
                                rowProp = rowVal.row(align=True)
                                txt += "|"
                                if tgl:
                                    if sk.enabled:
                                        if type(sk.default_value)==float:
                                            txt += str(sk.default_value)
                                        else:
                                            txt += str(tuple(sk.default_value))[1:-1]
                                        rowProp.column(align=True).prop(sk,'default_value', text="")
                                else:
                                    txt += "x"
                                    rowProp.operator(VqmtOpMain.bl_idname, text="")
                                    rowProp.enabled = False
                            rowAdd.ui_units_x = 2
                            rowAdd.operator(VqmtOpMain.bl_idname, text=str(nd.operation)[:3]).operation = nd.operation+txt
                    colLeft = rowLeft.column(align=isGap)
                    colLeft.ui_units_x = uiUnitsX
                ##
                LyVqmAddItem(colRight,'ADD','ADD')
                LyVqmAddItem(colRight,'SUBTRACT','REMOVE')
                ##
                LyVqmAddItem(colRight,'MULTIPLY','SORTBYEXT')
                LyVqmAddItem(colRight,'DIVIDE','FIXED_SIZE') #ITALIC  FIXED_SIZE
                ##
                colRight.separator()
                LyVqmAddItem(colRight, 'MULTIPLY_ADD')
                LyVqmAddItem(colRight, 'ABSOLUTE')
                colRight.separator()
                for li in ('SINE','COSINE','TANGENT'):
                    LyVqmAddItem(colCenter, li, 'FORCE_HARMONIC')
                if not isVec:
                    for li in ('POWER','SQRT','EXPONENT','LOGARITHM','INVERSE_SQRT','PINGPONG'):
                        LyVqmAddItem(colRight, li)
                    colRight.separator()
                    LyVqmAddItem(colRight, 'RADIANS')
                    LyVqmAddItem(colRight, 'DEGREES')
                    LyVqmAddItem(colLeft, 'FRACT', 'IPO_LINEAR')
                    for li in ('ARCTANGENT','ARCSINE','ARCCOSINE'):
                        LyVqmAddItem(colCenter, li, 'RNA')
                    for li in ('ARCTAN2','SINH','COSH','TANH'):
                        LyVqmAddItem(colCenter, li)
                else:
                    for li in ('SCALE','NORMALIZE','LENGTH','DISTANCE'):
                        LyVqmAddItem(colRight, li)
                    colRight.separator()
                    LyVqmAddItem(colLeft, 'FRACTION', 'IPO_LINEAR')
                LyVqmAddItem(colLeft,'FLOOR','IPO_CONSTANT')
                LyVqmAddItem(colLeft,'CEIL')
                LyVqmAddItem(colLeft,'MAXIMUM','NONE') #SORT_DESC  TRIA_UP_BAR
                LyVqmAddItem(colLeft,'MINIMUM','NONE') #SORT_ASC  TRIA_DOWN_BAR
                for li in ('MODULO', 'FLOORED_MODULO', 'SNAP', 'WRAP'):
                    LyVqmAddItem(colLeft, li)
                colLeft.separator()
                if not isVec:
                    for li in ('GREATER_THAN','LESS_THAN','TRUNC','SIGN','SMOOTH_MAX','SMOOTH_MIN','ROUND','COMPARE'):
                        LyVqmAddItem(colLeft, li)
                else:
                    LyVqmAddItem(colLeft,'DOT_PRODUCT',  'LAYER_ACTIVE')
                    LyVqmAddItem(colLeft,'CROSS_PRODUCT','ORIENTATION_LOCAL') #OUTLINER_DATA_EMPTY  ORIENTATION_LOCAL  EMPTY_ARROWS
                    LyVqmAddItem(colLeft,'PROJECT',      'CURVE_PATH') #SNAP_OFF  SNAP_ON  MOD_SIMPLIFY  CURVE_PATH
                    LyVqmAddItem(colLeft,'FACEFORWARD',  'ORIENTATION_NORMAL')
                    LyVqmAddItem(colLeft,'REFRACT',      'NODE_MATERIAL') #MOD_OFFSET  NODE_MATERIAL
                    LyVqmAddItem(colLeft,'REFLECT',      'INDIRECT_ONLY_OFF') #INDIRECT_ONLY_OFF  INDIRECT_ONLY_ON
            def DrawForBool():
                LyVqmAddItem(colRight,'AND')
                LyVqmAddItem(colRight,'OR')
                LyVqmAddItem(colRight,'NOT')
                LyVqmAddItem(colLeft,'NAND')
                LyVqmAddItem(colLeft,'NOR')
                LyVqmAddItem(colLeft,'XOR')
                LyVqmAddItem(colLeft,'XNOR')
                LyVqmAddItem(colCenter,'IMPLY')
                LyVqmAddItem(colCenter,'NIMPLY')
            def DrawForCol():
                for li in ('LIGHTEN','DARKEN','SCREEN','DODGE','LINEAR_LIGHT','SOFT_LIGHT','OVERLAY','BURN'):
                    LyVqmAddItem(colRight, li)
                for li in ('ADD','SUBTRACT','MULTIPLY','DIVIDE','DIFFERENCE','EXCLUSION'):
                    LyVqmAddItem(colLeft, li)
                for li in ('VALUE','SATURATION','HUE','COLOR'):
                    LyVqmAddItem(colCenter, li)
            match VqmtData.qmSkType:
                case 'VALUE'|'VECTOR': DrawForValVec(VqmtData.qmSkType=='VECTOR')
                case 'BOOLEAN': DrawForBool()
                case 'RGBA': DrawForCol()

list_classes += [VqmtOpMain, VqmtPieMath]

class VoronoiRantoTool(VoronoiToolNd): #Свершилось.
    bl_idname = 'node.voronoi_ranto'
    bl_label = "Voronoi RANTO"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    isOnlySelected: bpy.props.IntProperty(name="Only selected", default=0, min=0, max=2, description="0 – Any node.\n1 – Selected + reroutes.\n2 – Only selected")
    isUniWid:       bpy.props.BoolProperty(name="Uniform width", default=False)
    widthNd: bpy.props.IntProperty(name="Node width", default=140, soft_min=100, soft_max=180, subtype='FACTOR')
    indentX: bpy.props.IntProperty(name="Indent x",   default=40,  soft_min=0,   soft_max=80,  subtype='FACTOR')
    indentY: bpy.props.IntProperty(name="Indent y",   default=30,  soft_min=0,   soft_max=60,  subtype='FACTOR')
    isUncollapseNodes: bpy.props.BoolProperty(name="Uncollapse nodes", default=False)
    isDeleteReroutes:  bpy.props.BoolProperty(name="Delete reroutes",  default=False)
    isSelectNodes: bpy.props.IntProperty(name="Select nodes", default=1, min=-1, max=1, description="-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting involveds node")
    isIncludeMutedLinks:    bpy.props.BoolProperty(name="Include muted links",     default=False)
    isIncludeNonValidLinks: bpy.props.BoolProperty(name="Include non valid links", default=True)
    isAccumulate: bpy.props.BoolProperty(name="Accumulate", default=False)
    def DoRANTO(self, ndTar, tree, isFixIslands=True):
        if ndTar==self.lastNdProc:
            return
        self.lastNdProc = ndTar
        ndTar.select = True
        if not self.isAccumulate:
            tree.nodes.active = ndTar
        #elif self.ndMaxAccRoot:
        #    ndTar = self.ndMaxAccRoot
        def DoRanto(nd):
            rada = RantoData(self.isOnlySelected+self.isAccumulate, self.widthNd, self.isUniWid, self.indentX, self.indentY, self.isIncludeMutedLinks, self.isIncludeNonValidLinks, isFixIslands)
            VrtDoRecursiveAutomaticNodeTopologyOrganization(rada, nd)
            return rada
        if self.isUncollapseNodes:
            dict_remresNdHide = {}
            for nd in tree.nodes:
                dict_remresNdHide[nd] = nd.hide
                nd.hide = False
            bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
        rada = DoRanto(ndTar)
        if self.isDeleteReroutes:
            bpy.ops.node.select_all(action='DESELECT')
            isInvl = False
            for nd in rada.dict_ndTopoWorking:
                if nd.type=='REROUTE':
                    nd.select = True
                    isInvl = True
            if isInvl:
                bpy.ops.node.delete_reconnect()
                rada = DoRanto(ndTar)
        if (self.isSelectNodes==-1)and(not self.isAccumulate):
            bpy.ops.node.select_all(action='DESELECT')
        soldNAcc = not self.isAccumulate
        for nd in tree.nodes:
            tgl = nd in rada.dict_ndTopoWorking
            if (self.isSelectNodes==1)and(soldNAcc):
                nd.select = tgl
            if (not tgl)and(self.isUncollapseNodes): #Восстановить у незадействованных.
                nd.hide = dict_remresNdHide[nd]
        if self.isAccumulate:
            tree.nodes.active = ndTar
            for nd in rada.dict_ndTopoWorking:
                nd.select = True
        #ndTar.location = ndTar.location #bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue #За этим обращайтесь к оригинальному RANTO-аддону.
            self.fotagoNd = ftgNd
            #if not self.ndMaxAccRoot:
            #    self.ndMaxAccRoot = nd
            if prefs.vrtIsLiveRanto:
                self.DoRANTO(nd, tree, prefs.vrtIsFixIslands)
            break
    def MatterPurposeTool(self, event, prefs, tree):
        ndTar = self.fotagoNd.tar
        #if self.isAccumulate:
        #    self.ndMaxAccRoot = None
        #    self.lastNdProc = None
        self.DoRANTO(ndTar, tree, prefs.vrtIsFixIslands)
        #DisplayMessage("RANTO", TranslateIface("This tool is empty")+" ¯\_(ツ)_/¯")
    def InitTool(self, event, prefs, tree):
        self.lastNdProc = None
        #self.ndMaxAccRoot = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vrtIsLiveRanto')
        LyAddLeftProp(col, prefs,'vrtIsFixIslands')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey("This tool is empty") as dm:
            dm[ru_RU] = "Этот инструмент пуст"
#            dm[zh_CN] = ""
        ##
        with VlTrMapForKey(GetAnnotFromCls(cls,'isOnlySelected').name) as dm:
            dm[ru_RU] = "Только выделенные"
            dm[zh_CN] = "仅选定的"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isOnlySelected').description) as dm:
            dm[ru_RU] = "0 – Любой нод.\n1 – Выделенные + рероуты.\n2 – Только выделенные"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isUniWid').name) as dm:
            dm[ru_RU] = "Постоянная ширина"
            dm[zh_CN] = "统一宽度"
        with VlTrMapForKey(GetAnnotFromCls(cls,'widthNd').name) as dm:
            dm[ru_RU] = "Ширина нод"
            dm[zh_CN] = "节点宽度"
        with VlTrMapForKey(GetAnnotFromCls(cls,'indentX').name) as dm:
            dm[ru_RU] = "Отступ по X"
            dm[zh_CN] = "X缩进"
        with VlTrMapForKey(GetAnnotFromCls(cls,'indentY').name) as dm:
            dm[ru_RU] = "Отступ по Y"
            dm[zh_CN] = "Y缩进"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isUncollapseNodes').name) as dm:
            dm[ru_RU] = "Разворачивать ноды"
            dm[zh_CN] = "展开节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isDeleteReroutes').name) as dm:
            dm[ru_RU] = "Удалять рероуты"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNodes').name) as dm:
            dm[ru_RU] = "Выделять ноды"
            dm[zh_CN] = "选择节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNodes').description) as dm:
            dm[ru_RU] = "-1 – Де-выделять всё.\n 0 – Ничего не делать.\n 1 – Выделять задействованные ноды"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isIncludeMutedLinks').name) as dm:
            dm[ru_RU] = "Разрешить выключенные линки"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isIncludeNonValidLinks').name) as dm:
            dm[ru_RU] = "Разрешить невалидные линки"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isAccumulate').name) as dm:
            dm[ru_RU] = "Накапливать"
#            dm[zh_CN] = ""
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vrtIsLiveRanto').name) as dm:
            dm[ru_RU] = "Ranto в реальном времени"
            dm[zh_CN] = "实时对齐"
        with VlTrMapForKey(GetPrefsRnaProp('vrtIsFixIslands').name) as dm:
            dm[ru_RU] = "Чинить острова"
            dm[zh_CN] = ""

SmartAddToRegAndAddToKmiDefs(VoronoiRantoTool, "###_R")
SmartAddToRegAndAddToKmiDefs(VoronoiRantoTool, "S##_R", {'isAccumulate':True})
SmartAddToRegAndAddToKmiDefs(VoronoiRantoTool, "#C#_R", {'isOnlySelected':2})
SmartAddToRegAndAddToKmiDefs(VoronoiRantoTool, "#CA_R", {'isUniWid':True, 'isUncollapseNodes':True, 'isDeleteReroutes':True})
dict_setKmiCats['spc'].add(VoronoiRantoTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vrtIsLiveRanto:  bpy.props.BoolProperty(name="Live Ranto", default=True)
    vrtIsFixIslands: bpy.props.BoolProperty(name="Fix islands", default=True)

with VlTrMapForKey(VoronoiRantoTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi节点自动排布对齐"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiRantoTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiRantoTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiRantoTool.bl_label}节点自动排布对齐工具设置:"

dict_toolLangSpecifDataPool[VoronoiRantoTool, ru_RU] = "Сейчас этот инструмент не более чем пустышка.\nСтанет доступным, когда VL стяжет свои заслуженные(?) лавры популярности."

#Теперь RANTO интегрирован в VL. Неожиданно даже для меня.
#См. оригинал: https://github.com/ugorek000/RANTO

class RantoData():
    def __init__(self, isOnlySelected=0, widthNd=140, isUniWid=False, indentX=40, indentY=30, isIncludeMutedLinks=False, isIncludeNonValidLinks=False, isFixIslands=True):
        self.kapibara = ""
        self.dict_ndTopoWorking = {}

def VrtDoRecursiveAutomaticNodeTopologyOrganization(rada, ndRoot):
    rada.kapibara = "kapibara"


fitVstModeItems = ( ('SWAP', "Swap",     "All links from the first socket will be on the second, from the second on the first."),
                    ('ADD',  "Add",      "Add all links from the second socket to the first one."),
                    ('TRAN', "Transfer", "Move all links from the second socket to the first one with replacement.") )
class VoronoiSwapperTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_swaper'
    bl_label = "Voronoi Swapper"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    toolMode:     bpy.props.EnumProperty(name="Mode", default='SWAP', items=fitVstModeItems)
    isCanAnyType: bpy.props.BoolProperty(name="Can swap with any socket type", default=False)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            #За основу были взяты критерии от Миксера.
            if isFirstActivation:
                ftgSkOut, ftgSkIn = None, None
                for ftg in list_ftgSksOut: #todo0NA да это же Findanysk!?
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkOut = ftg
                        break
                for ftg in list_ftgSksIn:
                    if ftg.blid!='NodeSocketVirtual':
                        ftgSkIn = ftg
                        break
                #Разрешить возможность "добавлять" и для входов тоже, но только для мультиинпутов, ибо очевидное
                if (self.toolMode=='ADD')and(ftgSkIn):
                    #Проверка по типу, но не по 'is_multi_input', чтобы из обычного в мультиинпут можно было добавлять.
                    if (ftgSkIn.blid not in ('NodeSocketGeometry','NodeSocketString')):#or(not ftgSkIn.tar.is_multi_input): #Без второго условия больше возможностей.
                        ftgSkIn = None
                self.fotagoSk0 = MinFromFtgs(ftgSkOut, ftgSkIn)
            #Здесь вокруг аккумулировалось много странных проверок с None и т.п. -- результат соединения вместе многих типа высокоуровневых функций, что я понаизобретал.
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                for ftg in list_ftgSksOut if skOut0.is_output else list_ftgSksIn:
                    if ftg.blid=='NodeSocketVirtual':
                        continue
                    if (self.isCanAnyType)or(skOut0.bl_idname==ftg.blid)or(self.SkBetweenFieldsCheck(skOut0, ftg.tar)):
                        self.fotagoSk1 = ftg
                    if self.fotagoSk1: #В случае успеха прекращать поиск.
                        break
                if (self.fotagoSk1)and(skOut0==self.fotagoSk1.tar): #Проверка на самокопию.
                    self.fotagoSk1 = None
                    break #Ломать для isCanAnyType, когда isFirstActivation==False и сокет оказался самокопией; чтобы не находил сразу два нода.
                if not self.isCanAnyType:
                    if not(self.fotagoSk1 or isFirstActivation): #Если нет результата, продолжаем искать.
                        continue
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            break
    def MatterPurposePoll(self):
        return self.fotagoSk0 and self.fotagoSk1
    def MatterPurposeTool(self, event, prefs, tree):
        skIo0 = self.fotagoSk0.tar
        skIo1 = self.fotagoSk1.tar
        match self.toolMode:
            case 'SWAP':
                #Поменять местами все соединения у первого и второго сокета:
                list_memSks = []
                if skIo0.is_output: #Проверка одинаковости is_output -- забота для NextAssignmentTool().
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  Чтобы линк от нода не создался сам в себя. Проверять нужно у всех и таковые не обрабатывать.
                            list_memSks.append(lk.to_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.to_node!=skIo0.node: # T 0  ^
                            tree.links.new(skIo0, lk.to_socket)
                            if lk.to_socket.is_multi_input: #Для мультиинпутов удалить.
                                tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(skIo1, li)
                else:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            list_memSks.append(lk.from_socket)
                            tree.links.remove(lk)
                    for lk in skIo1.vl_sold_links_final:
                        if lk.from_node!=skIo0.node: # F 0  ^
                            tree.links.new(lk.from_socket, skIo0)
                            tree.links.remove(lk)
                    for li in list_memSks:
                        tree.links.new(li, skIo1)
            case 'ADD'|'TRAN':
                #Просто добавить линки с первого сокета на второй. Aka объединение, добавление.
                if self.toolMode=='TRAN':
                    #Тоже самое, как и добавление, только с потерей связей у первого сокета.
                    for lk in skIo1.vl_sold_links_final:
                        tree.links.remove(lk)
                if skIo0.is_output:
                    for lk in skIo0.vl_sold_links_final:
                        if lk.to_node!=skIo1.node: # T 1  ^
                            tree.links.new(skIo1, lk.to_socket)
                            if lk.to_socket.is_multi_input: #Без этого lk всё равно указывает на "добавленный" линк, от чего удаляется. Поэтому явная проверка для мультиинпутов.
                                tree.links.remove(lk)
                else: #Добавлено ради мультиинпутов.
                    for lk in skIo0.vl_sold_links_final:
                        if lk.from_node!=skIo1.node: # F 1  ^
                            tree.links.new(lk.from_socket, skIo1)
                            tree.links.remove(lk)
        #VST VLRT же без нужды, да ведь?
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.SWAP.name) as dm:
            dm[ru_RU] = "Поменять"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SWAP.description) as dm:
            dm[ru_RU] = "Все линки у первого сокета будут на втором, у второго на первом."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.ADD.name) as dm:
            dm[ru_RU] = "Добавить"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.ADD.description) as dm:
            dm[ru_RU] = "Добавить все линки со второго сокета на первый. Второй будет пустым."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.TRAN.name) as dm:
            dm[ru_RU] = "Переместить"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.TRAN.description) as dm:
            dm[ru_RU] = "Переместить все линки со второго сокета на первый с заменой."
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isCanAnyType').name) as dm:
            dm[ru_RU] = "Может меняться с любым типом"
            dm[zh_CN] = "可以与任何类型交换"

SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "S##_S", {'toolMode':'SWAP'})
SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "##A_S", {'toolMode':'ADD'})
SmartAddToRegAndAddToKmiDefs(VoronoiSwapperTool, "#CA_S", {'toolMode':'TRAN'})
dict_setKmiCats['oth'].add(VoronoiSwapperTool.bl_idname)

with VlTrMapForKey(VoronoiSwapperTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速替换端口"

dict_toolLangSpecifDataPool[VoronoiSwapperTool, ru_RU] = """Инструмент для обмена линков у двух сокетов, или добавления их к одному из них.
Для линка обмена не будет, если в итоге он окажется исходящим из своего же нода."""
dict_toolLangSpecifDataPool[VoronoiSwapperTool, zh_CN] = "Alt是批量替换输出端口,Shift是互换端口"

#Нужен только для наведения порядка и эстетики в дереве.
#Для тех, кого (например меня) напрягают "торчащие без дела" пустые сокеты выхода, или нулевые (чьё значение 0.0, чёрный, и т.п.) незадействованные сокеты входа.
fitVhtModeItems = ( ('NODE',      "Auto-node",    "Automatically processing of hiding of sockets for a node."),
                    ('SOCKET',    "Socket",       "Hiding the socket."),
                    ('SOCKETVAL', "Socket value", "Switching the visibility of a socket contents.") )
class VoronoiHiderTool(VoronoiToolAny):
    bl_idname = 'node.voronoi_hider'
    bl_label = "Voronoi Hider"
    usefulnessForCustomTree = True
    usefulnessForUndefTree = True
    toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVhtModeItems)
    isTriggerOnCollapsedNodes: bpy.props.BoolProperty(name="Trigger on collapsed nodes", default=True)
    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE')
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoAny = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if (not self.isTriggerOnCollapsedNodes)and(nd.hide):
                continue
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            self.fotagoAny = ftgNd
            match self.toolMode:
                case 'SOCKET'|'SOCKETVAL':
                    #Для режима сокетов обработка свёрнутости такая же, как у всех.
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
                    def GetNotLinked(list_ftgSks): #Findanysk.
                        for ftg in list_ftgSks:
                            if not ftg.tar.vl_sold_is_final_linked_cou:
                                return ftg
                    ftgSkIn = GetNotLinked(list_ftgSksIn)
                    ftgSkOut = GetNotLinked(list_ftgSksOut)
                    if self.toolMode=='SOCKET':
                        self.fotagoAny = MinFromFtgs(ftgSkOut, ftgSkIn)
                    else:
                        self.fotagoAny = ftgSkIn
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoAny) #Для режима сокетов тоже нужно перерисовывать, ибо нод у прицепившегося сокета может быть свёрнут.
                case 'NODE':
                    #Для режима нод нет разницы, раскрывать все подряд под курсором, или нет.
                    if prefs.vhtIsToggleNodesOnDrag:
                        if self.firstResult is None:
                            #Если активация для нода ничего не изменила, то для остальных хочется иметь сокрытие, а не раскрытие. Но текущая концепция не позволяет,
                            # информации об этом тупо нет. Поэтому реализовал это точечно вовне (здесь), а не модификацией самой реализации.
                            LGetVisSide = lambda a: [sk for sk in a if sk.enabled and not sk.hide]
                            list_visibleSks = [LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]
                            self.firstResult = HideFromNode(prefs, nd, True)
                            HideFromNode(prefs, nd, self.firstResult, True) #Заметка: Изменить для нода (для проверки ниже), но не трогать 'self.firstResult'.
                            if list_visibleSks==[LGetVisSide(nd.inputs), LGetVisSide(nd.outputs)]:
                                self.firstResult = True
                        HideFromNode(prefs, nd, self.firstResult, True)
                        #См. в вики, почему опция isReDrawAfterChange была удалена.
                        #Todo0v6SF Единственное возможное решение, так это сделать изменение нода _после_ отрисовки одного кадра.
                        #^ Т.е. цепляться к новому ноду на один кадр, а потом уже обработать его сразу с поиском нового нода и рисовки к нему (как для примера в вики).
            break
    def MatterPurposeTool(self, event, prefs, tree):
        match self.toolMode:
            case 'NODE':
                if not prefs.vhtIsToggleNodesOnDrag:
                    #Во время сокрытия сокета нужно иметь информацию обо всех, поэтому выполняется дважды. В первый заход собирается, во второй выполняется.
                    HideFromNode(prefs, self.fotagoAny.tar, HideFromNode(prefs, self.fotagoAny.tar, True), True)
            case 'SOCKET':
                self.fotagoAny.tar.hide = True
            case 'SOCKETVAL':
                self.fotagoAny.tar.hide_value = not self.fotagoAny.tar.hide_value
    def InitTool(self, event, prefs, tree):
        self.firstResult = None #Получить действие у первого нода "свернуть" или "развернуть", а потом транслировать его на все остальные попавшиеся.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddHandSplitProp(col, prefs,'vhtHideBoolSocket')
        LyAddHandSplitProp(col, prefs,'vhtHideHiddenBoolSocket')
        LyAddHandSplitProp(col, prefs,'vhtNeverHideGeometry')
        LyAddHandSplitProp(col, prefs,'vhtIsUnhideVirtual', forceBoolean=2)
        LyAddLeftProp(col, prefs,'vhtIsToggleNodesOnDrag')
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.NODE.name) as dm:
            dm[ru_RU] = "Авто-нод"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.NODE.description) as dm:
            dm[ru_RU] = "Автоматически обработать сокрытие сокетов для нода."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SOCKET.description) as dm:
            dm[ru_RU] = "Сокрытие сокета."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SOCKETVAL.name) as dm:
            dm[ru_RU] = "Значение сокета"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SOCKETVAL.description) as dm:
            dm[ru_RU] = "Переключение видимости содержимого сокета."
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isTriggerOnCollapsedNodes').name) as dm:
            dm[ru_RU] = "Триггериться на свёрнутые ноды"
            dm[zh_CN] = "仅触发已折叠节点"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideBoolSocket').name) as dm:
            dm[ru_RU] = "Скрывать Boolean сокеты"
            dm[zh_CN] = "隐藏布尔端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideHiddenBoolSocket').name) as dm:
            dm[ru_RU] = "Скрывать скрытые Boolean сокеты"
            dm[zh_CN] = "隐藏已隐藏的布尔端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideBoolSocket',1).name) as dm:
            dm[ru_RU] = "Если True"
            dm[zh_CN] = "如果为True"
        with VlTrMapForKey(GetPrefsRnaProp('vhtHideBoolSocket',3).name) as dm:
            dm[ru_RU] = "Если False"
            dm[zh_CN] = "如果为False"
        with VlTrMapForKey(GetPrefsRnaProp('vhtNeverHideGeometry').name) as dm:
            dm[ru_RU] = "Никогда не скрывать входные сокеты геометрии"
            dm[zh_CN] = "永不隐藏几何输入端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtNeverHideGeometry',1).name) as dm:
            dm[ru_RU] = "Только первый"
            dm[zh_CN] = "仅第一个端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtIsUnhideVirtual').name) as dm:
            dm[ru_RU] = "Показывать виртуальные сокеты"
            dm[zh_CN] = "显示虚拟端口"
        with VlTrMapForKey(GetPrefsRnaProp('vhtIsToggleNodesOnDrag').name) as dm:
            dm[ru_RU] = "Переключать ноды при ведении курсора" #"Обрабатывать ноды в реальном времени"
            dm[zh_CN] = "移动光标时切换节点"

SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "S##_E", {'toolMode':'SOCKET'})
SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "##A_E", {'toolMode':'SOCKETVAL'})
SmartAddToRegAndAddToKmiDefs(VoronoiHiderTool, "#C#_E", {'toolMode':'NODE'})
dict_setKmiCats['oth'].add(VoronoiHiderTool.bl_idname)

list_itemsProcBoolSocket = [('ALWAYS',"Always",""), ('IF_FALSE',"If false",""), ('NEVER',"Never",""), ('IF_TRUE',"If true","")]

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vhtHideBoolSocket:       bpy.props.EnumProperty(name="Hide boolean sockets",             default='IF_FALSE', items=list_itemsProcBoolSocket)
    vhtHideHiddenBoolSocket: bpy.props.EnumProperty(name="Hide hidden boolean sockets",      default='ALWAYS',   items=list_itemsProcBoolSocket)
    vhtNeverHideGeometry:    bpy.props.EnumProperty(name="Never hide geometry input socket", default='FALSE',    items=( ('FALSE',"False",""), ('ONLY_FIRST',"Only first",""), ('TRUE',"True","") ))
    vhtIsUnhideVirtual:      bpy.props.BoolProperty(name="Unhide virtual sockets",           default=False)
    vhtIsToggleNodesOnDrag:  bpy.props.BoolProperty(name="Toggle nodes on drag",             default=True)

with VlTrMapForKey(VoronoiHiderTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速隐藏"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiHiderTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiHiderTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiHiderTool.bl_label}快速隐藏端口设置:"

dict_toolLangSpecifDataPool[VoronoiHiderTool, ru_RU] = "Инструмент для наведения порядка и эстетики в дереве.\nСкорее всего 90% уйдёт на использование автоматического сокрытия нодов."
dict_toolLangSpecifDataPool[VoronoiHiderTool, zh_CN] = "Shift是自动隐藏数值为0/颜色纯黑/未连接的端口,Ctrl是单个隐藏端口"

def HideFromNode(prefs, ndTarget, lastResult, isCanDo=False): #Изначально лично моя утилита, была создана ещё до VL.
    set_equestrianHideVirtual = {'GROUP_INPUT','SIMULATION_INPUT','SIMULATION_OUTPUT','REPEAT_INPUT','REPEAT_OUTPUT'}
    scoGeoSks = 0 #Для CheckSkZeroDefaultValue().
    def CheckSkZeroDefaultValue(sk): #Shader и Virtual всегда True, Geometry от настроек аддона.
        match sk.type: #Отсортированы в порядке убывания сложности.
            case 'GEOMETRY':
                match prefs.vhtNeverHideGeometry: #Задумывалось и для out тоже, но как-то леновато, а ещё `GeometryNodeBoundBox`, так что...
                    case 'FALSE': return True
                    case 'TRUE': return False
                    case 'ONLY_FIRST':
                        nonlocal scoGeoSks
                        scoGeoSks += 1
                        return scoGeoSks!=1
            case 'VALUE':
                #Todo1v6 когда приспичит, или будет нечем заняться -- добавить список настраиваемых точечных сокрытий, через оценку с помощью питона.
                # ^ словарь[блид сокета]:{множество имён}. А ещё придумать, как пронести default_value.
                if (GetSkLabelName(sk) in {'Alpha', 'Factor'})and(sk.default_value==1): #Для некоторых float сокетов тоже было бы неплохо иметь точечную проверку.
                    return True
                return sk.default_value==0
            case 'VECTOR':
                if (GetSkLabelName(sk)=='Scale')and(sk.default_value[0]==1)and(sk.default_value[1]==1)and(sk.default_value[2]==1):
                    return True #Меня переодически напрягал 'GeometryNodeTransform', и в один прекрасной момент накопилось..
                return (sk.default_value[0]==0)and(sk.default_value[1]==0)and(sk.default_value[2]==0) #Заметка: `sk.default_value==(0,0,0)` не прокатит.
            case 'BOOLEAN':
                if not sk.hide_value: #Лень паять, всё обрабатывается в прямом виде.
                    match prefs.vhtHideBoolSocket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
                        case 'IF_FALSE': return not sk.default_value
                else:
                    match prefs.vhtHideHiddenBoolSocket:
                        case 'ALWAYS':   return True
                        case 'NEVER':    return False
                        case 'IF_TRUE':  return sk.default_value
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
                if (sk.enabled)and(not sk.hide)and(not sk.vl_sold_is_final_linked_cou)and(LMainCheck(sk)): #Ядро сокрытия находится здесь, в первых двух проверках.
                    success |= not sk.hide #Здесь success означает будет ли оно скрыто.
                    if isCanDo:
                        sk.hide = True
            return success
        #Если виртуальные были созданы вручную, то не скрывать их. Потому что. Но если входов групп больше одного, то всё равно скрывать.
        #Изначальный смысл LVirtual -- "LCheckOver" -- проверка "над", точечные дополнительные условия. Но в ней скопились только для виртуальных, поэтому переназвал.
        isMoreNgInputs = False if ndTarget.type!='GROUP_INPUT' else length([True for nd in ndTarget.id_data.nodes if nd.type=='GROUP_INPUT'])>1
        LVirtual = lambda sk: not( (sk.bl_idname=='NodeSocketVirtual')and #Смысл этой Labmda -- точечное не-сокрытие для тех, которые виртуальные,
                                   (sk.node.type in {'GROUP_INPUT','GROUP_OUTPUT'})and # у io-всадников,
                                   (sk!=( sk.node.outputs if sk.is_output else sk.node.inputs )[-1])and # и не последние (то ради чего),
                                   (not isMoreNgInputs) ) # и GROUP_INPUT в дереве всего один.
        #Ядро в трёх строчках ниже:
        success = CheckAndDoForIo(ndTarget.inputs, lambda sk: CheckSkZeroDefaultValue(sk)and(LVirtual(sk)) ) #Для входов мейнстримная проверка их значений, и дополнительно виртуальные.
        if any(True for sk in ndTarget.outputs if (sk.enabled)and(sk.vl_sold_is_final_linked_cou)): #Если хотя бы один сокет подсоединён вовне
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
                sk.hide = (sk.bl_idname=='NodeSocketVirtual')and(not prefs.vhtIsUnhideVirtual)
        return success

#"Массовый линкер" -- как линкер, только много за раз (ваш кэп).
#См. вики на гитхабе, чтобы посмотреть 5 примеров использования массового линкера. Дайте мне знать, если обнаружите ещё одно необычное применение этому инструменту.
class VoronoiMassLinkerTool(VoronoiToolRoot): #"Малыш котопёс", не ноды, не сокеты.
    bl_idname = 'node.voronoi_mass_linker'
    bl_label = "Voronoi MassLinker" #Единственный, у кого нет пробела. Потому что слишком котопёсный))00)0
    # А если серьёзно, то он действительно самый странный. Пародирует VLT с его dsIsAlwaysLine. SocketArea стакаются, если из нескольких в одного. Пишет в функции рисования...
    # А ещё именно он есть/будет на превью аддона, ибо обладает самой большой степенью визуальности из всех инструментов (причем без верхнего предела).
    usefulnessForCustomTree = True
    isIgnoreExistingLinks: bpy.props.BoolProperty(name="Ignore existing links", default=False)
    def CallbackDrawTool(self, drata):
        #Здесь нарушается местная VL'ская концепция чтения-записи, и CallbackDraw ищет и записывает найденные сокеты вместо того, чтобы просто читать и рисовать. Полагаю, так инструмент проще реализовать.
        self.list_equalFtgSks.clear() #Очищать каждый раз. P.s. важно делать это в начале, а не в ветке двух нод.
        if not self.ndTar0:
            TemplateDrawSksToolHh(drata, None, None, isClassicFlow=True)
        elif (self.ndTar0)and(not self.ndTar1):
            list_ftgSksOut = self.ToolGetNearestSockets(self.ndTar0)[1]
            if list_ftgSksOut:
                #Не известно, к кому это будет подсоединено и к кому получится -- рисовать от всех сокетов.
                TemplateDrawSksToolHh(drata, *list_ftgSksOut, isDrawText=False, isClassicFlow=True) #"Всем к курсору!"
            else:
                TemplateDrawSksToolHh(drata, None, None, isClassicFlow=True)
        else:
            list_ftgSksOut = self.ToolGetNearestSockets(self.ndTar0)[1]
            list_ftgSksIn = self.ToolGetNearestSockets(self.ndTar1)[0]
            for ftgo in list_ftgSksOut:
                for ftgi in list_ftgSksIn:
                    #Т.к. "массовый" -- критерии приходится автоматизировать и сделать их едиными для всех.
                    if CompareSkLabelName(ftgo.tar, ftgi.tar, self.prefs.vmltIgnoreCase): #Соединяться только с одинаковыми по именам сокетами.
                        tgl = False
                        if self.isIgnoreExistingLinks: #Если соединяться без разбору, то исключить уже имеющиеся "желанные" связи. Нужно для эстетики.
                            for lk in ftgi.tar.vl_sold_links_final:
                                #Проверка is_linked нужна, чтобы можно было включить выключенные линки, перезаменив их.
                                if (lk.from_socket.is_linked)and(lk.from_socket==ftgo.tar):
                                    tgl = True
                            tgl = not tgl
                        else: #Иначе не трогать уже соединённых.
                            tgl = not ftgi.tar.vl_sold_is_final_linked_cou
                        if tgl:
                            self.list_equalFtgSks.append( (ftgo, ftgi) )
            if not self.list_equalFtgSks:
                DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) #Иначе вообще всё исчезнет.
            for li in self.list_equalFtgSks:
                #Т.к. поиск по именам, рисоваться здесь и подсоединяться ниже, возможно из двух (и больше) сокетов в один и тот же одновременно. Типа "конфликт" одинаковых имён.
                TemplateDrawSksToolHh(drata, li[0], li[1], isDrawText=False, isClassicFlow=True) #*[ti for li in self.list_equalFtgSks for ti in li]
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            CheckUncollapseNodeAndReNext(nd, self, cond=isFirstActivation, flag=True)
            #Помимо свёрнутых также игнорируются и рероуты, потому что у них инпуты всегда одни и с одинаковыми именами.
            if nd.type=='REROUTE':
                continue
            self.ndTar1 = nd
            if isFirstActivation:
                self.ndTar0 = nd #Здесь нод-вывод устанавливается один раз.
            if self.ndTar0==self.ndTar1: #Проверка на самокопию.
                self.ndTar1 = None #Здесь нод-вход обнуляется каждый раз в случае неудачи.
            #Заметка: Первое нахождение ndTar1 -- list_equalFtgSks == [].
            if self.ndTar1:
                list_ftgSksIn = self.ToolGetNearestSockets(self.ndTar1)[0] #Только ради условия раскрытия. Можно было и list_equalFtgSks, но опять проскальзывающие кадры.
                CheckUncollapseNodeAndReNext(nd, self, cond=list_ftgSksIn, flag=False)
            break
    def MatterPurposePoll(self):
        return self.list_equalFtgSks
    def MatterPurposeTool(self, event, prefs, tree):
        if True:
            #Если выходы нода и входы другого нода имеют в сумме 4 одинаковых сокета по названию, то происходит не ожидаемое от инструмента поведение.
            #Поэтому соединять только один линк на входной сокет (мультиинпуты не в счёт).
            set_alreadyDone = set()
            list_skipToEndEq = []
            list_skipToEndSk = []
            for li in self.list_equalFtgSks:
                sko = li[0].tar
                ski = li[1].tar
                if ski in set_alreadyDone:
                    continue
                if sko in list_skipToEndSk: #Заметка: Достаточно и линейного чтения, но пока оставлю так, чтоб наверняка.
                    list_skipToEndEq.append(li)
                    continue
                tree.links.new(sko, ski) #Заметка: Наверное лучше оставить безопасное "сырое" соединение, учитывая массовость соединения и неограниченность количества.
                VlrtRememberLastSockets(sko, ski) #Заметка: Эта и далее -- "последнее всегда последнее", эффективно-ниже проверками уже не опуститься; ну или по крайней мере на моём уровне знаний.
                if not ski.is_multi_input: #"Мультиинпуты бездонны!"
                    set_alreadyDone.add(ski)
                list_skipToEndSk.append(sko)
            #Далее обрабатываются пропущенные на предыдущем цикле.
            for li in list_skipToEndEq:
                sko = li[0].tar
                ski = li[1].tar
                if ski in set_alreadyDone:
                    continue
                set_alreadyDone.add(ski)
                tree.links.new(sko, ski)
                VlrtRememberLastSockets(sko, ski)
        else:
            for li in self.list_equalFtgSks:
                tree.links.new(li[0].tar, li[1].tar) #Соединить всех!
    def InitTool(self, event, prefs, tree):
        self.ndTar0 = None
        self.ndTar1 = None
        self.list_equalFtgSks = []
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vmltIgnoreCase')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isIgnoreExistingLinks').name) as dm:
            dm[ru_RU] = "Игнорировать существующие связи"
            dm[zh_CN] = "忽略现有链接"
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vmltIgnoreCase').name) as dm:
            dm[ru_RU] = "Игнорировать регистр"
            dm[zh_CN] = "忽略端口名称的大小写"

SmartAddToRegAndAddToKmiDefs(VoronoiMassLinkerTool, "SCA_LEFTMOUSE")
SmartAddToRegAndAddToKmiDefs(VoronoiMassLinkerTool, "SCA_RIGHTMOUSE", {'isIgnoreExistingLinks':True})
dict_setKmiCats['oth'].add(VoronoiMassLinkerTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vmltIgnoreCase: bpy.props.BoolProperty(name="Ignore case", default=True)

with VlTrMapForKey(VoronoiMassLinkerTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi根据端口名批量快速连接"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiMassLinkerTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiMassLinkerTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiMassLinkerTool.bl_label}根据端口名批量连接设置:"

dict_toolLangSpecifDataPool[VoronoiMassLinkerTool, ru_RU] = """"Малыш котопёс", не ноды, не сокеты. Создан ради редких точечных спец-ускорений.
VLT на максималках. В связи со своим принципом работы, по своему божественен."""

class VestData:
    list_enumProps = [] #Для пайки, и проверка перед вызовом, есть ли вообще что.
    nd = None
    boxScale = 1.0 #Если забыть установить, то хотя бы коробка не сколлапсируется в ноль.
    isDarkStyle = False
    isDisplayLabels = False
    isPieChoice = False

class VoronoiEnumSelectorTool(VoronoiToolNd):
    bl_idname = 'node.voronoi_enum_selector'
    bl_label = "Voronoi Enum Selector"
    usefulnessForCustomTree = True
    canDrawInAppearance = True
    isInstantActivation: bpy.props.BoolProperty(name="Instant activation",  default=True,  description="Skip drawing to a node and activation when release, and activate immediately when pressed")
    isPieChoice:         bpy.props.BoolProperty(name="Pie choice",          default=False, description="Allows to select an enum by releasing the key")
    isToggleOptions:     bpy.props.BoolProperty(name="Toggle node options", default=False)
    isSelectNode:        bpy.props.IntProperty(name="Select target node",  default=1, min=0, max=3, description="0 – Do not select.\n1 – Select.\n2 – And center.\n3 – And zooming")
    def ToggleOptionsFromNode(self, nd, lastResult, isCanDo=False): #Принцип работы скопирован с VHT HideFromNode()'a.
        if lastResult:
            success = nd.show_options
            if isCanDo:
                nd.show_options = False
            return success
        elif isCanDo:
            success = not nd.show_options
            nd.show_options = True
            return success
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE': #Для этого инструмента рероуты пропускаются, по очевидным причинам.
                continue
            if nd.bl_idname in set_utilEquestrianPortalBlids: #Игнорировать всех всадников.
                continue
            if nd.hide: #У свёрнутых нодов результат переключения не увидеть, поэтому игнорировать.
                continue
            if self.isToggleOptions:
                self.fotagoNd = ftgNd
                #Смысл такой же, как и в VHT:
                if prefs.vestIsToggleNodesOnDrag:
                    if self.firstResult is None:
                        self.firstResult = self.ToggleOptionsFromNode(nd, True)
                    self.ToggleOptionsFromNode(nd, self.firstResult, True)
                break
            elif GetListOfNdEnums(nd): #Почему бы не игнорировать ноды без енум-свойств?.
                self.fotagoNd = ftgNd
                break
    def DoActivation(self, prefs, tree):
        def IsPtInRect(pos, rect): #return (pos[0]>rect[0])and(pos[1]>rect[1])and(pos[0]<rect[2])and(pos[1]>rect[3])
            if pos[0]<rect[0]:
                return False
            elif pos[1]<rect[1]:
                return False
            elif pos[0]>rect[2]:
                return False
            elif pos[1]>rect[3]:
                return False
            return True
        VestData.list_enumProps = GetListOfNdEnums(self.fotagoNd.tar)
        #Если ничего нет, то вызов коробки всё равно обрабатывается, словно она есть, и от чего повторный вызов инструмента не работает без движения курсора.
        if VestData.list_enumProps: #Поэтому если пусто, то ничего не делаем. А ещё assert в VestLyAddEnumSelectorBox().
            ndTar = self.fotagoNd.tar
            VestData.nd = ndTar
            VestData.boxScale = prefs.vestBoxScale
            VestData.isDarkStyle = prefs.vestDarkStyle
            VestData.isDisplayLabels = prefs.vestDisplayLabels
            VestData.isPieChoice = self.isPieChoice
            if self.isSelectNode:
                SelectAndActiveNdOnly(VestData.nd)
                if self.isSelectNode>1:
                    #Определить, если нод находится за пределами экрана; и только тогда центрировать:
                    region = self.region
                    vec = ndTar.location.copy()
                    tup1 = region.view2d.view_to_region(vec.x, vec.y, clip=False)
                    vec.x += ndTar.dimensions.x
                    vec.y -= ndTar.dimensions.y
                    tup2 = region.view2d.view_to_region(vec.x, vec.y, clip=False)
                    rect = (region.x, region.y, region.width, region.height)
                    if not(IsPtInRect(tup1, rect) and IsPtInRect(tup2, rect)):
                        if self.isSelectNode==3:
                            #"Хак", (но нужно ещё перерисовать):
                            rr1 = tree.nodes.new('NodeReroute')
                            rr1.location = (ndTar.location.x-360, ndTar.location.y)
                            rr2 = tree.nodes.new('NodeReroute')
                            rr2.location = (ndTar.location.x+360, ndTar.location.y)
                            bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
                        bpy.ops.node.view_selected('INVOKE_DEFAULT')
                        if self.isSelectNode==3:
                            tree.nodes.remove(rr1)
                            tree.nodes.remove(rr2)
            if self.isPieChoice:
                bpy.ops.wm.call_menu_pie(name=VestPieBox.bl_idname)
            else:
                bpy.ops.node.voronoi_enum_selector_box('INVOKE_DEFAULT')
            return True #Для modal(), чтобы вернуть успех.
    def MatterPurposeTool(self, event, prefs, tree):
        if self.isToggleOptions:
            if not prefs.vestIsToggleNodesOnDrag: #И тут так же, как и в VHT.
                self.ToggleOptionsFromNode(self.fotagoNd.tar, self.ToggleOptionsFromNode(self.fotagoNd.tar, True), True)
        else:
            if not self.isInstantActivation:
                self.DoActivation(prefs, tree)
    def InitTool(self, event, prefs, tree):
        if (self.isInstantActivation)and(not self.isToggleOptions):
            #Заметка: Коробка может полностью закрыть нод вместе с линией к нему.
            self.NextAssignmentRoot(None)
            if not self.fotagoNd:
                return {'CANCELLED'}
            self.DoActivation(prefs, tree)
            return {'FINISHED'} #Важно завершить инструмент.
        self.firstResult = None #В идеале тоже перед выше, но не обязательно, см. топологию isToggleOptions.
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddLeftProp(col, prefs,'vestIsToggleNodesOnDrag')
    @staticmethod
    def LyDrawInAppearance(colLy, prefs): #Заметка: Это @staticmethod.
        colBox = LyAddLabeledBoxCol(colLy, text=TranslateIface("Box ").strip()+" (VEST)")
        LyAddHandSplitProp(colBox, prefs,'vestBoxScale')
        LyAddHandSplitProp(colBox, prefs,'vestDisplayLabels')
        LyAddHandSplitProp(colBox, prefs,'vestDarkStyle')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey("Box ") as dm:
            dm[ru_RU] = "Коробка"
        ##
        with VlTrMapForKey(GetAnnotFromCls(cls,'isInstantActivation').name) as dm:
            dm[ru_RU] = "Моментальная активация"
            dm[zh_CN] = "直接打开饼菜单"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isInstantActivation').description) as dm:
            dm[ru_RU] = "Пропустить рисование к ноду и активацию при отпускании, и активировать немедленно при нажатии"
            dm[zh_CN] = "不勾选可以先根据鼠标位置动态选择节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPieChoice').name) as dm:
            dm[ru_RU] = "Выбор пирогом"
            dm[zh_CN] = "饼菜单选择"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isPieChoice').description) as dm:
            dm[ru_RU] = "Позволяет выбрать элемент отпусканием клавиши"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetAnnotFromCls(cls,'isToggleOptions').name) as dm:
            dm[ru_RU] = "Переключение опций нода"
#            dm[zh_CN] = "隐藏节点里的下拉列表"?
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNode').name) as dm:
            dm[ru_RU] = "Выделять целевой нод"
            dm[zh_CN] = "选择目标节点"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectNode').description) as dm:
            dm[ru_RU] = "0 – Не выделять.\n1 – Выделять.\n2 – и центрировать.\n3 – и приближать"
#            dm[zh_CN] = ""
        ##
        #* Перевод vestIsToggleNodesOnDrag уже есть в VHT *
        with VlTrMapForKey(GetPrefsRnaProp('vestBoxScale').name) as dm:
            dm[ru_RU] = "Масштаб панели"
            dm[zh_CN] = "下拉列表面板大小"
        with VlTrMapForKey(GetPrefsRnaProp('vestDisplayLabels').name) as dm:
            dm[ru_RU] = "Отображать имена свойств перечислений"
            dm[zh_CN] = "显示下拉列表属性名称"
        with VlTrMapForKey(GetPrefsRnaProp('vestDarkStyle').name) as dm:
            dm[ru_RU] = "Тёмный стиль"
            dm[zh_CN] = "暗色风格"

#Изначально хотел 'V_Sca', но слишком далеко тянуться пальцем до V. И вообще, учитывая причину создания этого инструмента, нужно минимизировать сложность вызова.
SmartAddToRegAndAddToKmiDefs(VoronoiEnumSelectorTool, "###_F", {'isPieChoice':True, 'isSelectNode':3})
SmartAddToRegAndAddToKmiDefs(VoronoiEnumSelectorTool, "S##_F", {'isInstantActivation':False})
SmartAddToRegAndAddToKmiDefs(VoronoiEnumSelectorTool, "##A_F", {'isToggleOptions':True})
dict_setKmiCats['oth'].add(VoronoiEnumSelectorTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vestIsToggleNodesOnDrag: bpy.props.BoolProperty(name="Toggle nodes on drag", default=True)
    ##
    vestBoxScale:            bpy.props.FloatProperty(name="Box scale",           default=1.5, min=1.0, max=2.0, subtype="FACTOR")
    vestDisplayLabels:       bpy.props.BoolProperty(name="Display enum names",   default=True)
    vestDarkStyle:           bpy.props.BoolProperty(name="Dark style",           default=False)

with VlTrMapForKey(VoronoiEnumSelectorTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速切换节点内部下拉列表"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiEnumSelectorTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiEnumSelectorTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiEnumSelectorTool.bl_label}快速显示节点里下拉列表设置:"

dict_toolLangSpecifDataPool[VoronoiEnumSelectorTool, ru_RU] = """Инструмент для удобно-ленивого переключения свойств перечисления.
Избавляет от прицеливания мышкой, клика, а потом ещё одного прицеливания и клика."""

def VestLyAddEnumSelectorBox(where, lyDomain=None):
    assert VestData.list_enumProps
    colMain = where.column()
    colDomain = lyDomain.column() if lyDomain else None
    nd = VestData.nd
    #Нод математики имеет высокоуровневое разбиение на категории для .prop(), но как показать их вручную простым перечислением я не знаю. И вообще, VQMT.
    #Игнорировать их не стал, пусть обрабатываются как есть. И с ними даже очень удобно выбирать операцию векторной математики (обычная не влезает).
    #Домен всегда первым. Например, StoreNamedAttribute и FieldAtIndex имеют одинаковые енумы, но в разном порядке; интересно почему.
    for cyc, li in enumerate(sorted(VestData.list_enumProps, key=lambda a:a.identifier!='domain')):
        if (cyc)and(colWhere!=colDomain):
            colProp.separator()
        colWhere = (colDomain if (lyDomain)and(li.identifier=='domain') else colMain)
        colProp = colWhere.column(align=True)
        if VestData.isDisplayLabels:
            rowLabel = colProp.row(align=True)
            rowLabel.alignment = 'CENTER'
            rowLabel.label(text=li.name)
            #rowLabel.active = not VestData.isPieChoice #Для пирога рамка прозрачная, от чего текст может сливаться с яркими нодами на фоне. Так что выключено.
            rowLabel.active = not(VestData.isDarkStyle and VestData.isPieChoice) #Но для тёмного пирога всё-таки отобразить их тёмными.
        elif cyc:
            colProp.separator()
        colEnum = colProp.column(align=True)
        colEnum.scale_y = VestData.boxScale
        if VestData.isDarkStyle:
            colEnum.prop_tabs_enum(nd, li.identifier)
        else:
            colEnum.prop(nd, li.identifier, expand=True)
    #В своей первой задумке я неправильно назвал этот инструмент -- "Prop Selector". Нужно придумать как отличить общие свойства нода от тех, которые рисуются у него в опциях.
    #Повезло, что у каждого нода енумов нет разных...
class VestOpBox(VoronoiOpTool):
    bl_idname = 'node.voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def execute(self, _context): #Для draw() ниже, иначе не отобразится.
        pass
    def draw(self, _context):
        VestLyAddEnumSelectorBox(self.layout)
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=int(128*VestData.boxScale))
class VestPieBox(bpy.types.Menu):
    bl_idname = 'VL_MT_Voronoi_enum_selector_box'
    bl_label = "Enum Selector"
    def draw(self, _context):
        pie = self.layout.menu_pie()
        def GetCol(where, tgl=True):
            col = (where.box() if tgl else where).column()
            col.ui_units_x = 7*((VestData.boxScale-1)/2+1)
            return col
        colDom = GetCol(pie, any(True for li in VestData.list_enumProps if li.identifier=='domain'))
        colAll = GetCol(pie, any(True for li in VestData.list_enumProps if li.identifier!='domain'))
        VestLyAddEnumSelectorBox(colAll, colDom)

list_classes += [VestOpBox, VestPieBox]

#См.: VlrtData, VlrtRememberLastSockets() и NewLinkHhAndRemember().

fitVlrtModeItems = ( ('SOCKET', "For socket", "Using the last link created by some from the tools, create the same for the specified socket."),
                     ('NODE',   "For node",   "Using name of the last socket, find and connect for a selected node.") )
class VoronoiLinkRepeatingTool(VoronoiToolAny): #Вынесено в отдельный инструмент, чтобы не осквернять святая святых спагетти-кодом (изначально был только для VLT).
    bl_idname = 'node.voronoi_link_repeating'
    bl_label = "Voronoi Link Repeating"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    toolMode: bpy.props.EnumProperty(name="Mode", default='SOCKET', items=fitVlrtModeItems)
    def CallbackDrawTool(self, drata):
        self.TemplateDrawAny(drata, self.fotagoAny, cond=self.toolMode=='NODE')
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        def IsSkBetweenFields(sk1, sk2):
            return (sk1.type in set_utilTypeSkFields)and( (sk2.type in set_utilTypeSkFields)or(sk1.type==sk2.type) )
        skLastOut = self.skLastOut
        skLastIn = self.skLastIn
        if not skLastOut:
            return
        SolderSkLinks(tree) #Вроде и без перепайки работает.
        self.fotagoAny = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd==skLastOut.node: #Исключить само-нод.
                break #continue
            if self.toolMode=='SOCKET':
                list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
                if skLastOut:
                    for ftg in list_ftgSksIn:
                        if (skLastOut.bl_idname==ftg.blid)or(IsSkBetweenFields(skLastOut, ftg.tar)):
                            can = True
                            for lk in ftg.tar.vl_sold_links_final:
                                if lk.from_socket==skLastOut: #Определить уже имеющийся линк, и не выбирать таковой сокет.
                                    can = False
                            if can:
                                self.fotagoAny = ftg
                                break
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoAny, flag=False)
            else:
                if skLastIn:
                    if nd.inputs:
                        self.fotagoAny = ftgNd
                    for sk in nd.inputs:
                        if CompareSkLabelName(sk, skLastIn):
                            if (sk.enabled)and(not sk.hide):
                                tree.links.new(skLastOut, sk) #Заметка: Не высокоуровневый; зачем для повторения по нодам нужны интерфейсы?.
            break
    def MatterPurposeTool(self, event, prefs, tree):
        if self.toolMode=='SOCKET':
            #Здесь нет нужды проверять на одинаковость дерева сокетов, проверка на это уже есть в NextAssignmentTool().
            #Также нет нужды проверять существование skLastOut, см. его топологию в NextAssignmentTool().
            #Заметка: Проверка одинаковости `.id_data` имеется у VlrtRememberLastSockets().
            #Заметка: Нет нужды проверять существование дерева, потому что если прицепившийся сокет тут существует, то уже где-то.
            DoLinkHh(self.skLastOut, self.fotagoAny.tar)
            VlrtRememberLastSockets(self.skLastOut, self.fotagoAny.tar) #Потому что. И вообще.. "саморекурсия"?.
    def InitTool(self, event, prefs, tree):
        for txt in "Out", "In":
            txtAttSkLast = 'skLast'+txt
            txtAttReprLastSk = 'reprLastSk'+txt #В случае неудачи записывать ничего.
            setattr(self, txtAttSkLast, None) #Инициализировать для инструмента и присвоить ниже.
            if reprTxtSk:=getattr(VlrtData, txtAttReprLastSk):
                try:
                    sk = eval(reprTxtSk)
                    if sk.id_data==tree:
                        setattr(self, txtAttSkLast, sk)
                    else:
                        setattr(VlrtData, txtAttReprLastSk, "")
                except:
                    setattr(VlrtData, txtAttReprLastSk, "")
        #Заметка: Оказывается, Ctrl Z делает (глобально сохранённую) ссылку на tree 'ReferenceError: StructRNA of type ShaderNodeTree has been removed'.
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.SOCKET.name) as dm:
            dm[ru_RU] = "Для сокета"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SOCKET.description) as dm:
            dm[ru_RU] = "Используя последний линк, созданный каким-н. из инструментов, создать такой же для указанного сокета."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.NODE.name) as dm:
            dm[ru_RU] = "Для нода"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.NODE.description) as dm:
            dm[ru_RU] = "Используя имя последнего сокета, найти и соединить для выбранного нода."
            dm[zh_CN] = "鼠标移动到节点旁自动恢复节点的连接"

SmartAddToRegAndAddToKmiDefs(VoronoiLinkRepeatingTool, "###_V", {'toolMode':'SOCKET'})
SmartAddToRegAndAddToKmiDefs(VoronoiLinkRepeatingTool, "S##_V", {'toolMode':'NODE'})
dict_setKmiCats['oth'].add(VoronoiLinkRepeatingTool.bl_idname)

with VlTrMapForKey(VoronoiLinkRepeatingTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi重复连接到上次用快速连接到的输出端" #dm[zh_CN] = "Voronoi快速恢复连接"

dict_toolLangSpecifDataPool[VoronoiLinkRepeatingTool, ru_RU] = """Полноценное ответвление от VLT, повторяет любой предыдущий линк от большинства
других инструментов. Обеспечивает удобство соединения "один ко многим"."""

class VoronoiQuickDimensionsTool(VoronoiToolTripleSk):
    bl_idname = 'node.voronoi_quick_dimensions'
    bl_label = "Voronoi Quick Dimensions"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    isPlaceImmediately: bpy.props.BoolProperty(name="Place immediately", default=False)
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1, self.fotagoSk2)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoSk0 = None
        if not self.canPickThird:
            self.fotagoSk1 = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksOut = self.ToolGetNearestSockets(nd)[1]
            if not list_ftgSksOut:
                continue
            if isFirstActivation:
                for ftg in list_ftgSksOut:
                    if (ftg.tar.type in set_utilTypeSkFields)or(ftg.tar.type=='GEOMETRY'):
                        self.fotagoSk0 = ftg
                        break
                CheckUncollapseNodeAndReNext(nd, self, cond=True, flag=True)
                break
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            skOut0 = FtgGetTargetOrNone(self.fotagoSk0)
            if skOut0:
                if skOut0.type not in {'VALUE','INT','BOOLEAN'}:
                    break
                if not self.canPickThird:
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==skOut0.type:
                            self.fotagoSk1 = ftg
                            break
                    if (self.fotagoSk1)and(self.fotagoSk1.tar==skOut0):
                        self.fotagoSk1 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
                    if self.fotagoSk1:
                        break
                else:
                    skOut1 = FtgGetTargetOrNone(self.fotagoSk1)
                    for ftg in list_ftgSksOut:
                        if ftg.tar.type==skOut0.type:
                            self.fotagoSk2 = ftg
                            break
                    if (self.fotagoSk2)and( (self.fotagoSk2.tar==skOut0)or(skOut1)and(self.fotagoSk2.tar==skOut1) ):
                        self.fotagoSk2 = None
                        break
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk2, flag=False)
                    if self.fotagoSk2:
                        break
    def MatterPurposePoll(self):
        return not not self.fotagoSk0
    def MatterPurposeTool(self, event, prefs, tree):
        skOut0 = self.fotagoSk0.tar
        dict_qDM = dict_vqdtQuickDimensionsMain.get(tree.bl_idname, None)
        if not dict_qDM:
            return {'CANCELLED'}
        isOutNdCol = skOut0.node.bl_idname==dict_qDM['RGBA'][0] #Заметка: Нод разделения; на выходе всегда флоаты.
        isGeoTree = tree.bl_idname=='GeometryNodeTree'
        isOutNdQuat = (isGeoTree)and(skOut0.node.bl_idname==dict_qDM['ROTATION'][0])
        #Добавить:
        bpy.ops.node.add_node('INVOKE_DEFAULT', type=dict_qDM[skOut0.type][isOutNdCol if not isOutNdQuat else 2], use_transform=not self.isPlaceImmediately)
        aNd = tree.nodes.active
        aNd.width = 140
        if aNd.bl_idname in {dict_qDM['RGBA'][0], dict_qDM['VALUE'][1]}: #|3|.
            aNd.show_options = False #Как-то неэстетично прятать без разбору, поэтому проверка выше.
        if skOut0.type in {'VECTOR', 'RGBA', 'ROTATION'}: #Зато экономия явных определений для каждого типа.
            aNd.inputs[0].hide_value = True
        #Установить одинаковость режимов (например, RGB и HSV):
        for li in GetListOfNdEnums(aNd):
            if hasattr(skOut0.node, li.identifier):
                setattr(aNd, li.identifier, getattr(skOut0.node, li.identifier))
        #Соединить:
        skIn = aNd.inputs[0]
        for ski in aNd.inputs:
            if skOut0.name==ski.name:
                skIn = ski
                break
        NewLinkHhAndRemember(skOut0, skIn)
        if self.fotagoSk1:
            NewLinkHhAndRemember(self.fotagoSk1.tar, aNd.inputs[1])
        if self.fotagoSk2:
            NewLinkHhAndRemember(self.fotagoSk2.tar, aNd.inputs[2])

SmartAddToRegAndAddToKmiDefs(VoronoiQuickDimensionsTool, "##A_D")
dict_setKmiCats['spc'].add(VoronoiQuickDimensionsTool.bl_idname)

with VlTrMapForKey(VoronoiQuickDimensionsTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速分离/合并 矢量/颜色"

dict_toolLangSpecifDataPool[VoronoiQuickDimensionsTool, ru_RU] = "Инструмент для ускорения нужд разделения и объединения векторов (и цвета).\nА ещё может разделить геометрию на составляющие."

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
                              'VALUE':    ('TextureNodeCombineColor',''), #Нет обработок отсутствия второго, поэтому пусто; см. |3|.
                              'INT':      ('TextureNodeCombineColor',)}}

def FindAnySk(nd, list_ftgSksIn, list_ftgSksOut): #Todo0NA нужно обобщение!, с лямбдой. И внешний цикл по спискам, а не два цикла.
    ftgSkOut, ftgSkIn = None, None
    for ftg in list_ftgSksOut:
        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
            ftgSkOut = ftg
            break
    for ftg in list_ftgSksIn:
        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
            ftgSkIn = ftg
            break
    return MinFromFtgs(ftgSkOut, ftgSkIn)

fitVitModeItems = ( ('COPY',   "Copy",   "Copy a socket name to clipboard."),
                    ('PASTE',  "Paste",  "Paste the contents of clipboard into an interface name."),
                    ('SWAP',   "Swap",   "Swap a two interfaces."),
                    ('FLIP',   "Flip",   "Move the interface to a new location, shifting everyone else."),
                    ('NEW',    "New",    "Create an interface using virtual sockets."),
                    ('CREATE', "Create", "Create an interface from a selected socket, and paste it into a specified location.") )
class VoronoiInterfacerTool(VoronoiToolPairSk):
    bl_idname = 'node.voronoi_interfacer'
    bl_label = "Voronoi Interfacer"
    usefulnessForCustomTree = False
    canDrawInAddonDiscl = False
    toolMode: bpy.props.EnumProperty(name="Mode", default='NEW', items=fitVitModeItems)
    def CallbackDrawTool(self, drata):
        match self.toolMode:
            case 'NEW':
                TemplateDrawSksToolHh(drata, self.fotagoSkRosw, self.fotagoSkMain, isClassicFlow=True)
            case 'CREATE':
                ftgMain = self.fotagoSkMain
                if ftgMain:
                    TemplateDrawSksToolHh(drata, ftgMain, isFlipSide=True)
                ftgNdTar = self.fotagoNdTar
                if ftgNdTar:
                    TemplateDrawNodeFull(drata, ftgNdTar)
                if not(ftgNdTar and ftgMain):
                    TemplateDrawSksToolHh(drata, None)
            case _:
                TemplateDrawSksToolHh(drata, self.fotagoSkMain, self.fotagoSkRosw)
    def NextAssignmentToolCopyPaste(self, _isFirstActivation, prefs, tree):
        self.fotagoSkMain = None
        if (self.toolMode=='PASTE')and(not self.clipboard): #Ожидаемо; а ещё #https://projects.blender.org/blender/blender/issues/113860
            return #Todo0VV пройтись по версиям и указать, в каких крашится.
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if (self.toolMode=='PASTE')and(nd.type not in Equestrian.set_equestrianNodeTypes):
                continue #Курсор должен быть рядом со всадником (или групповым нодом). А ещё с `continue` не будет высокоуровневой отмены.
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            self.fotagoSkMain = FindAnySk(nd, list_ftgSksIn, list_ftgSksOut)
            if self.fotagoSkMain:
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkMain.tar.node==nd, flag=True)
            break
    def NextAssignmentToolSwapFlip(self, isFirstActivation, prefs, tree):
        self.fotagoSkMain = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if nd.type not in Equestrian.set_equestrianNodeTypes:
                continue #Курсор должен быть рядом со всадником (или групповым нодом). А ещё с `continue` не будет высокоуровневой отмены.
            if (self.fotagoSkRosw)and(self.fotagoSkRosw.tar.node!=nd):
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            if isFirstActivation:
                self.fotagoSkRosw = FindAnySk(nd, list_ftgSksIn, list_ftgSksOut)
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkRosw, flag=True)
            skRosw = FtgGetTargetOrNone(self.fotagoSkRosw)
            if skRosw:
                for ftg in list_ftgSksOut if skRosw.is_output else list_ftgSksIn:
                    if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
                        self.fotagoSkMain = ftg
                        break
                if (self.fotagoSkMain)and(self.fotagoSkMain.tar==skRosw):
                    self.fotagoSkMain = None
            break
    def NextAssignmentToolNewCreate(self, isFirstActivation, prefs, tree):
        set_eqSimRepBlids = {'GeometryNodeSimulationInput', 'GeometryNodeSimulationOutput', 'GeometryNodeRepeatInput', 'GeometryNodeRepeatOutput'}
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            match self.toolMode:
                case 'NEW':
                    self.fotagoSkMain = None
                    if isFirstActivation:
                        self.fotagoSkRosw = None
                        for ftg in list_ftgSksOut:
                            self.fotagoSkRosw = ftg
                            self.tglCrossVirt = ftg.blid=='NodeSocketVirtual'
                            break
                        CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkRosw, flag=True)
                    skRosw = FtgGetTargetOrNone(self.fotagoSkRosw)
                    if skRosw:
                        for ftg in list_ftgSksIn:
                            if (ftg.blid=='NodeSocketVirtual')^self.tglCrossVirt:
                                self.fotagoSkMain = ftg
                                break
                        if (self.fotagoSkMain)and(self.fotagoSkMain.tar.node==skRosw.node): #todo0NA обобщить такую проверку для всех; мб в класс.
                            self.fotagoSkMain = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSkMain, flag=True)
                case 'CREATE':
                    if isFirstActivation:
                        ftgSkOut, ftgSkIn = None, None
                        for ftg in list_ftgSksIn:
                            if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
                                ftgSkIn = ftg
                                break
                        for ftg in list_ftgSksOut:
                            if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(nd, ftg.tar)):
                                ftgSkOut = ftg
                                break
                        self.fotagoSkMain = MinFromFtgs(ftgSkOut, ftgSkIn)
                    self.fotagoNdTar = None
                    skMain = FtgGetTargetOrNone(self.fotagoSkMain)
                    if skMain:
                        if nd==skMain.node: #Можно было бы и разрешить из своего нода тоже, но наверное лучше не стоит.
                            break
                        if nd.type not in Equestrian.set_equestrianNodeTypes:
                            continue
                        self.fotagoNdTar = ftgNd
            break
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        match self.toolMode:
            case 'COPY'|'PASTE':
                self.NextAssignmentToolCopyPaste(isFirstActivation, prefs, tree)
            case 'SWAP'|'FLIP':
                self.NextAssignmentToolSwapFlip(isFirstActivation, prefs, tree)
            case 'NEW'|'CREATE':
                self.NextAssignmentToolNewCreate(isFirstActivation, prefs, tree)
    def MatterPurposePoll(self):
        match self.toolMode:
            case 'COPY'|'PASTE':
                return not not self.fotagoSkMain
            case 'SWAP'|'FLIP':
                return self.fotagoSkRosw and self.fotagoSkMain
            case 'NEW':
                for dk, dv in self.dict_ndHidingVirtualIn.items():
                    dk.inputs[-1].hide = dv
                for dk, dv in self.dict_ndHidingVirtualOut.items():
                    dk.outputs[-1].hide = dv
                return self.fotagoSkRosw and self.fotagoSkMain
            case 'CREATE':
                return self.fotagoSkMain and self.fotagoNdTar
    def MatterPurposeTool(self, event, prefs, tree):
        match self.toolMode:
            case 'COPY':
                self.clipboard = GetSkLabelName(self.fotagoSkMain.tar)
            case 'PASTE':
                skMain = self.fotagoSkMain.tar
                Equestrian(skMain).GetSkfFromSk(skMain).name = self.clipboard
            case 'SWAP'|'FLIP':
                skMain = self.fotagoSkMain.tar
                equr = Equestrian(skMain)
                skfFrom = equr.GetSkfFromSk(self.fotagoSkRosw.tar)
                skfTo = equr.GetSkfFromSk(skMain)
                equr.MoveBySkfs(skfFrom, skfTo, isSwap=self.toolMode=='SWAP')
            case 'NEW':
                DoLinkHh(self.fotagoSkRosw.tar, self.fotagoSkMain.tar)
            case 'CREATE':
                ftgNdTar = self.fotagoNdTar
                ndTar = ftgNdTar.tar
                equr = Equestrian(ndTar)
                skMain = self.fotagoSkMain.tar
                skfNew = equr.NewSkfFromSk(skMain, isFlipSide=ndTar.type not in {'GROUP_INPUT', 'GROUP_OUTPUT'})
                can = True
                if not equr.is_simrep:
                    for skf in equr.skfa:
                        if skf.item_type=='PANEL': #Нахрен эту головную боль. Шатайтесь с этим сами, а мне уже лень.
                            can = False #|4|.
                            break
                if can: #tovo0v6 и панели тоже.
                    nameSn = skfNew.name
                    ftgNearest = None# MinFromFtgs(list_ftgSksIn[0] if list_ftgSksIn else None, list_ftgSksOut[0] if list_ftgSksOut else None)
                    min = 16777216.0
                    list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(ndTar)
                    for ftg in list_ftgSksIn if skMain.is_output else list_ftgSksOut:
                        if (ftg.blid!='NodeSocketVirtual')and(Equestrian.IsSimRepCorrectSk(ndTar, ftg.tar)):
                            len = (ftgNdTar.pos-ftg.pos).length
                            if min>len:
                                min = len
                                ftgNearest = ftg
                    if ftgNearest:
                        skfTo = equr.GetSkfFromSk(ftgNearest.tar)
                        equr.MoveBySkfs(skfNew, skfTo, isSwap=False)
                        if (ftgNdTar.pos.y<ftgNearest.pos.y): #'True' -- далее по списку в группе, а не мироориентация.
                            if equr.is_simrep:
                                equr.MoveBySkfs(equr.GetSkfFromSk(ftgNearest.tar), skfTo, isSwap=None) #Осторожнее с skfTo.
                            else:
                                equr.MoveBySkfs(skfNew, skfTo, isSwap=None) #Гениально!
                if equr.is_simrep:
                    tree.links.new(skMain, equr.GetSkFromSkf(equr.skfa.get(nameSn), isOut=not skMain.is_output))
                else:
                    tree.links.new(skMain, equr.GetSkFromSkf(skfNew, isOut=(skfNew.in_out=='OUTPUT')^(equr.type!='GROUP')))
    def InitTool(self, event, prefs, tree):
        self.fotagoSkMain = None
        self.fotagoSkRosw = None #RootSwap
        match self.toolMode:
            case 'NEW':
                self.dict_ndHidingVirtualIn = {}
                self.dict_ndHidingVirtualOut = {}
                #self.NextAssignmentRoot(True)
                #if self.fotagoSkRosw:
                #    nd = self.fotagoSkRosw.tar.node
                #    self.dict_ndHidingVirtualOut[nd] = nd.outputs[-1].hide
                #    nd.outputs[-1].hide = False
                #    self.NextAssignmentRoot(True)
                #    if self.fotagoSkRosw:
                #        tgl = self.fotagoSkRosw.blid!='NodeSocketVirtual'
                if True: #todo1v6 что-нибудь придумать с этим ради эстетики.
                        for nd in tree.nodes:
                            if nd.bl_idname in set_utilEquestrianPortalBlids:
                                if nd.inputs:
                                    self.dict_ndHidingVirtualIn[nd] = nd.inputs[-1].hide
                                    nd.inputs[-1].hide = False
                                if nd.outputs:
                                    self.dict_ndHidingVirtualOut[nd] = nd.outputs[-1].hide
                                    nd.outputs[-1].hide = False
                self.tglCrossVirt = None
                #Какой-то баг, если не перерисовать, то первый найденный виртуальный не сможет выбраться корректно.
                bpy.ops.wm.redraw_timer(type='DRAW', iterations=0)
            case 'CREATE':
                self.fotagoNdTar = None #Омг.
        VoronoiInterfacerTool.clipboard = property(lambda _:bpy.context.window_manager.clipboard, lambda _,v:setattr(bpy.context.window_manager,'clipboard', v))
    @classmethod
    def BringTranslations(cls):
        tran = GetAnnotFromCls(cls,'toolMode').items
        with VlTrMapForKey(tran.COPY.name) as dm:
            dm[ru_RU] = "Копировать"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.COPY.description) as dm:
            dm[ru_RU] = "Копировать имя сокета в буфер обмена."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.PASTE.name) as dm:
            dm[ru_RU] = "Вставить"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.PASTE.description) as dm:
            dm[ru_RU] = "Вставить содержимое буфера обмена в имя интерфейса."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SWAP.name) as dm:
            dm[ru_RU] = "Поменять местами"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.SWAP.description) as dm:
            dm[ru_RU] = "Поменять местами два интерфейса."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.FLIP.name) as dm:
            dm[ru_RU] = "Сдвинуть"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.FLIP.description) as dm:
            dm[ru_RU] = "Переместить интерфейс на новое место, сдвигая всех остальных."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.NEW.name) as dm:
            dm[ru_RU] = "Добавить"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.NEW.description) as dm:
            dm[ru_RU] = "Добавить интерфейс с помощью виртуальных сокетов."
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.CREATE.name) as dm:
            dm[ru_RU] = "Создать"
#            dm[zh_CN] = ""
        with VlTrMapForKey(tran.CREATE.description) as dm:
            dm[ru_RU] = "Создать интерфейс из выбранного сокета, и вставить его на указанное место."
#            dm[zh_CN] = ""

SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "SC#_A", {'toolMode':'NEW'})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_A", {'toolMode':'CREATE'})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_C", {'toolMode':'COPY'})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_V", {'toolMode':'PASTE'})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_X", {'toolMode':'SWAP'})
SmartAddToRegAndAddToKmiDefs(VoronoiInterfacerTool, "S#A_Z", {'toolMode':'FLIP'})
dict_setKmiCats['spc'].add(VoronoiInterfacerTool.bl_idname)

with VlTrMapForKey(VoronoiInterfacerTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi在节点组里快速复制粘贴端口名给节点组输入输出端"

dict_toolLangSpecifDataPool[VoronoiInterfacerTool, ru_RU] = """Инструмент на уровне "The Great Trio". Ответвление от VLT ради удобного ускорения
процесса создания и спец-манипуляций с интерфейсами. "Менеджер интерфейсов"."""

class VoronoiLinksTransferTool(VoronoiToolPairNd): #Todo2v6 кандидат на слияние с VST и превращение в "PairAny".
    bl_idname = 'node.voronoi_links_transfer'
    bl_label = "Voronoi Links Transfer"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    isByIndexes: bpy.props.BoolProperty(name="Transfer by indexes", default=False)
    def CallbackDrawTool(self, drata):
        #Паттерн VLT
        if not self.fotagoNd0:
            TemplateDrawSksToolHh(drata, None)
        elif (self.fotagoNd0)and(not self.fotagoNd1):
            TemplateDrawNodeFull(drata, self.fotagoNd0, side=-1)
            TemplateDrawSksToolHh(drata, None)
        else:
            TemplateDrawNodeFull(drata, self.fotagoNd0, side=-1)
            TemplateDrawNodeFull(drata, self.fotagoNd1, side=1)
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        if isFirstActivation:
            self.fotagoNd0 = None
        self.fotagoNd1 = None
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=False):
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            if isFirstActivation:
                self.fotagoNd0 = ftgNd
            self.fotagoNd1 = ftgNd
            if self.fotagoNd0.tar==self.fotagoNd1.tar:
                self.fotagoNd1 = None
            #Свершилось. Теперь у VL есть два нода.
            #Внезапно оказалось, что позиция "попадания" для нода буквально прилипает к нему, что весьма необычно наблюдать, когда тут вся тусовка про сокеты.
            # Должна ли она скользить вместо прилипания?. Скорее всего нет, ведь иначе неизбежны осеориентированные проекции, визуально "затирающие" информацию.
            # А также они оба будут изменяться от движения курсора, от чего не будет интуитивно понятно, кто первый, а кто второй,
            # В отличие от прилипания, когда точно понятно, что "вот этот вот первый"; что особенно актуально для этого инструмента, где важно, какой нод был выбран первым.
            if prefs.dsIsSlideOnNodes: #Не приспичило, но пусть будет.
                if self.fotagoNd0:
                    self.fotagoNd0.pos = GenFtgFromNd(self.fotagoNd0.tar, self.cursorLoc, self.uiScale).pos
            break
    def MatterPurposeTool(self, event, prefs, tree):
        ndFrom = self.fotagoNd0.tar
        ndTo = self.fotagoNd1.tar
        def NewLink(sk, lk):
            if sk.is_output:
                tree.links.new(sk, lk.to_socket)
                if lk.to_socket.is_multi_input:
                    tree.links.remove(lk)
            else:
                tree.links.new(lk.from_socket, sk)
                tree.links.remove(lk)
        def GetOnlyVisualSks(puts):
            return [sk for sk in puts if sk.enabled and not sk.hide]
        SolderSkLinks(tree) #Иначе на vl_sold_links_final будет '... has been removed'; но можно было обойтись и обычным 'sk.links'.
        if not self.isByIndexes:
            for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                for sk in putsFrom:
                    for lk in sk.vl_sold_links_final:
                        if not lk.is_muted:
                            skTar = putsTo.get(GetSkLabelName(sk))
                            if skTar:
                                NewLink(skTar, lk)
        else:
            for putsFrom, putsTo in [(ndFrom.inputs, ndTo.inputs), (ndFrom.outputs, ndTo.outputs)]:
                for zp in zip(GetOnlyVisualSks(putsFrom), GetOnlyVisualSks(putsTo)):
                    for lk in zp[0].vl_sold_links_final:
                        if not lk.is_muted:
                            NewLink(zp[1], lk)
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(VoronoiLinksTransferTool,'isByIndexes').name) as dm:
            dm[ru_RU] = "Переносить по индексам"
            dm[zh_CN] = "按顺序传输"

SmartAddToRegAndAddToKmiDefs(VoronoiLinksTransferTool, "#C#_T")
SmartAddToRegAndAddToKmiDefs(VoronoiLinksTransferTool, "SC#_T", {'isByIndexes':True})
dict_setKmiCats['spc'].add(VoronoiLinksTransferTool.bl_idname)

with VlTrMapForKey(VoronoiLinksTransferTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi链接按输入端类型切换到别的端口"

dict_toolLangSpecifDataPool[VoronoiLinksTransferTool, ru_RU] = "Инструмент для редких нужд переноса всех линков с одного нода на другой.\nВ будущем скорее всего будет слито с VST."

class VoronoiWarperTool(VoronoiToolSk):
    bl_idname = 'node.voronoi_warper'
    bl_label = "Voronoi Warper"
    usefulnessForCustomTree = True
    isZoomedTo: bpy.props.BoolProperty(name="Zoom to", default=True)
    isSelectReroutes: bpy.props.IntProperty(name="Select reroutes", default=1, min=-1, max=1, description="-1 – All deselect.\n 0 – Do nothing.\n 1 – Selecting linked reroutes")
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        def FindAnySk():
            ftgSkOut, ftgSkIn = None, None
            for ftg in list_ftgSksOut:
                if (ftg.tar.vl_sold_is_final_linked_cou)and(ftg.blid!='NodeSocketVirtual'):
                    ftgSkOut = ftg
                    break
            for ftg in list_ftgSksIn:
                if (ftg.tar.vl_sold_is_final_linked_cou)and(ftg.blid!='NodeSocketVirtual'):
                    ftgSkIn = ftg
                    break
            return MinFromFtgs(ftgSkOut, ftgSkIn)
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            if nd.type=='REROUTE': #todo0NA и это в обобщение к обобщению.
                self.fotagoSk = list_ftgSksIn[0] if self.cursorLoc.x<nd.location.x else list_ftgSksOut[0]
            else:
                self.fotagoSk = FindAnySk()
            if self.fotagoSk:
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk)
                break
    def ModalTool(self, event, prefs):
        if event.type==prefs.vwtSelectTargetKey:
            self.isSelectTargetKey = event.value=='PRESS'
    def MatterPurposeTool(self, event, prefs, tree):
        skTar = self.fotagoSk.tar
        bpy.ops.node.select_all(action='DESELECT')
        if skTar.vl_sold_is_final_linked_cou:
            def RecrRerouteWalkerSelecting(sk):
                for lk in sk.vl_sold_links_final:
                    nd = lk.to_node if sk.is_output else lk.from_node
                    if nd.type=='REROUTE':
                        if self.isSelectReroutes:
                            nd.select = self.isSelectReroutes>0
                        else:
                            nd.select = self.dict_saveRestoreRerouteSelecting[nd]
                        RecrRerouteWalkerSelecting(nd.outputs[0] if sk.is_output else nd.inputs[0])
                    else:
                        nd.select = True
            RecrRerouteWalkerSelecting(skTar)
            #Можно было бы добавить окраску выделенных нод, но я не знаю, как потом эти цвета отчищать. Хоткей для этого лепить будет слишком не юзабельно.
            #Todo0v6SF Или можно на один кадр нарисовать яркие прямоугольники поверх нодов. Но наверное это будет несовместимо с плавным зумом к цели.
            if self.isSelectTargetKey:
                skTar.node.select = True
            tree.nodes.active = skTar.node
            if self.isZoomedTo:
                bpy.ops.node.view_selected('INVOKE_DEFAULT')
        else: #Эта ветка не используется.
            skTar.node.select = True
            if self.isZoomedTo:
                bpy.ops.node.view_selected('INVOKE_DEFAULT')
            skTar.node.select = False #Огонь хак.
    def InitTool(self, event, prefs, tree):
        self.isSelectTargetKey = prefs.vwtSelectTargetKey in GetSetOfKeysFromEvent(event)
        self.dict_saveRestoreRerouteSelecting = {} #См. `action='DESELECT'`.
        for nd in tree.nodes:
            if nd.type=='REROUTE':
                self.dict_saveRestoreRerouteSelecting[nd] = nd.select
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddKeyTxtProp(col, prefs,'vwtSelectTargetKey')
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isZoomedTo').name) as dm:
            dm[ru_RU] = "Центрировать"
            dm[zh_CN] = "自动最大化显示"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectReroutes').name) as dm:
            dm[ru_RU] = "Выделять рероуты"
            dm[zh_CN] = "选择更改路线"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectReroutes').description) as dm:
            dm[ru_RU] = "-1 – Де-выделять всех.\n 0 – Ничего не делать.\n 1 – Выделять связанные рероуты"
#            dm[zh_CN] = ""
        ##
        with VlTrMapForKey(GetPrefsRnaProp('vwtSelectTargetKey').name) as dm:
            dm[ru_RU] = "Клавиша выделения цели"
            dm[zh_CN] = "选择目标快捷键"

SmartAddToRegAndAddToKmiDefs(VoronoiWarperTool, "##A_W")
SmartAddToRegAndAddToKmiDefs(VoronoiWarperTool, "S#A_W", {'isZoomedTo':False})
dict_setKmiCats['spc'].add(VoronoiWarperTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vwtSelectTargetKey: bpy.props.StringProperty(name="Select target Key", default='LEFT_ALT')

with VlTrMapForKey(VoronoiWarperTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速聚焦某条连接"

dict_toolLangSpecifDataPool[VoronoiWarperTool, ru_RU] = "Мини-ответвление реверс-инженеринга топологии, (как у VPT).\nИнструмент для \"точечных прыжков\" по сокетам."

class VoronoiLazyNodeStencilsTool(VoronoiToolPairSk): #Первый инструмент, созданный по запросам извне, а не по моим личным хотелкам.
    bl_idname = 'node.voronoi_lazy_node_stencils'
    bl_label = "Voronoi Lazy Node Stencils" #Три буквы на инструмент, дожили.
    def CallbackDrawTool(self, drata):
        #Заметка: Для разных гендеров получается не очевидное соответствие стороне текста гендеру сокета. Наверное, придётся смириться.
        TemplateDrawSksToolHh(drata, self.fotagoSk0, self.fotagoSk1)
        if ( (not not self.fotagoSk0)^(not not self.fotagoSk1) )and(drata.dsIsDrawPoint):
            DrawVlWidePoint(drata, drata.cursorLoc, col1=drata.dsCursorColor, col2=drata.dsCursorColor) #Для эстетики.
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        def FindAnySk():
            ftgSkOut, ftgSkIn = None, None
            for ftg in list_ftgSksOut:
                ftgSkOut = ftg
                break
            for ftg in list_ftgSksIn:
                ftgSkIn = ftg
                break
            return MinFromFtgs(ftgSkOut, ftgSkIn)
        self.fotagoSk1 = None
        #Из-за своего предназначения, этот инструмент гарантированно получает первый попавшийся сокет.
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            if isFirstActivation:
                self.fotagoSk0 = FindAnySk()
                CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk0, flag=True)
            skFirst = FtgGetTargetOrNone(self.fotagoSk0)
            if skFirst:
                self.fotagoSk1 = FindAnySk()
                if self.fotagoSk1:
                    if skFirst==self.fotagoSk1.tar:
                        self.fotagoSk1 = None
                    CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk1, flag=False)
            break
    def MatterPurposePoll(self):
        return not not self.fotagoSk0
    def MatterPurposeTool(self, event, prefs, tree):
        VlnstLazyTemplate(prefs, tree, FtgGetTargetOrNone(self.fotagoSk0), FtgGetTargetOrNone(self.fotagoSk1), self.cursorLoc)
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddNiceColorProp(col, prefs,'vlnstNonColorName')
        LyAddNiceColorProp(col, prefs,'vlnstLastExecError', ico='ERROR' if prefs.vlnstLastExecError else 'NONE', decor=0)
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetPrefsRnaProp('vlnstNonColorName').name) as dm:
            dm[ru_RU] = "Название \"Не-цветовых данных\""
            dm[zh_CN] = "图片纹理色彩空间名称"
        with VlTrMapForKey(GetPrefsRnaProp('vlnstLastExecError').name) as dm:
            dm[ru_RU] = "Последняя ошибка выполнения"
            dm[zh_CN] = "上次运行时错误"

SmartAddToRegAndAddToKmiDefs(VoronoiLazyNodeStencilsTool, "##A_Q")
dict_setKmiCats['spc'].add(VoronoiLazyNodeStencilsTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlnstNonColorName:  bpy.props.StringProperty(name="Non-Color name",  default="Non-Color")

with VlTrMapForKey(VoronoiLazyNodeStencilsTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi在输入端快速节点"
with VlTrMapForKey(TxtClsBlabToolSett(VoronoiLazyNodeStencilsTool)) as dm:
    dm[ru_RU] = f"Настройки инструмента {VoronoiLazyNodeStencilsTool.bl_label}:"
    dm[zh_CN] = f"{VoronoiLazyNodeStencilsTool.bl_label}快速添加纹理设置:"

dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, ru_RU] = """Мощь. Три буквы на инструмент, дожили... Инкапсулирует Ctrl-T от
NodeWrangler'а, и никогда не реализованный 'VoronoiLazyNodeContinuationTool'. """ #"Больше лени богу лени!"
dict_toolLangSpecifDataPool[VoronoiLazyNodeStencilsTool, zh_CN] = "代替NodeWrangler的ctrl+t"

class VlnstData:
    lastLastExecError = "" #Для пользовательского редактирования vlnstLastExecError, низя добавить или изменить, но можно удалить.
    isUpdateWorking = False
def VlnstUpdateLastExecError(self, _context):
    if VlnstData.isUpdateWorking:
        return
    VlnstData.isUpdateWorking = True
    if not VlnstData.lastLastExecError:
        self.vlnstLastExecError = ""
    elif self.vlnstLastExecError:
        if self.vlnstLastExecError!=VlnstData.lastLastExecError: #Заметка: Остерегаться переполнения стека.
            self.vlnstLastExecError = VlnstData.lastLastExecError
    else:
        VlnstData.lastLastExecError = ""
    VlnstData.isUpdateWorking = False
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vlnstLastExecError: bpy.props.StringProperty(name="Last exec error", default="", update=VlnstUpdateLastExecError)

#Внезапно оказалось, что моя когдато-шняя идея для инструмента "Ленивое Продолжение" инкапсулировалось в этом инструменте. Вот так неожиданность.
#Этот инструмент, то же самое, как и ^ (где сокет и нод однозначно определял следующий нод), только для двух сокетов; и возможностей больше!

lzAny = '!any'
class LazyKey():
    def __init__(self, fnb, fst, fsn, fsg, snb=lzAny, sst=lzAny, ssn=lzAny, ssg=lzAny):
        self.firstNdBlid = fnb
        self.firstSkBlid = dict_typeSkToBlid.get(fst, fst)
        self.firstSkName = fsn
        self.firstSkGend = fsg
        self.secondNdBlid = snb
        self.secondSkBlid = dict_typeSkToBlid.get(sst, sst)
        self.secondSkName = ssn
        self.secondSkGend = ssg
class LazyNode():
    #Чёрная магия. Если в __init__(list_props=[]), то указание в одном nd.list_props += [..] меняет вообще у всех в lzSt. Нереально чёрная магия; ночные кошмары обеспечены.
    def __init__(self, blid, list_props, ofsPos=(0,0), hhoSk=0, hhiSk=0):
        self.blid = blid
        #list_props Содержит в себе обработку и сокетов тоже.
        #Указание на сокеты (в list_props и lzHh_Sk) -- +1 от индекса, а знак указывает сторону; => 0 не используется.
        self.list_props = list_props
        self.lzHhOutSk = hhoSk
        self.lzHhInSk = hhiSk
        self.locloc = Vec2(ofsPos) #"Local location"; и offset от центра мира.
class LazyStencil():
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

#Database:
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VECTOR','Normal',False), 2, "Fast Color NormalMap")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeNormalMap', [], hhiSk=-2, hhoSk=1) )
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',True, lzAny,'VALUE',lzAny,False), 2, "Lazy Non-Color data to float socket")
lzSt.trees = {'ShaderNodeTree'}
lzSt.isSameLink = True
lzSt.txt_exec = "skFirst.node.image.colorspace_settings.name = prefs.vlnstNonColorName"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA','Color',False), 1, "NW TexCord Parody")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexImage', [(2,'hide',True)], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,0,1,0) ]
list_vlnstDataPool.append(lzSt)
lzSt = copy.deepcopy(lzSt)
lzSt.lzkey.firstSkName = "Base Color"
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'VECTOR','Vector',False), 1, "NW TexCord Parody Half")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], hhoSk=-1, ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeUVMap', [('width',140)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0) ]
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey(lzAny,'RGBA',lzAny,True, lzAny,'SHADER',lzAny,False), 2, "Insert Emission")
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeEmission', [], hhiSk=-1, hhoSk=1) )
list_vlnstDataPool.append(lzSt)
##
lzSt = LazyStencil(LazyKey('ShaderNodeBackground','RGBA','Color',False), 1, "World env texture", prior=1.0)
lzSt.trees = {'ShaderNodeTree'}
lzSt.list_nodes.append( LazyNode('ShaderNodeTexEnvironment', [], hhoSk=-1) )
lzSt.list_nodes.append( LazyNode('ShaderNodeMapping', [(-1,'hide_value',True)], ofsPos=(-180,0)) )
lzSt.list_nodes.append( LazyNode('ShaderNodeTexCoord', [('show_options',False)], ofsPos=(-360,0)) )
lzSt.list_links += [ (1,0,0,0),(2,3,1,0) ]
list_vlnstDataPool.append(lzSt)
##

list_vlnstDataPool.sort(key=lambda a:a.prior, reverse=True)

def DoLazyStencil(tree, skFirst, skSecond, lzSten):
    list_result = []
    firstCenter = None
    for li in lzSten.list_nodes:
        nd = tree.nodes.new(li.blid)
        nd.location += li.locloc
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
    #Для одного нода ещё и сгодилось бы, но учитывая большое разнообразие и гибкость, наверное лучше без NewLinkHhAndRemember(), соединять в сыром виде.
    for li in lzSten.list_links:
        tree.links.new(list_result[li[0]].outputs[li[1]], list_result[li[2]].inputs[li[3]])
    if lzSten.isSameLink:
        tree.links.new(skFirst, skSecond)
    return list_result
def LzCompare(a, b):
    return (a==b)or(a==lzAny)
def LzNodeDoubleCheck(zk, a, b): return LzCompare(zk.firstNdBlid,            a.bl_idname if a else "") and LzCompare(zk.secondNdBlid,            b.bl_idname if b else "")
def LzTypeDoubleCheck(zk, a, b): return LzCompare(zk.firstSkBlid, SkConvertTypeToBlid(a) if a else "") and LzCompare(zk.secondSkBlid, SkConvertTypeToBlid(b) if b else "") #Не 'type', а blid'ы; для аддонских деревьев.
def LzNameDoubleCheck(zk, a, b): return LzCompare(zk.firstSkName,      GetSkLabelName(a) if a else "") and LzCompare(zk.secondSkName,      GetSkLabelName(b) if b else "")
def LzGendDoubleCheck(zk, a, b): return LzCompare(zk.firstSkGend,            a.is_output if a else "") and LzCompare(zk.secondSkGend,            b.is_output if b else "")
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
                        if cyc: #Оба выхода и оба входа, но разные гендеры могут быть в разном порядке. Но перестановка имеет значение для содержания txt_exec'ов.
                            skF, skS = skSecond, skFirst
                        if LzTypeDoubleCheck(zk, skF, skS): #Совпадение Blid'ов сокетов.
                            if LzNameDoubleCheck(zk, skF, skS): #Имён/меток сокетов.
                                if LzGendDoubleCheck(zk, skF, skS): #Гендеров.
                                    result = DoLazyStencil(tree, skF, skS, li)
                                    if li.txt_exec:
                                        try:
                                            exec(li.txt_exec) #Тревога!1, А нет.. без паники, это внутреннее. Всё ещё всё в безопасности.
                                        except Exception as ex:
                                            VlnstData.lastLastExecError = str(ex)
                                            prefs.vlnstLastExecError = VlnstData.lastLastExecError
                                    return result
def VlnstLazyTemplate(prefs, tree, skFirst, skSecond, cursorLoc):
    list_nodes = LzLazyStencil(prefs, tree, skFirst, skSecond)
    if list_nodes:
        bpy.ops.node.select_all(action='DESELECT')
        firstOffset = cursorLoc-list_nodes[0].location
        for nd in list_nodes:
            nd.select = True
            nd.location += firstOffset
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')

class VoronoiResetNodeTool(VoronoiToolNd):
    bl_idname = 'node.voronoi_reset_node'
    bl_label = "Voronoi Reset Node"
    usefulnessForCustomTree = True
    canDrawInAddonDiscl = False
    isResetEnums: bpy.props.BoolProperty(name="Reset enums", default=False)
    isResetOnDrag: bpy.props.BoolProperty(name="Reset on grag (not recommended)", default=False)
    isSelectResetedNode: bpy.props.BoolProperty(name="Select reseted node", default=True)
    def VrntDoResetNode(self, ndTar, tree):
        ndNew = tree.nodes.new(ndTar.bl_idname)
        ndNew.location = ndTar.location
        with TryAndPass(): #SimRep'ы
            for cyc, sk in enumerate(ndTar.outputs):
                for lk in sk.vl_sold_links_final:
                    tree.links.new(ndNew.outputs[cyc], lk.to_socket)
            for cyc, sk in enumerate(ndTar.inputs):
                for lk in sk.vl_sold_links_final:
                    tree.links.new(lk.from_socket, ndNew.inputs[cyc])
        if ndNew.type=='GROUP':
            ndNew.node_tree = ndTar.node_tree
        if not self.isResetEnums: #Если не сбрасывать перечисления, то перенести их на новый нод.
            for li in ndNew.rna_type.properties.items():
                if (not li[1].is_readonly)and(getattr(li[1],'enum_items', None)):
                    setattr(ndNew, li[0], getattr(ndTar, li[0]))
        tree.nodes.remove(ndTar)
        tree.nodes.active = ndNew
        ndNew.select = self.isSelectResetedNode
        return ndNew
    def NextAssignmentTool(self, isFirstActivation, prefs, tree):
        SolderSkLinks(tree)
        self.fotagoNd = None
        for ftgNd in self.ToolGetNearestNodes(includePoorNodes=True):
            nd = ftgNd.tar
            if nd.type=='REROUTE': #"Вы что, хотите пересоздавать рероуты?".
                continue
            self.fotagoNd = ftgNd
            if (self.isResetOnDrag)and(nd not in self.set_done):
                self.set_done.add(self.VrntDoResetNode(self.fotagoNd.tar, tree))
                self.NextAssignmentTool(isFirstActivation, prefs, tree)
                #В целом с 'isResetOnDrag' лажа -- нужно перерисовать для новосозданных нодов, чтобы получить их высоту; или у меня нет идей.
                #И точка цепляется в угол нодов на один кадр.
            break
    def MatterPurposePoll(self):
        return (not self.isResetOnDrag)and(self.fotagoNd)
    def MatterPurposeTool(self, event, prefs, tree):
        self.VrntDoResetNode(self.fotagoNd.tar, tree)
    def InitTool(self, event, prefs, tree):
        self.set_done = set() #Без этого будет очень "страшна"-поведение, а если переусердствовать, то скорее всего краш.
    @classmethod
    def BringTranslations(cls):
        with VlTrMapForKey(GetAnnotFromCls(cls,'isResetEnums').name) as dm:
            dm[ru_RU] = "Восстанавливать свойства перечисления"
            dm[zh_CN] = "恢复下拉列表里的选择"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isResetOnDrag').name) as dm:
            dm[ru_RU] = "Восстанавливать при ведении курсора (не рекомендуется)"
#            dm[zh_CN] = "悬停时恢复"
        with VlTrMapForKey(GetAnnotFromCls(cls,'isSelectResetedNode').name) as dm:
            dm[ru_RU] = "Выделять восстановленный нод"
            dm[zh_CN] = "选择重置的节点"

SmartAddToRegAndAddToKmiDefs(VoronoiResetNodeTool, "###_BACK_SPACE")
SmartAddToRegAndAddToKmiDefs(VoronoiResetNodeTool, "S##_BACK_SPACE", {'isResetEnums':True})
dict_setKmiCats['spc'].add(VoronoiResetNodeTool.bl_idname)

with VlTrMapForKey(VoronoiResetNodeTool.bl_label) as dm:
    dm[zh_CN] = "Voronoi快速恢复节点默认参数"

dict_toolLangSpecifDataPool[VoronoiResetNodeTool, ru_RU] = """Инструмент для сброса нодов без нужды прицеливания, с удобствами ведения мышкой
и игнорированием свойств перечислений. Был создан, потому что в NW было похожее."""

class VoronoiDummyTool(VoronoiToolSk): #Шаблон для быстро-удобного(?) добавления нового инструмента.
    bl_idname = 'node.voronoi_dummy'
    bl_label = "Voronoi Dummy"
    usefulnessForCustomTree = True
    isDummy: bpy.props.BoolProperty(name="Dummy", default=False)
    def CallbackDrawTool(self, drata):
        TemplateDrawSksToolHh(drata, self.fotagoSk)
    def NextAssignmentTool(self, _isFirstActivation, prefs, tree):
        self.fotagoSk = None
        for ftgNd in self.ToolGetNearestNodes():
            nd = ftgNd.tar
            if nd.type=='REROUTE':
                continue
            list_ftgSksIn, list_ftgSksOut = self.ToolGetNearestSockets(nd)
            ftgSkIn = list_ftgSksIn[0] if list_ftgSksIn else None
            ftgSkOut = list_ftgSksOut[0] if list_ftgSksOut else None
            self.fotagoSk = MinFromFtgs(ftgSkOut, ftgSkIn)
            CheckUncollapseNodeAndReNext(nd, self, cond=self.fotagoSk, flag=False)
            break
        #todo0NA Я придумал что делать с концепцией, когда имеются разные критерии от isFirstActivation'а, и второй находится сразу рядом после первого моментально. Явное (и насильное) сравнение на своего и отмена.
    def MatterPurposePoll(self):
        return not not self.fotagoSk
    def MatterPurposeTool(self, event, prefs, tree):
        sk = self.fotagoSk.tar
        sk.name = sk.name if (sk.name)and(sk.name[0]=="\"") else f'"{sk.name}"'
        sk.node.label = "Hi i am vdt. See source code"
        VlrtRememberLastSockets(sk if sk.is_output else None, None)
    def InitTool(self, event, prefs, tree):
        self.fotagoSk = None
    @staticmethod
    def LyDrawInAddonDiscl(col, prefs):
        LyAddNiceColorProp(col, prefs,'vdtDummy')
    @classmethod
    def BringTranslations(cls):
        pass

#SmartAddToRegAndAddToKmiDefs(VoronoiDummyTool, "###_D", {'isDummy':True})
dict_setKmiCats['grt'].add(VoronoiDummyTool.bl_idname)

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vdtDummy: bpy.props.StringProperty(name="Dummy", default="Dummy")

with VlTrMapForKey(VoronoiDummyTool.bl_label) as dm:
    dm[ru_RU] = "Voronoi Болванка"

dict_toolLangSpecifDataPool[VoronoiDummyTool, ru_RU] = """"Ой дурачёк"."""

# =======

def GetVlKeyconfigAsPy(): #Взято из 'bl_keymap_utils.io'. Понятия не имею, как оно работает.
    def Ind(num):
        return " "*num
    def keyconfig_merge(kc1, kc2):
        kc1_names = {km.name for km in kc1.keymaps}
        merged_keymaps = [(km, kc1) for km in kc1.keymaps]
        if kc1!=kc2:
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
    result += "]"+" #kmi count: "+str(sco)+"\n"
    result += "\n"
    result += "if True:"+"\n"
    result += "    import bl_keymap_utils"+"\n"
    result += "    import bl_keymap_utils.versioning"+"\n" #Чёрная магия; кажется, такая же как и с "gpu_extras".
    result += "    kc = bpy.context.window_manager.keyconfigs.active"+"\n"
    result += f"    kd = bl_keymap_utils.versioning.keyconfig_update(list_keyconfigData, {bpy.app.version_file!r})"+"\n"
    result += "    bl_keymap_utils.io.keyconfig_init_from_data(kc, kd)"
    return result
def GetVaSettAsPy(prefs):
    set_ignoredAddonPrefs = {'bl_idname', 'vaUiTabs', 'vaInfoRestore', 'dsIsFieldDebug', 'dsIsTestDrawing',
                             'vaKmiMainstreamDiscl', 'vaKmiOtjersDiscl', 'vaKmiSpecialDiscl', 'vaKmiQqmDiscl', 'vaKmiCustomDiscl'}
    for cls in list_toolClasses:
        set_ignoredAddonPrefs.add(cls.disclBoxPropName)
        set_ignoredAddonPrefs.add(cls.disclBoxPropNameInfo)
    txt_vasp = ""
    txt_vasp += "#Exported/Importing addon settings for Voronoi Linker v"+txtAddonVer+"\n"
    import datetime
    txt_vasp += f"#Generated "+datetime.datetime.now().strftime("%Y.%m.%d")+"\n"
    txt_vasp += "\n"
    txt_vasp += "import bpy\n"
    #Сконструировать изменённые настройки аддона:
    txt_vasp += "\n"
    txt_vasp += "#Addon prefs:\n"
    txt_vasp += f"prefs = bpy.context.preferences.addons['{voronoiAddonName}'].preferences"+"\n\n"
    txt_vasp += "def SetProp(att, val):"+"\n"
    txt_vasp += "    if hasattr(prefs, att):"+"\n"
    txt_vasp += "        setattr(prefs, att, val)"+"\n\n"
    def AddAndProc(txt):
        nonlocal txt_vasp
        len = txt.find(",")
        txt_vasp += txt.replace(", ",","+" "*(42-len), 1)
    for pr in prefs.rna_type.properties:
        if not pr.is_readonly:
            #'_BoxDiscl'ы не стал игнорировать, пусть будут.
            if pr.identifier not in set_ignoredAddonPrefs:
                isArray = getattr(pr,'is_array', False)
                if isArray:
                    isDiff = not not [li for li in zip(pr.default_array, getattr(prefs, pr.identifier)) if li[0]!=li[1]]
                else:
                    isDiff = pr.default!=getattr(prefs, pr.identifier)
                if (True)or(isDiff): #Наверное сохранять только разницу небезопасно, вдруг не сохранённые свойства изменят своё значение по умолчанию.
                    if isArray:
                        #txt_vasp += f"prefs.{li.identifier} = ({' '.join([str(li)+',' for li in arr])})\n"
                        list_vals = [str(li)+"," for li in getattr(prefs, pr.identifier)]
                        list_vals[-1] = list_vals[-1][:-1]
                        AddAndProc(f"SetProp('{pr.identifier}', ("+" ".join(list_vals)+"))\n")
                    else:
                        match pr.type:
                            case 'STRING': AddAndProc(f"SetProp('{pr.identifier}', \"{getattr(prefs, pr.identifier)}\")"+"\n")
                            case 'ENUM':   AddAndProc(f"SetProp('{pr.identifier}', '{getattr(prefs, pr.identifier)}')"+"\n")
                            case _:        AddAndProc(f"SetProp('{pr.identifier}', {getattr(prefs, pr.identifier)})"+"\n")
    #Сконструировать все VL хоткеи:
    txt_vasp += "\n"
    txt_vasp += "#Addon keymaps:\n"
    #P.s. я не знаю, как обрабатывать только изменённые хоткеи; это выглядит слишком головной болью и дремучим лесом. #tovo0v6
    # Лень реверсинженерить '..\scripts\modules\bl_keymap_utils\io.py', поэтому просто сохранять всех.
    txt_vasp += GetVlKeyconfigAsPy() #Оно нахрен не работает; та часть, которая восстанавливает; сгенерированным скриптом ничего не сохраняется, только временный эффект.
    #Придётся ждать того героя, кто придёт и починит всё это.
    return txt_vasp

def GetFirstUpperLetters(txt):
    txtUppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" #"".join([chr(cyc) for cyc in range(65, 91)])
    list_result = []
    for ch1, ch2 in zip(" "+txt, txt):
        if (ch1 not in txtUppers)and(ch2 in txtUppers): #/(?<=[^A-Z])[A-Z]/
            list_result.append(ch2)
    return "".join(list_result)
def SolderClsToolNames():
    for cls in list_toolClasses:
        cls.vlTripleName = GetFirstUpperLetters(cls.bl_label)+"T" #Изначально было создано "потому что прикольно", но теперь это нужно; см. SetPieData().
        cls.disclBoxPropName = cls.vlTripleName[:-1].lower()+"BoxDiscl"
        cls.disclBoxPropNameInfo = cls.disclBoxPropName+"Info"
SolderClsToolNames()

for cls in list_toolClasses:
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropName}: bpy.props.BoolProperty(name=\"\", default=False)")
    exec(f"class VoronoiAddonPrefs(VoronoiAddonPrefs): {cls.disclBoxPropNameInfo}: bpy.props.BoolProperty(name=\"\", default=False)")

list_langDebEnumItems = []
for li in ["Free", "Special", "AddonPrefs"]+[cls.bl_label for cls in list_toolClasses]:
    list_langDebEnumItems.append( (li.upper(), GetFirstUpperLetters(li), "") )

def VaUpdateTestDraw(self, context):
    TestDraw.Toggle(context, self.dsIsTestDrawing)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaLangDebDiscl: bpy.props.BoolProperty(name="Language bruteforce debug", default=False)
    vaLangDebEnum: bpy.props.EnumProperty(name="LangDebEnum", default='FREE', items=list_langDebEnumItems)
    dsIsFieldDebug: bpy.props.BoolProperty(name="Field debug", default=False)
    dsIsTestDrawing: bpy.props.BoolProperty(name="Testing draw", default=False, update=VaUpdateTestDraw)
    dsIncludeDev: bpy.props.BoolProperty(name="IncludeDev", default=False)
    dev: bpy.props.FloatProperty(name="", default=0)

#Оставлю здесь маленький список моих личных "хотелок" (по хронологии интеграции), которые перекочевали из других моих личных аддонов в VL:
#Hider
#QuckMath и JustMathPie
#Warper
#RANTO

def Prefs():
    return bpy.context.preferences.addons[voronoiAddonName].preferences

class VoronoiOpAddonTabs(bpy.types.Operator):
    bl_idname = 'node.voronoi_addon_tabs'
    bl_label = "VL Addon Tabs"
    bl_description = "VL's addon tab" #todo1v6 придумать, как перевести для каждой вкладки разное.
    opt: bpy.props.StringProperty()
    def invoke(self, context, event):
        #if not self.opt: return {'CANCELLED'}
        prefs = Prefs()
        match self.opt:
            case 'GetPySett':
                context.window_manager.clipboard = GetVaSettAsPy(prefs)
            case 'AddNewKmi':
                GetUserKmNe().keymap_items.new("node.voronoi_",'D','PRESS').show_expanded = True
            case _:
                prefs.vaUiTabs = self.opt
        return {'FINISHED'}

def LyAddThinSep(where, scaleY):
    row = where.row(align=True)
    row.separator()
    row.scale_y = scaleY

class KmiCat():
    def __init__(self, propName='', set_kmis=set(), set_idn=set()):
        self.propName = propName
        self.set_kmis = set_kmis
        self.set_idn = set_idn
        self.sco = 0
class KmiCats:
    pass

vaUpdateSelfTgl = False
def VaUpdateDecorColSk(self, _context):
    global vaUpdateSelfTgl
    if vaUpdateSelfTgl:
        return
    vaUpdateSelfTgl = True
    self.vaDecorColSk = self.vaDecorColSkBack
    vaUpdateSelfTgl = False

fitTabItems = ( ('SETTINGS',"Settings",""), ('APPEARANCE',"Appearance",""), ('DRAW',"Draw",""), ('KEYMAP',"Keymap",""), ('INFO',"Info","") )#, ('DEV',"Dev","")
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    vaUiTabs: bpy.props.EnumProperty(name="Addon Prefs Tabs", default='SETTINGS', items=fitTabItems)
    vaInfoRestore:     bpy.props.BoolProperty(name="", description="This list is just a copy from the \"Preferences > Keymap\".\nResrore will restore everything \"Node Editor\", not just addon")
    #Box disclosures:
    vaKmiMainstreamDiscl: bpy.props.BoolProperty(name="The Great Trio ", default=True) #Заметка: Пробел важен для переводов.
    vaKmiOtjersDiscl:     bpy.props.BoolProperty(name="Others ", default=False)
    vaKmiSpecialDiscl:    bpy.props.BoolProperty(name="Specials ", default=False)
    vaKmiQqmDiscl:        bpy.props.BoolProperty(name="Quick quick math ", default=False)
    vaKmiCustomDiscl:     bpy.props.BoolProperty(name="Custom ", default=True)
    ##
    vaDecorLy:        bpy.props.FloatVectorProperty(name="DecorForLayout",   default=(0.01, 0.01, 0.01),   min=0, max=1, size=3, subtype='COLOR')
    vaDecorColSk:     bpy.props.FloatVectorProperty(name="DecorForColSk",    default=(1.0, 1.0, 1.0, 1.0), min=0, max=1, size=4, subtype='COLOR', update=VaUpdateDecorColSk)
    vaDecorColSkBack: bpy.props.FloatVectorProperty(name="vaDecorColSkBack", default=(1.0, 1.0, 1.0, 1.0), min = 0, max=1, size=4, subtype='COLOR')

class VoronoiAddonPrefs(VoronoiAddonPrefs):
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
    dsIsColoredNodes:  bpy.props.BoolProperty(name="Nodes",       default=True)
    ##
    dsSocketAreaAlpha: bpy.props.FloatProperty(name="Socket area alpha", default=0.075, min=0.0, max=1.0, subtype="FACTOR")
    ##
    dsUniformColor:     bpy.props.FloatVectorProperty(name="Alternative uniform color", default=(0.632502, 0.408091, 0.174378, 0.9), min=0, max=1, size=4, subtype='COLOR') #0.65, 0.65, 0.65, 1.0
    dsUniformNodeColor: bpy.props.FloatVectorProperty(name="Alternative nodes color",   default=(0.069818, 0.054827, 0.629139, 0.9), min=0, max=1, size=4, subtype='COLOR') #1.0, 1.0, 1.0, 0.9
    dsCursorColor:      bpy.props.FloatVectorProperty(name="Cursor color",              default=(0.730461, 0.539480, 0.964686, 1.0), min=0, max=1, size=4, subtype='COLOR') #1.0, 1.0, 1.0, 1.0
    dsCursorColorAvailability: bpy.props.IntProperty(name="Cursor color availability", default=2, min=0, max=2, description="If a line is drawn to the cursor, color part of it in the cursor color.\n0 – Disable.\n1 – For one line.\n2 – Always")
    ##
    dsDisplayStyle: bpy.props.EnumProperty(name="Display frame style", default='CLASSIC', items=( ('CLASSIC',"Classic",""), ('SIMPLIFIED',"Simplified",""), ('ONLY_TEXT',"Only text","") ))
    dsFontFile:     bpy.props.StringProperty(name="Font file",    default='C:\Windows\Fonts\consola.ttf', subtype='FILE_PATH') #"Пользователи Линукса негодуют".
    dsLineWidth:    bpy.props.FloatProperty( name="Line Width",   default=1.5, min=0.5, max=8.0, subtype="FACTOR")
    dsPointScale:   bpy.props.FloatProperty( name="Point scale",  default=1.0, min=0.0, max=3.0)
    dsFontSize:     bpy.props.IntProperty(   name="Font size",    default=28,  min=10,  max=48)
    dsMarkerStyle:  bpy.props.IntProperty(   name="Marker Style", default=0,   min=0,   max=2)
    ##
    dsManualAdjustment: bpy.props.FloatProperty(name="Manual adjustment",         default=-0.2, description="The Y-axis offset of text for this font") #https://blender.stackexchange.com/questions/312413/blf-module-how-to-draw-text-in-the-center
    dsPointOffsetX:     bpy.props.FloatProperty(name="Point offset X axis",       default=20.0,   min=-50.0, max=50.0)
    dsFrameOffset:      bpy.props.IntProperty(  name="Frame size",                default=0,      min=0,     max=24, subtype='FACTOR') #Заметка: Важно, чтобы это был Int.
    dsDistFromCursor:   bpy.props.FloatProperty(name="Text distance from cursor", default=25.0,   min=5.0,   max=50.0)
    ##
    dsIsAlwaysLine:        bpy.props.BoolProperty(name="Always draw line",      default=False, description="Draw a line to the cursor even from a single selected socket")
    dsIsSlideOnNodes:      bpy.props.BoolProperty(name="Slide on nodes",        default=False)
    dsIsDrawNodeNameLabel: bpy.props.BoolProperty(name="Display text for node", default=True)
    ##
    dsIsAllowTextShadow: bpy.props.BoolProperty(       name="Enable text shadow", default=True)
    dsShadowCol:         bpy.props.FloatVectorProperty(name="Shadow color",       default=(0.0, 0.0, 0.0, 0.5), min=0,   max=1,  size=4, subtype='COLOR')
    dsShadowOffset:      bpy.props.IntVectorProperty(  name="Shadow offset",      default=(2,-2),               min=-20, max=20, size=2)
    dsShadowBlur:        bpy.props.IntProperty(        name="Shadow blur",        default=2,                    min=0,   max=2)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    #Уж было я хотел добавить это, но потом мне стало таак лень. Это же нужно всё менять под "только сокеты", и критерии для нод неведомо как получать.
    #И выгода неизвестно какая, кроме эстетики. Так что ну его нахрен. "Работает -- не трогай".
    #А ещё реализация "только сокеты" где-то может грозить потенциальной кроличьей норой.
    vSearchMethod: bpy.props.EnumProperty(name="Search method", default='SOCKET', items=( ('NODE_SOCKET',"Nearest node > nearest socket",""), ('SOCKET',"Only nearest socket","") )) #Нигде не используется; и кажется, никогда не будет.
    vEdgePanFac: bpy.props.FloatProperty(name="Edge pan zoom factor", default=0.33, min=0.0, max=1.0, description="0.0 – Shift only; 1.0 – Scale only")
    vEdgePanSpeed: bpy.props.FloatProperty(name="Edge pan speed", default=1.0, min=0.0, max=2.5)
    vIsOverwriteZoomLimits: bpy.props.BoolProperty(name="Overwriting zoom limits", default=False)
    vOwZoomMin: bpy.props.FloatProperty(name="Zoom min", default=0.05,  min=0.0078125, max=1.0,  precision=3)
    vOwZoomMax: bpy.props.FloatProperty(name="Zoom max", default=2.301, min=1.0,       max=16.0, precision=3)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    @staticmethod
    def BringTranslations():
        with VlTrMapForKey(GetPrefsRnaProp('vaInfoRestore').description) as dm:
            dm[ru_RU] = "Этот список лишь копия из настроек. \"Восстановление\" восстановит всё, а не только аддон"
            dm[zh_CN] = "危险:“恢复”按钮将恢复整个快捷键里“节点编辑器”类中的所有设置,而不仅仅是恢复此插件!下面只显示本插件的快捷键。"
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiMainstreamDiscl').name) as dm:
            dm[ru_RU] = "Великое трио"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiOtjersDiscl').name) as dm:
            dm[ru_RU] = "Другие"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiSpecialDiscl').name) as dm:
            dm[ru_RU] = "Специальные"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiQqmDiscl').name) as dm:
            dm[ru_RU] = "Быстрая быстрая математика"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vaKmiCustomDiscl').name) as dm:
            dm[ru_RU] = "Кастомные"
#            dm[zh_CN] = ""
        #== Draw ==
        with VlTrMapForKey(GetPrefsRnaProp('dsUniformColor').name) as dm:
            dm[ru_RU] = "Альтернативный постоянный цвет"
            dm[zh_CN] = "自定义轮选时端口的颜色"
        with VlTrMapForKey(GetPrefsRnaProp('dsUniformNodeColor').name) as dm:
            dm[ru_RU] = "Альтернативный цвет нодов"
            dm[zh_CN] = "动态选择节点时标识的颜色(显示下拉列表时)"
        with VlTrMapForKey(GetPrefsRnaProp('dsCursorColor').name) as dm:
            dm[ru_RU] = "Цвет курсора"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsCursorColorAvailability').name) as dm:
            dm[ru_RU] = "Наличие цвета курсора"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsCursorColorAvailability').description) as dm:
            dm[ru_RU] = "Если линия рисуется к курсору, окрашивать её часть в цвет курсора.\n0 – Выключено.\n1 – Для одной линии.\n2 – Всегда"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsSocketAreaAlpha').name) as dm:
            dm[ru_RU] = "Прозрачность области сокета"
            dm[zh_CN] = "端口区域的透明度"
        with VlTrMapForKey(GetPrefsRnaProp('dsFontFile').name) as dm:
            dm[ru_RU] = "Файл шрифта"
            dm[zh_CN] = "字体文件"
        with VlTrMapForKey(GetPrefsRnaProp('dsManualAdjustment').name) as dm:
            dm[ru_RU] = "Ручная корректировка"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsManualAdjustment').description) as dm:
            dm[ru_RU] = "Смещение текста по оси Y для данного шрифта"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsPointOffsetX').name) as dm:
            dm[ru_RU] = "Смещение точки по оси X"
            dm[zh_CN] = "X轴上的点偏移"
        with VlTrMapForKey(GetPrefsRnaProp('dsFrameOffset').name) as dm:
            dm[ru_RU] = "Размер рамки"
            dm[zh_CN] = "边框大小"
        with VlTrMapForKey(GetPrefsRnaProp('dsFontSize').name) as dm:
            dm[ru_RU] = "Размер шрифта"
            dm[zh_CN] = "字体大小"
        with VlTrMapForKey(GetPrefsRnaProp('dsMarkerStyle').name) as dm:
            dm[ru_RU] = "Стиль маркера"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsIsDrawSkArea').name) as dm:
            dm[ru_RU] = "Область сокета"
            dm[zh_CN] = "高亮显示选中端口"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle').name) as dm:
            dm[ru_RU] = "Стиль отображения рамки"
            dm[zh_CN] = "边框显示样式"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle',0).name) as dm:
            dm[ru_RU] = "Классический"
            dm[zh_CN] = "经典"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle',1).name) as dm:
            dm[ru_RU] = "Упрощённый"
            dm[zh_CN] = "简化"
        with VlTrMapForKey(GetPrefsRnaProp('dsDisplayStyle',2).name) as dm:
            dm[ru_RU] = "Только текст"
            dm[zh_CN] = "仅文本"
        with VlTrMapForKey(GetPrefsRnaProp('dsPointScale').name) as dm:
            dm[ru_RU] = "Масштаб точки"
#            dm[zh_CN] = "点的大小"?
        with VlTrMapForKey(GetPrefsRnaProp('dsDistFromCursor').name) as dm:
            dm[ru_RU] = "Расстояние до текста от курсора"
            dm[zh_CN] = "到文本的距离"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsAlwaysLine').name) as dm:
            dm[ru_RU] = "Всегда рисовать линию"
            dm[zh_CN] = "始终绘制线条"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsAlwaysLine').description) as dm:
            dm[ru_RU] = "Рисовать линию к курсору даже от одного выбранного сокета"
            dm[zh_CN] = "在鼠标移动到移动到已有连接端口的时是否还显示连线"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsSlideOnNodes').name) as dm:
            dm[ru_RU] = "Скользить по нодам"
            dm[zh_CN] = "在节点上滑动"
        with VlTrMapForKey(GetPrefsRnaProp('dsIsAllowTextShadow').name) as dm:
            dm[ru_RU] = "Включить тень текста"
            dm[zh_CN] = "启用文本阴影"
        with VlTrMapForKey(GetPrefsRnaProp('dsShadowCol').name) as dm:
            dm[ru_RU] = "Цвет тени"
            dm[zh_CN] = "阴影颜色"
        with VlTrMapForKey(GetPrefsRnaProp('dsShadowOffset').name) as dm:
            dm[ru_RU] = "Смещение тени"
            dm[zh_CN] = "阴影偏移"
        with VlTrMapForKey(GetPrefsRnaProp('dsShadowBlur').name) as dm:
            dm[ru_RU] = "Размытие тени"
            dm[zh_CN] = "阴影模糊"
        #== Settings ==
        with VlTrMapForKey(GetPrefsRnaProp('vEdgePanFac').name) as dm:
            dm[ru_RU] = "Фактор панорамирования масштаба"
            dm[zh_CN] = "边缘平移缩放系数"
        with VlTrMapForKey(GetPrefsRnaProp('vEdgePanFac').description) as dm:
            dm[ru_RU] = "0.0 – Только сдвиг; 1.0 – Только масштаб"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vEdgePanSpeed').name) as dm:
            dm[ru_RU] = "Скорость краевого панорамирования"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vIsOverwriteZoomLimits').name) as dm:
            dm[ru_RU] = "Перезапись лимитов масштаба"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vOwZoomMin').name) as dm:
            dm[ru_RU] = "Минимальный масштаб"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('vOwZoomMax').name) as dm:
            dm[ru_RU] = "Максимальный масштаб"
#            dm[zh_CN] = ""
        with VlTrMapForKey(GetPrefsRnaProp('dsIsDrawNodeNameLabel').name) as dm:
            dm[ru_RU] = "Показывать заголовок для нода"
            dm[zh_CN] = "显示节点标签"

class VoronoiAddonPrefs(VoronoiAddonPrefs):
    def LyDrawTabSettings(self, where):
        def LyAddAddonBoxDiscl(where, who, att, *, txt=None, isWide=False, align=False):
            colBox = where.box().column(align=True)
            if LyAddDisclosureProp(colBox, who, att, txt=txt, active=False, isWide=isWide):
                rowTool = colBox.row()
                rowTool.separator()
                return rowTool.column(align=align)
            return None
        colMain = where.column()
        LyAddThinSep(colMain, 0.1)
        for cls in list_toolClasses:
            if cls.canDrawInAddonDiscl:
                if colDiscl:=LyAddAddonBoxDiscl(colMain, self, cls.disclBoxPropName, txt=TxtClsBlabToolSett(cls), align=True):
                    cls.LyDrawInAddonDiscl(colDiscl, self)
    def LyDrawTabAppearance(self, where):
        colMain = where.column()
        #LyAddHandSplitProp(LyAddLabeledBoxCol(colMain, text="Main"), self,'vSearchMethod')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Edge pan")
        LyAddHandSplitProp(colBox, self,'vEdgePanFac', text="Zoom factor")
        LyAddHandSplitProp(colBox, self,'vEdgePanSpeed', text="Speed")
        if (self.dsIncludeDev)or(self.vIsOverwriteZoomLimits):
            LyAddHandSplitProp(colBox, self,'vIsOverwriteZoomLimits', active=self.vIsOverwriteZoomLimits)
            if self.vIsOverwriteZoomLimits:
                LyAddHandSplitProp(colBox, self,'vOwZoomMin')
                LyAddHandSplitProp(colBox, self,'vOwZoomMax')
        ##
        for cls in list_toolClasses:
            if cls.canDrawInAppearance:
                cls.LyDrawInAppearance(colMain, self)
    def LyDrawTabDraw(self, where):
        def LyAddPairProp(where, txt):
            row = where.row(align=True)
            row.prop(self, txt)
            row.active = getattr(self, txt.replace("Colored","Draw"))
        colMain = where.column()
        splDrawColor = colMain.box().split(align=True)
        splDrawColor.use_property_split = True
        colDraw = splDrawColor.column(align=True, heading='Draw')
        colDraw.prop(self,'dsIsDrawText')
        colDraw.prop(self,'dsIsDrawMarker')
        colDraw.prop(self,'dsIsDrawPoint')
        colDraw.prop(self,'dsIsDrawLine')
        colDraw.prop(self,'dsIsDrawSkArea')
        with LyAddQuickInactiveCol(colDraw, active=self.dsIsDrawText) as row:
            row.prop(self,'dsIsDrawNodeNameLabel', text="Node text") #"Text for node"
        colCol = splDrawColor.column(align=True, heading='Colored')
        LyAddPairProp(colCol,'dsIsColoredText')
        LyAddPairProp(colCol,'dsIsColoredMarker')
        LyAddPairProp(colCol,'dsIsColoredPoint')
        LyAddPairProp(colCol,'dsIsColoredLine')
        LyAddPairProp(colCol,'dsIsColoredSkArea')
        tgl = (self.dsIsDrawLine)or(self.dsIsDrawPoint)or(self.dsIsDrawText and self.dsIsDrawNodeNameLabel)
        with LyAddQuickInactiveCol(colCol, active=tgl) as row:
            row.prop(self,'dsIsColoredNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Special")
        #LyAddHandSplitProp(colBox, self,'dsIsDrawNodeNameLabel', active=self.dsIsDrawText)
        LyAddHandSplitProp(colBox, self,'dsIsAlwaysLine')
        LyAddHandSplitProp(colBox, self,'dsIsSlideOnNodes')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Colors")
        LyAddHandSplitProp(colBox, self,'dsSocketAreaAlpha', active=self.dsIsDrawSkArea)
        tgl = ( (self.dsIsDrawText   and not self.dsIsColoredText  )or
                (self.dsIsDrawMarker and not self.dsIsColoredMarker)or
                (self.dsIsDrawPoint  and not self.dsIsColoredPoint )or
                (self.dsIsDrawLine   and not self.dsIsColoredLine  )or
                (self.dsIsDrawSkArea and not self.dsIsColoredSkArea) )
        LyAddHandSplitProp(colBox, self,'dsUniformColor', active=tgl)
        tgl = ( (self.dsIsDrawText   and self.dsIsColoredText  )or
                (self.dsIsDrawPoint  and self.dsIsColoredPoint )or
                (self.dsIsDrawLine   and self.dsIsColoredLine  ) )
        LyAddHandSplitProp(colBox, self,'dsUniformNodeColor', active=(tgl)and(not self.dsIsColoredNodes))
        tgl1 = (self.dsIsDrawPoint and self.dsIsColoredPoint)
        tgl2 = (self.dsIsDrawLine  and self.dsIsColoredLine)and(not not self.dsCursorColorAvailability)
        LyAddHandSplitProp(colBox, self,'dsCursorColor', active=tgl1 or tgl2)
        LyAddHandSplitProp(colBox, self,'dsCursorColorAvailability', active=self.dsIsDrawLine and self.dsIsColoredLine)
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Customization")
        LyAddHandSplitProp(colBox, self,'dsDisplayStyle')
        LyAddHandSplitProp(colBox, self,'dsFontFile')
        if not self.dsFontFile.endswith((".ttf",".otf")):
            spl = colBox.split(factor=0.4, align=True)
            spl.label(text="")
            spl.label(text=txt_onlyFontFormat, icon='ERROR')
        LyAddThinSep(colBox, 0.5)
        LyAddHandSplitProp(colBox, self,'dsLineWidth')
        LyAddHandSplitProp(colBox, self,'dsPointScale')
        LyAddHandSplitProp(colBox, self,'dsFontSize')
        LyAddHandSplitProp(colBox, self,'dsMarkerStyle')
        ##
        colBox = LyAddLabeledBoxCol(colMain, text="Advanced")
        LyAddHandSplitProp(colBox, self,'dsManualAdjustment')
        LyAddHandSplitProp(colBox, self,'dsPointOffsetX')
        LyAddHandSplitProp(colBox, self,'dsFrameOffset')
        LyAddHandSplitProp(colBox, self,'dsDistFromCursor')
        LyAddThinSep(colBox, 0.25) #Межгалкоевые отступы складываются, поэтому дополнительный отступ для выравнивания.
        LyAddHandSplitProp(colBox, self,'dsIsAllowTextShadow')
        colShadow = colBox.column(align=True)
        LyAddHandSplitProp(colShadow, self,'dsShadowCol', active=self.dsIsAllowTextShadow)
        LyAddHandSplitProp(colShadow, self,'dsShadowBlur') #Размытие тени разделяет их, чтобы не сливались вместе по середине.
        row = LyAddHandSplitProp(colShadow, self,'dsShadowOffset', returnAsLy=True).row(align=True)
        row.row().prop(self,'dsShadowOffset', text="X  ", translate=False, index=0, icon_only=True)
        row.row().prop(self,'dsShadowOffset', text="Y  ", translate=False, index=1, icon_only=True)
        colShadow.active = self.dsIsAllowTextShadow
        ##
        colDev = colMain.column(align=True)
        if (self.dsIncludeDev)or(self.dsIsFieldDebug)or(self.dsIsTestDrawing):
            with LyAddQuickInactiveCol(colDev, active=self.dsIsFieldDebug) as row:
                row.prop(self,'dsIsFieldDebug')
            with LyAddQuickInactiveCol(colDev, active=self.dsIsTestDrawing) as row:
                row.prop(self,'dsIsTestDrawing')
    def LyDrawTabKeymaps(self, where):
        colMain = where.column()
        colMain.separator()
        rowLabelMain = colMain.row(align=True)
        rowLabel = rowLabelMain.row(align=True)
        rowLabel.alignment = 'CENTER'
        rowLabel.label(icon='DOT')
        rowLabel.label(text="Node Editor")
        rowLabelPost = rowLabelMain.row(align=True)
        colList = colMain.column(align=True)
        kmUNe = GetUserKmNe()
        ##
        kmiCats = KmiCats()
        kmiCats.cus = KmiCat('vaKmiCustomDiscl',     set())
        kmiCats.qqm = KmiCat('vaKmiQqmDiscl',        set(), dict_setKmiCats['qqm'] )
        kmiCats.grt = KmiCat('vaKmiMainstreamDiscl', set(), dict_setKmiCats['grt'] )
        kmiCats.oth = KmiCat('vaKmiOtjersDiscl',     set(), dict_setKmiCats['oth'] )
        kmiCats.spc = KmiCat('vaKmiSpecialDiscl',    set(), dict_setKmiCats['spc'] )
        kmiCats.cus.LCond = lambda a: a.id<0 #Отрицательный ид для кастомных? Ну ладно. Пусть будет идентифицирующим критерием.
        kmiCats.qqm.LCond = lambda a: any(True for txt in {'quickOprFloat','quickOprVector','quickOprBool','quickOprColor','justPieCall','isRepeatLastOperation'} if getattr(a.properties, txt, None))
        kmiCats.grt.LCond = lambda a: a.idname in kmiCats.grt.set_idn
        kmiCats.oth.LCond = lambda a: a.idname in kmiCats.oth.set_idn
        kmiCats.spc.LCond = lambda a:True
        #В старых версиях аддона с другим методом поиска, на вкладке "keymap" порядок отображался в обратном порядке вызовов регистрации kmidef с одинаковыми `cls`.
        #Теперь сделал так. Как работал предыдущий метод -- для меня загадка.
        scoAll = 0
        for li in kmUNe.keymap_items:
            if li.idname.startswith("node.voronoi_"):
                for dv in kmiCats.__dict__.values():
                    if dv.LCond(li):
                        dv.set_kmis.add(li)
                        dv.sco += 1
                        break
                scoAll += 1 #Хоткеев теперь стало та-а-ак много, что неплохо было бы узнать их количество.
        if kmUNe.is_user_modified:
            rowRestore = rowLabelMain.row(align=True)
            with LyAddQuickInactiveCol(rowRestore, align=False) as row:
                row.prop(self,'vaInfoRestore', text="", icon='INFO', emboss=False)
            rowRestore.context_pointer_set('keymap', kmUNe)
            rowRestore.operator('preferences.keymap_restore', text="Restore")
        else:
            rowLabelMain.label()
        rowAddNew = rowLabelMain.row(align=True)
        rowAddNew.ui_units_x = 12
        rowAddNew.separator()
        rowAddNew.operator(VoronoiOpAddonTabs.bl_idname, text="Add New", icon='NONE').opt = 'AddNewKmi' #NONE  ADD
        def LyAddKmisCategory(where, cat):
            if not cat.set_kmis:
                return
            colListCat = where.row().column(align=True)
            txt = self.bl_rna.properties[cat.propName].name
            if not LyAddDisclosureProp(colListCat, self, cat.propName, txt=TranslateIface(txt)+f" ({cat.sco})", active=False, isWide=1-1):
                return
            for li in sorted(cat.set_kmis, key=lambda a:a.id):
                colListCat.context_pointer_set('keymap', kmUNe)
                rna_keymap_ui.draw_kmi([], bpy.context.window_manager.keyconfigs.user, kmUNe, li, colListCat, 0) #Заметка: Если colListCat будет не colListCat, то возможность удаления kmi станет недоступной.
        LyAddKmisCategory(colList, kmiCats.cus)
        LyAddKmisCategory(colList, kmiCats.grt)
        LyAddKmisCategory(colList, kmiCats.oth)
        LyAddKmisCategory(colList, kmiCats.spc)
        LyAddKmisCategory(colList, kmiCats.qqm)
        rowLabelPost.label(text=f"({scoAll})", translate=False)

    def LyDrawTabInfo(self, where):
        def LyAddUrlHl(where, text, url, txtHl=""):
            row = where.row(align=True)
            row.alignment = 'LEFT'
            if txtHl:
                txtHl = "#:~:text="+txtHl
            row.operator('wm.url_open', text=text, icon='URL').url=url+txtHl
            row.label()
        colMain = where.column()
        with LyAddQuickInactiveCol(colMain, att='column') as row:
            row.alignment = 'LEFT'
            row.label(text=txt_addonVerDateCreated)
            row.label(text=txt_addonBlVerSupporting)
        colUrls = colMain.column()
        LyAddUrlHl(colUrls, "Check for updates yourself", "https://github.com/ugorek000/VoronoiLinker", txtHl="Latest%20version")
        LyAddUrlHl(colUrls, "VL Wiki", bl_info['wiki_url'])
        LyAddUrlHl(colUrls, "RANTO Git", "https://github.com/ugorek000/RANTO")
        colUrls.separator()
        LyAddUrlHl(colUrls, "Event Type Items", "https://docs.blender.org/api/current/bpy_types_enum_items/event_type_items.html")
        LyAddUrlHl(colUrls, "Translator guide", "https://developer.blender.org/docs/handbook/translating/translator_guide/")
        LyAddUrlHl(colUrls, "Translator dev guide", "https://developer.blender.org/docs/handbook/translating/developer_guide/")
        ##
        colMain.separator()
        row = colMain.row(align=True)
        row.alignment = 'LEFT'
        row.operator(VoronoiOpAddonTabs.bl_idname, text=txt_copySettAsPyScript, icon='COPYDOWN').opt = 'GetPySett' #SCRIPT  COPYDOWN
        with LyAddQuickInactiveCol(colMain, active=self.dsIncludeDev) as row:
            row.prop(self,'dsIncludeDev')
        ##
        LyAddThinSep(colMain, 0.15)
        rowSettings = colMain.box().row(align=True)
        row = rowSettings.row(align=True)
        row.ui_units_x = 20
        view = bpy.context.preferences.view
        row.prop(view,'language', text="")
        row = rowSettings.row(align=True)
        langCode = view.language
        row.label(text=f"   '{langCode}'   ", translate=False)
        #row = rowSettings.row(align=True)
        #row.alignment = 'RIGHT'
        row.prop(view,'use_translate_interface', text="Interface")
        row.prop(view,'use_translate_tooltips', text="Tooltips")
        ##
        colVlTools = colMain.column(align=True)
        for cls in list_toolClasses:
            if txtToolInfo:=dict_toolLangSpecifDataPool.get((cls, langCode), ""):
                colDiscl = colVlTools.column(align=True)
                rowLabel = colDiscl.row(align=True)
                if LyAddDisclosureProp(rowLabel, self, cls.disclBoxPropNameInfo, txt=cls.bl_label+" Tool"):
                    rowTool = colDiscl.row(align=True)
                    rowTool.label(icon='BLANK1')
                    rowTool.label(icon='BLANK1')
                    colText = rowTool.column(align=True)
                    for li in txtToolInfo.split("\n"):
                        colText.label(text=li, translate=False)
                with LyAddQuickInactiveCol(rowLabel, att='row') as row:
                    row.alignment = 'LEFT'
                    row.label(text=f"({cls.vlTripleName})", translate=False)
                    row.alignment = 'EXPAND'
                    #row.prop(self, cls.disclBoxPropNameInfo, text=" ", translate=False, emboss=False)
        ##
        colLangDebug = colMain.column(align=True)
        if (self.dsIncludeDev)or(self.vaLangDebDiscl):
            with LyAddQuickInactiveCol(colLangDebug, active=self.vaLangDebDiscl) as row:
                row.prop(self,'vaLangDebDiscl')
        if self.vaLangDebDiscl:
            row = colLangDebug.row(align=True)
            row.alignment = 'LEFT'
            row.label(text=f"[{langCode}]", translate=False)
            row.label(text="–", translate=False)
            if langCode in dict_vlHhTranslations:
                dict_copy = dict_vlHhTranslations[langCode].copy()
                del dict_copy['trans']
                row.label(text=repr(dict_copy), translate=False)
            else:
                with LyAddQuickInactiveCol(row) as row:
                    row.label(text="{}", translate=False)
            colLangDebug.row().prop(self,'vaLangDebEnum', expand=True)
            def LyAddAlertNested(where, text):
                with LyAddQuickInactiveCol(where) as row:
                    row.label(text=text, translate=False)
                row = where.row(align=True)
                row.label(icon='BLANK1')
                return row.column(align=True)
            def LyAddTran(where, label, text, *, dot="."):
                rowRoot = where.row(align=True)
                with LyAddQuickInactiveCol(rowRoot) as row:
                    row.alignment = 'LEFT'
                    row.label(text=label+": ", translate=False)
                row = rowRoot.row(align=True)
                col = row.column(align=True)
                text = TranslateIface(text)
                if text:
                    list_split = text.split("\n")
                    hig = length(list_split)-1
                    for cyc, li in enumerate(list_split):
                        col.label(text=li+(dot if cyc==hig else ""), translate=False)
            def LyAddTranDataForProp(where, pr, dot="."):
                colRoot = where.column(align=True)
                with LyAddQuickInactiveCol(colRoot) as row:
                    row.label(text=pr.identifier, translate=False)
                row = colRoot.row(align=True)
                row.label(icon='BLANK1')
                col2 = row.column(align=True)
                LyAddTran(col2, "Name", pr.name, dot="")
                if pr.description:
                    LyAddTran(col2, "Description", pr.description, dot=dot)
                if type(pr)==typeEnum:
                    for en in pr.enum_items:
                        LyAddTranDataForProp(col2, en, dot="")
            typeEnum = bpy.types.EnumProperty
            match self.vaLangDebEnum:
                case 'FREE':
                    txt = TranslateIface("Free")
                    col = LyAddAlertNested(colLangDebug, f"{txt}")
                    col.label(text="Virtual")
                    col.label(text="Colored")
                    col.label(text="Restore")
                    col.label(text="Add New")
                    col.label(text="Edge pan")
                    with LyAddQuickInactiveCol(col, att='column') as col0:
                        col0.label(text="Zoom factor")
                        col0.label(text="Speed")
                    col.label(text="Pie")
                    col.label(text="Box ")
                    col.label(text="Special")
                    col.label(text="Colors")
                    col.label(text="Customization")
                    col.label(text="Advanced")
                    col.label(text=txt_FloatQuickMath)
                    col.label(text=txt_VectorQuickMath)
                    col.label(text=txt_BooleanQuickMath)
                    col.label(text=txt_ColorQuickMode)
                    col.label(text=txt_vmtNoMixingOptions)
                    col.label(text=txt_vqmtThereIsNothing)
                    col.label(text=bl_info['description'])
                    col.label(text=txt_addonVerDateCreated)
                    col.label(text=txt_addonBlVerSupporting)
                    col.label(text=txt_onlyFontFormat)
                    col.label(text=txt_copySettAsPyScript)
                    col.label(text=txt_сheckForUpdatesYourself)
                case 'SPECIAL':
                    txt = TranslateIface("Special")
                    col0 = LyAddAlertNested(colLangDebug, f"[{txt}]")
                    col1 = LyAddAlertNested(col0, "VMT")
                    for dv in dict_vmtMixerNodesDefs.values():
                        col1.label(text=dv[2])
                    col1 = LyAddAlertNested(col0, "VQMT")
                    for di in dict_vqmtQuickMathMain.items():
                        col2 = LyAddAlertNested(col1, di[0])
                        for ti in di[1]:
                            if ti[0]:
                                col2.label(text=ti[0])
                case 'ADDONPREFS':
                    col = LyAddAlertNested(colLangDebug, "[AddonPrefs]")
                    set_toolBoxDisctPropNames = set([cls.disclBoxPropName for cls in list_toolClasses])|set([cls.disclBoxPropNameInfo for cls in list_toolClasses])
                    set_toolBoxDisctPropNames.update({'vaLangDebEnum'})
                    for pr in self.bl_rna.properties[2:]:
                        if pr.identifier not in set_toolBoxDisctPropNames:
                            LyAddTranDataForProp(col, pr)
                case _:
                    dict_toolBlabToCls = {cls.bl_label.upper():cls for cls in list_toolClasses}
                    set_alreadyDone = set() #Учитывая разделение с помощью vaLangDebEnum, уже бесполезно.
                    col0 = colLangDebug.column(align=True)
                    cls = dict_toolBlabToCls[self.vaLangDebEnum]
                    col1 = LyAddAlertNested(col0, cls.bl_label)
                    rna = eval(f"bpy.ops.{cls.bl_idname}.get_rna_type()") #Через getattr какого-то чёрта не работает `getattr(bpy.ops, cls.bl_idname).get_rna_type()`.
                    for pr in rna.properties[1:]: #Пропуск rna_type.
                        rowLabel = col1.row(align=True)
                        if pr.identifier not in set_alreadyDone:
                            LyAddTranDataForProp(rowLabel, pr)
                            set_alreadyDone.add(pr.identifier)
class VoronoiAddonPrefs(VoronoiAddonPrefs):
    def draw(self, context):
        def LyAddDecorLyColRaw(where, sy=0.05, sx=1.0, en=False):
            where.prop(self,'vaDecorLy', text="")
            where.scale_x = sx
            where.scale_y = sy #Если будет меньше, чем 0.05, то макет исчезнет, и угловатость пропадёт.
            where.enabled = en
        colLy = self.layout.column()
        colMain = colLy.column(align=True)
        colTabs = colMain.column(align=True)
        rowTabs = colTabs.row(align=True)
        #Переключение вкладок создано через оператор, чтобы случайно не сменить вкладку при ведении зажатой мышки, кой есть особый соблазн с таким большим количеством "isColored".
        #А также теперь они задекорены ещё больше под "вкладки", чего нельзя сделать с обычным макетом prop'а с 'expand=True'.
        for cyc, li in enumerate(en for en in self.rna_type.properties['vaUiTabs'].enum_items):
            col = rowTabs.row().column(align=True)
            col.operator(VoronoiOpAddonTabs.bl_idname, text=TranslateIface(li.name), depress=self.vaUiTabs==li.identifier).opt = li.identifier
            #Теперь ещё больше похожи на вкладки
            LyAddDecorLyColRaw(col.row(align=True)) #row.operator(VoronoiOpAddonTabs.bl_idname, text="", emboss=False) #Через оператор тоже работает.
            #col.scale_x = min(1.0, (5.5-cyc)/2)
        colBox = colTabs.column(align=True)
        #LyAddDecorLyColRaw(colBox.row(align=True))
        #LyAddDecorLyColRaw(colBox.row(align=True), sy=0.25) #Коробка не может сузиться меньше, чем своё пустое состояние. Пришлось искать другой способ..
        try:
            match self.vaUiTabs:
                case 'SETTINGS':
                    self.LyDrawTabSettings(colMain)
                case 'APPEARANCE':
                    self.LyDrawTabAppearance(colMain)
                case 'DRAW':
                    self.LyDrawTabDraw(colMain)
                case 'KEYMAP':
                    self.LyDrawTabKeymaps(colMain)
                case 'INFO':
                    self.LyDrawTabInfo(colMain)
        except Exception as ex:
            LyAddEtb(colMain) #colMain.label(text=str(ex), icon='ERROR', translate=False)

list_classes += [VoronoiOpAddonTabs, VoronoiAddonPrefs]

list_addonKeymaps = []

isRegisterFromMain = False
def register():
    for li in list_classes:
        bpy.utils.register_class(li)
    ##
    prefs = Prefs()
    prefs.dev = random.random()
    if not isRegisterFromMain:
        prefs.vlnstLastExecError = ""
        prefs.vaLangDebDiscl = False
        for cls in list_toolClasses:
            setattr(prefs, cls.disclBoxPropNameInfo, False)
        prefs.dsIsTestDrawing = False
    ##
    kmANe = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Node Editor", space_type='NODE_EDITOR')
    for blid, key, shift, ctrl, alt, repeat, dict_props in list_kmiDefs:
        kmi = kmANe.keymap_items.new(idname=blid, type=key, value='PRESS', shift=shift, ctrl=ctrl, alt=alt, repeat=repeat)
        kmi.active = blid!='node.voronoi_dummy'
        if dict_props:
            for dk, dv in dict_props.items():
                setattr(kmi.properties, dk, dv)
        list_addonKeymaps.append(kmi)
    ##
    RegisterTranslations()
    RegisterSolderings()
def unregister():
    UnregisterSolderings()
    UnregisterTranslations()
    ##
    kmANe = bpy.context.window_manager.keyconfigs.addon.keymaps["Node Editor"]
    for li in list_addonKeymaps:
        kmANe.keymap_items.remove(li)
    list_addonKeymaps.clear()
    ##
    for li in reversed(list_classes):
        bpy.utils.unregister_class(li)

#Мой гит в bl_info, это конечно же круто, однако было бы неплохо иметь ещё и явно указанные способы связи:
#  coaltangle@gmail.com
#  ^ Моя почта. Если вдруг случится апокалипсис, или эта VL-археологическая-находка сможет решить не-полиномиальную задачу, то писать туда.
# Для более реалтаймового общения (предпочтительно) и по вопросам о VL и его коде пишите на мой дискорд 'ugorek#6434'.
# А ещё есть тема на blenderartists.org/t/voronoi-linker-addon-node-wrangler-killer

def DisableKmis(): #Для повторных запусков скрипта. Работает до первого "Restore".
    kmUNe = GetUserKmNe()
    for li, *oi in list_kmiDefs:
        for kmiCon in kmUNe.keymap_items:
            if li==kmiCon.idname:
                kmiCon.active = False #Это удаляет дубликаты. Хак?
                kmiCon.active = True #Вернуть обратно, если оригинал.
if __name__=="__main__":
    DisableKmis() #Кажется не важно в какой очерёдности вызывать, перед или после добавления хоткеев.
    isRegisterFromMain = True
    register()
