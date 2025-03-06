from pages.formatter_page import Formatter
from pages.moex_clien_page import MoexClient
from pages.portfolio_page import Portfolio
from pages.portfolio_printer_page import PortfolioPrinter
from pages.user_input_handler import UserInputHandler


class RebalanceApp:
    def __init__(self, tickers):
        self.tickers = tickers
        self.moex_client = MoexClient()
        self.formatter = Formatter()
        self.user_input_handler = UserInputHandler()
        self.portfolio = None

    def run(self):
        moex_data = self.moex_client.fetch_data(self.tickers)
        if not moex_data:
            print("Не удалось получить данные")
            return

        user_inputs = self.user_input_handler.get_inputs(self.tickers)
        self.portfolio = Portfolio(self.tickers, moex_data, user_inputs)

        printer = PortfolioPrinter(self.portfolio, self.formatter)
        print("\nСтратегия ребалансировки портфеля:")
        printer.print()