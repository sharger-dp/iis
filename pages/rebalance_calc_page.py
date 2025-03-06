class RebalanceCalculator:
    @staticmethod
    def calculate_rebalance(row_data, total_value, total_cap):
        action = "Держать"
        buy_qty = 0.0
        buy_amount = 0.0

        try:
            if row_data['portfolio_percent'] is not None and row_data['cap_percent'] is not None:
                if row_data['portfolio_percent'] <= row_data['cap_percent']:
                    action = "Докупать"

                    if row_data['portfolio_percent'] > 0 and total_value > 0:
                        target_qty = (row_data['cap_percent'] / 100 * total_value) / row_data['last_price']
                        buy_qty = max(0, target_qty - row_data['qty'])
                    else:
                        buy_qty = row_data['cap_percent'] / 100 * total_value / row_data['last_price'] if row_data[
                            'last_price'] else 0

                    buy_qty = round(buy_qty)
                    buy_amount = buy_qty * row_data['last_price'] if row_data['last_price'] else 0

        except (TypeError, ZeroDivisionError):
            pass

        return action, buy_qty, buy_amount
