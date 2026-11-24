#!/usr/bin/env python3
"""Добавляет страницу из файла (например seed/tarify.json) в ЧЕРНОВИК сайта в CRM.

Ничего не публикует: страницу сначала проверяют в редакторе и нажимают «Опубликовать».
Логин и пароль администратора CRM спрашиваются при запуске и никуда не сохраняются.
"""
import getpass
import json
import os
import sys
import urllib.error
import urllib.request


def env_file(path="/etc/drevo-sync.env"):
    out = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    out[k] = v
    except OSError:
        pass
    return out


def call(api, method, path, body=None, token=None):
    req = urllib.request.Request(api + path, method=method)
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except ValueError:
            pass
        sys.exit(f"CRM ответила ошибкой {err.code}: {detail}")


def main():
    if len(sys.argv) != 2:
        sys.exit("Использование: python3 add_page.py seed/tarify.json")
    with open(sys.argv[1], encoding="utf-8") as fh:
        new_blocks = json.load(fh)["blocks"]
    cfg = env_file()
    api = os.environ.get("CRM_API") or cfg.get("CRM_API", "http://127.0.0.1:4200/api")
    key = os.environ.get("SITE_KEY") or cfg.get("SITE_KEY", "drevo")
    new_slug = next((b["data"].get("slug") for b in new_blocks if b["type"] == "page"), None)

    email = input("E-mail администратора CRM: ").strip()
    password = getpass.getpass("Пароль (при вводе не виден): ")
    token = call(api, "POST", "/auth/login", {"email": email, "password": password})["accessToken"]

    sites = call(api, "GET", "/sites", token=token)
    site = next((s for s in sites if s.get("key") == key), None)
    if not site:
        sys.exit(f"Сайт с кодом «{key}» не найден в CRM")
    blocks = call(api, "GET", f"/sites/{site['id']}", token=token)["draft"]["blocks"]

    # если такая страница уже есть в черновике — заменяем её (блоки от «Новой страницы» до следующей или подвала)
    kept, skipping = [], False
    for b in blocks:
        if b["type"] == "page":
            skipping = (b.get("data") or {}).get("slug") == new_slug
        elif b["type"] == "footer":
            skipping = False
        if not skipping:
            kept.append(b)
    at = next((i for i, b in enumerate(kept) if b["type"] == "footer"), len(kept))
    merged = kept[:at] + new_blocks + kept[at:]

    call(api, "PUT", f"/sites/{site['id']}/draft", {"blocks": merged}, token=token)
    print(f"Готово: страница «{new_slug}» добавлена в черновик. Откройте CRM → Сайт → Редактировать,")
    print("проверьте блоки и нажмите «Опубликовать».")


if __name__ == "__main__":
    main()
