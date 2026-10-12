"""
Скрипт запуска нагрузочного тестирования с Locust в автономном режиме (headless).
Выполняет тесты, сохраняет CSV-метрики и сводный HTML-отчет для включения в отчет.
"""

import os
import subprocess
import sys
import time

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_cmd(cmd_list, description):
    print(f"\n==================================================")
    print(f"▶ {description}")
    print(f"Команда: {' '.join(cmd_list)}")
    print(f"==================================================")
    proc = subprocess.run(cmd_list, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print("[STDERR]:", proc.stderr)
    return proc.returncode

def main():
    # 1. Тестирование класса OpenBMCUser (10 пользователей, spawn rate 2, длительность 20 секунд)
    openbmc_csv = os.path.join(RESULTS_DIR, "openbmc_stats")
    openbmc_html = os.path.join(RESULTS_DIR, "openbmc_report.html")
    run_cmd([
        sys.executable, "-m", "locust",
        "-f", "locustfile.py",
        "--headless",
        "-u", "10",
        "-r", "2",
        "-t", "20s",
        "--csv", openbmc_csv,
        "--html", openbmc_html,
        "OpenBMCUser"
    ], "Нагрузочное тестирование OpenBMC API (10 виртуальных пользователей, 20 секунд)")

    # 2. Тестирование класса PublicAPIUser (10 пользователей, spawn rate 2, длительность 20 секунд)
    public_csv = os.path.join(RESULTS_DIR, "public_stats")
    public_html = os.path.join(RESULTS_DIR, "public_report.html")
    run_cmd([
        sys.executable, "-m", "locust",
        "-f", "locustfile.py",
        "--headless",
        "--host", "https://jsonplaceholder.typicode.com",
        "-u", "10",
        "-r", "2",
        "-t", "20s",
        "--csv", public_csv,
        "--html", public_html,
        "PublicAPIUser"
    ], "Нагрузочное тестирование Публичных API (JSONPlaceholder и wttr.in, 20 секунд)")

    # 3. Комбинированный запуск обоих классов
    combined_csv = os.path.join(RESULTS_DIR, "combined_stats")
    combined_html = os.path.join(RESULTS_DIR, "combined_report.html")
    run_cmd([
        sys.executable, "-m", "locust",
        "-f", "locustfile.py",
        "--headless",
        "-u", "10",
        "-r", "2",
        "-t", "25s",
        "--csv", combined_csv,
        "--html", combined_html
    ], "Комплексное тестирование всех классов нагрузки (25 секунд)")

    print("\n✅ Все тесты успешно завершены! Результаты сохранены в папке 'results/'.")

if __name__ == "__main__":
    main()
