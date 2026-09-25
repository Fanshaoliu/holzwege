"""Chapter 5: the corridor of nothing, old-world ruins, Echo's first core."""
from mapkit import Grid, Map
from art import props2  # noqa: F401
from art import props as PR
from art.px import Canvas
from art import pal as P


def corridor():
    g = Grid(30, 12, 'Z')
    for (a, b) in (((1, 6), (8, 6)), ((8, 6), (8, 9)), ((8, 9), (18, 9)), ((18, 9), (18, 4)), ((18, 4), (27, 4)), ((27, 4), (27, 6)), ((27, 6), (29, 6))):
        g.path([a, b], 'X')
    g.set(27, 3, 'X'); g.set(0, 6, 'X')
    m = Map('corridor', '无之回廊', g, music='none', indoor=True, dark=1.0)
    m.prop('bell_pedestal', 27, 3)
    m.event(27, 3, 'c5_bell', trigger='talk', cond='!c5_bell_got')
    m.event(27, 4, 'c5_bell', trigger='step', cond='c5_nothing_done & !c5_bell_got')
    m.event(5, 6, 'c5_corridor_1', trigger='step', cond='!c5_corridor_1')
    m.event(13, 9, 'c5_corridor_2', trigger='step', cond='!c5_corridor_2')
    m.event(22, 4, 'c5_corridor_3', trigger='step', cond='!c5_nothing_done')
    m.warp(29, 6, 'ruins', 1, 9, dir='right', cond='c5_nothing_done', deny='v_corridor_deny')
    m.warp(0, 6, 'hut', 6, 4, dir='down')
    return m


def ruins():
    g = Grid(24, 18, 'O')
    g.rect(0, 0, 24, 2, '#'); g.rect(0, 0, 1, 18, '#'); g.rect(23, 0, 1, 18, '#'); g.rect(0, 17, 24, 1, '#')
    g.set(0, 9, 'O'); g.set(23, 9, 'O')
    g.rect(4, 5, 16, 8, 'I')
    m = Map('ruins', '旧世遗迹', g, music='ruins', indoor=True, dark=0.55)
    m.wall_style = 'metal'
    m.prop('vending', 3, 2, talk='c5_vending')
    m.prop('poster', 7, 1, solid=False, layer='below', talk='c5_poster')
    m.prop('subway_sign', 12, 1, solid=False, layer='below')
    m.event(11, 1, 'v_ruins_sign', trigger='talk', w=3)
    m.prop('drawing', 19, 1, solid=False, layer='below', talk='c5_drawing')
    m.prop('phone_floor', 11, 10, solid=False, layer='below')
    m.event(11, 10, None, trigger='talk')
    m.events[-1]['pages'] = [['c5_phone_got', 'v_phone_after'], [None, 'c5_phone']]
    m.event(11, 2, 'c5_phone_notice', trigger='step', cond='c5_ruins_in & !c5_phone_got', h=15)
    for x in (15, 16, 17, 18, 19, 20):
        m.prop('rack', x, 14, seed=x)
    m.prop('bench', 6, 14); m.prop('bench', 8, 14); m.prop('crate', 21, 3); m.prop('crate', 20, 3)
    m.prop('rack', 1, 3); m.prop('rack', 22, 12)
    m.event(0, 0, 'c5_ruins', trigger='auto', cond='!c5_ruins_in')
    m.event(0, 0, 'c5_drawing', trigger='none')
    m.warp(0, 9, 'corridor', 28, 6, dir='left')
    m.warp(23, 9, 'core', 1, 7, dir='right')
    return m


def core():
    g = Grid(18, 14, 'I')
    g.rect(0, 0, 18, 2, '#'); g.rect(0, 0, 1, 14, '#'); g.rect(17, 0, 1, 14, '#'); g.rect(0, 13, 18, 1, '#')
    g.set(0, 7, 'I')
    m = Map('core', '第一回声站', g, music='core', indoor=True, dark=0.5)
    m.wall_style = 'metal'
    for x in (2, 3, 4, 13, 14, 15):
        m.prop('rack', x, 2, seed=x)
    for y in (5, 8, 11):
        m.prop('rack', 2, y, seed=y); m.prop('rack', 15, y, seed=y + 3)
    m.prop('core', 8, 6)
    m.anim('core', 8, 6, lit='c5_echo_heard')
    m.event(7, 9, 'c5_core', trigger='step', cond='!c5_echo_heard', w=4)
    m.npc('gest', 'gest_faceless', 8, 11, dir='up', show='false', pages=[[None, 'p_default']])
    m.npc('ister', 'ister', 11, 11, dir='up', show='false', pages=[[None, 'p_default']])
    m.warp(0, 7, 'ruins', 22, 9, dir='left', cond='!c5_echo_heard | c5_boss_won')
    return m


MAPS = [corridor, ruins, core]
