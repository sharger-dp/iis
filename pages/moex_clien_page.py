import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MoexClient:
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.xml"
        self.index_url = "https://iss.moex.com/iss/engines/stock/markets/index/securities.xml"
        self.index_history_url = "https://iss.moex.com/iss/engines/stock/markets/index/securities/IMOEX/candles.xml"

    @staticmethod
    def _safe_float(value):
        try:
            return float(value) if value and value != 'N/A' else None
        except:
            return None

    def fetch_data(self, tickers):
        if not tickers:
            return {}
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()

            if not response.content:
                logger.warning("Получен пустой ответ от сервера")
                return {}
            root = ET.fromstring(response.content)
            return self._parse_xml(root, tickers)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка подключения: {e}")
            return None
        except ET.ParseError:
            logger.error("Ошибка обработки XML-данных")
            return None

    def get_rts_index_price(self):
        """Получить текущую цену индекса IMOEX"""
        try:
            response = requests.get(self.index_url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            # Находим блок <data id="marketdata">
            marketdata = root.find(".//data[@id='marketdata']")
            if marketdata is None:
                print("⚠️ Не найден блок marketdata")
                return None
            # Ищем все <row> внутри него
            for row in marketdata.findall(".//row"):
                secid = row.get("SECID")
                if secid == "IMOEX":
                    last_value = row.get("LAST") or row.get("LASTVALUE")
                    if last_value:
                        return float(last_value)
                    else:
                        print(f"⚠️ У {secid} отсутствует поле LAST или LASTVALUE")
                        return None

            print("⚠️ IMOEX не найден в marketdata")
            return None
        except Exception as e:
            print(f"❌ Ошибка получения данных индекса: {e}")
            return None
    
    def get_index_history(self, index_code="IMOEX", days=30):
        """
        Получить исторические данные индекса за указанное количество дней.
        Возвращает значение индекса на дату days дней назад.
        Использует endpoint candles.xml с interval=24 (дневные свечи)
        """
        try:
            from datetime import datetime, timedelta
            
            # Рассчитываем даты для запроса
            till_date = datetime.now()
            from_date = till_date - timedelta(days=days + 15)
            
            from_date_str = from_date.strftime("%Y-%m-%d")
            till_date_str = till_date.strftime("%Y-%m-%d")
            
            # Формируем URL в правильном формате
            url = f"{self.index_history_url}?interval=24&from={from_date_str}&till={till_date_str}&limit=1000"
            
            print(f"🔍 Запрос к MOEX: {url}")
            
            response = requests.get(url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
            # Находим блок с данными свечей
            candles_data = root.find(".//data[@id='candles']")
            if candles_data is None:
                print("⚠️ Не найден блок candles в ответе")
                return None
                
            rows_elem = candles_data.find('rows')
            if rows_elem is None:
                print("⚠️ Не найдены строки с данными свечей")
                return None
                
            rows = rows_elem.findall('row')
            if not rows:
                print(f"⚠️ Нет данных свечей для {index_code}")
                return None
            
            print(f"✅ Получено {len(rows)} записей свечей")
            
            # Целевая дата (days дней назад)
            target_date = datetime.now() - timedelta(days=days)
            print(f"🎯 Целевая дата: {target_date.strftime('%Y-%m-%d')}")
            
            # Ищем ближайшую свечу к целевой дате (не более чем на 5 дней отличающуюся)
            best_match = None
            best_date_diff = float('inf')
            
            for row in rows:
                trade_date_str = row.get("begin") or row.get("end")
                if not trade_date_str:
                    continue
                
                try:
                    # Парсим дату из формата ISO 8601 (например, 2024-01-15T00:00:00 или 2024-01-15 00:00:00)
                    if 'T' in trade_date_str:
                        trade_date = datetime.strptime(trade_date_str.split('T')[0], "%Y-%m-%d")
                    elif ' ' in trade_date_str:
                        trade_date = datetime.strptime(trade_date_str.split(' ')[0], "%Y-%m-%d")
                    else:
                        trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d")
                    
                    date_diff = abs((trade_date - target_date).days)
                    
                    # Берем запись не старше 7 дней от целевой даты и ближе всех к ней
                    if date_diff <= 7 and date_diff < best_date_diff:
                        best_date_diff = date_diff
                        best_match = row
                        print(f"  📅 Найдена свеча за {trade_date.strftime('%Y-%m-%d')} (разница: {date_diff} дн.)")
                except ValueError as e:
                    print(f"  ⚠️ Ошибка парсинга даты {trade_date_str}: {e}")
                    continue
            
            if best_match is not None:
                # Для свечей используем close цену
                value = best_match.get("close") or best_match.get("CLOSE")
                begin_date = best_match.get("begin", "N/A")
                if value:
                    print(f"✅ Найдено значение индекса {value} за {begin_date}")
                    return float(value)
                else:
                    print(f"⚠️ У свечи за {begin_date} отсутствует поле close")
            
            # Если не нашли близкую дату, берем самую свежую (последнюю) из доступных
            if rows:
                latest_row = rows[-1]  # Берем последнюю (самую свежую) запись
                value = latest_row.get("close") or latest_row.get("CLOSE")
                begin_date = latest_row.get("begin", "N/A")
                if value:
                    print(f"⚠️ Используем ближайшее доступное значение {value} за {begin_date}")
                    return float(value)
            
            # Если совсем ничего не нашли - возвращаем None
            logger.warning(f"Не найдено значение индекса {index_code} за период ~{days} дней назад")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка получения истории индекса: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_xml(self, root, tickers):
        data = {ticker: {'SECNAME': 'N/A', 'LAST': None, 'ISSUECAPITALIZATION': None}
                for ticker in tickers}

        self._parse_securities(root, data)
        self._parse_marketdata(root, data)
        return data

    def _parse_securities(self, root, data):
        security_rows = root.find(".//data[@id='securities']/rows")
        if security_rows:
            for row in security_rows.findall('row'):
                secid = row.attrib.get('SECID')
                if secid in data:
                    data[secid]['SECNAME'] = row.attrib.get('SECNAME', 'N/A')

    def _parse_marketdata(self, root, data):
        market_rows = root.find(".//data[@id='marketdata']/rows")
        if market_rows:
            for row in market_rows.findall('row'):
                secid = row.attrib.get('SECID')
                if secid in data:
                    # Пробуем получить LAST, если пусто - используем MARKETPRICE
                    last = self._safe_float(row.attrib.get('LAST'))
                    if last is None:
                        last = self._safe_float(row.attrib.get('MARKETPRICE'))
                    data[secid]['LAST'] = last
                    
                    cap = row.attrib.get('ISSUECAPITALIZATION')
                    data[secid]['ISSUECAPITALIZATION'] = self._safe_float(cap)