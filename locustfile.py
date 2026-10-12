"""
Лабораторная работа 6. Разработка сценария нагрузочного тестирования с использованием Locust.

Скрипт содержит два класса пользователей:
1. OpenBMCUser - тестирование REST API стандарта Redfish в OpenBMC:
   - Аутентификация в OpenBMC (получение X-Auth-Token)
   - Запрос на получение информации о системе (/redfish/v1/Systems/system)
   - Запрос состояния питания (PowerState)
   - Запрос тепловой телеметрии (/redfish/v1/Chassis/chassis/Thermal)

2. PublicAPIUser - тестирование внешних публичных сервисов:
   - Запрос списка постов на JSONPlaceholder (/posts)
   - Запрос прогноза погоды на wttr.in (https://wttr.in/Novosibirsk?format=j1)
"""

import json
import logging
import os
from locust import HttpUser, task, between, events

logger = logging.getLogger("LocustLoadTest")

# При запуске вне отдельного процесса поднимаем локальный сервер OpenBMC, если он ещё не запущен
@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    try:
        from openbmc_server import start_server
        start_server(18443)
    except Exception as e:
        logger.warning(f"Не удалось инициализировать встроенный сервер: {e}")


# =============================================================================
# 1. Класс нагрузки для OpenBMC API
# =============================================================================
class OpenBMCUser(HttpUser):
    """
    Моделирует поведение администратора или автоматизированной системы мониторинга,
    периодически опрашивающей Redfish API серверной платформы OpenBMC.
    """
    # Базовый URL по умолчанию (локальный OpenBMC или QEMU)
    host = os.getenv("OPENBMC_HOST", "http://127.0.0.1:18443")
    wait_time = between(1.0, 2.5)
    weight = 3

    def on_start(self):
        """Выполняется при запуске каждого виртуального пользователя: аутентификация в BMC."""
        login_payload = {
            "UserName": "root",
            "Password": "0penBmc"
        }
        with self.client.post(
            "/redfish/v1/SessionService/Sessions",
            json=login_payload,
            name="[OpenBMC] POST /SessionService/Sessions (Auth)",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201):
                token = response.headers.get("X-Auth-Token")
                if not token and response.text:
                    try:
                        token = response.json().get("Token")
                    except Exception:
                        token = None
                if token:
                    self.client.headers["X-Auth-Token"] = token
                response.success()
            else:
                response.failure(f"Auth failed with status {response.status_code}")

    @task(3)
    def get_system_info(self):
        """Запрос общей информации о системе (ComputerSystem)."""
        with self.client.get(
            "/redfish/v1/Systems/system",
            name="[OpenBMC] GET /Systems/system (System Info)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "Status" in data and "PowerState" in data:
                        response.success()
                    else:
                        response.failure("Missing 'Status' or 'PowerState' in JSON response")
                except Exception as e:
                    response.failure(f"JSON decode error: {e}")
            else:
                response.failure(f"Expected 200 OK, got {response.status_code}")

    @task(2)
    def get_power_state(self):
        """Запрос состояния питания сервера (PowerState)."""
        with self.client.get(
            "/redfish/v1/Systems/system",
            name="[OpenBMC] GET /Systems/system (PowerState)",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    power_state = data.get("PowerState")
                    if power_state in ("On", "Off", "PoweringOn", "PoweringOff"):
                        response.success()
                    else:
                        response.failure(f"Invalid PowerState value: {power_state}")
                except Exception as e:
                    response.failure(f"JSON decode error: {e}")
            else:
                response.failure(f"Expected 200 OK, got {response.status_code}")

    @task(1)
    def get_thermal_telemetry(self):
        """Запрос телеметрии термодатчиков шасси (Thermal)."""
        with self.client.get(
            "/redfish/v1/Chassis/chassis/Thermal",
            name="[OpenBMC] GET /Chassis/chassis/Thermal",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected 200 OK, got {response.status_code}")


# =============================================================================
# 2. Класс нагрузки для Публичного API (JSONPlaceholder и wttr.in)
# =============================================================================
class PublicAPIUser(HttpUser):
    """
    Моделирует нагрузку на внешние публичные REST API сервисы:
    - JSONPlaceholder (получение списка постов)
    - wttr.in (получение прогноза погоды для Новосибирска в формате JSON)
    """
    host = "https://jsonplaceholder.typicode.com"
    wait_time = between(1.5, 3.0)
    weight = 2

    @task(3)
    def get_posts(self):
        """Запрос списка публикаций на JSONPlaceholder (/posts)."""
        with self.client.get(
            "/posts",
            name="[Public] JSONPlaceholder GET /posts",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    posts = response.json()
                    if isinstance(posts, list) and len(posts) > 0:
                        response.success()
                    else:
                        response.failure("Response is empty or not a list")
                except Exception as e:
                    response.failure(f"JSON decode error: {e}")
            else:
                response.failure(f"Expected 200 OK, got {response.status_code}")

    @task(1)
    def get_weather(self):
        """Запрос погоды для Новосибирска на wttr.in."""
        weather_url = "https://wttr.in/Novosibirsk?format=j1"
        with self.client.get(
            weather_url,
            name="[Public] wttr.in GET Novosibirsk Weather",
            catch_response=True,
            timeout=10.0
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "current_condition" in data:
                        response.success()
                    else:
                        response.failure("Missing 'current_condition' in weather data")
                except Exception as e:
                    response.failure(f"JSON decode error: {e}")
            elif response.status_code == 429:
                response.failure("Rate limited (429 Too Many Requests)")
            else:
                response.failure(f"Expected 200 OK, got {response.status_code}")
