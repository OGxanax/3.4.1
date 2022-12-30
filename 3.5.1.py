import pandas as pd
import xmltodict
import requests
import sqlite3
import time
from datetime import datetime


class ExchangeRateParser:
    """Класс, используемый для представления парсера курсов валют."""

    currencies = ['BYR', 'USD', 'EUR', 'KZT', 'UAH', 'AZN', 'KGS', 'UZS']

    @staticmethod
    def fetch_exchange_rate_per_year_month(year: int, month: int):
        """Парсит курс валют в указанный месяц и год.

        Args:
            year (int): Год
            month (int): Месяц

        Returns:
            dict: Курсы валют в указанный месяц и год
        """
        exchange_rate = {}
        date = f'01/{str(month).zfill(2)}/{year}'
        url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}&d=0'
        resp = requests.get(url)
        resp.close()
        valutes = xmltodict.parse(resp.content)['ValCurs']['Valute']
        for val in valutes:
            if val['CharCode'] in ExchangeRateParser.currencies:
                value = val['Value'].replace(',', '.')
                nominal = val['Nominal'].replace(',', '.')
                exchange_rate[val['CharCode']] = round(float(value) / float(nominal), 8)
        for currency in ExchangeRateParser.currencies:
            if currency not in exchange_rate:
                exchange_rate[currency] = None
        return exchange_rate

    @staticmethod
    def get_month_range_list(begin: datetime, end: datetime):
        """Возвращает список, состоящий из дат с промежутком в 1 месяц между указанными датами.

        Args:
            begin (datetime): Начальная дата
            end (datetime): Конечная дата

        Returns:
            list: Список дат
        """
        dates = []
        for year in range(begin.year, end.year + 1):
            for month in range(1, 12 + 1):
                dates.append(f'{year}-{str(month).zfill(2)}')
        return dates

    @staticmethod
    def parse_to_database(begin: datetime, end: datetime, result_filename):
        """Парсит курсы валют между указанными датами в базу данных.

        Args:
            begin (datetime): Начальная дата
            end (datetime): Конечная дата
            result_filename (str): Имя файла базы данных
        """
        currencies = {}
        for year in range(begin.year, end.year + 1):
            for month in range(1, 12 + 1):
                exchange_rate = ExchangeRateParser.fetch_exchange_rate_per_year_month(year, month)
                time.sleep(0.05)
                for currency in exchange_rate:
                    if currency not in currencies:
                        currencies[currency] = []
                    currencies[currency].append(exchange_rate[currency])
        date_index = ExchangeRateParser.get_month_range_list(begin, end)
        data = pd.DataFrame(currencies, index=date_index)
        data.index.name = 'date'
        cnx = sqlite3.connect(result_filename)
        data.to_sql('currencies', cnx)
        cnx.close()


ExchangeRateParser.parse_to_database(datetime(2003, 1, 1), datetime(2022, 12, 31), 'currencies.sqlite')
