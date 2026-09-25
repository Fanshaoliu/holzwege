"""16x16 item icons -> assets/items.png (+ data/items.js)."""
import json
import math
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from art.px import Canvas, mix  # noqa: E402
from art import pal as P  # noqa: E402

OUT = P.OUT
W = P.WOOD; M = P.METAL; G = P.GOLD


def ic():
    return Canvas(16, 16)


def hammer():
    c = ic(); c.line(3, 13, 10, 6, W[3]); c.line(4, 13, 11, 6, W[2]); c.rect(8, 2, 7, 4, M[3]); c.rect(8, 2, 7, 1, M[5]); c.px(14, 5, M[1]); c.outline(OUT); return c
def hammer_handle():
    c = ic(); c.line(3, 13, 11, 5, W[3]); c.line(4, 13, 12, 5, W[2]); c.px(8, 9, W[1]); c.outline(OUT); return c
def hammer_head():
    c = ic(); c.rect(4, 6, 9, 5, M[3]); c.rect(4, 6, 9, 1, M[5]); c.rect(7, 7, 2, 3, M[0]); c.px(5, 12, P.WATER[4]); c.px(10, 12, P.WATER[4]); c.outline(OUT); return c
def sluice_key():
    c = ic(); c.circle(5, 6, 3, G[3]); c.circle(5, 6, 1.4, (0, 0, 0, 0)); c.line(7, 8, 13, 14, G[3]); c.px(12, 12, G[2]); c.px(11, 13, G[2]); c.outline(OUT); return c
def forest_map():
    c = ic(); c.rect(2, 3, 12, 10, P.PLASTER[3]); c.line(3, 11, 7, 6, W[2]); c.line(7, 6, 12, 8, W[2]); c.line(7, 6, 6, 4, W[2])
    c.px(12, 8, P.RED[3]); c.px(6, 4, P.RED[3]); c.px(3, 11, P.GRASS[2]); c.outline(OUT); return c
def lantern():
    c = ic(); c.rect(5, 5, 6, 8, M[1]); c.rect(6, 6, 4, 6, P.AMBER[3]); c.rect(6, 6, 2, 3, P.AMBER[4]); c.rect(4, 4, 8, 1, M[2]); c.rect(4, 13, 8, 1, M[2]); c.line(6, 3, 10, 3, M[2]); c.outline(OUT); return c
def letter_sealed():
    c = ic(); c.rect(2, 4, 12, 9, P.PLASTER[4]); c.line(2, 4, 8, 9, P.PLASTER[1]); c.line(13, 4, 8, 9, P.PLASTER[1]); c.circle(8, 9, 1.6, P.RED[3]); c.outline(OUT); return c
def letter():
    c = ic(); c.rect(3, 2, 10, 12, P.PLASTER[4]); [c.hline(5, 11, y, P.PLASTER[1]) for y in (5, 7, 9, 11)]; c.outline(OUT); return c
def bridge_nail():
    c = ic(); c.rect(4, 3, 8, 2, M[3]); c.rect(7, 5, 2, 8, M[3]); c.px(7, 13, M[2]); c.px(8, 14, M[2]); c.hline(5, 10, 3, M[5]); c.outline(OUT); return c
def pendulum():
    c = ic(); c.vline(8, 1, 9, G[2]); c.circle(8, 11, 3.4, G[3]); c.circle(7, 10, 1.4, G[5]); c.outline(OUT); return c
def watch():
    c = ic(); c.circle(8, 9, 5.5, G[2]); c.circle(8, 9, 4.2, P.PLASTER[4]); c.line(8, 9, 6, 11, OUT); c.line(8, 9, 10, 6, OUT); c.rect(7, 1, 2, 3, G[3]); c.outline(OUT); return c
def jug():
    c = ic(); c.ellipse(8, 10, 5, 4.5, P.TERRA[2]); c.rect(6, 3, 4, 4, P.TERRA[2]); c.ellipse(8, 3, 2.4, 1, P.TERRA[1]); c.line(11, 5, 13, 8, P.TERRA[2]); c.px(6, 8, P.TERRA[4]); c.vline(5, 8, 11, P.TERRA[3]); c.outline(OUT); return c
def poem():
    c = ic(); c.rect(3, 2, 10, 12, P.PLASTER[3]); c.hline(5, 11, 5, OUT); c.hline(5, 9, 7, OUT); c.line(5, 10, 11, 12, P.RED[2]); c.line(6, 12, 11, 9, P.RED[2]); c.outline(OUT); return c
def photo():
    c = ic(); c.rect(2, 3, 12, 10, P.PLASTER[4]); c.rect(3, 4, 10, 7, P.SLATE_B[2]); c.circle(6, 7, 1.6, P.RED[3]); c.circle(10, 7, 1.6, W[3]); c.rect(5, 9, 3, 2, P.PLASTER[3]); c.rect(9, 9, 3, 2, P.PLASTER[3]); c.outline(OUT); return c
def archive_key():
    c = ic(); c.circle(5, 5, 3, P.MARBLE[4]); c.circle(5, 5, 1.2, P.GLOW[2]); c.line(7, 7, 13, 13, P.MARBLE[3]); c.px(12, 11, P.MARBLE[2]); c.outline(OUT); return c
def teleport_log():
    c = ic(); c.rect(3, 2, 10, 12, P.GLOW[1]); c.rect(4, 3, 8, 10, P.GLOW[2]); [c.hline(5, 10, y, P.GLOW[4]) for y in (5, 7, 9)]; c.outline(OUT); return c
def backup_void():
    c = ic(); c.rect(3, 3, 10, 10, P.MARBLE[4]); c.line(3, 3, 12, 12, P.RED[3]); c.line(12, 3, 3, 12, P.RED[3]); c.outline(OUT); return c
def pebble():
    c = ic(); c.ellipse(8, 9, 5, 4, P.STONE[3]); c.ellipse(7, 8, 3, 2, P.AMBER[3], only='opaque'); c.px(6, 7, P.AMBER[4]); c.outline(OUT); return c
def bell():
    c = ic(); c.ellipse(8, 8, 4.5, 5, G[3]); c.rect(3, 11, 10, 2, G[2]); c.px(6, 5, G[5]); c.rect(7, 2, 2, 2, G[2]); c.outline(OUT); return c
def phone():
    c = ic(); c.rect(5, 2, 6, 12, (20, 20, 26, 255)); c.rect(6, 3, 4, 9, (46, 50, 64, 255)); c.line(6, 4, 9, 9, M[4]); c.outline(OUT); return c
def shoes():
    c = ic(); c.ellipse(5, 10, 3.6, 2.6, (104, 70, 40, 255)); c.ellipse(11, 11, 3.6, 2.6, (104, 70, 40, 255)); c.px(5, 9, (50, 30, 18, 255)); c.px(11, 10, (50, 30, 18, 255)); c.outline(OUT); return c
def coin():
    c = ic(); c.circle(8, 8, 5, P.METAL[3]); c.circle(8, 8, 4, P.METAL[4]); c.px(7, 6, P.METAL[5]); c.hline(6, 10, 9, P.METAL[2]); c.outline(OUT); return c
def coin_jar():
    c = ic(); c.rect(4, 4, 8, 10, (190, 210, 220, 255)); c.rect(4, 3, 8, 2, G[2]); [c.circle(x, y, 1.5, P.METAL[4]) for (x, y) in ((6, 12), (9, 12), (7, 9), (10, 10))]; c.outline(OUT); return c


ITEMS = [
    ('hammer', '霍夫的锤子', '霍夫用了四十年的锤子。锤柄换过一次，是你自己装的。用它的时候，你会忘了它。', hammer),
    ('hammer_handle', '光秃秃的锤柄', '锤头飞进了河里。只剩一根木柄，上面有裂纹、虫眼，和一圈别人的手印。', hammer_handle),
    ('hammer_head', '锤头', '皮普从河里捞上来的锤头，还在滴水。', hammer_head),
    ('sluice_key', '水闸钥匙', '村长给的钥匙。说好了，先把木桥上那块板子钉牢。', sluice_key),
    ('forest_map', '林中路图', '老樵的爷爷画的地图。每条路的尽头都画着叉。死路尽头也不是什么都没有。', forest_map),
    ('lantern', '伊斯特的灯', '一盏旧灯。它照亮一圈，那一圈外面就显得更黑。', lantern),
    ('letter_sealed', '霍夫的信（未拆）', '「等我走了再拆。早拆了，我死了也爬起来揍你。」', letter_sealed),
    ('letter', '霍夫的信', '「要是哪天你找到了把你放在那儿的人……告诉它：你很好。门轴记得修。」', letter),
    ('bridge_nail', '桥钉', '钉帽上刻着架桥那天的日子。全村的人每人一颗。', bridge_nail),
    ('pendulum', '摆锤', '钟楼擒纵机构的摆锤。玛尔塔拿它压了十年泥巴。', pendulum),
    ('watch', '停摆的怀表', '奥托妻子的怀表，停在九点二十七分。那一刻没有过去，它一直在奥托身上。', watch),
    ('jug', '空壶', '玛尔塔手捏的陶壶，壶身有一道她拇指留下的指痕。装什么都行，空着也行。', jug),
    ('poem', '诗人的残页', '「哪里有危险，哪里也生长着救渡。」以太执行不了这一页。', poem),
    ('photo', '旧照片', '克洛伊和赛拉。那年克洛伊十二岁，刚进学院。', photo),
    ('archive_key', '档案库钥匙', '笛卡教授「丢」的一把铜钥匙。', archive_key),
    ('teleport_log', '移位记录', '执行官克洛伊，移位记录三千一百二十七次。原位分解，异地重建。', teleport_log),
    ('backup_void', '作废的续存凭证', '上面有克洛伊的签名。从那天起，她只会死一次。', backup_void),
    ('pebble', '发光的石子', '刻着一行字：请让他在这里。', pebble),
    ('bell', '无声铃', '没有铃舌的铜铃。只在你什么都不想的时候响。', bell),
    ('phone', '黑色玻璃板', '旧世的人随身带的东西。它没坏，能和它说话的那个世界已经不在了。', phone),
    ('shoes', '一双旧农鞋', '葛蕾塔穿了三十年的鞋。鞋口里被脚磨出一块黑。', shoes),
    ('coin', '旧世硬币', '正面是一个人，背面是一片叶子。两百年前的人拿它换面包。', coin),
    ('coin_jar', '一罐旧世硬币', '十二枚，一枚不差。罐子里装着一个时代。', coin_jar),
]


def main():
    sheet = Canvas(16 * len(ITEMS), 16)
    data = {}
    for i, (iid, name, desc, fn) in enumerate(ITEMS):
        sheet.blit(fn(), i * 16, 0)
        data[iid] = {'name': name, 'desc': desc, 'icon': i}
    sheet.save('assets/items.png')
    with open('data/items.js', 'w', encoding='utf-8') as f:
        f.write('window.ITEMS = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    print('icons', len(ITEMS))


if __name__ == '__main__':
    main()
