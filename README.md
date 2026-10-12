# Лабораторная работа 6. Разработка сценария нагрузочного тестирования с использованием Locust

## Цель работы
Освоить разработку сценариев нагрузочного тестирования с использованием инструмента **Locust**, выполнив нагрузочное тестирование REST API стандарта Redfish в **OpenBMC** и открытых публичных API (**JSONPlaceholder**, **wttr.in**). Оценить производительность, проанализировать задержки, пропускную способность (RPS), перцентили времени отклика и возможные точки отказа под нагрузкой.

---

## Архитектура и структура проекта
- `locustfile.py` — основной файл сценариев нагрузки Locust с двумя классами виртуальных пользователей (`OpenBMCUser` и `PublicAPIUser`).
- `openbmc_server.py` — сервер-эмулятор OpenBMC Redfish API (DMTF Redfish v1) для автономного локального запуска без тяжелого QEMU.
- `run_load_tests.py` — скрипт автоматизированного запуска тестов в headless-режиме со сбором статистики в CSV и HTML.
- `results/` — директория с выгруженными CSV-метриками и интерактивными HTML-отчетами Locust (`openbmc_report.html`, `public_report.html`, `combined_report.html`).
- `report_lab6.html` — исходный HTML-документ отчёта по лабораторной работе.
- `Отчет_Лабораторная_работа_6.pdf` — официальный чистовой отчёт по лабораторной работе в формате PDF.

---

## Реализованные классы пользователей Locust (`locustfile.py`)

### 1. Класс нагрузки `OpenBMCUser` (Redfish API)
- **Авторизация (`on_start`)**: отправка `POST /redfish/v1/SessionService/Sessions` с учётными данными `root` / `0penBmc`, получение токена `X-Auth-Token` и прикрепление его ко всем последующим запросам.
- **Запрос информации о системе (`@task(3) get_system_info`)**: `GET /redfish/v1/Systems/system`, валидация полей `Status` и `PowerState`.
- **Запрос состояния питания (`@task(2) get_power_state`)**: `GET /redfish/v1/Systems/system`, валидация допустимых значений `PowerState` (`On`, `Off`, `PoweringOn`).
- **Запрос тепловой телеметрии (`@task(1) get_thermal_telemetry`)**: `GET /redfish/v1/Chassis/chassis/Thermal`.

### 2. Класс нагрузки `PublicAPIUser` (Публичные сервисы)
- **Запрос списка постов (`@task(3) get_posts`)**: `GET /posts` на `https://jsonplaceholder.typicode.com`, валидация непустого JSON-массива постов.
- **Запрос погоды (`@task(1) get_weather`)**: `GET https://wttr.in/Novosibirsk?format=j1`, валидация JSON-структуры текущих метеорологических условий Новосибирска.

---

## Запуск нагрузочного тестирования

### 1. Установка зависимостей
```bash
pip install locust requests
```

### 2. Запуск в режиме Web UI
Для интерактивного запуска через браузер:
```bash
locust
```
Затем откройте в браузере: `http://localhost:8089`  
Укажите параметры:
- Number of users: `10`
- Ramp up (spawn rate): `2`
- Host: `http://127.0.0.1:18443` (для OpenBMC) или оставьте дефолтный.

### 3. Запуск в автоматическом Headless-режиме
Для автоматического прогона всех сценариев и генерации отчетов:
```bash
python run_load_tests.py
```

---

## Ссылка на GitHub репозиторий
Код сценариев, вспомогательных скриптов и отчётных материалов опубликован в репозитории:  
`https://github.com/dra1nerrr/lab6_TPO`
