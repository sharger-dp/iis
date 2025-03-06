import logging
from logging.handlers import RotatingFileHandler
import os


class Logger:
    def __init__(self, name='portfolio_logger'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Создаем папку для логов если ее нет
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Настройка формата
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Ротирующий файловый обработчик (10 МБ на файл, максимум 5 файлов)
        file_handler = RotatingFileHandler(
            'logs/portfolio.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

        # Консольный вывод для ошибок
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Логирование старта
        self.logger.info(f"{'=' * 30} Session started {'=' * 30}")

    def log(self, level, message, extra=None):
        log_levels = {
            'debug': self.logger.debug,
            'info': self.logger.info,
            'warning': self.logger.warning,
            'error': self.logger.error,
            'critical': self.logger.critical
        }
        log_levels[level](message, extra=extra)
