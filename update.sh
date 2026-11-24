#!/usr/bin/env bash
# Обновляет уже установленную синхронизацию (токен не спрашивает).
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Запустите от root"; exit 1; }
SRC="$(cd "$(dirname "$0")" && pwd)"
[ -f /etc/drevo-sync.env ] || { echo "Сначала установите: ./setup.sh"; exit 1; }
git -C "$SRC" pull --ff-only
cp "$SRC/build.py" "$SRC/sync.py" "$SRC/schema.json" /opt/drevo-site/
rm -f /var/lib/drevo-sync/state.json   # чтобы новое описание блоков ушло в CRM
systemctl start drevo-sync.service
journalctl -u drevo-sync.service -n 5 --no-pager
echo "ГОТОВО. Обновите редактор в CRM (F5): в списке блоков появится «Новая страница»."
