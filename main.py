import psutil
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, Gauge
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import time
import threading

# Создаём реестр метрик
registry = CollectorRegistry()

# Определяем метрики с меткой 'core' для каждого ядра процессора
cpu_usage_percentage = Gauge('cpu_usage_percentage', 'Процент использования процессоров', ['core'], registry=registry)
memory_total_bytes = Gauge('memory_total_bytes', 'Общий объем оперативной памяти', registry=registry)
memory_used_bytes = Gauge('memory_used_bytes', 'Используемая оперативная память', registry=registry)
disk_total_bytes = Gauge('disk_total_bytes', 'Общий объем дисков', registry=registry)
disk_used_bytes = Gauge('disk_used_bytes', 'Используемое место на дисках', registry=registry)

# Функция для сбора метрик
def collect_metrics():
    while True:
        # Получаем использование каждого ядра процессора
        cpu_percentages = psutil.cpu_percent(interval=1, percpu=True)
        for i, cpu_percent in enumerate(cpu_percentages):
            cpu_usage_percentage.labels(core=i).set(cpu_percent)  # Добавляем метку для каждого ядра

        # Получаем информацию о памяти
        memory = psutil.virtual_memory()
        memory_total_bytes.set(memory.total)
        memory_used_bytes.set(memory.used)

        # Получаем информацию о диска
        disk = psutil.disk_usage('/')
        disk_total_bytes.set(disk.total)
        disk_used_bytes.set(disk.used)

        # Интервал сбора метрик (например, 5 секунд)
        time.sleep(5)

# Класс обработчика HTTP-запросов
class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                metrics = generate_latest(registry)
                self.send_response(200)
                self.send_header('Content-Type', CONTENT_TYPE_LATEST)
                self.send_header('Content-Length', str(len(metrics)))
                self.end_headers()
                self.wfile.write(metrics)
            except Exception as e:
                self.send_error(500, "Error generating metrics")
        else:
            self.send_error(404, "Page not found")  # Изменено на ASCII

    def log_message(self, format, *args):
        return  # Отключаем логирование запросов

# Основная функция
def main():
    # Определяем переменные окружения для хоста и порта
    exporter_host = os.getenv('EXPORTER_HOST', '0.0.0.0')
    exporter_port = int(os.getenv('EXPORTER_PORT', 8000))

    # Запуск потока для сбора метрик
    metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
    metrics_thread.start()

    # Запуск HTTP-сервера
    server_address = (exporter_host, exporter_port)
    httpd = HTTPServer(server_address, MetricsHandler)
    print(f"Exporter работает на http://{exporter_host}:{exporter_port}/")
    print(f"Prometheus доступен по адресу http://localhost:9090/")
    httpd.serve_forever()

if __name__ == '__main__':
    main()