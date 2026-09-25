"""The capital Gestell and its interiors."""
from mapkit import Grid, Map
from art import props2  # noqa: F401
from art import props as PR
from art.px import Canvas
from art import pal as P

CAP_LEGEND = {
    '.': dict(base='plaza'), 'g': dict(base='grass'), ',': dict(base='grass', decor='flowers'),
    'T': dict(base='grass', obj='tree'), 'B': dict(base='grass', obj='bush'), 'M': dict(base='marble'),
    'h': dict(base='grass', obj='bushf'),
}


def _ivy_door():
    c = Canvas(16, 16)
    c.rect(2, 1, 12, 15, P.METAL[1]); c.rect(3, 2, 10, 13, P.METAL[2]); c.px(10, 8, P.GOLD[4])
    for i in range(18):
        x = int(1 + (i * 7) % 15); y = int((i * 5) % 16)
        c.px(x, y, P.LEAF[3]); c.px(x, y + 1 if y < 15 else y, P.LEAF[2])
    c.outline(P.OUT)
    return c


def capital():
    g = Grid(48, 42, '.')
    g.rect(0, 0, 48, 2, '#'); g.rect(0, 0, 2, 42, '#'); g.rect(46, 0, 2, 42, '#'); g.rect(0, 40, 48, 2, '#')
    g.rect(22, 40, 4, 2, '.')
    # avenues of marble
    g.rect(22, 10, 4, 30, 'M'); g.rect(2, 20, 44, 3, 'M')
    # academy garden
    g.rect(32, 10, 13, 10, 'g'); g.scatter(',', 18, (32, 10, 13, 10), seed=51, only='g')
    for x in range(32, 45, 3): g.set(x, 19, 'h')
    # west gardens & planters
    g.rect(3, 12, 8, 6, 'g'); g.scatter(',', 10, (3, 12, 8, 6), seed=52, only='g')
    for (x, y) in ((4, 13), (9, 16), (27, 11), (27, 17), (20, 11), (20, 17), (13, 25), (32, 25), (13, 36), (32, 36)):
        g.set(x, y, 'T')
    m = Map('capital', '格斯特尔城', g, music='capital', legend=CAP_LEGEND, seed=12)
    m.wall_style = 'marble'
    m.building(19, 3, w=8, roof_h=3, wall_h=3, roof='slate_b', wall='marble', doors=(4,), windows=(1, 6), seed=21,
               flowers=False, warp=dict(to='orderhq', tx=6, ty=7, dir='up'))
    m.building(33, 3, w=10, roof_h=3, wall_h=3, roof='gold', wall='marble', doors=(5,), windows=(1, 3, 7, 9), seed=22,
               flowers=False, glow=True, warp=dict(to='lab', tx=6, ty=7, dir='up'))
    m.building(3, 4, w=7, roof_h=2, wall_h=3, roof='white', wall='marble', doors=(3,), windows=(1, 5), seed=23,
               flowers=False, warp=dict(to='museum', tx=7, ty=7, dir='up'))
    m.building(4, 27, w=9, roof_h=2, wall_h=3, roof='slate_p', wall='marble', doors=(4,), windows=(1, 2, 6, 7), seed=24,
               flowers=False, glow=True, warp=dict(to='backup', tx=8, ty=10, dir='up'))
    for (x, y, r) in ((14, 12, 'slate_b'), (27, 26, 'slate_b'), (14, 30, 'white'), (34, 30, 'slate_b'), (38, 34, 'white')):
        m.building(x, y, w=5, roof_h=2, wall_h=2, roof=r, wall='marble', doors=(2,), windows=(0, 4), seed=x + y, flowers=False,
                   locked='v_door_capital')
    m.prop('banner', 18, 7); m.prop('banner', 27, 7); m.prop('banner', 32, 7)
    m.prop('fountain', 36, 12)
    m.prop('kiosk', 20, 24)
    m.prop('airship', 25, 33)
    m.prop('telescope', 44, 24, talk='c4_dam')
    for (x, y) in ((21, 12), (26, 12), (21, 18), (26, 18), (21, 30), (26, 30), (10, 21), (37, 21), (21, 38), (26, 38)):
        m.prop('lamp_white', x, y)
    m.prop('pot', 3, 34)
    m.decal('ivy', _ivy_door, 45, 15, 1, 1, solid=[[45, 15]])
    m.event(45, 15, None, trigger='talk')
    m.events[-1]['pages'] = [['c4_archive_open', 'c4_archive_go'], ['item:archive_key', 'c4_archive_door'], [None, 'c4_archive_locked']]
    m.event(25, 33, 'obj_airship', trigger='talk')
    m.chest('cap_garden', 44, 11, 'coin')
    m.spots = [dict(id='cap_pot', x=3, y=34, item='coin', label='花盆')]
    # people
    m.npc('orderguard', 'orderguard', 22, 9, pages=[['c4_chloe_ran & !c4_wall_done', 'c4_hint_2'], [None, 'v_cap_8']])
    m.npc('sera', 'sera_faceless', 36, 16, dir='up', show='c4_gest_met & !c4_sera_restored', pages=[
        ['c4_backup_deleted', 'c4_sera_truth'], ['c4_sera_met', 'c4_sera_again'], [None, 'c4_sera']])
    m.npc('student', 'student', 34, 17, dir='right', pages=[[None, 'v_cap_7']])
    m.npc('youth', 'youth_half', 16, 22, pages=[[None, 'v_cap_5']])
    m.npc('damman', 'damman_faded', 43, 25, dir='right', pages=[['c4_dam_seen', 'v_dam_after'], [None, 'c4_dam']])
    m.npc('backupman', 'citizen_m', 10, 33, pages=[[None, 'v_cap_6']])
    m.npc('hint1', 'citizen_m_faceless', 24, 28, move='wander', pages=[['c4_chloe_ran & !c4_wall_done', 'c4_hint_1'], ['c5_home', 'v_cap_after'], [None, 'v_cap_1']])
    m.npc('cit2', 'citizen_f_faceless', 30, 21, move='wander', pages=[[None, 'v_cap_2']])
    m.npc('cit3', 'citizen_m_faceless', 12, 21, move='wander', pages=[[None, 'v_cap_4']])
    m.npc('cit4', 'citizen_f_faceless', 18, 34, move='wander', pages=[[None, 'v_cap_1']])
    for i, x in enumerate((21, 22, 23, 24)):
        m.npc(f'queue{i}', 'citizen_f_faceless' if i % 2 else 'citizen_m_faceless', x, 26, dir='up', pages=[[None, 'v_cap_3']])
    m.npc('chloe', 'chloe', 3, 36, dir='left', show='c4_chloe_ran & !c4_wall_done', pages=[[None, 'c4_wall']])
    m.event(0, 0, 'c4_arrive', trigger='auto', cond='!c4_arrived')
    m.warp(22, 41, 'world', 38, 9, dir='down', w=4)
    return m


def _interior(w, h, floor='M', exit_x=None):
    g = Grid(w, h, floor)
    g.rect(0, 0, w, 2, '#'); g.rect(0, 0, 1, h, '#'); g.rect(w - 1, 0, 1, h, '#'); g.rect(0, h - 1, w, 1, '#')
    if exit_x is not None: g.set(exit_x, h - 1, floor)
    return g


def orderhq():
    g = _interior(12, 9, 'M', exit_x=6)
    g.rect(5, 2, 2, 6, 'k')
    m = Map('orderhq', '秩序司 · 院长室', g, music='capital_in', indoor=True)
    m.wall_style = 'marble'
    m.prop('desk', 5, 2); m.prop('banner', 2, 2); m.prop('banner', 9, 2)
    m.prop('window', 3, 0, solid=False, layer='below'); m.prop('window', 8, 0, solid=False, layer='below')
    m.prop('shelf_white', 1, 5); m.prop('shelf_white', 10, 5)
    m.npc('gest', 'gest', 6, 4, show='!c4_gest_warned', pages=[['c4_gest_met', 'c4_gest_busy'], [None, 'c4_gest']])
    m.warp(6, 8, 'capital', 23, 9, dir='down')
    return m


def lab():
    g = _interior(12, 9, 'W', exit_x=6)
    m = Map('lab', '学院 · 笛卡研究室', g, music='capital_in', indoor=True)
    m.wall_style = 'plaster'
    m.prop('desk', 2, 2); m.prop('shelf', 6, 2, talk='obj_books_deca'); m.prop('shelf', 7, 2, talk='obj_books_academy')
    m.prop('book_pile', 9, 3); m.prop('book_pile', 1, 6); m.prop('telescope', 10, 3); m.prop('cage', 10, 6)
    m.npc('deca', 'deca', 4, 4, pages=[['c4_letter_opened & !c4_pebble_known', 'c4_deca_pebble'], ['c4_sentinel_won', 'v_deca_after'],
                                       ['c4_deca_met', 'c4_deca_wait'], [None, 'c4_deca']])
    m.npc('sera', 'sera', 8, 5, dir='left', show='c4_sera_restored', pages=[[None, 'v_sera_restored']])
    m.npc('gest', 'gest', 6, 6, dir='up', show='c4_pebble_known & !c4_gest_warned', pages=[[None, 'c4_gest_busy']])
    m.warp(6, 8, 'capital', 38, 9, dir='down')
    return m


def archive():
    g = _interior(22, 16, 'M', exit_x=11)
    g.rect(0, 5, 22, 2, '#'); g.set(11, 5, 'M'); g.set(11, 6, 'M')
    m = Map('archive', '学院档案库', g, music='archive', indoor=True, dark=0.25)
    m.wall_style = 'marble'
    for x in (2, 3, 5, 6, 8, 9, 13, 14, 16, 17, 19):
        for y in (8, 11):
            m.prop('shelf_white', x, y, talk='obj_books_archive', seed=x * 3 + y)
    m.prop('tablet', 10, 3)
    m.prop('shelf_white', 2, 2); m.prop('shelf_white', 18, 2)
    m.npc('sentinel', 'm_sentinel', 11, 6, show='!c4_sentinel_won', pages=[[None, 'c4_sentinel_pre']], move='bob')
    m.event(10, 3, None, trigger='talk', w=2)
    m.events[-1]['pages'] = [['c4_chloe_ran', 'obj_tablet_after'], ['c4_sentinel_won', 'c4_archive_truth']]
    m.warp(11, 15, 'capital', 44, 15, dir='left')
    return m


def museum():
    g = _interior(14, 9, 'M', exit_x=7)
    m = Map('museum', '都城博物馆', g, music='capital_in', indoor=True)
    m.wall_style = 'marble'
    m.prop('painting', 7, 2, talk='c4_museum')
    m.prop('statue', 2, 3); m.prop('statue', 11, 3)
    m.prop('rug_b', 5, 4, solid=False, layer='below')
    m.npc('museumman', 'museumman', 8, 5, dir='up', pages=[['c4_museum_seen', 'v_museum_after'], [None, 'c4_museum']])
    m.warp(7, 8, 'capital', 6, 9, dir='down')
    return m


def backup():
    g = _interior(18, 12, 'M', exit_x=8)
    for y in range(4, 11): g.set(8, y, 'k')
    m = Map('backup', '续存堂', g, music='backup', indoor=True)
    m.wall_style = 'marble'
    for x in range(1, 17):
        if x in (7, 8, 9): continue
        m.prop('backup', x, 2, seed=x)
        m.event(x, 2, 'obj_backup_ivan' if x == 14 else 'obj_backup_cell', trigger='talk')
    for y in (5, 7, 9):
        m.prop('backup', 1, y); m.prop('backup', 16, y)
    m.prop('desk', 7, 4)
    m.prop('lamp_lit', 10, 3)
    m.npc('rena', 'rena', 8, 3, pages=[['c4_rena_done', 'c4_rena_again'], ['c4_wall_done & !c4_backup_deleted', 'c4_backup'], [None, 'v_rena_0']])
    m.talkover = [[7, 4], [8, 4]]
    m.warp(8, 11, 'capital', 8, 32, dir='down')
    return m


MAPS = [capital, orderhq, lab, archive, museum, backup]
