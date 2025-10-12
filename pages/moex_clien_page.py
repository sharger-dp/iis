import requests
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

class MoexClient:
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.xml"
        self.index_url = "https://iss.moex.com/iss/engines/stock/markets/index/securities.xml"

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
                    data[secid]['LAST'] = self._safe_float(row.attrib.get('LAST'))
                    cap = row.attrib.get('ISSUECAPITALIZATION')
                    data[secid]['ISSUECAPITALIZATION'] = self._safe_float(cap)