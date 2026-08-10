# log-samba-audit-viewer

Программа с графическим интерфейсом (Python 3 + tkinter) для чтения
JSON-аудита Samba AD DC. 

<img width="1919" height="1047" alt="изображение" src="https://github.com/user-attachments/assets/7084f367-df4c-4636-8912-95eacdc85f77" />

## Возможности
- Чтение аудита по сети через `systemd-journal-gatewayd` (порт 19531):
  HTTP, HTTPS с проверкой по CA, взаимный TLS (клиентский сертификат).
- Выбор юнитов journald (несколько через запятую, по умолчанию `samba.service`).
- Таблица событий с цветовой подсветкой (успех/неудача) и панелью полного JSON.
- Фильтры: диапазон дат, тип события, статус (все/успех/неудача), текстовый поиск.
- Режим слежения (follow) — показ только новых событий по мере поступления.
- Двуязычный интерфейс (English по умолчанию, Русский). Переключение в меню
  «Язык», применяется после перезапуска.
- Настройки, язык и размер окна сохраняются в `~/.config/log-samba-audit.ini`.

Только стандартная библиотека Python 3 (модули из репозитория ALT Linux),
без сторонних зависимостей.

## Предварительная настройка серверной части
Для чтения системных журналов, нужно настроить службу systemd-journal-gatewayd, 
которая последством RESTfulAPI от Journald предоставляет доступ к системному журналу на КД.

```
[root@dc ~]# apt-get update && apt-get install systemd-journal-remote -y
[root@dc ~]# useradd --system --no-create-home --user-group systemd-journal-gateway
[root@dc ~]# usermod -aG systemd-journal systemd-journal-gateway
[root@dc ~]# mkdir -p /etc/systemd/system/systemd-journal-gatewayd.socket.d/
[root@dc ~]# cat > /etc/systemd/system/systemd-journal-gatewayd.socket.d/listen.conf << 'EOF'
[Socket]
# Сбрасываем дефолтный ListenStream
ListenStream=
# Слушаем на всех интерфейсах, порт 19531 (по умолчанию)
ListenStream=0.0.0.0:19531
EOF
systemctl daemon-reload
[root@dc ~]# systemctl enable systemd-journal-gatewayd.socket
[root@dc ~]# systemctl start systemd-journal-gatewayd.socket
[root@dc ~]# ss -tlnp | grep 19531
```


## Зависимости (ALT Linux)
- `python3`
- `python3-module-tkinter`

## Запуск
```sh
python3 log-samba-audit-viewer.py
```

## Локализация
Строки — в `po/<язык>.po`. После правки перевода пересоберите `.mo`:
```sh
python3 build_locale.py
```
(Использует только stdlib, утилита `msgfmt` не требуется.)

## Не реализовано в 1.0
- Чтение из локальной папки с логами — см. `TODO.md`.
