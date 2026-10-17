#!/usr/bin/env python3
"""Прототип пути клиента на improducer.co/test/.

    python3 test/_build/build.py          # из корня сайта: пересобрать все страницы test/

Экраны, порядок, переходы, блоки и состояния повторяют путь клиента образца (разбор — папка работы
~/Desktop/improducer/работа/2026-10-16_claude/, разбор.md: экраны S01–S27, пути F01–F08, компоненты C01–C28).
Вид — только дизайн-система improducer (_design/: tokens.css, components.css, шрифты, знак). Продукт —
безымянный ИИ-ассистент «improducer»: чаты, проекты, артефакты, коннекторы, планы. Тексты свои.
Пользователь — выдуманный «Тест». Вход — настоящий Google (my.improducer.co/google), остальные формы ничего не отправляют, оплаты нет.

Папка _build GitHub Pages не публикует (Jekyll пропускает папки с «_»): здесь исходник,
снаружи — собранные test/<путь>/index.html и test/assets/.
"""

import hashlib
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
               "denied": "Нет доступа", "long": "Длинный текст", "saved": "Сохранено",
               "confirm": "Подтверждение", "sent": "Письмо отправлено", "code": "Ввод кода",
               "badcode": "Неверный код", "limit": "Лимит исчерпан", "streaming": "Ответ идёт",
               "paid": "Оплачено", "tool": "С инструментом", "month": "Помесячно", "canceled": "Отменён",
               "close": "Близко к лимиту", "notfound": "Ничего не найдено", "select": "Выбор нескольких",
               "kbfull": "Знания почти заполнены", "add": "Добавить свой", "exported": "Экспорт запрошен", "signout": "Выйти везде",
               "decided": "Решение принято"}

PAGES = {}  # путь → html
KEEP = {"_build", "assets"}  # каталоги test/, которые сборка не удаляет


def check_labels():
    """Метки состояний в test.js — та же строка, что STATE_LABEL: расхождение валит сборку."""
    js = (HERE / "test.js").read_text(encoding="utf-8")
    want = "var LABEL = {" + ", ".join(f"{k}: '{v}'" for k, v in STATE_LABEL.items()) + "};"
    if want not in js:
        raise SystemExit("test.js: LABEL не совпадает со STATE_LABEL в build.py — поправьте строку в test.js:\n" + want)


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
    for name in ("test.css", "test.js", "vhod.css"):
        shutil.copy2(HERE / name, out / name)
    (out / "vhod").mkdir(exist_ok=True)
    for f in VHOD_PREV.glob("*.jpg"):
        shutil.copy2(f, out / "vhod" / f.name)
    # Geologica — шрифт строки площадок на входе (владелец 17.10, выбран из шести); в _design/ его пока нет.
    for f in (HERE / "fonts").iterdir():
        shutil.copy2(f, out / "fonts" / f.name)


# ── Общие куски ─────────────────────────────────────────────────────────────

def ver(src):
    """Метка версии файла в ссылке (?v=…): без неё браузер держит старый CSS/JS из кэша после выкладки."""
    return hashlib.sha256(src.read_bytes()).hexdigest()[:10]


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
<link rel="stylesheet" href="/test/assets/tokens.css?v={ver(DESIGN / "tokens.css")}">
<link rel="stylesheet" href="/test/assets/components.css?v={ver(DESIGN / "components.css")}">
<link rel="stylesheet" href="/test/assets/test.css?v={ver(HERE / "test.css")}">
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


def off_btn(text, primary=False):
    """Кнопка, у которой в прототипе нет страницы: видна, но не нажимается."""
    cls = "btn btn--primary" if primary else "btn"
    return f'<span class="{cls}" aria-disabled="true">{text}</span>'


LONG = ("Очень длинное название, которое не помещается в одну строку и проверяет перенос на телефоне "
        "и в узкой колонке без обрезки и наложения")
SCRIPT = f'<script src="/test/assets/test.js?v={ver(HERE / "test.js")}"></script>'


# ── Сайт ────────────────────────────────────────────────────────────────────

SITE_NAV = [("/test/product/", "Продукт"), ("/test/pricing/", "Цены"),
            ("/test/download/", "В своём Claude"), ("/test/help/", "Помощь")]
TRY = "Попробовать improducer"
CONNECTOR_URL = "https://connect.improducer.co/mcp"
OWN_CLAUDE = "Подключить в своём Claude"


def site_page(path, title, desc, body, states=("full",), crumb=None):
    nav = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{t}</a></li>'
                  for h, t in SITE_NAV)
    menu = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{t}</a>' for h, t in SITE_NAV)
    crumbbar = ""
    if crumb:
        crumbbar = (f'<div class="crumbbar"><div class="in"><span class="meta">{E(crumb)}</span>'
                    '<a class="meta" href="/test/help/">Помощь →</a></div></div>')
    PAGES[path] = (head(title, desc) + '<body class="site">'
                   f'<header class="site-head"><div class="in">{wordmark()}'
                   f'<ul class="site-nav">{nav}</ul>'
                   '<div class="site-cta">'
                   '<a class="btn hide-m" href="/test/login/">Войти</a>'
                   f'<a class="btn btn--primary hide-s" href="/test/login/">{TRY}</a></div>'
                   '<details class="site-menu"><summary class="btn">Меню</summary>'
                   f'<div class="pop"><a class="hide-wide" href="/test/login/"><b>{TRY}</b></a>{menu}<hr><a href="/test/login/">Войти</a></div></details>'
                   f'</div></header>{crumbbar}'
                   f'<main class="wrap">{body}</main>'
                   '<footer class="wrap"><div class="foot"><span>improducer.co</span>'
                   '<a href="/test/pricing/">Цены</a><a href="/test/download/">В своём Claude</a>'
                   '<a href="/test/help/">Помощь</a>'
                   '<a href="/privacy.html">Политика конфиденциальности</a>'
                   '<a href="/terms.html">Условия использования</a>'
                   '<span>Прототип: формы ничего не отправляют</span></div></footer>'
                   f'{proto(list(states))}{SCRIPT}</body></html>\n')


def bare_page(path, title, desc, body, states=("full",)):
    PAGES[path] = (head(title, desc) + '<body class="site">'
                   f'<header class="bare-head">{wordmark()}</header>'
                   f'<main>{body}</main>{proto(list(states))}'
                   f'{SCRIPT}</body></html>\n')


# Иконки боковой панели и поля ввода: линии в цвет текста, viewBox 20. Своих иконок в _design/ нет —
# рисуем простые, на правку _design/ (см. DESIGN_TODO).
_IC = {
    "panel": '<rect x="3" y="4" width="14" height="12" rx="2"/><path d="M8 4v12"/>',
    "chat": '<path d="M4 5.5h12v8H9.5L6 16v-2.5H4z"/>',
    "cabinet": '<rect x="3.5" y="3.5" width="5.5" height="5.5" rx="1.2"/><rect x="11" y="3.5" width="5.5" height="5.5" rx="1.2"/>'
               '<rect x="3.5" y="11" width="5.5" height="5.5" rx="1.2"/><rect x="11" y="11" width="5.5" height="5.5" rx="1.2"/>',
    "search": '<circle cx="9" cy="9" r="5"/><path d="m13 13 3.5 3.5"/>',
    "plus": '<path d="M10 4v12M4 10h12"/>',
    "projects": '<rect x="3.5" y="7" width="13" height="9.5" rx="1.8"/><path d="M5.5 4.5h9"/>',
    "artifacts": '<circle cx="7" cy="7" r="3"/><rect x="11" y="11" width="6" height="6" rx="1.2"/><path d="M13.5 3.5l3 5h-6z"/>',
    "clock": '<circle cx="10" cy="10" r="6.5"/><path d="M10 6.5V10l2.5 1.5"/>',
    "sliders": '<path d="M4 6h7M15 6h1M4 14h1M9 14h7"/><circle cx="13" cy="6" r="2"/><circle cx="7" cy="14" r="2"/>',
    "right": '<path d="m8 5 5 5-5 5"/>',
    "down": '<path d="m6 8 4 4 4-4"/>',
    "file": '<path d="M6 3.5h5.5L15 7v9.5H6z"/><path d="M11.5 3.5V7H15"/>',
    "ghost": '<path d="M5 17V9a5 5 0 0 1 10 0v8l-1.7-1.3L11.7 17 10 15.7 8.3 17l-1.6-1.3z"/><path d="M8 9h.01M12 9h.01"/>',
    "mic": '<rect x="8" y="3" width="4" height="9" rx="2"/><path d="M5 10a5 5 0 0 0 10 0M10 15v2.5"/>',
    "settings": '<circle cx="10" cy="10" r="2.5"/><path d="M10 3v2M10 15v2M3 10h2M15 10h2M5 5l1.4 1.4M13.6 13.6 15 15M5 15l1.4-1.4M13.6 6.4 15 5"/>',
    "help": '<circle cx="10" cy="10" r="6.5"/><path d="M8.2 8a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.2M10 13.5h.01"/>',
    "globe": '<circle cx="10" cy="10" r="6.5"/><path d="M3.5 10h13M10 3.5c2 2 2 11 0 13M10 3.5c-2 2-2 11 0 13"/>',
    "out": '<path d="M8 4H5v12h3M12 6.5 15.5 10 12 13.5M15.5 10H8"/>',
    "up": '<path d="M10 16V4M4.5 9.5 10 4l5.5 5.5"/>',
    "gauge": '<path d="M4 14a6 6 0 1 1 12 0"/><path d="m10 14 3-3.5"/>',
    "card": '<rect x="3" y="5" width="14" height="10" rx="1.8"/><path d="M3 8.5h14"/>',
}


def ic(name, label=None):
    aria = f' role="img" aria-label="{E(label)}"' if label else ' aria-hidden="true"'
    return (f'<svg class="ic" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round"{aria}>{_IC[name]}</svg>')


# ── Приложение ──────────────────────────────────────────────────────────────

RECENT = [("Что дальше по каналу?", "/test/chat/youtube/"), ("План поездки в Казань на 3 дня", "/test/chat/"),
          ("Письмо соседям о ремонте", "/test/chat/"), ("Разбор таблицы расходов", "/test/chat/"),
          ("Меню на неделю без молочного", "/test/chat/")]
ACCOUNT_MENU = ('<p class="pi">test@example.com</p>'
                f'<a href="/test/settings/general/">{ic("settings")}<span>Настройки</span></a>'
                f'<a class="usage-mini" href="/test/settings/usage/">{ic("gauge")}<span>Использование'
                '<span class="bar-mini"><i style="width:62%"></i></span>'
                '<span class="meta">62% · сброс в 18:00</span></span></a>'
                f'<a href="/test/settings/billing/">{ic("card")}<span>Подписка<span class="meta">Бесплатный план</span></span></a>'
                f'<a class="up" href="/test/upgrade/">{ic("up")}<span>Повысить план</span></a><hr>'
                f'<a href="/test/settings/general/#lang">{ic("globe")}<span>Язык</span><span class="meta">Русский</span></a>'
                f'<a href="/test/help/">{ic("help")}<span>Помощь</span></a><hr>'
                f'<a href="/test/logout/">{ic("out")}<span>Выйти</span></a>')


SIDE_NAV = [("/test/new/", "plus", "Новый чат"), ("/test/projects/", "projects", "Проекты"),
            ("/test/cabinet/", "cabinet", "Кабинет"), (None, "artifacts", "Артефакты"),
            (None, "clock", "Расписание"), ("/test/settings/capabilities/", "sliders", "Настроить")]
SIDE_MORE = [("/test/recents/", "Все чаты"), ("/test/settings/connectors/", "Коннекторы"), ("/test/help/", "Помощь")]
PINNED = [("Канал «Тест»", "/test/cabinet/youtube/"), ("Пример проекта", "/test/project/primer/")]


def app_page(path, title, desc, body, states=("full",), wide=False, active=None):
    active = active or path

    def item(h, icon, t):
        if not h:
            return f'<li><span class="off">{ic(icon)}<span>{t}</span></span></li>'
        cur = ' aria-current="page"' if h == active or (h == "/test/cabinet/" and active.startswith("/test/cabinet/")) else ""
        return f'<li><a href="{h}"{cur}>{ic(icon)}<span>{t}</span></a></li>'
    nav = "".join(item(*x) for x in SIDE_NAV)
    more = "".join(f'<a href="{h}">{t}</a>' for h, t in SIDE_MORE)
    nav += (f'<li><details class="more"><summary>{ic("right")}<span>Ещё</span></summary>'
            f'<div class="more-in">{more}</div></details></li>')
    pinned = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == active else ""}>{ic("projects")}'
                     f'<span>{E(t)}</span></a></li>' for t, h in PINNED)
    # Один чат на адрес: подсвечен первый пункт «Недавних» с адресом текущей страницы.
    lit = next((i for i, (_, h) in enumerate(RECENT) if h == active), None)
    recent = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if i == lit else ""}>'
                     f'<span>{E(t)}</span></a></li>' for i, (t, h) in enumerate(RECENT))
    menu = (f'<a href="/test/new/"><b>Новый чат</b></a>'
            + "".join(f'<a href="{h}">{t}</a>' for h, _, t in SIDE_NAV if h and h != "/test/new/")
            + '<hr><p class="pi">Недавние</p>'
            + "".join(f'<a href="{h}">{E(t)}</a>' for t, h in RECENT[:3])
            + "<hr>" + ACCOUNT_MENU)
    seg = (f'<span class="seg"><a href="/test/new/"{" aria-current=\"page\"" if not active.startswith("/test/cabinet/") else ""} '
           f'title="Чат">{ic("chat", "Чат")}</a><a href="/test/cabinet/"'
           f'{" aria-current=\"page\"" if active.startswith("/test/cabinet/") else ""} title="Кабинет">{ic("cabinet", "Кабинет")}</a></span>')
    PAGES[path] = (head(title, desc) + "<body>"
                   '<div class="app"><aside class="side">'
                   f'<div class="side-top"><button class="icon-btn hide-m" type="button" aria-label="Свернуть панель">{ic("panel")}</button>'
                   f'{wordmark("/test/new/", small=True, co=False)}{seg}'
                   '<details class="side-menu"><summary class="btn">Меню</summary>'
                   f'<div class="pop">{menu}</div></details></div>'
                   '<div class="side-nav">'
                   f'<label class="side-search">{ic("search")}<span class="visually-hidden">Поиск</span>'
                   '<input type="search" placeholder="Поиск"></label>'
                   f'<ul class="snav">{nav}</ul>'
                   f'<p class="side-k">Закреплённые</p><ul class="snav">{pinned}</ul>'
                   f'<div class="side-k side-k--row"><span>Недавние</span>'
                   f'<button class="icon-btn" type="button" aria-label="Фильтр">{ic("sliders")}</button></div>'
                   f'<ul class="snav recent">{recent}</ul></div>'
                   '<div class="side-foot"><details class="acct"><summary><span class="ava">Т</span>'
                   '<span class="who"><b>Тест</b><span class="meta">Бесплатный план</span></span>'
                   f'{ic("down")}</summary><div class="pop acct-pop">{ACCOUNT_MENU}</div></details></div>'
                   '</aside>'
                   f'<main class="main"><div class="{"main-wide" if wide else "main-in"}">{body}</div></main></div>'
                   f'{proto(list(states))}{SCRIPT}</body></html>\n')


def composer(off=False, text="", placeholder=None, nxt="/test/chat/", under=True):
    ph = placeholder or "Чем помочь сегодня?"
    dis = " disabled" if off else ""
    cls = " is-off" if off else ""
    under_html = ('<div class="under">'
                  f'<details class="umenu"><summary>Проект {ic("down")}</summary><div class="pop">'
                  '<a href="/test/project/primer/">Пример проекта</a><a href="/test/cabinet/youtube/">Канал «Тест»</a>'
                  '<hr><a href="/test/projects/">Все проекты</a></div></details>'
                  f'<details class="umenu umenu--r"><summary>Средне {ic("down")}</summary>'
                  '<div class="pop"><p class="pi">Глубина</p><a href="#">Быстро</a><a href="#"><b>Средне</b></a>'
                  '<a href="#">Глубоко</a></div></details></div>') if under else ""
    return (f'<div class="composer-wrap"><div class="composer{cls}"><label class="visually-hidden" for="q">Сообщение</label>'
            f'<textarea id="q" rows="2" placeholder="{E(ph)}" data-next="{nxt}"{dis}>{E(text)}</textarea>'
            f'<div class="tools"><details class="cmenu"><summary class="icon-btn" aria-label="Добавить">{ic("plus")}</summary>'
            f'<div class="pop"><a href="#">{ic("file")}<span>Файлы и фото</span></a>'
            f'<a href="/test/cabinet/">{ic("cabinet")}<span>Площадки</span><span class="meta">YouTube ✓</span></a>'
            f'<a href="/test/settings/connectors/">{ic("sliders")}<span>Коннекторы</span></a></div></details>'
            f'<span class="tools-r"><button class="icon-btn mic" type="button" aria-label="Диктовка"{dis}>{ic("mic")}{ic("down")}</button>'
            f'<a class="send" href="{nxt}" aria-label="Отправить"{" aria-disabled=\"true\"" if off else ""}>{ic("up")}</a>'
            f'</span></div></div>{under_html}</div>')


def limit_bar(until="18:00"):
    """C24: плашка над полем ввода — лимит до сброса и путь к плану."""
    return (f'<div class="limit" role="status"><span>Лимит сообщений исчерпан до {until}</span>'
            '<a href="/test/upgrade/">Повысить план</a></div>')


# ── Планы ───────────────────────────────────────────────────────────────────

TBD = "цена появится"  # цены не утверждены: у платных планов числа нет нигде в прототипе
PLANS = {
    "individual": [
        {"title": "Бесплатно", "sub": "Попробовать improducer", "price": "0 $", "pnote": "Бесплатно для всех",
         "plus": None,
         "ticks": ["Чат на improducer.co", "Площадка YouTube: один канал", "Кабинет с результатами",
                   "Работа в своём Claude через коннектор", "Анкета, ДНК, ниша и концепция"]},
        {"title": "Про", "sub": "Для канала, который выходит каждую неделю", "price": TBD,
         "pnote": "Сумма появится на этой странице", "plus": "Всё из Бесплатного, плюс:",
         "ticks": ["Больше использования*", "Доска идей, контент-план, сценарии", "Обложки и выпуск после вашего «да»",
                   "Аналитика вышедших роликов", "Коннекторы к своим сервисам"]},
        {"title": "Макс", "sub": "Для нескольких каналов и площадок", "price": TBD,
         "pnote": "Сумма появится на этой странице", "plus": "Всё из Про, плюс:", "main": True,
         "ticks": ["Больше каналов на площадке", "Telegram и Instagram — первыми, когда появятся",
                   "Ещё больше использования*", "Приоритет в часы высокой нагрузки"]},
    ],
    "team": [
        {"title": "Команда", "sub": "Стандартное место", "price": TBD, "pnote": "за участника в месяц",
         "plus": "Всё из Про для каждого, плюс:",
         "ticks": ["Общий кабинет площадок команды", "Оплата и участники в одном месте",
                   "Коннекторы для всей команды"]},
        {"title": "Команда", "sub": "Премиум место", "price": TBD, "pnote": "за участника в месяц",
         "plus": "Всё из стандартного места, плюс:", "main": True,
         "ticks": ["Больше использования", "Новые площадки — первыми"]},
    ],
    "api": [
        {"title": "Коннектор", "sub": "Свой Claude с кабинетом improducer", "price": TBD,
         "pnote": "входит в план аккаунта", "plus": None, "api": True,
         "ticks": ["Адрес коннектора и вход через Google", "Результаты — в том же кабинете"]},
        {"title": "API", "sub": "Данные кабинета в ваших программах", "price": TBD,
         "pnote": "оплата за объём запросов", "plus": None, "api": True, "main": True,
         "ticks": ["Доступ по ключу API", "Результаты функций площадок"]},
    ],
}

PLAN_TABS = [("individual", "Для себя"), ("team", "Команды"), ("api", "API")]


def plan_card(p, cta_href="/test/login/", cta="Попробовать"):
    main = " is-main" if p.get("main") else ""
    price = (f'<p class="pp{" tbd" if p["price"] == TBD else ""}">{p["price"]}</p>' if p["price"] else "")
    plus = f'<p class="small"><b>{p["plus"]}</b></p>' if p["plus"] else ""
    if p.get("api"):
        btn = a_btn("/test/download/", "Как подключить", True) if p["title"] == "Коннектор" else off_btn("Ключ API — нет в прототипе")
    else:
        btn = a_btn(cta_href, cta, True)
    ticks = "".join(f"<li>{t}</li>" for t in p["ticks"])
    return (f'<article class="card plan{main}"><h3 class="pt">{p["title"]}</h3><p class="muted">{p["sub"]}</p>'
            f'{price}<p class="small muted">{p["pnote"]}</p>'
            f'{btn}<hr class="hr">{plus}<ul class="ticks">{ticks}</ul></article>')


def plan_tabs(active, base="/test/pricing/"):
    tabs = "".join(f'<li><a href="{base}#{k}"{" aria-current=\"page\"" if k == active else ""}>{t}</a></li>'
                   for k, t in PLAN_TABS)
    return f'<div class="center"><ul class="cnav tabs">{tabs}</ul></div>'


FAQ_SITE = [
    ("Что такое improducer?",
     "Чат, который работает с вашими площадками: YouTube, Telegram, Instagram. Анкета, ДНК, ниша, "
     "концепция, идеи, план, сценарии, обложки, выпуск и аналитика — функциями, результаты — в кабинете."),
    ("Это бесплатно?",
     "Бесплатный план есть у всех. Цены платных планов появятся на странице «Цены»."),
    ("Можно работать в своём Claude?",
     "Да. Подключите коннектор improducer в своём Claude — результаты будут в том же кабинете, что и здесь."),
    ("Что система делает с каналом без меня?",
     "Читает статистику. Править канал и выкладывать ролики — только после вашего «да» в чате."),
    ("Где мои результаты?",
     "В кабинете: кнопка в боковой панели. У каждой площадки свой кабинет — функции и готовые страницы."),
]


def faq(items):
    return '<div class="faq">' + "".join(
        f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in items) + "</div>"


PLATFORMS = [("YouTube", "Канал: статистика, идеи, сценарии, выпуск", "есть"),
             ("Telegram", "Канал и посты", ""), ("Instagram", "Профиль и рилсы", "")]


def two_ways():
    """Два пути работы: чат здесь и свой Claude через коннектор; результаты — в одном кабинете."""
    return ('<div class="grid2 mt-s">'
            '<div class="card stack"><h3>Здесь, в чате</h3>'
            '<p>Пишите на improducer.co, как в обычном чате: «что дальше по каналу?». Ответ — с результатом рядом.</p>'
            f'<div class="btn-row">{a_btn("/test/login/", TRY, True)}</div></div>'
            '<div class="card stack"><h3>В своём Claude</h3>'
            '<p>Подключите коннектор improducer в своём Claude — на сайте или в приложении. Те же функции.</p>'
            f'<div class="btn-row">{a_btn("/test/download/", OWN_CLAUDE)}</div></div></div>'
            '<p class="small muted mt-s">В обоих случаях результаты — в вашем кабинете на improducer.co.</p>')


# ── Страницы сайта ──────────────────────────────────────────────────────────

def page_home():
    page_login("/test/")


def page_product():
    caps = [(t, w) for k, t, _, w, _, _, _ in FUNCS if k not in ("channel", "photos")]
    tl = "".join(f'<div class="tile"><span class="tn">{i:02d}</span><span class="tt">{t}</span>'
                 f'<span class="tr">{w}</span></div>' for i, (t, w) in enumerate(caps, 1))
    pl = "".join(f'<div class="card stack"><h3>{t} <span class="badge{" badge--ok" if s == "есть" else ""}">{s}</span></h3>'
                 f'<p>{d}</p></div>' for t, d, s in PLATFORMS)
    body = ('<section class="center" style="padding-top:var(--space-64)"><h1>Познакомьтесь с improducer</h1>'
            '<p class="lede">Чат, который ведёт ваши площадки: от анкеты и концепции до выпуска и разбора роликов.</p>'
            f'<div class="btn-row mt-s" style="justify-content:center">{a_btn("/test/login/", TRY, True)}'
            f'{a_btn("/test/pricing/", "Цены")}</div></section>'
            '<section class="mt"><h2>Что умеет на YouTube</h2>'
            '<p class="muted">Каждая функция — в чате словами и страницей результата в кабинете.</p>'
            f'<div class="tiles">{tl}</div></section>'
            f'<section class="mt"><h2>Площадки</h2><div class="grid3">{pl}</div></section>'
            f'<section class="mt"><h2>Где работать</h2>{two_ways()}</section>'
            '<section class="center mt"><h2>Начните бесплатно</h2>'
            f'<div class="btn-row mt-s" style="justify-content:center">{a_btn("/test/login/", TRY, True)}</div></section>')
    site_page("/test/product/", "Продукт", "Что умеет improducer по площадкам и функциям.", body, crumb="Продукт")


COMPARE = [("Чат на improducer.co", "✓", "✓", "✓"),
           ("Работа в своём Claude через коннектор", "✓", "✓", "✓"),
           ("Кабинет площадок", "✓", "✓", "✓"),
           ("YouTube: анкета, ДНК, ниша, концепция", "✓", "✓", "✓"),
           ("YouTube: доска идей, контент-план, сценарии", "×", "✓", "✓"),
           ("YouTube: обложки и выпуск после вашего «да»", "×", "✓", "✓"),
           ("Аналитика вышедших роликов", "базовая", "✓", "✓"),
           ("Каналов на площадке", "один", "один", "несколько"),
           ("Коннекторы к своим сервисам", "×", "✓", "✓"),
           ("Использование", "базовое", "больше", "ещё больше"),
           ("Telegram и Instagram — первыми", "×", "×", "✓")]


def compare_table():
    def cell(v):
        if v == "✓":
            return '<td><span class="badge badge--ok">✓</span></td>'
        if v == "×":
            return '<td><span class="badge">×</span></td>'
        return f'<td>{E(v)}</td>'
    tb = "".join(f'<tr><td>{E(r[0])}</td>{"".join(cell(v) for v in r[1:])}</tr>' for r in COMPARE)
    heads = "".join(f'<th>{n}<br>{a_btn("/test/login/", "Попробовать")}</th>' for n in ("Бесплатно", "Про", "Макс"))
    return ('<div class="field" style="max-width:var(--tile-min)"><label class="visually-hidden" for="cs">Поиск</label>'
            '<input id="cs" type="search" placeholder="Поиск по возможностям"></div>'
            f'<div class="scroll mt-s"><table class="compare"><thead><tr><th>Возможности</th>{heads}</tr></thead>'
            f'<tbody>{tb}</tbody></table></div>')


def page_pricing():
    blocks = []
    for k, _ in PLAN_TABS:
        cards = "".join(plan_card(p) for p in PLANS[k])
        tabs = "".join(f'<li><a href="#{kk}"{" aria-current=\"page\"" if kk == k else ""}>{tt}</a></li>'
                       for kk, tt in PLAN_TABS)
        foot = {"individual": "* Действуют лимиты использования. Цены платных планов появятся здесь.",
                "team": "Цена места появится здесь.",
                "api": "Коннектор подключается к своему Claude; ключ API — в Настройках."}[k]
        blocks.append(f'<div id="{k}" class="fmt-tab"><div class="center"><ul class="cnav tabs">{tabs}</ul></div>'
                      f'<div class="plans">{cards}</div><p class="center small muted mt-s">{foot}</p></div>')
    body = ('<section class="center" style="padding-top:var(--space-48)"><h1>Цены</h1></section>'
            f'<div class="mt-s fmt-tabs">{"".join(blocks)}</div>'
            f'<section class="mt"><h2>Сравнить планы</h2>{compare_table()}</section>'
            '<section class="center mt"><h2>Вопросы</h2></section>'
            f'{faq(FAQ_SITE[1:])}'
            # Вкладки — якорями, без скрипта: видна первая или та, на которую ведёт #якорь.
            '<style>.fmt-tabs:not(:has(.fmt-tab:target)) .fmt-tab:not(:first-child),'
            '.fmt-tab:target~.fmt-tab,.fmt-tab:has(~.fmt-tab:target){display:none}</style>')
    site_page("/test/pricing/", "Цены", "Планы improducer: Бесплатно, Про, Макс; команды; коннектор и API.", body, crumb="Цены")


def connector_steps():
    """Три шага: как подключить improducer к своему Claude."""
    steps = ["В своём Claude откройте Настройки → Коннекторы → «Добавить свой коннектор».",
             f"Название — improducer, адрес — <code>{CONNECTOR_URL}</code>.",
             "Войдите через Google тем же аккаунтом, что здесь, и напишите в чате: «improducer, что дальше по каналу?»."]
    return '<ol class="steps">' + "".join(f'<li><span class="n">{i:02d}</span><span class="t">{t}</span></li>'
                                         for i, t in enumerate(steps, 1)) + "</ol>"


def connector_addr():
    return (f'<div class="addr"><code>{CONNECTOR_URL}</code>'
            '<button class="btn" type="button" data-copy="' + CONNECTOR_URL + '">Скопировать</button></div>')


def page_download():
    rows = ('<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">В браузере</p>'
            f'<p class="rmeta">Ничего ставить не нужно</p></div>{a_btn("/test/login/", "Открыть", True)}</div></div>'
            '<div class="row" id="claude"><div class="row-top"><div class="rhead"><p class="rtitle">В своём Claude</p>'
            f'<p class="rmeta">Сайт и приложение Claude · коннектор improducer</p></div>{a_btn("#steps", "Подключить коннектор")}</div>'
            f'<div class="row-body">{connector_addr()}</div></div>'
            '<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">Телефон</p>'
            f'<p class="rmeta">Приложение improducer</p></div><span class="badge">скоро</span></div></div>')
    body = ('<section class="center" style="padding-top:var(--space-48)"><h1>Где работать с improducer</h1>'
            '<p class="lede">В браузере на improducer.co или в своём Claude. Результаты — в одном кабинете.</p>'
            '<div class="btn-row mt-s" style="justify-content:center">'
            f'{a_btn("/test/login/", "Открыть в браузере", True)}{a_btn("#steps", "Подключить в Claude")}</div></section>'
            '<section class="mt split"><div><h2>Все способы</h2>'
            '<p class="muted">Вход тот же — Google. Чаты, площадки и кабинет общие.</p></div>'
            f'<div class="card ways">{rows}</div></section>'
            '<section class="mt split" id="steps"><div><h2>Подключить к своему Claude</h2>'
            '<p class="muted">Три шага. Функции те же, что в чате здесь; результаты лягут в ваш кабинет.</p></div>'
            f'<div class="card stack">{connector_steps()}{connector_addr()}</div></section>'
            '<section class="center mt"><h2>Вопросы</h2></section>'
            + faq([("Нужен ли отдельный аккаунт для коннектора?", "Нет, вход тот же — Google. Кабинет общий."),
                   ("Что видит мой Claude?", "Функции improducer и результаты в кабинете: анкету, ДНК, концепцию, план."),
                   ("Будет ли приложение для телефона?", "Да, позже. Пока — браузер на телефоне или приложение Claude.")]))
    site_page("/test/download/", "В своём Claude", "Где работать с improducer: браузер, свой Claude, телефон.", body,
              crumb="В своём Claude")


HELP_TOPICS = [("Начало работы", "Вход, первый чат, подсказки"), ("Площадки и кабинет", "YouTube, функции, результаты"),
               ("Свой Claude", "Коннектор improducer, адрес, вход"), ("Аккаунт и вход", "Почта, Google, выход"),
               ("Планы и оплата", "Про, Макс, отмена, счета"), ("Приватность", "Экспорт, удаление, хранение")]


def page_help():
    pop = ["Начало работы с improducer", "Как подключить YouTube-канал", "Что лежит в кабинете",
           "Как работать в своём Claude", "Как устроены лимиты использования", "Как отменить план Про или Макс"]
    pl = "".join(f'<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">'
                 f'<a href="/test/help/start/">{t}</a></p></div></div></div>' for t in pop)
    tl = "".join(f'<a class="tile" href="/test/help/start/"><span class="tt">{t}</span><span class="tr">{d}</span>'
                 '<span class="tgo">Открыть →</span></a>' for t, d in HELP_TOPICS)
    search = ('<div class="field"><label for="hs">Поиск по статьям <span class="meta">⌘K</span></label>'
              '<input id="hs" type="search" placeholder="Например: лимит" data-next="/test/help/#s=empty"></div>')
    body = ('<section style="padding-top:var(--space-48)"><h1>Чем помочь?</h1>'
            f'<div class="mt-s" style="max-width:var(--container-single)">{search}</div></section>'
            + st("full long", f'<section class="mt"><h2>Частые статьи</h2>{pl}'
                 '<p class="small muted mt-s">В прототипе открывается одна статья-пример.</p></section>'
                 f'<section class="mt"><h2>Разделы</h2><div class="tiles">{tl}</div></section>')
            + st("empty", '<section class="mt">' + empty("По запросу «лимит» ничего не нашлось.",
                                                          "появится статья с этим словом; пока — раздел «Планы и оплата»")
                 + "</section>")
            + st("loading", '<section class="mt">' + skel(4, True) + "</section>"))
    site_page("/test/help/", "Помощь", "Помощь по improducer.", body, states=("full", "empty", "loading"))


def page_help_start():
    toc = [("what", "Что такое improducer"), ("where", "Где работать"), ("age", "Возраст"),
           ("how", "Как писать запросы"), ("plus", "Кнопка «+»"), ("model", "Какая модель отвечает"),
           ("limits", "Лимиты")]
    tc = "".join(f'<li><a href="#{k}">{t}</a></li>' for k, t in toc)
    text = ('<h2 id="what">Что такое improducer</h2><p>Чат, который работает с вашими площадками. Сейчас — YouTube: '
            'анкета, ДНК, ниша, концепция, идеи, план, сценарии, обложки, выпуск и аналитика. Результаты — в кабинете.</p>'
            '<h2 id="where">Где работать</h2><p>В браузере — improducer.co. В своём Claude — через коннектор '
            f'{CONNECTOR_URL}. Приложение для телефона — скоро. Вход везде один, кабинет общий.</p>'
            '<h2 id="age">Возраст</h2><p>Пользоваться можно с 18 лет.</p>'
            '<h2 id="how">Как писать запросы</h2><p>Пишите как коллеге — обычными словами. Про канал: '
            '«Что дальше по каналу?», «Идеи на неделю», «Разбери последний ролик». Любая другая задача — тоже словами.</p>'
            '<h2 id="plus">Кнопка «+»</h2><p>Слева внизу в поле ввода: файлы, ваши площадки, коннекторы.</p>'
            '<h2 id="model">Какая модель отвечает</h2><p>Название модели — под полем ввода, там же её можно сменить.</p>'
            '<h2 id="limits">Лимиты</h2><p>У каждого плана свой лимит сообщений. Когда он исчерпан, над полем '
            'ввода видно время сброса и ссылку «Повысить план».</p>')
    body = ('<div style="padding-top:var(--space-40)">'
            '<p class="crumb"><a href="/test/help/">Помощь</a> / Начало работы</p>'
            '<div class="split-r"><article><h1>Начало работы с improducer</h1>'
            '<p class="lede">Что умеет improducer и как начать первый чат.</p>'
            + st("full", text) + st("long", text + f"<p>{LONG}. {LONG}. {LONG}.</p>" * 3)
            + '<div class="marks" style="border:0;padding-inline:0"><span class="small muted">Статья помогла?</span>'
            '<button class="mbtn" type="button">Да</button><button class="mbtn" type="button">Нет</button></div>'
            '</article>'
            f'<aside class="card toc"><h3>В статье</h3><ul class="plain stack-s">{tc}</ul></aside></div></div>')
    site_page("/test/help/start/", "Начало работы", "Статья помощи: начало работы с improducer.", body,
              states=("full", "long"))


# Знак площадок — один в один состояние «Все пять» из _design/ideas/platforms-wave.html (владелец 17.10: «возьми
# вариант 5 из 5 с серыми колонками»): девять полосок с шагом 8, чётные — площадки на местах полосок знака, залиты
# их цветом, нечётные — серые, высотой среднее соседей. Пульс — из идеи, 2.4 с, одна фаза (test.css .wave-pulse).
WAVE_CX = [18, 26, 34, 42, 50, 58, 66, 74, 82]
WAVE_H = [12, 24, 36, 50, 64, 50, 36, 24, 12]
WAVE_BW, WAVE_SW, WAVE_REST = 4.5, .9, "#C9D1DC"
# Место на волне → (название, цвета, переход снизу вверх) — как NETS в идее.
WAVE_NETS = {0: ("TikTok", ["#25F4EE", "#FE2C55"], False),
             2: ("Instagram", ["#FEDA75", "#FA7E1E", "#D62976", "#962FBF", "#4F5BD5"], True),
             4: ("YouTube", ["#FF0000"], False),
             6: ("Telegram", ["#2AABEE", "#229ED9"], False),
             8: ("X", ["#1B2230"], False)}


# Строка названий под знаком — вразнобой (владелец 17.10); RedNote убран 17.10.
PLATFORM_CLOUD = ["TikTok", "YouTube", "Threads", "Telegram", "Facebook", "Instagram", "X"]


def platform_wave():
    defs, bars = [], []
    for i, (cx, h) in enumerate(zip(WAVE_CX, WAVE_H)):
        box = f'x="{cx - WAVE_BW / 2:g}" y="{50 - h / 2:g}" width="{WAVE_BW}" height="{h}" rx="{WAVE_BW / 2:g}"'
        if i not in WAVE_NETS:
            bars.append(f'<rect {box} fill="{WAVE_REST}"/>')
            continue
        name, colors, up = WAVE_NETS[i]
        if len(colors) > 1:
            stops = "".join(f'<stop offset="{k / (len(colors) - 1):g}" stop-color="{c}"/>' for k, c in enumerate(colors))
            defs.append(f'<linearGradient id="w{i}" x1="0" y1="{1 if up else 0}" x2="0" y2="{0 if up else 1}">'
                        f'{stops}</linearGradient>')
            paint = f"url(#w{i})"
        else:
            paint = colors[0]
        bars.append(f'<rect class="wave-pulse" {box} fill="none" stroke="{paint}" stroke-width="{WAVE_SW}"/>'
                    f'<rect {box} fill="{paint}"><title>{name}</title></rect>')
    names = ", ".join(n for n, _, _ in WAVE_NETS.values())
    # Рамка — по полоскам, с запасом на пульс (контур растёт в 1.9 раза вширь и в 1.14 ввысь): без пустых полей
    # SVG знак не отрывается от строки названий.
    left, right = WAVE_CX[0] - 2.5 * WAVE_BW, WAVE_CX[-1] + 2.5 * WAVE_BW
    top, height = 50 - max(WAVE_H) * .57, max(WAVE_H) * 1.14
    return (f'<svg class="wave" viewBox="{left:g} {top:g} {right - left:g} {height:g}" role="img" '
            f'aria-label="Площадки: {names}"><defs>{"".join(defs)}</defs>{"".join(bars)}</svg>')


def platform_cloud():
    return "".join(f"<li>{t}</li>" for t in PLATFORM_CLOUD)


# ── Вход и первый запуск ─────────────────────────────────────────────────────

# Владелец 17.10: кнопка ведёт в настоящий вход Google — тот же, что у кабинета (Катя, Юля), без своего макета окна.
# my.improducer.co/google ставит метку браузера, отправляет в Google и после входа возвращает в /test/new/.
SIGNIN = "https://my.improducer.co/google"


def login_form():
    return ('<div class="auth auth--login">'
            f'{gbtn(SIGNIN)}'
            '<p class="small muted">Продолжая, вы принимаете <a href="/terms.html">условия</a> и '
            '<a href="/privacy.html">политику конфиденциальности</a>.</p></div>')


def login_states():
    """Все состояния формы входа — одни на /test/login/ и на вариантах /test/vhod/NN/.
    Вход только через Google (владелец 17.10): почты, письма и кода нет — Google автору нужен всё равно для канала."""
    return (st("full", login_form())
            + st("loading", '<div class="auth auth--login">' + skel(3) + "</div>")
            + st("error", '<div class="auth auth--login">' + warn("Вход не завершён",
                                                                 "Окно Google закрыли или вход отменён. Попробуйте ещё раз.")
                 + gbtn(SIGNIN) + "</div>"))


LOGIN_STATES = ("full", "loading", "error")


def page_login(path="/test/login/"):
    # Владелец 17.10: из своих вариантов /test/vhod/ пока взят 06 «Горизонт» — временно, остальные варианты остаются.
    # Разметка и вид — те же, что у варианта (vx_horizon, vhod.css), чтобы не разъехались.
    cls, body = vx_horizon()
    PAGES[path] = (vx_head("Вход", "Вход в improducer через Google.")
                   + f'<body class="vx vx-06 {cls}">{body}{proto(list(LOGIN_STATES))}{SCRIPT}</body></html>\n')


def page_connect():
    """Макет окна согласия Google при подключении YouTube-канала."""
    scopes = ('<ul class="ticks"><li>Статистика канала «Тест»: просмотры, удержание, ролики</li>'
              '<li>Правки и выпуск роликов — только после вашего «да» в чате</li></ul>')
    body = ('<div class="centered"><div class="box"><div class="card stack">'
            '<p class="meta">accounts.google.com · test@example.com</p>'
            + st("full long", '<h1 class="screen-title">improducer запрашивает доступ к YouTube</h1>'
                 f'<p><b>improducer</b> запрашивает:</p>{scopes}'
                 '<p class="small muted">Доступ можно отключить в Настройках → Коннекторы.</p>'
                 f'<div class="btn-row">{a_btn("/test/cabinet/youtube/", "Разрешить", True)}'
                 f'{a_btn("/test/cabinet/", "Отклонить")}</div>')
            + st("loading", skel(4))
            + st("error", warn("Google не ответил", "Не удалось открыть окно согласия. Попробуйте ещё раз.",
                               a_btn("/test/connect/", "Повторить", True)))
            + "</div><p class=\"small muted center mt-s\">Макет: окно Google.</p></div></div>")
    bare_page("/test/connect/", "Доступ к YouTube", "Окно согласия Google при подключении YouTube-канала.",
              body, states=("full", "loading", "error"))


# ── Работа в приложении ─────────────────────────────────────────────────────

CHIPS = ('<div class="chips"><a href="/test/chat/youtube/">Что дальше по каналу?</a>'
         '<a href="/test/chat/youtube/">Идеи на неделю</a><a href="/test/chat/youtube/">Разбери последний ролик</a>'
         '<a href="/test/chat/">Написать</a></div>')


def page_new():
    hello = ('<h1 class="hello"><img src="/test/assets/logo/mark.svg" alt="" width="44" height="44">'
             '<span>Привет, Тест</span></h1>')
    tmp = f'<a class="icon-btn tmp-chat" href="#" title="Временный чат" aria-label="Временный чат">{ic("ghost")}</a>'
    body = (f'<div class="home">{tmp}<div class="home-c">'
            + st("full", hello + composer())
            + st("limit", hello + f'<div class="dock-limit">{limit_bar()}'
                 f'{composer(off=True, placeholder="Лимит исчерпан до 18:00")}</div>')
            + st("long", hello + composer(text=LONG))
            + st("loading", '<div style="width:100%">' + skel(2, True) + "</div>")
            + "</div></div>")
    app_page("/test/new/", "Новый чат", "Экран после входа: приветствие, поле ввода, проект и модель.", body,
             states=("full", "limit", "long", "loading"))


ARTIFACT = ('<h3>Казань за 3 дня</h3>'
            '<p><b>День 1.</b> Кремль и Кул-Шариф, вечером — улица Баумана.</p>'
            '<p><b>День 2.</b> Старо-Татарская слобода, музей чак-чака, набережная Казанки.</p>'
            '<p><b>День 3.</b> Свияжск: утренний автобус, обратно к ужину.</p>'
            '<p class="small muted">Пример документа-артефакта.</p>')


def page_chat():
    q = '<div class="msg-u">Составь план поездки в Казань на 3 дня</div>'
    card = ('<a class="art-card" href="#s=full"><span class="meta">Документ</span><b>Казань за 3 дня</b></a>')
    acts = ('<div class="acts"><button class="btn btn--ghost" type="button">Копировать</button>'
            '<a class="btn btn--ghost" href="#s=streaming">Повторить</a>'
            '<button class="btn btn--ghost" type="button" aria-label="Хороший ответ">↑</button>'
            '<button class="btn btn--ghost" type="button" aria-label="Плохой ответ">↓</button></div>')
    ready = (f'<div class="thread">{q}<div class="msg-a"><p>Вот план на три дня: центр, слобода и Свияжск. '
             f'Документ — справа.</p>{card}{acts}</div></div>')
    going = (f'<div class="thread">{q}<div class="msg-a"><p>Вот план на три дня: центр, слобода и</p>'
             '<span class="typing" aria-label="Ответ идёт"><i></i><i></i><i></i></span></div></div>')
    err = (f'<div class="thread">{q}'
           + warn("Ответ не пришёл", "Связь прервалась. Сообщение сохранено.", a_btn("#s=full", "Повторить", True))
           + "</div>")
    long = (f'<div class="thread"><div class="msg-u">{LONG}</div>'
            + "".join(f'<div class="msg-a"><p>{LONG}. {LONG}.</p></div>' for _ in range(3))
            + warn("Чат слишком длинный", "Лимит длины чата. Начните новый чат — важное можно перенести в проект.",
                   a_btn("/test/new/", "Новый чат", True)) + "</div>")
    tool = ('<div class="thread"><div class="msg-u">Найди в заметках список покупок и добавь хлеб</div>'
            '<div class="msg-a"><p><span class="badge badge--ok">Заметки · найдено 1</span> '
            '<span class="badge badge--ok">Заметки · изменено</span></p>'
            '<p>Нашёл заметку «Покупки» и добавил в неё хлеб. Теперь в списке 7 пунктов.</p></div></div>')
    limit_thread = ready.replace(card, "")

    panel = ('<aside class="card art"><div class="panel-h"><b>Казань за 3 дня</b><span class="badge">версия 2 из 2</span>'
             '<div class="btn-row"><button class="btn btn--ghost" type="button">Копировать</button>'
             '<button class="btn btn--ghost" type="button">Скачать</button>'
             '<a class="btn btn--ghost" href="#s=tool" aria-label="Закрыть">✕</a></div></div>'
             '<ul class="cnav"><li><a href="#s=full" aria-current="page">Просмотр</a></li>'
             '<li><a href="#s=full">Код</a></li></ul>'
             + st("full long limit", ARTIFACT) + st("streaming", '<p class="meta">создаётся…</p>' + skel(4))
             + "</aside>")
    body = ('<div class="page-top"><h1 class="screen-title">' + st("full streaming error limit long", "План поездки в Казань", "span")
            + st("tool", "Список покупок", "span") + '</h1>'
            '<div class="btn-row"><button class="btn" type="button">Поделиться</button></div></div>'
            '<div class="chat-split"><div class="chat-col">'
            + st("full", ready) + st("streaming", going) + st("error", err) + st("long", long)
            + st("tool", tool) + st("limit", limit_thread)
            + '<div class="dock">'
            + st("full streaming error long tool", composer(placeholder="Ответить…"))
            + st("limit", limit_bar() + composer(off=True, placeholder="Лимит исчерпан до 18:00"))
            + "</div></div>"
            + st("full streaming limit long", panel)
            + "</div>")
    app_page("/test/chat/", "Чат", "Чат: сообщения, ответ, панель артефакта, состояния.", body,
             states=("full", "streaming", "error", "long", "limit", "tool"), wide=True)


CONCEPT_DOC = ('<h3>Концепция канала «Тест» · вариант 2</h3>'
               '<p><b>О чём.</b> Разборы реальных задач из практики автора: один случай — один ролик, с числами.</p>'
               '<p><b>Для кого.</b> Специалисты в начале пути, которые ищут, как работают опытные коллеги.</p>'
               '<p><b>Чем отличается.</b> Не теория, а разобранный случай: что было, что сделали, что вышло.</p>'
               '<p class="small muted">Пример на выдуманном авторе «Тест».</p>')
CONCEPT_HREF = "/test/cabinet/youtube/koncepciya/"


def page_chat_youtube():
    q = '<div class="msg-u">Что дальше по каналу?</div>'
    card = (f'<a class="art-card" href="#s=full"><span class="meta">Концепция · YouTube</span>'
            '<b>Концепция канала «Тест» · вариант 2</b></a>')
    acts = ('<div class="acts"><button class="btn btn--ghost" type="button">Копировать</button>'
            '<a class="btn btn--ghost" href="#s=streaming">Повторить</a>'
            '<button class="btn btn--ghost" type="button" aria-label="Хороший ответ">↑</button>'
            '<button class="btn btn--ghost" type="button" aria-label="Плохой ответ">↓</button></div>')
    ready = (f'<div class="thread">{q}<div class="msg-a"><p>По каналу «Тест» готово 6 из 12. Сейчас нужен ваш выбор — '
             'концепция канала. Система предложила два варианта; второй ближе к вашей анкете и ДНК.</p>'
             f'<p>Вариант 2 — справа. Утвердить, поправить или взять другой можно здесь словами или в кабинете.</p>{card}{acts}</div></div>')
    going = (f'<div class="thread">{q}<div class="msg-a"><p>По каналу «Тест» готово 6 из 12. Сейчас нужен ваш</p>'
             '<span class="typing" aria-label="Ответ идёт"><i></i><i></i><i></i></span></div></div>')
    err = (f'<div class="thread">{q}'
           + warn("Ответ не пришёл", "Связь прервалась. Сообщение сохранено.", a_btn("#s=full", "Повторить", True))
           + "</div>")
    long = (f'<div class="thread"><div class="msg-u">{LONG}</div>'
            + "".join(f'<div class="msg-a"><p>{LONG}. {LONG}.</p></div>' for _ in range(3)) + "</div>")
    panel = ('<aside class="card art"><div class="panel-h"><b>Концепция канала «Тест» · вариант 2</b>'
             '<span class="badge badge--wait">ваше решение</span>'
             f'<div class="btn-row">{a_btn(CONCEPT_HREF, "Открыть в кабинете", True)}'
             '<button class="btn btn--ghost" type="button">Копировать</button>'
             '<button class="btn btn--ghost" type="button" aria-label="Закрыть">✕</button></div></div>'
             + st("full long", CONCEPT_DOC) + st("streaming", '<p class="meta">создаётся…</p>' + skel(4))
             + "</aside>")
    body = ('<div class="page-top"><h1 class="screen-title">Что дальше по каналу?</h1>'
            f'<div class="btn-row"><span class="badge badge--ok">YouTube · канал «Тест»</span>'
            '<button class="btn" type="button">Поделиться</button></div></div>'
            '<div class="chat-split"><div class="chat-col">'
            + st("full", ready) + st("streaming", going) + st("error", err) + st("long", long)
            + f'<div class="dock">{composer(placeholder="Ответить…", nxt="/test/chat/youtube/")}</div></div>'
            + st("full streaming long", panel)
            + "</div>")
    app_page("/test/chat/youtube/", "Что дальше по каналу?", "Чат про канал «Тест»: ответ и концепция в панели справа.",
             body, states=("full", "streaming", "error", "long"), wide=True)


CHATS = [("Что дальше по каналу?", "5 минут назад"), ("План поездки в Казань на 3 дня", "2 часа назад"), ("Письмо соседям о ремонте", "вчера"),
         ("Разбор таблицы расходов", "3 дня назад"), ("Меню на неделю без молочного", "5 дней назад"),
         ("Как вывести пятно от кофе", "неделю назад"), ("Поздравление коллеге с юбилеем", "2 недели назад")]


def chat_rows(long=False, select=False, items=CHATS):
    out = []
    for i, (t, when) in enumerate(items):
        t = f"{t} — {LONG}" if long and i == 0 else t
        box = f'<input type="checkbox" aria-label="Выбрать"{" checked" if i < 2 else ""}> ' if select else ""
        out.append(f'<div class="row"><div class="row-top"><div class="rhead"><p class="rtitle">{box}'
                   f'<a href="{"/test/chat/youtube/" if t == "Что дальше по каналу?" else "/test/chat/"}">{E(t)}</a></p>'
                   f'<p class="rmeta">Последнее сообщение {when}</p></div></div></div>')
    return "".join(out)


def page_recents():
    search = ('<div class="field"><label class="visually-hidden" for="rs">Поиск</label>'
              '<input id="rs" type="search" placeholder="Поиск по чатам" data-next="/test/recents/#s=notfound"></div>')
    body = ('<div class="page-top"><h1>Чаты</h1><div class="btn-row">'
            f'{a_btn("/test/new/", "＋ Новый чат", True)}</div></div>'
            f'<div class="stack">{search}'
            + st("full", f'<p class="small muted">7 чатов · <a href="#s=select">Выбрать</a></p>{chat_rows()}')
            + st("select", '<div class="btn-row"><span class="small">Выбрано 2</span>'
                 f'<button class="btn" type="button">Удалить</button>{a_btn("#s=full", "Отмена")}</div>'
                 + chat_rows(select=True))
            + st("long", f'<p class="small muted">7 чатов</p>{chat_rows(long=True)}')
            + st("empty", empty("Чатов пока нет.", "вы начнёте первый чат") +
                 f'<div class="btn-row">{a_btn("/test/new/", "Начать чат", True)}</div>')
            + st("notfound", empty("По запросу «отпуск» ничего не нашлось.", "появится чат с этим словом"))
            + st("loading", skel(2) + skel(2))
            + "</div>")
    app_page("/test/recents/", "Чаты", "Все чаты: поиск и выбор.", body,
             states=("full", "select", "long", "empty", "notfound", "loading"))


PROJECTS = [("Домашний бюджет", "Расходы по месяцам и план накоплений", "изменён вчера"),
            ("Поездка в Казань", "Билеты, жильё и маршрут", "изменён 3 дня назад"),
            ("Ремонт кухни", "Смета, замеры, список покупок", "изменён 2 недели назад")]


def project_tiles(long=False):
    out = []
    for i, (t, d, w) in enumerate(PROJECTS):
        t = f"{t} — {LONG}" if long and i == 0 else t
        out.append(f'<a class="tile" href="/test/project/primer/"><span class="tt">{E(t)}</span>'
                   f'<span class="tr">{d}</span><span class="meta">{w}</span></a>')
    return f'<div class="tiles">{"".join(out)}</div>'


def page_projects():
    tools = ('<div class="proj-tools"><div class="field"><label class="visually-hidden" for="ps">Поиск</label>'
             '<input id="ps" type="search" placeholder="Поиск по проектам"></div>'
             '<div class="field"><label class="visually-hidden" for="so">Сортировка</label>'
             '<select id="so"><option>Последние изменения</option><option>По названию</option>'
             '<option>По дате создания</option></select></div></div>')
    body = ('<div class="page-top"><h1>Проекты</h1><div class="btn-row">'
            f'{a_btn("/test/project/primer/#s=empty", "＋ Новый проект", True)}</div></div>'
            + tools
            + st("full", project_tiles()) + st("long", project_tiles(long=True))
            + st("empty", empty("Проектов пока нет.", "вы создадите первый проект: папку с инструкциями и файлами")
                 + f'<div class="btn-row mt-s">{a_btn("/test/project/primer/#s=empty", "Создать проект", True)}</div>')
            + st("loading", '<div class="tiles">' + skel(1, True) * 3 + "</div>"))
    app_page("/test/projects/", "Проекты", "Проекты: сетка, поиск, сортировка.", body,
             states=("full", "long", "empty", "loading"), wide=True)


def kb_bar(pct):
    return (f'<p class="small"><b>Ёмкость знаний</b> <span class="meta">занято {pct}%</span></p>'
            f'<svg viewBox="0 0 100 4" preserveAspectRatio="none" width="100%" height="8" aria-hidden="true">'
            f'<rect class="g-track" width="100" height="4" rx="2"/><rect class="g-fill" width="{pct}" height="4" rx="2"/></svg>')


def page_project():
    files = "".join(f'<li><span>{f}</span> <span class="meta">{s}</span></li>' for f, s in
                    (("расходы-2026.csv", "48 КБ"), ("план-накоплений.pdf", "120 КБ"), ("заметки.txt", "3 КБ")))
    side_full = ('<aside class="stack">'
                 '<div class="card"><div class="panel-h"><b>Инструкции</b><div class="btn-row">'
                 '<button class="btn btn--ghost" type="button">Изменить</button></div></div>'
                 '<p class="small">Отвечай коротко. Суммы — в рублях, округляй до сотен.</p></div>'
                 '<div class="card"><div class="panel-h"><b>Знания</b><div class="btn-row">'
                 '<button class="btn btn--ghost" type="button">＋ Добавить</button></div></div>'
                 '{bar}<ul class="plain stack-s mt-s">' + files + '</ul>{warn}</div></aside>')
    side_empty = ('<aside class="stack"><div class="card"><b>Инструкции</b>'
                  '<p class="small muted">Расскажите, как отвечать в этом проекте.</p>'
                  '<button class="btn" type="button">Добавить инструкции</button></div>'
                  '<div class="card"><b>Знания</b><p class="small muted">Файлы, которые учитывает каждый чат проекта.</p>'
                  '<button class="btn" type="button">＋ Добавить файлы</button></div></aside>')
    chats = chat_rows(items=[("Разбор таблицы расходов", "вчера"), ("Сколько откладывать в месяц", "4 дня назад")])
    body = ('<p class="crumb"><a href="/test/projects/">Все проекты</a></p>'
            '<div class="page-top"><h1>' + st("full kbfull loading", "Домашний бюджет", "span")
            + st("empty", "Новый проект", "span") + '</h1></div>'
            + st("full kbfull", '<p class="muted">Расходы по месяцам и план накоплений</p>')
            + '<div class="split-r"><div class="stack">'
            + composer(placeholder="Начать чат в проекте…")
            + st("full kbfull", f'<h2>Чаты проекта</h2>{chats}')
            + st("empty", empty("Чатов в проекте пока нет.", "вы начнёте первый чат в поле выше"))
            + st("loading", skel(2) + skel(2))
            + "</div>"
            + st("full", side_full.replace("{bar}", kb_bar(12)).replace("{warn}", ""))
            + st("kbfull", side_full.replace("{bar}", kb_bar(92)).replace(
                "{warn}", warn("Знания почти заполнены", "Уберите ненужные файлы или разделите проект на два.")))
            + st("empty", side_empty)
            + st("loading", '<aside class="stack">' + skel(3) + "</aside>")
            + "</div>")
    app_page("/test/project/primer/", "Проект", "Проект: чаты, инструкции и знания.", body,
             states=("full", "empty", "kbfull", "loading"), wide=True, active="/test/projects/")


# ── Кабинет: площадки и их функции ─────────────────────────────────────────

# Функции площадки YouTube: что / зачем — из AI OS Basic/author_steps.json (через генератор 342ce61).
# key, название, состояние, что, зачем, фраза для чата, «заполнится, когда …» (для «ждёт»).
FUNCS = [
    ("channel", "Подключение канала", "done", "Вход Google-аккаунтом канала: система видит статистику",
     "видно, что у вас уже работает; править канал — только после вашего «да»", "Подключи мой YouTube-канал", ""),
    ("anketa", "Анкета", "done", "О чём канал, для кого, цель, как снимаете, границы, куда звать зрителя",
     "из ваших слов и материалов собирается ДНК", "Покажи мою анкету", ""),
    ("photos", "Фото для обложек", "done", "Хотя бы 6 разных снимков: лицо крупно, разные повороты и эмоции",
     "обложки собираются из ваших фото", "Каких фото не хватает для обложек?", ""),
    ("dna", "ДНК", "done", "Кто вы, во что верите, что продаёте и чего не делаете",
     "по ней пишутся темы и сценарии — вашими словами", "Что в моей ДНК?", ""),
    ("niche", "Ниша и каналы-доноры", "done", "Каналы вашей ниши и ролики, которые у них выстрелили",
     "темы берутся из того, что уже доказало спрос", "Покажи каналы-доноры", ""),
    ("concept", "Концепция", "now", "О чём канал, для кого и чем он отличается",
     "решение за вами — от него зависят все темы", "Покажи варианты концепции", ""),
    ("board", "Доска идей", "wait", "Идеи роликов по вашим рубрикам",
     "вы отмечаете ✓ / ✕, какие идеи берёте", "Идеи на неделю", "утверждена концепция"),
    ("plan", "Контент-план", "wait", "Темы по датам съёмки и выхода",
     "видно, что снимать и когда", "Что снимать на этой неделе?", "отмечены идеи на доске"),
    ("scripts", "Сценарии и упаковка", "wait", "Сценарий целиком и упаковка: название, описание, теги",
     "готово к съёмке слово в слово", "Напиши сценарий следующего ролика", "готов контент-план"),
    ("covers", "Обложки", "wait", "Обложки из ваших фото",
     "обложка решает, нажмут ли на ролик", "Собери обложку для ролика", "готов сценарий"),
    ("release", "Выпуск", "wait", "Ролик выходит на канале после вашего «да»",
     "без ручной загрузки и копирования описаний", "Выложи ролик в четверг", "готов первый ролик"),
    ("analytics", "Аналитика вышедших роликов", "done", "Что сработало в вышедших роликах и что поменять",
     "следующие темы — по вашим цифрам, а не наугад", "Разбери последний ролик", ""),
]
FUNC_STATE = {"done": ("готово", "badge--ok"), "now": ("ваше решение", "badge--wait"), "wait": ("ждёт", "")}
DONE = sum(1 for f in FUNCS if f[2] == "done")


def func_rows(long=False):
    out = []
    for i, (key, title, state, what, why, say, when) in enumerate(FUNCS, 1):
        label, badge = FUNC_STATE[state]
        if long and key == "concept":
            title = f"{title} — {LONG}"
        if key == "concept":
            go = a_btn(CONCEPT_HREF, "Открыть →", True)
        elif state == "done":
            go = '<span class="meta">страница результата — нет в прототипе</span>'
        else:
            go = f'<span class="meta">заполнится, когда {when}</span>'
        name = f'<a href="{CONCEPT_HREF}">{E(title)}</a>' if key == "concept" else E(title)
        out.append(f'<div class="row fn{" now" if state == "now" else ""}" id="{key}"><div class="row-top">'
                   f'<span class="rank">{i:02d}</span><div class="rhead"><p class="rtitle">{name}</p>'
                   f'<p class="rmeta">в чате: «{E(say)}»</p></div><span class="badge {badge}">{label}</span></div>'
                   f'<div class="row-body"><p><b>Что.</b> {E(what)}. <b>Зачем.</b> {E(why[0].upper() + why[1:])}.</p>'
                   f'<div class="btn-row">{go}</div></div></div>')
    return '<div class="fn-list">' + "".join(out) + "</div>"


def own_claude_card():
    return ('<aside class="card stack own"><h3>Работать в своём Claude</h3>'
            '<p class="small">Подключите improducer к своему Claude — функции те же, результаты лягут сюда же.</p>'
            f'{connector_addr()}'
            f'<div class="btn-row">{a_btn("/test/download/#steps", "Как подключить →")}</div></aside>')


def plat_tiles(long=False):
    yt_title = f"YouTube — {LONG}" if long else "YouTube"
    yt = ('<a class="tile plat" href="/test/cabinet/youtube/"><span class="tn">Площадка</span>'
          f'<span class="tt">{E(yt_title)}</span><span class="tr">канал «Тест» · подключён</span>'
          f'<span class="tv">{DONE} из {len(FUNCS)}</span><span class="small muted">функций готово · '
          'ваше решение: концепция</span><span class="tgo">Открыть кабинет →</span></a>')
    soon = "".join(f'<div class="tile plat"><span class="tn">Площадка</span><span class="tt">{t}</span>'
                   f'<span class="tr">{d}</span></div>' for t, d, _ in PLATFORMS[1:])
    add = ('<a class="tile plat is-add" href="/test/settings/connectors/"><span class="tt">＋ Добавить площадку</span>'
           '<span class="tr">Подключения площадок и своих сервисов — в Настройках → Коннекторы.</span>'
           '<span class="tgo">Открыть →</span></a>')
    return f'<div class="tiles plats">{yt}{soon}{add}</div>'


def page_cabinet():
    body = ('<div class="page-top"><h1>Кабинет</h1><div class="btn-row">'
            f'{a_btn("/test/chat/youtube/", "Обсудить в чате")}</div></div>'
            '<p class="muted">Площадки и результаты работы — из чата здесь и из вашего Claude.</p>'
            '<div class="mt-s">'
            + st("full", plat_tiles()) + st("long", plat_tiles(long=True))
            + st("empty", empty("Площадки не подключены.", "вы подключите первую площадку — сейчас это YouTube")
                 + f'<div class="btn-row mt-s">{gbtn("/test/connect/", "Подключить YouTube через Google")}</div>')
            + st("loading", '<div class="tiles plats">' + skel(1, True) * 4 + "</div>")
            + st("error", warn("Кабинет не загрузился", "Сервер не ответил. Данные на месте — обновите страницу.",
                               a_btn("/test/cabinet/", "Обновить", True)))
            + "</div>")
    app_page("/test/cabinet/", "Кабинет", "Кабинет: площадки и их результаты.", body,
             states=("full", "empty", "loading", "error", "long"), wide=True, active="/test/cabinet/")


def page_cabinet_youtube():
    facts = ('<div class="facts"><div class="fact"><span class="k">функций готово</span>'
             f'<span class="v num">{DONE} из {len(FUNCS)}</span></div>'
             '<div class="fact"><span class="k">ваше решение</span><span class="v">Концепция</span></div>'
             '<div class="fact"><span class="k">роликов на канале</span><span class="v num">9</span></div></div>')
    body = ('<p class="crumb"><a href="/test/cabinet/">Кабинет</a> / YouTube</p>'
            '<div class="page-top"><h1>' + st("full loading error", "YouTube · канал «Тест»", "span")
            + st("long", f"YouTube · {LONG}", "span") + '</h1><div class="btn-row">'
            f'{a_btn("/test/chat/youtube/", "Обсудить в чате")}{a_btn(CONCEPT_HREF, "Ваше решение: концепция", True)}</div></div>'
            + st("full long", facts) + st("loading", skel(1))
            + '<div class="cab-split mt-s"><section class="stack"><h2>Функции площадки</h2>'
            + st("full", func_rows()) + st("long", func_rows(long=True))
            + st("loading", skel(2) + skel(2) + skel(2))
            + st("error", warn("Функции не загрузились", "Сервер не ответил. Данные на месте — обновите страницу.",
                               a_btn("/test/cabinet/youtube/", "Обновить", True)))
            + f'</section>{own_claude_card()}</div>')
    app_page("/test/cabinet/youtube/", "YouTube · канал «Тест»", "Кабинет площадки YouTube: функции и результаты.",
             body, states=("full", "loading", "error", "long"), wide=True, active="/test/cabinet/")


def page_concept():
    decide = ('<div class="card stack"><h3>Ваше решение</h3>'
              '<p>Концепция задаёт все темы. Выберите — система продолжит с доски идей.</p>'
              '<div class="btn-row btn-row--stack">'
              f'{a_btn("#s=decided", "Утвердить", True)}{a_btn("#s=confirm", "С правками")}'
              f'{a_btn("#s=loading", "Другой вариант")}</div>'
              f'<div class="btn-row">{a_btn("/test/chat/youtube/", "Обсудить в чате")}</div></div>')
    edits = ('<div class="card stack"><h3>Что поправить</h3><div class="field"><label for="ed">Правки словами</label>'
             '<textarea id="ed">Добавить, что ролики — с разбором ошибок, не только удачных случаев.</textarea></div>'
             f'<div class="btn-row">{a_btn("#s=loading", "Отправить правки", True)}{a_btn("#s=full", "Отмена")}</div></div>')
    done = ('<div class="card stack"><span class="badge badge--ok">утверждено</span><h3>Концепция утверждена</h3>'
            '<p>Система собирает доску идей по рубрикам концепции. Она появится в кабинете YouTube.</p>'
            f'<div class="btn-row">{a_btn("/test/cabinet/youtube/", "В кабинет YouTube", True)}'
            f'{a_btn("/test/chat/youtube/", "Обсудить в чате")}</div></div>')
    left = ('<div class="stack"><p class="lede">Система предложила два варианта. Второй точнее совпадает '
            'с анкетой и ДНК: те же слова о практике и случаях.</p>'
            '<div class="facts" style="margin-top:0"><div class="fact"><span class="k">вариантов</span><span class="v num">2</span></div>'
            '<div class="fact"><span class="k">из ДНК</span><span class="v num">5 опор</span></div>'
            '<div class="fact"><span class="k">ниша</span><span class="v num">12 каналов</span></div></div>')
    variants = ('<ul class="cnav"><li><a href="#s=full">Вариант 1</a></li>'
                '<li><a href="#s=full" aria-current="page">Вариант 2</a></li></ul>')
    doc = (f'<article class="card"><div class="panel-h"><b>Концепция</b><span class="badge">вариант 2 из 2</span></div>'
           f'{variants}{{body}}</article>')
    body = ('<p class="crumb"><a href="/test/cabinet/">Кабинет</a> / <a href="/test/cabinet/youtube/">YouTube</a> / Концепция</p>'
            '<div class="page-top"><h1>Концепция канала</h1>'
            + st("full confirm loading error empty long", '<span class="badge badge--wait">ваше решение</span>', "span")
            + st("decided", '<span class="badge badge--ok">утверждено</span>', "span") + '</div>'
            '<div class="split">'
            + st("full long", left + decide + "</div>")
            + st("confirm", left + edits + "</div>")
            + st("decided", left + done + "</div>")
            + st("loading", '<div class="stack">' + skel(4) + "</div>")
            + st("error", '<div class="stack">' + warn("Решение не сохранилось",
                                                        "Связь прервалась. Нажмите ещё раз — второй раз не запишется.",
                                                        a_btn("#s=full", "Повторить", True)) + "</div>")
            + st("empty", '<div class="stack">' + empty("Концепции пока нет.", "готовы ДНК и ниша") + "</div>")
            + st("full confirm decided error", doc.replace("{body}", CONCEPT_DOC))
            + st("long", doc.replace("{body}", CONCEPT_DOC + f"<p>{LONG}. {LONG}. {LONG}.</p>"))
            + st("loading empty", '<article class="card">' + skel(5) + "</article>")
            + "</div>")
    app_page(CONCEPT_HREF, "Концепция канала", "Результат функции «Концепция» и решение автора.", body,
             states=("full", "confirm", "decided", "loading", "error", "empty", "long"), wide=True, active="/test/cabinet/")


# ── Настройки ───────────────────────────────────────────────────────────────

SET_TABS = [("general", "Общие"), ("account", "Аккаунт"), ("privacy", "Приватность"),
            ("billing", "Оплата"), ("usage", "Использование"), ("capabilities", "Возможности"),
            ("connectors", "Коннекторы")]


def settings_page(key, title, body, states=("full",)):
    tabs = "".join(f'<li><a href="/test/settings/{k}/"{" aria-current=\"page\"" if k == key else ""}>{t}</a></li>'
                   for k, t in SET_TABS)
    full = (f'<div class="page-top"><h1>Настройки</h1></div><div class="settings">'
            f'<nav aria-label="Разделы настроек"><ul class="cnav cnav--side">{tabs}</ul></nav>'
            f'<div class="card"><h2>{title}</h2>{body}</div></div>')
    app_page(f"/test/settings/{key}/", f"Настройки · {title}", f"Настройки: {title}.", full,
             states=states, wide=True, active=f"/test/settings/{key}/")


def set_row(label, hint, val):
    h = f'<span class="small muted">{hint}</span>' if hint else ""
    return f'<div class="set-row"><div class="lbl"><b>{label}</b>{h}</div><div class="val">{val}</div></div>'


def switch(on=True, text="", disabled=False):
    return (f'<label class="switch"><input type="checkbox"{" checked" if on else ""}{" disabled" if disabled else ""}>'
            f' {text}</label>')


def dialog(title, text, action_href, action, extra=""):
    """C28: заголовок, текст, поля, «Отмена / Действие»."""
    return ('<div class="dlg" role="dialog" aria-labelledby="dh" style="position:static;margin:var(--space-16) 0">'
            f'<div class="dlg-h"><b id="dh">{title}</b>{a_btn("#s=full", "✕")}</div>'
            f'<div class="dlg-b"><p>{text}</p>{extra}</div>'
            f'<div class="dlg-f">{a_btn("#s=full", "Отмена")}{a_btn(action_href, action, True)}</div></div>')


def usage_bar(label, pct, reset):
    return (f'<div class="use"><p class="small"><b>{label}</b> <span class="meta">использовано {pct}% · {reset}</span></p>'
            f'<svg viewBox="0 0 100 4" preserveAspectRatio="none" width="100%" height="8" aria-hidden="true">'
            f'<rect class="g-track" width="100" height="4" rx="2"/><rect class="g-fill" width="{pct}" height="4" rx="2"/></svg></div>')


def page_settings():
    PAGES["/test/settings/"] = (head("Настройки", "Настройки.") +
                                '<body><meta http-equiv="refresh" content="0; url=/test/settings/general/">'
                                '<p class="wrap"><a href="/test/settings/general/">Настройки → Общие</a></p>'
                                f'{proto(["full"])}{SCRIPT}</body></html>\n')
    profile = ('<h3>Профиль</h3>'
               '<div class="grid2"><div class="field"><label for="pn">Полное имя</label><input id="pn" value="Тест"></div>'
               '<div class="field"><label for="pa">Как к вам обращаться?</label><input id="pa" value="Тест"></div></div>'
               '<div class="field mt-s"><label for="pw">Чем вы занимаетесь?</label><select id="pw">'
               '<option>Личные задачи</option><option>Учёба</option><option>Работа с текстами</option>'
               '<option>Разработка</option></select></div>'
               '<div class="field mt-s"><label for="pp">Личные предпочтения</label>'
               '<textarea id="pp">Отвечай коротко, без лишних вступлений.</textarea>'
               '<p class="hint">Ассистент учитывает это в каждом ответе.</p></div>'
               '<div class="mt"><h3>Вид</h3></div>'
               + set_row("Язык интерфейса", "", '<select class="select" aria-label="Язык"><option>Русский</option>'
                         '<option>English</option></select>')
               + set_row("Тема", "", '<span class="badge">Светлая</span>'))
    settings_page("general", "Общие",
                  st("full", profile + f'<div class="btn-row mt-s">{a_btn("#s=saved", "Сохранить", True)}</div>')
                  + st("saved", profile + '<div class="btn-row mt-s"><span class="badge badge--ok">сохранено</span></div>')
                  + st("error", profile.replace('id="pn" value="Тест"', 'id="pn" value="" aria-invalid="true"')
                       + '<p class="err">Имя не может быть пустым.</p>'
                       + f'<div class="btn-row mt-s">{a_btn("#s=saved", "Сохранить", True)}</div>')
                  + st("loading", skel(4))
                  + st("long", profile.replace("Отвечай коротко, без лишних вступлений.", LONG)),
                  states=("full", "saved", "error", "loading", "long"))

    acc = (set_row("Почта", "test@example.com · вход через Google", '<span class="badge badge--ok">Google</span>')
           + set_row("Выйти на всех устройствах", "Закроет вход везде, кроме этого браузера",
                     a_btn("#s=signout", "Выйти везде"))
           + set_row("Удалить аккаунт", "Чаты, проекты и файлы будут удалены", a_btn("#s=confirm", "Удалить аккаунт")))
    del_dlg = dialog("Удалить аккаунт?", "Удалим чаты, проекты и файлы. Отменить нельзя. Если есть платный план — "
                     "сначала отмените его в разделе «Оплата».", "/test/logout/", "Удалить",
                     '<div class="field"><label for="dc">Введите почту для подтверждения</label>'
                     '<input id="dc" placeholder="test@example.com"></div>')
    out_dlg = dialog("Выйти на всех устройствах?", "Придётся войти заново на телефоне и компьютере.",
                     "/test/logout/", "Выйти везде")
    settings_page("account", "Аккаунт", st("full", acc) + st("confirm", acc + del_dlg) + st("signout", acc + out_dlg)
                  + st("loading", skel(3)), states=("full", "confirm", "signout", "loading"))

    priv = (set_row("Экспорт данных", "Архив чатов и проектов придёт ссылкой на почту",
                    a_btn("#s=exported", "Экспортировать"))
            + set_row("Помогать улучшать improducer", "Разрешить использовать ваши чаты для обучения моделей",
                      switch(False))
            + set_row("Память между чатами", "Ассистент помнит важное из прошлых чатов", switch(True))
            + set_row("Хранение данных", "Удалённые чаты стираются с серверов за 30 дней",
                      '<a href="/privacy.html">Политика конфиденциальности</a>'))
    settings_page("privacy", "Приватность",
                  st("full", priv)
                  + st("exported", note("Экспорт запрошен", "Ссылка на архив придёт на test@example.com. "
                                        "Ссылка действует сутки.") + priv)
                  + st("loading", skel(3)), states=("full", "exported", "loading"))

    invoices = "".join(f'<tr><td class="n">{d}</td><td>{t}</td><td class="n">{s}</td>'
                       f'<td><span class="badge badge--ok">оплачен</span></td></tr>'
                       for d, t, s in (("16.10.2026", "Про · год", "—"),))
    free = (set_row("Бесплатный план", "Чат, YouTube: один канал, кабинет, свой Claude",
                    a_btn("/test/upgrade/", "Повысить план", True)))
    paid = (set_row("План Про", "Оплата за год · следующее списание 16.10.2027",
                    '<span class="badge badge--ok">активен</span>')
            + set_row("Способ оплаты", "Visa •••• 4242", '<button class="btn" type="button">Изменить</button>')
            + '<div class="mt-s"><h3>Счета</h3></div><div class="scroll"><table><thead><tr><th>Дата</th><th>План</th><th>Сумма</th>'
            f'<th>Состояние</th></tr></thead><tbody>{invoices}</tbody></table></div>'
            + set_row("Отменить план", "План работает до конца оплаченного периода", a_btn("#s=canceled", "Отменить")))
    settings_page("billing", "Оплата",
                  st("full", free)
                  + st("paid", note("План Про активен", "Больше использования, доска идей, план и сценарии уже доступны.",
                                    a_btn("/test/new/", "Новый чат", True)) + paid)
                  + st("canceled", note("План отменён", "Про работает до 16.10.2027, потом — бесплатный план.",
                                        a_btn("/test/upgrade/", "Возобновить")) + paid.replace("активен", "до 16.10.2027"))
                  + st("error", warn("Оплата не прошла", "Банк отклонил платёж. Обновите способ оплаты.",
                                     a_btn("/test/upgrade/checkout/", "Оплатить снова", True)) + free)
                  + st("loading", skel(5)),
                  states=("full", "paid", "canceled", "error", "loading"))

    settings_page("usage", "Использование",
                  st("full", usage_bar("Текущая сессия", 24, "сброс через 3 ч 40 мин")
                     + usage_bar("Неделя", 31, "сброс в пн 10:00"))
                  + st("close", usage_bar("Текущая сессия", 88, "сброс через 1 ч 05 мин")
                       + usage_bar("Неделя", 74, "сброс в пн 10:00")
                       + note("Близко к лимиту", "Осталось немного сообщений до сброса.",
                              a_btn("/test/upgrade/", "Повысить план")))
                  + st("limit", usage_bar("Текущая сессия", 100, "сброс в 18:00")
                       + usage_bar("Неделя", 80, "сброс в пн 10:00")
                       + warn("Лимит исчерпан", "Сообщения снова можно отправлять в 18:00.",
                              a_btn("/test/upgrade/", "Повысить план", True)))
                  + st("loading", skel(3)),
                  states=("full", "close", "limit", "loading"))

    caps = [("Артефакты", "Документы, таблицы и код — отдельной панелью", switch(True)),
            ("Анализ данных", "Запуск кода для таблиц и графиков", switch(True)),
            ("Создание файлов", "Документы и таблицы для скачивания", switch(True)),
            ("Поиск в интернете", "Свежие сведения со ссылками", switch(True)),
            ("Память между чатами", "Учитывать прошлые чаты", switch(False)),
            ("Задачи по расписанию", "Доступно на плане Про", '<span class="badge">Про</span>' + switch(False, "", True))]
    cr = "".join(set_row(t, h, v) for t, h, v in caps)
    settings_page("capabilities", "Возможности", st("full", cr) + st("loading", skel(6)), states=("full", "loading"))

    rows_ok = (set_row("YouTube (Google)", "Канал «Тест» · статистика; правки — только после вашего «да» в чате",
                       '<span class="badge badge--ok">подключён</span><button class="btn" type="button">Отключить</button>')
               + "".join(set_row(t, d, '') for t, d, _ in PLATFORMS[1:])
               + set_row("Ваш Claude", "Подключите improducer к своему Claude: Настройки → Коннекторы → "
                         "«Добавить свой коннектор», этот адрес, вход через Google",
                         connector_addr() + a_btn("/test/download/#steps", "Как подключить")))
    custom = set_row("Свой коннектор", "Удалённый сервер по адресу — ваш сервис для чата здесь",
                     a_btn("#s=add", "Добавить свой"))
    add = dialog("Добавить свой коннектор", "Укажите название и адрес удалённого сервера.", "#s=saved", "Добавить",
                 '<div class="field"><label for="cn">Название</label><input id="cn" value="Заметки"></div>'
                 '<div class="field mt-s"><label for="cu">Адрес сервера</label>'
                 '<input id="cu" value="https://notes.example.com/mcp"></div>')
    cat = '<p class="small muted mt-s">Каталог коннекторов — нет в прототипе.</p>'
    settings_page("connectors", "Коннекторы",
                  st("full", rows_ok + custom + cat)
                  + st("add", rows_ok + custom + add)
                  + st("saved", note("Коннектор добавлен", "«Заметки» подключены: в чате — через «＋» → «Коннекторы».")
                       + rows_ok + set_row("Заметки", "notes.example.com · свой коннектор",
                                           '<span class="badge badge--ok">подключён</span>') + custom)
                  + st("error", warn("Не подключено", "Доступ не разрешён или сервер не ответил. Попробуйте ещё раз.",
                                     a_btn("/test/connect/", "Повторить", True)) + rows_ok + custom)
                  + st("loading", skel(4)),
                  states=("full", "add", "saved", "error", "loading"))


# ── Повышение плана, оплата, выход ───────────────────────────────────────────

def page_upgrade():
    def cards(year):
        grp = "plan-y" if year else "plan-m"  # у каждого состояния своя группа: иначе отмечен последний
        pro_price = TBD
        pro_note = "оплата за год" if year else "оплата помесячно"
        return ('<div class="plans plans--2">'
                f'<label class="card plan is-main"><span class="switch"><input type="radio" name="{grp}" checked> Про</span>'
                f'<p class="muted">Для канала, который выходит каждую неделю</p><p class="pp tbd">{pro_price}</p><p class="small muted">{pro_note}</p>'
                '<ul class="ticks"><li>Больше использования</li><li>Доска идей, план, сценарии</li><li>Обложки и выпуск</li></ul></label>'
                f'<label class="card plan"><span class="switch"><input type="radio" name="{grp}"> Макс</span>'
                '<p class="muted">Для нескольких каналов и площадок</p>'
                f'<p class="pp tbd">{TBD}</p><p class="small muted">в месяц</p>'
                '<ul class="ticks"><li>Больше каналов на площадке</li><li>Новые площадки — первыми</li></ul></label>'
                '</div>')

    def period(active):
        return ('<ul class="cnav tabs">'
                f'<li><a href="#s=month"{" aria-current=\"page\"" if active == "month" else ""}>Помесячно</a></li>'
                f'<li><a href="#s=full"{" aria-current=\"page\"" if active == "year" else ""}>За год · выгоднее</a></li></ul>')
    go = f'<div class="btn-row mt-s" style="justify-content:center">{a_btn("/test/upgrade/checkout/", "Перейти к оплате", True)}</div>'
    body = ('<div class="center"><h1>Повысьте план</h1>'
            '<p class="lede">Больше использования и новые возможности. Отменить можно в любой момент.</p></div>'
            + st("full", f'<div class="center mt-s">{period("year")}</div>{cards(True)}{go}')
            + st("month", f'<div class="center mt-s">{period("month")}</div>{cards(False)}{go}')
            + st("loading", '<div class="plans plans--2">' + skel(4) * 2 + "</div>")
            + '<p class="center small muted mt-s">Цены появятся здесь. Оплата — на странице платёжного сервиса.</p>')
    app_page("/test/upgrade/", "Повысить план", "Выбор плана: Про или Макс, помесячно или за год.", body,
             states=("full", "month", "loading"), wide=True, active="/test/upgrade/")

    form = ('<div class="field"><label for="ce">Почта</label><input id="ce" value="test@example.com" disabled></div>'
            '<div class="field mt-s"><label for="cc">Номер карты</label><input id="cc" placeholder="1234 1234 1234 1234" disabled></div>'
            '<div class="grid2 mt-s"><div class="field"><label for="cx">Срок</label><input id="cx" placeholder="ММ / ГГ" disabled></div>'
            '<div class="field"><label for="cv">CVC</label><input id="cv" placeholder="123" disabled></div></div>'
            '<div class="field mt-s"><label for="cn">Страна</label><select id="cn" disabled><option>Казахстан</option></select></div>')
    pay = a_btn("/test/settings/billing/#s=paid", "Оплатить", True)
    checkout = ('<div class="wrap" style="padding-block:var(--space-40)"><div class="split">'
                '<div class="stack"><p class="meta">improducer · оплата</p><h1 class="screen-title">Про · за год</h1>'
                '<div class="facts" style="margin-top:0"><div class="fact"><span class="k">к оплате</span>'
                f'<span class="v">{TBD}</span></div><div class="fact"><span class="k">период</span>'
                '<span class="v">год</span></div></div>'
                f'<p class="small muted">Продлевается раз в год. Отменить — в Настройках → Оплата.</p>{a_btn("/test/upgrade/", "← Назад")}</div>'
                '<div class="card stack">'
                + st("full", form + f'<div class="btn-row">{pay}</div>')
                + st("error", warn("Карта отклонена", "Банк не подтвердил платёж, деньги не списаны. Попробуйте другую карту.")
                     + form + f'<div class="btn-row">{pay}</div>')
                + st("loading", skel(4))
                + '<p class="small muted">Макет страницы платёжного сервиса: поля выключены, деньги не списываются.</p>'
                "</div></div></div>")
    bare_page("/test/upgrade/checkout/", "Оплата", "Макет страницы платёжного сервиса.", checkout,
              states=("full", "error", "loading"))


def page_logout():
    body = ('<div class="centered"><div class="box"><div class="card stack">'
            '<h1 class="screen-title">Вы вышли</h1><p>Чаты и проекты на месте. Войти снова — тем же способом.</p>'
            f'<div class="btn-row">{a_btn("/test/login/", "Войти", True)}{a_btn("/test/", "На главную")}</div>'
            "</div></div></div>")
    bare_page("/test/logout/", "Вы вышли", "Выход из аккаунта.", body)


# ── Опись ───────────────────────────────────────────────────────────────────

OPIS_SCREENS = [
    # id, их экран, их адрес, наш адрес, что взяли, чего нет и почему, состояния
    ("S01", "Выдача поиска", "google.com/search?q=claude", None,
     "—", "Без аналога: выдача — чужая страница, в прототип не входит.", "—"),
    ("S02", "Главная", "claude.com/", "/test/",
     "Ничего: главная — это вход (владелец 17.10: на главной только вход, остальное — вода)",
     "Та же страница, что /test/login/: вариант 06 «Горизонт», вход через Google. Героя, планов, вопросов и "
     "примера чата нет; Продукт, Цены, Помощь — по своим адресам.", "заполнено · загрузка · ошибка"),
    ("S03", "Продукт", "claude.com/product/overview", "/test/product/",
     "Полоса раздела, заголовок по центру с двумя кнопками, блоки ниже",
     "Россыпи картинок и видео нет: функции YouTube — плитками, площадки — карточками, два пути работы", "заполнено"),
    ("S04", "Цены", "claude.com/pricing", "/test/pricing/",
     "Вкладки «Для себя / Команды / API», три карточки с ценой, пояснением и «Всё из …, плюс», "
     "таблица сравнения с поиском и кнопками в шапке, вопросы",
     "Цен нет: у «Бесплатно» — 0 $, у остальных — «цена появится». Возможности — наши (чат, площадки, кабинет, "
     "коннекторы, свой Claude). Вкладка API — коннектор и ключ API. Карточки «Предприятие» нет: у образца она ведёт "
     "в отдел продаж, а в продукте людей нет. Групп сравнения одна, без сворачивания.", "заполнено (вкладки якорями)"),
    ("S05", "Скачать", "claude.com/download", "/test/download/",
     "Заголовок с главной кнопкой, строки «платформа → действие», вторая колонка с подробностью, вопросы",
     "Своё: страница «В своём Claude» — В браузере → Открыть; В своём Claude → коннектор, адрес и 3 шага; "
     "Телефон — скоро. QR и файлов нет: приложений у нас нет", "заполнено"),
    ("S06", "Помощь", "support.claude.com/en/", "/test/help/",
     "Поиск с ⌘K, частые статьи строками, коллекции плитками", "Бокового меню разделов нет; открывается одна статья",
     "заполнено · пусто · загрузка"),
    ("S07", "Вход", "claude.ai/login", "/test/login/",
     "Ничего: свой вход, не копия (владелец 17.10 — копии чужих входов выглядят как скам)",
     "Пока взят вариант 06 «Горизонт» из /test/vhod/ (временно, владелец 17.10): линия во всю ширину посередине, над ней "
     "знак со словом, под ней «Продолжить с Google» и согласие. Своего текста нет, почты нет", "заполнено · загрузка · ошибка"),
    ("S08", "Письмо и код", "claude.ai/login (шаг 2)", None,
     "—", "Убрано (владелец 17.10): вход только через Google, писем и кодов нет.", "—"),
    ("S09", "Каталог коннекторов", "claude.com/marketplace/connectors-plugins", None,
     "—", "Без аналога: каталога в прототипе нет; подключение — через «Добавить свой» в Настройках → Коннекторы", "—"),
    ("S10", "Статья помощи", "support.claude.com/en/articles/8114491", "/test/help/start/",
     "Крошки, H1, разделы, оглавление справа, «помогла?»", "—", "заполнено · длинный"),
    ("S11", "Первый запуск", "claude.ai/onboarding (шаги)", None,
     "—", "Убрано (владелец 17.10): после настоящего входа Google сразу приложение (/test/new/), шагов «имя», "
     "«возраст и условия», «первая площадка» нет", "—"),
    ("S12", "Новый чат", "claude.ai/new", "/test/new/",
     "Боковая панель C14; знак и приветствие по центру; поле ввода с «+» и выбором модели; подсказки под ним",
     "В панели свой пункт «Кабинет»; в «+» — «Файлы», «Площадки: YouTube ✓», «Коннекторы»; подсказки про канал. "
     "Боковая панель не сворачивается; «Артефакты» — без страницы", "заполнено · лимит · длинный · загрузка"),
    ("S13", "Чат", "claude.ai/chat/<id>", "/test/chat/",
     "Реплика справа плашкой, ответ текстом с действиями (копировать, повторить, оценка), поле внизу",
     "Ответ не печатается вживую — состояние «ответ идёт» показано отдельно. Поле ввода на ≥820 прижато к низу",
     "заполнено · ответ идёт · ошибка · длинный (лимит длины) · лимит · с инструментом"),
    ("S14", "Недавние", "claude.ai/recents", "/test/recents/",
     "Поиск, строки «название · последнее сообщение», «Выбрать», новый чат", "—",
     "заполнено · выбор нескольких · длинный · пусто · ничего не найдено · загрузка"),
    ("S15", "Проекты", "claude.ai/projects", "/test/projects/",
     "Сетка карточек (название, описание, «изменён»), «Новый проект», поиск, сортировка",
     "Все карточки ведут на один проект-пример", "заполнено · длинный · пусто · загрузка"),
    ("S16", "Проект", "claude.ai/project/<id>", "/test/project/primer/",
     "Слева поле ввода и чаты проекта, справа инструкции, знания и ёмкость", "Файлы не загружаются",
     "заполнено · пустой проект · знания почти заполнены · загрузка"),
    ("S17", "Артефакт", "панель справа в чате", "/test/chat/",
     "Панель справа: заголовок, версия, «Просмотр / Код», копировать, скачать, закрыть; карточка в ответе",
     "На телефоне панель под чатом, не на весь экран", "готов · создаётся"),
    ("S18", "Настройки: общие", "claude.ai/settings/general", "/test/settings/general/",
     "Вкладки слева в порядке образца, профиль, предпочтения, вид, «Сохранить»", "Тема только светлая",
     "заполнено · сохранено · ошибка · загрузка · длинный"),
    ("S19", "Настройки: оплата", "claude.ai/settings/billing", "/test/settings/billing/",
     "Бесплатный план с «Повысить»; платный: план, способ, счета, отмена до конца периода", "—",
     "бесплатный · оплачено · отменён · ошибка · загрузка"),
    ("S20", "Настройки: использование", "claude.ai/settings/usage", "/test/settings/usage/",
     "Полосы «сессия» и «неделя» со временем сброса", "—", "норма · близко к лимиту · лимит · загрузка"),
    ("S21", "Настройки: возможности", "claude.ai/settings/capabilities", "/test/settings/capabilities/",
     "Строки функций с переключателем; недоступное на плане", "—", "заполнено · загрузка"),
    ("S22", "Настройки: коннекторы", "claude.ai/settings/connectors", "/test/settings/connectors/",
     "Строки коннекторов: подключён, не подключён, ошибка; «Добавить свой» с адресом",
     "Каталога нет. Свои строки: YouTube (Google) — подключён; Telegram, Instagram — строки с описанием; «Ваш Claude» — адрес и "
     "«Скопировать»", "заполнено · добавить свой · добавлен · ошибка · загрузка"),
    ("S23", "Повысить план", "claude.ai/upgrade", "/test/upgrade/",
     "Карточки Про / Макс, помесячно / за год, «Перейти к оплате»", "Цен нет: «цена появится»; Макс — одна карточка",
     "за год · помесячно · загрузка"),
    ("—", "Оплата (платёжный сервис)", "checkout.stripe.com", "/test/upgrade/checkout/",
     "Слева сумма, справа поля карты и «Оплатить»", "Макет: поля выключены, деньги не списываются",
     "заполнено · карта отклонена · загрузка"),
    ("S24", "Лимит исчерпан", "плашка над полем ввода", "/test/new/#s=limit",
     "Плашка «до ЧЧ:ММ · Повысить план» над полем, поле недоступно; то же в чате", "Недельного лимита плашкой нет",
     "лимит сессии"),
    ("S25", "Меню аккаунта и выход", "поповер внизу боковой панели", "/test/logout/",
     "Почта, Настройки, Язык, Помощь, Посмотреть планы, Выйти; экран после выхода", "Язык не переключается", "заполнено"),
    ("—", "Окно согласия Google (YouTube)", "OAuth стороннего сервиса", "/test/connect/",
     "Что запрашивается, «Разрешить / Отклонить»",
     "Макет окна Google: статистика канала; правки — только после «да» в чате. «Разрешить» → кабинет YouTube",
     "заполнено · загрузка · ошибка"),
    ("—", "Кабинет", "без аналога (свой экран)", "/test/cabinet/",
     "Сетка плиток, как «Проекты» образца", "Свой экран: площадки YouTube (подключён, 6 из 12), Telegram и Instagram — "
     "плитки с описанием, «Добавить площадку» → Коннекторы", "заполнено · пусто · загрузка · ошибка · длинный"),
    ("—", "Кабинет площадки YouTube", "без аналога (свой экран)", "/test/cabinet/youtube/",
     "Раскладка проекта образца: слева основное, справа карточка", "Свой экран: 3 факта, 12 функций со состоянием, "
     "«в чате: …» и ссылкой; справа «Работать в своём Claude»", "заполнено · загрузка · ошибка · длинный"),
    ("—", "Результат: концепция", "без аналога (свой экран)", "/test/cabinet/youtube/koncepciya/",
     "Крошки, H1, две колонки", "Свой экран: варианты, «Ваше решение» — Утвердить / С правками / Другой вариант, "
     "«Обсудить в чате»", "заполнено · с правками · решение принято · загрузка · ошибка · пусто · длинный"),
    ("—", "Чат про канал", "claude.ai/chat/<id>", "/test/chat/youtube/",
     "Раскладка S13 и панель артефакта S17", "Артефакт — концепция; на панели «Открыть в кабинете»",
     "заполнено · ответ идёт · ошибка · длинный"),
    ("S26", "Настройки: аккаунт", "claude.ai/settings/account", "/test/settings/account/",
     "Выйти везде и удалить аккаунт — с подтверждением в диалоге", "—",
     "заполнено · подтверждение удаления · выйти везде · загрузка"),
    ("S27", "Настройки: приватность", "claude.ai/settings/privacy", "/test/settings/privacy/",
     "Экспорт данных, обучение на чатах, память, хранение", "—", "заполнено · экспорт запрошен · загрузка"),
]

OPIS_PATHS = [
    ("F01", "Найти, войти, начать",
     "S01 → S07 → Google → S11 (телефон, 18+, имя) → S12 · ≈7 кликов (через сайт +2)",
     "/test/ → «Попробовать improducer» → /test/login/ → «Продолжить с Google» → настоящий вход Google (как у "
     "кабинета) → /test/new/ · 2 клика + Google. Шагов «имя», «возраст», «первая площадка» нет, входа почтой нет "
     "(владелец 17.10). YouTube — потом в приложении: Кабинет → «Подключить YouTube через Google» → /test/connect/",
     "/test/", "Решение: настоящий вход Google — и сразу приложение. Телефона нет"),
    ("F02", "Первая работа", "S12 → ввод → S13 (идёт → готов) → S17 → S14 · 3 клика",
     "/test/new/ → подсказка «Что дальше по каналу?» → /test/chat/youtube/ (ответ и концепция в панели) → «Открыть в "
     "кабинете» → /test/cabinet/youtube/koncepciya/ → «Утвердить» → #s=decided · 3 клика",
     "/test/new/", "Ответ не печатается: «идёт» — отдельное состояние"),
    ("F03", "Работа в проекте", "S12 → S15 → «Новый проект» → S16 → S13 · 4 клика",
     "/test/new/ → «Проекты» → /test/projects/ → «＋ Новый проект» → /test/project/primer/#s=empty → «Отправить» → /test/chat/ · 3 клика",
     "/test/projects/", "—"),
    ("F04", "Подключить инструмент", "S12 → S25 → S22 → «Добавить свой» (URL) → OAuth → S13 · 5 кликов",
     "/test/new/ → «＋» → «Коннекторы» → /test/settings/connectors/ → «Добавить свой» → «Добавить» → #s=saved · 4 клика",
     "/test/settings/connectors/", "Каталога (S09) нет; окно согласия /test/connect/ теперь только для YouTube"),
    ("F05", "Упёрся в лимит → заплатил", "S13 → S24 → «Повысить» → S23 → оплата → S19 → S12 · 4 клика + оплата",
     "/test/new/#s=limit → «Повысить план» → /test/upgrade/ → «Перейти к оплате» → /test/upgrade/checkout/ → «Оплатить» → "
     "/test/settings/billing/#s=paid → «Новый чат» → /test/new/ · 4 клика",
     "/test/new/#s=limit", "Оплата — макет; суммы нет: цены не заданы"),
    ("F06", "Настройки и выход", "S25 → S18 → S20 → S21 → S26 → «Выйти» → S07 · 5 кликов",
     "меню аккаунта → /test/settings/general/ → «Использование» → «Возможности» → «Аккаунт» → меню → «Выйти» → "
     "/test/logout/ → «Войти» → /test/login/ · 6 кликов",
     "/test/settings/general/", "Экран «Вы вышли» между выходом и входом"),
    ("F07", "Помощь", "S02 → S06 → S10 · 2 клика",
     "/test/new/ → меню аккаунта → «Помощь» → /test/help/ → статья → /test/help/start/ · 3 клика",
     "/test/help/", "—"),
    ("F08", "Работать в своём Claude", "S02 → S05 → файл · 2 клика",
     "/test/ → «Подключить коннектор →» → /test/download/#claude → 3 шага и адрес · 1 клик",
     "/test/download/", "Вместо файла приложения — адрес коннектора"),
    ("F09", "Кабинет → результат", "без аналога (свой путь)",
     "любая страница приложения → «Кабинет» → /test/cabinet/ → YouTube → /test/cabinet/youtube/ → «Концепция» → "
     "/test/cabinet/youtube/koncepciya/ → «Обсудить в чате» → /test/chat/youtube/ · 4 клика",
     "/test/cabinet/", "—"),
]

DECISIONS = [
    ("Людей в продукте нет", "Нет разговоров, созвонов, записи, листа ожидания и ручного включения. Всё делают код и модель."),
    ("Лицо и приложение — как у Claude", "Сайт и основной интерфейс повторяют образец; главный экран приложения — чат."),
    ("Кабинет — кнопка, не главная", "«Кабинет» — пункт боковой панели. В нём площадки; у каждой свой кабинет: функции "
     "и готовые страницы результатов."),
    ("Площадки", "YouTube, Telegram, Instagram стоят на своих местах обычным текстом с описанием, без «скоро» (владелец 17.10). Кабинет и функции есть у YouTube; у Telegram и Instagram страниц в прототипе нет."),
    ("Два пути работы", "Чат на improducer.co или свой Claude через коннектор https://connect.improducer.co/mcp. "
     "Результаты в обоих случаях — в одном кабинете."),
    ("Коннекторы — как у Claude", "Подключаются и здесь: Настройки → Коннекторы, «Добавить свой»."),
    ("Первый запуск без телефона", "Имя → 18+ и условия → первая площадка. Вход через Google уже подтверждает человека."),
    ("После «Разрешить» — кабинет YouTube", "Не новый чат: человек сразу видит функции канала и что от него ждут."),
    ("Цены не заданы", "У «Бесплатно» — 0 $, у остальных планов — «цена появится»; в оплате суммы нет."),
    ("6 из 12 готово", "Двенадцать функций YouTube; у «Теста» готовы подключение, анкета, фото, ДНК, ниша и аналитика "
     "уже вышедших роликов; концепция ждёт решения."),
    ("Поле ввода без названий моделей", "Под полем — «Проект» и глубина (Быстро · Средне · Глубоко); модель выбирает система. "
     "Голос — только диктовка, без голосового режима (владелец 17.10)."),
    ("Боковая панель — как у Claude", "Пункты «Артефакты», «Расписание», «Настроить» остаются как в образце "
     "(владелец 17.10)."),
    ("Главная — только вход", "На /test/ та же страница, что /test/login/: пока вариант 06 «Горизонт» (временно), вход "
     "только Google. Своего текста, ссылки на свой Claude и Apple нет (владелец 17.10)."),
]

DESIGN_TODO = [
    ("Оболочка приложения: боковая панель + рабочая область", "≥1180 — панель слева; меньше — полоса сверху и меню по кнопке",
     "component.app.side-width = 292 (сейчас --tile-min + --space-32)"),
    ("Шапка сайта", "обычная · липкая · телефон — меню по кнопке", "без новых значений: --nav-height, --sticky-bar-*"),
    ("Поле ввода (C15)", "пусто · текст · недоступно (лимит) · «+» · глубина",
     "component.composer: радиус = --radius-card, высота = --field-textarea-min; стрелка — красная (исключение README)"),
    ("Плашка лимита (C24)", "лимит сессии", "цвета --color-status-warn-*"),
    ("Сообщение чата (C16)", "реплика · ответ · идёт · ошибка · длинный", "component.message.author-bg = --color-bg-sunken"),
    ("Панель артефакта (C20)", "создаётся · готов · версия", "две колонки по --breakpoint-desktop"),
    ("Карточка плана (C04)", "обычная · выделенная", "без новых значений"),
    ("Таблица сравнения (C05)", "обычная · телефон — прокрутка", "без новых значений"),
    ("Аккордеон вопросов (C06)", "свёрнут · раскрыт · фокус", "component.disclosure.marker"),
    ("Поповер (меню аккаунта, «+», меню на телефоне)", "открыт · закрыт · фокус", "component.popover.shadow = --shadow-popover"),
    ("Строка коннектора (C22)", "не подключён · подключён · ошибка · требует план", "set-row + badge"),
    ("Полоса использования (C23)", "норма · близко · исчерпан", "g-track / g-fill"),
    ("Пустое место «заполнится, когда…»", "пусто", "пунктирная граница --color-border-control"),
    ("Заготовки загрузки", "загрузка", "фон --color-bg-sunken, радиус --radius-8"),
    ("Плитка площадки", "подключена · без подключения · добавить", "tile + badge; «скоро» — пунктир --color-border-control"),
    ("Строка функции площадки", "готово · ваше решение · ждёт", "row + badge; «ваше решение» — --nav-active-*"),
    ("Адрес коннектора с «Скопировать»", "обычный", "code на --color-bg-sunken, радиус --radius-control"),
    ("Полоса площадок на сайте", "название + описание", "без новых значений"),
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
        rid = sid if sid != "—" else ours.strip("/").replace("/", "-")
        screens.append(
            f'<div class="row" data-id="{rid}"><div class="row-top"><span class="rank">{sid}</span><div class="rhead">'
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
        ("Первый запуск нового аккаунта (S11)", "новых аккаунтов не заводим; по статьям 8287232, 8114491, 13117299"),
        ("«Лимит исчерпан» (S24)", "не вызвать без расхода лимита владельца; по статье 11647753"),
        ("Оплата Stripe", "платить нельзя; по статье 8325609"),
        ("Выдача на 390 и 820", "по заданию — одна выдача, один снимок 1440"),
        ("Telegram и Instagram", "в кабинете, на сайте и в первом запуске — названием с описанием, без «скоро»; страниц у них нет — площадок ещё нет"),
        ("Страницы результатов, кроме концепции", "в прототипе одна страница-пример — концепция; у остальных функций "
         "кабинета ссылка заменена пометкой «нет в прототипе» или «заполнится, когда …»"),
    ]
    nd = "".join(f'<tr><td>{E(a)}</td><td>{E(b)}</td></tr>' for a, b in notdone)
    decisions = "".join(
        f'<div class="row" data-id="D{i:02d}"><div class="row-top"><span class="rank">D{i:02d}</span><div class="rhead">'
        f'<p class="rtitle">{E(t)}</p><p class="rmeta">{E(d)}</p></div></div>'
        '<div class="marks"><button class="mbtn" type="button" data-mark="ok">✓</button>'
        '<button class="mbtn" type="button" data-mark="no">✕</button>'
        '<button class="mbtn" type="button" data-mark="wrong">⊘</button>'
        '<textarea class="cmt" rows="1" placeholder="Комментарий"></textarea></div></div>'
        for i, (t, d) in enumerate(DECISIONS, 1))
    commits = json.loads((HERE / "commits.json").read_text()) if (HERE / "commits.json").exists() else []
    cm = "".join(f'<li><code>{E(c["sha"])}</code> {E(c["msg"])}</li>' for c in commits) or "<li>заполнится после выкладки</li>"
    body = f"""
<div class="wrap opis" style="padding-top:var(--space-page-top)">
<header class="page-head" style="padding-top:0">{wordmark()}
<p class="crumb">Прототип · опись</p>
<h1>Путь клиента: Claude → improducer</h1>
<p class="lede">Первый прототип нашего фронтенда: путь клиента Claude — те же экраны, порядок, переходы, блоки и
состояния — в дизайн-системе improducer, поверх — видение владельца: площадки, кабинет, два пути работы.
Пользователь — выдуманный «Тест». Вход — настоящий Google, остальные формы ничего не отправляют, оплаты нет.</p>
<div class="btn-row mt-s"><a class="btn btn--primary" href="/test/">Открыть прототип</a>
<button class="btn" type="button" data-act="copy-marks">Скопировать отметки</button></div>
<pre class="quote small" data-copy-out hidden></pre>
{note("Отметки — только в этом браузере",
      "Сайт статический: ✓ · ✕ · ⊘ и комментарии хранятся в этом браузере (localStorage) и до нас не доходят. "
      "Нажмите «Скопировать отметки» и вставьте в чат — вердикты собираем там.")}
</header>

<section><h2>1. Решения</h2><p class="muted">Принципы прототипа — по ним сверять каждый экран.</p>
{decisions}</section>

<section><h2>2. Пути</h2><p class="muted">Их путь против нашего: экраны по порядку и клики. Ссылка — первая страница пути.</p>
{paths}</section>

<section><h2>3. Экраны</h2><p class="muted">Совпадение раскладки — imgdiff.py, режим layout: края, не цвет;
снимки с домена 16.10, на 390 / 820 / 1440 (прошлая сборка: баллы не пересчитаны).</p>
{note("Почему все баллы ниже 75",
      "Мера считает плотность краёв в клетках сетки, а края на странице — это в основном буквы. Тексты у нас свои, "
      "поэтому баллы 3–23. Проверка меры: две разные страницы самого образца друг с другом дают 7–28 "
      "(цены ↔ помощь 19, цены ↔ продукт 28), на сетке 4 и 6 колонок — то же: наши пары в среднем 25–30, "
      "чужие 26–33. Значит, мера не отличает похожую раскладку от непохожей, когда текст разный. Поднять балл можно "
      "только переносом текста и картинок образца — по заданию нельзя. Раскладку сверяем глазами: строки ниже и "
      "проход по путям, отметка ✕ — правка.")}
{"".join(screens)}</section>

<section><h2>4. Не снято / нет и почему</h2><div class="scroll"><table><thead><tr><th>Что</th><th>Почему и чем заменили</th></tr></thead>
<tbody>{nd}</tbody></table></div></section>

<section><h2>5. На правку _design/</h2><p class="muted">В прототипе новых значений нет: раскладка — test/assets/test.css
на переменных tokens.css. Это стоит закрепить компонентами, если прототип принят.</p>
<div class="scroll"><table><thead><tr><th>Компонент</th><th>Состояния</th><th>Токен</th></tr></thead><tbody>{todo}</tbody></table></div></section>

<section><h2>6. Инструкция</h2>
<h3>Где лежат файлы</h3>
<ul><li>Сайт: репозиторий <code>ImproducerCo/improducerco.github.io</code>, на Маке — <code>~/.improducer/site</code>.</li>
<li>Страницы: <code>test/&lt;путь&gt;/index.html</code>, общий вид — <code>test/assets/</code>.</li>
<li>Исходник: <code>test/_build/build.py</code> (тексты и разметка), <code>test.css</code>, <code>test.js</code>.
Папку <code>_build</code> GitHub Pages не публикует. Сборка удаляет из <code>test/</code> всё, кроме
<code>_build</code> и <code>assets</code>, и пишет страницы заново.</li>
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
                            + f"{SCRIPT}</body></html>\n")


# ── Варианты входа /test/vhod/ ───────────────────────────────────────────────
# 17.10 владелец: нынешний вход не нравится, нужны 15–20 вариантов с чистого листа по входам сильных площадок;
# выберет один. Из первых двадцати понравился только 01 (Google), 02–20 сняты (история — git, сайт 7456592).
# Правила владельца 17.10: только Google; знак и название вместе (wordmark) и один раз на странице; своего текста нет —
# ни заголовка, ни подзаголовка; по центру, не слева. Потом владелец снял и 01, 21–26: раскладки «как у Google, Apple…»
# выглядят как скам или копия — никого не копировать (сайт e450026 — история). Сейчас 10 своих страниц: идея у каждой
# своя (пропуск, кадр, объектив…), из общего — только правила выше. Каждый вариант — своя раскладка и подача, форма и её состояния общие (login_states()).
# Разбор образцов — ~/Desktop/improducer/работа/2026-10-17_vhod/разбор.md. Свой вид — vhod.css (только на этих
# страницах), превью для каталога — _build/vhod/NN.jpg (снимок 1728×1080), копирует сборка.
VHOD_CSS = HERE / "vhod.css"
VHOD_PREV = HERE / "vhod"
VHOD = []  # (номер, образец, что взято, функция → (класс body, разметка))


def vhod(n, ref, took):
    def reg(fn):
        VHOD.append((n, ref, took, fn))
        return fn
    return reg


def vx_head(title, desc):
    css = f'<link rel="stylesheet" href="/test/assets/vhod.css?v={ver(VHOD_CSS)}">\n</head>'
    return head(title, desc).replace("</head>", css, 1)


def vx_mark(cls="vx-mark"):
    """Основной знак как есть: mark.svg без перекраски, только размер."""
    return f'<img class="{cls}" src="/test/assets/logo/mark.svg" alt="improducer">'


def vx_legal(sep=""):
    links = ['<a href="/test/help/">Помощь</a>', '<a href="/privacy.html">Конфиденциальность</a>',
             '<a href="/terms.html">Условия</a>']
    return sep.join(links)


def vx_title(text, cls="vx-title"):
    """Заголовок без красной черты (по центру ей не место): для экранных чтецов — H1, на экране — абзац."""
    return f'<h1 class="visually-hidden">Вход в improducer</h1><p class="{cls}">{text}</p>'


def page_vhod():
    n_all = len(VHOD)
    for i, (n, ref, took, fn) in enumerate(VHOD):
        cls, body = fn()
        prev, nxt = VHOD[i - 1][0], VHOD[(i + 1) % n_all][0]
        nav = (f'<a href="/test/vhod/">Все варианты</a><a href="/test/vhod/{prev}/">← Вариант {prev}</a>'
               f'<a href="/test/vhod/{nxt}/">Вариант {nxt} →</a>')
        pr = proto(list(LOGIN_STATES)).replace('<a href="/test/opis/">Опись и инструкция</a>', nav)
        PAGES[f"/test/vhod/{n}/"] = (vx_head(f"Вход · вариант {n}", f"Вариант входа {n}: по образцу {ref}.")
                                     + f'<body class="vx vx-{n} {cls}">{body}{pr}{SCRIPT}</body></html>\n')
    cards = []
    for n, ref, took, _ in VHOD:
        img = (f'<img src="/test/assets/vhod/{n}.jpg?v={ver(VHOD_PREV / f"{n}.jpg")}" alt="" loading="lazy">'
               if (VHOD_PREV / f"{n}.jpg").exists() else '<span class="vxc-none">снимка ещё нет</span>')
        cards.append(f'<a class="vxc" href="/test/vhod/{n}/"><span class="vxc-img">{img}</span>'
                     f'<span class="vxc-top"><span class="meta">{n}</span><b>{E(ref)}</b></span>'
                     f'<span class="vxc-took">{E(took)}</span><span class="vxc-go">Открыть →</span></a>')
    body = (f'<header class="bare-head">{wordmark()}</header><main class="vxcat">'
            f'<h1>Вход: {n_all} вариантов</h1>'
            f'<p class="lede">{n_all} своих страниц входа, придуманных под improducer, — без копий чужих входов. У всех '
            'одно и то же: знак со словом один раз, кнопка Google, согласие и ссылки; своего текста нет, всё по центру. '
            'Отметки ✓ · ✕ · ⊘ и '
            'комментарий — на <a href="https://pult.improducer.co/#front/vhod">пульте, вкладка «Фронтенд»</a>.</p>'
            f'<div class="vxgrid">{"".join(cards)}</div></main>')
    PAGES["/test/vhod/"] = (vx_head("Вход: варианты", "Варианты страницы входа improducer на выбор.")
                            + f'<body class="site">{body}{SCRIPT}</body></html>\n')


def vx_foot(cls="vx-foot"):
    """Нижняя строка — только ссылки. Своего текста нет."""
    return f'<footer class="{cls}"><nav class="vx-links">{vx_legal()}</nav></footer>'


VX_H1 = '<h1 class="visually-hidden">Вход в improducer</h1>'


def vx_form(cls="vx-form"):
    return f'<div class="{cls}">{login_states()}</div>'


@vhod("01", "Пропуск", "Вход — это пропуск: карточка-билет, сверху знак со словом, линия отрыва с вырезами по краям, "
                       "под ней кнопка Google")
def vx_pass():
    return "", ('<main class="ps-main"><div class="ps-ticket">'
                f'<div class="ps-top">{VX_H1}{wordmark()}</div><div class="ps-cut" aria-hidden="true"></div>'
                f'{vx_form("ps-bot")}</div>{vx_foot()}</main>')


@vhod("02", "Видоискатель", "Авторы снимают — страница как кадр в видоискателе: уголки рамки 16:9, внутри знак со словом "
                            "и кнопка")
def vx_viewfinder():
    corners = "".join(f'<i class="vf-c vf-{c}"></i>' for c in ("tl", "tr", "bl", "br"))
    return "", ('<main class="vf-main"><div class="vf-frame">'
                f'<span aria-hidden="true">{corners}</span>'
                f'<div class="vf-in">{VX_H1}{wordmark()}{vx_form()}</div></div>{vx_foot()}</main>')


@vhod("03", "Кадр 9:16", "Вертикальная карточка в формате коротких роликов: знак со словом посередине, кнопка внизу")
def vx_vertical():
    return "", ('<main class="vt-main"><div class="vt-card">'
                f'<div class="vt-mark">{VX_H1}{wordmark()}</div>{vx_form()}</div>{vx_foot()}</main>')


@vhod("04", "Объектив", "Круг с тонким вторым кольцом, как линза: знак со словом в центре круга, кнопка под ним")
def vx_lens():
    return "", (f'<main class="ob-main"><div class="ob-ring">{VX_H1}{wordmark()}</div>{vx_form()}{vx_foot()}</main>')


@vhod("05", "Ось", "Тонкая вертикальная линия через весь экран; знак со словом и кнопка стоят на ней, линия уходит "
                   "вверх и вниз")
def vx_axis():
    return "", (f'<main class="ax-main"><div class="ax-mark">{VX_H1}{wordmark()}</div>{vx_form("vx-form ax-form")}'
                f'</main>{vx_foot()}')


@vhod("06", "Горизонт", "Тонкая линия во всю ширину ровно по середине экрана: над ней крупный знак со словом, под ней кнопка")
def vx_horizon():
    return "", ('<main class="hz-main">'
                f'<div class="hz-top">{VX_H1}{wordmark()}</div><div class="hz-line" aria-hidden="true"></div>'
                f'<div class="hz-bot">{vx_form()}</div></main>{vx_foot()}')


@vhod("07", "Паспарту", "Белое поле в рамке по краю экрана, как фото в паспарту; знак со словом и кнопка в центре, "
                        "ссылки — в разрыве нижней линии рамки")
def vx_mat():
    return "", ('<main class="pp-main"><div class="pp-frame">'
                f'{VX_H1}{wordmark()}{vx_form()}{vx_foot("pp-foot")}</div></main>')


@vhod("08", "Сетка", "Тонкая сетка на фоне, гаснущая к краям; по центру белый блок ровно по клеткам — знак со словом "
                     "и кнопка")
def vx_grid():
    return "", ('<main class="gd-main"><div class="gd-block">'
                f'{VX_H1}{wordmark()}{vx_form()}</div></main>{vx_foot()}')


@vhod("09", "Плакат", "Только знак со словом очень крупно, как афиша, и спокойная кнопка под ним")
def vx_poster():
    return "", (f'<main class="pt-main">{VX_H1}{wordmark()}{vx_form()}</main>{vx_foot()}')


@vhod("10", "Монтаж", "Под знаком со словом — тонкая монтажная линейка с делениями и красной меткой воспроизведения; "
                      "под линейкой кнопка")
def vx_timeline():
    return "", (f'<main class="tl-main">{VX_H1}{wordmark()}'
                '<div class="tl-ruler" aria-hidden="true"><i class="tl-head"></i></div>'
                f'{vx_form()}</main>{vx_foot()}')


def main():
    check_labels()
    copy_assets()
    for fn in (page_home, page_product, page_pricing, page_download, page_help, page_help_start,
               page_login, page_connect, page_new, page_chat, page_chat_youtube, page_recents,
               page_projects, page_project, page_cabinet, page_cabinet_youtube, page_concept,
               page_settings, page_upgrade, page_logout, page_opis, page_vhod):
        fn()
    # Старое не остаётся: всё, кроме исходника и общего вида, собирается заново.
    for d in TEST.iterdir():
        if d.is_dir() and d.name not in KEEP:
            shutil.rmtree(d)
    for path, text in PAGES.items():
        out = TEST / path.removeprefix("/test/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(f"страниц: {len(PAGES)}")


if __name__ == "__main__":
    main()
