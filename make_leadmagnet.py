# -*- coding: utf-8 -*-
"""BIBLY 가입 선물 PDF — 종말 핵심 한눈에 보기 (천년왕국 연대표 & 중요성구 암송노트)"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, PageBreak, Flowable)

# ---- 폰트 ----
pdfmetrics.registerFont(TTFont('Malgun', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunB', 'C:/Windows/Fonts/malgunbd.ttf'))
registerFontFamily('Malgun', normal='Malgun', bold='MalgunB', italic='Malgun', boldItalic='MalgunB')

# ---- 색 ----
INK   = colors.HexColor('#15203a')
NAVY  = colors.HexColor('#1b2a4a')
GOLD  = colors.HexColor('#b8923f')
PAPER = colors.HexColor('#fcfaf6')
SAND  = colors.HexColor('#efe7d6')
LGOLD = colors.HexColor('#f4eedd')
GREY  = colors.HexColor('#5a6275')
LINEC = colors.HexColor('#d9d2c0')

OUT = os.path.join(os.path.dirname(__file__), 'files', '종말핵심-한눈에-보기.pdf')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

MARGIN = 1.5 * cm
doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                        topMargin=1.3*cm, bottomMargin=1.3*cm,
                        title='종말 핵심 한눈에 보기 — 천년왕국 연대표 & 중요성구 암송노트',
                        author='BIBLY 바이블 인사이트 (오광일)')
CW = A4[0] - 2*MARGIN  # content width

def P(text, **kw):
    st = ParagraphStyle('p', fontName='Malgun', fontSize=kw.get('size',10.3),
                        leading=kw.get('leading',15.5), textColor=kw.get('color',INK),
                        alignment=kw.get('align',TA_LEFT), spaceAfter=kw.get('after',0),
                        spaceBefore=kw.get('before',0))
    return Paragraph(text, st)

story = []

# ===== 표지 밴드 =====
band = Table([
    [P('B I B L Y · 바이블 인사이트', size=9.5, color=GOLD, align=TA_CENTER)],
    [P('<b>종말 핵심 한눈에 보기</b>', size=23, leading=29, color=colors.white, align=TA_CENTER)],
    [P('천년왕국 연대표 &amp; 중요성구 암송노트', size=12.5, color=colors.HexColor('#d8d2c4'), align=TA_CENTER)],
], colWidths=[CW])
band.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),INK),
    ('TOPPADDING',(0,0),(-1,0),20), ('BOTTOMPADDING',(0,0),(-1,0),2),
    ('TOPPADDING',(0,1),(-1,1),4), ('BOTTOMPADDING',(0,1),(-1,1),3),
    ('TOPPADDING',(0,2),(-1,2),2), ('BOTTOMPADDING',(0,2),(-1,2),20),
    ('LINEBELOW',(0,0),(-1,-1),3,GOLD),
]))
story += [band, Spacer(1, 14)]

story += [P('종말은 막연한 두려움이 아니라, 성경이 분명한 순서로 보여 주는 <b>소망의 청사진</b>입니다. '
            '이 자료는 「천년왕국 세미나」의 흐름을 따라 종말의 큰 그림을 한눈에 정리하고, '
            '꼭 마음에 새길 핵심 성구를 <b>직접 써 보며</b> 암송하도록 돕습니다.', size=10.5, leading=16.5)]
story += [Spacer(1, 7)]
tip = Table([[P('<b>사용법</b>  ①&nbsp; 먼저 연대표로 종말의 전체 흐름을 잡으세요.  '
                '②&nbsp; 암송노트는 매일 한 구절씩, 직접 손으로 써 보며 외우면 오래 남습니다.', size=9.7, leading=15)]],
             colWidths=[CW])
tip.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LGOLD),('BOX',(0,0),(-1,-1),0.7,GOLD),
                         ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                         ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
story += [tip, Spacer(1, 16)]

# ===== 섹션 제목 =====
def section(title, sub):
    t = Table([[P('<b>'+title+'</b>', size=15, leading=19, color=INK)],
               [P(sub, size=9.3, color=GOLD)]], colWidths=[CW])
    t.setStyle(TableStyle([('LINEBELOW',(0,1),(-1,1),1.4,GOLD),
                           ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,0),1),
                           ('BOTTOMPADDING',(0,1),(-1,1),5),('LEFTPADDING',(0,0),(-1,-1),0)]))
    return t

story += [section('① 천년왕국 연대표', 'THE END-TIMES TIMELINE · 종말의 큰 그림'), Spacer(1,10)]

# ===== 연대표 =====
stages = [
    ('지금','교회 시대 · 은혜의 시대','복음이 온 땅에 전파되는 때. 믿는 자가 죽으면 그 영혼은 즉시 주님과 함께 낙원(중간 상태)에 거합니다.','고후 6:2 · 눅 23:43', GREY),
    ('1','휴거 (성도를 공중으로)','주님이 공중에 강림하시고, 죽은 성도가 부활하며 살아 있는 성도는 변화되어 공중에서 주를 맞이합니다(첫째 부활).','살전 4:16-17 · 고전 15:51-52', GOLD),
    ('2','7년 대환난','땅에 하나님의 심판이 임하고 적그리스도가 일어나는 환난의 때 — 다니엘 70이레의 마지막 한 이레.','단 9:27 · 계 6-18장', NAVY),
    ('3','그리스도의 지상 재림','만왕의 왕으로 친히 땅에 오셔서 짐승과 악의 세력을 심판하십니다(아마겟돈).','계 19:11-21', GOLD),
    ('4','천년왕국','사탄이 결박되고, 그리스도께서 천 년 동안 친히 의(義)로 다스리시는 평화의 나라.','계 20:1-6 · 사 11:6-9', NAVY),
    ('5','사탄의 반란 · 백보좌 심판','천 년 후 사탄이 잠깐 놓여 최후 반란을 일으키나 즉시 진압되고, 죽은 자가 행위대로 심판받습니다(둘째 부활·둘째 사망).','계 20:7-15', GOLD),
    ('6','영원한 나라','새 하늘과 새 땅, 새 예루살렘이 임하여 다시는 사망도 눈물도 없는 하나님과의 영원한 거함.','계 21-22장', INK),
]
for i,(num,title,desc,ref,badge) in enumerate(stages):
    badgecell = P('<b>'+num+'</b>', size=(12 if num.isdigit() else 10.5), color=colors.white, align=TA_CENTER)
    content = [P('<b>'+title+'</b>', size=11.6, color=INK, after=2),
               P(desc, size=9.6, color=GREY, leading=14.5, after=3),
               P(ref, size=8.8, color=GOLD)]
    card = Table([[badgecell, content]], colWidths=[1.25*cm, CW-1.25*cm])
    card.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),badge), ('BACKGROUND',(1,0),(1,0),PAPER),
        ('VALIGN',(0,0),(0,0),'MIDDLE'), ('VALIGN',(1,0),(1,0),'MIDDLE'),
        ('BOX',(1,0),(1,0),0.6,SAND),
        ('LEFTPADDING',(1,0),(1,0),13),('RIGHTPADDING',(1,0),(1,0),12),
        ('TOPPADDING',(1,0),(1,0),9),('BOTTOMPADDING',(1,0),(1,0),9),
    ]))
    story += [KeepTogether([card])]
    if i < len(stages)-1:
        story += [Spacer(1,1), P('▼', size=8.5, color=GOLD, align=TA_LEFT, before=1, after=1), Spacer(1,1)]

story += [PageBreak()]

# ===== 암송노트 =====
story += [section('② 중요성구 암송노트', 'SCRIPTURE MEMORY NOTE · 손으로 쓰며 마음에 새기기'), Spacer(1,4)]
story += [P('아래 구절을 성경에서 찾아 <b>직접 손으로 써 보세요.</b> 쓰는 동안 말씀이 마음에 새겨집니다. '
            '다 외우면 □ 칸에 표시하세요.', size=9.5, color=GREY, leading=14.5)]
story += [Spacer(1,9)]

def dline():
    t = Table([['']], colWidths=[CW-0.6*cm], rowHeights=[0.62*cm])
    t.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,-1),0.6,LINEC,None,(1,2))]))
    return t

themes = [
    ('재림과 산 소망', [
        ('살전 4:16-17','휴거의 핵심 장면 — 우리의 산 소망'),
        ('요 14:1-3','“너희를 위하여 처소를 예비하러 간다”는 약속'),
        ('계 22:20','“내가 진실로 속히 오리라” — 성경의 마지막 약속'),
    ]),
    ('깨어 준비하라', [
        ('마 24:42-44','그 날과 그 때를 모르니 늘 깨어 있으라'),
        ('마 25:13','열 처녀 비유가 주는 결론'),
    ]),
    ('천년왕국과 그리스도의 통치', [
        ('계 20:6','첫째 부활에 참여하는 자의 복'),
        ('사 11:9','여호와를 아는 지식이 충만한 평화의 나라'),
    ]),
    ('부활과 심판', [
        ('고전 15:51-52','마지막 나팔에 홀연히 변화되리라'),
        ('고후 5:10','우리가 다 그리스도의 심판대 앞에 서리라'),
    ]),
    ('영원한 나라와 구원의 확신', [
        ('계 21:3-4','다시는 사망도 눈물도 없는 하나님의 나라'),
        ('요 3:16','믿는 자에게 주시는 영생의 약속'),
        ('롬 10:9-10','입으로 시인하고 마음으로 믿어 얻는 구원'),
    ]),
]
for tname, verses in themes:
    head = Table([[P('◆  '+tname, size=11, color=INK)]], colWidths=[CW])
    head.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),SAND),
                              ('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),5),
                              ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    block = [head, Spacer(1,5)]
    for ref, note in verses:
        line = Table([[P('<b><font color="#b8923f">'+ref+'</font></b>  <font color="#5a6275" size="9">— '+note+'</font>', size=10.5),
                       P('□ 암송', size=9, color=GREY, align=TA_CENTER)]],
                     colWidths=[CW-2.2*cm, 2.2*cm])
        line.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(0,0),2),
                                  ('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        block += [line, dline(), Spacer(1,9)]
    story += [KeepTogether(block)]
    story += [Spacer(1,4)]

# ===== 푸터 안내 =====
story += [Spacer(1,6)]
foot = Table([[P('이 자료가 도움이 되셨나요? <b>강의실에서 더 깊은 강의·노트·진단평가</b>로 이어서 공부해 보세요. '
                 '함께 말씀으로 시대를 분별하는 길에 초대합니다.', size=9.6, color=INK, leading=15)]], colWidths=[CW])
foot.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LGOLD),('BOX',(0,0),(-1,-1),0.7,GOLD),
                          ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                          ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
story += [foot, Spacer(1,8)]
story += [P('© BIBLY 바이블 인사이트 · 대표강사 오광일   |   본 자료는 「천년왕국 세미나」의 관점을 따른 학습용 요약입니다.   |   insight.josephoh1611.workers.dev',
            size=7.8, color=GREY, align=TA_CENTER)]

doc.build(story)
print('OK ->', OUT, '·', round(os.path.getsize(OUT)/1024,1), 'KB')
