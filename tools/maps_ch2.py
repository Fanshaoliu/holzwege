"""Forest, world map, Clock Harbor and its interiors."""
from mapkit import Grid, Map
from art import props2  # noqa: F401
from art import props as PR
from art.px import Canvas
from art import pal as P

FOREST_LEGEND = {
    '=': dict(base='forest', over='dirt'), 'f': dict(base='forest'), '.': dict(base='grass'),
    ',': dict(base='grass', decor='flowers'), 'u': dict(base='forest', decor='mushrooms'),
}


def forest():
    g = Grid(52, 44, 't')
    g.scatter('p', 380, (0, 0, 52, 44), seed=21, only='t')
    g.scatter('d', 14, (0, 0, 52, 44), seed=22, only='t')
    P_ = lambda pts, w=1: g.path(pts, '=', width=w)
    P_([(25, 43), (25, 38)], 2)
    P_([(25, 38), (20, 38)])
    P_([(20, 38), (20, 33)])
    P_([(20, 33), (26, 33)])
    P_([(26, 33), (26, 27)])
    P_([(26, 27), (31, 27)])
    P_([(31, 27), (31, 21)])
    P_([(31, 21), (26, 21)])
    P_([(26, 21), (26, 13)])
    # holzwege: branches that end
    P_([(20, 38), (12, 38), (12, 36), (6, 36)])
    P_([(26, 30), (35, 30), (35, 34), (44, 34)])
    P_([(20, 34), (14, 34), (14, 26), (10, 26)])
    P_([(31, 24), (40, 24), (40, 20), (45, 20)])
    P_([(26, 19), (18, 19), (18, 16), (9, 16)])
    # little glades at dead ends
    for (cx, cy) in ((5, 36), (45, 34), (9, 26), (46, 20), (8, 16)):
        for yy in range(cy - 1, cy + 2):
            for xx in range(cx - 1, cx + 2):
                if g.get(xx, yy) in ('t', 'p', 'd'): g.set(xx, yy, 'f')
        g.set(cx, cy + 1 if g.get(cx, cy + 1) == 'f' else cy - 1, 'u')
    # entrance glade
    g.rect(21, 39, 9, 4, 'f'); g.rect(25, 39, 2, 5, '=')
    # clearing
    for y in range(0, 16):
        for x in range(17, 36):
            if ((x - 26) / 8.5) ** 2 + ((y - 7.5) / 6.3) ** 2 <= 1.0:
                g.set(x, y, '.')
    g.scatter(',', 26, (18, 1, 17, 13), seed=23)
    g.set(26, 14, '='); g.set(26, 13, '=')
    m = Map('forest', '黑森林 · 林中路', g, music='forest', legend=FOREST_LEGEND, seed=4, dark=0.32)
    m.building(24, 3, kind='hut', doors=(1,), warp=dict(to='hut', tx=4, ty=6, dir='up'))
    m.prop('bigtree', 19, 8)
    m.prop('logs', 22, 40); m.prop('stump', 28, 41); m.prop('stump', 23, 42)
    m.prop('rock_lizard', 9, 26)
    m.prop('stump', 5, 36, talk='c2_deadend'); m.prop('stump', 46, 20, talk='c2_deadend')
    m.prop('pot', 29, 8)
    m.chest('f_se', 45, 34, 'coin'); m.chest('f_w', 8, 16, 'coin')
    m.npc('woodcutter', 'woodcutter', 27, 40, dir='left', pages=[['!c2_woodcutter_done', 'c2_woodcutter'], [None, 'c2_woodcutter_again']])
    m.npc('slime', 'm_slime', 20, 36, show='!c2_slime_won', pages=[[None, 'c2_slime_pre']], move='bob')
    m.npc('wolf', 'm_wolf', 26, 16, show='!c2_wolf_won', pages=[[None, 'c2_wolf_pre']], move='bob')
    m.npc('ister', 'ister', 28, 8, dir='left', show='c2_met_ister', pages=[['c5_ister_done', 'c5_ister_after'], [None, 'c2_ister_again']])
    m.event(9, 26, None, trigger='talk')
    m.events[-1]['pages'] = [['c2_lizard_done', 'v_lizard'], [None, 'c2_lizard']]
    m.event(0, 0, 'c2_gate', trigger='auto', cond='ch>=2 & !c2_gate_done')
    m.event(26, 13, 'c2_clearing', trigger='step', cond='!c2_met_ister')
    m.event(26, 12, 'c5_ister', trigger='step', cond='c5_home & !c5_ister_done')
    m.warp(25, 43, 'village', 21, 1, dir='down', w=2)
    return m


WORLD_LEGEND = {
    '~': dict(base='grass', over='water', solid=True, water=True),
    'm': dict(base='grass', obj='mountain'), 'w': dict(base='grass', decor='wtrees'),
    'W': dict(base='forest', obj='wtrees_dark'), 's': dict(base='grass', over='sand'),
}


def _dam():
    c = Canvas(32, 20)
    c.rect(0, 2, 32, 14, P.MARBLE[3]); c.rect(0, 2, 32, 2, P.MARBLE[5]); c.rect(0, 14, 32, 2, P.MARBLE[1])
    for x in range(2, 32, 6): c.vline(x, 4, 13, P.MARBLE[2])
    c.outline(P.OUT)
    return c


def world():
    g = Grid(48, 36, '.')
    # sea
    g.rect(0, 31, 48, 5, '~'); g.rect(45, 0, 3, 36, '~')
    for x in range(0, 45): g.set(x, 30, 's')
    g.rect(44, 0, 1, 31, 's')
    # black forest
    g.rect(1, 1, 20, 12, 'W')
    for x in range(1, 21): g.set(x, 13, 'w' if x % 3 else 'W')
    g.scatter('w', 25, (1, 1, 20, 12), seed=31, only='W')
    # mountains
    g.rect(16, 15, 9, 3, 'm'); g.rect(17, 21, 8, 3, 'm'); g.rect(24, 8, 5, 6, 'm')
    g.scatter('.', 6, (16, 15, 9, 3), seed=32, only='m')
    # river & dam
    g.rect(34, 0, 1, 31, '~'); g.set(34, 26, 'b')
    # roads
    g.path([(7, 20), (28, 20)], '=')
    g.path([(28, 20), (28, 27)], '=')
    g.path([(29, 27), (38, 27)], '=')
    g.set(34, 27, 'b'); g.set(34, 26, '~')
    g.path([(38, 27), (38, 9)], '=')
    g.path([(11, 14), (11, 19)], '=')
    # scenery
    g.scatter('w', 70, (2, 14, 42, 16), seed=33)
    g.scatter('m', 10, (36, 12, 8, 10), seed=34)
    g.scatter(',', 30, (2, 14, 42, 16), seed=35)
    for x in range(7, 29): g.set(x, 20, '=')
    for y in range(20, 28): g.set(28, y, '=')
    for x in range(29, 39): g.set(x, 27, '=')
    g.set(34, 27, 'b')
    for y in range(9, 28): g.set(38, y, '=')
    for y in range(14, 20): g.set(11, y, '=')
    g.set(20, 20, '='); g.set(21, 20, '=')
    m = Map('world', '世界', g, music='world', legend=WORLD_LEGEND, seed=7)
    m.prop('town_village', 6, 20, solid=False, layer='below')
    m.prop('town_forest', 11, 13, solid=False, layer='below')
    m.prop('town_harbor', 29, 28, solid=False, layer='below')
    m.prop('town_capital', 38, 8, solid=False, layer='below')
    m.decal('dam', _dam, 33, 5, 2, 1)
    m.npc('bat', 'm_bat', 20, 20, show='c2_done & !c3_bat_won', pages=[[None, 'c3_bat_pre']], move='bob')
    m.warp(6, 20, 'village', 42, 17, dir='left')
    m.warp(11, 13, 'forest', 25, 42, dir='up', cond='ch>=2', deny='v1_gate_deny')
    m.warp(29, 28, 'harbor', 1, 17, dir='right')
    m.warp(38, 8, 'capital', 23, 39, dir='up', cond='ch>=4', deny='v_capital_deny')
    return m


HARBOR_LEGEND = {
    '.': dict(base='pave'), 'g': dict(base='grass'), ',': dict(base='grass', decor='flowers'),
    'e': dict(base='pave', over='canal', joins=('canal',), bridge=True, water=True),
    'q': dict(base='pave', over='canal', solid=True, water=True), ':': dict(base='cobble'),
}


def harbor():
    g = Grid(46, 38, ':')
    # sea & piers
    g.rect(0, 32, 46, 6, 'q')
    for x in (10, 11, 26, 27): g.vline(x, 32, 35, 'e')
    # canals
    g.rect(0, 21, 46, 2, 'q'); g.rect(14, 0, 2, 21, 'q')
    for (x, y, w, h) in ((6, 21, 2, 2), (22, 21, 2, 2), (36, 21, 2, 2), (14, 17, 2, 2), (14, 6, 2, 2)):
        g.rect(x, y, w, h, 'e')
    # plaza around the tower
    g.rect(16, 11, 16, 9, '.')
    g.rect(16, 23, 30, 8, ':')
    # little gardens
    g.rect(1, 7, 12, 2, 'g'); g.scatter(',', 8, (1, 7, 12, 2), seed=41, only='g')
    g.rect(33, 7, 10, 3, 'g'); g.scatter(',', 8, (33, 7, 10, 3), seed=42, only='g')
    g.rect(1, 29, 12, 2, 'g')
    # alley walls
    for y in range(9, 19): g.set(42, y, '#'); g.set(44, y, '#')
    g.set(43, 9, '#')
    m = Map('harbor', '钟港', g, music='harbor', legend=HARBOR_LEGEND, seed=9)
    m.wall_style = 'stone'
    m.building(21, 2, kind='tower', doors=(1,), warp=dict(to='tower1', tx=6, ty=10, dir='up', cond='c3_tower_open', deny='c3_tower_deny'))
    m.building(4, 10, w=4, roof_h=2, wall_h=2, roof='slate_b', wall='brick', doors=(1,), windows=(3,), sign='clock', sign_col=2,
               seed=11, warp=dict(to='clockshop', tx=5, ty=6, dir='up'))
    m.building(2, 2, w=5, roof_h=2, wall_h=2, roof='terra', wall='plaster', doors=(2,), windows=(0, 4), chimney=4, seed=12, locked='v_door_harbor')
    m.building(30, 12, w=6, roof_h=2, wall_h=2, roof='teal', wall='stone', doors=(2,), windows=(0, 4, 5), sign='cup', sign_col=3,
               seed=13, glow=True, warp=dict(to='cafe', tx=6, ty=7, dir='up'))
    m.building(6, 25, w=4, roof_h=2, wall_h=2, roof='terra', wall='plaster', doors=(1,), windows=(3,), sign='pot', sign_col=2,
               chimney=3, seed=14, warp=dict(to='pottery', tx=5, ty=6, dir='up'))
    m.building(27, 2, w=5, roof_h=2, wall_h=2, roof='slate_b', wall='plaster', doors=(2,), windows=(0, 4), chimney=1, seed=15, locked='v_door_harbor')
    m.building(37, 2, w=5, roof_h=2, wall_h=2, roof='slate_p', wall='brick', doors=(2,), windows=(0, 4), seed=16, locked='v_door_harbor')
    m.building(17, 25, w=5, roof_h=2, wall_h=2, roof='slate_b', wall='brick', doors=(2,), windows=(0, 4), chimney=4, seed=17, locked='v_door_harbor')
    m.building(38, 25, w=5, roof_h=2, wall_h=2, roof='terra', wall='stone', doors=(2,), windows=(0, 4), seed=18, locked='v_door_harbor')
    for (x, y) in ((17, 12), (30, 19), (17, 19), (12, 17), (9, 23), (25, 23)):
        m.prop('lamp_lit', x, y)
    for (x, y) in ((19, 17), (27, 17)): m.prop('bench', x, y)
    for (x, y) in ((29, 11), (18, 11), (13, 11)): m.prop('bushf', x, y)
    m.prop('barrel', 8, 31); m.prop('barrel', 9, 31); m.prop('crate', 24, 31); m.prop('crate', 29, 31)
    m.prop('boat', 13, 34); m.prop('boat', 30, 33)
    m.prop('sign', 2, 16, talk='obj_sign_harbor')
    m.chest('h_alley', 43, 10, 'coin')
    m.spots = [dict(id='h_barrel', x=8, y=31, item='coin', label='木桶'), dict(id='h_crate', x=29, y=31, item='coin', label='木箱')]
    m.npc('guard', 'guard', 21, 11, pages=[['c3_giant_won', 'v_guard_after'], ['c3_otto_done & item:pendulum & !c3_tower_open', 'c3_guard_open'],
                                           ['c3_otto_done & !c3_tower_open', 'c3_guard_nobob'], ['!c3_tower_open', 'c3_guard_locked'], [None, 'v_guard_after']])
    m.npc('coinlady', 'coinlady', 18, 15, pages=[['coin_done', 'v_coin_after'], ['!coin_quest', 'c3_coin_lady'], ['coins>=12', 'v_coin_all'],
                                                 ['coins>=1', 'v_coin_some'], [None, 'v_coin_none']])
    m.npc('knewit', 'knewit', 26, 14, dir='left', pages=[['c3_clock_restarted', 'v_knew_2'], [None, 'v_knew_1']])
    m.npc('countboy', 'countboy', 20, 19, pages=[[None, 'v_boy_count']])
    m.npc('faceless_w', 'citizen_f_faceless', 4, 18, dir='right', pages=[['c3_clock_restarted', 'v_faceless_woman_2'], [None, 'v_faceless_woman_1']])
    m.npc('sailor', 'sailor', 26, 31, dir='down', pages=[['c3_clock_restarted', 'v_sailor_2'], [None, 'v_sailor_1']])
    m.npc('mask', 'm_mask', 43, 12, show='c3_fried_done & !c3_mask_won', pages=[[None, 'c3_mask_pre']], move='bob')
    m.npc('dog', 'dog', 24, 15, move='wander', pages=[[None, 'v_dog']])
    m.event(0, 0, 'c3_arrive', trigger='auto', cond='!c3_arrived')
    m.event(32, 18, 'c3_night', trigger='step', cond='c3_otto_watch & c3_marta_jug & c3_poem_got & !c3_night_done', w=2)
    m.warp(0, 17, 'world', 28, 28, dir='left', h=2)
    return m


def _interior(w, h, floor='W', exit_x=None):
    g = Grid(w, h, floor)
    g.rect(0, 0, w, 2, '#'); g.rect(0, 0, 1, h, '#'); g.rect(w - 1, 0, 1, h, '#'); g.rect(0, h - 1, w, 1, '#')
    if exit_x is not None: g.set(exit_x, h - 1, floor)
    return g


def clockshop():
    g = _interior(11, 8, 'W', exit_x=5)
    m = Map('clockshop', '奥托钟表店', g, music='harbor_in', indoor=True)
    m.wall_style = 'wood'
    for x in (1, 2, 8, 9): m.prop('clock_shelf', x, 2)
    m.prop('wallclock', 5, 0, solid=False, layer='below'); m.prop('wallclock', 3, 0, solid=False, layer='below')
    m.prop('counter2', 4, 4); m.talkover = [[4, 4], [5, 4]]
    m.prop('gear', 6, 0, solid=False, layer='below')
    m.npc('otto', 'otto', 5, 3, pages=[['c3_otto_watch', 'v_otto_after'], ['c3_clock_restarted & !c3_otto_watch', 'c3_otto_watch'],
                                       ['c3_otto_done', 'c3_otto_wait'], [None, 'c3_otto']])
    m.warp(5, 7, 'harbor', 5, 14, dir='down')
    return m


def pottery():
    g = _interior(11, 8, 'S', exit_x=5)
    m = Map('pottery', '玛尔塔的陶坊', g, music='harbor_in', indoor=True)
    m.wall_style = 'plaster'
    m.prop('potter_wheel', 4, 3); m.prop('jugs', 1, 2); m.prop('jugs', 2, 2); m.prop('jugs', 8, 2); m.prop('cupboard', 9, 2)
    m.prop('sacks', 1, 5); m.prop('pot', 8, 5)
    m.npc('marta', 'marta', 5, 3, pages=[['c3_marta_jug', 'v_marta_after'], ['c3_clock_restarted & !c3_marta_jug', 'c3_marta_jug'],
                                         ['c3_marta_done', 'c3_marta_wait'], ['c3_otto_done', 'c3_marta'], [None, 'v_marta_0']])
    m.warp(5, 7, 'harbor', 7, 29, dir='down')
    return m


def cafe():
    g = _interior(13, 9, 'W', exit_x=6)
    m = Map('cafe', '露西咖啡馆', g, music='harbor_in', indoor=True)
    m.wall_style = 'plaster'
    m.prop('counter', 1, 3); m.talkover = [[1, 3], [2, 3], [3, 3]]
    m.prop('cupboard', 1, 2); m.prop('shelf', 4, 2)
    m.prop('table', 7, 3); m.prop('chair_up', 7, 5); m.prop('table', 9, 6); m.prop('chair_up', 9, 7)
    m.prop('window', 8, 0, solid=False, layer='below'); m.prop('window', 10, 0, solid=False, layer='below')
    m.prop('pot', 11, 2)
    m.npc('lucy', 'lucy', 2, 2, pages=[['c3_clock_restarted', 'v_lucy_2'], [None, 'v_lucy_1']])
    m.npc('fried', 'fried', 11, 6, dir='left', pages=[['c3_poem_got', 'v_fried_after'], ['c3_mask_won', 'c3_fried_gift'],
                                                     ['c3_fried_done', 'c3_fried_wait'], [None, 'c3_fried']])
    m.warp(6, 8, 'harbor', 32, 16, dir='down')
    return m


def tower1():
    g = _interior(12, 12, 'S', exit_x=6)
    m = Map('tower1', '钟楼 · 一层', g, music='tower', indoor=True)
    m.wall_style = 'stone'
    m.prop('gear_big', 2, 4, talk='c3_gears'); m.prop('gear_big', 8, 6, talk='c3_gears'); m.prop('gear_big', 3, 8, talk='c3_gears')
    m.prop('stairs_up', 9, 2, solid=False)
    m.warp(9, 2, 'tower2', 2, 7, dir='right')
    m.prop('crate', 1, 2); m.prop('barrel', 10, 9)
    m.warp(6, 11, 'harbor', 22, 11, dir='down')
    return m


def tower2():
    g = _interior(12, 10, 'S')
    m = Map('tower2', '钟楼 · 顶层', g, music='tower', indoor=True)
    m.wall_style = 'stone'
    m.prop('gear_big', 8, 3); m.prop('gear_big', 3, 3)
    m.prop('stairs_down', 2, 8, solid=False)
    m.warp(2, 8, 'tower1', 9, 3, dir='down')
    m.npc('giant', 'm_giant', 6, 4, show='!c3_giant_won', pages=[[None, 'c3_giant_pre']], move='bob')
    return m


MAPS = [forest, world, harbor, clockshop, pottery, cafe, tower1, tower2]
