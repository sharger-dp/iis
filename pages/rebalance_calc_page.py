class RebalanceCalculator:
    @staticmethod
    def calculate_rebalance(row_data, total_value, total_cap, free_cash=0):
        action = "Держать"
        buy_qty = 0.0
        buy_amount = 0.0

        try:
            if row_data['portfolio_percent'] is not None and row_data['cap_percent'] is not None:
                if row_data['portfolio_percent'] < row_data['cap_percent']:
                    action = "Докупать"

                    # сколько недостаёт до целевой доли
                    target_value = row_data['cap_percent'] / 100 * (total_value + free_cash)
                    need_to_invest = target_value - (row_data['qty'] * row_data['last_price'])

                    # ограничиваем доступными деньгами
                    buy_amount = min(max(0, need_to_invest), free_cash)
                    buy_qty = buy_amount / row_data['last_price'] if row_data['last_price'] else 0

        except (TypeError, ZeroDivisionError):
            pass

        return action, round(buy_qty), buy_amount
