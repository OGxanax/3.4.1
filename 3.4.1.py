import numpy as np
import pandas as pd


class ExchangeRateConverter:
    """Класс, используемый для представления конвертатора курсов валют."""

    def __init__(self, exchange_rate_filename: str):
        """Инициализирует экземпляр ExchangeRateConverter.

        Args:
            exchange_rate_filename (str): Имя файла с курсами валют
        """
        self.load_exchange_rate(exchange_rate_filename)

    def load_exchange_rate(self, exchange_rate_filename: str):
        """Загружает курсы валют из файла.

        Args:
            exchange_rate_filename (str): Имя файла с курсами валют
        """
        self.exchange_rate = pd.read_csv(exchange_rate_filename, delimiter=',')
        self.exchange_rate = self.exchange_rate.set_index('date')

    def convert_to_rubles(self, year: int, month: int, amount: float, currency_identifier: str):
        """Переводит валюту в рубли.

        Args:
            year (int): Год
            month (int): Месяц
            amount (float): Кол-во валюты
            currency_identifier (float): Валюта

        Returns:
            int: Рубли
        """
        if currency_identifier == 'RUR':
            return amount
        if currency_identifier not in self.exchange_rate.columns:
            return None
        date = f'{year}-{month}'
        rate = self.exchange_rate.loc[[date]][currency_identifier][0]
        if np.isnan(rate):
            return None
        return int(rate * amount)

    def convert_row_to_rubles(self, row):
        """Переводит pandas строку в рубли.

        Args:
            row: Pandas строка

        Returns:
            int: Результат конвертации
        """
        salary_currency = row['salary_currency']
        if pd.isna(salary_currency):
            return np.nan
        year, month = row['published_at'][:4], row['published_at'][5:7]
        return self.convert_to_rubles(year, month, row['salary'], salary_currency)

    def parse_vacancies(self, vacancies_filename: str, result_filename: str):
        """Обрабатывает вакансии и сохраняет результат в csv файл.

        Args:
            vacancies_filename (str): Имя файла с вакансиями
            result_filename (str): Имя файла после обработки
        """
        data = pd.read_csv(vacancies_filename, delimiter=',')
        data['salary'] = data[['salary_from', 'salary_to']].mean(1)
        data['salary'] = data.apply(lambda r: self.convert_row_to_rubles(r), 1)
        data[['name', 'salary', 'area_name', 'published_at']].to_csv(result_filename, encoding="utf-8", index=False)


exchange_rate_converter = ExchangeRateConverter('currencies.csv')
exchange_rate_converter.parse_vacancies('vacancies_dif_currencies.csv', 'parsed_vacancies.csv')
