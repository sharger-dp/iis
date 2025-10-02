import streamlit as st
import pandas as pd
import json
from pages.rebalance_calc_page import RebalanceCalculator
from pages.moex_clien_page import MoexClient
from pages.portfolio_page import Portfolio

st.set_page_config(page_title="Портфель", layout="wide")
st.title("📈 Инвестиционный портфель с ребалансировкой")

json_file_path = "portfolio_data.json"

# ===== Функции для работы с JSON =====
def load_portfolio():
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_portfolio(data):
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Инициализация состояния =====
if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = load_portfolio()

if "update_flag" not in st.session_state:
    st.session_state.update_flag = False

portfolio_data = st.session_state.portfolio_data

# ===== Ввод тикеров =====
tickers_input = st.text_input(
    "Введите тикеры через запятую (например: SBER, LKOH):",
    value=",".join(portfolio_data.keys()) if portfolio_data else "SBER, LKOH"
)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# ===== Ввод депозита =====
deposit = st.number_input("💰 Внесенная сумма на счет:", min_value=0, step=1000)

# ===== Получаем данные с MOEX =====
moex_client = MoexClient()
moex_data = moex_client.fetch_data(tickers)
if not moex_data:
    st.error("Не удалось получить данные с MOEX")
    st.stop()

# ===== Создаем объект портфеля =====
user_inputs = {ticker: portfolio_data.get(ticker, {"qty": 0, "invested": 0.0}) for ticker in tickers}
portfolio = Portfolio(tickers, moex_data, user_inputs)

# ===== Функция для формирования таблицы =====
def get_portfolio_table(portfolio, deposit):
    rows = []
    total_value = portfolio._calculate_portfolio_total() + deposit

    for ticker in tickers:
        data = moex_data[ticker]
        inputs = user_inputs[ticker]

        last_price = data["LAST"] or 0
        qty = inputs["qty"]
        current_value = last_price * qty if last_price else 0
        portfolio_percent = (current_value / total_value * 100) if total_value > 0 else 0
        cap_percent = (data.get("ISSUECAPITALIZATION", 0) / portfolio.total_cap * 100
                       if data.get("ISSUECAPITALIZATION") and portfolio.total_cap > 0 else 0)

        action, buy_qty, buy_amount = RebalanceCalculator.calculate_rebalance(
            {
                "portfolio_percent": portfolio_percent,
                "cap_percent": cap_percent,
                "last_price": last_price,
                "qty": qty
            },
            total_value,
            portfolio.total_cap,
            deposit  # free_cash
        )

        rows.append([
            ticker,
            qty,
            last_price,
            current_value,
            f"{portfolio_percent:.2f}%",
            f"{cap_percent:.2f}%" if cap_percent else "N/A",
            action,
            buy_qty,
            buy_amount
        ])

    df = pd.DataFrame(rows, columns=[
        "Тикер", "Кол-во", "Цена", "Стоимость", "Доля, %", "Кап.доля, %", "Действие", "Купить шт", "Сумма покупки"
    ])
    return df, total_value

# ===== Форма для покупки/докупки бумаги =====
st.subheader("➕ Добавить или докупить бумагу")

with st.form(key="add_stock_form"):
    new_ticker = st.text_input("Тикер бумаги", value="", key="ticker_input")
    new_qty = st.number_input("Количество акций", min_value=0, step=1, value=0, key="qty_input")
    new_price = st.number_input("Цена за акцию, ₽", min_value=0.0, step=1.0, value=0.0, key="price_input")
    submit_button = st.form_submit_button("Купить")

    if submit_button:
        if new_ticker and new_qty > 0 and new_price > 0:
            invested = new_qty * new_price
            if new_ticker in st.session_state.portfolio_data:
                st.session_state.portfolio_data[new_ticker]['qty'] += new_qty
                st.session_state.portfolio_data[new_ticker]['invested'] += invested
            else:
                st.session_state.portfolio_data[new_ticker] = {
                    "qty": new_qty,
                    "invested": invested
                }
            save_portfolio(st.session_state.portfolio_data)
            st.success(f"{new_ticker} обновлен/добавлен: {st.session_state.portfolio_data[new_ticker]['qty']} шт., вложено {st.session_state.portfolio_data[new_ticker]['invested']:,.2f} ₽")
            st.session_state.update_flag = True
        else:
            st.warning("Введите корректные данные для покупки бумаги")

# ===== Вывод таблицы портфеля =====
if st.session_state.update_flag:
    portfolio_data = st.session_state.portfolio_data
    tickers = list(portfolio_data.keys())
    user_inputs = {ticker: portfolio_data[ticker] for ticker in tickers}
    portfolio = Portfolio(tickers, moex_data, user_inputs)
    st.session_state.update_flag = False

st.subheader("📊 Текущий портфель")
df, total_value = get_portfolio_table(portfolio, deposit)
st.dataframe(df.style.format({"Цена": "{:,.2f}", "Стоимость": "{:,.2f}", "Сумма покупки": "{:,.2f}"}))

st.subheader(f"💵 Общая стоимость портфеля: {portfolio._calculate_portfolio_total():,.2f} ₽")
st.subheader(f"💰 Общая сумма с депозитом: {total_value:,.2f} ₽")
