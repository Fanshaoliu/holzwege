"""Compile the screenplay (script/*.md) into game data, and assemble the readable 剧本.md / 思想手记.md."""
import glob
import json
import os
import re
import sys

SPEAKERS = {
    '林恩': 'hero', '{林恩}': 'hero', '克洛伊': 'chloe', '罐头': 'tin', '霍夫': 'hof', '伊斯特': 'ister', '赛拉': 'sera',
    '笛卡': 'deca', '格斯特': 'gest', '弗里德': 'fried', '玛尔塔': 'marta', '奥托': 'otto', '蕾娜': 'rena', '艾可': 'echo',
    '巴托': 'bato', '莫莉': 'molly', '汉斯': 'hans', '皮普': 'pip', '莉莉': 'lily', '葛蕾塔': 'greta', '老祭司': 'priest',
    '老樵': 'woodcutter', '露西': 'lucy', '婆婆': 'coinlady', '看画的老人': 'museumman', '无面的女人': 'faceless',
    '早就知道的男人': 'knewit', '半张脸的年轻人': 'youth', '水手': 'sailor', '以太': 'aether', '回声石': 'aether',
    '无面的男人': 'faceless', '无面的市民': 'faceless', '无面的路人': 'faceless', '排队的人': 'faceless',
}

RE_SCENE = re.compile(r'^###\s*〔([A-Za-z0-9_]+)〕\s*(.*)$')
RE_SAY = re.compile(r'^\*\*(.+?)\*\*(?:（(.+?)）)?：(.*)$')
RE_CMD = re.compile(r'<!--\s*(.*?)\s*-->')
RE_OPT = re.compile(r'^-\s+(.+?)\s*→\s*〔([A-Za-z0-9_]+)〕\s*(?:<!--\s*if\s+(.+?)\s*-->)?\s*$')
RE_GOTO = re.compile(r'^→\s*〔([A-Za-z0-9_]+)〕\s*$')


def parse_cmd(s):
    parts = s.split()
    if not parts: return None
    op, args = parts[0], parts[1:]
    if op == 'set':
        k = ' '.join(args)
        if '=' in k:
            a, b = k.split('=', 1)
            try: b = int(b)
            except ValueError: pass
            return {'t': 'set', 'k': a.strip(), 'v': b}
        return {'t': 'set', 'k': k, 'v': 1}
    if op == 'unset': return {'t': 'set', 'k': args[0], 'v': 0}
    if op in ('give', 'take'): return {'t': op, 'item': args[0], 'n': int(args[1]) if len(args) > 1 else 1}
    if op == 'codex': return {'t': 'codex', 'id': args[0]}
    if op == 'battle': return {'t': 'battle', 'id': args[0]}
    if op == 'warp': return {'t': 'warp', 'map': args[0], 'x': int(args[1]), 'y': int(args[2]), 'dir': args[3] if len(args) > 3 else 'down'}
    if op == 'fade': return {'t': 'fade', 'mode': args[0] if args else 'out'}
    if op in ('music', 'sfx'): return {'t': op, 'name': args[0] if args else 'none'}
    if op == 'wait': return {'t': 'wait', 'ms': int(args[0])}
    if op in ('show', 'hide'): return {'t': op, 'id': args[0]}
    if op == 'party': return {'t': 'party', 'op': args[0], 'id': args[1]}
    if op == 'cg': return {'t': 'cg', 'name': args[0]}
    if op in ('shake', 'flash', 'heal', 'end', 'name'): return {'t': op}
    if op == 'night': return {'t': 'night', 'on': args[0] == 'on'}
    if op == 'title': return {'t': 'title', 'text': ' '.join(args)}
    if op == 'ending': return {'t': 'ending', 'n': int(args[0])}
    if op == 'call': return {'t': 'call', 'id': args[0]}
    if op == 'move': return {'t': 'move', 'id': args[0], 'path': args[1]}
    if op == 'face': return {'t': 'face', 'id': args[0], 'dir': args[1]}
    if op == 'emote': return {'t': 'emote', 'id': args[0], 'e': args[1] if len(args) > 1 else '!'}
    if op == 'if': return {'t': 'if', 'cond': ' '.join(args)}
    if op == 'else': return {'t': 'else'}
    if op == 'endif': return {'t': 'endif'}
    print('WARN unknown cmd', s, file=sys.stderr)
    return None


def parse_file(path, scenes, warnings):
    cur = None
    stack = None
    choice = None
    for ln, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n').strip()
        m = RE_SCENE.match(line)
        if m:
            cur = {'id': m.group(1), 'title': m.group(2), 'cmds': []}
            if cur['id'] in scenes: warnings.append(f'dup scene {cur["id"]}')
            scenes[cur['id']] = cur
            stack = [cur['cmds']]; choice = None
            continue
        if line.startswith('#'):
            cur = None; stack = None; choice = None
            continue
        if cur is None or not line:
            if not line: choice = None
            continue
        if line.startswith('（') and line.endswith('）'):
            continue
        target = stack[-1]
        if line == '**【选择】**':
            choice = {'t': 'choice', 'options': []}
            target.append(choice)
            continue
        mo = RE_OPT.match(line)
        if mo and choice is not None:
            choice['options'].append({'text': mo.group(1), 'goto': mo.group(2), 'cond': mo.group(3)})
            continue
        choice = None
        mg = RE_GOTO.match(line)
        if mg:
            target.append({'t': 'goto', 'id': mg.group(1)}); continue
        # pure command lines (one or more comments)
        if line.startswith('<!--'):
            for c in RE_CMD.findall(line):
                cmd = parse_cmd(c)
                if not cmd: continue
                if cmd['t'] == 'if':
                    node = {'t': 'if', 'cond': cmd['cond'], 'then': [], 'else': []}
                    stack[-1].append(node); stack.append(node['then']); node_stack_push(stack, node)
                elif cmd['t'] == 'else':
                    stack.pop(); node = stack_nodes[-1]; stack.append(node['else'])
                elif cmd['t'] == 'endif':
                    stack.pop(); stack_nodes.pop()
                else:
                    stack[-1].append(cmd)
            continue
        ms = RE_SAY.match(line)
        if ms:
            name, tone, text = ms.group(1), ms.group(2), ms.group(3)
            who = SPEAKERS.get(name)
            item = {'t': 'say', 'name': name, 'text': text}
            if who: item['who'] = who
            if tone: item['tone'] = tone
            target.append(item); continue
        if line.startswith('>'):
            target.append({'t': 'narr', 'text': line[1:].strip()}); continue
        warnings.append(f'{os.path.basename(path)}:{ln}: unparsed line: {line[:40]}')


stack_nodes = []


def node_stack_push(stack, node):
    stack_nodes.append(node)


def parse_codex(path):
    entries = []
    cur = None
    for raw in open(path, encoding='utf-8'):
        line = raw.rstrip('\n').strip()
        m = re.match(r'^##\s*〔([A-Za-z0-9_]+)〕\s*(.*)$', line)
        if m:
            cur = {'id': m.group(1), 'title': m.group(2), 'de': '', 'src': '', 'group': '', 'body': [], 'game': '', 'ai': ''}
            entries.append(cur); continue
        if cur is None or not line: continue
        if line.startswith('- 德文：'): cur['de'] = line[5:]; continue
        if line.startswith('- 出处：'): cur['src'] = line[5:]; continue
        if line.startswith('- 分组：'): cur['group'] = line[5:]; continue
        if line.startswith('**在游戏里**：'): cur['game'] = line[len('**在游戏里**：'):]; continue
        if line.startswith('**关于人工智能**：'): cur['ai'] = line[len('**关于人工智能**：'):]; continue
        cur['body'].append(line)
    return entries


def main():
    scenes, warnings = {}, []
    files = sorted(glob.glob('script/0[1-6]*.md'))
    for f in files:
        parse_file(f, scenes, warnings)
    codex = parse_codex('script/07_思想手记.md')
    # references check
    ids = set(scenes)
    def walk(cmds):
        for c in cmds:
            if c['t'] == 'goto' and c['id'] not in ids: warnings.append(f'missing goto {c["id"]}')
            if c['t'] == 'choice':
                for o in c['options']:
                    if o['goto'] not in ids: warnings.append(f'missing option goto {o["goto"]}')
            if c['t'] == 'if': walk(c['then']); walk(c['else'])
            if c['t'] == 'codex' and c['id'] not in {e['id'] for e in codex}: warnings.append(f'missing codex {c["id"]}')
    for s in scenes.values(): walk(s['cmds'])
    os.makedirs('data', exist_ok=True)
    with open('data/story.js', 'w', encoding='utf-8') as f:
        f.write('window.STORY = ' + json.dumps(scenes, ensure_ascii=False) + ';\n')
        f.write('window.CODEX = ' + json.dumps(codex, ensure_ascii=False) + ';\n')
    # readable deliverables
    with open('剧本.md', 'w', encoding='utf-8') as out:
        for f in sorted(glob.glob('script/0[0-6]*.md')):
            out.write(open(f, encoding='utf-8').read().rstrip() + '\n\n---\n\n')
        app = 'script/appendix_battles.md'
        if os.path.exists(app):
            out.write(open(app, encoding='utf-8').read())
    with open('思想手记.md', 'w', encoding='utf-8') as out:
        out.write(open('script/07_思想手记.md', encoding='utf-8').read())
    chars = sum(len(open(f, encoding='utf-8').read()) for f in glob.glob('script/*.md'))
    print(f'scenes: {len(scenes)}  codex: {len(codex)}  script chars: {chars}')
    for w in warnings: print('  ', w)
    return scenes, codex


if __name__ == '__main__':
    main()
