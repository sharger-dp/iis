class UserInputHandler:
    def get_inputs(self, tickers):
        inputs = {}
        print("Введите данные для каждого инструмента:")
        for ticker in tickers:
            inputs[ticker] = {
                'qty': self._get_integer_input(f"{ticker} - Количество: "),
                'invested': self._get_float_input(f"{ticker} - Сумма вложений (руб): ")
            }
        return inputs

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