"""Chapter 1-2 maps: Todtnau village and its interiors."""
from mapkit import Grid, Map
from art import props2  # noqa: F401  (registers props)
from art import props as PR
from art.px import Canvas
from art import pal as P


def _bridge_new():
    from mapkit import _bridge_planks
    return _bridge_planks(3, 1)


def _bridge_broken():
    c = Canvas(48, 16)
    W = P.WOOD
    for x in (1, 17, 31, 45):
        c.rect(x, 4, 3, 10, W[1]); c.rect(x, 4, 3, 1, W[3])
    c.line(3, 8, 12, 11, W[2]); c.line(33, 7, 40, 10, W[2])
    return c


def _sluice_closed():
    from art.props2 import sluice_gate
    return sluice_gate(False)


def _sluice_open():
    from art.props2 import sluice_gate
    return sluice_gate(True)


def _bed_hof():
    img, ax, ay = PR.PROPS['bed_hof']()
    return img


def _trapdoor_open():
    return PR.PROPS['trapdoor_open']()[0]


def village():
    g = Grid(44, 36, '.')
    g.border('T', 2, seed=3, gaps=[(20, 0, 23, 2), (33, 0, 35, 35)])
    # east bank: woods with the road
    g.rect(36, 0, 8, 36, 'T')
    g.scatter('P', 60, (36, 0, 8, 36), seed=5, only='T')
    g.rect(36, 16, 8, 3, '.')
    g.hline(36, 43, 17, '=')
    for x in range(37, 44): g.set(x, 16, '.' if x % 3 else ','); g.set(x, 18, '.')
    # river
    g.rect(33, 0, 3, 36, '~')
    for x in (33, 34, 35):
        g.set(x, 3, 'b')
        g.set(x, 17, 'x')
    # clearings for buildings / sluice / grave
    g.rect(2, 2, 12, 8, '.')
    g.rect(22, 2, 11, 9, '.')
    g.rect(29, 1, 4, 4, '.')
    g.rect(6, 2, 5, 2, '.')
    # roads
    g.path([(21, 0), (21, 12)], '=', width=2)
    g.hline(6, 32, 12, '=', width=2)
    g.hline(6, 7, 9, '=')
    g.vline(7, 9, 11, '=')
    g.vline(25, 6, 11, '=')
    g.vline(30, 10, 12, '=')
    g.hline(26, 32, 17, '=')
    g.vline(19, 17, 25, '=', width=2)
    g.hline(8, 31, 24, '=', width=2)
    g.vline(13, 26, 30, '=')
    g.vline(31, 26, 31, '=')
    # square
    g.rect(16, 11, 11, 7, ':')
    # junkyard
    g.rect(2, 11, 4, 5, '=')
    for y in range(10, 17): g.set(6, y, '|' if y != 12 else '=')
    for x in range(2, 7): g.set(x, 10, '-')
    g.set(6, 10, '-')
    # field
    g.rect(3, 27, 9, 5, 'y')
    for x in range(2, 13): g.set(x, 26, '-'); g.set(x, 32, '-')
    for y in range(26, 33): g.set(2, y, '|'); g.set(12, y, '|')
    g.set(12, 29, '=')
    # decoration
    g.scatter(',', 45, (2, 2, 31, 32), seed=11)
    g.scatter('"', 18, (2, 2, 31, 32), seed=12)
    for (x, y) in ((14, 7), (17, 5), (11, 16), (27, 15), (8, 16), (29, 30), (16, 30), (24, 31), (10, 20), (26, 27), (18, 7), (3, 23), (31, 15)):
        g.set(x, y, 'T')
    for (x, y) in ((15, 9), (9, 23), (20, 27), (27, 8), (11, 5)):
        g.set(x, y, 'B')
    for (x, y) in ((28, 29), (5, 24)):
        g.set(x, y, 'o')
    m = Map('village', '托特瑙村', g, music='village', seed=1)

    # buildings
    m.building(4, 4, w=6, roof_h=3, wall_h=2, roof='thatch', wall='plaster', doors=(2,), windows=(0, 4), chimney=4,
               dormers=(1,), sign='tool', sign_col=3, seed=1, warp=dict(to='workshop', tx=6, ty=8, dir='up'))
    m.building(23, 2, w=5, roof_h=2, wall_h=2, roof='teal', wall='stone', doors=(2,), windows=(0, 4), sign='echo', sign_col=3,
               seed=2, flowers=False, warp=dict(to='shrine', tx=5, ty=8, dir='up'))
    m.building(29, 6, w=4, roof_h=2, wall_h=2, roof='thatch', wall='wood', doors=(1,), windows=(3,), chimney=2, seed=3,
               warp=dict(to='mill', tx=4, ty=6, dir='up'))
    m.building(12, 19, w=6, roof_h=3, wall_h=2, roof='terra', wall='plaster', doors=(2,), windows=(0, 4, 5), chimney=1,
               dormers=(3,), sign='cup', sign_col=3, seed=4, warp=dict(to='tavern', tx=6, ty=8, dir='up'))
    m.building(21, 20, w=5, roof_h=2, wall_h=2, roof='slate_b', wall='stone', doors=(2,), windows=(0, 4), chimney=4, seed=5,
               warp=dict(to='chief', tx=5, ty=7, dir='up'))
    m.building(3, 17, w=4, roof_h=2, wall_h=2, roof='terra', wall='wood', doors=(1,), windows=(3,), seed=6, locked='v_door_pip')
    m.building(27, 19, w=4, roof_h=2, wall_h=2, roof='slate_p', wall='plaster', doors=(1,), windows=(3,), chimney=2, seed=7,
               locked='v_door_lily')

    # props
    m.prop('trough', 20, 14, talk='v_chloe_trough')
    m.prop('well', 24, 12, talk='obj_well')
    m.prop('sign', 17, 11, talk='obj_sign_village')
    m.prop('lamp', 16, 10); m.prop('lamp', 27, 10); m.prop('lamp', 18, 26); m.prop('lamp', 29, 17)
    m.prop('anvil', 9, 10, talk='obj_anvil'); m.prop('logs', 2, 8); m.prop('barrel', 11, 8); m.prop('crate', 3, 7)
    m.prop('barrel', 28, 9); m.prop('sacks', 32, 10); m.prop('crate', 11, 23); m.prop('barrel', 18, 23)
    m.prop('pot', 26, 23); m.prop('bench', 23, 16); m.prop('bench', 13, 14)
    m.prop('sluice', 32, 2)
    for (x, y) in ((2, 12), (4, 11), (5, 14), (2, 15)):
        m.prop('junk', x, y)
    m.prop('sign', 32, 18, talk='obj_sign_bridge', cond='c2_bridge_done')
    m.prop('grave', 8, 2, talk='obj_grave', cond='c4_hof_died')
    m.prop('chest', 31, 31)
    # conditional scenery
    m.decal('bridge_new', _bridge_new, 33, 17, 3, 1, cond='c2_bridge_done', walk=[[33, 17], [34, 17], [35, 17]])
    m.decal('bridge_broken', _bridge_broken, 33, 17, 3, 1, cond='!c2_bridge_done')
    m.decal('sluice_c', _sluice_closed, 33, 1, 3, 1, cond='!c1_sluice_open')
    m.decal('sluice_o', _sluice_open, 33, 1, 3, 1, cond='c1_sluice_open')
    m.anim('wheel', 33, 7, spin='c1_mill_done')

    # npcs
    m.npc('hans', 'hans', 31, 11, dir='left', pages=[
        ['!c1_hans_talked', 'c1_hans'],
        ['c1_hans_talked & !c1_sluice_open', 'c1_hans_wait'],
        ['c1_sluice_open & !c1_hammer_broke', 'c1_mill_gear'],
        ['c1_hammer_broke & !c1_hammer_fixed', 'c1_hans_broke'],
        ['c1_hammer_fixed & !c1_mill_done', 'c1_mill_done'],
        ['c2_bridge_started & !c2_bridge_wood', 'c2_bridge_hans'],
        ['c4_hof_died', 'v_hans_5'], ['c2_hof_ill', 'v_hans_2'], [None, 'v_hans_1']])
    m.npc('pip', 'pip', 18, 20, move='wander', pages=[
        ['c1_hammer_broke & !c1_got_head', 'c1_pip_dive'],
        ['c1_hans_talked & !c1_knows_plank', 'c1_pip_river'],
        ['c4_hof_died', 'v_pip_5'], ['c2_bridge_done', 'v_pip_3'], ['c1_chloe_arrived', 'v_pip_2'], [None, 'v_pip_1']])
    m.npc('lily', 'lily', 23, 14, pages=[
        ['c4_hof_died', 'v_lily_5'], ['c2_done', 'v_lily_3'], ['c1_tin_joined', 'v_lily_2'], [None, 'v_lily_1']])
    m.npc('greta', 'greta', 13, 28, dir='left', pages=[
        ['c2_bridge_started & !c2_bridge_rope', 'c2_bridge_greta'],
        ['c2_bridge_done & !greta_shoes', 'v_greta_shoes'],
        ['greta_shoes', 'v_greta_2'], [None, 'v_greta_1']])
    m.npc('chloe', 'chloe', 20, 16, show='false', pages=[[None, 'v_chloe_trough']])
    m.npc('tin', 'tin', 3, 13, show='!c1_tin_joined', pages=[['c1_quest_tin', 'c1_tin_repair'], [None, 'v_tin_broken']])
    m.npc('cat', 'cat', 17, 16, move='wander', pages=[[None, 'v_cat']])
    m.npc('dog', 'dog', 15, 25, move='wander', pages=[[None, 'v_dog']])
    m.npc('bato', 'bato', 32, 16, show='c2_hof_bed_done & !c2_done', pages=[
        ['!c2_bridge_started', 'c2_bridge_start'],
        ['c2_bridge_wood & c2_bridge_rope & c2_bridge_nails & c2_bridge_food & !c2_bridge_done', 'c2_bridge_build'],
        ['c2_bridge_started & !c2_bridge_done', 'c2_bridge_wait'], [None, 'v_bato_3']])
    m.npc('hof_bridge', 'hof', 31, 18, dir='right', show='c2_bridge_done & !c2_done', pages=[[None, 'c2_farewell']])
    m.npc('bato_grave', 'bato', 7, 3, dir='left', show='c4_hof_died & !c5_grave_done', pages=[[None, 'c5_grave']])
    m.npc('molly_grave', 'molly', 9, 3, dir='left', show='c4_hof_died & !c5_grave_done', pages=[[None, 'c5_grave']])

    # events
    m.event(16, 11, 'c1_chloe_arrive', trigger='step', cond='c1_mill_done & !c1_chloe_arrived', w=11, h=7)
    m.event(0, 0, 'c2_hof_collapse', trigger='auto', cond='c2_ister_done & !c2_hof_ill')
    m.event(32, 2, None, trigger='talk')
    m.events[-1]['pages'] = [['c1_sluice_open', 'v_sluice_open'], ['c1_got_key & c1_plank_fixed', 'c1_sluice_open'],
                             ['c1_got_key', 'c1_sluice_notyet'], [None, 'c1_sluice_locked']]
    m.event(34, 3, None, trigger='talk')
    m.events[-1]['pages'] = [['c1_plank_fixed', 'v_plank_ok'], ['item:hammer', 'c1_plank_fix'], [None, 'c1_plank_look']]
    m.event(31, 31, None, trigger='talk')
    m.events[-1]['pages'] = [['chest_talked', 'obj_chest_done'], [None, 'obj_talking_chest']]
    m.event(10, 3, 'c5_grave', trigger='step', cond='c5_home & !c5_grave_done', h=2)
    m.chest('v_junk', 5, 11, 'coin')
    m.spots = [dict(id='v_barrel', x=18, y=23, item='coin', label='木桶')]

    # warps
    m.warp(21, 0, 'forest', 25, 42, dir='up', cond='ch>=2', deny='v1_gate_deny', w=2)
    m.warp(43, 17, 'world', 8, 20, dir='right', cond='c2_done', w=1, h=1)
    return m


def _interior(w, h, floor='W', exit_x=None):
    g = Grid(w, h, floor)
    g.rect(0, 0, w, 2, '#')
    g.rect(0, 0, 1, h, '#'); g.rect(w - 1, 0, 1, h, '#'); g.rect(0, h - 1, w, 1, '#')
    if exit_x is not None: g.set(exit_x, h - 1, floor)
    return g


def workshop():
    g = _interior(14, 10, 'W', exit_x=6)
    m = Map('workshop', '修补工坊', g, music='home', indoor=True)
    m.wall_style = 'wood'
    m.prop('stairs_up', 2, 2, solid=False)
    m.warp(2, 2, 'attic', 7, 3, dir='down')
    m.prop('workbench', 4, 2, talk='obj_workbench')
    m.prop('fireplace', 7, 2)
    m.prop('shelf', 10, 2)
    m.prop('bed', 12, 2)
    m.decal('bed_hof', _bed_hof, 12, 1, 1, 2, cond='c2_hof_ill & !c4_hof_died')
    m.prop('crate', 12, 6)
    m.prop('barrel', 1, 7); m.prop('barrel', 1, 8); m.prop('anvil', 9, 5, talk='obj_anvil')
    m.prop('rug', 4, 5, solid=False, layer='below')
    m.prop('window', 4, 0, solid=False, layer='below'); m.prop('wallclock', 11, 0, solid=False, layer='below')
    m.prop('table1', 11, 6)
    m.npc('hof', 'hof', 5, 4, pages=[
        ['!c1_got_hammer', 'c1_hof_hammer'],
        ['c1_hammer_broke & !c1_got_head', 'c1_hof_nohead'],
        ['c1_got_head & !c1_hammer_fixed', 'c1_hof_fix'],
        ['c1_done', 'v2_hof'], ['c1_tin_joined', 'v1_hof_d'], ['c1_quest_tin', 'v1_hof_c'], ['c1_mill_done', 'v1_hof_b'], [None, 'v1_hof_a']],
        show='!c1_night_done | c1_done & !c2_hof_ill')
    m.npc('hof_morning', 'hof', 6, 7, dir='up', show='c1_night_done & !c1_done', pages=[[None, 'c1_morning']])
    m.event(12, 6, None, trigger='talk')
    m.events[-1]['pages'] = [['c2_bridge_started & !c2_bridge_nails', 'c2_bridge_nails'], [None, 'obj_crate']]
    m.event(12, 3, None, trigger='talk')
    m.events[-1]['pages'] = [['c2_bridge_started & !c2_bridge_nails', 'c2_hof_nails'],
                             ['c2_hof_bed_done & !c4_hof_died', 'c2_hof_sleeping'], [None, 'obj_bed_hero']]
    m.event(0, 0, 'c1_hof_hammer', trigger='auto', cond='c1_woke & !c1_got_hammer')
    m.event(0, 0, 'c1_night', trigger='auto', cond='c1_tin_joined & !c1_night_done')
    m.event(0, 0, 'c2_hof_bed', trigger='auto', cond='c2_hof_ill & !c2_hof_bed_done')
    m.event(6, 8, 'c5_door', trigger='talk', cond='c5_home & !c5_door_fixed')
    m.warp(6, 9, 'village', 6, 9, dir='down')
    return m


def attic():
    g = _interior(10, 7, 'W')
    m = Map('attic', '阁楼', g, music='home', indoor=True)
    m.wall_style = 'wood'
    m.prop('bed', 2, 2, talk='obj_bed_hero')
    m.prop('stairs_down', 7, 2, solid=False)
    m.warp(7, 2, 'workshop', 2, 3, dir='down')
    m.prop('window', 4, 0, solid=False, layer='below')
    m.prop('crate', 8, 4); m.prop('book_pile', 1, 5); m.prop('pot', 5, 2)
    m.event(0, 0, 'c1_wake', trigger='auto', cond='!c1_woke')
    return m


def roof():
    g = Grid(14, 9, 'R')
    g.rect(0, 0, 14, 4, 'Y')
    m = Map('roof', '屋顶', g, music='night', indoor=True, night=True)
    m.prop('pot', 10, 4)
    m.npc('chloe', 'chloe', 8, 5, dir='up', show='c1_tin_joined & !c1_night_done', pages=[[None, 'p_default']])
    return m


def tavern():
    g = _interior(14, 10, 'W', exit_x=6)
    m = Map('tavern', '莫莉的酒馆', g, music='tavern', indoor=True)
    m.wall_style = 'plaster'
    m.prop('counter', 2, 3)
    m.talkover = [[2, 3], [3, 3], [4, 3]]
    m.prop('cupboard', 1, 2); m.prop('shelf', 5, 2)
    m.prop('fireplace', 10, 2)
    m.prop('table', 8, 5); m.prop('chair', 8, 4, solid=True); m.prop('chair_up', 9, 7)
    m.prop('table', 3, 6); m.prop('chair_up', 3, 8); m.prop('chair_up', 4, 8)
    m.prop('barrel', 12, 5); m.prop('barrel', 12, 6); m.prop('pot', 1, 8)
    m.prop('window', 7, 0, solid=False, layer='below')
    m.npc('molly', 'molly', 3, 2, pages=[
        ['c1_hans_talked & !c1_knows_chief', 'c1_molly_gate'],
        ['c2_bridge_started & !c2_bridge_food', 'c2_bridge_molly'],
        ['c4_hof_died', 'v_molly_5'], ['c2_bridge_done', 'v_molly_3'], ['c1_chloe_arrived', 'v_molly_2'], [None, 'v_molly_1']])
    m.spots = [dict(id='t_pot', x=1, y=8, item='coin', label='陶罐')]
    m.warp(6, 9, 'village', 14, 24, dir='down')
    return m


def chief():
    g = _interior(11, 9, 'W', exit_x=5)
    g.rect(1, 2, 9, 1, 'K')
    m = Map('chief', '村长家', g, music='home', indoor=True)
    m.wall_style = 'plaster'
    m.prop('shelf', 1, 2, talk='obj_books_village'); m.prop('shelf', 2, 2, talk='obj_books_village')
    m.prop('desk', 6, 2); m.prop('rug', 3, 4, solid=False, layer='below')
    m.prop('bed_red', 9, 4); m.prop('pot', 1, 6)
    m.prop('window', 4, 0, solid=False, layer='below')
    m.npc('bato', 'bato', 5, 4, show='!(c2_hof_bed_done & !c2_done)', pages=[
        ['c1_knows_chief & c1_knows_plank & !c1_got_key', 'c1_bato_key'],
        ['c1_knows_chief & !c1_got_key', 'c1_bato_ask'],
        ['c2_bridge_done', 'v_bato_3'], [None, 'v_bato_1']])
    m.warp(5, 8, 'village', 23, 24, dir='down')
    return m


def mill():
    g = _interior(10, 8, 'S', exit_x=4)
    m = Map('mill', '磨坊', g, music='home', indoor=True)
    m.wall_style = 'stone'
    m.prop('millstone', 4, 3)
    m.prop('sacks', 1, 4); m.prop('sacks', 8, 4); m.prop('barrel', 8, 2); m.prop('crate', 1, 2)
    m.prop('gear', 6, 0, solid=False, layer='below')
    m.spots = [dict(id='m_barrel', x=8, y=2, item='coin', label='木桶')]
    m.warp(4, 7, 'village', 30, 10, dir='down')
    return m


def shrine():
    g = _interior(11, 10, 'S', exit_x=5)
    for y in range(3, 9): g.set(5, y, 'k')
    m = Map('shrine', '回声祠', g, music='shrine', indoor=True)
    m.wall_style = 'stone'
    m.prop('echostone', 5, 2)
    m.event(5, 2, None, trigger='talk')
    m.events[-1]['pages'] = [['ending', 'obj_echostone_end'], ['c4_truth_echo', 'obj_echostone2'], [None, 'obj_echostone']]
    for (x, y) in ((2, 5), (7, 5), (2, 7), (7, 7)): m.prop('bench', x, y)
    m.prop('lamp_lit', 3, 2); m.prop('lamp_lit', 7, 2)
    m.npc('priest', 'priest', 3, 4, pages=[['c5_home', 'v_priest_5'], [None, 'v_priest_1']])
    m.event(0, 0, 'c5_home', trigger='auto', cond='c4_done & !c5_home')
    m.warp(5, 9, 'village', 25, 6, dir='down')
    return m


def hut():
    g = _interior(10, 8, 'W', exit_x=4)
    m = Map('hut', '伊斯特的木屋', g, music='clearing', indoor=True)
    m.wall_style = 'wood'
    m.prop('shelf', 1, 2, talk='obj_books_hut'); m.prop('stove', 7, 2)
    m.prop('table', 3, 3); m.prop('chair_up', 3, 5)
    m.prop('bed', 8, 4); m.prop('book_pile', 1, 5); m.prop('pot', 2, 6)
    m.prop('trapdoor', 6, 3, solid=False, layer='below')
    m.decal('trap_open', _trapdoor_open, 6, 3, 1, 1, cond='c5_trapdoor_open')
    m.event(3, 3, 'obj_hut_tea', trigger='talk')
    m.event(6, 3, 'c5_trapdoor', trigger='talk', cond='c5_ister_done & !c5_trapdoor_open')
    m.warp(6, 3, 'corridor', 1, 6, dir='right', cond='c5_trapdoor_open')
    m.warp(4, 7, 'forest', 25, 7, dir='down')
    return m


MAPS = [village, workshop, attic, roof, tavern, chief, mill, shrine, hut]
