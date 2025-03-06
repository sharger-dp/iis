class Formatter:
    @staticmethod
    def format_value(value, ftype='currency'):
        """Форматирование числовых значений с обработкой ошибок"""
        if value is None:
            return 'N/A'
        try:
            value = float(value)
            if ftype == 'currency':
                return f"{value:,.0f} ₽".replace(",", " ")
            elif ftype == 'price':
                return f"{value:,.2f} ₽".replace(",", " ")
            return f"{value:,.2f}"
        except (ValueError, TypeError):
            return 'N/A'

    @staticmethod
    def format_result(value):
        if value is None:
            return 'N/A'
        try:
            value = float(value)
            color_code = '\033[92m' if value >= 0 else '\033[91m'
            reset_code = '\033[0m'
            formatted = f"{abs(value):,.0f} ₽".replace(",", " ")

            # Добавляем цветовые коды, но сохраняем визуальную ширину
            return f"{color_code}{formatted:>12}{reset_code}"

        except (ValueError, TypeError):
            return 'N/A'

    @staticmethod
    def format_action(action):
        """Форматирование действия с цветовым выделением"""
        colors = {
            'Докупать': '\033[92m',  # Зеленый
            'Держать': '\033[93m',   # Желтый
        }
        reset = '\033[0m'
        return f"{colors.get(action, '')}{action:^{10}}{reset}"

    @staticmethod
    def format_percent_bar(portfolio_percent, cap_percent, width=20):
        """Текстовая полоса с двумя показателями"""
        scaled_portfolio = int(portfolio_percent / 100 * width)
        scaled_cap = int(cap_percent / 100 * width)

        bar = '\033[92m' + '█' * scaled_portfolio + '\033[0m'
        bar += '\033[93m' + '░' * (scaled_cap - scaled_portfolio) + '\033[0m'
        bar += ' ' * (width - max(scaled_portfolio, scaled_cap))
        return f"{bar} {portfolio_percent:5.1f}%/{cap_percent:5.1f}%"

    @staticmethod
    def format_percent(value):
        """Форматирование процентов с цветовым выделением"""
        if value is None:
            return 'N/A'
        try:
            value = float(value)
            color_code = '\033[92m' if value >= 0 else '\033[91m'
            reset_code = '\033[0m'
            return f"{color_code}{value:>7.1f}%{reset_code}"
        except (ValueError, TypeError):
            return 'N/A'