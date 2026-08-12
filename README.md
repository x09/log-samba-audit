# log-samba-audit-viewer

Программа с графическим интерфейсом (Python 3 + tkinter) для чтения
JSON-аудита Samba AD DC через REST API systemd-journal-gatewayd. 

<img width="1919" height="1048" alt="log-samba-audit-viewer" src="https://github.com/user-attachments/assets/c39408a5-13ba-4126-aad8-f6cceeabb02e" />


## Возможности
- Чтение аудита по сети через `systemd-journal-gatewayd` (порт 19531):
  HTTP, HTTPS с проверкой по CA, взаимный TLS (клиентский сертификат).
- Выбор юнитов journald (несколько через запятую, по умолчанию `samba.service`).
- Таблица событий с цветовой подсветкой (успех/неудача) и панелью полного JSON.
- Фильтры: диапазон дат, тип события, статус (все/успех/неудача).
- **Расширенный текстовый поиск** с логическими операторами (`&`, `|`), скобками и wildcard (`*`, `?`):
  - `domainuser1 & administrator` — оба термина в событии
  - `user1 | user2 | admin` — любой из терминов
  - `(domain* | admin*) & success` — группировка и префиксный поиск
  - См. [docs/SEARCH_SYNTAX.md](docs/SEARCH_SYNTAX.md) для подробной документации.
- Кнопка остановки долгих поисков (сканирование можно прервать в любой момент).
- Режим слежения (follow) — показ только новых событий по мере поступления.
- Двуязычный интерфейс (English по умолчанию, Русский). Переключение в меню
  «Язык», применяется после перезапуска.
- Настройки, язык и размер окна сохраняются в `~/.config/log-samba-audit.ini`.

Только стандартная библиотека Python 3 (модули из репозитория ALT Linux).

## Предварительная настройка серверной части
Для чтения системных журналов настраивается служба systemd-journal-gatewayd, предоставляющая через REST API доступ к журналам systemd-journald на контроллере домена.

```
[root@dc ~]# apt-get update && apt-get install systemd-journal-remote -y
[root@dc ~]# mkdir -p /etc/systemd/system/systemd-journal-gatewayd.socket.d/
[root@dc ~]# cat > /etc/systemd/system/systemd-journal-gatewayd.socket.d/listen.conf << 'EOF'
[Socket]
# Сбрасываем дефолтный ListenStream
ListenStream=
# Слушаем на всех интерфейсах, порт 19531 (по умолчанию)
ListenStream=0.0.0.0:19531
EOF
systemctl daemon-reload
[root@dc ~]# systemctl enable --now systemd-journal-gatewayd
[root@dc ~]# ss -tlnp | grep 19531
```


## Зависимости (ALT Linux)
- `python3`
- `python3-module-tkinter`
- `python3-module-lark` (для парсинга логических выражений в поиске)

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
