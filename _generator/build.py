"""Builds index.html (portal look, self-marking) from source.html (the teacher's file).

Usage: python -X utf8 -I _generator/build.py   (run from the site folder)
Part B answers are read from the teacher's own answer keys in source.html.
Part A (book extracts) has no printed key; those answers are in PART_A below and are
flagged on the page. Fails loudly if anything does not line up.
"""
import html as H
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / 'source.html').read_text(encoding='utf-8')
TPL = (HERE / 'template.html').read_text(encoding='utf-8')
GAP = '<span class="g"></span>'


def die(msg):
    sys.exit('BUILD ERROR: ' + msg)


# ---------------------------------------------------------------- Part A answers
# (kind, answers). text: each gap has a list of accepted answers. select: same, picked from the box.
PART_A = {
    'sb7': [
        ('text', [['is raising', 'raising'], ['rises'], ['raised'], ['raise'],
                  ['has risen', 'has been rising'], ['rose']]),
        ('free', [
            'There was a 20% fall in the amount of study time.',
            'There was a considerable improvement in reading speeds.',
            'There has been a slight drop in sales of electronic books this month.',
            'There will be a 10% increase in the number of lecture hours.',
            'There was a peak in the cost of fees in 2011.',
            'There is a rise in the number of words people know as they get older.',
            'There was a fluctuation in literacy levels in rural areas during the 1990s.']),
        ('select', [['of'], ['to'], ['between'], ['at'], ['by'], ['from'], ['to'], ['over']]),
    ],
    'sb8': [
        ('select', [['impressive'], ['outdated'], ['fashionable'], ['dull'], ['stressful']]),
        ('order', [['correct'], ['lively historical'], ['fascinating colourful'],
                   ['correct'], ['correct'], ['correct']]),
        ('free', [
            'Riyadh is the city in Saudi Arabia where I grew up.',
            'The horses that/which we rode in the country park were very beautiful.',
            'People who/that travel by train can enjoy the passing scenery.',
            'Greece is the country where the first Olympic Games took place.',
            'Tourists who/that try new activities are more adventurous. (Also: More adventurous tourists are the ones who try new activities.)']),
        ('text', [['who', 'that'], ['which', 'that'], ['where'], ['that', 'which'],
                  ['that', 'which'], ['that', 'which'], ['where']]),
    ],
    'pt78': [
        ('select', [['attend'], ['participate'], ['write'], ['receive'], ['give']]),
        ('text', [['risen'], ['raise'], ['rose'], ['raised'], ['rising']]),
        ('text', [['to'], ['at'], ['of'], ['in'], ['by']]),
        ('mcq', [['C'], ['C'], ['A'], ['A'], ['B']]),
        ('text', [['destination'], ['resorts'], ['accommodation'], ['facilities'], ['culture']]),
        ('text2', [['impressive modern'], ['lovely traditional'], ['dull industrial'],
                   ['expensive new'], ['friendly local']]),
    ],
}
PART_A_NOTE = ('The book prints no answer key for this exercise. The answers on this page were prepared for it '
               'and checked against the grammar in the unit. If your teacher gives a different answer, follow your teacher.')


# ---------------------------------------------------------------- helpers
def attr(v):
    return H.escape(v, quote=True)


def ans_attr(answers):
    return attr(json.dumps(answers, ensure_ascii=False))


def plain(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def box_words(blk):
    m = re.search(r'<div class="box">(.*?)</div>', blk, re.S)
    if not m:
        die('no word box in block')
    words = [plain(w) for w in re.split(r'&nbsp;/&nbsp;', m.group(1))]
    return [w for w in words if w]


def box_html(blk):
    def fix(m):
        words = [plain(w) for w in re.split(r'&nbsp;/&nbsp;', m.group(1))]
        return '<div class="box">' + ''.join('<span class="w">%s</span>' % H.escape(w) for w in words if w) + '</div>'
    return re.sub(r'<div class="box">(.*?)</div>', fix, blk, flags=re.S)


def gap_control(bid, k, kind, answers, options=None):
    cid = '%s-%d' % (bid, k)
    label = 'Answer %d' % k
    if kind == 'select':
        opts = ''.join('<option value="%s">%s</option>' % (attr(o), H.escape(o)) for o in sorted(options, key=str.lower))
        return ('<select class="gap" data-id="%s" data-ans=\'%s\' aria-label="%s"><option value="">Choose…</option>%s</select>'
                '<span class="fix" data-for="%s"></span>') % (cid, ans_attr(answers), label, opts, cid)
    cls = {'text': 'gap', 'text2': 'gap w2', 'order': 'gap w2'}[kind]
    ph = ' placeholder="e.g. crowded, urban"' if kind == 'order' else ''
    return ('<input class="%s" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" data-id="%s" '
            'data-ans=\'%s\' aria-label="%s"%s><span class="fix" data-for="%s"></span>') % (cls, cid, ans_attr(answers), label, ph, cid)


def example_cls(s):
    return s.replace('class="ex"', 'class="eg"')


def tr_gaps(blk, bid, kind, answers):
    """Replace each blank by an input/select, in order."""
    options = box_words(blk) if kind == 'select' else None
    n = blk.count(GAP)
    if n != len(answers):
        die('%s: %d gaps but %d answers' % (bid, n, len(answers)))
    it = iter(range(len(answers)))

    def sub(_):
        k = next(it)
        return gap_control(bid, k + 1, kind, answers[k], options)
    out = re.sub(re.escape(GAP), sub, blk)
    return box_html(out)


def tr_match(blk, bid, letters):
    m = re.search(r'<ol>(.*?)</ol>', blk, re.S)
    terms = re.findall(r'<li>(.*?)</li>', m.group(1), re.S)
    if len(terms) != len(letters):
        die('%s: %d terms, %d letters' % (bid, len(terms), len(letters)))
    abc = [chr(97 + i) for i in range(len(terms))]
    lis = []
    for i, t in enumerate(terms):
        cid = '%s-%d' % (bid, i + 1)
        opts = ''.join('<option value="%s">%s</option>' % (c, c) for c in abc)
        sel = ('<select class="gap" data-id="%s" data-ans=\'%s\' aria-label="Definition for %s"><option value="">–</option>%s</select>'
               '<span class="fix" data-for="%s"></span>') % (cid, ans_attr([letters[i]]), attr(plain(t)), opts, cid)
        lis.append('<li><b>%s</b> %s</li>' % (t, sel))
    return blk.replace(m.group(0), '<ol class="terms">' + ''.join(lis) + '</ol>')


def tr_mcq(blk, bid, letters):
    """Each <li> with a .opts row becomes a button group. An example li (has class ex) is locked."""
    count = [0]

    def li_sub(m):
        li = m.group(0)
        om = re.search(r'<div class="opts">(.*?)</div>', li, re.S)
        if not om:
            return li
        spans = re.findall(r'<span>(.*?)</span>', om.group(1), re.S)
        ex = 'class="ex"' in li
        locked = None
        btns = []
        for s in spans:
            letter, text = s[0], s[2:]
            if '(example answer)' in text:
                locked = letter
                text = text.replace('(example answer)', '').strip()
            btns.append('<button type="button" class="opt%s" data-v="%s"%s><b>%s</b>%s</button>' % (
                ' locked' if ex else '', letter, ' disabled' if ex else '', letter, H.escape(H.unescape(text))))
        if ex:
            if not locked:
                die('%s: example item without marked answer' % bid)
            grp = '<div class="opts" data-id="%s-ex" data-locked="%s">%s</div>' % (bid, locked, ''.join(btns))
        else:
            k = count[0]
            count[0] += 1
            cid = '%s-%d' % (bid, k + 1)
            grp = ('<div class="opts" role="radiogroup" data-id="%s" data-ans=\'%s\' aria-label="Question %d">%s</div>'
                   '<span class="fix" data-for="%s"></span>') % (cid, ans_attr([letters[k]]), k + 1, ''.join(btns), cid)
        out = li.replace(om.group(0), grp)
        return example_cls(out)
    out = re.sub(r'<li>.*?</li>(?=\s*(?:<li>|</ol>))', li_sub, blk, flags=re.S)
    if count[0] != len(letters):
        die('%s: %d questions, %d answers' % (bid, count[0], len(letters)))
    return out


def tr_free(blk, bid, suggestions):
    count = [0]

    def li_sub(m):
        li = m.group(0)
        if 'class="ex"' in li:
            return example_cls(li)
        k = count[0]
        count[0] += 1
        cid = '%s-%d' % (bid, k + 1)
        add = ('<textarea class="free" data-id="%s" rows="2" aria-label="Your answer %d" placeholder="Write your sentence here"></textarea>'
               '<div class="sugg" hidden><b>Suggestion:</b> %s</div>') % (cid, k + 1, H.escape(suggestions[k]))
        return li.replace('</li>', add + '</li>')
    out = re.sub(r'<li>.*?</li>', li_sub, blk, flags=re.S)
    if count[0] != len(suggestions):
        die('%s: %d items, %d suggestions' % (bid, count[0], len(suggestions)))
    return out


def tr_order(blk, bid, answers):
    count = [0]

    def li_sub(m):
        li = m.group(0)
        if 'class="ex"' in li:
            return example_cls(li)
        k = count[0]
        count[0] += 1
        return li.replace('</li>', ' ' + gap_control(bid, k + 1, 'order', answers[k]) + '</li>')
    out = re.sub(r'<li>.*?</li>', li_sub, blk, flags=re.S)
    if count[0] != len(answers):
        die('%s: %d items, %d answers' % (bid, count[0], len(answers)))
    return out


# ---------------------------------------------------------------- Part B keys
def parse_key(key_html):
    """Return dict part -> list. Exercises 1-2 have A/B/C lines; 3-6 one line of 'n word'."""
    t = key_html
    t = re.sub(r'^<b>Answer key, Exercise \d\.</b>', '', t.strip())
    lines = [l.strip() for l in t.split('<br>') if l.strip()]
    res = {}
    if lines and re.match(r'<b>[ABC]:</b>', lines[0]):
        for l in lines:
            m = re.match(r'<b>([ABC]):</b>\s*(.*)', l, re.S)
            res[m.group(1)] = re.sub(r'\(unused:.*?\)', '', m.group(2)).strip()
    else:
        body = re.split(r'Unused:', plain(t))[0]
        res['G'] = body
    return res


def pairs(text, word_re):
    out = re.findall(r'(\d+)\s+(%s)' % word_re, text)
    nums = [int(n) for n, _ in out]
    if nums != list(range(1, len(nums) + 1)):
        die('key numbering broken: %r' % nums)
    return [w for _, w in out]


# ---------------------------------------------------------------- split the source
body = SRC[SRC.index('<!-- ================= PART A'):SRC.index('<footer>')]
body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
body = re.sub(r'<h2 class="part[^"]*" id="[^"]*">.*?</h2>', '', body, flags=re.S)
body = re.sub(r'<div class="note">.*?</div>', '', body, count=1, flags=re.S)
chunks = re.split(r'(?=<h2 class="sec" id=")', body)
chunks = [c for c in chunks if c.strip()]

TAB_LABELS = {
    'sb7': ('A', 'Unit 7 review'), 'sb8': ('A', 'Unit 8 review'), 'pt78': ('A', 'Progress test'),
    'ex1': ('B', 'Ex 1 · Unit 7'), 'ex2': ('B', 'Ex 2 · Unit 8'), 'ex3': ('B', 'Ex 3 · Speaking 7'),
    'ex4': ('B', 'Ex 4 · Writing 7'), 'ex5': ('B', 'Ex 5 · Speaking 8'), 'ex6': ('B', 'Ex 6 · Writing 8'),
}

# Short teacher notes (Vietnamese) shown under one exercise. They explain the rule and use their own
# examples, so they never give away the answers of the exercise they sit under.
BLOCK_NOTES = {
    'sb7-1': (
        '<div class="note" lang="vi"><b>Khi nào dùng rise, khi nào dùng raise?</b>'
        '<ul style="margin:6px 0 0;padding-left:20px">'
        '<li><b>rise</b> (rise, rose, risen): tự tăng lên, không cần ai tác động và <u>không có tân ngữ</u> theo sau. '
        'Ví dụ: <i>Temperatures rose sharply.</i></li>'
        '<li><b>raise</b> (raise, raised, raised): làm cho cái gì đó tăng lên hoặc nâng nó lên, nên <u>luôn có tân ngữ</u>. '
        'Ví dụ: <i>The shop raised its prices.</i></li>'
        '<li>Cách kiểm tra nhanh: sau chỗ trống có danh từ thì dùng <b>raise</b>. Không có danh từ, chủ ngữ tự tăng thì dùng <b>rise</b>.</li>'
        '<li>Trong Writing Task 1, tả đường trên biểu đồ thì dùng <b>rise</b> (<i>The figure rose to 19%</i>). '
        'Viết <i>The figure raised</i> là lỗi thường gặp.</li>'
        '</ul></div>'),
}

sections_html = []
tab_ids = []
total_auto = 0

for chunk in chunks:
    m = re.match(r'<h2 class="sec" id="([^"]+)">(.*?)</h2>', chunk, re.S)
    sid, title = m.group(1), m.group(2)
    tab_ids.append(sid)
    rest = chunk[m.end():]
    # answer key (Part B)
    km = re.search(r'<div class="key">(.*?)</div>', rest, re.S)
    key = parse_key(km.group(1)) if km else None
    if km:
        rest = rest.replace(km.group(0), '')
    # split into h3 pieces
    pieces = re.split(r'(?=<h3>)', rest)
    intro = pieces[0]
    srcm = re.search(r'<p class="src">(.*?)</p>', intro, re.S)
    src_line = srcm.group(1) if srcm else ''
    src_line = src_line.replace('Answers written by hand in the book are shown in blue as examples.',
                                'Examples written in the book are shown in orange.')
    intro = intro.replace(srcm.group(0), '') if srcm else intro
    out = ['<section class="sec" id="%s" role="tabpanel">' % sid,
           '<div class="sec-head"><h2>%s</h2><p class="src">%s</p>%s<div class="sec-score" aria-live="polite"></div></div>' % (
               title, src_line, ('<div class="note">%s</div>' % PART_A_NOTE) if sid in PART_A else ''),
           intro]
    bi = 0
    for piece in pieces[1:]:
        hm = re.match(r'<h3>(.*?)</h3>', piece, re.S)
        head, content = hm.group(0), piece[hm.end():]
        if not content.strip():
            out.append('<div class="grp">%s</div>' % hm.group(1))
            continue
        bid = '%s-%d' % (sid, bi + 1)
        checkable = True
        if sid in PART_A:
            kind, answers = PART_A[sid][bi]
            if kind == 'mcq':
                content = tr_mcq(content, bid, [a[0] for a in answers])
            elif kind == 'free':
                content = tr_free(content, bid, answers)
                checkable = False
            elif kind == 'order':
                content = tr_order(content, bid, answers)
            else:
                content = tr_gaps(content, bid, kind, answers)
        elif sid in ('ex1', 'ex2'):
            part = 'ABC'[bi]
            if part == 'A':
                content = tr_match(content, bid, pairs(key['A'], '[a-j]'))
            elif part == 'B':
                words = pairs(key['B'], r'[A-Za-z-]+')
                content = tr_gaps(content, bid, 'select', [[w] for w in words])
            else:
                content = tr_mcq(content, bid, pairs(key['C'], '[ABC]'))
        else:
            words = pairs(key['G'], r'[A-Za-z-]+')
            content = tr_gaps(content, bid, 'select', [[w] for w in words])
        content = example_cls(content)
        content = re.sub(r'<ol start="0">', '<ol start="0">', content)
        n_items = len(re.findall(r'data-ans=', content))
        total_auto += n_items
        # The buttons differ per page (homework page: check each exercise; test page: one Finish button).
        actions = '@@ACT:check@@' if checkable else '@@ACT:sugg@@'
        out.append('<div class="blk" data-blk="%s"%s>%s%s%s%s</div>' % (
            bid, ' data-checkable="1"' if checkable else '', head, content, actions,
            BLOCK_NOTES.get(bid, '')))
        bi += 1
    if sid in PART_A and bi != len(PART_A[sid]):
        die('%s: %d blocks, %d specs' % (sid, bi, len(PART_A[sid])))
    out.append('</section>')
    sections_html.append('\n'.join(out))

if set(tab_ids) != set(TAB_LABELS):
    die('sections found: %r' % tab_ids)

ACT_HOMEWORK = {
    'check': ('<div class="actions"><button type="button" class="btn primary js-check">Check answers</button>'
              '<button type="button" class="btn js-reset">Try again</button><span class="blk-score"></span></div>'),
    'sugg': ('<div class="actions"><button type="button" class="btn primary js-sugg">Show suggested answers</button>'
             '<span class="note" style="margin:0;border:0;background:none;padding:0">Write your own answer first, then compare. Other correct answers are possible.</span></div>'),
}
ACT_TEST = {
    'check': '<div class="actions"><span class="blk-score"></span></div>',
    'sugg': '<div class="actions"><span class="note" style="margin:0;border:0;background:none;padding:0">Write your own sentence. Suggested answers appear when you finish the test. This one is not marked.</span></div>',
}

TEST_SECS = ['sb7', 'sb8', 'pt78']
VOCAB_SECS = ['ex1', 'ex2', 'ex3', 'ex4', 'ex5', 'ex6']
BOOK = ('Complete IELTS Bands 4-5 by Guy Brook-Hart and Vanessa Jakeman with David Jay, Cambridge University Press, 2012')

PAGES = [
    dict(file='test.html', mode='test', secs=TEST_SECS, key='ih.complete45.units78.test.v1',
         title='Complete IELTS 4-5 · Units 7-8 Test',
         eyebrow='Complete IELTS Bands 4-5 · Units 7 and 8 · Compulsory test',
         h1='Units 7-8 Test',
         sub=('This test is compulsory. Answer all three parts: <b>Unit 7 review</b>, <b>Unit 8 review</b> and the <b>Progress test</b>. '
              'Then press <b>Finish and send my results</b> at the bottom of the page. You see the correct answers only after you finish. '
              'Your answers are saved on this device while you work.'),
         group='Compulsory test',
         sources=(BOOK + ': Student&rsquo;s Book p.86-87 (Vocabulary and grammar review, Units 7 and 8); Teacher&rsquo;s Book p.97-98 '
                  '(Progress test, Units 7 and 8). Book extracts are reproduced for classroom use by the teacher.')),
    dict(file='vocabulary.html', mode='homework', secs=VOCAB_SECS, key='ih.complete45.units78.vocab.v1',
         title='Complete IELTS 4-5 · Units 7-8 Vocabulary Extension',
         eyebrow='Complete IELTS Bands 4-5 · Units 7 and 8 · Homework',
         h1='Vocabulary Extension',
         sub='Six exercises on the vocabulary of Units 7 and 8. Type or choose your answers, then press <b>Check answers</b>. Your work is saved on this device.',
         group='Exercises 1 to 6',
         sources=('Word lists: ' + BOOK + ', Teacher&rsquo;s Book p.85 and p.96 (Vocabulary extension). '
                  'Exercises 1 to 6 are original materials written from those word lists.')),
]

HERO_EXTRA_TEST = (
    '<p class="who" id="who" hidden></p>\n'
    '<div class="result" id="result" hidden role="status">\n'
    '  <h2>You have finished the test</h2>\n'
    '  <p class="big" id="res-score"></p>\n'
    '  <ul id="res-secs"></ul>\n'
    '  <p class="sent" id="res-sent"></p>\n'
    '  <div class="actions" style="border:0;padding-top:0;margin-top:4px">'
    '<button type="button" class="btn primary" id="res-retry" hidden>Send again</button>'
    '<button type="button" class="btn" id="res-again">Do the test again</button></div>\n'
    '  <p class="src">Open each tab to see what was right and wrong. The sentences you wrote are not marked; suggested answers are shown under them.</p>\n'
    '</div>')
AFTER_TEST = (
    '<div class="finish" id="finish">\n'
    '  <p><b>Before you submit:</b> make sure you have completed <b>Unit 7 review</b>, <b>Unit 8 review</b> and the <b>Progress test</b>. '
    'Check each tab. When you press the button, your answers are marked, you see the correct answers, '
    'and your result is sent to your teacher. You cannot change your answers after that.</p>\n'
    '  <button type="button" class="btn primary" id="finish-btn">Finish and send my results</button>\n'
    '</div>')

sec_by_id = dict(zip(tab_ids, sections_html))
for cfg in PAGES:
    acts = ACT_TEST if cfg['mode'] == 'test' else ACT_HOMEWORK
    secs = [sec_by_id[s] for s in cfg['secs']]
    secs = [re.sub(r'@@ACT:(\w+)@@', lambda m: acts[m.group(1)], s) for s in secs]
    btns = ''.join('<button type="button" class="tab" role="tab" data-sec="%s" aria-selected="false">%s</button>' % (s, TAB_LABELS[s][1])
                   for s in cfg['secs'])
    tabs = '<div class="tabgroup"><span class="glabel">%s</span>%s</div>' % (cfg['group'], btns)
    page = TPL
    for k, val in (('@@TITLE@@', cfg['title']), ('@@EYEBROW@@', cfg['eyebrow']), ('@@H1@@', cfg['h1']), ('@@SUB@@', cfg['sub']),
                   ('@@SOURCES@@', cfg['sources']), ('@@MODE@@', cfg['mode']), ('@@KEY@@', cfg['key']),
                   ('@@TESTID@@', 'complete45-units78'),
                   ('@@HERO_EXTRA@@', HERO_EXTRA_TEST if cfg['mode'] == 'test' else ''),
                   ('@@AFTER@@', AFTER_TEST if cfg['mode'] == 'test' else ''),
                   ('@@TABS@@', tabs), ('@@SECTIONS@@', '\n'.join(secs))):
        page = page.replace(k, val)
    if '@@' in page:
        die('unreplaced placeholder in %s: %s' % (cfg['file'], re.findall(r'@@\w+(?::\w+)?@@', page)[:3]))
    n_auto = len(re.findall(r'data-ans=', page))
    (HERE.parent / cfg['file']).write_text(page, encoding='utf-8')
    print('wrote', cfg['file'], len(page), 'bytes;', n_auto, 'auto-marked answers;', len(cfg['secs']), 'sections')

# ---- landing page: two cards
style = re.search(r'<style>.*?</style>', TPL, re.S).group(0)
landing = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Complete IELTS 4-5 · Units 7-8 · IELTS Harper Portal</title>
%s
<style>.pick{display:grid;gap:14px;margin:0 0 24px}.pick a{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 22px;text-decoration:none;color:var(--ink)}.pick a:hover{border-color:var(--brand)}.pick h2{color:var(--heading);font-size:1.25rem;margin:0 0 4px}.pick p{margin:0;color:var(--muted)}.tag{display:inline-block;font-size:.72rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;border-radius:999px;padding:2px 10px;margin-bottom:8px;background:var(--brand-soft);color:var(--brand)}</style>
</head>
<body>
<div class="topbar"><div class="wrap">
  <a class="brand" href="https://ieltsharper.github.io/portal/"><span class="brand-mark" aria-hidden="true">IH</span>IELTS Harper Portal</a>
  <a class="topbar-link" href="https://ieltsharper.github.io/portal/">&larr; Back to the portal</a>
</div></div>
<main class="wrap">
  <div class="hero">
    <p class="eyebrow">Complete IELTS Bands 4-5 · Units 7 and 8</p>
    <h1>Units 7-8</h1>
    <p class="sub">Choose what you need to do.</p>
  </div>
  <div class="pick">
    <a href="test.html"><span class="tag">Compulsory</span><h2>Units 7-8 Test</h2><p>Unit 7 review, Unit 8 review and the Progress test. You type your name first, and your result is sent to your teacher when you finish.</p></a>
    <a href="vocabulary.html"><span class="tag">Homework</span><h2>Vocabulary Extension</h2><p>Six vocabulary exercises with instant marking. Check each exercise as often as you like.</p></a>
  </div>
</main>
</body>
</html>
''' % style
(HERE.parent / 'index.html').write_text(landing, encoding='utf-8')
print('wrote index.html (landing)')
