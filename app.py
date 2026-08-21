import streamlit as st
import pandas as pd
import json
import random
from pages.rebalance_calc_page import RebalanceCalculator
from pages.moex_clien_page import MoexClient
from pages.portfolio_page import Portfolio

# Настройка страницы с современным дизайном
st.set_page_config(
    page_title="Инвестиционный Портфель",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили для современного интерфейса
st.markdown("""
<style>
    /* Основной фон и шрифты */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Карточки метрик */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Заголовки */
    h1, h2, h3, h4, h5 {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Метрики */
    .stMetric {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Таблицы */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Кнопки */
    .stButton > button {
        background: linear-gradient(45deg, #FF6B6B, #EE5A6F);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
    }
    
    /* Поля ввода */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.9);
    }
    
    /* Сайдбар */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2D3748 0%, #1A202C 100%);
    }
    
    /* Уведомления */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Заголовок с логотипом
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("<div style='font-size: 48px;'>📊</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='margin-top: 10px;'>Инвестиционный Портфель</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.8); font-size: 18px;'>Профессиональная система управления активами с автоматической ребалансировкой</p>", unsafe_allow_html=True)

st.markdown("---", unsafe_allow_html=True)

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

# ===== Ввод тикеров и депозита в карточках =====
col_input1, col_input2 = st.columns(2)
with col_input1:
    tickers_input = st.text_input(
        "🎫 Тикеры через запятую",
        value=",".join(portfolio_data.keys()) if portfolio_data else "SBER, LKOH",
        help="Введите тикеры бумаг, которые хотите отслеживать"
    )
input_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

with col_input2:
    deposit = st.number_input(
        "💰 Свободные средства (₽)", 
        min_value=0, 
        step=1000,
        help="Укажите доступные средства для инвестиций"
    )

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

# Отображение ключевых метрик в виде карточек
st.markdown("### 📊 Ключевые показатели портфеля")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 Вложено средств",
        value=f"{total_invested:,.0f} ₽",
        delta=None
    )

with col2:
    st.metric(
        label="💵 Стоимость портфеля",
        value=f"{current_value:,.0f} ₽",
        delta=None
    )

with col3:
    delta_color = "normal" if profit_percentage >= 0 else "inverse"
    st.metric(
        label="📈 Доходность",
        value=f"{profit_percentage:.2f}%",
        delta=f"{profit_percentage:.2f}%" if profit_percentage != 0 else None,
        delta_color=delta_color
    )

with col4:
    delta_color = "normal" if profit_amount >= 0 else "inverse"
    st.metric(
        label="➕ Чистая прибыль",
        value=f"{profit_amount:,.0f} ₽",
        delta=f"{profit_amount:,.0f} ₽" if profit_amount != 0 else None,
        delta_color=delta_color
    )

st.markdown("---", unsafe_allow_html=True)

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

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📊 Рост портфеля (без депозита)")
                color = "green" if change_rub > 0 else ("red" if change_rub < 0 else "gray")
                st.markdown(
                    f"<span style='font-size:22px; color:{color}'>{change_rub:,.2f} ₽ ({change_pct:+.2f}%)</span>",
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown("#### 📈 Средний рост в день")
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
            portfolio_percent,  # ← Теперь число!
            cap_percent if cap_percent else 0,  # ← Теперь число!
            action,
            buy_qty,
            buy_amount
        ])

    df = pd.DataFrame(rows, columns=[
        "Тикер", "Кол-во", "Цена", "Стоимость", "Доля, %", "Кап.доля, %", "Действие", "Купить шт", "Сумма покупки"
    ])
    return df, total_value

# ===== Форма для добавления/докупки бумаги =====
st.markdown("### ➕ Добавление новой позиции")

# Ввод тикера вне формы (динамическое подтягивание цены)
col_ticker1, col_ticker2 = st.columns([3, 1])
with col_ticker1:
    new_ticker = st.text_input(
        "Тикер бумаги", 
        value="", 
        help="Введите тикер, например: SBER, LKOH, YNDX",
        placeholder="SBER"
    ).strip().upper()

current_price = None
if new_ticker:
    try:
        tmp_raw = moex_client.fetch_data([new_ticker]) or {}
        tmp = tmp_raw.get(new_ticker, {})
        current_price = tmp.get("LAST")
    except Exception as e:
        st.warning(f"⚠️ Ошибка при получении данных с MOEX: {e}")

if current_price is not None:
    st.success(f"**💰 Текущая цена {new_ticker}:** {current_price:,.2f} ₽")
elif new_ticker:
    st.warning("❌ Не удалось получить цену. Проверьте правильность тикера.")

st.markdown("---", unsafe_allow_html=True)

with st.form(key="add_stock_form", clear_on_submit=False):
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        new_price = st.number_input(
            "Цена за акцию (₽)",
            min_value=0.01,
            value=float(current_price) if current_price else 0.01,
            step=0.01
        )
    
    with col_f2:
        new_qty = st.number_input(
            "Количество акций", 
            min_value=1, 
            step=1
        )
    
    with col_f3:
        # Пустая колонка для выравнивания кнопки
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    
    submit_button = st.form_submit_button(
        "➕ Добавить в портфель", 
        use_container_width=False
    )

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
st.markdown("### 📋 Детализация портфеля")
df, total_value = get_portfolio_table(portfolio, deposit)

# Стильное отображение таблицы
st.data_editor(
    df,
    column_config={
        "Тикер": st.column_config.TextColumn(width="small"),
        "Кол-во": st.column_config.NumberColumn(format="%d шт."),
        "Цена": st.column_config.NumberColumn(format="%.2f ₽"),
        "Стоимость": st.column_config.NumberColumn(format="%.0f ₽"),
        "Доля, %": st.column_config.NumberColumn(format="%.2f %%"),
        "Кап.доля, %": st.column_config.NumberColumn(format="%.2f %%"),
        "Действие": st.column_config.TextColumn(width="medium"),
        "Купить шт": st.column_config.NumberColumn(format="%d"),
        "Сумма покупки": st.column_config.NumberColumn(format="%.0f ₽")
    },
    hide_index=True,
    disabled=True,
    use_container_width=True
)

st.markdown("---", unsafe_allow_html=True)

# ===== Сравнение с рыночным индексом =====
st.markdown("### 📊 Сравнение с рыночным индексом RTS")

# Получаем текущую цену индекса
moex_client = MoexClient()
market_index_current = moex_client.get_rts_index_price()
# Историческая цена индекса (например, за 30 дней назад)
# Для простоты используем фиктивные данные (в реальности нужно загружать историю)
market_index_historical = 2171.47  # Пример: цена индекса 30 дней назад

# Рассчитаем доходность индекса
if market_index_current and market_index_historical > 0:
    market_index_return = ((market_index_current - market_index_historical) / market_index_historical) * 100
else:
    market_index_return = 0.0

# Рассчитаем доходность портфеля
portfolio_return = ((current_value - total_invested) / total_invested) * 100 if total_invested > 0 else 0.0

# Отображение в виде карточек
col_idx1, col_idx2 = st.columns(2)

with col_idx1:
    delta_color_p = "normal" if portfolio_return >= 0 else "inverse"
    st.metric(
        label="📈 Доходность портфеля",
        value=f"{portfolio_return:.2f}%",
        delta=f"{portfolio_return:.2f}%" if portfolio_return != 0 else None,
        delta_color=delta_color_p
    )

with col_idx2:
    delta_color_i = "normal" if market_index_return >= 0 else "inverse"
    st.metric(
        label="🏛️ Доходность индекса RTS",
        value=f"{market_index_return:.2f}%",
        delta=f"{market_index_return:.2f}%" if market_index_return != 0 else None,
        delta_color=delta_color_i
    )

# Визуальное сравнение
if portfolio_return > market_index_return:
    st.success(f"✅ Ваш портфель превосходит индекс RTS на {(portfolio_return - market_index_return):.2f}%")
elif portfolio_return < market_index_return:
    st.warning(f"⚠️ Ваш портфель отстаёт от индекса RTS на {(market_index_return - portfolio_return):.2f}%")
else:
    st.info("ℹ️ Доходность портфеля совпадает с доходностью индекса")

# Футер
st.markdown("---", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: rgba(255,255,255,0.6); padding: 20px;'>",
    unsafe_allow_html=True
)
st.markdown(
    "**Инвестиционный Портфель** | Профессиональная система управления активами © 2024",
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)