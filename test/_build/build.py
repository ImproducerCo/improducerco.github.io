#!/usr/bin/env python3
"""Прототип пути клиента improducer на improducer.co/test/.

    python3 test/_build/build.py          # из корня сайта: пересобрать все страницы test/

Раскладка и логика экранов взяты у пути клиента Claude (разбор — папка работы
~/Desktop/improducer/работа/2026-10-16_claude/), вид — только дизайн-система improducer
(_design/: tokens.css, components.css, шрифты, знак). Тексты свои. Примеры — выдуманный
автор «Тест». Формы ничего не отправляют, настоящих входа, OAuth и оплаты нет.

Папка _build GitHub Pages не публикует (Jekyll пропускает папки с «_»): здесь исходник,
снаружи — собранные test/<путь>/index.html и test/assets/.
"""

import html
import json
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST = HERE.parent
DESIGN = Path(os.environ.get("IMPRODUCER_DESIGN",
                             Path.home() / "Desktop/improducer/code/y-basic/_design"))
SCORES = HERE / "scores.json"
E = html.escape

STATE_LABEL = {"full": "Заполнено", "empty": "Пусто", "loading": "Загрузка", "error": "Ошибка",
               "denied": "Нет доступа", "long": "Длинный текст", "booked": "Записан на разговор",
               "saved": "Сохранено", "confirm": "Подтверждение", "near": "Близко к сроку"}
ALL6 = ["full", "empty", "loading", "error", "denied", "long"]

PAGES = {}  # путь → html


def copy_assets():
    """Дизайн-система — копией из _design/ (правда там), раскладка прототипа — из _build/."""
    out = TEST / "assets"
    (out / "fonts").mkdir(parents=True, exist_ok=True)
    (out / "logo").mkdir(parents=True, exist_ok=True)
    for name in ("tokens.css", "components.css"):
        shutil.copy2(DESIGN / name, out / name)
    for f in (DESIGN / "fonts").iterdir():
        if f.suffix in (".woff2", ".txt"):
            shutil.copy2(f, out / "fonts" / f.name)
    for name in ("mark.svg", "favicon.svg", "google-g.svg"):
        shutil.copy2(DESIGN / "logo" / name, out / "logo" / name)
    for name in ("test.css", "test.js"):
        shutil.copy2(HERE / name, out / name)


# ── Общие куски ─────────────────────────────────────────────────────────────

def head(title, desc):
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{E(title)} — прототип improducer</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#F9FAFC">
<link rel="icon" href="/test/assets/logo/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/test/assets/tokens.css">
<link rel="stylesheet" href="/test/assets/components.css">
<link rel="stylesheet" href="/test/assets/test.css">
</head>
"""


def wordmark(href="/test/", small=False, co=True):
    cls = "wordmark wordmark--sm" if small else "wordmark"
    suffix = '<span class="co">.co</span>' if co else ""
    return f'<a class="{cls}" href="{href}"><span>improducer{suffix}</span></a>'


def proto(states):
    links = "".join(f'<a href="#s={s}" data-s="{s}">{STATE_LABEL[s]}</a>' for s in states) if len(states) > 1 else ""
    first = '<p class="pi">Состояние экрана</p>' if links else ""
    return (f'<details class="proto"><summary><span class="badge badge--wait">Прототип · <b>{STATE_LABEL[states[0]]}</b>'
            f'</span></summary><div class="pop">{first}{links}{"<hr>" if links else ""}'
            '<a href="/test/opis/">Опись и инструкция</a></div></details>')


def st(key, body, tag="div", cls=""):
    """Блок одного или нескольких состояний (`key` — через пробел)."""
    hidden = "" if "full" in key.split() else " hidden"
    c = f' class="{cls}"' if cls else ""
    return f'<{tag} data-st="{key}"{c}{hidden}>{body}</{tag}>'


def skel(lines=4, box=False):
    parts = ['<span class="skel h"></span>']
    for i in range(lines):
        parts.append('<span class="skel {}"></span>'.format(["w", "", "s", "w"][i % 4]))
    if box:
        parts.append('<span class="skel box"></span>')
    return '<div aria-busy="true" aria-label="Загрузка">' + "".join(parts) + "</div>"


def warn(title, text, btn=None):
    b = f'<div class="btn-row mt-s">{btn}</div>' if btn else ""
    return f'<div class="call warn" role="alert"><h4>{E(title)}</h4><p>{text}</p>{b}</div>'


def note(title, text, btn=None):
    b = f'<div class="btn-row mt-s">{btn}</div>' if btn else ""
    return f'<div class="call"><h4>{E(title)}</h4><p>{text}</p>{b}</div>'


def empty(what, when):
    return f'<div class="empty"><b>{what}</b><br>Заполнится, когда {when}.</div>'


def a_btn(href, text, primary=False, extra=""):
    cls = "btn btn--primary" if primary else "btn"
    return f'<a class="{cls}" href="{href}"{extra}>{text}</a>'


def gbtn(href, text="Продолжить с Google"):
    return f'<a class="gbtn" href="{href}"><img src="/test/assets/logo/google-g.svg" alt="">{text}</a>'


def stage(code, text="появится"):
    return f'<span class="badge badge--wait">{text} · {code}</span>'


def have(text="есть сейчас"):
    return f'<span class="badge badge--ok">{text}</span>'


PAUSED_CALL = warn("Пауза: только чтение",
                   "Срок оплаты прошёл. Всё на месте и ничего не стирается — смотреть можно всё. "
                   "Новые шаги, решения и разбор роликов вернутся после продления.",
                   a_btn("/test/upgrade/", "Продлить", True))


# ── Сайт ────────────────────────────────────────────────────────────────────

SITE_NAV = [("/test/product/", "Как устроено"), ("/test/pricing/", "Форматы"),
            ("/test/download/", "В своём Claude"), ("/test/help/", "Помощь")]


def site_page(path, title, desc, body, states=("full",), crumb=None):
    nav = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{t}</a></li>'
                  for h, t in SITE_NAV)
    menu = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{t}</a>' for h, t in SITE_NAV)
    crumbbar = ""
    if crumb:
        crumbbar = (f'<div class="crumbbar"><div class="in"><span class="meta">{E(crumb)}</span>'
                    '<a class="meta" href="/test/help/">Вопросы →</a></div></div>')
    PAGES[path] = (head(title, desc) + '<body class="site">'
                   f'<header class="site-head"><div class="in">{wordmark()}'
                   f'<ul class="site-nav">{nav}</ul>'
                   '<div class="site-cta">'
                   '<a class="btn hide-m" href="/test/login/">Войти</a>'
                   '<a class="btn btn--primary hide-s" href="/test/login/">Записаться на разговор</a></div>'
                   '<details class="site-menu"><summary class="btn">Меню</summary>'
                   f'<div class="pop"><a class="hide-wide" href="/test/login/"><b>Записаться на разговор</b></a>{menu}<hr><a href="/test/login/">Войти</a></div></details>'
                   f'</div></header>{crumbbar}'
                   f'<main class="wrap">{body}</main>'
                   '<footer class="wrap"><div class="foot"><span>improducer.co</span>'
                   '<a href="/privacy.html">Политика конфиденциальности</a>'
                   '<a href="/terms.html">Условия использования</a>'
                   '<a href="/test/help/">Помощь</a>'
                   '<span>Прототип: формы ничего не отправляют</span></div></footer>'
                   f'{proto(list(states))}<script src="/test/assets/test.js"></script></body></html>\n')


def bare_page(path, title, desc, body, states=("full",)):
    PAGES[path] = (head(title, desc) + '<body class="site">'
                   f'<header class="bare-head">{wordmark()}</header>'
                   f'<main>{body}</main>{proto(list(states))}'
                   '<script src="/test/assets/test.js"></script></body></html>\n')


# ── Приложение (my.) ────────────────────────────────────────────────────────

APP_NAV = [("/test/new/", "Ваш путь", ""), ("/test/chat/", "Чат", "Э4-2"),
           ("/test/recents/", "Решения и события", ""), ("/test/projects/", "Каналы", "")]
SECTIONS = [("anketa", "Анкета"), ("dna", "ДНК"), ("niche", "Ниша"), ("concept", "Концепция"),
            ("board", "Доска идей"), ("plan", "Контент-план"), ("scripts", "Сценарии"),
            ("analytics", "Канал и аналитика")]
ACCOUNT_MENU = [("/test/settings/general/", "Настройки"), ("/test/settings/billing/", "План и оплата"),
                ("/test/help/", "Помощь")]


def section_href(key):
    return "/test/project/test/koncepciya/" if key == "concept" else f"/test/project/test/#{key}"


def app_page(path, title, desc, body, states=("full",), wide=False, active=None):
    active = active or path
    nav = "".join(
        f'<li><a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{t}'
        f'{f" <span class=\"badge badge--wait\">{s}</span>" if s else ""}</a></li>' for h, t, s in APP_NAV)
    secs = "".join(f'<li><a href="{section_href(k)}"'
                   f'{" aria-current=\"page\"" if section_href(k) == active else ""}>{t}</a></li>'
                   for k, t in SECTIONS)
    acct_links = "".join(f'<a href="{h}">{t}</a>' for h, t in ACCOUNT_MENU)
    menu = ("".join(f'<a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{t}</a>' for h, t, _ in APP_NAV)
            + '<hr><p class="pi">Канал «Тест»</p>'
            + "".join(f'<a href="{section_href(k)}">{t}</a>' for k, t in SECTIONS)
            + "<hr>" + acct_links + '<a href="/test/logout/">Выйти</a>')
    PAGES[path] = (head(title, desc) + "<body>"
                   '<div class="app"><aside class="side">'
                   f'<div class="side-top">{wordmark("/test/new/", small=True, co=False)}'
                   '<details class="side-menu"><summary class="btn">Меню</summary>'
                   f'<div class="pop">{menu}</div></details></div>'
                   '<div class="side-nav stack-s">'
                   '<a class="btn btn--primary" href="/test/project/test/koncepciya/">Ваш шаг: концепция</a>'
                   f'<ul class="cnav cnav--side">{nav}</ul>'
                   f'<p class="side-k">Канал «Тест»</p><ul class="cnav cnav--side">{secs}</ul></div>'
                   '<div class="side-foot"><details class="acct"><summary><span class="ava">Т</span>'
                   '<span class="who"><b>Тест</b><span class="meta">Пилот «вместе»</span></span></summary>'
                   f'<div class="pop"><p class="pi">test@example.com</p>{acct_links}<hr>'
                   '<a href="/test/logout/">Выйти</a></div></details></div>'
                   '</aside>'
                   f'<main class="main"><div class="{"main-wide" if wide else "main-in"}">{body}</div></main></div>'
                   f'{proto(list(states))}<script src="/test/assets/test.js"></script></body></html>\n')


# ── Данные «Теста» ──────────────────────────────────────────────────────────

STEPS = [  # заголовки и «что / зачем» — из AI OS Basic/author_steps.json
    ("channel", "Подключить канал", "done"),
    ("anketa", "Анкета", "done"),
    ("photos", "Фото для обложек", "done"),
    ("dna", "ДНК", "done"),
    ("niche", "Ниша и каналы-доноры", "done"),
    ("concept", "Концепция канала", "now"),
    ("board", "Доска идей", "wait"),
    ("plan", "Контент-план", "wait"),
    ("scripts", "Сценарии и упаковка", "wait"),
    ("covers", "Обложки", "wait"),
    ("release", "Выпуск", "wait"),
    ("analytics", "Аналитика вышедших роликов", "wait"),
]
STEP_BADGE = {"done": '<span class="badge badge--ok">готово</span>',
              "now": '<span class="badge badge--wait">ваше решение</span>',
              "wait": '<span class="badge">ждёт</span>'}
LONG = ("Очень длинное название, которое не помещается в одну строку и проверяет перенос на телефоне "
        "и в узкой колонке без обрезки и наложения")


def steps_html(first_day=False, long=False, limit=None, two=False):
    items = []
    for i, (key, title, state) in enumerate(STEPS[:limit] if limit else STEPS, 1):
        if first_day:
            state = "now" if i == 1 else "wait"
        t = f"{title} — {LONG}" if long and i == 6 else title
        href = section_href(key) if key in dict(SECTIONS) or key == "concept" else "/test/project/test/"
        cls = ' class="now"' if state == "now" else ""
        items.append(f'<li{cls}><span class="n">{i:02d}</span><a class="t" href="{href}">{E(t)}</a>{STEP_BADGE[state]}</li>')
    return f'<ol class="steps{" steps-2" if two else ""}">{"".join(items)}</ol>'


def composer(off=False, text="", placeholder=None):
    ph = placeholder or "Спросите о своём канале…"
    dis = " disabled" if off else ""
    cls = " is-off" if off else ""
    return (f'<div class="composer{cls}"><label class="visually-hidden" for="q">Сообщение</label>'
            f'<textarea id="q" rows="2" placeholder="{E(ph)}" data-next="/test/chat/"{dis}>{E(text)}</textarea>'
            '<div class="tools"><a class="btn btn--ghost" href="/test/project/test/">＋ Материалы</a>'
            '<span class="meta">ваш Claude</span>'
            f'<a class="send" href="/test/chat/" aria-label="Отправить"{" aria-disabled=\"true\"" if off else ""}>'
            '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M10 16V4M4.5 9.5 10 4l5.5 5.5" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a></div></div>')


FORMATS = [  # fmt.* из SPEC/продукт/фронтенд.json; цены не утверждены (Д1, Д7)
    {"key": "fmt.razbor", "tab": "start", "title": "Разбор канала", "sub": "Вход без подключения канала",
     "ticks": ["Числа канала и ниши по открытым данным", "3 решения: что менять первым", "1 разговор"],
     "plus": None, "stage": None},
    {"key": "fmt.dna", "tab": "start", "title": "ДНК и концепция", "sub": "Основа: кто вы и о чём канал",
     "ticks": ["Подключение канала", "ДНК из ваших слов и материалов", "Концепция на ваше решение"],
     "plus": "Всё из разбора, плюс:", "stage": None},
    {"key": "fmt.pilot", "tab": "start", "title": "Пилот «вместе»", "sub": "Основной формат · 4 недели",
     "ticks": ["Путь до 4 сценариев с упаковкой", "3 разговора по ходу", "Разбор аналитики канала"],
     "plus": "Всё из ДНК и концепции, плюс:", "stage": None, "main": True},
    {"key": "fmt.self", "tab": "sub", "title": "Со своим Claude", "sub": "Подписка для тех, у кого есть Claude",
     "ticks": ["Весь путь и цикл в вашем Claude", "Приложение my.improducer.co"],
     "plus": None, "stage": "Э3"},
    {"key": "fmt.allin", "tab": "sub", "title": "Всё включено", "sub": "Подписка без своего Claude",
     "ticks": ["То же, что «со своим Claude»", "Чат в приложении"],
     "plus": None, "stage": "Э4"},
    {"key": "fmt.studio", "tab": "studio", "title": "Студия", "sub": "До 3 каналов",
     "ticks": ["Всё из подписки на каждый канал", "Выбор канала в приложении"],
     "plus": None, "stage": "Э3-4"},
]
FMT_TABS = [("start", "Начать"), ("sub", "Подписка"), ("studio", "Студия")]


def plan_card(f, cta_href="/test/login/", cta="Записаться на разговор"):
    main = " is-main" if f.get("main") else ""
    badge = '<span class="badge badge--accent">основной</span>' if f.get("main") else ""
    later = stage(f["stage"]) if f["stage"] else ""
    plus = f'<p class="small"><b>{f["plus"]}</b></p>' if f["plus"] else ""
    btn = (f'<span class="btn" aria-disabled="true">Появится · {f["stage"]}</span>' if f["stage"]
           else a_btn(cta_href, cta, True))
    ticks = "".join(f'<li{" class=\"later\"" if f["stage"] else ""}>{t}</li>' for t in f["ticks"])
    return (f'<article class="card plan{main}"><div class="sig">{badge}{later}</div>'
            f'<h3 class="pt">{f["title"]}</h3><p class="muted">{f["sub"]}</p>'
            '<p class="pp">цена — после решения</p>'
            f'{btn}<hr class="hr">{plus}<ul class="ticks">{ticks}</ul></article>')


def formats_block(active="start", cta_href="/test/login/", cta="Записаться на разговор"):
    tabs = "".join(f'<li><a href="/test/pricing/#{k}"{" aria-current=\"page\"" if k == active else ""}>{t}</a></li>'
                   for k, t in FMT_TABS)
    cards = "".join(plan_card(f, cta_href, cta) for f in FORMATS if f["tab"] == active)
    return f'<div class="center"><ul class="cnav tabs">{tabs}</ul></div><div class="plans">{cards}</div>'


FAQ_SITE = [
    ("Нужен ли мне свой Claude?",
     "Для пилота — желательно: система работает через ваш Claude, он подключается коннектором за пару минут. "
     "Без своего Claude — подписка «всё включено» с чатом в приложении, она появится на этапе Э4."),
    ("Что система видит на моём канале?",
     "Статистику и данные канала — чтобы готовить отчёты и решения. Правки на канале — названия, описания, "
     "плейлисты — только после вашего «да» и только на вашем канале. Видео, комментарии и субтитры мы не удаляем. "
     "Доступ отзывается в любой момент."),
    ("Сколько стоит?", "Цены ещё не утверждены. На разговоре назовём цену формата числом до оплаты."),
    ("Что будет, если не продлить?",
     "Пауза: только чтение. Всё остаётся на месте и ничего не стирается, новые шаги — после продления."),
    ("Я живу в России — можно?",
     "Сейчас нет: Claude не работает в России, а система работает через Claude. Если вы живёте в другой стране — можно."),
]


def faq(items):
    return '<div class="faq">' + "".join(
        f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in items) + "</div>"


def preview_card():
    """Пример кабинета на сайте: «Ваш путь» выдуманного автора «Тест»."""
    return ('<div class="preview" aria-label="Пример кабинета автора «Тест»">'
            '<p class="meta">Пример · выдуманный автор «Тест»</p>'
            '<div class="card stack">'
            '<div class="inset"><p class="k">Ваш шаг 06 из 12</p><h3>Концепция канала</h3>'
            '<p>Система предлагает, о чём канал, для кого и чем он отличается. Решение за вами.</p></div>'
            f'{steps_html(limit=6)}'
            '<div class="facts"><div class="fact"><span class="k">готово</span><span class="v num">5 из 12</span></div>'
            '<div class="fact"><span class="k">ваших решений</span><span class="v num">1</span></div></div>'
            "</div></div>")


# ── Страницы сайта ──────────────────────────────────────────────────────────

def page_home():
    body = ('<section class="hero"><div class="hero-text">'
            '<h1>Основа канала, который приводит вам клиентов</h1>'
            '<p class="lede">ДНК, ниша на измеренных числах, концепция, план и сценарии — вместе с вами, '
            'за 4 недели. Решения на каждом шаге — ваши.</p>'
            '<div class="card auth">'
            f'{gbtn("/test/login/")}'
            '<div class="or">или</div>'
            f'{a_btn("/test/login/", "Записаться на разговор", True)}'
            '<p class="small muted">Сначала разговор, оплата — после него. Продолжая, вы принимаете '
            '<a href="/terms.html">условия</a> и <a href="/privacy.html">политику</a>.</p></div>'
            f'{a_btn("/test/download/", "Подключить в своём Claude")}'
            f'</div>{preview_card()}</section>'
            '<section class="center mt"><h2>Форматы</h2></section>'
            f'{formats_block()}'
            '<p class="center small muted mt-s">Цены — после решения. Разбор засчитывается в ДНК и пилот.</p>'
            '<section class="center mt"><h2>Вопросы</h2></section>'
            f'{faq(FAQ_SITE)}')
    site_page("/test/", "Главная", "Основа канала, который приводит вам клиентов — прототип пути клиента.", body)


def page_product():
    tiles = [
        ("01", "Неделя 1", "ДНК", "Кто вы, во что верите, что продаёте и чего не делаете — из ваших слов и материалов."),
        ("02", "Неделя 2", "Концепция и план", "О чём канал и для кого, доска идей с вашими отметками, план на 8 роликов."),
        ("03", "Недели 3–4", "Сценарии", "4 сценария с упаковкой: название, описание, бриф обложки."),
        ("04", "Дальше", "Разбор роликов", "Что сработало в вышедших роликах и что поменять. Автору — появится, Э1-13."),
    ]
    tl = "".join(f'<div class="tile"><span class="tn">{n} · {w}</span><span class="tt">{t}</span>'
                 f'<span class="tr">{d}</span></div>' for n, w, t, d in tiles)
    diff = [("Закрытые данные канала", "Статистика по вашему разрешению, ваша речь целиком, измеренная база ниши."),
            ("Числа с источником", "Числа считает сервер, у каждого — откуда оно взято."),
            ("Проверка результата", "Сдачу проверяет код: хук, длина, запреты автора — а не модель о своём тексте."),
            ("Правило по вашим роликам", "Правило канала включается, только когда его подтвердили вышедшие ролики.")]
    df = "".join(f'<div class="card"><h3>{t}</h3><p>{d}</p></div>' for t, d in diff)
    who = [("Вы", "Анкета, фото, решения: концепция, отметки идей, «да» плану и сценариям. Съёмка."),
           ("Ваш Claude", "ДНК, формулировки ниши, концепция, сценарии — через коннектор improducer."),
           ("Система", "Данные канала, все числа, проверка каждой сдачи, разбор роликов, кабинет."),
           ("Человек improducer", "Три разговора в пилоте и страховка там, где функция ещё не готова.")]
    wh = "".join(f'<tr><td><b>{a}</b></td><td>{b}</td></tr>' for a, b in who)
    body = ('<section class="center" style="padding-top:var(--space-64)"><h1>Система, которая собирает основу канала</h1>'
            '<p class="lede">Не доступ к ИИ, а результат: путь из 12 шагов от подключения канала до разбора '
            'вышедших роликов. Решаете вы — система считает и проверяет.</p>'
            f'<div class="btn-row mt-s" style="justify-content:center">{a_btn("/test/login/", "Записаться на разговор", True)}'
            f'{a_btn("/test/pricing/", "Форматы")}</div></section>'
            '<section class="mt"><h2>Что будет по неделям</h2>'
            '<p class="muted">Цель пилота. Сроки проверяются на первых авторах.</p>'
            f'<div class="tiles">{tl}</div></section>'
            f'<section class="mt"><h2>Чем это не промт в чате</h2><div class="grid2">{df}</div></section>'
            '<section class="mt"><h2>Кто что делает</h2><div class="scroll"><table><thead><tr><th>Кто</th>'
            f'<th>Что делает</th></tr></thead><tbody>{wh}</tbody></table></div></section>'
            '<section class="mt"><h2>12 шагов пути</h2>'
            f'{steps_html(two=True)}</section>')
    site_page("/test/product/", "Как устроено", "Как устроена система improducer: 12 шагов пути.", body,
              crumb="Как устроено")


def page_pricing():
    blocks = []
    for k, t in FMT_TABS:
        cards = "".join(plan_card(f) for f in FORMATS if f["tab"] == k)
        tabs = "".join(f'<li><a href="#{kk}"{" aria-current=\"page\"" if kk == k else ""}>{tt}</a></li>'
                       for kk, tt in FMT_TABS)
        blocks.append(f'<div id="{k}" class="fmt-tab"><div class="center"><ul class="cnav tabs">{tabs}</ul></div>'
                      f'<div class="plans">{cards}</div></div>')
    rows = [("Числа канала и ниши", "✓", "✓", "✓", "✓"),
            ("Подключение канала", "—", "✓", "✓", "✓"),
            ("ДНК и концепция", "—", "✓", "✓", "✓"),
            ("Доска идей и план на 8 роликов", "—", "—", "✓", "✓"),
            ("Сценарии с упаковкой", "—", "—", "до 4", "✓"),
            ("Разбор вышедших роликов", "—", "—", "✓", "✓"),
            ("Разговоры", "1", "—", "3", "—"),
            ("Нужен свой Claude", "нет", "нет", "желательно", "да")]

    def cell(v):
        if v == "✓":
            return '<td><span class="badge badge--ok">✓</span></td>'
        if v == "—":
            return '<td><span class="badge">—</span></td>'
        return f'<td>{E(v)}</td>'
    tb = "".join(f'<tr><td>{E(r[0])}</td>{"".join(cell(v) for v in r[1:])}</tr>' for r in rows)
    body = ('<section class="center" style="padding-top:var(--space-48)"><h1>Форматы</h1>'
            '<p class="lede">Одна лестница: разбор засчитывается в ДНК и пилот, ДНК — в пилот. '
            'Цены ещё не утверждены — на разговоре назовём числом до оплаты.</p></section>'
            f'<div class="mt-s fmt-tabs">{"".join(blocks)}</div>'
            '<p class="center small muted mt-s">Тариф — за канал в месяц, услуга — за результат. '
            'За сообщения и токены не берём.</p>'
            '<section class="mt"><h2>Что входит</h2><div class="scroll"><table><thead><tr><th>Что</th>'
            '<th>Разбор</th><th>ДНК и концепция</th><th>Пилот</th><th>Подписка · Э3</th></tr></thead>'
            f'<tbody>{tb}</tbody></table></div></section>'
            '<section class="center mt"><h2>Вопросы</h2></section>'
            f'{faq(FAQ_SITE[2:])}'
            # Вкладки — якорями, без скрипта: видна первая или та, на которую ведёт #якорь.
            '<style>.fmt-tabs:not(:has(.fmt-tab:target)) .fmt-tab:not(:first-child),'
            '.fmt-tab:target~.fmt-tab,.fmt-tab:has(~.fmt-tab:target){display:none}</style>')
    site_page("/test/pricing/", "Форматы", "Форматы работы с improducer: разбор, ДНК и концепция, пилот.", body,
              crumb="Форматы")


def page_download():
    rows = [("Claude в браузере", "claude.ai — Настройки → Коннекторы → Добавить свой коннектор"),
            ("Claude для Mac и Windows", "то же в приложении: подключение общее с браузером"),
            ("Claude на телефоне", "тот же аккаунт Claude: подключённый коннектор виден и там")]
    rr = "".join(f'<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">{t}</p>'
                 f'<p class="rmeta">{d}</p></div>{a_btn("/test/settings/connectors/", "Подключить")}</div></div>'
                 for t, d in rows)
    steps = ("<ol class=\"stack-s\"><li>В кабинете — «Подключения» → «Получить код подключения».</li>"
             "<li>В Claude: <b>Настройки → Коннекторы → Добавить свой коннектор</b>. Название — "
             "<b>improducer</b>, адрес — <code>https://connect.improducer.co/mcp</code>.</li>"
             "<li>«Подключить» → введите код. Код одноразовый, действует сутки.</li>"
             "<li>Новый чат: «improducer, что дальше?» — Claude откроет вашу систему.</li></ol>")
    body = ('<section class="center" style="padding-top:var(--space-48)"><h1>improducer в вашем Claude</h1>'
            '<p class="lede">Работайте с системой словами в своём Claude: темы, сценарии, план, решения.</p>'
            f'<div class="btn-row mt-s" style="justify-content:center">'
            f'{a_btn("/test/settings/connectors/", "Подключить коннектор", True)}</div></section>'
            '<section class="mt split"><div><h2>Где работает</h2>'
            '<p class="muted">Подключаете один раз — работает везде, где вы входите в свой Claude.</p></div>'
            f'<div class="card"><h3>Ваш Claude</h3>{rr}</div></section>'
            f'<section class="mt split"><div><h2>Как подключить</h2><p class="muted">Две минуты.</p></div>'
            f'<div class="card">{steps}</div></section>'
            '<section class="mt split"><div><h2>Без своего Claude</h2></div>'
            '<div class="card"><h3>Чат в приложении</h3><p>Подписка «всё включено» с чатом прямо в '
            f'my.improducer.co.</p><div class="sig">{stage("Э4-2")}</div></div></section>'
            '<section class="center mt"><h2>Вопросы</h2></section>'
            + faq([("Какой нужен тариф Claude?",
                    "Свои коннекторы работают на платных тарифах Claude. Лимит сообщений — ваш, в вашем Claude."),
                   ("Где взять код подключения?", "В кабинете: «Подключения» → «Получить код подключения»."),
                   ("Claude спрашивает разрешение на каждый вопрос",
                    "В настройках коннектора, «Разрешения инструментов», поставьте «Разрешать всегда» на обе группы.")]))
    site_page("/test/download/", "В своём Claude", "Подключить improducer в своём Claude.", body,
              crumb="В своём Claude")


HELP_TOPICS = [("Начало", "Вход, разговор, первый запуск"), ("Канал и доступ", "Что видит система, как отозвать"),
               ("Ваш Claude", "Коннектор, код, разрешения"), ("Оплата и пауза", "Форматы, продление, только чтение"),
               ("Данные", "Что хранится, удаление по просьбе")]


def page_help():
    pop = [("С чего начать", "/test/help/start/"), ("Как подключить свой Claude", "/test/download/"),
           ("Что будет, если не продлить", "/test/paused/"), ("Что система видит на канале", "/test/settings/privacy/")]
    pl = "".join(f'<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">'
                 f'<a href="{h}">{t}</a></p></div></div></div>' for t, h in pop)
    tl = "".join(f'<a class="tile" href="/test/help/start/"><span class="tt">{t}</span><span class="tr">{d}</span>'
                 '<span class="tgo">Открыть →</span></a>' for t, d in HELP_TOPICS)
    search = ('<div class="field"><label for="hs">Поиск по вопросам</label>'
              '<input id="hs" type="search" placeholder="Например: пауза" data-next="/test/help/#s=empty"></div>')
    body = ('<section style="padding-top:var(--space-48)"><h1>Помощь</h1>'
            f'<div class="mt-s" style="max-width:var(--container-single)">{search}</div></section>'
            + st("full long", f'<section class="mt"><h2>Частые вопросы</h2>{pl}</section>'
                 f'<section class="mt"><h2>Разделы</h2><div class="tiles">{tl}</div></section>')
            + st("empty", '<section class="mt">' + empty("По запросу «пауза» ничего не нашлось.",
                                                          "в помощи появится статья об этом; пока — раздел «Оплата и пауза»")
                 + "</section>")
            + st("loading", '<section class="mt">' + skel(4, True) + "</section>"))
    site_page("/test/help/", "Помощь", "Помощь по improducer.", body, states=("full", "empty", "loading"))


def page_help_start():
    body = ('<article class="main-in" style="padding-top:var(--space-40)">'
            '<p class="crumb"><a href="/test/help/">Помощь</a> / Начало</p><h1>С чего начать</h1>'
            '<p class="lede">Пять шагов от сайта до первой работы.</p>'
            '<h2 class="mt">1. Войдите</h2><p>Вход — только Google. Пароля и входа по почте нет.</p>'
            '<h2>2. Разговор</h2><p>Выберите время. На разговоре — цель канала и формат, цена числом.</p>'
            '<h2>3. Оплата</h2><p>Ссылка на оплату приходит после разговора: картой или в USDT. '
            'Доступ включаем вручную в тот же день; автоматически — появится, Э3-2.</p>'
            '<h2>4. Анкета и канал</h2><p>Анкета — одна ссылка, <code>my.improducer.co/anketa</code>. '
            'Канал подключается входом Google на connect.improducer.co.</p>'
            '<h2>5. Ваш путь</h2><p>В кабинете — «Ваш путь»: один шаг на экране и решение кнопкой. '
            'Работать словами — в своём Claude.</p>'
            + note("Не нашли ответ", "Напишите на founder@improducer.co.")
            + '<div class="marks" style="border:0;padding-inline:0"><span class="small muted">Статья помогла?</span>'
            '<button class="mbtn" type="button">Да</button><button class="mbtn" type="button">Нет</button></div>'
            "</article>")
    site_page("/test/help/start/", "С чего начать", "С чего начать работу с improducer.", body)


# ── Вход и первый запуск ─────────────────────────────────────────────────────

def page_login():
    form = ('<div class="card auth">'
            + st("full long", gbtn("/test/login/check/"))
            + st("loading", '<span class="gbtn" aria-busy="true">Открываем Google…</span>')
            + st("error", warn("Google не подтвердил вход",
                               "Окно Google закрыли или вход отменён. Попробуйте ещё раз.") + gbtn("/test/login/check/"))
            + st("denied", note("Вход по приглашению",
                                "Вход для авторов откроется — Э3-5. Сейчас — лист ожидания и разговор.",
                                a_btn("/test/login/check/#s=full", "Встать в лист ожидания", True)))
            + '<p class="small muted">Входа по почте и паролю нет — только Google. Продолжая, вы принимаете '
            '<a href="/terms.html">условия</a> и <a href="/privacy.html">политику</a>.</p></div>')
    h1 = st("full loading error denied", "<h1>Вход в improducer</h1>") + st("long", f"<h1>Вход в improducer — {LONG}</h1>")
    body = ('<div class="login"><div class="hero-text">'
            f'{h1}<p class="lede">Ваш путь, решения и материалы канала — в одном кабинете.</p>{form}'
            f'{a_btn("/test/download/", "Подключить в своём Claude")}</div>{preview_card()}</div>')
    bare_page("/test/login/", "Вход", "Вход в кабинет improducer через Google.", body,
              states=("full", "loading", "error", "denied", "long"))


SLOTS = ["чт · 10:00", "чт · 15:00", "пт · 11:00", "пн · 10:00"]


def page_login_check():
    slots = "".join(f'<label class="switch"><input type="radio" name="slot"{" checked" if i == 0 else ""}> {s}</label>'
                    for i, s in enumerate(SLOTS))
    body = ('<div class="centered"><div class="box">'
            + st("full", '<div class="card stack"><p class="meta">Вошли как test@example.com</p>'
                 '<h1 class="screen-title">Выберите время разговора</h1>'
                 '<p>Вход открыт по разговору: 30 минут о канале и цели, формат и цена числом. '
                 'Оплата — после разговора.</p>'
                 f'<div class="stack-s">{slots}</div><p class="small muted">Время — по вашему часовому поясу.</p>'
                 f'{a_btn("#s=booked", "Записаться", True)}</div>')
            + st("booked", '<div class="card stack"><span class="badge badge--ok">записаны</span>'
                 '<h1 class="screen-title">Разговор в четверг, 10:00</h1>'
                 '<p>Напоминание придёт на почту. После разговора здесь появится ссылка на оплату.</p>'
                 f'{note("После разговора", "Ссылка на оплату выбранного формата.", a_btn("/test/upgrade/", "Перейти к оплате", True))}'
                 '</div>')
            + st("loading", '<div class="card stack">' + skel(3) + "</div>")
            + st("error", '<div class="card stack">' + warn(
                "Вход не завершён", "Google вернул отказ: доступ к адресу почты не дан. Без него войти нельзя.",
                gbtn("/test/login/check/", "Войти ещё раз")) + "</div>")
            + st("denied", '<div class="card stack"><h1 class="screen-title">Мы не можем открыть систему</h1>'
                 '<p>Система работает через Claude, а Claude недоступен в стране, указанной в аккаунте. '
                 'Если вы живёте в другой стране — напишите на founder@improducer.co.</p></div>')
            + "</div></div>")
    bare_page("/test/login/check/", "Проверка входа", "Возврат из Google: лист ожидания и запись на разговор.",
              body, states=("full", "booked", "loading", "error", "denied"))


def onboarding_shell(path, n, title, body_full, nxt, prev=None, states=("full", "loading", "error")):
    pager = (f'<nav class="pager">{f"<a href=\"{prev}\">← Назад</a>" if prev else ""}'
             f'<span class="pos">{n:02d} / 03</span></nav>')
    body = ('<div class="centered"><div class="box"><div class="card stack">'
            + pager
            + st("full long", f'<h1 class="screen-title">{title}</h1>{body_full}'
                 f'<div class="btn-row">{a_btn(nxt, "Дальше", True)}</div>')
            + st("loading", skel(3))
            + st("error", warn("Не сохранилось", "Проверьте связь и нажмите «Дальше» ещё раз.",
                               a_btn(nxt, "Дальше", True)))
            + "</div></div></div>")
    bare_page(path, title, "Первый запуск в кабинете improducer.", body, states=states)


def page_onboarding():
    onboarding_shell(
        "/test/onboarding/", 1, "Как к вам обращаться",
        '<div class="field"><label for="nm">Имя</label><input id="nm" value="Тест" data-next="/test/onboarding/anketa/">'
        '<p class="hint">Так система будет обращаться к вам в кабинете и в письмах.</p></div>'
        '<label class="switch"><input type="checkbox" checked> Принимаю <a href="/terms.html">условия</a> и '
        '<a href="/privacy.html">политику</a></label>',
        "/test/onboarding/anketa/")
    onboarding_shell(
        "/test/onboarding/anketa/", 2, "Анкета",
        '<p>Минимум анкеты — о чём канал, для кого, цель, как снимаете, границы, куда звать зрителя — и ваши '
        'площадки. Видео, страницы сайта и посты система соберёт сама.</p>'
        '<p class="small muted">Анкета живёт по одной ссылке: <code>my.improducer.co/anketa</code>. '
        'Там же — 6 фото для обложек.</p>'
        '<div class="facts" style="margin-top:0"><div class="fact"><span class="k">заполнено</span>'
        '<span class="v num">6 из 6</span></div><div class="fact"><span class="k">фото</span><span class="v num">8</span></div></div>',
        "/test/onboarding/kanal/", prev="/test/onboarding/")
    onboarding_shell(
        "/test/onboarding/kanal/", 3, "Подключите канал",
        '<p>Войдите Google-аккаунтом своего канала и оставьте отмеченными все разрешения. По статистике система '
        'видит, что у вас уже работает; правки на канале — только после вашего «да».</p>'
        f'{gbtn("/test/connect/", "Подключить канал через Google")}',
        "/test/connect/", prev="/test/onboarding/anketa/")


def page_connect():
    scopes = ('<ul class="ticks"><li><b>Статистика и данные канала</b> — чтобы готовить отчёты и решения по контенту.</li>'
              '<li><b>Правки на канале</b> — названия, описания и теги, плейлисты, шапка, загрузка готовых роликов. '
              'Каждую правку система сначала показывает «было → станет» и вносит только после вашего «да».</li></ul>')
    body = ('<div class="centered"><div class="box"><div class="card stack">'
            '<p class="meta">connect.improducer.co</p>'
            + st("full long", '<h1 class="screen-title">Доступ к каналу «Тест»</h1>'
                 f'<p>Google попросит одно согласие на всё, что нужно системе:</p>{scopes}'
                 '<p class="small muted">Видео, комментарии и субтитры мы не удаляем. Доступ отзывается в любой момент.</p>'
                 f'<div class="btn-row">{a_btn("/test/new/", "Разрешить", True)}{a_btn("/test/onboarding/kanal/", "Не сейчас")}</div>')
            + st("loading", skel(4))
            + st("error", warn("Не все разрешения отмечены",
                               "Без статистики система не видит, что у вас работает. Подключите ещё раз и оставьте "
                               "отмеченными все галочки.", gbtn("/test/connect/", "Подключить ещё раз")))
            + st("denied", warn("Канал уже подключён к другому аккаунту",
                                "Войдите тем аккаунтом Google, которым подключали канал, или напишите на founder@improducer.co."))
            + "</div></div></div>")
    bare_page("/test/connect/", "Подключение канала", "Подключение YouTube-канала: какие права и зачем.", body,
              states=("full", "loading", "error", "denied", "long"))


# ── Работа в приложении ─────────────────────────────────────────────────────

def page_new():
    step = ('<div class="inset"><p class="k">Ваш шаг 06 из 12</p><h3>Концепция канала</h3>'
            '<p>Система предлагает, о чём канал, для кого и чем он отличается. Зачем: от решения по концепции '
            'зависят все темы.</p>'
            f'<div class="btn-row">{a_btn("/test/project/test/koncepciya/", "Открыть концепцию →", True)}</div></div>')
    chips = ('<div class="chips"><a href="/test/chat/">Что дальше?</a><a href="/test/chat/">Покажи концепцию</a>'
             '<a href="/test/chat/">Разбери последний ролик</a></div>')
    hint = ('<p class="small muted">Чат здесь появится — Э4-2. Сейчас то же самое — в вашем Claude: '
            '«improducer, что дальше?»</p>')
    body = ('<div class="greet">'
            + st("full", f'<h1>Тест, решение за вами</h1>{step}{composer()}{chips}{hint}')
            + st("long", f'<h1>Тест, решение за вами</h1><div class="inset"><p class="k">Ваш шаг 06 из 12</p>'
                 f'<h3>Концепция канала — {LONG}</h3><p>{LONG}. {LONG}.</p></div>{composer(text=LONG)}{chips}')
            + st("empty", '<h1>Тест, начнём с канала</h1><div class="inset"><p class="k">Ваш шаг 01 из 12</p>'
                 '<h3>Подключить канал</h3><p>Войти Google-аккаунтом своего канала. Зачем: по статистике система '
                 'видит, что у вас уже работает.</p>'
                 f'<div class="btn-row">{a_btn("/test/connect/", "Подключить канал", True)}</div></div>{composer(off=True, placeholder="Чат откроется после подключения канала")}')
            + st("loading", '<div style="width:100%">' + skel(3, True) + "</div>")
            + st("error", '<h1>Тест, путь не загрузился</h1>' + warn(
                "Не удалось загрузить путь", "Сервер не ответил. Данные на месте — обновите страницу через минуту.",
                a_btn("/test/new/", "Обновить", True)))
            + st("denied", f'<h1>Тест, ваш путь на паузе</h1>{PAUSED_CALL}{composer(off=True, placeholder="Пауза: только чтение")}')
            + "</div>"
            '<section><h2>Ваш путь</h2>'
            + st("full denied loading error", '<p class="small muted">Готово 5 из 12</p>' + steps_html())
            + st("long", '<p class="small muted">Готово 5 из 12</p>' + steps_html(long=True))
            + st("empty", '<p class="small muted">Готово 0 из 12</p>' + steps_html(first_day=True))
            + "</section>")
    app_page("/test/new/", "Ваш путь", "«Ваш путь»: где автор сейчас и что решить.", body, states=ALL6)


CONCEPT_DOC = ('<h3>Концепция канала «Тест» · вариант 2</h3>'
               '<p><b>О чём.</b> Разборы реальных задач из практики автора: один случай — один ролик, с числами.</p>'
               '<p><b>Для кого.</b> Специалисты в начале пути, которые ищут, как работают опытные коллеги.</p>'
               '<p><b>Чем отличается.</b> Не теория, а разобранный случай: что было, что сделали, что вышло.</p>'
               '<p class="small muted">Пример на выдуманном авторе «Тест».</p>')


def page_chat():
    thread_ready = ('<div class="thread">'
                    '<div class="msg-u">Что дальше по каналу?</div>'
                    '<div class="msg-a"><p>Сейчас ваш шаг — концепция канала. Система предложила два варианта; '
                    'второй точнее совпадает с вашей анкетой и ДНК.</p><p>Откройте концепцию справа и выберите: '
                    'утвердить, с правками или другой вариант.</p>'
                    '<div class="acts"><a class="btn btn--ghost" href="#s=full">Копировать</a>'
                    '<a class="btn btn--ghost" href="#s=loading">Повторить</a></div></div></div>')
    thread_going = ('<div class="thread"><div class="msg-u">Что дальше по каналу?</div>'
                    '<div class="msg-a"><p>Сейчас ваш шаг — концепция канала. Система предложила</p>'
                    '<span class="typing" aria-label="Ответ идёт"><i></i><i></i><i></i></span></div></div>')
    thread_err = ('<div class="thread"><div class="msg-u">Что дальше по каналу?</div>'
                  + warn("Ответ не пришёл", "Связь прервалась. Сообщение сохранено.",
                         a_btn("#s=full", "Повторить", True)) + "</div>")
    thread_long = ('<div class="thread">' + f'<div class="msg-u">{LONG}</div>'
                   + "".join(f'<div class="msg-a"><p>{LONG}. {LONG}.</p></div>' for _ in range(3)) + "</div>")
    artifact = ('<aside class="card"><div class="panel-h"><b>Концепция канала</b><span class="badge">вариант 2 из 2</span>'
                f'<div class="btn-row">{a_btn("/test/project/test/koncepciya/", "Открыть")}</div></div>{CONCEPT_DOC}</aside>')
    body = ('<div class="page-top"><h1 class="screen-title">Что дальше по каналу</h1>'
            f'{stage("Э4-2", "макет · чат появится")}</div>'
            '<div class="split"><div>'
            + st("full", thread_ready) + st("loading", thread_going) + st("error", thread_err)
            + st("long", thread_long)
            + st("empty", empty("Разговора пока нет.", "вы зададите первый вопрос; подсказки — на «Ваш путь»"))
            + st("denied", PAUSED_CALL)
            + '<div class="dock">'
            + st("full loading error long empty", composer())
            + st("denied", composer(off=True, placeholder="Пауза: только чтение"))
            + "</div></div>"
            + st("full loading long", artifact)
            + st("error empty denied", empty("Здесь откроется результат — концепция, план или сценарий.",
                                             "ответ сошлётся на результат шага"))
            + "</div>")
    app_page("/test/chat/", "Чат", "Макет чата в приложении: раскладка и состояния.", body, states=ALL6, wide=True)


EVENTS = [("сегодня", "Система предложила концепцию, вариант 2", "ждёт решения"),
          ("вчера", "Ниша: изучены 12 каналов и их сильные ролики", "готово"),
          ("3 дня назад", "ДНК собрана из анкеты и 9 ваших роликов", "готово"),
          ("5 дней назад", "Фото для обложек: принято 8", "готово"),
          ("неделю назад", "Анкета заполнена", "готово"),
          ("неделю назад", "Канал «Тест» подключён", "готово")]


def events_html(long=False):
    out = []
    for when, what, state in EVENTS:
        b = '<span class="badge badge--wait">ждёт решения</span>' if state != "готово" else '<span class="badge badge--ok">готово</span>'
        w = f"{what} — {LONG}" if long else what
        out.append(f'<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">'
                   f'<a href="/test/project/test/">{E(w)}</a></p><p class="rmeta">{when}</p></div>{b}</div></div>')
    return "".join(out)


def page_recents():
    search = ('<div class="field"><label class="visually-hidden" for="rs">Поиск</label>'
              '<input id="rs" type="search" placeholder="Поиск по решениям и событиям" data-next="/test/recents/#s=error"></div>')
    body = ('<div class="page-top"><h1>Решения и события</h1></div>'
            f'<div class="stack">{search}'
            + st("full", f'<p class="small muted">6 событий канала «Тест»</p>{events_html()}')
            + st("long", f'<p class="small muted">6 событий</p>{events_html(long=True)}')
            + st("empty", empty("Событий пока нет.", "система сделает первый шаг — подключение канала"))
            + st("loading", skel(2) + skel(2))
            + st("error", empty("По запросу ничего не нашлось.", "такое событие случится; попробуйте другое слово"))
            + st("denied", PAUSED_CALL + events_html())
            + "</div>")
    app_page("/test/recents/", "Решения и события", "Что сделано и что решено по каналу.", body, states=ALL6)


def page_projects():
    card = ('<a class="tile" href="/test/project/test/"><span class="tn">канал</span><span class="tt">{name}</span>'
            '<span class="tr">Шаг 06 из 12 · ждёт вашего решения по концепции</span><span class="tgo">Открыть →</span></a>')
    add = ('<div class="tile"><span class="tn">студия</span><span class="tt">Второй канал</span>'
           f'<span class="tr">До 3 каналов в одном кабинете.</span>{stage("Э3-4")}</div>')
    body = ('<div class="page-top"><h1>Каналы</h1><div class="btn-row">'
            '<span class="btn" aria-disabled="true">＋ Канал · Э3-4</span></div></div>'
            + st("full", f'<div class="tiles">{card.format(name="Тест")}{add}</div>')
            + st("long", f'<div class="tiles">{card.format(name="Тест — " + LONG)}{add}</div>')
            + st("empty", '<div class="tiles">' + empty("Каналов пока нет.", "вы подключите канал через Google")
                 + "</div>" + f'<div class="btn-row mt-s">{a_btn("/test/connect/", "Подключить канал", True)}</div>')
            + st("loading", '<div class="tiles">' + skel(1, True) + skel(1, True) + "</div>")
            + st("error", warn("Список каналов не загрузился", "Обновите страницу через минуту.",
                               a_btn("/test/projects/", "Обновить", True)))
            + st("denied", PAUSED_CALL + f'<div class="tiles">{card.format(name="Тест")}</div>'))
    app_page("/test/projects/", "Каналы", "Каналы автора.", body, states=ALL6, wide=True)


SECTION_TILES = [
    ("anketa", "01", "Анкета", "6 из 6 ответов, 4 площадки", "готово"),
    ("dna", "04", "ДНК", "Кто вы, во что верите, что продаёте", "готово"),
    ("niche", "05", "Ниша", "12 каналов, 40 сильных роликов", "готово"),
    ("concept", "06", "Концепция", "2 варианта, ждёт решения", "ваше решение"),
    ("board", "07", "Доска идей", "", "ждёт"),
    ("plan", "08", "Контент-план", "", "ждёт"),
    ("scripts", "09", "Сценарии", "", "ждёт"),
    ("analytics", "12", "Канал и аналитика", "", "ждёт"),
]
WHEN = {"board": "утверждена концепция", "plan": "отмечены идеи на доске", "scripts": "утверждён план",
        "analytics": "выйдет первый ролик и пройдёт 14 дней"}


def section_tiles(long=False):
    out = []
    for key, n, title, res, state in SECTION_TILES:
        badge = {"готово": "badge--ok", "ваше решение": "badge--wait"}.get(state, "")
        r = res or f"Заполнится, когда {WHEN[key]}."
        if long and key == "concept":
            title = f"{title} — {LONG}"
        out.append(f'<a class="tile" id="{key}" href="{section_href(key)}"><span class="tn">{n}</span>'
                   f'<span class="tt">{E(title)}</span><span class="tr">{E(r)}</span>'
                   f'<span class="badge {badge}">{state}</span><span class="tgo">Открыть →</span></a>')
    return f'<div class="tiles">{"".join(out)}</div>'


def page_project():
    side = ('<aside class="stack"><div class="card"><h3>Концепция одной строкой</h3>'
            '<p class="muted">Заполнится, когда вы утвердите концепцию.</p></div>'
            '<div class="card"><h3>Источники</h3><div class="facts" style="margin-top:0">'
            '<div class="fact"><span class="k">роликов</span><span class="v num">9</span></div>'
            '<div class="fact"><span class="k">площадок</span><span class="v num">4</span></div>'
            '<div class="fact"><span class="k">фото</span><span class="v num">8</span></div></div>'
            f'<div class="btn-row mt-s">{a_btn("/test/onboarding/anketa/", "Анкета")}</div></div></aside>')
    body = ('<p class="crumb"><a href="/test/projects/">Каналы</a> / Тест</p>'
            '<div class="page-top"><h1>Канал «Тест»</h1><div class="btn-row">'
            f'{a_btn("/test/project/test/koncepciya/", "Ваш шаг: концепция", True)}</div></div>'
            '<div class="split-r"><div class="stack">'
            + st("full", section_tiles())
            + st("denied", PAUSED_CALL + section_tiles())
            + st("long", section_tiles(long=True))
            + st("empty", empty("Разделы канала пусты.", "подключён канал и заполнена анкета") + steps_html(first_day=True, limit=3))
            + st("loading", '<div class="tiles">' + skel(1, True) * 3 + "</div>")
            + st("error", warn("Разделы не загрузились", "Обновите страницу через минуту.",
                               a_btn("/test/project/test/", "Обновить", True)))
            + f'{composer()}</div>{side}</div>')
    app_page("/test/project/test/", "Канал «Тест»", "Канал автора: разделы шагов и источники.", body,
             states=ALL6, wide=True, active="/test/projects/")


def page_concept():
    decide = ('<div class="card stack"><h3>Ваше решение</h3>'
              '<p>Концепция задаёт все темы. Выберите — система продолжит с доски идей.</p>'
              '<div class="btn-row btn-row--stack">'
              f'{a_btn("/test/new/#s=full", "Утвердить", True)}{a_btn("#s=confirm", "С правками")}'
              f'{a_btn("#s=loading", "Другой вариант")}</div></div>')
    edits = ('<div class="card stack"><h3>Что поправить</h3><div class="field"><label for="ed">Правки словами</label>'
             '<textarea id="ed">Добавить, что ролики — с разбором ошибок, не только удачных случаев.</textarea></div>'
             f'<div class="btn-row">{a_btn("/test/new/", "Отправить правки", True)}{a_btn("#s=full", "Отмена")}</div></div>')
    left = ('<div class="stack"><p class="lede">Система предложила два варианта. Второй точнее совпадает '
            'с анкетой и ДНК: те же слова о практике и случаях.</p>'
            '<div class="facts" style="margin-top:0"><div class="fact"><span class="k">вариантов</span><span class="v num">2</span></div>'
            '<div class="fact"><span class="k">из ДНК</span><span class="v num">5 опор</span></div>'
            '<div class="fact"><span class="k">ниша</span><span class="v num">12 каналов</span></div></div>')
    body = ('<p class="crumb"><a href="/test/project/test/">Канал «Тест»</a> / Концепция</p>'
            '<div class="page-top"><h1>Концепция канала</h1>'
            '<span class="badge badge--wait">ваше решение</span></div>'
            '<div class="split">'
            + st("full long", left + decide + "</div>")
            + st("confirm", left + edits + "</div>")
            + st("loading", '<div class="stack">' + skel(4) + "</div>")
            + st("error", '<div class="stack">' + warn("Решение не сохранилось",
                                                        "Связь прервалась. Нажмите ещё раз — второй раз не запишется.",
                                                        a_btn("#s=full", "Повторить", True)) + "</div>")
            + st("denied", '<div class="stack">' + PAUSED_CALL + "</div>")
            + st("empty", '<div class="stack">' + empty("Концепции пока нет.", "готовы ДНК и ниша") + "</div>")
            + st("full confirm error denied", f'<article class="card"><div class="panel-h"><b>Концепция</b>'
                 '<span class="badge">вариант 2 из 2</span></div>' + CONCEPT_DOC + "</article>")
            + st("long", '<article class="card"><div class="panel-h"><b>Концепция</b><span class="badge">вариант 2 из 2</span></div>'
                 + CONCEPT_DOC + f"<p>{LONG}. {LONG}. {LONG}.</p></article>")
            + st("loading empty", '<article class="card">' + skel(5) + "</article>")
            + "</div>")
    app_page("/test/project/test/koncepciya/", "Концепция канала", "Результат шага и решение автора.", body,
             states=ALL6 + ["confirm"], wide=True, active="/test/project/test/koncepciya/")


# ── Настройки ───────────────────────────────────────────────────────────────

SET_TABS = [("general", "Профиль"), ("account", "Аккаунт"), ("privacy", "Приватность"),
            ("billing", "План и оплата"), ("usage", "Срок и доступ"), ("capabilities", "Возможности"),
            ("connectors", "Подключения")]


def settings_page(key, title, body, states=("full",)):
    tabs = "".join(f'<li><a href="/test/settings/{k}/"{" aria-current=\"page\"" if k == key else ""}>{t}</a></li>'
                   for k, t in SET_TABS)
    full = (f'<div class="page-top"><h1>Настройки</h1></div><div class="settings">'
            f'<nav aria-label="Разделы настроек"><ul class="cnav cnav--side">{tabs}</ul></nav>'
            f'<div class="card"><h2>{title}</h2>{body}</div></div>')
    app_page(f"/test/settings/{key}/", f"Настройки · {title}", f"Настройки кабинета: {title}.", full,
             states=states, wide=True, active=f"/test/settings/{key}/")


def set_row(label, hint, val):
    h = f'<span class="small muted">{hint}</span>' if hint else ""
    return f'<div class="set-row"><div class="lbl"><b>{label}</b>{h}</div><div class="val">{val}</div></div>'


def page_settings():
    PAGES["/test/settings/"] = (head("Настройки", "Настройки кабинета.") +
                                '<body><meta http-equiv="refresh" content="0; url=/test/settings/general/">'
                                '<p class="wrap"><a href="/test/settings/general/">Настройки → Профиль</a></p></body></html>\n')
    profile = ('<div class="field"><label for="pn">Имя</label><input id="pn" value="Тест"></div>'
               '<div class="field mt-s"><label for="pc">Канал одной строкой</label>'
               '<input id="pc" value="Разборы реальных задач из практики"></div>'
               '<div class="field mt-s"><label for="pl">Язык кабинета</label><select id="pl"><option>Русский</option>'
               '<option disabled>English · Э3-19</option></select></div>')
    settings_page("general", "Профиль",
                  st("full", profile + f'<div class="btn-row mt-s">{a_btn("#s=saved", "Сохранить", True)}</div>')
                  + st("saved", profile + '<div class="btn-row mt-s"><span class="badge badge--ok">сохранено</span></div>')
                  + st("error", profile.replace('value="Тест"', 'value="" aria-invalid="true"')
                       + '<p class="err" style="color:var(--field-error-text)">Имя не может быть пустым.</p>'
                       + f'<div class="btn-row mt-s">{a_btn("#s=saved", "Сохранить", True)}</div>')
                  + st("loading", skel(4))
                  + st("long", profile.replace("Разборы реальных задач из практики", LONG)),
                  states=("full", "saved", "error", "loading", "long"))

    acc = (set_row("Вход", "Google: test@example.com", '<span class="badge badge--ok">Google</span>')
           + set_row("Выйти на всех устройствах", "Закроет вход везде, кроме этого браузера", a_btn("#s=confirm", "Выйти везде"))
           + set_row("Удалить данные", "По вашей просьбе удаляем систему канала и материалы",
                     a_btn("#s=confirm", "Удалить данные")))
    dlg = ('<div class="dlg" role="dialog" aria-labelledby="dh" style="position:static;margin:var(--space-16) 0">'
           '<div class="dlg-h"><b id="dh">Удалить данные канала «Тест»?</b>'
           f'{a_btn("#s=full", "✕")}</div><div class="dlg-b"><p>Удалим систему канала, материалы и доступ к каналу. '
           'Отменить нельзя. Оплаченный срок не возвращается автоматически — напишите, если нужен возврат.</p></div>'
           f'<div class="dlg-f">{a_btn("#s=full", "Отмена")}{a_btn("/test/logout/", "Удалить", True)}</div></div>')
    settings_page("account", "Аккаунт", st("full long", acc) + st("confirm", acc + dlg) + st("loading", skel(3)),
                  states=("full", "confirm", "loading"))

    priv = (set_row("Статистика и данные канала", "Чтобы готовить отчёты и решения", have("разрешено"))
            + set_row("Правки на канале", "Только после вашего «да», только на вашем канале", have("разрешено"))
            + set_row("Отозвать доступ", "В аккаунте Google: Безопасность → Сторонние приложения → improducer",
                      a_btn("/test/settings/connectors/#s=error", "Как это выглядит"))
            + set_row("Политика", "Что храним и зачем", '<a href="/privacy.html">Политика конфиденциальности</a>'))
    settings_page("privacy", "Приватность", st("full", priv) + st("loading", skel(3)), states=("full", "loading"))

    pays = [("13.10", "Пилот «вместе», первый платёж", "оплачено"), ("—", "Второй платёж — после концепции", "ждёт")]
    pay_rows = "".join(f'<tr><td class="n">{d}</td><td>{t}</td><td><span class="badge {"badge--ok" if s == "оплачено" else ""}">{s}</span></td></tr>'
                       for d, t, s in pays)
    bill = (set_row("Формат", "Пилот «вместе» · 4 недели", '<span class="badge badge--accent">основной</span>')
            + set_row("Цена", "Назовём числом на разговоре", '<span class="meta">цена — после решения</span>')
            + set_row("Срок", "Действует до 13.11 · письмо за 3 дня", '<span class="badge badge--ok">действует</span>')
            + set_row("Способ", "Картой по ссылке или счётом в USDT", a_btn("/test/upgrade/", "Сменить формат"))
            + '<h3 class="mt-s">Оплаты</h3><div class="scroll"><table><thead><tr><th>Дата</th><th>Что</th><th>Состояние</th>'
            f'</tr></thead><tbody>{pay_rows}</tbody></table></div>'
            + set_row("Не продлевать", "После срока — только чтение, ничего не стирается", a_btn("/test/paused/", "Отменить продление")))
    settings_page("billing", "План и оплата",
                  st("full long", f'<div class="sig">{stage("Э3-16")}</div>' + bill)
                  + st("empty", empty("Формат не выбран.", "вы выберете формат после разговора")
                       + f'<div class="btn-row mt-s">{a_btn("/test/upgrade/", "Выбрать формат", True)}</div>')
                  + st("error", warn("Оплата не прошла", "Банк отклонил платёж. Деньги не списаны. Попробуйте другую карту или USDT.",
                                     a_btn("/test/upgrade/", "Оплатить снова", True)) + bill)
                  + st("denied", PAUSED_CALL + bill)
                  + st("loading", skel(5)),
                  states=("full", "empty", "error", "denied", "loading", "long"))

    def bar(used, total, label):
        w = round(used / total * 100)
        return (f'<p class="small"><b>{label}</b> <span class="meta">{used} из {total} дней</span></p>'
                f'<svg viewBox="0 0 100 4" preserveAspectRatio="none" width="100%" height="8" aria-hidden="true">'
                f'<rect class="g-track" width="100" height="4" rx="2"/><rect class="g-fill" width="{w}" height="4" rx="2"/></svg>')
    usage_note = ('<p class="small muted">Лимита сообщений у нас нет: тариф — за канал в месяц. '
                  'Лимит вашего Claude виден в вашем Claude.</p>')
    settings_page("usage", "Срок и доступ",
                  st("full", '<div class="facts" style="margin-top:0"><div class="fact"><span class="k">доступ</span>'
                     '<span class="v">полный</span></div><div class="fact"><span class="k">до продления</span>'
                     '<span class="v num">27 дней</span></div></div><div class="mt-s">' + bar(3, 30, "Текущий период") + "</div>" + usage_note)
                  + st("near", '<div class="facts" style="margin-top:0"><div class="fact"><span class="k">доступ</span>'
                       '<span class="v">полный</span></div><div class="fact"><span class="k">до продления</span>'
                       '<span class="v num">3 дня</span></div></div><div class="mt-s">' + bar(27, 30, "Текущий период") + "</div>"
                       + note("Письмо отправлено", "Напоминание о продлении ушло на test@example.com.",
                              a_btn("/test/mail/renew/", "Открыть письмо")))
                  + st("denied", PAUSED_CALL + bar(30, 30, "Период закончился"))
                  + st("loading", skel(3)),
                  states=("full", "near", "denied", "loading"))

    caps = [("Подключить канал", True, ""), ("Анкета и фото", True, ""), ("ДНК", True, ""),
            ("Ниша и каналы-доноры", True, ""), ("Концепция — решение кнопкой", True, ""),
            ("Доска идей — отметки ✓ / ✕", True, ""), ("Контент-план", True, ""),
            ("Сценарии и упаковка", True, "закрытие через Claude — Э1-9"),
            ("Обложки", False, "Э2-9"), ("Выпуск", False, "Э1-27"),
            ("Разбор вышедших роликов для автора", False, "Э1-13"), ("Чат в приложении", False, "Э4-2")]
    cr = "".join(set_row(t, n, have() if ok else stage(n)) for t, ok, n in caps)
    cr += set_row("Письма-напоминания", "На 3-й день тишины, второе — через 7 дней · Э2-11",
                  '<label class="switch"><input type="checkbox" checked> Включены</label>')
    settings_page("capabilities", "Возможности", st("full", cr) + st("loading", skel(6)), states=("full", "loading"))

    yt_ok = set_row("YouTube: канал «Тест»", "Статистика и правки после «да» · подключён неделю назад",
                    '<span class="badge badge--ok">подключён</span>' + a_btn("/test/settings/privacy/", "Отключить"))
    yt_off = set_row("YouTube-канал", "Войти Google-аккаунтом канала", a_btn("/test/connect/", "Подключить", True))
    yt_err = set_row("YouTube: канал «Тест»", "Доступ отозван в Google — система не видит статистику",
                     '<span class="badge badge--no">нет доступа</span>' + a_btn("/test/connect/", "Подключить снова", True))
    cl_ok = set_row("Ваш Claude: коннектор improducer", "connect.improducer.co/mcp · последний вызов сегодня",
                    '<span class="badge badge--ok">подключён</span>' + a_btn("#s=loading", "Новый код"))
    cl_off = set_row("Ваш Claude", "Коннектор improducer: код действует сутки",
                     a_btn("#s=loading", "Получить код подключения", True))
    code = note("Код подключения", "1. В Claude: Настройки → Коннекторы → Добавить свой коннектор. Название — improducer, "
                "адрес — <code>https://connect.improducer.co/mcp</code>.<br>2. «Подключить» → код "
                "<code>TEST-0000</code> (пример).<br>3. «Разрешения инструментов» → «Разрешать всегда» на обе группы.")
    gl = set_row("Вход в кабинет", "Google: test@example.com", '<span class="badge badge--ok">Google</span>')
    settings_page("connectors", "Подключения",
                  st("full long", yt_ok + cl_ok + gl) + st("empty", yt_off + cl_off + gl)
                  + st("error", yt_err + cl_ok + gl) + st("loading", yt_ok + cl_off + code + gl),
                  states=("full", "empty", "error", "loading"))


# ── Оплата, пауза, письмо, выход ─────────────────────────────────────────────

def page_upgrade():
    pay_tabs = ('<ul class="cnav"><li><a href="#s=full" aria-current="page">Картой</a></li>'
                '<li><a href="#s=full">USDT</a></li></ul>')
    cards = "".join(plan_card(f, "/test/upgrade/paid/", "Оплатить") for f in FORMATS if f["tab"] == "start")
    body = ('<div class="center"><h1>Выберите формат</h1>'
            '<p class="lede">Разбор засчитывается в ДНК и пилот. Цены — после решения: на разговоре назовём числом.</p>'
            f'<div class="mt-s">{pay_tabs}</div></div>'
            + st("full long", f'<div class="plans">{cards}</div>')
            + st("loading", '<div class="plans">' + skel(5) * 3 + "</div>")
            + st("error", warn("Оплата не прошла", "Банк отклонил платёж, деньги не списаны. Попробуйте другую карту или USDT.",
                               a_btn("#s=full", "Выбрать снова", True)))
            + st("denied", note("Оплата — после разговора", "Ссылка на оплату приходит после разговора о канале.",
                                a_btn("/test/login/check/", "Записаться на разговор", True)))
            + '<p class="center small muted mt-s">Картой — ссылкой на оплату, комиссию берёт платёжный сервис. '
            'USDT — счётом на кошелёк, возврат только переводом вручную. Оплата автоматически — Э3-2.</p>')
    app_page("/test/upgrade/", "Выбрать формат", "Выбор формата и способа оплаты.", body,
             states=("full", "loading", "error", "denied", "long"), wide=True, active="/test/settings/billing/")
    paid = ('<div class="centered"><div class="box"><div class="card stack">'
            '<span class="badge badge--ok">оплачено</span><h1 class="screen-title">Оплата получена</h1>'
            '<p>Пилот «вместе», первый платёж. Доступ включаем вручную — обычно в тот же день. '
            'Письмо придёт на test@example.com.</p>'
            f'<div class="btn-row">{a_btn("/test/onboarding/", "Начать", True)}{a_btn("/test/settings/billing/", "План и оплата")}</div>'
            "</div></div></div>")
    bare_page("/test/upgrade/paid/", "Оплата получена", "Подтверждение оплаты.", paid)


def page_paused():
    body = ('<div class="greet"><h1>Тест, ваш путь на паузе</h1>'
            + st("full", PAUSED_CALL) + st("near", note("Через 3 дня — продление",
                                                        "Если не продлить, кабинет перейдёт в режим «только чтение». Ничего не стирается.",
                                                        a_btn("/test/upgrade/", "Продлить", True)))
            + st("full", composer(off=True, placeholder="Пауза: только чтение · продлите, чтобы продолжить"))
            + st("near", composer())
            + "</div><section><h2>Ваш путь</h2>"
            '<p class="small muted">Готово 5 из 12 · смотреть можно всё</p>' + steps_html() + "</section>")
    app_page("/test/paused/", "Пауза", "Пауза — только чтение: ничего не стирается.", body, states=("full", "near"))


def page_mail():
    body = ('<div class="wrap" style="padding-top:var(--space-40)"><div class="mail">'
            '<p class="crumb">Письмо · пример</p><div class="card stack">'
            '<div class="mail-h meta"><span>От</span><span>improducer &lt;founder@improducer.co&gt;</span>'
            '<span>Кому</span><span>test@example.com</span><span>Тема</span><span>Через 3 дня — продление</span></div>'
            f'{wordmark()}<p>Тест, здравствуйте.</p>'
            '<p>13.11 заканчивается оплаченный срок пилота «вместе». Чтобы путь шёл дальше без перерыва, продлите его.</p>'
            '<p>Если не продлить — кабинет перейдёт в режим «только чтение»: всё останется на месте, ничего не '
            'стирается. Новые шаги, решения и разбор роликов вернутся после продления.</p>'
            f'<div class="btn-row">{a_btn("/test/upgrade/", "Продлить", True)}{a_btn("/test/settings/billing/", "План и оплата")}</div>'
            '<p class="small muted">Письма о продлении приходят за 3 дня до срока · появится, Э2-12.</p></div></div></div>')
    PAGES["/test/mail/renew/"] = (head("Письмо о продлении", "Письмо за 3 дня до продления.") + '<body class="site">'
                                  + body + proto(["full"]) + '<script src="/test/assets/test.js"></script></body></html>\n')


def page_logout():
    body = ('<div class="centered"><div class="box"><div class="card stack">'
            '<h1 class="screen-title">Вы вышли</h1><p>Кабинет и материалы на месте. Войти снова — тем же аккаунтом Google.</p>'
            f'<div class="btn-row">{a_btn("/test/login/", "Войти", True)}{a_btn("/test/", "На главную")}</div>'
            "</div></div></div>")
    bare_page("/test/logout/", "Вы вышли", "Выход из кабинета.", body)


# ── Опись ───────────────────────────────────────────────────────────────────

OPIS_SCREENS = [
    # id, их экран, их адрес, наш адрес, что взяли, чего нет и почему, состояния
    ("S01", "Выдача поиска", "google.com/search?q=claude", None,
     "—", "Без аналога: выдача — чужая страница. Наш вход — метка go.improducer.co/<код> → /test/.", "—"),
    ("S02", "Главная", "claude.com/", "/test/",
     "Герой с карточкой входа по центру слева и примером справа; кнопка «в своём Claude» под карточкой; "
     "блок форматов с вкладками; вопросы",
     "Картинки нет — вместо неё пример кабинета «Теста». Кнопки «Скачать» нет: приложения нет, есть коннектор.",
     "заполнено"),
    ("S03", "Продукт", "claude.com/product/overview", "/test/product/",
     "Заголовок по центру с двумя кнопками, крошка раздела, блоки ниже",
     "Россыпи картинок нет: показываем недели, отличия и 12 шагов", "заполнено"),
    ("S04", "Цены", "claude.com/pricing", "/test/pricing/",
     "Вкладки, три карточки с «всё из …, плюс», таблица сравнения, вопросы",
     "Цен нет — «цена — после решения» (Д1). Подписки и студия — «появится Э3/Э4»", "заполнено"),
    ("S05", "Скачать", "claude.com/download", "/test/download/",
     "Заголовок с главной кнопкой; слева подпись блока, справа карточка со строками «где → действие»",
     "Без QR и магазинов: своего приложения нет, коннектор живёт в Claude автора", "заполнено"),
    ("S06", "Помощь", "support.claude.com/en/", "/test/help/",
     "Поиск, частые вопросы строками, разделы плитками", "Бокового меню разделов нет: разделов 5, хватает плиток",
     "заполнено · пусто · загрузка"),
    ("S07", "Вход", "claude.ai/login", "/test/login/",
     "Две колонки: слева заголовок и карточка входа, справа картинка; кнопка под карточкой",
     "Только Google: входа по почте и Apple нет (S-073). Справа — пример кабинета",
     "заполнено · загрузка · ошибка · нет доступа · длинный"),
    ("S08", "Письмо и код", "claude.ai/login (шаг 2)", "/test/login/check/",
     "Экран после выбора способа входа: что дальше, ошибка",
     "Кода по почте нет. На его месте — наш шаг: лист ожидания и запись на разговор",
     "заполнено · записан · загрузка · ошибка · нет доступа"),
    ("S09", "Каталог коннекторов", "claude.com/marketplace/connectors-plugins", None,
     "—", "Без аналога: у нас один коннектор, каталог — у Anthropic (вход in.catalog). Подключение — /test/download/", "—"),
    ("S10", "Статья помощи", "support.claude.com/en/articles/8114491", "/test/help/start/",
     "Крошки, H1, разделы статьи, «помогла?»", "Оглавления нет: статья короткая", "заполнено"),
    ("S11", "Первый запуск", "claude.ai (первый вход)", "/test/onboarding/",
     "Карточка по центру, один вопрос на экран, счёт шагов, «Дальше»",
     "Телефона и кода нет. Шаги наши: имя и согласие → анкета → канал", "заполнено · загрузка · ошибка"),
    ("S11b", "Доступ сервиса (OAuth)", "окно согласия коннектора", "/test/connect/",
     "Экран прав перед согласием", "Права — дословно наши две группы", "заполнено · загрузка · ошибка · нет доступа · длинный"),
    ("S12", "Новый чат", "claude.ai/new", "/test/new/",
     "Боковая панель; приветствие по центру; поле ввода; подсказки под ним; меню аккаунта внизу",
     "Чата нет (Э4-2): поле ведёт на макет, над ним — «Ваш шаг». Ниже — 12 шагов пути", "все шесть"),
    ("S13", "Чат", "claude.ai/chat/<id>", "/test/chat/",
     "Реплики, ответ с действиями, поле внизу, результат в панели справа", "Макет: чат не построен (Э4-2)", "все шесть"),
    ("S14", "Недавние", "claude.ai/recents", "/test/recents/",
     "Поиск сверху и строки «что · когда»", "Вместо чатов — решения и события канала", "все шесть"),
    ("S15", "Проекты", "claude.ai/projects", "/test/projects/",
     "Сетка карточек и кнопка «новый» справа от заголовка", "Второй канал — студия, Э3-4", "все шесть"),
    ("S16", "Проект", "claude.ai/project/<id>", "/test/project/test/",
     "Слева работа и поле ввода, справа — знания проекта", "Вместо чатов проекта — разделы шагов", "все шесть"),
    ("S17", "Артефакт", "панель справа в чате", "/test/project/test/koncepciya/",
     "Результат отдельной панелью рядом с разговором; версия", "Вместо «копировать» — решение кнопками",
     "все шесть + подтверждение"),
    ("S18", "Настройки: профиль", "claude.ai/settings/general", "/test/settings/general/",
     "Вкладки слева, форма справа, «Сохранить»", "—", "заполнено · сохранено · ошибка · загрузка · длинный"),
    ("S19", "Настройки: оплата", "claude.ai/settings/billing", "/test/settings/billing/",
     "Строки «подпись — значение», оплаты таблицей, отмена продления", "Цена — после решения", "все шесть"),
    ("S20", "Настройки: использование", "claude.ai/settings/usage", "/test/settings/usage/",
     "Полоса периода с подписью", "Лимита сообщений нет: тариф за канал (S-074)", "заполнено · близко к сроку · нет доступа · загрузка"),
    ("S21", "Настройки: возможности", "claude.ai/settings/capabilities", "/test/settings/capabilities/",
     "Строки функций с переключателем", "Функции не выключаются — показываем «есть / появится Э-…»", "заполнено · загрузка"),
    ("S22", "Настройки: коннекторы", "claude.ai/settings/connectors", "/test/settings/connectors/",
     "Строки подключений с состоянием и кнопкой", "—", "заполнено · пусто · ошибка · загрузка"),
    ("S23", "Повысить план", "claude.ai/upgrade", "/test/upgrade/",
     "Заголовок, переключатель способа, карточки, «Оплатить»", "Цен нет; оплата — после разговора", "заполнено · загрузка · ошибка · нет доступа · длинный"),
    ("S24", "Лимит исчерпан", "плашка над полем ввода", "/test/paused/",
     "Плашка над полем, поле недоступно, кнопка «Продлить»", "Лимита нет — есть пауза «только чтение» (S-077)", "заполнено · близко к сроку"),
    ("S25", "Меню и выход", "поповер аккаунта", "/test/logout/",
     "Меню внизу боковой панели; экран после выхода", "—", "заполнено"),
    ("S26", "Настройки: аккаунт", "claude.ai/settings/account", "/test/settings/account/",
     "Выйти везде, удалить — с подтверждением", "Удаление — по просьбе", "заполнено · подтверждение · загрузка"),
    ("S27", "Настройки: приватность", "claude.ai/settings/privacy", "/test/settings/privacy/",
     "Строки «что видим — состояние»", "Экспорта нет", "заполнено · загрузка"),
    ("—", "Письмо о продлении", "у образца не снято", "/test/mail/renew/",
     "—", "Наш шаг пути: письмо за 3 дня (Э2-12)", "заполнено"),
]

OPIS_PATHS = [
    ("F01", "Найти, войти, начать",
     "S01 → S07 → Google → S11 (телефон, код, 18+, имя) → S12 · ≈7 кликов",
     "/test/ → «Войти» → /test/login/ → Google → /test/login/check/ (время, «Записаться») → «Перейти к оплате» → "
     "/test/upgrade/ → «Оплатить» → /test/upgrade/paid/ → «Начать» → /test/onboarding/ → анкета → канал → "
     "/test/connect/ → «Разрешить» → /test/new/ · 12 кликов",
     "/test/", "У нас разговор и оплата — до работы (§4.8, S-073): бесплатного входа нет до проверки Google"),
    ("F02", "Первая работа", "S12 → ввод → S13 (идёт → готов) → S17 → S14 · 3 клика",
     "/test/new/ → «Открыть концепцию» → /test/project/test/koncepciya/ → «Утвердить» → /test/new/ → /test/recents/ · 3 клика",
     "/test/new/", "Работа — решения кнопками; разговор словами — в своём Claude, чат в приложении — Э4-2"),
    ("F03", "Работа в проекте", "S12 → S15 → S16 → S13 · 4 клика",
     "/test/new/ → «Каналы» → /test/projects/ → «Тест» → /test/project/test/ → раздел · 3 клика",
     "/test/projects/", "Проект = канал; второй канал — студия, Э3-4"),
    ("F04", "Подключить инструмент", "S25 → S22 → «Добавить свой» → OAuth → S13 · 5 кликов",
     "/test/download/ → «Подключить коннектор» → /test/settings/connectors/ → «Получить код» → код в Claude · 3 клика",
     "/test/download/", "Наш коннектор подключается в Claude автора; каталога нет"),
    ("F05", "Упёрся в лимит → заплатил", "S13 → S24 → «Повысить» → S23 → оплата → S19 · 4 клика",
     "/test/mail/renew/ → «Продлить» или /test/paused/ → «Продлить» → /test/upgrade/ → «Оплатить» → /test/upgrade/paid/ · 3 клика",
     "/test/mail/renew/", "Лимита нет — есть срок: письмо за 3 дня, потом пауза «только чтение»"),
    ("F06", "Настройки и выход", "S25 → S18 → S20 → S21 → S26 → «Выйти» → S07 · 5 кликов",
     "меню аккаунта → /test/settings/general/ → вкладки → /test/settings/account/ → «Выйти» → /test/logout/ · 5 кликов",
     "/test/settings/general/", "—"),
    ("F07", "Помощь", "S02 → S06 → S10 · 2 клика", "/test/ → «Помощь» → /test/help/ → /test/help/start/ · 2 клика",
     "/test/help/", "—"),
    ("F08", "Поставить приложение", "S02 → S05 → файл · 2 клика",
     "/test/ → «Подключить в своём Claude» → /test/download/ → «Подключить» · 2 клика", "/test/download/",
     "Приложения нет — коннектор в Claude автора"),
]

DESIGN_TODO = [
    ("Оболочка приложения: боковая панель + рабочая область", "≥1180 — панель слева; меньше — полоса сверху и меню по кнопке",
     "component.app.side-width = 260 (сейчас --tile-min)"),
    ("Шапка сайта", "обычная · липкая · телефон — меню по кнопке", "без новых значений: --nav-height, --sticky-bar-*"),
    ("Поле ввода чата", "пусто · текст · отправка · недоступно (пауза) · ошибка",
     "component.composer: радиус = --radius-card, высота = --field-textarea-min; стрелка — красная (исключение README)"),
    ("Сообщение чата", "реплика автора · ответ · идёт · ошибка · длинный", "component.message.author-bg = --color-bg-sunken"),
    ("Две колонки «работа · результат»", "≥1180 рядом, меньше — друг под другом", "сетка по --breakpoint-desktop"),
    ("Аккордеон вопросов", "свёрнут · раскрыт · фокус", "component.disclosure.marker"),
    ("Поповер (меню аккаунта, меню на телефоне)", "открыт · закрыт · фокус", "component.popover.shadow = --shadow-popover"),
    ("Карточка формата", "обычная · основной · появится Э-…", "без новых значений"),
    ("Шаги пути", "готово · ваше решение · ждёт", "в кабинете есть path-steps, в _design/ нет — перенести"),
    ("Пустое место «заполнится, когда…»", "пусто", "пунктирная граница --color-border-control"),
    ("Заготовки загрузки", "загрузка", "фон --color-bg-sunken, радиус --radius-8"),
]


def page_opis():
    scores = json.loads(SCORES.read_text()) if SCORES.exists() else {}

    def score(sid):
        s = scores.get(sid)
        if not s:
            return '<span class="meta">снимка образца нет</span>'
        return " · ".join(f'<span class="score">{w}: {s.get(w, "—")}</span>' for w in ("390", "820", "1440"))

    paths = "".join(
        f'<div class="row" data-id="{fid}"><div class="row-top"><span class="rank">{fid}</span><div class="rhead">'
        f'<p class="rtitle"><a href="{start}">{E(goal)}</a></p><p class="rmeta">{E(why)}</p></div></div>'
        f'<div class="cols"><p><b>Claude:</b> {E(theirs)}</p><p><b>Наш:</b> {E(ours)}</p></div>'
        '<div class="marks"><button class="mbtn" type="button" data-mark="ok">✓</button>'
        '<button class="mbtn" type="button" data-mark="no">✕</button>'
        '<button class="mbtn" type="button" data-mark="wrong">⊘</button>'
        '<textarea class="cmt" rows="1" placeholder="Комментарий"></textarea></div></div>'
        for fid, goal, theirs, ours, start, why in OPIS_PATHS)
    screens = []
    for sid, name, their, ours, took, miss, states in OPIS_SCREENS:
        link = f'<a href="{ours}">{ours}</a>' if ours else "без аналога"
        screens.append(
            f'<div class="row" data-id="{sid}"><div class="row-top"><span class="rank">{sid}</span><div class="rhead">'
            f'<p class="rtitle">{E(name)} → {link}</p><p class="rmeta">{E(their)} · совпадение {score(sid)}</p></div></div>'
            f'<div class="cols"><p><b>Взяли:</b> {E(took)}</p><p><b>Нет и почему:</b> {E(miss)}</p>'
            f'<p><b>Состояния:</b> {E(states)}</p></div>'
            '<div class="marks"><button class="mbtn" type="button" data-mark="ok">✓</button>'
            '<button class="mbtn" type="button" data-mark="no">✕</button>'
            '<button class="mbtn" type="button" data-mark="wrong">⊘</button>'
            '<textarea class="cmt" rows="1" placeholder="Комментарий"></textarea></div></div>')
    todo = "".join(f'<tr><td>{E(a)}</td><td>{E(b)}</td><td>{E(c)}</td></tr>' for a, b, c in DESIGN_TODO)
    notdone = [
        ("Экраны claude.ai после входа (S11–S27)",
         "Claude in Chrome не открывает claude.ai («Navigation to this domain is not allowed»). Восстановлены по статьям "
         "помощи и устройству образца; совпадение раскладки для них не мерено."),
        ("Ошибка кода и письмо со ссылкой (S08)", "нужен ввод почты — ушло бы письмо; восстановлено по статье 13189465"),
        ("Первый запуск нового аккаунта (S11)", "новых аккаунтов не заводим; по статьям 8287232, 8114491, 13117299"),
        ("«Лимит исчерпан» (S24)", "не вызвать без расхода лимита владельца; по статье 11647753"),
        ("Оплата Stripe", "платить нельзя; по статье 8325609"),
        ("Выдача на 390 и 820", "по заданию — одна выдача, один снимок 1440"),
    ]
    nd = "".join(f'<tr><td>{E(a)}</td><td>{E(b)}</td></tr>' for a, b in notdone)
    commits = json.loads((HERE / "commits.json").read_text()) if (HERE / "commits.json").exists() else []
    cm = "".join(f'<li><code>{E(c["sha"])}</code> {E(c["msg"])}</li>' for c in commits) or "<li>заполнится после выкладки</li>"
    body = f"""
<div class="wrap opis" style="padding-top:var(--space-page-top)">
<header class="page-head" style="padding-top:0">{wordmark()}
<p class="crumb">Прототип · опись</p>
<h1>Путь клиента: Claude → improducer</h1>
<p class="lede">Раскладка и логика пути клиента Claude, собранные для improducer в нашей дизайн-системе.
Примеры — выдуманный автор «Тест». Формы ничего не отправляют, входа, OAuth и оплаты нет.</p>
<div class="btn-row mt-s"><a class="btn btn--primary" href="/test/">Открыть прототип</a>
<button class="btn" type="button" data-act="copy-marks">Скопировать отметки</button></div>
<pre class="quote small" data-copy-out hidden></pre>
{note("Отметки — только в этом браузере",
      "Сайт статический: ✓ · ✕ · ⊘ и комментарии хранятся в этом браузере (localStorage) и до нас не доходят. "
      "Нажмите «Скопировать отметки» и вставьте в чат — вердикты собираем там.")}
</header>

<section><h2>1. Пути</h2><p class="muted">Их путь против нашего: экраны по порядку и клики. Ссылка — первая страница пути.</p>
{paths}</section>

<section><h2>2. Экраны</h2><p class="muted">Совпадение раскладки — imgdiff.py, режим layout: края, не цвет.
90+ совпадает, 75+ близко, 50+ частично. Ниже 75 — причина в «нет и почему».</p>
{"".join(screens)}</section>

<section><h2>3. Не снято и почему</h2><div class="scroll"><table><thead><tr><th>Что</th><th>Почему и чем заменили</th></tr></thead>
<tbody>{nd}</tbody></table></div></section>

<section><h2>4. На правку _design/</h2><p class="muted">В прототипе новых значений нет: раскладка — test/assets/test.css
на переменных tokens.css. Это стоит закрепить компонентами, если прототип принят.</p>
<div class="scroll"><table><thead><tr><th>Компонент</th><th>Состояния</th><th>Токен</th></tr></thead><tbody>{todo}</tbody></table></div></section>

<section><h2>5. Инструкция</h2>
<h3>Где лежат файлы</h3>
<ul><li>Сайт: репозиторий <code>ImproducerCo/improducerco.github.io</code>, на Маке — <code>~/.improducer/site</code>.</li>
<li>Страницы: <code>test/&lt;путь&gt;/index.html</code>, общий вид — <code>test/assets/</code>.</li>
<li>Исходник: <code>test/_build/build.py</code> (тексты и разметка), <code>test.css</code>, <code>test.js</code>.
Папку <code>_build</code> GitHub Pages не публикует.</li>
<li>Разбор образца: <code>~/Desktop/improducer/работа/2026-10-16_claude/</code> — <code>разбор.md</code>, снимки
<code>screens/</code> (их), <code>ours/</code> (наши), <code>diffs/</code>.</li></ul>
<h3>Поправить одну страницу и выложить</h3>
<pre class="quote small">cd ~/.improducer/site
# правка текста или разметки — в test/_build/build.py (функция page_…)
python3 test/_build/build.py
git add test/ &amp;&amp; git commit -m "fix(test): …" &amp;&amp; git pull --rebase &amp;&amp; git push</pre>
<p class="small muted">GitHub Pages обновляет страницы за 1–2 минуты после push. Вид (цвета, шрифты) берётся из
<code>_design/</code> при сборке — правка вида идёт туда, не в test/.</p>
<h3>Убрать /test/ целиком</h3>
<pre class="quote small">cd ~/.improducer/site
git rm -r test/
git commit -m "chore(test): remove client path prototype"
git pull --rebase &amp;&amp; git push</pre>
<h3>Коммиты</h3><ul>{cm}</ul>
</section>
<footer class="foot"><span>Все страницы /test/ закрыты от поиска (noindex), ссылок на них с сайта нет.</span></footer>
</div>"""
    PAGES["/test/opis/"] = (head("Опись", "Опись прототипа пути клиента и инструкция.") + "<body>" + body
                            + '<script src="/test/assets/test.js"></script></body></html>\n')


def main():
    copy_assets()
    for fn in (page_home, page_product, page_pricing, page_download, page_help, page_help_start,
               page_login, page_login_check, page_onboarding, page_connect, page_new, page_chat, page_recents,
               page_projects, page_project, page_concept, page_settings, page_upgrade, page_paused, page_mail,
               page_logout, page_opis):
        fn()
    for path, text in PAGES.items():
        out = TEST / path.removeprefix("/test/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(f"страниц: {len(PAGES)}")


if __name__ == "__main__":
    main()
