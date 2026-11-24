"""Собирает index.html из содержимого, которое отдала CRM (или из initial в schema.json).

Использование как модуль: build.render(content, resolve_image) -> str
resolve_image(значение_поля) -> путь к файлу картинки на сайте.
"""
import re
from html import escape


def e(v):
    return escape(str(v if v is not None else ""), quote=True)


def g(d, k):
    return d.get(k) or ""


def lst(d, k):
    return d.get(k) or []


HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&amp;display=swap">
<style>
html{{scroll-behavior:smooth}}
body{{margin:0;background:#FAF6EF}}
a{{color:#1B2A4A}}a:hover{{color:#0F1A30}}
summary{{cursor:pointer;list-style:none}}
summary::-webkit-details-marker{{display:none}}
@media (max-width: 640px){{
  h1{{font-size:36px !important}}
  h2{{font-size:30px !important}}
  .hero-photo{{height:380px !important}}
  .pay-card{{padding:28px !important}}
}}
</style>
</head>
<body>
<div style="width: 100%; font-family: Manrope, system-ui, sans-serif; color: #222222; background: #FAF6EF; font-size: 18px; line-height: 1.6">
"""

TAIL = """
</div>
</body>
</html>
"""

SVG = 'width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
ICONS = {
    "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
    "cart": '<circle cx="9" cy="20" r="1.5"></circle><circle cx="18" cy="20" r="1.5"></circle><path d="M2 3h3l2.5 12h11.5l2-8H6.5"></path>',
    "building": '<path d="M3 21h18M5 21V8l7-5 7 5v13M10 21v-6h4v6"></path>',
    "phone": '<rect x="6" y="2" width="12" height="20" rx="2"></rect><path d="M11 18h2"></path>',
    "home": '<path d="M3 11l9-8 9 8M5 10v10h14V10"></path>',
    "museum": '<path d="M2 9h20M4 9v11h16V9M12 2l9 7H3z"></path>',
    "check": '<path d="M9 11l3 3 8-8M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"></path>',
}
WA_ICON = '<path d="M21 12a9 9 0 0 1-13.5 7.8L3 21l1.3-4.4A9 9 0 1 1 21 12z"></path>'
TG_ICON = '<path d="M22 3L2 11l7 2 2 7 4-5 5 4z"></path>'

BTN = "text-decoration: none; min-height: 44px; box-sizing: border-box; display: inline-flex; align-items: center"


def link(url, style, label, extra=""):
    return f'<a href="{e(url)}" style="{style}"{extra}>{label}</a>'


def header(d, img):
    nav = "".join(link(i.get("url"), "text-decoration: none", e(i.get("label"))) for i in lst(d, "nav"))
    if g(d, "phone"):
        nav += link(g(d, "phone_url") or "#", "text-decoration: none; color: #1B2A4A", e(d["phone"]))
    if g(d, "cta_label"):
        nav += link(g(d, "cta_url") or "#", "text-decoration: none; background: #E8833A; color: #1B2A4A; padding: 12px 20px; border-radius: 999px; font-weight: 800; min-height: 44px; box-sizing: border-box; display: inline-flex; align-items: center", e(d["cta_label"]))
    tag = f'<span style="font-size: 14px; color: #55607A">{e(d["tagline"])}</span>' if g(d, "tagline") else ""
    return f"""<header style="background: #FAF6EF; border-bottom: 1px solid #E8DFD0">
<div style="max-width: 1200px; margin: 0 auto; padding: 18px 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px">
<a href="/" style="text-decoration: none; color: inherit; display: flex; align-items: center; gap: 12px">
<svg width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="#1B2A4A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="20" cy="15" r="11"></circle><path d="M20 26v10M14 36h12M20 26l-5-6M20 22l5-5"></path></svg>
<div style="display: flex; flex-direction: column; line-height: 1.2"><span style="font-weight: 800; font-size: 22px; color: #1B2A4A">{e(g(d, "brand"))}</span>{tag}</div>
</a>
<nav style="display: flex; flex-wrap: wrap; align-items: center; gap: 20px; font-size: 16px; font-weight: 600">{nav}</nav>
</div>
</header>"""


def hero(d, img):
    b1 = b2 = ""
    if g(d, "btn1_label"):
        b1 = (f'<a href="{e(g(d, "btn1_url") or "#")}" style="text-decoration: none; background: #E8833A; color: #1B2A4A; padding: 18px 28px; border-radius: 999px; font-weight: 800; font-size: 18px; display: inline-flex; align-items: center; gap: 10px; min-height: 44px; box-sizing: border-box">\n'
              f'<svg {SVG.format(s=22, c="#1B2A4A")}>{WA_ICON}</svg>\n{e(d["btn1_label"])}</a>')
    if g(d, "btn2_label"):
        b2 = (f'<a href="{e(g(d, "btn2_url") or "#")}" style="text-decoration: none; border: 2px solid #FFFFFF; color: #FFFFFF; padding: 16px 26px; border-radius: 999px; font-weight: 700; font-size: 18px; display: inline-flex; align-items: center; gap: 10px; min-height: 44px; box-sizing: border-box">\n'
              f'<svg {SVG.format(s=22, c="#FFFFFF")}>{TG_ICON}</svg>\n{e(d["btn2_label"])}</a>')
    badge = f'<span style="align-self: flex-start; background: rgba(255,255,255,0.12); padding: 8px 16px; border-radius: 999px; font-size: 15px; font-weight: 600">{e(d["badge"])}</span>' if g(d, "badge") else ""
    text = f'<p style="margin: 0; font-size: 20px; color: #D6DCEA; max-width: 620px">{e(d["text"])}</p>' if g(d, "text") else ""
    note = f'<p style="margin: 0; font-size: 15px; color: #B9C2D6">{e(d["note"])}</p>' if g(d, "note") else ""
    photo = ""
    if g(d, "photo"):
        photo = f'<div class="hero-photo" style="flex: 1 1 380px; min-width: 0; height: 520px; border-radius: 28px; overflow: hidden; background: #2C3D63"><img src="{e(img(d["photo"]))}" alt="{e(g(d, "photo_alt"))}" style="width: 100%; height: 100%; object-fit: cover; object-position: center 40%; display: block"></div>'
    trust = "".join(f'<span>{e(i.get("text"))}</span>' for i in lst(d, "trust"))
    trust_bar = f"""<div style="background: #152238">
<div style="max-width: 1200px; margin: 0 auto; padding: 20px 24px; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; font-size: 15px; font-weight: 600; color: #E3E8F2">{trust}</div>
</div>""" if trust else ""
    return f"""<section style="background: #1B2A4A; color: #FFFFFF">
<div style="max-width: 1200px; margin: 0 auto; padding: 80px 24px; display: flex; flex-wrap: wrap; gap: 48px; align-items: center">
<div style="flex: 999 1 520px; min-width: 0; display: flex; flex-direction: column; gap: 24px">
{badge}
<h1 style="margin: 0; font-size: 56px; line-height: 1.1; font-weight: 800; letter-spacing: -0.02em">{e(g(d, "title"))}</h1>
{text}
<div style="display: flex; flex-wrap: wrap; gap: 12px">
{b1}
{b2}
</div>
{note}
</div>
{photo}
</div>
{trust_bar}
</section>"""


def pains(d, img):
    cards = "\n".join(f'<div style="background: #FFFFFF; border-radius: 20px; padding: 28px; font-size: 18px">{e(i.get("text"))}</div>' for i in lst(d, "items"))
    concl = f'<p style="margin: 0; font-size: 26px; line-height: 1.4; font-weight: 700; color: #1B2A4A; max-width: 820px">{e(d["conclusion"])}</p>' if g(d, "conclusion") else ""
    return f"""<section>
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px">
{cards}
</div>
{concl}
</div>
</section>"""


def compare(d, img):
    def ul(items, extra=""):
        li = "\n".join(f"<li>{e(i.get('text'))}</li>" for i in items)
        return f'<ul style="margin: 0; padding-left: 22px; display: flex; flex-direction: column; gap: 10px{extra}">\n{li}\n</ul>'
    tip = ""
    if g(d, "tip_title") or g(d, "tip_text"):
        btn = link(g(d, "tip_btn_url") or "#", "text-decoration: none; color: #FFFFFF; border: 2px solid #FFFFFF; padding: 14px 24px; border-radius: 999px; font-weight: 700; " + BTN.split("; ", 1)[1], e(d["tip_btn_label"])) if g(d, "tip_btn_label") else ""
        tip = f"""<div style="background: #1B2A4A; color: #FFFFFF; border-radius: 24px; padding: 32px 36px; display: flex; flex-wrap: wrap; gap: 24px; align-items: center; justify-content: space-between">
<div style="flex: 999 1 420px; min-width: 0">
<h3 style="margin: 0 0 8px; font-size: 22px">{e(g(d, "tip_title"))}</h3>
<p style="margin: 0; color: #D6DCEA">{e(g(d, "tip_text"))}</p>
</div>
{btn}
</div>"""
    return f"""<section style="background: #E3ECF7">
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); gap: 24px">
<div style="background: #FFFFFF; border-radius: 24px; padding: 36px; display: flex; flex-direction: column; gap: 16px">
<h3 style="margin: 0; font-size: 24px; color: #1B2A4A">{e(g(d, "yes_title"))}</h3>
{ul(lst(d, "yes_items"))}
</div>
<div style="background: #FFFFFF; border-radius: 24px; padding: 36px; display: flex; flex-direction: column; gap: 16px">
<h3 style="margin: 0; font-size: 24px; color: #55607A">{e(g(d, "no_title"))}</h3>
{ul(lst(d, "no_items"), "; color: #3A4256")}
</div>
</div>
{tip}
</div>
</section>"""


def services(d, img):
    cards = []
    for i in lst(d, "items"):
        icon = ICONS.get(i.get("icon") or "chat", ICONS["chat"])
        cards.append(f"""<div style="background: #FFFFFF; border-radius: 20px; padding: 28px; display: flex; flex-direction: column; gap: 12px">
<div style="width: 56px; height: 56px; border-radius: 50%; background: #F3E3C3; display: flex; align-items: center; justify-content: center"><svg {SVG.format(s=28, c="#1B2A4A")}>{icon}</svg></div>
<h3 style="margin: 0; font-size: 20px; color: #1B2A4A">{e(i.get("title"))}</h3>
<p style="margin: 0; font-size: 16px; color: #3A4256">{e(i.get("text"))}</p>
</div>""")
    sub = f'<p style="margin: 0; color: #55607A">{e(d["subtitle"])}</p>' if g(d, "subtitle") else ""
    return f"""<section>
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<div style="display: flex; flex-direction: column; gap: 12px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
{sub}
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px">
{chr(10).join(cards)}
</div>
</div>
</section>"""


def steps(d, img):
    items = []
    for n, i in enumerate(lst(d, "items"), 1):
        items.append(f"""<li style="background: #FAF6EF; border-radius: 20px; padding: 28px; display: flex; flex-direction: column; gap: 12px">
<span style="width: 48px; height: 48px; border-radius: 50%; background: #1B2A4A; color: #FFFFFF; font-weight: 800; font-size: 20px; display: flex; align-items: center; justify-content: center">{n}</span>
<h3 style="margin: 0; font-size: 20px; color: #1B2A4A">{e(i.get("title"))}</h3>
<p style="margin: 0; font-size: 16px; color: #3A4256">{e(i.get("text"))}</p>
</li>""")
    return f"""<section id="how" style="background: #FFFFFF">
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
<ol style="margin: 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px">
{chr(10).join(items)}
</ol>
</div>
</section>"""


def coordinator(d, img):
    lis = []
    for i in lst(d, "bullets"):
        bold = f"<strong>{e(i['bold'])}</strong> " if i.get("bold") else ""
        lis.append(f"<li>{bold}{e(i.get('text'))}</li>")
    photo = f'<div style="flex: 1 1 340px; min-width: 0; height: 480px; border-radius: 28px; overflow: hidden; background: #F3E3C3"><img src="{e(img(d["photo"]))}" alt="{e(g(d, "photo_alt"))}" loading="lazy" style="width: 100%; height: 100%; object-fit: cover; object-position: center 20%; display: block"></div>' if g(d, "photo") else ""
    return f"""<section>
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-wrap: wrap; gap: 48px; align-items: center">
{photo}
<div style="flex: 999 1 520px; min-width: 0; display: flex; flex-direction: column; gap: 20px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
<ul style="margin: 0; padding-left: 22px; display: flex; flex-direction: column; gap: 10px">
{chr(10).join(lis)}
</ul>
</div>
</div>
</section>"""


def selection(d, img):
    cards = "\n".join(f'<div style="background: #24365C; border-radius: 20px; padding: 28px"><h3 style="margin: 0 0 8px; font-size: 20px">{e(i.get("title"))}</h3><p style="margin: 0; font-size: 16px; color: #D6DCEA">{e(i.get("text"))}</p></div>' for i in lst(d, "items"))
    sub = f'<p style="margin: 0; color: #D6DCEA; font-size: 20px">{e(d["subtitle"])}</p>' if g(d, "subtitle") else ""
    return f"""<section style="background: #1B2A4A; color: #FFFFFF">
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<div style="display: flex; flex-direction: column; gap: 12px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800">{e(g(d, "title"))}</h2>
{sub}
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px">
{cards}
</div>
</div>
</section>"""


def payment(d, img):
    lis = "\n".join(f"<li>{e(i.get('text'))}</li>" for i in lst(d, "bullets"))
    tiles = []
    for i in lst(d, "currencies"):
        t = i.get("text") or ""
        if len(t) <= 2:
            tiles.append(f'<div style="background: #FAF6EF; border-radius: 16px; padding: 24px; text-align: center; font-size: 32px; font-weight: 800; color: #1B2A4A">{e(t)}</div>')
        else:
            tiles.append(f'<div style="background: #FAF6EF; border-radius: 16px; padding: 24px; text-align: center; font-size: 18px; font-weight: 700; color: #1B2A4A; display: flex; align-items: center; justify-content: center">{e(t)}</div>')
    return f"""<section>
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px">
<div class="pay-card" style="background: #FFFFFF; border-radius: 28px; padding: 48px; display: flex; flex-wrap: wrap; gap: 40px; align-items: center">
<div style="flex: 999 1 480px; min-width: 0; display: flex; flex-direction: column; gap: 16px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
<ul style="margin: 0; padding-left: 22px; display: flex; flex-direction: column; gap: 10px">
{lis}
</ul>
</div>
<div style="flex: 1 1 280px; min-width: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px">
{chr(10).join(tiles)}
</div>
</div>
</div>
</section>"""


def prices(d, img):
    cards = []
    for i in lst(d, "items"):
        num = f'<span style="font-size: 44px; font-weight: 800; color: #1B2A4A; line-height: 1">{e(i.get("number"))}</span>'
        body = f'{num}<h3 style="margin: 0; font-size: 20px; color: #1B2A4A">{e(i.get("title"))}</h3><p style="margin: 0; font-size: 16px; color: #3A4256">{e(i.get("text"))}</p>'
        if i.get("badge"):
            cards.append(f'<div style="border: 3px solid #1B2A4A; border-radius: 24px; padding: 32px; display: flex; flex-direction: column; gap: 12px; position: relative"><span style="position: absolute; top: -16px; left: 24px; background: #E8833A; color: #1B2A4A; font-size: 14px; font-weight: 800; padding: 4px 14px; border-radius: 999px">{e(i["badge"])}</span>{body}</div>')
        else:
            cards.append(f'<div style="border: 2px solid #E8DFD0; border-radius: 24px; padding: 32px; display: flex; flex-direction: column; gap: 12px">{body}</div>')
    btns = ""
    if g(d, "btn1_label"):
        btns += link(g(d, "btn1_url") or "#", "text-decoration: none; background: #1B2A4A; color: #FFFFFF; padding: 16px 28px; border-radius: 999px; font-weight: 700; min-height: 44px; box-sizing: border-box; display: inline-flex; align-items: center", e(d["btn1_label"])) + "\n"
    if g(d, "btn2_label"):
        btns += link(g(d, "btn2_url") or "#", "text-decoration: none; background: #E8833A; color: #1B2A4A; padding: 16px 28px; border-radius: 999px; font-weight: 800; min-height: 44px; box-sizing: border-box; display: inline-flex; align-items: center", e(d["btn2_label"]))
    sub = f'<p style="margin: 0; color: #55607A">{e(d["subtitle"])}</p>' if g(d, "subtitle") else ""
    return f"""<section id="prices" style="background: #FFFFFF">
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<div style="display: flex; flex-direction: column; gap: 12px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
{sub}
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px">
{chr(10).join(cards)}
</div>
<div style="display: flex; flex-wrap: wrap; gap: 12px">
{btns}
</div>
</div>
</section>"""


def stories(d, img):
    phone = ""
    if g(d, "phone_image"):
        phone = f"""<figure style="margin: 0; flex: 0 0 auto; display: flex; flex-direction: column; gap: 14px; align-items: center; margin-inline: auto">
<div style="width: 320px; max-width: 100%; height: 600px; border-radius: 44px; background: #1B2A4A; padding: 14px; box-sizing: border-box">
<div style="width: 100%; height: 100%; border-radius: 32px; overflow: hidden; background: #1A1626">
<img src="{e(img(d["phone_image"]))}" alt="{e(g(d, "phone_alt"))}" loading="lazy" style="width: 100%; height: 100%; object-fit: cover; object-position: top; display: block">
</div>
</div>
<figcaption style="font-size: 16px; color: #3A4256; text-align: center; max-width: 320px">{e(g(d, "phone_caption"))}</figcaption>
</figure>"""
    others = []
    for i in lst(d, "items"):
        others.append(f"""<figure style="margin: 0; display: flex; flex-direction: column; gap: 12px">
<div style="background: #FFFFFF; border-radius: 24px; padding: 12px; box-shadow: 0 8px 24px rgba(27,42,74,0.08)">
<img src="{e(img(i.get("image")))}" alt="{e(i.get("alt"))}" loading="lazy" style="width: 100%; height: auto; display: block; border-radius: 14px">
</div>
<figcaption style="font-size: 16px; color: #3A4256">{e(i.get("caption"))}</figcaption>
</figure>""")
    sub = f'<p style="margin: -24px 0 0; color: #55607A">{e(d["subtitle"])}</p>' if g(d, "subtitle") else ""
    return f"""<section>
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
{sub}
<div style="display: flex; flex-wrap: wrap; gap: 40px; align-items: flex-start">
{phone}
<div style="flex: 999 1 480px; min-width: 0; display: flex; flex-direction: column; gap: 28px">
{chr(10).join(others)}
</div>
</div>
</div>
</section>"""


def faq(d, img):
    items = []
    for i in lst(d, "items"):
        op = " open" if i.get("open") else ""
        items.append(f'<details{op} style="background: #FFFFFF; border-radius: 16px; padding: 20px 24px"><summary style="font-weight: 700; font-size: 19px; color: #1B2A4A">{e(i.get("question"))}</summary><p style="margin: 12px 0 0; color: #3A4256">{e(i.get("answer"))}</p></details>')
    return f"""<section id="faq">
<div style="max-width: 900px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 32px">
<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>
<div style="display: flex; flex-direction: column; gap: 12px">
{chr(10).join(items)}
</div>
</div>
</section>"""


def contacts(d, img):
    btns = []
    for i in lst(d, "buttons"):
        if i.get("style") == "outline":
            st = "text-decoration: none; border: 2px solid #FFFFFF; color: #FFFFFF; padding: 16px 26px; border-radius: 999px; font-weight: 700; "
        else:
            st = "text-decoration: none; background: #E8833A; color: #1B2A4A; padding: 18px 28px; border-radius: 999px; font-weight: 800; "
        btns.append(link(i.get("url"), st + BTN.split("; ", 1)[1], e(i.get("label"))))
    qr = ""
    if g(d, "qr_image"):
        qr = f"""<div style="display: flex; align-items: center; gap: 16px; color: #B9C2D6; font-size: 15px">
<div style="width: 96px; height: 96px; background: #FFFFFF; border-radius: 12px; padding: 8px; box-sizing: border-box"><img src="{e(img(d["qr_image"]))}" alt="{e(g(d, "qr_alt"))}" style="width: 100%; height: 100%; display: block; image-rendering: pixelated"></div>
<span style="text-align: left; max-width: 220px">{e(g(d, "qr_text"))}</span>
</div>"""
    text = f'<p style="margin: 0; color: #D6DCEA; font-size: 20px">{e(d["text"])}</p>' if g(d, "text") else ""
    return f"""<section id="contacts" style="background: #1B2A4A; color: #FFFFFF">
<div style="max-width: 1000px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; align-items: center; gap: 28px; text-align: center">
<h2 style="margin: 0; font-size: 44px; line-height: 1.15; font-weight: 800">{e(g(d, "title"))}</h2>
{text}
<div style="display: flex; flex-wrap: wrap; gap: 12px; justify-content: center">
{chr(10).join(btns)}
</div>
{qr}
</div>
</section>"""


def footer(d, img):
    links = "\n".join(f'<a href="{e(i.get("url"))}" style="color: #D6DCEA">{e(i.get("label"))}</a>' for i in lst(d, "links"))
    return f"""<footer style="background: #152238; color: #B9C2D6; font-size: 14px">
<div style="max-width: 1200px; margin: 0 auto; padding: 32px 24px; display: flex; flex-wrap: wrap; gap: 16px 32px; justify-content: space-between">
<span>{e(g(d, "copyright"))}</span>
<div style="display: flex; flex-wrap: wrap; gap: 20px">
{links}
</div>
</div>
</footer>"""


RENDERERS = {
    "header": header, "hero": hero, "pains": pains, "compare": compare, "services": services,
    "steps": steps, "coordinator": coordinator, "selection": selection, "payment": payment,
    "prices": prices, "stories": stories, "faq": faq, "contacts": contacts, "footer": footer,
}



def page_intro(d, img):
    sub = f'<p style="margin: 0; font-size: 24px; line-height: 1.5; color: #D6DCEA; max-width: 640px">{e(d["subtitle"])}</p>' if g(d, "subtitle") else ""
    photo = ""
    if g(d, "photo"):
        photo = f'<div class="hero-photo" style="flex: 1 1 420px; min-width: 0; height: 480px; border-radius: 28px; overflow: hidden; background: #2C3D63"><img src="{e(img(d["photo"]))}" alt="{e(g(d, "photo_alt"))}" style="width: 100%; height: 100%; object-fit: cover; object-position: center 40%; display: block"></div>'
    return f"""<section style="background: #1B2A4A; color: #FFFFFF">
<div style="max-width: 1200px; margin: 0 auto; padding: 80px 24px; display: flex; flex-wrap: wrap; gap: 56px; align-items: center">
<div style="flex: 1 1 460px; min-width: 0; display: flex; flex-direction: column; gap: 24px">
<h1 style="margin: 0; font-size: 64px; line-height: 1.08; font-weight: 800; letter-spacing: -0.02em">{e(g(d, "title"))}</h1>
{sub}
</div>
{photo}
</div>
</section>"""


def rich_text(body):
    """Абзацы — через пустую строку; «## » — подзаголовок; строки с «- » — маркированный список."""
    out = []
    for para in re.split(r"\n\s*\n", (body or "").strip()):
        lines = [x.strip() for x in para.split("\n") if x.strip()]
        if not lines:
            continue
        if len(lines) == 1 and lines[0].startswith("## "):
            out.append(f'<h3 style="margin: 16px 0 0; font-size: 26px; line-height: 1.3; color: #1B2A4A">{e(lines[0][3:])}</h3>')
        elif all(x.startswith("- ") for x in lines):
            li = "".join(f"<li>{e(x[2:])}</li>" for x in lines)
            out.append(f'<ul style="margin: 0; padding-left: 22px; display: flex; flex-direction: column; gap: 8px">{li}</ul>')
        else:
            out.append(f'<p style="margin: 0; color: #3A4256">{"<br>".join(e(x) for x in lines)}</p>')
    return "\n".join(out)


def text_block(d, img):
    title = f'<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(d["title"])}</h2>' if g(d, "title") else ""
    return f"""<section>
<div style="max-width: 900px; margin: 0 auto; padding: 64px 24px; display: flex; flex-direction: column; gap: 20px">
{title}
{rich_text(g(d, "body"))}
</div>
</section>"""


CHECK = f'<svg {SVG.format(s=20, c="#E8833A")} style="flex: none; margin-top: 4px"><path d="M5 12l5 5L20 7"></path></svg>'


def tariffs(d, img):
    head = f'<h2 style="margin: 0; font-size: 40px; line-height: 1.2; font-weight: 800; color: #1B2A4A">{e(g(d, "title"))}</h2>'
    sub = f'<p style="margin: 0; color: #55607A">{e(d["subtitle"])}</p>' if g(d, "subtitle") else ""
    chooser = ""
    if lst(d, "chooser"):
        cards = "".join(
            f'<div style="background: #FFFFFF; border-radius: 16px; padding: 18px 22px; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 16px; color: #55607A">{e(i.get("question"))}</span><span style="font-weight: 800; font-size: 18px; color: #1B2A4A">→ {e(i.get("answer"))}</span></div>'
            for i in lst(d, "chooser"))
        chooser = f"""<div style="display: flex; flex-direction: column; gap: 14px">
<h3 style="margin: 0; font-size: 22px; color: #1B2A4A">{e(g(d, "chooser_title") or "Не знаете, что выбрать?")}</h3>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px">{cards}</div>
</div>"""
    packs = []
    for p in lst(d, "items"):
        hl = bool(p.get("badge"))
        border = "3px solid #1B2A4A" if hl else "2px solid #E8DFD0"
        badge = f'<span style="position: absolute; top: -16px; left: 24px; background: #E8833A; color: #1B2A4A; font-size: 14px; font-weight: 800; padding: 4px 14px; border-radius: 999px">{e(p["badge"])}</span>' if hl else ""
        period = f'<span style="font-size: 15px; font-weight: 600; color: #55607A">{e(p["period"])}</span>' if p.get("period") else ""
        tag = f'<p style="margin: 0; font-size: 18px; line-height: 1.4; font-weight: 700; color: #1B2A4A">{e(p["tagline"])}</p>' if p.get("tagline") else ""
        aud = f'<p style="margin: 0; font-size: 16px; color: #3A4256"><strong style="color: #1B2A4A">Для кого:</strong> {e(p["audience"])}</p>' if p.get("audience") else ""
        lis = "".join(f'<li style="display: flex; gap: 10px">{CHECK}<span>{e(x.get("text"))}</span></li>' for x in lst(p, "bullets"))
        ul = f'<ul style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 10px; font-size: 17px; color: #3A4256">{lis}</ul>' if lis else ""
        res = f'<div style="background: #FAF6EF; border-left: 4px solid #E8833A; border-radius: 12px; padding: 14px 16px; font-size: 16px; font-weight: 600; color: #1B2A4A">{e(p["result"])}</div>' if p.get("result") else ""
        btn = ""
        if p.get("btn_label"):
            st = "background: #E8833A; color: #1B2A4A" if hl else "background: #1B2A4A; color: #FFFFFF"
            btn = f'<div style="margin-top: auto; padding-top: 8px">{link(p.get("btn_url") or "#", f"text-decoration: none; {st}; padding: 14px 24px; border-radius: 999px; font-weight: 800; justify-content: center; width: 100%; " + BTN.split("; ", 1)[1], e(p["btn_label"]))}</div>'
        packs.append(f"""<div style="background: #FFFFFF; border: {border}; border-radius: 24px; padding: 32px; display: flex; flex-direction: column; gap: 14px; position: relative">
{badge}<span style="font-size: 52px; font-weight: 800; color: #1B2A4A; line-height: 1">{e(p.get("price"))}</span>
{period}
<h3 style="margin: 0; font-size: 24px; color: #1B2A4A">{e(p.get("name"))}</h3>
{tag}
{aud}
{ul}
{res}
{btn}
</div>""")
    note = f'<p style="margin: 0; font-size: 18px; color: #3A4256">{e(d["note"])}</p>' if g(d, "note") else ""
    btns = []
    for i in lst(d, "buttons"):
        s = i.get("style")
        base = {"outline": "border: 2px solid #1B2A4A; color: #1B2A4A; padding: 14px 26px; font-weight: 700",
                "dark": "background: #1B2A4A; color: #FFFFFF; padding: 16px 28px; font-weight: 700"}.get(s, "background: #E8833A; color: #1B2A4A; padding: 16px 28px; font-weight: 800")
        btns.append(link(i.get("url"), f"text-decoration: none; {base}; border-radius: 999px; " + BTN.split("; ", 1)[1], e(i.get("label"))))
    bottom = f'<div style="display: flex; flex-wrap: wrap; gap: 12px">{"".join(btns)}</div>' if btns else ""
    return f"""<section id="prices">
<div style="max-width: 1200px; margin: 0 auto; padding: 96px 24px; display: flex; flex-direction: column; gap: 40px">
<div style="display: flex; flex-direction: column; gap: 12px">
{head}
{sub}
</div>
{chooser}
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(480px, 100%), 1fr)); gap: 28px; align-items: stretch">
{chr(10).join(packs)}
</div>
{note}
{bottom}
</div>
</section>"""


# ───────────── цвет блока ─────────────
NAVY_TEXT = "#1B2A4A"
THEMES = {  # название в редакторе: (цвет фона, тёмный ли)
    "Кремовый": ("#FAF6EF", False), "Белый": ("#FFFFFF", False), "Голубой": ("#E3ECF7", False),
    "Песочный": ("#F3E3C3", False), "Зелёный": ("#E4EFE4", False), "Персиковый": ("#FBE8D8", False),
    "Тёмно-синий": ("#1B2A4A", True),
}
BG_OPTIONS = ["Как сейчас"] + list(THEMES)
DARK_DEFAULT = {"hero", "selection", "contacts", "page_intro"}
ORANGE = "background: #E8833A; color: #1B2A4A"


def _light_to_dark(h):
    h = h.replace(ORANGE, "\0ORANGE\0")
    for a, c in (("color: #1B2A4A", "color: #FFFFFF"), ("color: #3A4256", "color: #D6DCEA"), ("color: #55607A", "color: #B9C2D6")):
        h = h.replace(a, c)
    h = h.replace("background: #FFFFFF", "background: #24365C").replace("background: #FAF6EF", "background: #24365C")
    h = h.replace("border: 2px solid #E8DFD0", "border: 2px solid #3A4C75").replace("border: 3px solid #1B2A4A", "border: 3px solid #FFFFFF")
    h = h.replace("border: 2px solid #1B2A4A", "border: 2px solid #FFFFFF")
    h = h.replace("background: #1B2A4A; color: #FFFFFF; border-radius: 24px", "background: #24365C; color: #FFFFFF; border-radius: 24px")
    h = h.replace("background: #1B2A4A; padding: 14px", "background: #0F1A30; padding: 14px")
    h = h.replace("background: #1B2A4A; color: #FFFFFF", "background: #FFFFFF; color: #1B2A4A")
    return h.replace("\0ORANGE\0", ORANGE)


def _dark_to_light(h):
    h = h.replace(ORANGE, "\0ORANGE\0")
    for a, c in (("color: #FFFFFF", "color: #1B2A4A"), ("color: #D6DCEA", "color: #3A4256"), ("color: #B9C2D6", "color: #55607A"),
                 ("color: #E3E8F2", "color: #3A4256"), ("border: 2px solid #FFFFFF", "border: 2px solid #1B2A4A"),
                 ('stroke="#FFFFFF"', 'stroke="#1B2A4A"'), ("background: #24365C", "background: #FFFFFF"),
                 ("background: #152238", "background: #EDE5D6"), ("background: rgba(255,255,255,0.12)", "background: rgba(27,42,74,0.08)")):
        h = h.replace(a, c)
    return h.replace("\0ORANGE\0", ORANGE)


def apply_style(btype, html, data):
    """Цвет фона блока (bg) и якорь для ссылок (anchor)."""
    m = re.search(r"<section\b[^>]*>", html)
    if not m:
        return html
    tag, rest, theme = m.group(0), html[m.end():], g(data, "bg")
    if theme in THEMES:
        color, dark = THEMES[theme]
        default_dark = btype in DARK_DEFAULT
        if dark and not default_dark:
            rest = _light_to_dark(rest)
        elif not dark and default_dark:
            rest = _dark_to_light(rest)
        if not dark and not default_dark:
            # карточки внутри должны отличаться от фона
            if color == "#FFFFFF":
                rest = rest.replace("background: #FFFFFF", "background: #FAF6EF")
            elif color == "#FAF6EF" and btype == "steps":
                rest = rest.replace("background: #FAF6EF", "background: #FFFFFF")
        style = f"background: {color}; color: {'#FFFFFF' if dark else NAVY_TEXT}" if (dark or default_dark) else f"background: {color}"
        if 'style="' in tag:
            tag = re.sub(r'style="[^"]*"', f'style="{style}"', tag, count=1)
        else:
            tag = tag[:-1] + f' style="{style}">'
    anchor = re.sub(r"[^a-z0-9_-]", "", g(data, "anchor").lower())
    if anchor:
        tag = re.sub(r'\sid="[^"]*"', "", tag, count=1)
        tag = tag[:-1] + f' id="{anchor}">'
    return tag + rest


RENDERERS.update({"page_intro": page_intro, "text": text_block, "tariffs": tariffs})
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
RESERVED = {"images", "assets", "static"}
ANCHORS = ("how", "prices", "faq", "contacts")


def _fix_anchor_links(value, key=""):
    """На внутренних страницах ссылки вида «#prices» должны вести на главную: «/#prices»."""
    if isinstance(value, dict):
        return {k: _fix_anchor_links(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_fix_anchor_links(v, key) for v in value]
    if isinstance(value, str) and key.endswith("url") and re.fullmatch(r"#[A-Za-z0-9_-]+", value):
        return "/" + value
    return value


def _dedupe_ids(html):
    for a in ANCHORS:
        needle = f' id="{a}"'
        first = html.find(needle)
        if first >= 0:
            cut = first + len(needle)
            html = html[:cut] + html[cut:].replace(needle, "")
    return html


def _page_html(head_data, header_block, footer_block, blocks, img, is_main):
    def data(b):
        d = b.get("data") or {}
        return d if is_main or b["type"] not in ("header", "footer") else _fix_anchor_links(d)
    parts = [HEAD.format(title=e(g(head_data, "page_title") or g(head_data, "brand")), description=e(g(head_data, "page_description")))]
    if header_block:
        parts.append(header(data(header_block), img))
    for b in blocks:
        parts.append(apply_style(b["type"], RENDERERS[b["type"]](data(b), img), data(b)))
    if footer_block:
        parts.append(footer(data(footer_block), img))
    return _dedupe_ids("\n\n".join(parts)) + TAIL


def render_site(content, resolve_image=lambda v: v):
    """Возвращает {путь: html}: "" — главная страница, "tarify" — страница /tarify/ и т. д."""
    all_blocks = [b for b in content.get("blocks", []) if b.get("type") in RENDERERS or b.get("type") == "page"]
    header_block = next((b for b in all_blocks if b["type"] == "header" and not b.get("hidden")), None)
    footer_block = next((b for b in all_blocks if b["type"] == "footer" and not b.get("hidden")), None)
    head_main = (header_block or {}).get("data") or {}

    groups = [{"slug": "", "meta": head_main, "hidden": False, "blocks": []}]
    for b in all_blocks:
        if b["type"] in ("header", "footer"):
            continue
        if b["type"] == "page":
            d = b.get("data") or {}
            groups.append({"slug": g(d, "slug").strip().strip("/").lower(), "meta": d, "hidden": bool(b.get("hidden")), "blocks": []})
        elif not b.get("hidden"):
            groups[-1]["blocks"].append(b)

    pages, seen = {}, set()
    for grp in groups:
        slug = grp["slug"]
        if grp["hidden"] or slug in seen:
            continue
        if slug and (not SLUG.match(slug) or slug in RESERVED):
            continue
        seen.add(slug)
        pages[slug] = _page_html(grp["meta"], header_block, footer_block, grp["blocks"], resolve_image, slug == "")
    return pages


def render(content, resolve_image=lambda v: v):
    """Главная страница."""
    return render_site(content, resolve_image)[""]
