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
        self.index_history_url = "https://iss.moex.com/iss/engines/stock/markets/index/analytics/securities.xml"

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
        """
        try:
            from datetime import datetime, timedelta
            
            # Рассчитываем дату days дней назад
            target_date = datetime.now() - timedelta(days=days)
            from_date = (target_date - timedelta(days=10)).strftime("%Y-%m-%d")
            till_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Используем другой endpoint для истории индексов
            url = f"https://iss.moex.com/iss/engines/stock/markets/index/history.xml?securities={index_code}&from={from_date}&till={till_date}&boardid=SNDX"
            response = requests.get(url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
            # Ищем данные в marketdata - там должны быть исторические значения
            marketdata = root.find(".//data[@id='marketdata']")
            if marketdata is not None:
                rows_elem = marketdata.find('rows')
                if rows_elem is not None:
                    rows = rows_elem.findall('row')
                    
                    # Фильтруем строки с нужным индексом и датой
                    best_match = None
                    best_date_diff = float('inf')
                    
                    for row in rows:
                        secid = row.get("SECID")
                        if secid != index_code:
                            continue
                        
                        trade_date_str = row.get("TRADEDATE")
                        if not trade_date_str:
                            continue
                        
                        try:
                            trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d")
                            date_diff = abs((trade_date - target_date).days)
                            
                            # Берем ближайшую дату к целевой
                            if date_diff < best_date_diff:
                                best_date_diff = date_diff
                                best_match = row
                        except ValueError:
                            continue
                    
                    if best_match:
                        # Пробуем получить VALUE, затем CLOSE, затем LAST
                        value = best_match.get("VALUE") or best_match.get("CLOSE") or best_match.get("LAST")
                        if value:
                            return float(value)
            
            # Если не нашли через marketdata, пробуем получить из history блока
            history_data = root.find(".//data[@id='history']")
            if history_data is not None:
                rows_elem = history_data.find('rows')
                if rows_elem is not None:
                    rows = rows_elem.findall('row')
                    # Проверяем, содержатся ли здесь фактические данные
                    if rows and 'TRADEDATE' in rows[0].attrib and 'SECID' in rows[0].attrib:
                        best_match = None
                        best_date_diff = float('inf')
                        
                        for row in rows:
                            secid = row.get("SECID")
                            if secid != index_code:
                                continue
                            
                            trade_date_str = row.get("TRADEDATE")
                            if not trade_date_str:
                                continue
                            
                            try:
                                trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d")
                                date_diff = abs((trade_date - target_date).days)
                                if date_diff < best_date_diff:
                                    best_date_diff = date_diff
                                    best_match = row
                            except ValueError:
                                continue
                        
                        if best_match:
                            value = best_match.get("VALUE") or best_match.get("CLOSE") or best_match.get("LAST")
                            if value:
                                return float(value)
            
            print(f"⚠️ Не найдено значение индекса {index_code} за период ~{days} дней назад")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка получения истории индекса: {e}")
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