import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Конфигурация PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'portfolio_db',
    'user': 'postgres',
    'password': 'postgres'
}

def get_connection():
    """Получить соединение с БД PostgreSQL"""
    conn = psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    return conn

def init_db():
    """Инициализация базы данных - создание таблиц"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица для хранения позиций портфеля
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_positions (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(50) UNIQUE NOT NULL,
            qty INTEGER NOT NULL DEFAULT 0,
            invested REAL NOT NULL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для истории стоимости портфеля
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL UNIQUE,
            portfolio_value REAL NOT NULL,
            total_with_deposit REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для истории транзакций (опционально)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(50) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            qty INTEGER NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# ===== Функции для работы с позициями портфеля =====

def load_portfolio() -> Dict[str, Dict[str, Any]]:
    """Загрузить все позиции портфеля из БД"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT ticker, qty, invested FROM portfolio_positions ORDER BY ticker")
    rows = cursor.fetchall()
    conn.close()
    
    portfolio = {}
    for row in rows:
        portfolio[row['ticker']] = {
            'qty': row['qty'],
            'invested': float(row['invested']) if row['invested'] else 0.0
        }
    return portfolio

def save_portfolio_position(ticker: str, qty: int, invested: float):
    """Сохранить или обновить позицию в портфеле"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, существует ли уже позиция
    cursor.execute("SELECT id FROM portfolio_positions WHERE ticker = %s", (ticker,))
    existing = cursor.fetchone()
    
    if existing:
        # Обновляем существующую позицию
        cursor.execute("""
            UPDATE portfolio_positions 
            SET qty = %s, invested = %s, updated_at = CURRENT_TIMESTAMP
            WHERE ticker = %s
        """, (qty, invested, ticker))
    else:
        # Добавляем новую позицию
        cursor.execute("""
            INSERT INTO portfolio_positions (ticker, qty, invested)
            VALUES (%s, %s, %s)
        """, (ticker, qty, invested))
    
    conn.commit()
    conn.close()

def delete_portfolio_position(ticker: str):
    """Удалить позицию из портфеля"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio_positions WHERE ticker = %s", (ticker,))
    conn.commit()
    conn.close()

def get_all_tickers() -> List[str]:
    """Получить список всех тикеров в портфеле"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM portfolio_positions ORDER BY ticker")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ===== Функции для работы с историей портфеля =====

def load_history() -> List[Dict[str, Any]]:
    """Загрузить историю стоимости портфеля из БД"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT date, portfolio_value, total_with_deposit 
        FROM portfolio_history 
        ORDER BY date
    """)
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'date': str(row['date']),
            'portfolio_value': float(row['portfolio_value']) if row['portfolio_value'] else 0.0,
            'total_with_deposit': float(row['total_with_deposit']) if row['total_with_deposit'] else 0.0
        })
    return history

def save_history_entry(date: str, portfolio_value: float, total_with_deposit: float):
    """Сохранить запись в историю портфеля"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, существует ли уже запись за эту дату
    cursor.execute("SELECT id FROM portfolio_history WHERE date = %s", (date,))
    existing = cursor.fetchone()
    
    if existing:
        # Обновляем существующую запись
        cursor.execute("""
            UPDATE portfolio_history 
            SET portfolio_value = %s, total_with_deposit = %s
            WHERE date = %s
        """, (portfolio_value, total_with_deposit, date))
    else:
        # Добавляем новую запись
        cursor.execute("""
            INSERT INTO portfolio_history (date, portfolio_value, total_with_deposit)
            VALUES (%s, %s, %s)
        """, (date, portfolio_value, total_with_deposit))
    
    conn.commit()
    conn.close()

def clear_history():
    """Очистить всю историю портфеля"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio_history")
    conn.commit()
    conn.close()

# ===== Функции для работы с транзакциями =====

def add_transaction(ticker: str, transaction_type: str, qty: int, price: float, total_amount: float):
    """Добавить запись о транзакции"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (ticker, transaction_type, qty, price, total_amount)
        VALUES (%s, %s, %s, %s, %s)
    """, (ticker, transaction_type, qty, price, total_amount))
    conn.commit()
    conn.close()

def get_transactions(ticker: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Получить список транзакций"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if ticker:
        cursor.execute("""
            SELECT ticker, transaction_type, qty, price, total_amount, transaction_date
            FROM transactions
            WHERE ticker = %s
            ORDER BY transaction_date DESC
            LIMIT %s
        """, (ticker, limit))
    else:
        cursor.execute("""
            SELECT ticker, transaction_type, qty, price, total_amount, transaction_date
            FROM transactions
            ORDER BY transaction_date DESC
            LIMIT %s
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    transactions = []
    for row in rows:
        transactions.append({
            'ticker': row['ticker'],
            'transaction_type': row['transaction_type'],
            'qty': row['qty'],
            'price': float(row['price']) if row['price'] else 0.0,
            'total_amount': float(row['total_amount']) if row['total_amount'] else 0.0,
            'transaction_date': str(row['transaction_date']) if row['transaction_date'] else None
        })
    return transactions

# ===== Функции миграции данных из JSON в PostgreSQL =====

def migrate_from_json_to_db():
    """Миграция данных из JSON файлов в базу данных PostgreSQL"""
    
    # Инициализируем БД
    init_db()
    
    # Мигрируем данные портфеля
    portfolio_file = "portfolio_data.json"
    if os.path.exists(portfolio_file):
        with open(portfolio_file, "r", encoding="utf-8") as f:
            portfolio_data = json.load(f)
        
        for ticker, data in portfolio_data.items():
            save_portfolio_position(
                ticker=ticker,
                qty=data.get('qty', 0),
                invested=data.get('invested', 0.0)
            )
        print(f"✅ Миграция портфеля завершена: {len(portfolio_data)} позиций")
    
    # Мигрируем историю
    history_file = "portfolio_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)
        
        for entry in history_data:
            save_history_entry(
                date=entry.get('date', ''),
                portfolio_value=entry.get('portfolio_value', 0.0),
                total_with_deposit=entry.get('total_with_deposit', 0.0)
            )
        print(f"✅ Миграция истории завершена: {len(history_data)} записей")
    
    print("🎉 Миграция данных в PostgreSQL завершена успешно!")

if __name__ == "__main__":
    # Инициализация БД и миграция данных при запуске скрипта
    init_db()
    migrate_from_json_to_db()
