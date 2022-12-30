import sqlite3
import pandas as pd


class DataSet:
    """Класс, используемый для представления данных вакансий.

    Attributes:
        vacancies_year_salaries (pd.DataFrame): Средняя зарплата по годам
        vacancies_year_count (pd.DataFrame): Количество вакансий по годам
        profession_salaries (pd.DataFrame): Средняя зарплата по выбранной профессии по годам
        profession_count (pd.DataFrame): Количество вакансий по выбранной профессии по годам
        vacancies_area_salaries (pd.DataFrame): Средняя зарплата по городам
        fractions (pd.DataFrame): Доли вакансий по городам
    """

    def process_statistics(self, db_filename: str, profession: str):
        """Рассчитывает статистику по выбранной профессии.

        Args:
            db_filename (str): Имя файла базы данных с вакансиями
            profession (str): Выбранная профессия
        """
        conn = sqlite3.connect(db_filename)
        self.vacancies_year_salaries = pd.DataFrame(pd.read_sql_query(
            """
        SELECT strftime('%Y', substr(published_at, 1, 10)) AS year,
		round(avg(salary)) AS salary FROM vacancies GROUP BY year;
        """
        , conn))
        self.vacancies_year_count = pd.DataFrame(pd.read_sql_query(
            """
        SELECT strftime('%Y', substr(published_at, 1, 10)) AS year,
		count(name) as count FROM vacancies GROUP BY year;
        """
        , conn))
        self.profession_salaries = pd.DataFrame(pd.read_sql_query(
            f"""
        SELECT strftime('%Y', substr(published_at, 1, 10)) AS year,
 		round(avg(salary)) AS profession_salary FROM vacancies WHERE name like '%{profession}%' GROUP BY year;
        """, conn))
        self.profession_count = pd.DataFrame(pd.read_sql_query(
            f"""
        SELECT strftime('%Y', substr(published_at, 1, 10)) AS year,
        count(name) as profession_count FROM vacancies WHERE name like '%{profession}%' GROUP BY year;
        """, conn))
        self.vacancies_area_salaries = pd.DataFrame(pd.read_sql_query(
            """
        SELECT area_name, round(avg(salary)) AS salary 
        FROM vacancies 
        GROUP BY area_name 
        HAVING CAST(count(area_name) as REAL) * 100 / (SELECT count(area_name) FROM vacancies) >= 1
        ORDER BY salary DESC
        LIMIT 10;
        """, conn))
        self.fractions = pd.DataFrame(pd.read_sql_query(
            """
        SELECT area_name, CAST(count(area_name) as REAL) * 100 / (SELECT count(area_name) FROM vacancies) AS percentage
        FROM vacancies 
        GROUP BY area_name 
        HAVING percentage >= 1
        ORDER BY percentage DESC
        LIMIT 10;
        """, conn))


class InputConnect:
    """Класс, используемый для обработки вводимых пользователем данных.

    Attributes:
        db_filename (str): Имя файла базы данных с вакансиями
    """

    def display_statistics(self, dataset: DataSet):
        """Выводит статистику.

        Args:
            dataset (DataSet): Данные вакансий
        """
        print(f'Динамика уровня зарплат по годам:\n{dataset.vacancies_year_salaries.to_string()}')
        print(f'Динамика количества вакансий по годам:\n{dataset.vacancies_year_count.to_string()}')
        print(f'Динамика уровня зарплат по годам для выбранной профессии:\n{dataset.profession_salaries.to_string()}')
        print(f'Динамика количества вакансий по годам для выбранной профессии:\n{dataset.profession_count.to_string()}')
        print(f'Уровень зарплат по городам:\n{dataset.vacancies_area_salaries.to_string()}')
        print(f'Доля вакансий по городам:\n{dataset.fractions.to_string()}')

    def __init__(self):
        """Инициализирует экземпляр InputConnect."""
        self.db_filename = input('Введите название файла: ')
        self.profession = input('Введите название профессии: ')
        if self.db_filename and self.profession:
            dataset = DataSet()
            dataset.process_statistics(self.db_filename, self.profession)
            self.display_statistics(dataset)


InputConnect()
