import json
import pandas as pd

class UserInputHandler:
    def __init__(self, json_file_path='portfolio_data.json'):
        self.json_file_path = json_file_path

    def get_inputs(self, tickers):
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                inputs = {}
                for ticker in tickers:
                    if ticker in data:
                        inputs[ticker] = {
                            'qty': data[ticker].get('qty', 0),
                            'invested': data[ticker].get('invested', 0.0)
                        }
                    else:
                        inputs[ticker] = {
                            'qty': 0,
                            'invested': 0.0
                        }
                return inputs
        except FileNotFoundError:
            print(f"Файл {self.json_file_path} не найден.")
            return {ticker: {'qty': 0, 'invested': 0.0} for ticker in tickers}
        except json.JSONDecodeError:
            print(f"Ошибка при чтении JSON-файла {self.json_file_path}.")
            return {ticker: {'qty': 0, 'invested': 0.0} for ticker in tickers}

    def _get_integer_input(self, prompt):
        while True:
            try:
                return int(input(prompt).strip() or 0)
            except ValueError:
                print("Ошибка! Введите целое число.")

    def _get_float_input(self, prompt):
        while True:
            try:
                return float(input(prompt).strip() or 0)
            except ValueError:
                print("Ошибка! Введите число (например 15000.50).")