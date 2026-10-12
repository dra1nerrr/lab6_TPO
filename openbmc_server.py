"""
Сервер-эмулятор OpenBMC Redfish API для нагрузочного тестирования с Locust.
Лабораторная работа №6.
Предоставляет эндпоинты:
- GET /redfish/v1/ (ServiceRoot)
- POST /redfish/v1/SessionService/Sessions (создание сессии)
- GET /redfish/v1/Systems/system (информация о системе)
- GET /redfish/v1/Chassis/chassis/Thermal (тепловые параметры)
"""

import json
import logging
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OpenBMCServer")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class OpenBMCRedfishHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Отключаем дефолтный вывод каждого запроса в консоль, чтобы не перегружать вывод при высокой нагрузке
        pass

    def _send_json(self, status_code: int, data: dict, extra_headers: dict = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "keep-alive")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Имитация реального времени отклика OpenBMC bmcweb (~5-15 мс)
        time.sleep(0.008)

        path = self.path.split("?")[0].rstrip("/")
        if not path:
            path = "/"

        if path in ("/redfish", "/redfish/v1"):
            self._send_json(200, {
                "@odata.type": "#ServiceRoot.v1_5_0.ServiceRoot",
                "Id": "RootService",
                "Name": "Root Service",
                "RedfishVersion": "1.8.0",
                "UUID": "7c823f65-4e78-4395-8d5f-97217db5679a",
                "SessionService": {"@odata.id": "/redfish/v1/SessionService"},
                "Systems": {"@odata.id": "/redfish/v1/Systems"},
                "Chassis": {"@odata.id": "/redfish/v1/Chassis"}
            })
            return

        if path == "/redfish/v1/Systems/system":
            self._send_json(200, {
                "@odata.type": "#ComputerSystem.v1_13_0.ComputerSystem",
                "Id": "system",
                "Name": "Romulus OpenBMC Host System",
                "SystemType": "Physical",
                "Manufacturer": "OpenBMC",
                "Model": "Romulus POWER9 Server",
                "SerialNumber": "ROMULUS-LOAD-2026",
                "PowerState": "On",
                "Status": {
                    "State": "Enabled",
                    "Health": "OK"
                },
                "ProcessorSummary": {
                    "Count": 2,
                    "Model": "IBM POWER9 (24-core)",
                    "Status": {"State": "Enabled", "Health": "OK"}
                },
                "MemorySummary": {
                    "TotalSystemMemoryGiB": 64,
                    "Status": {"State": "Enabled", "Health": "OK"}
                }
            })
            return

        if path in ("/redfish/v1/Chassis/chassis", "/redfish/v1/Chassis/chassis/Thermal"):
            self._send_json(200, {
                "@odata.type": "#Thermal.v1_7_1.Thermal",
                "Id": "Thermal",
                "Name": "Thermal Information",
                "Temperatures": [
                    {
                        "MemberId": "0",
                        "Name": "CPU0 Core Temp",
                        "ReadingCelsius": 42.5,
                        "Status": {"State": "Enabled", "Health": "OK"}
                    },
                    {
                        "MemberId": "1",
                        "Name": "CPU1 Core Temp",
                        "ReadingCelsius": 44.0,
                        "Status": {"State": "Enabled", "Health": "OK"}
                    }
                ]
            })
            return

        self._send_json(404, {"error": "Not Found", "path": path})

    def do_POST(self):
        time.sleep(0.010)
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}

        if path == "/redfish/v1/SessionService/Sessions":
            username = body.get("UserName", "")
            password = body.get("Password", "")
            if username == "root" and password == "0penBmc":
                token = f"bmc_token_{uuid.uuid4().hex[:12]}"
                self._send_json(201, {
                    "Id": "session_load_test",
                    "UserName": "root",
                    "Token": token
                }, extra_headers={"X-Auth-Token": token, "Location": "/redfish/v1/SessionService/Sessions/1"})
            else:
                self._send_json(401, {"error": "Unauthorized"})
            return

        self._send_json(404, {"error": "Not Found"})


_server = None

def start_server(port: int = 18443):
    global _server
    if _server is not None:
        return
    _server = ThreadedHTTPServer(("127.0.0.1", port), OpenBMCRedfishHandler)
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()
    logger.info(f"OpenBMC Redfish Server запущен на http://127.0.0.1:{port}")
    time.sleep(0.2)


if __name__ == "__main__":
    start_server(18443)
    print("Сервер работает. Нажмите Ctrl+C для остановки.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Остановка сервера.")
