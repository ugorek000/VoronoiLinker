### BEGIN LICENSE BLOCK
# I don't understand about licenses.
# Do what you want with it.
### END LICENSE BLOCK
bl_info = {'name': 'Voronoi Linker', 'author': 'ugorek', 'version': (1, 9, 1), 'blender': (3, 5, 0),  # 05.04.2023
           'description': 'Simplification of create node links.', 'location': 'Node Editor > Alt + RMB', 'warning': '',
           'category': 'Node', 'wiki_url': 'https://github.com/ugorek000/VoronoiLinker/blob/main/README.md',
           'tracker_url': 'https://github.com/ugorek000/VoronoiLinker/issues'}
# Этот аддон является самописом лично для меня, который я сделал публичным для всех желающих. Наслаждайтесь!
# This addon is a self-writing for me personally, which I made publicly available to everyone wishing. Enjoy!

from builtins import len as length
import bpy, bgl, blf, gpu
from gpu_extras.batch import batch_for_shader as BatchForShader
from mathutils import Vector
from math import pi, inf, sin, cos, copysign

# TODO: Ужасный бардак. Было бы не плохо навести здесь полный рефакторинг. Жаль навыков не хватает D:
gv_shaders = [None, None]
gv_uifac = [1.0]
gv_font_id = [0]
gv_where = [None]


def DrawWay(vtxs, vcol, siz):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    gv_shaders[0].bind()
    bgl.glLineWidth(siz)
    BatchForShader(gv_shaders[0], 'LINE_STRIP', {'pos': vtxs, 'color': vcol}).draw(gv_shaders[0])


def DrawAreaFan(vtxs, col, sm):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_POLYGON_SMOOTH) if sm else bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
    gv_shaders[1].bind()
    gv_shaders[1].uniform_float('color', col)
    BatchForShader(gv_shaders[1], 'TRI_FAN', {'pos': vtxs}).draw(gv_shaders[1])


def DrawLine(ps1, ps2, sz=1, cl1=(1.0, 1.0, 1.0, 0.75), cl2=(1.0, 1.0, 1.0, 0.75), fs=[0, 0]):
    DrawWay(((ps1[0] + fs[0], ps1[1] + fs[1]), (ps2[0] + fs[0], ps2[1] + fs[1])), (cl1, cl2), sz)


def DrawCircleOuter(pos, rd, siz=1, col=(1.0, 1.0, 1.0, 0.75), resolution=16):
    vtxs = []
    vcol = []
    for cyc in range(resolution + 1):
        vtxs.append((
        rd * cos(cyc * 2 * pi / resolution) + pos[0], rd * sin(cyc * 2 * pi / resolution) + pos[1])); vcol.append(col)
    DrawWay(vtxs, vcol, siz)


def DrawCircle(pos, rd, col=(1.0, 1.0, 1.0, 0.75), resl=54):
    DrawAreaFan([(pos[0], pos[1]),
                 *[(rd * cos(i * 2 * pi / resl) + pos[0], rd * sin(i * 2 * pi / resl) + pos[1]) for i in
                     range(resl + 1)]], col, True)


def DrawWidePoint(pos, rd, colfac=Vector((1, 1, 1, 1))):
    col1 = Vector((0.5, 0.5, 0.5, 0.4))
    col2 = Vector((0.5, 0.5, 0.5, 0.4))
    col3 = Vector((1, 1, 1, 1))
    colfac = colfac if GetAddonPrefs().ds_is_colored_point else Vector((1, 1, 1, 1))
    rd = (rd * rd + 10) ** .5
    rs = GetAddonPrefs().ds_point_resolution
    DrawCircle(pos, rd + 3, col1 * colfac, rs)
    DrawCircle(pos, rd, col2 * colfac, rs)
    DrawCircle(pos, rd / 1.5, col3 * colfac, rs)


def DrawRectangle(ps1, ps2, cl):
    DrawAreaFan([(ps1[0], ps1[1]), (ps2[0], ps1[1]), (ps2[0], ps2[1]), (ps1[0], ps2[1])], cl, False)


def DrawRectangleOnSocket(sk, stEn, colfac=Vector((1, 1, 1, 1))):
    if GetAddonPrefs().ds_is_draw_area == False:
        return
    loc = RecrGetNodeFinalLoc(sk.node).copy() * gv_uifac[0]
    pos1 = PosViewToReg(loc.x, stEn[0] * gv_uifac[0])
    colfac = colfac if GetAddonPrefs().ds_is_colored_area else Vector((1, 1, 1, 1))
    pos2 = PosViewToReg(loc.x + sk.node.dimensions.x, stEn[1] * gv_uifac[0])
    DrawRectangle(pos1, pos2, Vector((1.0, 1.0, 1.0, 0.075)) * colfac)


def DrawIsLinked(loc, ofsx, ofsy, sk_col):
    ofsx += ((20 + GetAddonPrefs().ds_text_dist_from_cursor) * 1.5 + GetAddonPrefs().ds_text_frame_offset) * copysign(1,
                                                                                                                      ofsx) + 4
    if GetAddonPrefs().ds_is_draw_marker == False:
        return
    vec = PosViewToReg(loc.x, loc.y)
    gc = 0.65
    col1 = (0, 0, 0, 0.5)
    col2 = (gc, gc, gc, max(max(sk_col[0], sk_col[1]), sk_col[2]) * .9)
    col3 = (sk_col[0], sk_col[1], sk_col[2], .925)
    DrawCircleOuter([vec[0] + ofsx + 1.5, vec[1] + 3.5 + ofsy], 9.0, 3.0, col1)
    DrawCircleOuter([vec[0] + ofsx - 3.5, vec[1] - 5 + ofsy], 9.0, 3.0, col1)
    DrawCircleOuter([vec[0] + ofsx, vec[1] + 5 + ofsy], 9.0, 3.0, col2)
    DrawCircleOuter([vec[0] + ofsx - 5, vec[1] - 3.5 + ofsy], 9.0, 3.0, col2)
    DrawCircleOuter([vec[0] + ofsx, vec[1] + 5 + ofsy], 9.0, 1.0, col3)
    DrawCircleOuter([vec[0] + ofsx - 5, vec[1] - 3.5 + ofsy], 9.0, 1.0, col3)


def DrawText(pos, ofsx, ofsy, txt, draw_col):
    isdrsh = GetAddonPrefs().ds_is_draw_sk_text_shadow
    if isdrsh:
        blf.enable(gv_font_id[0], blf.SHADOW)
        sdcol = GetAddonPrefs().ds_shadow_col
        blf.shadow(gv_font_id[0], [0, 3, 5][GetAddonPrefs().ds_shadow_blur], sdcol[0], sdcol[1], sdcol[2], sdcol[3])
        sdofs = GetAddonPrefs().ds_shadow_offset
        blf.shadow_offset(gv_font_id[0], sdofs[0], sdofs[1])
    else:
        blf.disable(gv_font_id[0], blf.SHADOW)
    tof = GetAddonPrefs().ds_text_frame_offset
    txsz = GetAddonPrefs().ds_font_size
    blf.size(gv_font_id[0], txsz, 72)
    txdim = [blf.dimensions(gv_font_id[0], txt)[0], blf.dimensions(gv_font_id[0], '█')[1]]
    pos = [pos[0] - (txdim[0] + tof + 10) * (ofsx < 0) + (tof + 1) * (ofsx > -1), pos[1] + tof]
    pw = 1 / 1.975
    muv = round((txdim[1] + tof * 2) * ofsy)
    pos1 = [pos[0] + ofsx - tof, pos[1] + muv - tof]
    pos2 = [pos[0] + ofsx + 10 + txdim[0] + tof, pos[1] + muv + txdim[1] + tof]
    list = [.4, .55, .7, .85, 1]
    uh = 1 / len(list) * (txdim[1] + tof * 2)
    if GetAddonPrefs().ds_text_style == 'Classic':
        for cyc in range(len(list)):
            DrawRectangle([pos1[0], pos1[1] + cyc * uh], [pos2[0], pos1[1] + cyc * uh + uh],
                          (draw_col[0] / 2, draw_col[1] / 2, draw_col[2] / 2, list[cyc]))
        col = (draw_col[0] ** pw, draw_col[1] ** pw, draw_col[2] ** pw, 1)
        DrawLine(pos1, [pos2[0], pos1[1]], 1, col, col)
        DrawLine([pos2[0], pos1[1]], pos2, 1, col, col)
        DrawLine(pos2, [pos1[0], pos2[1]], 1, col, col)
        DrawLine([pos1[0], pos2[1]], pos1, 1, col, col)
        col = (col[0], col[1], col[2], .375)
        thS = GetAddonPrefs().ds_text_lineframe_offset
        DrawLine(pos1, [pos2[0], pos1[1]], 1, col, col, [0, -thS])
        DrawLine([pos2[0], pos1[1]], pos2, 1, col, col, [+thS, 0])
        DrawLine(pos2, [pos1[0], pos2[1]], 1, col, col, [0, +thS])
        DrawLine([pos1[0], pos2[1]], pos1, 1, col, col, [-thS, 0])
        DrawLine([pos1[0] - thS, pos1[1]], [pos1[0], pos1[1] - thS], 1, col, col)
        DrawLine([pos2[0] + thS, pos1[1]], [pos2[0], pos1[1] - thS], 1, col, col)
        DrawLine([pos2[0] + thS, pos2[1]], [pos2[0], pos2[1] + thS], 1, col, col)
        DrawLine([pos1[0] - thS, pos2[1]], [pos1[0], pos2[1] + thS], 1, col, col)
    elif GetAddonPrefs().ds_text_style == 'Simplified':
        DrawRectangle([pos1[0], pos1[1]], [pos2[0], pos2[1]],
                      (draw_col[0] / 2.4, draw_col[1] / 2.4, draw_col[2] / 2.4, .8))
        col = (.1, .1, .1, .95)
        DrawLine(pos1, [pos2[0], pos1[1]], 2, col, col)
        DrawLine([pos2[0], pos1[1]], pos2, 2, col, col)
        DrawLine(pos2, [pos1[0], pos2[1]], 2, col, col)
        DrawLine([pos1[0], pos2[1]], pos1, 2, col, col)
    blf.position(gv_font_id[0], pos[0] + ofsx + 3.5, pos[1] + muv + txdim[1] * .3, 0)
    blf.color(gv_font_id[0], draw_col[0] ** pw, draw_col[1] ** pw, draw_col[2] ** pw, 1.0)
    blf.draw(gv_font_id[0], txt)
    return [txdim[0] + tof, txdim[1] + tof * 2]


def DrawSkText(pos, ofsx, ofsy, Sk):
    if GetAddonPrefs().ds_is_draw_sk_text == False:
        return [0, 0]
    try:
        sk_col = GetSkCol(Sk)
    except:
        sk_col = (1, 0, 0, 1)
    sk_col = sk_col if GetAddonPrefs().ds_is_colored_sk_text else (.9, .9, .9, 1)
    txt = Sk.name if Sk.bl_idname != 'NodeSocketVirtual' else 'Virtual'
    return DrawText(pos, ofsx, ofsy, txt, sk_col)


def GetSkCol(Sk):
    return Sk.draw_color(bpy.context, Sk.node)


def Vec4Pow(vec, pw):
    return Vector((vec.x ** pw, vec.y ** pw, vec.z ** pw, vec.w ** pw))


def GetSkVecCol(Sk, apw):
    return Vec4Pow(Vector(Sk.draw_color(bpy.context, Sk.node)), 1 / apw)


def GetAddonPrefs():
    return bpy.context.preferences.addons[__name__ if __name__ != '__main__' else 'VoronoiLinker'].preferences


def SetFont():
    gv_font_id[0] = blf.load(r'C:\Windows\Fonts\consola.ttf')
    gv_font_id[0] = 0 if gv_font_id[0] == -1 else gv_font_id[
        0]  # for change Blender themes


def PosViewToReg(x, y):
    return bpy.context.region.view2d.view_to_region(x, y, clip=False)


def PreparGetWP(loc, offsetx):
    pos = PosViewToReg(loc.x + offsetx, loc.y)
    rd = \
        PosViewToReg(loc.x + offsetx + 6 * GetAddonPrefs().ds_point_radius, loc.y)[0] - pos[0]; return pos, rd


def DebugDrawCallback(sender, context):
    def DrawDbText(pos, txt, r=1, g=1, b=1):
        blf.size(gv_font_id[0], 14, 72)
        blf.position(gv_font_id[0], pos[0] + 10, pos[1], 0)
        blf.color(gv_font_id[0], r, g, b, 1.0)
        blf.draw(gv_font_id[0], txt)

    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    wp = PreparGetWP(mouse_pos, 0)
    DrawWidePoint(wp[0], wp[1])
    DrawDbText(PosViewToReg(mouse_pos[0], mouse_pos[1]), 'Cursor position here.')
    list_nodes = GenNearestNodeList(context.space_data.edit_tree.nodes, mouse_pos)
    sco = 0
    for li in list_nodes:
        if li[1].type != 'FRAME':
            wp = PreparGetWP(li[2], 0); DrawWidePoint(wp[0], wp[1], Vector((1, .5, .5, 1)))
            DrawDbText(wp[0],
                       str(sco) + ' Node goal here',
                       g=.5,
                       b=.5); sco += 1
    list_socket_in, list_socket_out = GenNearestSocketsList(list_nodes[0][1], mouse_pos)
    if list_socket_out:
        wp = PreparGetWP(list_socket_out[0][2], 0); DrawWidePoint(wp[0], wp[1], Vector((.5, .5, 1, 1)))
        DrawDbText(
                wp[0], 'Nearest socketOut here', r=.75, g=.75)
    if list_socket_in:
        wp = PreparGetWP(list_socket_in[0][2], 0); DrawWidePoint(wp[0], wp[1], Vector((.5, 1, .5, 1)))
        DrawDbText(
                wp[0], 'Nearest socketIn here', r=.5, b=.5)


def UiScale():
    return bpy.context.preferences.system.dpi * bpy.context.preferences.system.pixel_size / 72


def RecrGetNodeFinalLoc(nd):
    return nd.location if nd.parent == None else nd.location + RecrGetNodeFinalLoc(nd.parent)


def GenNearestNodeList(nodes,
                       pick_pos):  # Выдаёт список "ближайших нод". Честное поле расстояний. Спасибо RayMarching'у, без него я бы до такого не допёр.
    def ToSign(vec2):
        return Vector((copysign(1, vec2[0]), copysign(1, vec2[1])))  # Для запоминания своего квадранта перед abs().

    list_nodes = []
    for nd in nodes:
        # Расчехлить иерархию родителей и получить итоговую позицию нода. Подготовить размер нода
        nd_location = RecrGetNodeFinalLoc(nd)
        nd_size = Vector((4, 4)) if nd.bl_idname == 'NodeReroute' else nd.dimensions / UiScale()
        # Для рероута позицию в центр. Для нода позицию в нижний левый угол, чтобы быть миро-ориентированным и спокойно прибавлять половину размера нода
        nd_location = nd_location - nd_size / 2 if nd.bl_idname == 'NodeReroute' else nd_location - Vector(
                (0, nd_size[1]))
        # field_uv -- сырой от pick_pos. field_xy -- абсолютные предыдущего, нужен для восстановления направления
        field_uv = pick_pos - (nd_location + nd_size / 2)
        field_xy = Vector((abs(field_uv.x), abs(field_uv.y))) - nd_size / 2
        # Сконструировать внутренности чтобы корректно находить ближайшего при наслаивающихся нодов
        field_en = ToSign(field_xy)
        field_en = min(abs(field_xy.x), abs(field_xy.y)) * (field_en.x + field_en.y == -2)
        field_xy = Vector((max(field_xy.x, 0), max(field_xy.y, 0)))
        # Добавить в список отработанный нод. Ближайшая позиция = курсор - восстановленное направление
        list_nodes.append((field_xy.length + field_en, nd, pick_pos - field_xy * ToSign(field_uv)))
    list_nodes.sort(key=lambda list_nodes: list_nodes[0])
    return list_nodes


def GenNearestSocketsList(nd,
                          pick_pos):  # Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного.
    list_socket_in = []
    list_socket_out = []
    # Обработать исключающую ситуацию, когда искать не у кого
    if nd == None:
        return [], []
    # Так же расшифровать иерархию родителей, как и в поиске ближайшего нода, потому что теперь ищутся сокеты
    nd_location = RecrGetNodeFinalLoc(nd)
    nd_dim = Vector(nd.dimensions / UiScale())
    # Если рероут, то имеем простой вариант не требующий вычисления; вход и выход всего одни, позиция сокета -- он сам
    if nd.bl_idname == 'NodeReroute':
        len = Vector(pick_pos - nd_location).length
        list_socket_in.append([len, nd.inputs[0], nd_location, (-1, -1)])
        list_socket_out.append([len, nd.outputs[0], nd_location, (-1, -1)])
        return list_socket_in, list_socket_out

    def GetFromPut(side_mark, who_puts):
        list_whom = []
        # Установить "каретку" в первый сокет своей стороны. Верхний если выход, нижний если вход
        sk_loc_car = Vector((nd_location.x + nd_dim.x, nd_location.y - 35)) if side_mark == 1 else Vector(
                (nd_location.x, nd_location.y - nd_dim.y + 16))
        for wh in who_puts:
            # Игнорировать выключенные и спрятанные
            if (wh.enabled) and (wh.hide == False):
                muv = 0  # для высоты варпа от вектор-сокетов-не-в-одну-строчку.
                # Если текущий сокет -- входящий вектор, и он же свободный и не спрятан в одну строчку
                if (side_mark == -1) and (wh.type == 'VECTOR') and (wh.is_linked == False) and (wh.hide_value == False):
                    # Ручками вычисляем занимаемую высоту сокета.
                    # Для сферы направления у ShaderNodeNormal и таких же у групп. И для особо-отличившихся нод с векторами, которые могут быть в одну строчку
                    if str(wh.bl_rna).find('VectorDirection') != -1:
                        sk_loc_car.y += 20 * 2
                        muv = 2
                    elif ((nd.type in ('BSDF_PRINCIPLED', 'SUBSURFACE_SCATTERING')) == False) or (
                            (wh.name in ('Subsurface Radius', 'Radius')) == False):
                        sk_loc_car.y += 30 * 2
                        muv = 3
                goal_pos = sk_loc_car.copy()
                # skHigLigHei так же учитывает текущую высоту мульти-инпута подсчётом количества соединений, но только для входов
                list_whom.append([(pick_pos - sk_loc_car).length, wh, goal_pos, (goal_pos.y - 11 - muv * 20,
                                                                                 goal_pos.y + 11 + max(
                                                                                     length(wh.links) - 2, 0) * 5 * (
                                                                                             side_mark == -1))])
                # Сдвинуть до следующего на своё направление
                sk_loc_car.y -= 22 * side_mark
        return list_whom

    list_socket_in = GetFromPut(-1, reversed(nd.inputs))
    list_socket_out = GetFromPut(1, nd.outputs)
    list_socket_in.sort(key=lambda list_socket_in: list_socket_in[0])
    list_socket_out.sort(key=lambda list_socket_out: list_socket_out[0])
    return list_socket_in, list_socket_out


list_sk_perms = ['VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN']


def VoronoiLinkerDrawCallback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    if GetAddonPrefs().ds_is_draw_debug:
        DebugDrawCallback(sender, context); return
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    lw = GetAddonPrefs().ds_line_width

    def LinkerDrawSk(Sk):
        txtdim = DrawSkText(PosViewToReg(mouse_pos.x, mouse_pos.y),
                            -GetAddonPrefs().ds_text_dist_from_cursor * (Sk.is_output * 2 - 1), -.5, Sk)
        if Sk.is_linked:
            DrawIsLinked(mouse_pos, -txtdim[0] * (Sk.is_output * 2 - 1), 0,
                         GetSkCol(Sk) if GetAddonPrefs().ds_is_colored_marker else (.9, .9, .9, 1))

    if (sender.list_sk_goal_out == []):
        if GetAddonPrefs().ds_is_draw_point:
            wp1 = PreparGetWP(mouse_pos, -GetAddonPrefs().ds_point_offset_x * .75)
            wp2 = PreparGetWP(mouse_pos, GetAddonPrefs().ds_point_offset_x * .75)
            DrawWidePoint(wp1[0], wp1[1])
            DrawWidePoint(wp2[0], wp2[1])
        if (GetAddonPrefs().vlds_is_always_line) and (GetAddonPrefs().ds_is_draw_line):
            DrawLine(wp1[0], wp2[0], lw, (1, 1, 1, 1), (1, 1, 1, 1))
    elif (sender.list_sk_goal_out) and (sender.list_sk_goal_in == []):
        DrawRectangleOnSocket(sender.list_sk_goal_out[1], sender.list_sk_goal_out[3],
                              GetSkVecCol(sender.list_sk_goal_out[1], 2.2))
        wp1 = PreparGetWP(sender.list_sk_goal_out[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
        wp2 = PreparGetWP(mouse_pos, 0)
        if (GetAddonPrefs().vlds_is_always_line) and (GetAddonPrefs().ds_is_draw_line):
            DrawLine(wp1[0], wp2[0], lw,
                     GetSkCol(sender.list_sk_goal_out[1]) if GetAddonPrefs().ds_is_colored_line else (1, 1, 1, 1),
                     (1, 1, 1, 1))
        if GetAddonPrefs().ds_is_draw_point:
            DrawWidePoint(wp1[0], wp1[1], GetSkVecCol(sender.list_sk_goal_out[1], 2.2)); DrawWidePoint(wp2[0], wp2[1])
        LinkerDrawSk(sender.list_sk_goal_out[1])
    else:
        DrawRectangleOnSocket(sender.list_sk_goal_out[1], sender.list_sk_goal_out[3],
                              GetSkVecCol(sender.list_sk_goal_out[1], 2.2))
        DrawRectangleOnSocket(sender.list_sk_goal_in[1], sender.list_sk_goal_in[3],
                              GetSkVecCol(sender.list_sk_goal_in[1], 2.2))
        if GetAddonPrefs().ds_is_colored_line:
            col1 = GetSkCol(sender.list_sk_goal_out[1])
            col2 = GetSkCol(sender.list_sk_goal_in[1])
        else:
            col1 = (1, 1, 1, 1)
            col2 = (1, 1, 1, 1)
        wp1 = PreparGetWP(sender.list_sk_goal_out[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
        wp2 = PreparGetWP(sender.list_sk_goal_in[2] * gv_uifac[0], -GetAddonPrefs().ds_point_offset_x)
        if GetAddonPrefs().ds_is_draw_line:
            DrawLine(wp1[0], wp2[0], lw, col1, col2)
        if GetAddonPrefs().ds_is_draw_point:
            DrawWidePoint(wp1[0], wp1[1], GetSkVecCol(sender.list_sk_goal_out[1], 2.2))
            DrawWidePoint(wp2[0], wp2[1], GetSkVecCol(sender.list_sk_goal_in[1], 2.2))
        LinkerDrawSk(sender.list_sk_goal_out[1])
        LinkerDrawSk(sender.list_sk_goal_in[1])


class VoronoiLinker(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_linker'
    bl_label = 'Voronoi Linker'
    bl_options = {'UNDO'}

    def NextAssign(sender, context, isBoth):
        pick_pos = context.space_data.cursor_location
        list_nodes = GenNearestNodeList(context.space_data.edit_tree.nodes, pick_pos)
        sender.list_sk_goal_in = []  # Если не разрешён, то предыдущий остаётся, что не удобно. Поэтому обнуляется каждый раз перед поиском.
        for li in list_nodes:
            nd = li[1]
            if (nd.type != 'FRAME') and ((nd.hide == False) or (nd.type == 'REROUTE')):
                list_socket_in, list_socket_out = GenNearestSocketsList(nd, pick_pos)
                # Этот инструмент триггерится на любой выход
                if isBoth:
                    sender.list_sk_goal_out = list_socket_out[0] if list_socket_out else []
                # Получить вход по условиям:
                if list_socket_in == []:  # На ноды без входов триггериться, и обнулять предыдущий результат если имеется.
                    sender.list_sk_goal_in = []
                    break  # break можно делать, потому что далее вход искать негде.
                skout = sender.list_sk_goal_out[1] if sender.list_sk_goal_out else None
                if skout:  # Первый заход всегда isBoth=True, однако нод может не иметь выходов.
                    for lsi in list_socket_in:
                        skin = lsi[1]
                        # Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет минуя различные типы
                        tgl = ((skin.type in list_sk_perms) and (skout.type in list_sk_perms) or (
                                skout.node.type == 'REROUTE'))
                        # Любой сокет для виртуального выхода; разрешить в виртуальный для любого сокета. Обоим в себя запретить
                        tgl = (tgl) or (
                                (skin.bl_idname == 'NodeSocketVirtual') ^ (skout.bl_idname == 'NodeSocketVirtual'))
                        # Если имена типов одинаковые, но не виртуальные
                        tgl = (tgl) or (skin.bl_idname == skout.bl_idname) and (
                            not ((skin.bl_idname == 'NodeSocketVirtual') and (skout.bl_idname == 'NodeSocketVirtual')))
                        if tgl:
                            sender.list_sk_goal_in = lsi; break  # Без break'а goal'ом будет самый дальний от курсора, удовлетворяющий условиям.
                    # Финальная проверка на корректность
                    if sender.list_sk_goal_in:
                        if (sender.list_sk_goal_out[1].node == sender.list_sk_goal_in[1].node):
                            sender.list_sk_goal_in = []
                        elif (sender.list_sk_goal_out[1].is_linked):
                            for lk in sender.list_sk_goal_out[1].links:
                                # Выгода от break минимальна, мультиинпуты с большим количеством соединений редки
                                if lk.to_socket == sender.list_sk_goal_in[1]:
                                    sender.list_sk_goal_in = []; break
                break  # Обработать нужно только первый ближайший, удовлетворяющий условиям.

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiLinker.NextAssign(self, context, False)
            case 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if (event.value == 'RELEASE') and (self.list_sk_goal_out) and (self.list_sk_goal_in):
                    tree = context.space_data.edit_tree
                    try:
                        lk = tree.links.new(self.list_sk_goal_out[1], self.list_sk_goal_in[1])
                    except:
                        pass  # NodeSocketUndefined
                    tgl = (lk.from_socket.bl_idname == 'NodeSocketVirtual') + (
                            lk.to_socket.bl_idname == 'NodeSocketVirtual') * 2
                    if tgl > 0:  # В версии 3.5 новый сокет автоматически не создаётся.
                        if tgl == 1:
                            tree.inputs.new(lk.to_socket.bl_idname, lk.to_socket.name)
                            tree.links.remove(lk)
                            tree.links.new(self.list_sk_goal_out[1].node.outputs[-2], self.list_sk_goal_in[1])
                        else:
                            tree.outputs.new(lk.from_socket.bl_idname, lk.from_socket.name)
                            tree.links.remove(lk)
                            tree.links.new(self.list_sk_goal_out[1], self.list_sk_goal_in[1].node.inputs[-2])
                    if self.list_sk_goal_in[
                        1].is_multi_input:  # Если мультиинпут -- реализовать адекватный порядок подключения. Накой смысол последние лепятся в начало?.
                        list_sk_links = []
                        for lk in self.list_sk_goal_in[1].links:
                            list_sk_links.append((lk.from_socket, lk.to_socket)); tree.links.remove(lk)
                        if self.list_sk_goal_out[1].bl_idname == 'NodeSocketVirtual':
                            self.list_sk_goal_out[1] = self.list_sk_goal_out[1].node.outputs[
                                length(self.list_sk_goal_out[1].node.outputs) - 2]
                        tree.links.new(self.list_sk_goal_out[1], self.list_sk_goal_in[1])
                        for cyc in range(0, length(list_sk_links) - 1):
                            tree.links.new(list_sk_links[cyc][0], list_sk_links[cyc][1])
                    return {'FINISHED'}
                else:
                    return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if (context.area.type != 'NODE_EDITOR') or (context.space_data.edit_tree == None):
            return {'CANCELLED'}
        self.list_sk_goal_out = []
        self.list_sk_goal_in = []
        gv_uifac[0] = UiScale()
        gv_where[0] = context.space_data
        SetFont()
        context.area.tag_redraw()
        VoronoiLinker.NextAssign(self, context, True)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiLinkerDrawCallback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def VoronoiMassLinkerDrawCallback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    if GetAddonPrefs().ds_is_draw_debug:
        DebugDrawCallback(sender, context); return
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    lw = GetAddonPrefs().ds_line_width

    def LinkerDrawSk(Sk):
        txtdim = DrawSkText(PosViewToReg(mouse_pos.x, mouse_pos.y),
                            -GetAddonPrefs().ds_text_dist_from_cursor * (Sk.is_output * 2 - 1), -.5, Sk)
        if Sk.is_linked:
            DrawIsLinked(mouse_pos, -txtdim[0] * (Sk.is_output * 2 - 1), 0,
                         GetSkCol(Sk) if GetAddonPrefs().ds_is_colored_marker else (.9, .9, .9, 1))

    def DrawIfNone():
        wp = PreparGetWP(mouse_pos, 0)
        DrawWidePoint(wp[0], wp[1])

    if (sender.nd_goal_out == None):
        DrawIfNone()
    elif (sender.nd_goal_out) and (sender.nd_goal_in == None):
        list_Sks = GenNearestSocketsList(sender.nd_goal_out, mouse_pos)[1]
        if list_Sks == []:
            DrawIfNone()
        for lsk in list_Sks:
            DrawRectangleOnSocket(lsk[1], lsk[3], GetSkVecCol(lsk[1], 2.2))
            wp1 = PreparGetWP(lsk[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
            wp2 = PreparGetWP(mouse_pos, 0)
            if (GetAddonPrefs().vlds_is_always_line) and (GetAddonPrefs().ds_is_draw_line):
                DrawLine(wp1[0], wp2[0], lw, GetSkCol(lsk[1]) if GetAddonPrefs().ds_is_colored_line else (1, 1, 1, 1),
                         (1, 1, 1, 1))
            if GetAddonPrefs().ds_is_draw_point:
                DrawWidePoint(wp1[0], wp1[1], GetSkVecCol(lsk[1], 2.2)); DrawWidePoint(wp2[0], wp2[1])
    else:
        list_SksOut = GenNearestSocketsList(sender.nd_goal_out, mouse_pos)[1]
        list_SksIn = GenNearestSocketsList(sender.nd_goal_in, mouse_pos)[0]
        sender.list_equalSks = []
        for sko in list_SksOut:
            for ski in list_SksIn:
                if (sko[1].name == ski[1].name) and (ski[1].is_linked == False):
                    sender.list_equalSks.append((sko, ski))
                    continue
        if sender.list_equalSks == []:
            DrawIfNone()
        for lsks in sender.list_equalSks:
            DrawRectangleOnSocket(lsks[0][1], lsks[0][3], GetSkVecCol(lsks[0][1], 2.2))
            DrawRectangleOnSocket(lsks[1][1], lsks[1][3], GetSkVecCol(lsks[1][1], 2.2))
            if GetAddonPrefs().ds_is_colored_line:
                col1 = GetSkCol(lsks[0][1])
                col2 = GetSkCol(lsks[1][1])
            else:
                col1 = (1, 1, 1, 1)
                col2 = (1, 1, 1, 1)
            wp1 = PreparGetWP(lsks[0][2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
            wp2 = PreparGetWP(lsks[1][2] * gv_uifac[0], -GetAddonPrefs().ds_point_offset_x)
            if GetAddonPrefs().ds_is_draw_line:
                DrawLine(wp1[0], wp2[0], lw, col1, col2)
            if GetAddonPrefs().ds_is_draw_point:
                DrawWidePoint(wp1[0], wp1[1], GetSkVecCol(lsks[0][1], 2.2))
                DrawWidePoint(wp2[0], wp2[1],
                              GetSkVecCol(lsks[1][1], 2.2))


class VoronoiMassLinker(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_masslinker'
    bl_label = 'Voronoi Linker'
    bl_options = {'UNDO'}

    def NextAssign(sender, context, isBoth):
        pick_pos = context.space_data.cursor_location
        list_nodes = GenNearestNodeList(context.space_data.edit_tree.nodes, pick_pos)
        for li in list_nodes:
            nd = li[1]
            if (nd.type != 'FRAME') and ((nd.hide == False) or (nd.type == 'REROUTE')):
                sender.nd_goal_in = nd
                if isBoth:
                    sender.nd_goal_out = nd
                break
        if sender.nd_goal_out == sender.nd_goal_in:
            sender.nd_goal_in = None

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiMassLinker.NextAssign(self, context, False)
            case 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if (event.value == 'RELEASE') and (self.nd_goal_out) and (self.nd_goal_in):
                    tree = context.space_data.edit_tree
                    for lsks in self.list_equalSks:
                        try:
                            tree.links.new(lsks[0][1], lsks[1][1])
                        except:
                            pass
                    return {'FINISHED'}
                else:
                    return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if (context.area.type != 'NODE_EDITOR') or (context.space_data.edit_tree == None):
            return {'CANCELLED'}
        self.nd_goal_out = None
        self.nd_goal_in = None
        gv_uifac[0] = UiScale()
        gv_where[0] = context.space_data
        SetFont()
        context.area.tag_redraw()
        VoronoiMassLinker.NextAssign(self, context, True)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiMassLinkerDrawCallback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def VoronoiMixerDrawCallback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    mouse_region_pos = PosViewToReg(mouse_pos.x, mouse_pos.y)
    lw = GetAddonPrefs().ds_line_width
    if GetAddonPrefs().ds_is_draw_debug:
        DebugDrawCallback(sender, context); return

    def MixerDrawSk(Sk, ys, lys):
        txtdim = DrawSkText(PosViewToReg(mouse_pos.x, mouse_pos.y), GetAddonPrefs().ds_text_dist_from_cursor, ys, Sk)
        if Sk.is_linked:
            DrawIsLinked(mouse_pos, txtdim[0], txtdim[1] * lys * .75,
                         GetSkCol(Sk) if GetAddonPrefs().ds_is_colored_marker else (.9, .9, .9, 1))

    if (sender.list_sk_goal_out1 == []):
        if GetAddonPrefs().ds_is_draw_point:
            wp1 = PreparGetWP(mouse_pos, -GetAddonPrefs().ds_point_offset_x * .75)
            wp2 = PreparGetWP(mouse_pos, GetAddonPrefs().ds_point_offset_x * .75)
            DrawWidePoint(wp1[0], wp1[1])
            DrawWidePoint(wp2[0], wp2[1])
    elif (sender.list_sk_goal_out1) and (sender.list_sk_goal_out2 == []):
        DrawRectangleOnSocket(sender.list_sk_goal_out1[1], sender.list_sk_goal_out1[3],
                              GetSkVecCol(sender.list_sk_goal_out1[1], 2.2))
        wp1 = PreparGetWP(sender.list_sk_goal_out1[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
        wp2 = PreparGetWP(mouse_pos, 0)
        col = Vector((1, 1, 1, 1))
        if GetAddonPrefs().ds_is_draw_line:
            DrawLine(wp1[0], mouse_region_pos, lw,
                     GetSkCol(sender.list_sk_goal_out1[1]) if GetAddonPrefs().ds_is_colored_line else col, col)
        if GetAddonPrefs().ds_is_draw_point:
            DrawWidePoint(wp1[0], wp1[1], GetSkVecCol(sender.list_sk_goal_out1[1], 2.2)); DrawWidePoint(wp2[0], wp2[1])
        MixerDrawSk(sender.list_sk_goal_out1[1], -.5, 0)
    else:
        DrawRectangleOnSocket(sender.list_sk_goal_out1[1], sender.list_sk_goal_out1[3],
                              GetSkVecCol(sender.list_sk_goal_out1[1], 2.2))
        DrawRectangleOnSocket(sender.list_sk_goal_out2[1], sender.list_sk_goal_out2[3],
                              GetSkVecCol(sender.list_sk_goal_out2[1], 2.2))
        if GetAddonPrefs().ds_is_colored_line:
            col1 = GetSkCol(sender.list_sk_goal_out1[1])
            col2 = GetSkCol(sender.list_sk_goal_out2[1])
        else:
            col1 = (1, 1, 1, 1)
            col2 = (1, 1, 1, 1)
        wp1 = PreparGetWP(sender.list_sk_goal_out1[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
        wp2 = PreparGetWP(sender.list_sk_goal_out2[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
        if GetAddonPrefs().ds_is_draw_line:
            DrawLine(mouse_region_pos, wp2[0], lw, col2, col2); DrawLine(wp1[0], mouse_region_pos, lw, col1, col1)
        if GetAddonPrefs().ds_is_draw_point:
            DrawWidePoint(wp1[0], wp1[1], GetSkVecCol(sender.list_sk_goal_out1[1], 2.2))
            DrawWidePoint(wp2[0], wp2[1], GetSkVecCol(sender.list_sk_goal_out2[1], 2.2))
        MixerDrawSk(sender.list_sk_goal_out1[1], .25, 1)
        MixerDrawSk(sender.list_sk_goal_out2[1], -1.25, -1)


class VoronoiMixer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_mixer'
    bl_label = 'Voronoi Mixer'
    bl_options = {'UNDO'}

    def NextAssign(sender, context, isBoth):
        pick_pos = context.space_data.cursor_location
        list_nodes = GenNearestNodeList(context.space_data.edit_tree.nodes, pick_pos)
        for li in list_nodes:
            nd = li[1]
            if (nd.type != 'FRAME') and ((nd.hide == False) or (nd.type == 'REROUTE')):
                list_socket_in, list_socket_out = GenNearestSocketsList(nd, pick_pos)
                # Этот инструмент триггерится на любой выход для первого
                if isBoth:
                    sender.list_sk_goal_out1 = list_socket_out[0] if list_socket_out else []
                # Для второго по условиям:
                skout1 = sender.list_sk_goal_out1[1] if sender.list_sk_goal_out1 else None
                if skout1:
                    for lso in list_socket_out:
                        skout2 = lso[1]
                        # Критерии типов у Миксера такие же, как и в Линкере
                        tgl = ((skout2.type in list_sk_perms) and (skout1.type in list_sk_perms) or (
                                skout1.node.type == 'REROUTE'))
                        tgl = (tgl) or ((skout2.bl_idname == 'NodeSocketVirtual') ^ (
                                skout1.bl_idname == 'NodeSocketVirtual'))
                        tgl = (tgl) or (skout2.bl_idname == skout1.bl_idname) and (not (
                                (skout2.bl_idname == 'NodeSocketVirtual') and (
                                skout1.bl_idname == 'NodeSocketVirtual')))
                        # Добавляется разрешение для виртуальных в рамках одного нода, чтобы первый клик не выбирал сразу два сокета
                        tgl = (tgl) or (skout1.bl_idname == 'NodeSocketVirtual') and (skout1.node == skout2.node)
                        if tgl:
                            sender.list_sk_goal_out2 = lso; break
                    # Финальная проверка на корректность
                    if sender.list_sk_goal_out2:
                        if (skout1 == sender.list_sk_goal_out2[1]):
                            sender.list_sk_goal_out2 = []
                break

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiMixer.NextAssign(self, context, False)
            case 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if event.value == 'RELEASE':
                    if (self.list_sk_goal_out1) and (self.list_sk_goal_out2):
                        mixerSks[0] = self.list_sk_goal_out1[1]
                        mixerSks[1] = self.list_sk_goal_out2[1]
                        mixerSkTyp[0] = mixerSks[0].type if mixerSks[0].bl_idname != 'NodeSocketVirtual' else mixerSks[
                            1].type
                        if GetAddonPrefs().fm_is_included:
                            tgl0 = GetAddonPrefs().fm_trigger_activate == 'FMA1'
                            displayWho[0] = mixerSks[0].bl_idname == 'NodeSocketVector'
                            Check = lambda sk: sk.bl_idname in ['NodeSocketFloat', 'NodeSocketVector', 'NodeSocketInt']
                            tgl1 = Check(mixerSks[0])
                            tgl2 = Check(mixerSks[1])
                            if (tgl0) and (tgl1) and (tgl2) or (not tgl0) and ((tgl1) or (tgl2)):
                                bpy.ops.node.a_voronoi_fastmath('INVOKE_DEFAULT')
                                return {'FINISHED'}
                        dm = dictMixerMain[context.space_data.tree_type][mixerSkTyp[0]]
                        if len(dm) != 0:
                            if (GetAddonPrefs().vm_is_one_skip) and (len(dm) == 1):
                                DoMix(context, dm[0])
                            else:
                                if GetAddonPrefs().vm_menu_style == 'Pie':
                                    bpy.ops.wm.call_menu_pie(name='VL_MT_voronoi_mixer_menu')
                                else:
                                    bpy.ops.wm.call_menu(name='VL_MT_voronoi_mixer_menu')
                    elif (self.list_sk_goal_out1) and (self.list_sk_goal_out2 == []) and (
                            GetAddonPrefs().fm_is_included):
                        mixerSks[0] = self.list_sk_goal_out1[1]
                        displayWho[0] = mixerSks[0].bl_idname == 'NodeSocketVector'
                        if mixerSks[0].bl_idname in ['NodeSocketFloat', 'NodeSocketVector', 'NodeSocketInt']:
                            bpy.ops.node.a_voronoi_fastmath('INVOKE_DEFAULT')
                    return {'FINISHED'}
                else:
                    return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if (context.area.type != 'NODE_EDITOR') or (context.space_data.edit_tree == None):
            return {'CANCELLED'}
        self.list_sk_goal_out1 = []
        self.list_sk_goal_out2 = []
        gv_uifac[0] = UiScale()
        gv_where[0] = context.space_data
        SetFont()
        context.area.tag_redraw()
        VoronoiMixer.NextAssign(self, context, True)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiMixerDrawCallback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


mixerSks = [None, None]
mixerSkTyp = [None]
dict_mixer_defs = {'GeometryNodeSwitch': [-1, -1, 'Switch'], 'ShaderNodeMixShader': [1, 2, 'Mix'],
                   'ShaderNodeAddShader': [0, 1, 'Add'], 'ShaderNodeMixRGB': [1, 2, 'Mix RGB'],
                   'ShaderNodeMath': [0, 1, 'Max'], 'ShaderNodeVectorMath': [0, 1, 'Max'],
                   'FunctionNodeBooleanMath': [0, 1, 'Or'], 'FunctionNodeCompare': [-1, -1, 'Compare'],
                   'GeometryNodeCurveToMesh': [0, 1, 'Curve to Mesh'],
                   'GeometryNodeInstanceOnPoints': [0, 2, 'Instance on Points'],
                   'GeometryNodeMeshBoolean': [0, 1, 'Boolean'], 'GeometryNodeStringJoin': [1, 1, 'Join'],
                   'GeometryNodeJoinGeometry': [0, 0, 'Join'], 'GeometryNodeGeometryToInstance': [0, 0, 'To Instance'],
                   'CompositorNodeMixRGB': [1, 2, 'Mix'], 'CompositorNodeMath': [0, 1, 'Max'],
                   'CompositorNodeSwitch': [0, 1, 'Switch'], 'CompositorNodeAlphaOver': [1, 2, 'Alpha Over'],
                   'CompositorNodeSplitViewer': [0, 1, 'Split Viewer'],
                   'CompositorNodeSwitchView': [0, 1, 'Switch View'], 'TextureNodeMixRGB': [1, 2, 'Mix'],
                   'TextureNodeMath': [0, 1, 'Max'], 'TextureNodeTexture': [0, 1, 'Texture'],
                   'TextureNodeDistance': [0, 1, 'Distance'], 'ShaderNodeMix': [-1, -1, 'Mix']}
dict_mixer_switch_type = {'VALUE': 'FLOAT', 'INT': 'FLOAT'}
dict_mixer_user_sk_name = {'VALUE': 'Float', 'RGBA': 'Color'}
dict_mixer_mix_int = {'INT': 'VALUE'}


def DoMix(context, who):
    tree = context.space_data.edit_tree
    if tree != None:
        bpy.ops.node.add_node('INVOKE_DEFAULT', type=who, use_transform=True)
        active_nd = tree.nodes.active
        active_nd.width = 140
        match active_nd.bl_idname:
            case 'ShaderNodeMath' | 'ShaderNodeVectorMath' | 'CompositorNodeMath' | 'TextureNodeMath':
                active_nd.operation = 'MAXIMUM'
            case 'FunctionNodeBooleanMath':
                active_nd.operation = 'OR'
            case 'TextureNodeTexture':
                active_nd.show_preview = False
            case 'GeometryNodeSwitch':
                active_nd.input_type = dict_mixer_switch_type.get(mixerSkTyp[0], mixerSkTyp[0])
            case 'FunctionNodeCompare':
                active_nd.data_type = dict_mixer_switch_type.get(mixerSkTyp[0], mixerSkTyp[0])
                active_nd.operation = active_nd.operation if active_nd.data_type != 'FLOAT' else 'EQUAL'
            case 'ShaderNodeMix':
                active_nd.data_type = dict_mixer_switch_type.get(mixerSkTyp[0], mixerSkTyp[0])
        match active_nd.bl_idname:
            case 'GeometryNodeSwitch' | 'FunctionNodeCompare' | 'ShaderNodeMix':
                tgl = active_nd.bl_idname != 'FunctionNodeCompare'
                foundSkList = [sk for sk in (reversed(active_nd.inputs) if tgl else active_nd.inputs) if
                               sk.type == dict_mixer_mix_int.get(mixerSkTyp[0], mixerSkTyp[0])]
                tree.links.new(mixerSks[0], foundSkList[tgl])
                tree.links.new(mixerSks[1], foundSkList[not tgl])
            case _:
                if active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][0]].is_multi_input:
                    tree.links.new(mixerSks[1], active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][1]])
                tree.links.new(mixerSks[0], active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][0]])
                if active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][0]].is_multi_input == False:
                    tree.links.new(mixerSks[1], active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][1]])


class VoronoiMixerMixer(bpy.types.Operator):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = 'Voronoi Mixer Mixer'
    bl_options = {'UNDO'}
    who: bpy.props.StringProperty()

    def execute(self, context):
        DoMix(context, self.who)
        return {'FINISHED'}


dictMixerMain = {'ShaderNodeTree': {'SHADER': ['ShaderNodeMixShader', 'ShaderNodeAddShader'],
                                    'VALUE': ['ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeMath'],
                                    'RGBA': ['ShaderNodeMix', 'ShaderNodeMixRGB'],
                                    'VECTOR': ['ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeVectorMath'],
                                    'INT': ['ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeMath']},
                 'GeometryNodeTree': {
                     'VALUE': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare', 'ShaderNodeMath'],
                     'RGBA': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare'],
                     'VECTOR': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare',
                                'ShaderNodeVectorMath'],
                     'STRING': ['GeometryNodeSwitch', 'FunctionNodeCompare', 'GeometryNodeStringJoin'],
                     'INT': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare', 'ShaderNodeMath'],
                     'GEOMETRY': ['GeometryNodeSwitch', 'GeometryNodeJoinGeometry', 'GeometryNodeInstanceOnPoints',
                                  'GeometryNodeCurveToMesh', 'GeometryNodeMeshBoolean',
                                  'GeometryNodeGeometryToInstance'],
                     'BOOLEAN': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'ShaderNodeMath', 'FunctionNodeBooleanMath'],
                     'OBJECT': ['GeometryNodeSwitch'], 'MATERIAL': ['GeometryNodeSwitch'],
                     'COLLECTION': ['GeometryNodeSwitch'], 'TEXTURE': ['GeometryNodeSwitch'],
                     'IMAGE': ['GeometryNodeSwitch']}, 'CompositorNodeTree': {
        'VALUE': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer',
                  'CompositorNodeSwitchView', 'CompositorNodeMath'],
        'RGBA': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer',
                 'CompositorNodeSwitchView', 'CompositorNodeAlphaOver'],
        'VECTOR': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer',
                   'CompositorNodeSwitchView'],
        'INT': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer', 'CompositorNodeSwitchView',
                'CompositorNodeMath']},
                 'TextureNodeTree': {'VALUE': ['TextureNodeMixRGB', 'TextureNodeMath', 'TextureNodeTexture'],
                                     'RGBA': ['TextureNodeMixRGB', 'TextureNodeTexture'],
                                     'VECTOR': ['TextureNodeMixRGB', 'TextureNodeDistance'],
                                     'INT': ['TextureNodeMixRGB', 'TextureNodeMath', 'TextureNodeTexture']}}


class VoronoiMixerMenu(bpy.types.Menu):
    bl_idname = 'VL_MT_voronoi_mixer_menu'
    bl_label = ''

    def draw(self, context):
        who = self.layout.menu_pie() if GetAddonPrefs().vm_menu_style == 'Pie' else self.layout
        who.label(text=dict_mixer_user_sk_name.get(mixerSkTyp[0], mixerSkTyp[0].capitalize()))
        for li in dictMixerMain[context.space_data.tree_type][mixerSkTyp[0]]:
            who.operator('node.voronoi_mixer_mixer', text=dict_mixer_defs[li][2]).who = li


def VoronoiPreviewerDrawCallback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    mouse_region_pos = PosViewToReg(mouse_pos.x, mouse_pos.y)
    lw = GetAddonPrefs().ds_line_width
    if GetAddonPrefs().ds_is_draw_debug:
        DebugDrawCallback(sender, context); return
    if (sender.list_sk_goal_out == []) or (sender.list_sk_goal_out[1] == None):  # Второе условие -- для (1).
        if GetAddonPrefs().ds_is_draw_point:
            wp = PreparGetWP(mouse_pos, 0); DrawWidePoint(wp[0], wp[1])
    else:
        DrawRectangleOnSocket(sender.list_sk_goal_out[1], sender.list_sk_goal_out[3],
                              GetSkVecCol(sender.list_sk_goal_out[1], 2.2))
        col = GetSkCol(sender.list_sk_goal_out[1]) if GetAddonPrefs().ds_is_colored_line else (1, 1, 1, 1)
        wp = PreparGetWP(sender.list_sk_goal_out[2] * gv_uifac[0], GetAddonPrefs().ds_point_offset_x)
        if GetAddonPrefs().ds_is_draw_line:
            DrawLine(wp[0], mouse_region_pos, lw, col, col)
        if GetAddonPrefs().ds_is_draw_point:
            DrawWidePoint(wp[0], wp[1], GetSkVecCol(sender.list_sk_goal_out[1], 2.2))

        def PreviewerDrawSk(Sk):
            txtdim = DrawSkText(PosViewToReg(mouse_pos.x, mouse_pos.y), GetAddonPrefs().ds_text_dist_from_cursor, -.5,
                                Sk)
            if Sk.is_linked:
                DrawIsLinked(mouse_pos, txtdim[0], 0,
                             GetSkCol(Sk) if GetAddonPrefs().ds_is_colored_marker else (.9, .9, .9, 1))

        PreviewerDrawSk(sender.list_sk_goal_out[1])


class VoronoiPreviewer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_previewer'
    bl_label = 'Voronoi Previewer'
    bl_options = {'UNDO'}

    def NextAssign(sender, context):
        pick_pos = context.space_data.cursor_location
        list_nodes = GenNearestNodeList(context.space_data.edit_tree.nodes, pick_pos)
        ancohor_exist = context.space_data.edit_tree.nodes.get(
                'Voronoi_Anchor') != None  # Если в геонодах есть якорь, то не триггериться только на геосокеты.
        for li in list_nodes:
            nd = li[1]
            # Если в геометрических нодах, игнорировать ноды без выводов геометрии
            if (context.space_data.tree_type == 'GeometryNodeTree') and (ancohor_exist == False):
                if [ndo for ndo in nd.outputs if ndo.type == 'GEOMETRY'] == []:
                    continue
            # Стандартное условие
            tgl = (nd.type != 'FRAME') and ((nd.hide == False) or (nd.type == 'REROUTE'))
            # Игнорировать свой собственный спец-рероут-якорь (полное совпадение имени и заголовка)
            tgl = (tgl) and (not ((nd.name == 'Voronoi_Anchor') and (nd.label == 'Voronoi_Anchor')))
            # Игнорировать ноды с пустыми выходами, чтобы точка не висела просто так и нод не мешал для удобного использования инструмента
            tgl = (tgl) and (len(nd.outputs) != 0)
            if tgl:
                list_socket_in, list_socket_out = GenNearestSocketsList(nd, pick_pos)
                for lso in list_socket_out:
                    skout = lso[1]
                    # Этот инструмент триггерится на любой выход кроме виртуального. В геометрических нодах искать только выходы геометрии
                    tgl = (skout.bl_idname != 'NodeSocketVirtual') and (
                            (context.space_data.tree_type != 'GeometryNodeTree') or (skout.type == 'GEOMETRY') or (
                        ancohor_exist))
                    if tgl:
                        sender.list_sk_goal_out = lso; break
                break
        if (GetAddonPrefs().vp_is_live_preview) and (sender.list_sk_goal_out):
            sender.list_sk_goal_out[1] = VoronoiPreviewer_DoPreview(context, sender.list_sk_goal_out[1])

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiPreviewer.NextAssign(self, context)
            case 'LEFTMOUSE' | 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if (event.value == 'RELEASE') and (self.list_sk_goal_out):
                    self.list_sk_goal_out[1] = VoronoiPreviewer_DoPreview(context, self.list_sk_goal_out[1])
                    return {'FINISHED'}
                else:
                    return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if (context.area.type != 'NODE_EDITOR') or (context.space_data.edit_tree == None):
            return {'CANCELLED'}
        if ('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
            match context.space_data.tree_type:
                case 'GeometryNodeTree':
                    if GetAddonPrefs().va_allow_classic_geo_viewer:
                        return {'PASS_THROUGH'}
                case 'CompositorNodeTree':
                    if GetAddonPrefs().va_allow_classic_compos_viewer:
                        return {'PASS_THROUGH'}
        if (event.type == 'RIGHTMOUSE') ^ GetAddonPrefs().vm_preview_hk_inverse:
            nodes = context.space_data.edit_tree.nodes
            for nd in nodes:
                nd.select = False
            nnd = (nodes.get('Voronoi_Anchor') or nodes.new('NodeReroute'))
            nnd.name = 'Voronoi_Anchor'
            nnd.label = 'Voronoi_Anchor'
            nnd.location = context.space_data.cursor_location
            nnd.select = True
            return {'FINISHED'}
        else:
            self.list_sk_goal_out = []
            gv_uifac[0] = UiScale()
            gv_where[0] = context.space_data
            SetFont()
            context.area.tag_redraw()
            VoronoiPreviewer.NextAssign(self, context)
            self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiPreviewerDrawCallback, (self, context),
                                                                         'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


list_shader_shaders_with_color = ['BSDF_ANISOTROPIC', 'BSDF_DIFFUSE', 'EMISSION', 'BSDF_GLASS', 'BSDF_GLOSSY',
                                  'BSDF_HAIR', 'BSDF_HAIR_PRINCIPLED', 'PRINCIPLED_VOLUME', 'BACKGROUND',
                                  'BSDF_REFRACTION', 'SUBSURFACE_SCATTERING', 'BSDF_TOON', 'BSDF_TRANSLUCENT',
                                  'BSDF_TRANSPARENT', 'BSDF_VELVET', 'VOLUME_ABSORPTION', 'VOLUME_SCATTER']


def VoronoiPreviewer_DoPreview(context, goalSk):
    def GetSocketIndex(socket):
        return int(socket.path_from_id().split('.')[-1].split('[')[-1][:-1])

    def GetTrueTreeWay(context, nd):
        # Идею рекурсивного нахождения пути через активный нод дерева я взял у NodeWrangler'a его функции "get_active_tree"
        # которая использовала "while tree.nodes.active != context.active_node:" (строка 613 версии 3.43).
        # Этот способ имеет недостатки, ибо активным нодом может оказаться не нод-группа, банально тем что можно открыть два окна редактора узлов и спокойно нарушить этот "путь".
        # Я мирился с этим маленьким и редким недостатком до того, пока в один прекрасный момент не возмутился от странности этого метода.
        # После отправился на сёрфинг api документации и открытого исходного кода. Результатом было банальное обнаружение ".space_data.path"
        # См. https://docs.blender.org/api/current/bpy.types.SpaceNodeEditorPath.html
        # Это "честный" api, дающий доступ у редактора узлов к пути от базы до финального дерева, отображаемого прямо сейчас.
        # Аддон, написанный 5-ю людьми, что встроен в Блендер по умолчанию, использует столь странный похожий на костыль метод получения пути? Может я что-то понимаю не так?
        way_trnd = []
        if False:  # bad way by parody on NodeWrangler
            wyc_tree = context.space_data.node_tree
            lim = 0  # lim'ит нужен для предохранителя вечного цикла.
            while (wyc_tree != context.space_data.edit_tree) and (lim < 64):
                way_trnd.insert(0, (wyc_tree, wyc_tree.nodes.active))
                wyc_tree = wyc_tree.nodes.active.node_tree
                lim += 1
            way_trnd.insert(0, (wyc_tree, nd))
        else:  # best way by my study of the api docs
            # Как я могу судить, сама суть реализации редактора узлов не хранит нод, через который пользователь зашёл в группу (Но это не точно).
            way_trnd = [[pn.node_tree, pn.node_tree.nodes.active] for pn in reversed(context.space_data.path)]
            # Поэтому если активным оказалась не нод-группа, то заменить на первого по имени (или ничего, если не найдено)
            for cyc in range(1, length(way_trnd)):
                wtn = way_trnd[cyc]
                if (wtn[1] == None) or (wtn[1].type != 'GROUP') or (wtn[1].node_tree != way_trnd[cyc - 1][0]):
                    wtn[1] = None  # Если не найден, то останется имеющийся неправильный. Поэтому обнулить его.
                    for nd in wtn[0].nodes:
                        if (nd.type == 'GROUP') and (nd.node_tree == way_trnd[cyc - 1][0]):
                            wtn[1] = nd
                            break
        return way_trnd

    # Для (1):
    if not goalSk:
        return None

    def GetSkIndex(sk):
        return int(sk.path_from_id().split('.')[-1].split('[')[-1][:-1])

    skix = GetSkIndex(goalSk)
    # Удалить все свои следы предыдущего использования для нод-групп текущего типа редактора
    for ng in bpy.data.node_groups:
        if ng.type == context.space_data.node_tree.type:
            sk = ng.outputs.get('voronoi_preview')
            if sk != None:
                ng.outputs.remove(sk)
    # (1)Переполучить сокет. Нужен для ситуациях присасывания к сокетам "voronoi_preview", которые исчезли
    goalSk = goalSk.node.outputs[skix] if skix < length(goalSk.node.outputs) else None
    # Если неудача, то выйти
    if goalSk == None:
        return None
    # Иначе выстроить путь:
    cur_tree = context.space_data.edit_tree
    list_way_trnd = GetTrueTreeWay(context, goalSk.node)
    hig_way = len(list_way_trnd) - 1
    ix_sk_last_used = -1
    is_zero_preview_gen = True
    for cyc in range(hig_way + 1):
        if (list_way_trnd[cyc][1] == None) and (cyc > 0):
            continue  # Проверка по той же причине, по которой мне не нравился способ от NW.
        node_in = None
        sock_out = None
        sock_in = None
        # Найти принимающий нод текущего уровня
        if cyc != hig_way:
            for nd in list_way_trnd[cyc][0].nodes:
                if (nd.type in ['GROUP_OUTPUT', 'OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'OUTPUT_LIGHT', 'COMPOSITE',
                                'OUTPUT']) and (nd.is_active_output):
                    node_in = nd
        else:
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        if nd.type in ['OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'OUTPUT_LIGHT', 'OUTPUT_LINESTYLE', 'OUTPUT']:
                            sock_in = nd.inputs[(goalSk.name == 'Volume') * (nd.type in ['OUTPUT_MATERIAL',
                                                                                         'OUTPUT_WORLD'])] if nd.is_active_output else sock_in
                case 'CompositorNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        sock_in = nd.inputs[0] if (nd.type == 'VIEWER') else sock_in
                    if sock_in == None:
                        for nd in list_way_trnd[hig_way][0].nodes:
                            sock_in = nd.inputs[0] if (nd.type == 'COMPOSITE') else sock_in
                case 'GeometryNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        if nd.type == 'GROUP_OUTPUT':
                            lis = [sk for sk in nd.inputs if sk.type == 'GEOMETRY']
                            if lis:
                                sock_in = lis[0]
                                break
                            else:
                                continue
                case 'TextureNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        sock_in = nd.inputs[0] if (nd.type == 'OUTPUT') else sock_in
            if sock_in:
                node_in = sock_in.node  # Иначе корень не имеет вывода.
        # Определить сокет отправляющего нода
        if cyc == 0:
            sock_out = goalSk
        else:
            sock_out = list_way_trnd[cyc][1].outputs.get('voronoi_preview')
            if (sock_out == None) and (ix_sk_last_used in range(0, length(list_way_trnd[cyc][1].outputs))):
                sock_out = list_way_trnd[cyc][1].outputs[ix_sk_last_used]
            if sock_out == None:
                continue  # Если нод-группа не имеет выходов
        # Определить сокет принимающего нода:
        for sl in sock_out.links:
            if sl.to_node == node_in:
                sock_in = sl.to_socket; ix_sk_last_used = GetSocketIndex(sock_in)
        if (sock_in == None) and (cyc != hig_way):  # cyc!=hig_way -- если корень потерял вывод.
            sock_in = list_way_trnd[cyc][0].outputs.get('voronoi_preview')
            if sock_in == None:
                txt = 'NodeSocketColor' if context.space_data.tree_type != 'GeometryNodeTree' else 'NodeSocketGeometry'
                txt = 'NodeSocketShader' if sock_out.type == 'SHADER' else txt
                list_way_trnd[cyc][0].outputs.new(txt, 'voronoi_preview')
                if node_in == None:
                    node_in = list_way_trnd[cyc][0].nodes.new('NodeGroupOutput')
                    node_in.location = list_way_trnd[cyc][1].location
                    node_in.location.x += list_way_trnd[cyc][1].width * 2
                sock_in = node_in.inputs.get('voronoi_preview')
                sock_in.hide_value = True
                is_zero_preview_gen = False
        # Удобный сразу-в-шейдер. "and(sock_in)" -- если у корня нет вывода
        if (sock_out.type in ('RGBA')) and (cyc == hig_way) and (sock_in) and (len(sock_in.links) != 0):
            if (sock_in.links[0].from_node.type in list_shader_shaders_with_color) and (is_zero_preview_gen):
                if len(sock_in.links[0].from_socket.links) == 1:
                    sock_in = sock_in.links[0].from_node.inputs.get('Color')
        # Соединить:
        nd_va = list_way_trnd[cyc][0].nodes.get('Voronoi_Anchor')
        if nd_va:
            list_way_trnd[cyc][0].links.new(sock_out, nd_va.inputs[0])
            break  # Завершение после напарывания повышает возможности использования якоря.
        elif (sock_out) and (sock_in) and ((sock_in.name == 'voronoi_preview') or (cyc == hig_way)):
            list_way_trnd[cyc][0].links.new(sock_out, sock_in)
    # Выделить предпросматриваемый нод:
    if GetAddonPrefs().vp_select_previewed_node:
        for nd in cur_tree.nodes:
            nd.select = False
        cur_tree.nodes.active = goalSk.node
        goalSk.node.select = True
    return goalSk  # Возвращать сокет. Нужно для (1).


def VoronoiHiderDrawCallback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    mouse_region_pos = PosViewToReg(mouse_pos.x, mouse_pos.y)
    lw = GetAddonPrefs().ds_line_width
    if GetAddonPrefs().ds_is_draw_debug:
        DebugDrawCallback(sender, context); return
    if sender.is_target_node:
        if (sender.list_nd_goal == []):
            if GetAddonPrefs().ds_is_draw_point:
                wp = PreparGetWP(mouse_pos, 0); DrawWidePoint(wp[0], wp[1])
        else:
            wp = PreparGetWP(sender.list_nd_goal[2] * gv_uifac[0], 0)
            col = (1, 1, 1, 1)
            if GetAddonPrefs().ds_is_draw_line:
                DrawLine(wp[0], mouse_region_pos, lw, col, col)
            if GetAddonPrefs().ds_is_draw_point:
                DrawWidePoint(wp[0], wp[1])
            if GetAddonPrefs().vh_draw_text_for_unhide:
                lbl = sender.list_nd_goal[1].label
                l_ys = [.25, -1.25] if lbl else [-.5, -.5]
                DrawText(PosViewToReg(mouse_pos.x, mouse_pos.y), GetAddonPrefs().ds_text_dist_from_cursor, l_ys[0],
                         sender.list_nd_goal[1].name, (1, 1, 1, 1))
                if lbl:
                    DrawText(PosViewToReg(mouse_pos.x, mouse_pos.y), GetAddonPrefs().ds_text_dist_from_cursor, l_ys[1],
                             lbl, (1, 1, 1, 1))
    else:
        if (sender.list_sk_goal == []):
            if GetAddonPrefs().ds_is_draw_point:
                wp = PreparGetWP(mouse_pos, 0); DrawWidePoint(wp[0], wp[1])
        else:
            DrawRectangleOnSocket(sender.list_sk_goal[1], sender.list_sk_goal[3],
                                  GetSkVecCol(sender.list_sk_goal[1], 2.2))
            col = GetSkCol(sender.list_sk_goal[1]) if GetAddonPrefs().ds_is_colored_line else (1, 1, 1, 1)
            wp = PreparGetWP(sender.list_sk_goal[2] * gv_uifac[0],
                             GetAddonPrefs().ds_point_offset_x * (sender.list_sk_goal[1].is_output * 2 - 1))
            if GetAddonPrefs().ds_is_draw_line:
                DrawLine(wp[0], mouse_region_pos, lw, col, col)
            if GetAddonPrefs().ds_is_draw_point:
                DrawWidePoint(wp[0], wp[1], GetSkVecCol(sender.list_sk_goal[1], 2.2))

            def HiderDrawSk(Sk):
                txtdim = DrawSkText(PosViewToReg(mouse_pos.x, mouse_pos.y),
                                    GetAddonPrefs().ds_text_dist_from_cursor * (Sk.is_output * 2 - 1), -.5, Sk)
                if Sk.is_linked:
                    DrawIsLinked(mouse_pos, txtdim[0] * (Sk.is_output * 2 - 1), 0,
                                 GetSkCol(Sk) if GetAddonPrefs().ds_is_colored_marker else (.9, .9, .9, 1))

            HiderDrawSk(sender.list_sk_goal[1])


class VoronoiHider(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_hider'
    bl_label = 'Voronoi Hider'
    bl_options = {'UNDO'}

    def NextAssign(sender, context):
        sender.list_sk_goal = []
        pick_pos = context.space_data.cursor_location
        list_nodes = GenNearestNodeList(context.space_data.edit_tree.nodes, pick_pos)
        for li in list_nodes:
            nd = li[1]
            if not nd.type in ['FRAME', 'REROUTE']:
                sender.list_nd_goal = li
                list_socket_in, list_socket_out = GenNearestSocketsList(nd, pick_pos)

                def MucGetNotLinked(list_sks):
                    for sk in list_sks:
                        if sk[1].is_linked == False:
                            return sk
                    return None

                skin = MucGetNotLinked(list_socket_in)
                skout = MucGetNotLinked(list_socket_out)
                if (skin) or (skout):
                    if skin == None:
                        sender.list_sk_goal = skout
                    elif skout == None:
                        sender.list_sk_goal = skin
                    else:
                        sender.list_sk_goal = skin if skin[0] < skout[0] else skout
                break

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                VoronoiHider.NextAssign(self, context)
            case 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                return {'CANCELLED'}
            case 'E':
                if (event.is_repeat == False) and (event.value == 'RELEASE'):
                    bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                    if self.is_target_node == False:
                        if self.list_sk_goal:
                            self.list_sk_goal[1].hide = True
                    elif self.list_nd_goal:
                        for ni in self.list_nd_goal[1].inputs:
                            ni.hide = False
                        for no in self.list_nd_goal[1].outputs:
                            no.hide = False
                    return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.list_sk_goal = []
        self.list_nd_goal = []
        self.is_target_node = (event.shift) and (event.ctrl)
        gv_uifac[0] = UiScale()
        gv_where[0] = context.space_data
        SetFont()
        context.area.tag_redraw()
        VoronoiHider.NextAssign(self, context)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiHiderDrawCallback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


listDictMathEditor = [{'ShaderNodeTree': 'ShaderNodeMath', 'GeometryNodeTree': 'ShaderNodeMath',
                       'CompositorNodeTree': 'CompositorNodeMath', 'TextureNodeTree': 'TextureNodeMath'},
                      {'ShaderNodeTree': 'ShaderNodeVectorMath', 'GeometryNodeTree': 'ShaderNodeVectorMath'}]
displayList = [[]]
displayWho = [0]
displayDeep = [0]


class FastMath_Main(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_fastmath'
    bl_label = 'Fast Maths Pie'
    bridge: bpy.props.StringProperty()

    def modal(self, context, event):
        self.bridge = ''
        return {'FINISHED'}

    def invoke(self, context, event):
        tree = context.space_data.edit_tree
        if tree == None:
            return {'CANCELLED'}

        def DispMenu(dp):
            displayDeep[0] = dp
            bpy.ops.wm.call_menu_pie(name='VL_MT_voronoi_fastmath_pie')

        whoList = listMathMap if displayWho[0] == 0 else listVecMathMap
        displayList[0] = [li[0] for li in whoList]
        if self.bridge in ['', ' ']:
            DispMenu(0)
        elif self.bridge in displayList[0]:
            displayList[0] = [li[1] for li in whoList if li[0] == self.bridge][0]
            DispMenu(1)
        else:
            typ = listDictMathEditor[displayWho[0]].get(context.space_data.tree_type, None)
            if typ == None:
                return {'CANCELLED'}
            bpy.ops.node.add_node('INVOKE_DEFAULT', type=typ, use_transform=True)
            aNd = context.space_data.edit_tree.nodes.active
            aNd.operation = self.bridge
            tree.links.new(mixerSks[0], aNd.inputs[0])
            if mixerSks[1]:  # Чтобы можно было "вытягивать" быструю математику из сокета
                tree.links.new(mixerSks[1], aNd.inputs[1])
        return {'RUNNING_MODAL'}


listMathMap = [('Advanced', ['SQRT', 'POWER', 'EXPONENT', 'LOGARITHM', 'INVERSE_SQRT', 'PINGPONG']),
               ('Compatible Primitives', ['SUBTRACT', 'ADD', 'DIVIDE', 'MULTIPLY', 'ABSOLUTE', 'MULTIPLY_ADD']), (
               'Rounding',
               ['SMOOTH_MIN', 'SMOOTH_MAX', 'LESS_THAN', 'GREATER_THAN', 'SIGN', 'COMPARE', 'TRUNC', 'ROUND']),
               ('Compatible Vector', ['MINIMUM', 'MAXIMUM', 'FLOOR', 'CEIL', 'MODULO', 'FRACT', 'WRAP', 'SNAP']),
               ('', []), ('', []), ('Other', ['COSH', 'RADIANS', 'DEGREES', 'SINH', 'TANH']),
               ('Trigonometric', ['SINE', 'COSINE', 'TANGENT', 'ARCTANGENT', 'ARCSINE', 'ARCCOSINE', 'ARCTAN2'])]
listVecMathMap = [('Advanced', ['NORMALIZE', 'SCALE', 'LENGTH', 'DISTANCE', 'SINE', 'COSINE', 'TANGENT']),
                  ('Compatible Primitives', ['SUBTRACT', 'ADD', 'DIVIDE', 'MULTIPLY', 'ABSOLUTE', 'MULTIPLY_ADD']),
                  ('Rays', ['DOT_PRODUCT', 'CROSS_PRODUCT', 'FACEFORWARD', 'PROJECT', 'REFRACT', 'REFLECT']),
                  ('Compatible Vector', ['MINIMUM', 'MAXIMUM', 'FLOOR', 'CEIL', 'MODULO', 'FRACTION', 'WRAP', 'SNAP']),
                  (' ', []), (' ', []), (' ', []), (' ', [])]


class FastMath_Pie(bpy.types.Menu):
    bl_idname = 'VL_MT_voronoi_fastmath_pie'
    bl_label = ''

    def draw(self, context):
        pie = self.layout.menu_pie()
        for li in displayList[0]:
            if (GetAddonPrefs().fm_is_empty_hold == False) and (li == ' '):
                continue
            pie.operator(FastMath_Main.bl_idname, text=li.capitalize() if displayDeep[0] == 1 else li).bridge = li


class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__ if __name__ != '__main__' else 'VoronoiLinker'
    ds_line_width: bpy.props.IntProperty(name='Line Width', default=1, min=1, max=16, subtype='FACTOR')
    ds_point_offset_x: bpy.props.FloatProperty(name='Point offset X', default=20, min=-50, max=50)
    ds_point_resolution: bpy.props.IntProperty(name='Point resolution', default=54, min=3, max=64)
    ds_point_radius: bpy.props.FloatProperty(name='Point radius scale', default=1, min=0, max=3)
    ds_is_draw_sk_text: bpy.props.BoolProperty(name='Draw Text', default=True)
    ds_is_colored_sk_text: bpy.props.BoolProperty(name='Colored Text', default=True)
    ds_is_draw_marker: bpy.props.BoolProperty(name='Draw Markers', default=True)
    ds_is_colored_marker: bpy.props.BoolProperty(name='Colored Markers', default=True)
    ds_is_draw_point: bpy.props.BoolProperty(name='Draw Points', default=True)
    ds_is_colored_point: bpy.props.BoolProperty(name='Colored Points', default=True)
    ds_is_draw_line: bpy.props.BoolProperty(name='Draw Line', default=True)
    ds_is_colored_line: bpy.props.BoolProperty(name='Colored Line', default=True)
    ds_is_draw_area: bpy.props.BoolProperty(name='Draw Socket Area', default=True)
    ds_is_colored_area: bpy.props.BoolProperty(name='Colored Socket Area', default=True)
    ds_text_style: bpy.props.EnumProperty(name='Text Frame Style', default='Classic',
                                          items={('Classic', 'Classic', ''), ('Simplified', 'Simplified', ''),
                                                 ('Text', 'Only text', '')})
    vlds_is_always_line: bpy.props.BoolProperty(name='Always draw line for VoronoiLinker', default=False)
    vm_preview_hk_inverse: bpy.props.BoolProperty(name='Previews hotkey inverse', default=False)
    vm_is_one_skip: bpy.props.BoolProperty(name='One Choise to skip', default=True,
                                           description='If the selection contains a single element, skip the selection and add it immediately')
    vm_menu_style: bpy.props.EnumProperty(name='Mixer Menu Style', default='Pie',
                                          items={('Pie', 'Pie', ''), ('List', 'List', '')})
    vp_is_live_preview: bpy.props.BoolProperty(name='Live Preview', default=True)
    vp_select_previewed_node: bpy.props.BoolProperty(name='Select Previewed Node', default=True,
                                                     description='Select and set acttive for node that was used by VoronoiPreview')
    ds_text_frame_offset: bpy.props.IntProperty(name='Text Frame Offset', default=0, min=0, max=24, subtype='FACTOR')
    ds_font_size: bpy.props.IntProperty(name='Text Size', default=28, min=10, max=48)
    a_display_advanced: bpy.props.BoolProperty(name='Display advanced options', default=False)
    ds_text_dist_from_cursor: bpy.props.FloatProperty(name='Text distance from cursor', default=25, min=5, max=50)
    ds_text_lineframe_offset: bpy.props.FloatProperty(name='Text Line-frame offset', default=2, min=0, max=10)
    ds_is_draw_sk_text_shadow: bpy.props.BoolProperty(name='Draw Text Shadow', default=True)
    ds_shadow_col: bpy.props.FloatVectorProperty(name='Shadow Color', default=[0.0, 0.0, 0.0, .5], size=4, min=0, max=1,
                                                 subtype='COLOR')
    ds_shadow_offset: bpy.props.IntVectorProperty(name='Shadow Offset', default=[2, -2], size=2, min=-20, max=20)
    ds_shadow_blur: bpy.props.IntProperty(name='Shadow Blur', default=2, min=0, max=2)
    va_allow_classic_compos_viewer: bpy.props.BoolProperty(name='Allow classic Compositor viewer', default=False)
    va_allow_classic_geo_viewer: bpy.props.BoolProperty(name='Allow classic GeoNodes viewer', default=True)
    vh_draw_text_for_unhide: bpy.props.BoolProperty(name='Draw text for unhide node', default=False)
    ds_is_draw_debug: bpy.props.BoolProperty(name='draw debug', default=False)
    fm_is_included: bpy.props.BoolProperty(name='Include Fast Math Pie', default=True)
    fm_is_empty_hold: bpy.props.BoolProperty(name='Empty placeholders', default=True)
    fm_trigger_activate: bpy.props.EnumProperty(name='Activate trigger', default='FMA0',
                                                items={('FMA0', 'If at least one is a math socket', ''),
                                                       ('FMA1', 'If everyone is a math socket', '')})

    def draw(self, context):
        col0 = self.layout.column()
        col1 = col0.column(align=True)
        col1.prop(self, 'va_allow_classic_compos_viewer')
        col1.prop(self, 'va_allow_classic_geo_viewer')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Draw settings:')
        col1.prop(self, 'ds_point_offset_x')
        col1.prop(self, 'ds_text_frame_offset')
        col1.prop(self, 'ds_font_size')
        box = col1.box()
        box.prop(self, 'a_display_advanced')
        if self.a_display_advanced:
            col2 = box.column()
            col3 = col2.column(align=True)
            col3.prop(self, 'ds_line_width')
            col3.prop(self, 'ds_point_radius')
            col3.prop(self, 'ds_point_resolution')
            col3 = col2.column(align=True)
            col3.prop(self, 'ds_text_dist_from_cursor')
            col3.prop(self, 'ds_text_lineframe_offset')
            col3 = col2.column(align=True)
            box = col2.box()
            col4 = box.column()
            col4.prop(self, 'ds_is_draw_sk_text_shadow')
            if self.ds_is_draw_sk_text_shadow:
                row = col4.row(align=True)
                row.prop(self, 'ds_shadow_col')
                row = col4.row(align=True)
                row.prop(self, 'ds_shadow_offset')
                col4.prop(self, 'ds_shadow_blur')
            col2.prop(self, 'ds_is_draw_debug')
        row = col1.row(align=True)
        row.prop(self, 'ds_is_draw_sk_text')
        row.prop(self, 'ds_is_colored_sk_text')
        row = col1.row(align=True)
        row.prop(self, 'ds_is_draw_marker')
        row.prop(self, 'ds_is_colored_marker')
        row = col1.row(align=True)
        row.prop(self, 'ds_is_draw_point')
        row.prop(self, 'ds_is_colored_point')
        row = col1.row(align=True)
        row.prop(self, 'ds_is_draw_line')
        row.prop(self, 'ds_is_colored_line')
        row = col1.row(align=True)
        row.prop(self, 'ds_is_draw_area')
        row.prop(self, 'ds_is_colored_area')
        col1.prop(self, 'ds_text_style')
        col1.prop(self, 'vlds_is_always_line')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Mixer settings:')
        col1.prop(self, 'vm_menu_style')
        col1.prop(self, 'vm_is_one_skip')
        box = box.box()
        col1 = box.column(align=True)
        col1.prop(self, 'fm_is_included')
        if self.fm_is_included:
            box = col1.box()
            col1 = box.column(align=True)
            col1.prop(self, 'fm_trigger_activate')
            col1.prop(self, 'fm_is_empty_hold')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Preview settings:')
        col1.prop(self, 'vp_is_live_preview')
        col1.prop(self, 'vp_select_previewed_node')
        col1.prop(self, 'vm_preview_hk_inverse')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Hider settings:')
        col1.prop(self, 'vh_draw_text_for_unhide')


list_classes = [VoronoiLinker, VoronoiMassLinker, VoronoiMixer, VoronoiMixerMixer, VoronoiMixerMenu, VoronoiPreviewer,
                VoronoiHider, FastMath_Main, FastMath_Pie, VoronoiAddonPrefs]
list_addon_keymaps = []
kmi_defs = ((VoronoiLinker.bl_idname, 'RIGHTMOUSE', False, False, True),
            (VoronoiMassLinker.bl_idname, 'RIGHTMOUSE', True, True, True),
            (VoronoiMixer.bl_idname, 'RIGHTMOUSE', True, False, True),
            (VoronoiPreviewer.bl_idname, 'LEFTMOUSE', True, True, False),
            (VoronoiPreviewer.bl_idname, 'RIGHTMOUSE', True, True, False),
            (VoronoiHider.bl_idname, 'E', True, False, False), (VoronoiHider.bl_idname, 'E', True, True, False))


def register():
    for li in list_classes:
        bpy.utils.register_class(li)
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    for (bl_id, key, Shift, Ctrl, Alt) in kmi_defs:
        kmi = km.keymap_items.new(idname=bl_id, type=key, value='PRESS', shift=Shift, ctrl=Ctrl,
                                  alt=Alt); list_addon_keymaps.append((km, kmi))


def unregister():
    for li in reversed(list_classes):
        bpy.utils.unregister_class(li)
    for km, kmi in list_addon_keymaps:
        km.keymap_items.remove(kmi)
    list_addon_keymaps.clear()


if __name__ == '__main__':
    register()
