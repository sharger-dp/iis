import database

class UserInputHandler:
    def __init__(self):
        pass

    def get_inputs(self, tickers):
        try:
            portfolio_data = database.load_portfolio()
            inputs = {}
            for ticker in tickers:
                if ticker in portfolio_data:
                    inputs[ticker] = {
                        'qty': portfolio_data[ticker].get('qty', 0),
                        'invested': portfolio_data[ticker].get('invested', 0.0)
                    }
                else:
                    inputs[ticker] = {
                        'qty': 0,
                        'invested': 0.0
                    }
            return inputs
        except Exception as e:
            print(f"Ошибка при загрузке данных из БД: {e}")
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