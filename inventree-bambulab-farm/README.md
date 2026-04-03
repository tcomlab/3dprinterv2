# InvenTree Bambu Lab Farm Plugin

Плагін для інтеграції ферми 3D-принтерів **Bambu Lab** в InvenTree.

## Що вміє

- Підключається до декількох принтерів Bambu через локальний MQTT (`bblp`).
- Зчитує та кешує останній `print`-статус кожного принтера.
- Надає в коді плагіна методи:
  - `get_farm_status()` — список поточних станів принтерів.
  - `refresh_farm()` — примусове оновлення (`pushall`) для всіх принтерів.

## Встановлення

```bash
pip install ./inventree-bambulab-farm
```

або як editable-пакет:

```bash
pip install -e ./inventree-bambulab-farm
```

## Налаштування у InvenTree

У налаштуваннях плагіна заповніть `Printers JSON`, наприклад:

```json
[
  {
    "name": "Bambu X1C #1",
    "serial": "01P00C123456789",
    "host": "192.168.1.101",
    "access_code": "12345678",
    "port": 8883
  },
  {
    "name": "Bambu P1S #2",
    "serial": "01P00C987654321",
    "host": "192.168.1.102",
    "access_code": "12345678"
  }
]
```

> `port` необов'язковий (за замовчуванням `8883`).

## Важливо

- Принтери та сервер InvenTree мають бути в одній мережі.
- Потрібен коректний LAN access code для кожного принтера.
- Це базовий каркас плагіна: для production варто додати UI/API endpoint-и та обробку алертів.
