#!/usr/bin/env bash
# Подключает сайт к CRM: ставит скрипт синхронизации и запускает его раз в минуту.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Запустите от root"; exit 1; }

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST=/opt/drevo-site
WEBROOT="${WEBROOT:-/var/www/drevo-zhizny.ru}"
CRM_API="${CRM_API:-http://127.0.0.1:4200/api}"
SITE_KEY="${SITE_KEY:-drevo}"

[ -f "$WEBROOT/index.html" ] || { echo "Не найден $WEBROOT/index.html"; exit 1; }
command -v python3 >/dev/null || apt-get install -y python3

echo "== 1. Проверяю, что CRM отвечает"
if ! curl -fsS --max-time 5 "$CRM_API/health" >/dev/null 2>&1; then
  echo "ВНИМАНИЕ: $CRM_API/health не отвечает. Проверьте, что CRM запущена: docker ps"
  echo "Если CRM слушает другой порт, запустите так: CRM_API=http://127.0.0.1:ПОРТ/api $0"
  exit 1
fi

echo "== 2. Копирую файлы"
mkdir -p "$DEST"
cp "$SRC/build.py" "$SRC/sync.py" "$SRC/schema.json" "$DEST/"
if [ ! -f /root/index.before-crm.html ]; then
  cp "$WEBROOT/index.html" /root/index.before-crm.html
  echo "Старая страница сохранена в /root/index.before-crm.html"
fi

echo "== 3. Токен сайта"
read -r -s -p "Вставьте токен из CRM (при вводе он не виден) и нажмите Enter: " TOKEN
echo
[ -n "$TOKEN" ] || { echo "Токен пустой"; exit 1; }
( umask 077; cat > /etc/drevo-sync.env <<ENV
CRM_API=$CRM_API
SITE_KEY=$SITE_KEY
SITE_TOKEN=$TOKEN
WEBROOT=$WEBROOT
ENV
)

echo "== 4. Запускаю по расписанию (раз в минуту)"
cat > /etc/systemd/system/drevo-sync.service <<UNIT
[Unit]
Description=Синхронизация сайта с CRM

[Service]
Type=oneshot
EnvironmentFile=/etc/drevo-sync.env
ExecStart=/usr/bin/python3 -I $DEST/sync.py
UNIT
cat > /etc/systemd/system/drevo-sync.timer <<UNIT
[Unit]
Description=Синхронизация сайта с CRM раз в минуту

[Timer]
OnBootSec=30s
OnUnitActiveSec=60s

[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now drevo-sync.timer

echo "== 5. Первый запуск"
systemctl start drevo-sync.service || true
journalctl -u drevo-sync.service -n 5 --no-pager || true
echo
echo "ГОТОВО. В CRM (раздел «Сайт») статус сайта должен стать зелёным, появится кнопка «Редактировать»."
