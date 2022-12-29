import csv
import datetime
import sqlite3

import pandas as pd


class ExchangeRateConverter:
    """Класс, используемый для представления конвертатора курсов валют."""

    currencies = {'BYR', 'USD', 'EUR', 'KZT', 'UAH', 'AZN', 'KGS', 'UZS'}

    def __init__(self, exchange_rate_db_filename: str):
        """Инициализирует экземпляр ExchangeRateConverter.

        Args:
            exchange_rate_db_filename (str): Имя файла базы данных
        """
        self.exchange_rate = sqlite3.connect(exchange_rate_db_filename)

    def get_exchange_rate(self, currency: str, year: int, month: int):
        """Возвращает курс валюты в указанный месяц и год.

        Args:
            currency (str): Валюты
            year (int): Год
            month (int): Месяц

        Returns:
            float: Курс указанной валюты
        """
        if currency not in ExchangeRateConverter.currencies:
            return None
        cur = self.exchange_rate.cursor()
        date = f"{year}-{str(month).zfill(2)}"
        sql = f"SELECT {currency} FROM currencies WHERE date = '{date}'"
        cur.execute(sql)
        rate = cur.fetchone()
        cur.close()
        return rate[0]

    def convert_to_rubles_per_month_year(self, amount: float, currency: str, year: int, month: int):
        """Переводит валюту в рубли.

        Args:
            amount (float): Кол-во валюты
            currency (str): Валюта
            year (int): Год
            month (int): Месяц

        Returns:
            int: Рубли
        """
        if currency == 'RUR':
            return int(amount)
        rate = self.get_exchange_rate(currency, year, month)
        if rate is None:
            return None
        return int(amount * rate)

    def process_vacancies_file(self, vacancies_filename: str, result_filename: str):
        """Обрабатывает файл с вакансиями и сохраняет его в базу данных.

        Args:
            vacancies_filename (str): Имя файла с вакансиями
            result_filename (str): Имя обработанного результата
        """
        vacancies = open(vacancies_filename, 'r', encoding="utf-8-sig")
        reader = csv.reader(vacancies)
        next(reader)
        data = []
        for line in reader:
            name = line[0]
            salary_from = line[1]
            salary_to = line[2]
            salary_currency = line[3]
            published_at = datetime.datetime.strptime(line[5], '%Y-%m-%dT%H:%M:%S%z')
            if salary_from == salary_to == '' or salary_currency == '':
                salary = None
            elif (salary_from == '' and salary_to != '') or (salary_from != '' and salary_to == ''):
                if salary_from != "":
                    salary = self.convert_to_rubles_per_month_year(float(salary_from), salary_currency,
                                                                   published_at.year, published_at.month)
                else:
                    salary = self.convert_to_rubles_per_month_year(float(salary_to), salary_currency,
                                                                   published_at.year, published_at.month)
            else:
                salary = self.convert_to_rubles_per_month_year((float(salary_from) + float(salary_to)) / 2,
                                                               salary_currency, published_at.year, published_at.month)
            area = line[4]
            data.append([name, salary, area, published_at.strftime("%Y-%m-%dT%H:%M:%S%z")])
        conn = sqlite3.connect(result_filename)
        cur = conn.cursor()
        cur.execute("CREATE TABLE vacancies (name, salary, area_name, published_at)")
        cur.executemany("INSERT INTO vacancies VALUES(?, ?, ?, ?)", data)
        conn.commit()
        conn.close()


exchange_rate_converter = ExchangeRateConverter('currencies.sqlite')
exchange_rate_converter.process_vacancies_file('vacancies_dif_currencies.csv', 'vacancies.sqlite')
