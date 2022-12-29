import pdfkit
import matplotlib.pyplot as plt
import numpy as np
import csv
import os
import pandas as pd
from jinja2 import Environment, FileSystemLoader


class DataSet:
    """Класс, используемый для представления данных вакансий.

    Attributes:
        __columns (list): Названия столбцов csv файла
        __reader (_reader): Reader для чтения файла
        vacancies_year_salaries (dict): Средняя зарплата по годам
        vacancies_year_count (dict): Количество вакансий по годам
        profession_salaries (dict): Средняя зарплата по выбранной профессии по годам
        profession_count (dict): Количество вакансий по выбранной профессии по годам
        vacancies_area_salaries (dict): Средняя зарплата по городам
        vacancies_area_count (dict): Количество вакансий по городам
        fractions (dict): Доли вакансий по городам
    """

    def __init__(self, filename: str):
        """Инициализирует экземпляр DataSet.

        Args:
            filename (str): Имя исходного файла с вакансиями
        """
        vacancies_file = open(filename, 'r', encoding="utf-8-sig")
        self.__reader = csv.reader(vacancies_file)
        self.__columns = next(self.__reader)
        self.vacancies_year_salaries = {}
        self.vacancies_year_count = {}
        self.vacancies_area_salaries = {}
        self.vacancies_area_count = {}
        self.profession_salaries = {}
        self.profession_count = {}
        self.fractions = {}

    def is_file_empty(self):
        """Возвращает True, если файл с вакансиями пуст, в другом случае False.

        Returns:
            bool: True, если файл с вакансиями пуст, в другом случае False
        """
        return True if not self.__columns else False

    def process_statistics(self, csv_filename: str, profession: str):
        """Рассчитывает статистику по выбранной профессии

        Args:
            csv_filename (str): Имя csv файла с вакансиями
            profession (str): Выбранная профессия
        """
        data = pd.read_csv(csv_filename, delimiter=',')
        data['publish_year'] = data['published_at'].apply(lambda d: int(d[:4]))
        vacancies_year_salaries = data.groupby('publish_year')['salary'].mean()
        self.vacancies_year_salaries = vacancies_year_salaries.astype('int').to_dict()
        vacancies_year_count = data['publish_year'].value_counts().sort_index()
        self.vacancies_year_count = vacancies_year_count.to_dict()
        vacancies_for_profession = data[data['name'].str.contains(profession)]
        profession_salaries = vacancies_for_profession.groupby('publish_year')['salary'].mean().dropna()
        self.profession_salaries = profession_salaries.astype('int').to_dict()
        profession_count = vacancies_for_profession['publish_year'].value_counts().sort_index()
        self.profession_count = profession_count.to_dict()
        vacancies_area_count = data['area_name'].value_counts()
        self.vacancies_area_count = vacancies_area_count.to_dict()
        fractions = vacancies_area_count[vacancies_area_count * 100 / vacancies_area_count.sum() >= 1]\
            .apply(lambda count: count / vacancies_area_count.sum()).head(10)
        self.fractions = fractions.to_dict()
        vacancies_area_salaries = data.groupby('area_name')['salary'].mean()
        vacancies_area_salaries = vacancies_area_salaries[vacancies_area_salaries.index.isin(fractions.index)] \
            .sort_values(ascending=False).head(10)
        self.vacancies_area_salaries = vacancies_area_salaries.astype('int').to_dict()


class InputConnect:
    """Класс, используемый для обработки вводимых пользователем данных.

    Attributes:
        csv_filename (str): Имя csv файла с вакансиями
    """

    def display_statistics(self, dataset: DataSet):
        """Выводит статистику.

        Args:
            dataset (DataSet): Данные вакансий
        """
        print(f'Динамика уровня зарплат по годам: {dataset.vacancies_year_salaries}')
        print(f'Динамика количества вакансий по годам: {dataset.vacancies_year_count}')
        print(f'Динамика уровня зарплат по годам для выбранной профессии: {dataset.profession_salaries}')
        print(f'Динамика количества вакансий по годам для выбранной профессии: {dataset.profession_count}')

    def get_short_string(self, s):
        """Возвращает укороченную строку.

        Args:
            s (str): Строка

        Returns:
            str: Укороченная  строка
        """
        if len(s) <= 100:
            return s
        return f'{s[:100]}...'

    def __init__(self):
        """Инициализирует экземпляр InputConnect."""

        self.csv_filename = input('Введите название файла: ')
        self.profession = input('Введите название профессии: ')
        if self.csv_filename and self.profession:
            try:
                dataset = DataSet(self.csv_filename)
            except StopIteration:
                print('Пустой файл')
            if not dataset.is_file_empty():
                dataset.process_statistics(self.csv_filename, self.profession)
                report = Report(dataset)
                report.create_plots(self.profession)
                report.create_pdf(self.profession)
                self.display_statistics(dataset)


class Report:
    """Класс, используемый для представления отчёта."""

    def __init__(self, dataset: DataSet):
        self.__dataset = dataset

    def create_plots(self, profession: str):
        """Создаёт графики для выбранной профессии.

        Args:
            profession (str): Выбранная профессия
        """
        fig, ((vacancies_year_salaries_plot, vacancies_year_count_plot),
              (vacancies_area_salaries_plot, fractions_plot)) = plt.subplots(2, 2)
        Report.create_vacancies_year_salaries_plot(vacancies_year_salaries_plot,
                                                   self.__dataset.vacancies_year_salaries,
                                                   self.__dataset.profession_salaries,
                                                   profession)
        Report.create_vacancies_year_count_plot(vacancies_year_count_plot,
                                                self.__dataset.vacancies_year_count,
                                                self.__dataset.profession_count,
                                                profession)
        Report.create_vacancies_area_salaries_plot(vacancies_area_salaries_plot, self.__dataset.vacancies_area_salaries)
        Report.create_fractions_plot(fractions_plot, self.__dataset.fractions)
        fig.tight_layout()
        plt.savefig('plots.png')

    @staticmethod
    def create_vacancies_year_salaries_plot(plot, vacancies_year_salaries: dict, profession_salaries: dict, profession: str):
        """Создает график зарплат по годам.

        Args:
            plot: График
            vacancies_year_salaries (dict): Средняя зарплата по годам
            profession_salaries (dict): Ссредней зарплата по годам для выбранной профессии
            profession (str): Выбранная профессия
        """
        width = 0.4
        average_salaries = [vacancies_year_salaries[year] for year in profession_salaries]
        average_salaries_for_profession = [profession_salaries[year] for year in profession_salaries]
        labels = [year for year in profession_salaries]
        x = np.arange(len(labels))
        average_bar = plot.bar(x - width / 2, average_salaries, width, label='Средняя зарплата')
        average_bar_for_profession = plot.bar(x + width / 2, average_salaries_for_profession, width,
                                              label=f'Зарплата {profession}')
        plot.set_title('Уровень зарплат по годам')
        plot.set_xticks(x, labels, rotation=90)
        for label in (plot.get_xticklabels() + plot.get_yticklabels()):
            label.set_fontsize(8)
        plot.legend(fontsize=8)
        plot.grid(True, axis='y')

    @staticmethod
    def create_vacancies_year_count_plot(plot, vacancies_year_count: dict, profession_count: dict, profession: str):
        """Создает график количества вакансий по годам.

        Args:
            plot: График
            vacancies_year_count (dict): Количество вакансий по годам
            profession_count (dict): Количество вакансий по годам для выбранной профессии
            profession (str): Выбранная профессия
        """
        width = 0.4
        vacancies_count = [vacancies_year_count[year] for year in profession_count]
        vacancies_count_for_profession = [profession_count[year] for year in profession_count]
        labels = [year for year in profession_count]
        x = np.arange(len(labels))
        vacancies_count_bar = plot.bar(x - width / 2, vacancies_count, width, label='Кол-во вакансий')
        vacancies_count_for_profession_bar = plot.bar(x + width / 2, vacancies_count_for_profession, width,
                                        label=f'Кол-во вакансий\n{profession}')
        plot.set_title('Количество вакансий по годам')
        plot.set_xticks(x, labels, rotation=90)
        for label in (plot.get_xticklabels() + plot.get_yticklabels()):
            label.set_fontsize(8)
        plot.legend(fontsize=8)
        plot.grid(True, axis='y')

    @staticmethod
    def create_vacancies_area_salaries_plot(plot, vacancies_area_salaries: dict):
        """Создает график уровня зарплат по городам.

        Args:
            plot: График
            vacancies_area_salaries (dict): Средняя зарплата по городам
        """
        average_salaries = [vacancies_area_salaries[area] for area in vacancies_area_salaries]
        area_labels = [Report.get_string_with_breaklines(area) for area in vacancies_area_salaries]
        y = np.arange(len(area_labels))
        plot.barh(y, average_salaries)
        plot.set_title('Уровень зарплат по городам')
        plot.set_yticks(y, labels=area_labels, fontsize=6, horizontalalignment="right", verticalalignment="center")
        plot.invert_yaxis()
        for label in (plot.get_xticklabels()):
            label.set_fontsize(8)
        plot.grid(True, axis='x')

    @staticmethod
    def create_fractions_plot(plot, fractions: dict):
        """Создает график количества вакансий по городам.

        Args:
            plot: График
            fractions (dict): Доли вакансий по городам
        """
        fraction = [fractions[area] for area in fractions]
        other_area_fraction = 1 - sum(fraction)
        fraction = [other_area_fraction] + fraction
        fraction_labels = ['Другие'] + [area for area in fractions]
        plot.pie(fraction, labels=fraction_labels, textprops={"fontsize": 6})
        plot.set_title('Доля вакансий по городам')

    @staticmethod
    def get_string_with_breaklines(s: str):
        """Разделяет строку переносами при необходимости.

        Args:
            s (str): Строка

        Returns:
            str: Обработанная строка
        """
        if len(s.split()) == len(s.split('-')) == 1:
            return s
        elif len(s.split()) > len(s.split('-')):
            return '\n'.join(s.split())
        else:
            return '-\n'.join(s.split('-'))

    def create_pdf(self, profession: str):
        """Создает pdf отчет.

        Args:
            profession (str): Выбранная профессия
        """
        env = Environment(loader=FileSystemLoader('.'))
        report_template = env.get_template('report_template.html')
        img_path = f"file:///{os.path.abspath('plots.png')}"
        pdf_template = report_template.render(
            {'profession': profession, "img_path": img_path,
             'vacancies_year_salaries': self.__dataset.vacancies_year_salaries,
             'profession_salaries': self.__dataset.profession_salaries,
             'vacancies_year_count': self.__dataset.vacancies_year_count,
             'profession_count': self.__dataset.profession_count,
             'vacancies_area_salaries': self.__dataset.vacancies_area_salaries, 'fractions': self.__dataset.fractions})
        path_to_wkhtmltopdf = r'"C:\Users\alexa\PycharmProjects\pythonProject2\wkhtmltopdf.exe"'
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
        pdfkit.from_string(pdf_template, 'report.pdf', configuration=config,
                           options={'enable-local-file-access': None})


InputConnect()
