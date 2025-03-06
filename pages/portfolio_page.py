class Portfolio:
    def __init__(self, tickers, moex_data, user_inputs):
        self.tickers = tickers
        self.moex_data = moex_data
        self.user_inputs = user_inputs
        self.total_cap = self._calculate_total_cap()
        self.portfolio_total = self._calculate_portfolio_total()
        self.sorted_tickers = self._get_sorted_tickers()
        self.max_bar_width = 20

    def _get_sorted_tickers(self):
        tickers_with_cap = []
        for ticker in self.tickers:
            cap = self.moex_data[ticker]['ISSUECAPITALIZATION']
            cap_percent = (cap / self.total_cap * 100) if cap and self.total_cap > 0 else 0
            tickers_with_cap.append((ticker, cap_percent))

        return sorted(
            tickers_with_cap,
            key=lambda x: x[1],
            reverse=True
        )

    def _calculate_total_cap(self):
        return sum(
            data['ISSUECAPITALIZATION']
            for data in self.moex_data.values()
            if data['ISSUECAPITALIZATION']
        )

    def _calculate_portfolio_total(self):
        return sum(
            self.moex_data[ticker]['LAST'] * self.user_inputs[ticker]['qty']
            for ticker in self.tickers
            if self.moex_data[ticker]['LAST'] is not None
            and self.user_inputs[ticker]['qty'] > 0
        )