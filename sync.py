#!/usr/bin/env python3
"""Забирает опубликованное содержимое из CRM и пересобирает index.html сайта.

Запускается раз в минуту (systemd timer). Если CRM недоступна — сайт остаётся как был.
Настройки — переменные окружения: CRM_API, SITE_KEY, SITE_TOKEN, WEBROOT.
"""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build  # noqa: E402

API = os.environ.get("CRM_API", "").rstrip("/")
KEY = os.environ.get("SITE_KEY", "")
TOKEN = os.environ.get("SITE_TOKEN", "")
WEBROOT = os.environ.get("WEBROOT", "/var/www/drevo-zhizny.ru")
STATE = os.environ.get("STATE_FILE", "/var/lib/drevo-sync/state.json")
ASSET_WIDTH = 1600


def log(msg):
    print(msg, flush=True)


def call(method, path, body=None, raw=False):
    req = urllib.request.Request(f"{API}/public/sites/{KEY}/{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=30) as r:
        payload = r.read()
    return payload if raw else json.loads(payload.decode("utf-8"))


def load_state():
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def main():
    if not (API and KEY and TOKEN):
        log("Не заданы CRM_API, SITE_KEY или SITE_TOKEN")
        return 2
    with open(os.path.join(HERE, "schema.json"), encoding="utf-8") as fh:
        schema_text = fh.read()
    schema = json.loads(schema_text)
    state = load_state()

    try:
        digest = hashlib.sha256(schema_text.encode("utf-8")).hexdigest()
        if state.get("schema") != digest:
            call("PUT", "schema", schema)
            state["schema"] = digest
            save_state(state)
            log("Описание блоков отправлено в CRM")
        published = call("GET", "published")
    except (urllib.error.URLError, OSError, ValueError) as err:
        log(f"CRM недоступна, сайт не меняю: {err}")
        return 0

    content = published.get("content") or schema.get("initial") or {"blocks": []}

    # загружаем фото, которые редактор положил в CRM
    ids = set(re.findall(r"asset:([0-9a-f-]{36})", json.dumps(content)))
    cms_dir = os.path.join(WEBROOT, "images", "cms")
    for aid in ids:
        target = os.path.join(cms_dir, f"{aid}.webp")
        if os.path.exists(target):
            continue
        try:
            blob = call("GET", f"assets/{aid}?w={ASSET_WIDTH}", raw=True)
        except (urllib.error.URLError, OSError) as err:
            log(f"Не удалось скачать фото {aid}: {err}")
            return 0
        os.makedirs(cms_dir, exist_ok=True)
        tmp = target + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(blob)
        os.chmod(tmp, 0o644)
        os.replace(tmp, target)

    def resolve(value):
        m = re.fullmatch(r"asset:([0-9a-f-]{36})", value or "")
        if m:
            return f"/images/cms/{m.group(1)}.webp"
        return "/" + (value or "").lstrip("/")   # от корня сайта: работает и на внутренних страницах

    pages = build.render_site(content, resolve)
    changed = []
    for slug, html in pages.items():
        folder = os.path.join(WEBROOT, slug) if slug else WEBROOT
        index = os.path.join(folder, "index.html")
        try:
            with open(index, encoding="utf-8") as fh:
                if fh.read() == html:
                    continue
        except OSError:
            pass
        os.makedirs(folder, exist_ok=True)
        os.chmod(folder, 0o755)
        tmp = index + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(html)
        os.chmod(tmp, 0o644)
        os.replace(tmp, index)
        changed.append("/" + slug if slug else "/")

    # страницы, которые убрали в редакторе, удаляем (только те, что создали мы)
    old_slugs = set(state.get("pages", []))
    new_slugs = {s for s in pages if s}
    for slug in old_slugs - new_slugs:
        folder = os.path.join(WEBROOT, slug)
        try:
            os.remove(os.path.join(folder, "index.html"))
            os.rmdir(folder)
            changed.append(f"удалена /{slug}")
        except OSError:
            pass
    if old_slugs != new_slugs:
        state["pages"] = sorted(new_slugs)
        save_state(state)

    if changed:
        log(f"Сайт обновлён (версия {published.get('version')}): {', '.join(changed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
