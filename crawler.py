# pycodestyle -W291
# coding=utf-8
from bs4 import BeautifulSoup
import requests
import json
import os
import logging
import logging.config

import coloredlogs

coloredlogs.install(level='DEBUG')

DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'scrapy': {
            'level': 'DEBUG',
        },
    }
}


logging.config.dictConfig(DEFAULT_LOGGING)


def isLastPage(soup):
    header2 = soup.find(
        "div",
        {"class": "first_child last_child test"}).find("h2")
    return header2.string.strip() == u"По вашему запросу ничего не найдено"


def isField(tag):
    return (tag.name == "div") and (tag.find("span") is not None)


# Перебираем страницы page1.html, page2.html и тд.
# Сущестование страницы проверяем функцией isLastPage
# Если не сущетвует выходим из функции
def parse():
    programsInfo = {}
    page = 0
    URL = "https://www.hse.ru/edu/courses/page{0}.html?language=&edu_level=78397&full_words=&genelective=-1&xlc=&words=&level=1191462%3A130721827&edu_year=2016&filial=22723&mandatory=&is_dpo=0&lecturer="
    while True:
        page += 1
        url = URL.format(page)
        response = requests.post(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if isLastPage(soup):
            return programsInfo
        programs = soup.find_all(
            "div",
            {"class": "first_child last_child b-program__inner"})
        for program in programs:
            # Берем все значения, кроме года потому что его неудобно парсить))00)0
            programDescription = {}
            programName = program.find("h2").string.strip()
            # Уберем ненужные теги
            program = program.find("div", {"class": "last_child data"})
            #Описания
            fields = program.find_all(isField)
            for field in fields:
                data = []   # strings in tag
                #  Костыль чтобы вытащить из тэга его текст
                #  и текст внутреннго тэга, не нашел как сделать проще(((
                for string in field.strings:
                    string = string.strip()
                    # Проверка на пустую строку
                    if string:
                        data.append(string)
                # Убираем двоеточие в конце
                data[0] = data[0][:len(data[0]) - 1]
                key = data[0]
                value = data[1]
                if key == u"Преподаватель" or key == u"Преподаватели":
                    # Забираем имена преподавателей из всех ссылок данного поля
                    key = u'Преподаватели'
                    links = field.find_all("a")
                    teachers = [link.string for link in links if link.string]
                    programDescription[key] = teachers
                elif key == u"Автор" or key == u"Авторы":
                    # Забираем имена авторов из всех ссылок данного поля
                    key = u'Авторы'
                    links = field.find_all("a")
                    authors = [link.string for link in links if link.string]
                    programDescription[key] = authors
                elif key == u"Прогр. уч. дисц.":
                    pdf_link = field.find_all("a", limit=2)
                    pdf_link = pdf_link[1]
                    programDescription[key] = pdf_link["href"]
                else:
                    programDescription[key] = data[1]

            programsInfo[programName] = programDescription


def writeJson(data):
    file = open("data.json", "w")
    json.dump(data, file, ensure_ascii=False)
    file.close()


def download(data):
    host = "https://www.hse.ru/"
    currentDir = os.getcwd()
    try:
        os.stat("pdf")
    except:
        os.mkdir("pdf")
    pdfDir = currentDir + "/pdfDir/pdf"

    id = 0
    for courseName in data:
        course = data[courseName]
        id += 1
        course["id"] = id
        if u"Прогр. уч. дисц." in course:
            url = host + course[u"Прогр. уч. дисц."]
            logging.debug("Download started")
            response = requests.get(url)
            logging.debug("Download finished")
            filepath = pdfDir + str(id) + ".pdf"
            with open(filepath, "wb") as pdf:
                pdf.write(response.content)


if __name__ == "__main__":
    data = parse()
    # with open("data.json", "r") as temp:
    #     data = json.load(temp)
    #     temp.close()
    download(data)
    writeJson(data)
