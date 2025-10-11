import streamlit as st
import pandas as pd
import json
import random
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

# ===== Ввод тикеров (пользователь) =====
tickers_input = st.text_input(
    "Введите тикеры через запятую (например: SBER, LKOH):",
    value=",".join(portfolio_data.keys()) if portfolio_data else "SBER, LKOH"
)
input_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# ===== Ввод депозита =====
deposit = st.number_input("💰 Внесенная сумма на счет:", min_value=0, step=1000)

# ===== Собираем итоговый список тикеров (ввод пользователя + сохранённый портфель) =====
saved_tickers = list(st.session_state.portfolio_data.keys()) if st.session_state.portfolio_data else []
combined_tickers = sorted(set(input_tickers) | set(saved_tickers))

# ===== Получаем данные с MOEX для всех нужных тикеров =====
moex_client = MoexClient()
try:
    raw_moex = moex_client.fetch_data(combined_tickers) or {}
except Exception as e:
    raw_moex = {}
    st.warning(f"⚠️ Ошибка при получении данных с MOEX: {e}")

# ===== Гарантируем, что moex_data имеет ключи для всех combined_tickers (заглушки для отсутствующих) =====
moex_data = {}
for t in combined_tickers:
    if t in raw_moex and isinstance(raw_moex[t], dict):
        moex_data[t] = raw_moex[t]
    else:
        # заглушка — чтобы код не падал при отсутствии данных
        moex_data[t] = {"LAST": None, "ISSUECAPITALIZATION": 0}

if not moex_data and combined_tickers:
    st.error("Не удалось получить данные с MOEX для запрошенных тикеров.")
    st.stop()

# ===== Создаем объект портфеля =====
user_inputs = {ticker: portfolio_data.get(ticker, {"qty": 0, "invested": 0.0}) for ticker in combined_tickers}
portfolio = Portfolio(combined_tickers, moex_data, user_inputs)

# Рассчитаем общую сумму вложений
total_invested = deposit + sum(
    ticker_data.get("invested", 0) for ticker_data in st.session_state.portfolio_data.values()
)

# Рассчитаем текущую стоимость портфеля
current_value = portfolio._calculate_portfolio_total()

# Рассчитаем доходность
if total_invested > 0:
    profit_percentage = ((current_value - total_invested) / total_invested) * 100
else:
    profit_percentage = 0.0

# Рассчитаем чистую прибыль
profit_amount = current_value - total_invested
color_profit = "green" if profit_percentage >= 0 else "red"
color_amount = "green" if profit_amount >= 0 else "red"

st.markdown(f"<h3 style='color:{color_profit}'>📈 Доходность портфеля: {profit_percentage:.2f}%</h3>", unsafe_allow_html=True)
st.subheader(f"💰 Общая сумма вложений: {total_invested:,.2f} ₽")
st.subheader(f"💵 Общая стоимость портфеля: {portfolio._calculate_portfolio_total():,.2f} ₽")
st.markdown(f"<h3 style='color:{color_amount}'>➕ Чистая прибыль: {profit_amount:,.2f} ₽</h3>", unsafe_allow_html=True)

# ===== Функция для формирования таблицы =====
def get_portfolio_table(portfolio, deposit, history=None):
    rows = []
    total_value = portfolio._calculate_portfolio_total() + deposit

    import datetime
    history_file = "portfolio_history.json"

    def load_history():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_history(data):
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    history = load_history()
    today = datetime.date.today().isoformat()

    if not any(entry["date"] == today for entry in history):
        history.append({
            "date": today,
            "portfolio_value": portfolio._calculate_portfolio_total(),
            "total_with_deposit": total_value
        })
        save_history(history)

    st.subheader("📈 Динамика стоимости портфеля")

    if history:
        import altair as alt
        df_hist = pd.DataFrame(history)
        df_hist["date"] = pd.to_datetime(df_hist["date"])
        df_hist = df_hist.sort_values("date")

        st.write("Показать за период:")
        period = st.segmented_control(
            "Период",
            options=["7 дней", "30 дней", "90 дней", "Все время"],
            default="30 дней"
        )

        if period != "Все время":
            days = int(period.split()[0])
            cutoff_date = pd.Timestamp.today() - pd.Timedelta(days=days)
            df_filtered = df_hist[df_hist["date"] >= cutoff_date]
        else:
            df_filtered = df_hist.copy()

        base = alt.Chart(df_filtered).encode(
            x=alt.X("date:T", title="Дата"),
            tooltip=[
                alt.Tooltip("date:T", title="Дата"),
                alt.Tooltip("portfolio_value:Q", title="Портфель (₽)", format=",.0f"),
                alt.Tooltip("total_with_deposit:Q", title="С депозитом (₽)", format=",.0f")
            ]
        )

        line_portfolio = base.mark_line(color="#1f77b4", strokeWidth=2).encode(
            y=alt.Y("portfolio_value:Q", title="Стоимость (₽)")
        )

        line_total = base.mark_line(color="#2ca02c", strokeDash=[5, 3], strokeWidth=2).encode(
            y="total_with_deposit:Q"
        )

        chart = alt.layer(line_portfolio, line_total).properties(
            width="container",
            height=350,
            title=f"Изменение стоимости портфеля ({period.lower()})"
        ).interactive(bind_y=False)

        st.altair_chart(chart, use_container_width=True)

        if len(df_filtered) >= 2:
            start_val = df_filtered.iloc[0]["portfolio_value"]
            end_val = df_filtered.iloc[-1]["portfolio_value"]
            change_rub = end_val - start_val
            change_pct = (change_rub / start_val * 100) if start_val > 0 else 0

            start_total = df_filtered.iloc[0]["total_with_deposit"]
            end_total = df_filtered.iloc[-1]["total_with_deposit"]
            change_total_rub = end_total - start_total
            change_total_pct = (change_total_rub / start_total * 100) if start_total > 0 else 0

            days_diff = (df_filtered.iloc[-1]["date"] - df_filtered.iloc[0]["date"]).days
            avg_daily_return = (change_pct / days_diff) if days_diff > 0 else 0
            avg_daily_total_return = (change_total_pct / days_diff) if days_diff > 0 else 0

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### 📊 Доходность портфеля (без депозита)")
                color = "green" if change_rub > 0 else ("red" if change_rub < 0 else "gray")
                st.markdown(
                    f"<span style='font-size:22px; color:{color}'>{change_rub:,.2f} ₽ ({change_pct:+.2f}%)</span>",
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown("#### 💰 Доходность с депозитом")
                color = "green" if change_total_rub > 0 else ("red" if change_total_rub < 0 else "gray")
                st.markdown(
                    f"<span style='font-size:22px; color:{color}'>{change_total_rub:,.2f} ₽ ({change_total_pct:+.2f}%)</span>",
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown("#### 📈 Средняя доходность в день")
                avg_color = "green" if avg_daily_total_return > 0 else ("red" if avg_daily_total_return < 0 else "gray")
                st.markdown(
                    f"<span style='font-size:22px; color:{avg_color}'>{avg_daily_total_return:+.2f}%/день</span>",
                    unsafe_allow_html=True
                )

            df_filtered["daily_change_pct"] = df_filtered["portfolio_value"].pct_change() * 100
            df_filtered = df_filtered.dropna(subset=["daily_change_pct"])

            st.markdown("### 📊 Дневная доходность")
            bar_chart = alt.Chart(df_filtered).mark_bar().encode(
                x=alt.X("date:T", title="Дата"),
                y=alt.Y("daily_change_pct:Q", title="Доходность за день (%)"),
                color=alt.condition(
                    alt.datum.daily_change_pct > 0,
                    alt.value("#2ca02c"),
                    alt.value("#d62728")
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Дата"),
                    alt.Tooltip("daily_change_pct:Q", title="Доходность (%)", format="+.2f")
                ]
            ).properties(height=180, width="container")

            st.altair_chart(bar_chart, use_container_width=True)

        else:
            st.info("Недостаточно данных для расчёта доходности за выбранный период.")
    else:
        st.info("История стоимости пока отсутствует. Она начнёт формироваться после первого обновления портфеля.")

    # ===== Используем combined_tickers из внешнего контекста =====
    for ticker in combined_tickers:
        data = moex_data.get(ticker, {})
        last_price = data.get("LAST") or 0
        inputs = portfolio_data.get(ticker, {"qty": 0, "invested": 0.0})
        qty = inputs.get("qty", 0)
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
            deposit
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

# ===== Форма для добавления/докупки бумаги =====
st.subheader("➕ Добавление/докупка бумаги")

# Ввод тикера вне формы (динамическое подтягивание цены)
new_ticker = st.text_input("🎫 Тикер", value="", help="Пример: SBER, LKOH").strip().upper()

current_price = None
if new_ticker:
    try:
        tmp_raw = moex_client.fetch_data([new_ticker]) or {}
        tmp = tmp_raw.get(new_ticker, {})
        current_price = tmp.get("LAST")
    except Exception as e:
        st.warning(f"⚠️ Ошибка при получении данных с MOEX: {e}")

if current_price is not None:
    st.info(f"💰 Текущая цена {new_ticker}: {current_price:,.2f} ₽")
else:
    if new_ticker:
        st.warning("❌ Не удалось получить цену. Проверь тикер.")

with st.form(key="add_stock_form"):
    new_price = st.number_input(
        "💵 Цена за акцию",
        min_value=0.01,
        value=float(current_price) if current_price else 0.01,
        step=0.01
    )

    new_qty = st.number_input("🔢 Количество", min_value=1, step=1)
    submit_button = st.form_submit_button("💼 Добавить в портфель")

if submit_button:
    if not new_ticker:
        st.error("⚠️ Укажите тикер")
    elif new_qty <= 0:
        st.error("⚠️ Количество должно быть больше 0")
    elif new_price <= 0:
        st.error("⚠️ Цена должна быть больше 0")
    else:
        total_invested_for_security = new_price * new_qty

        if new_ticker in st.session_state.portfolio_data:
            existing = st.session_state.portfolio_data[new_ticker]
            st.session_state.portfolio_data[new_ticker] = {
                "qty": existing["qty"] + new_qty,
                "invested": existing["invested"] + total_invested_for_security
            }
        else:
            st.session_state.portfolio_data[new_ticker] = {
                "qty": new_qty,
                "invested": total_invested_for_security
            }

        save_portfolio(st.session_state.portfolio_data)
        st.success(f"✅ {new_qty} шт. {new_ticker} добавлено в портфель за {total_invested_for_security:,.2f} ₽")
        st.session_state.update_flag = True

# ===== Если был добавлен новый актив — обновляем moex_data и объект Portfolio =====
if st.session_state.update_flag:
    portfolio_data = st.session_state.portfolio_data
    saved_tickers = list(portfolio_data.keys()) if portfolio_data else []
    input_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    combined_tickers = sorted(set(input_tickers) | set(saved_tickers))

    try:
        raw_moex = moex_client.fetch_data(combined_tickers) or {}
    except Exception as e:
        raw_moex = {}
        st.warning(f"⚠️ Ошибка при получении данных с MOEX: {e}")

    # снова формируем moex_data с заглушками
    moex_data = {}
    for t in combined_tickers:
        moex_data[t] = raw_moex.get(t, {"LAST": None, "ISSUECAPITALIZATION": 0})

    user_inputs = {ticker: portfolio_data.get(ticker, {"qty": 0, "invested": 0.0}) for ticker in combined_tickers}
    portfolio = Portfolio(combined_tickers, moex_data, user_inputs)
    st.session_state.update_flag = False

# ===== Вывод таблицы портфеля =====
df, total_value = get_portfolio_table(portfolio, deposit)
st.dataframe(df.style.format({"Цена": "{:,.2f}", "Стоимость": "{:,.2f}", "Сумма покупки": "{:,.2f}"}))

st.subheader(f"💵 Общая стоимость портфеля: {portfolio._calculate_portfolio_total():,.2f} ₽")
st.subheader(f"💰 Общая сумма с депозитом: {total_value:,.2f} ₽")
