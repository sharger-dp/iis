from pages.rebalance_calc_page import RebalanceCalculator


class PortfolioPrinter:
    def __init__(self, portfolio, formatter, free_cash=0):
        self.portfolio = portfolio
        self.formatter = formatter
        self.free_cash = free_cash
        self.total = {
            'current_value': 0.0,
            'invested': 0.0,
            'result': 0.0,
            'buy_amount_total': 0.0,
            'weights': 0.0
        }

    def print(self):
        self._print_header()
        self._print_body()
        self._print_footer()
        self._print_distribution_chart()

    def _print_header(self):
        header = [
            f"{'Тикер':<8} | {'Название':<20} |",
            f"{'Котировка':>12} |",
            f"{'Кол-во':>8} |",
            f"{'Стоимость':>12} |",
            f"{'Вложено':>12} |",
            f"{'Результат':>12} |",
            f"{'Рез.%':>8} |",
            f"{'Доля,%':>8} |",
            f"{'Капитализация':>20} │",
            f"{'Кап.доля,%':>10} |",
            f"{'Действие':>10} |",
            f"{'Докупка':>12} |",
            f"{'Сумма':>12}"
        ]
        print("".join(header))
        print("-" * 190)

    def _print_body(self):
        for ticker, _ in self.portfolio.sorted_tickers:
            self._print_row(ticker)

    def _print_row(self, ticker):
        data = self.portfolio.moex_data[ticker]
        inputs = self.portfolio.user_inputs[ticker]

        last_price = data['LAST'] or 0
        qty = inputs['qty']
        invested = inputs['invested']
        current_value = last_price * qty if last_price else 0
        result_value = current_value - invested
        result_percent = (result_value / invested * 100) if invested != 0 else 0.0
        portfolio_percent = (
                    current_value / self.portfolio.portfolio_total * 100) if self.portfolio.portfolio_total > 0 else 0
        capitalization = data.get('ISSUECAPITALIZATION', 0)  # Получаем капитализацию
        cap_percent = (data['ISSUECAPITALIZATION'] / self.portfolio.total_cap * 100) if data[
                                                                                            'ISSUECAPITALIZATION'] and self.portfolio.total_cap > 0 else 0

        action, buy_qty, buy_amount = RebalanceCalculator.calculate_rebalance(
            {
                'portfolio_percent': portfolio_percent,
                'cap_percent': cap_percent,
                'last_price': last_price,
                'qty': qty
            },
            self.portfolio.portfolio_total,
            self.portfolio.total_cap,
            self.free_cash  # 🔹 новый параметр
        )

        self._update_totals(current_value, invested, result_value, buy_amount, cap_percent)

        row = [
            f"{ticker:<8} | {data['SECNAME'][:20]:<20} |",
            f"{self.formatter.format_value(last_price, 'price') if last_price else 'N/A':>12} |",
            f"{qty:>8} |",
            f"{self.formatter.format_value(current_value, 'currency'):>12} |",
            f"{self.formatter.format_value(invested, 'currency'):>12} |",
            f"{self.formatter.format_result(result_value)} |"
            f"{self.formatter.format_percent(result_percent):>8} |",
            f"{portfolio_percent:>7.2f}% |",
            f"{self.formatter.format_value(capitalization, 'currency'):>20} │",
            f"{cap_percent:>9.2f}% |" if cap_percent else f"{'N/A':>10} |",
            f"{self.formatter.format_action(action)} |",
            f"{round(buy_qty):>12} |",
            f"{self.formatter.format_value(buy_amount, 'currency') if buy_amount else '0':>12}"
        ]
        print("".join(row))

    def _update_totals(self, current_value, invested, result_value, buy_amount, cap_percent):
        self.total['current_value'] += current_value
        self.total['invested'] += invested
        self.total['result'] += result_value
        self.total['buy_amount_total'] += buy_amount
        self.total['weights'] += cap_percent

    def _print_footer(self):
        print("-" * 190)
        total_row = [
            f"{'ИТОГО':<9}  {'':<21} ",
            f"{'':>13} ",
            f"{'':>8} |",
            f"{self.formatter.format_value(self.total['current_value'], 'currency'):>12} |",
            f"{self.formatter.format_value(self.total['invested'], 'currency'):>12} |",
            f"{self.formatter.format_value(self.total['result'], 'currency'):>12} |",
            f"{'':>9} ",
            f"{'':>9} ",
            f"{'':>20} ",
            f"{'':>11} ",
            f"{'':>11} ",
            f"{'':>12} |",
            f"{self.formatter.format_value(self.total['buy_amount_total'], 'currency'):>12}"
        ]
        print("".join(total_row))

    def _print_distribution_chart(self):
        print("\nРаспределение долей:")
        max_percent = max(
            max(data['ISSUECAPITALIZATION'] / self.portfolio.total_cap * 100
                for data in self.portfolio.moex_data.values()),
            max((self.portfolio.moex_data[ticker]['LAST'] * self.portfolio.user_inputs[ticker]['qty'] /
                 self.portfolio.portfolio_total * 100)
                for ticker in self.portfolio.tickers)
        ) if self.portfolio.total_cap > 0 and self.portfolio.portfolio_total > 0 else 100

        for ticker, _ in self.portfolio.sorted_tickers:
            data = self.portfolio.moex_data[ticker]
            inputs = self.portfolio.user_inputs[ticker]

            last_price = data['LAST'] or 0
            qty = inputs['qty']
            current_value = last_price * qty if last_price else 0

            portfolio_percent = (
                        current_value / self.portfolio.portfolio_total * 100) if self.portfolio.portfolio_total > 0 else 0
            cap_percent = (data['ISSUECAPITALIZATION'] / self.portfolio.total_cap * 100) if data[
                                                                                                'ISSUECAPITALIZATION'] and self.portfolio.total_cap > 0 else 0

            bar = self.formatter.format_percent_bar(portfolio_percent, cap_percent)
            print(f"{ticker:<6} {bar}")