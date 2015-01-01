# -*- coding: utf-8 -*-
"""
 !!!!!!!!!! ПЕРЕРАБОТАТЬ СООБЩЕНИЯ ОБ ОШИБКАХ !!!!!!!!!!!!!
"""
import MySQLdb as db

class Mysql:
    def __init__(self, host, userName, userPass, userDB=None):
        try:
            self.connect = db.connect(host, userName, userPass)
            self.cursor  = self.connect.cursor()
            self.listDB  = [] # !!!! ПРИ ЛЮБЫХ ОПЕРАЦИЯХ СО СПИСКОМ - ИСПОЛЬЗОВАТЬ .lower() !!!!!
            self.listTbl = {} # !!!! ПРИ ЛЮБЫХ ОПЕРАЦИЯХ СО СЛОВАРЕМ - ИСПОЛЬЗОВАТЬ .lower() !!!!!
            self.listCol = {} # !!!! ПРИ ЛЮБЫХ ОПЕРАЦИЯХ СО СЛОВАРЕМ - ИСПОЛЬЗОВАТЬ .lower() !!!!
            self.listData= {} # !!!! ПРИ ЛЮБЫХ ОПЕРАЦИЯХ СО СЛОВАРЕМ - ИСПОЛЬЗОВАТЬ .lower() !!!!
            self.describeTbl = {}
        except:
            print("Error 1") # Error 1 - отсутствует соединение с базой данных

    # Фукнция для запросов к бд
    def execute(self, sql):
        try:
            self.cursor.execute(sql)
        except:
            return "Error 1"

    # ПОЛУЧЕНИЕ СПИСКА БАЗ ДАННЫХ
    def getBDlist(self):
        self.execute('SHOW DATABASES')
        result = self.cursor.fetchall()
        for row in result:
            self.listDB.append(row[0].lower())

    # ПОЛУЧЕНИЕ СПИСКА ТАБЛИЦ ДЛЯ КАЖДОЙ БАЗЫ ДАННЫХ
    def getTableList(self):
        self.listTbl.clear()
        for db in self.listDB:
            self.listTbl[db] = []
            self.execute("SHOW TABLES FROM %s" % (db))
            result = self.cursor.fetchall()
            for tbl in result:
                self.listTbl[db].append(tbl[0].lower())

    # Функция - создание новой базы данных
    def createNewDB(self, dbName):
        # Проверяем существование базы данных с таким именем
        if dbName.lower() in self.listDB:
            return "Error 3" # Error 3 - попытка создать существующую базу данных!
        self.execute('create database %s' % (str(dbName)))
        self.listDB.append(dbName.lower())
        self.getTableList()
        return True



    # Функция - удаление базы данных
    def deleteDB(self, dbName):
        if dbName.lower() not in self.listDB:
            return "Error 4" # Error 4 - попытка удалить несуществующую базу данных!
        self.execute('DROP DATABASE %s' % (str(dbName)))
        self.listDB.remove(dbName.lower())
        self.getTableList()
        return True

    # Функция - создание таблицы в указанной базе данных
    def createTable(self, dbName, tblName, columns = ['id']):
        # Проверка на существование указанной базы данных
        if dbName.lower() not in self.listDB:
            return "Error 5" # Error 5 - попытка создать таблицу в несуществующей базе данных!
        # Выбор базы данных
        try:
            self.connect.select_db(dbName)
        except:
            print("Error 1") # Error 1 - отсутствует соединение с базой данных
        # Проверка на существование указанной таблицы
        if tblName.lower in self.listTbl[dbName]:
            return "Error 6" # Error 6 - попытка создать существующую таблицу
        # создаем строку со столбцами
        strCol = ""
        for row in columns:
            strCol = strCol+row+','

        # Создание таблицы
        self.execute('CREATE TABLE `'+tblName+'` ('+strCol[0:-1]+')')
        # После создания таблицы - добавление её в словарь listTbl
        self.listTbl[dbName].append(tblName.lower())
        return True

    # Функция - удаление таблицы
    def deleteTable(self, dbName, tblName):
        # Проверяем - существует ли указанная база данных
        if dbName.lower() not in self.listDB:
            return "Error 7" # Error 7 - попытка удалить таблицу в несуществующей базе данных
        self.connect.select_db(dbName)
        # Проверяем - существует ли указанная таблица
        if tblName.lower() not in self.listTbl[dbName.lower()]:
            return "Error 8" # Error 8 - попытка удалить несуществующую таблицу
        # Удаление таблицы
        self.execute("DROP TABLE `%s`" % (str(tblName)))
        self.listTbl[dbName.lower()].remove(tblName.lower())

    # Функция - получение данных в таблице. Возвращает
    def getTableData(self, dbName, tblName):
        self.listCol.clear()
        self.listData.clear()
        # Проверяем - существует ли указанная база данных
        if dbName.lower() not in self.listDB:
            return "Error 9" # Error 9 - попытка подключиться к несуществующей базе данных
        self.connect.select_db(dbName)
        # Проверяем - существует ли указанная таблица
        if tblName.lower() not in self.listTbl[dbName.lower()]:
            return "Error 10" # Error 10 - попытка получить данные из несуществующей таблицы
        # Получаем имена столбцов в таблице
        self.execute("SHOW COLUMNS FROM %s" % (str(tblName)))
        result = self.cursor.fetchall()
        self.listCol[tblName.lower()] = []
        for col in result:
            self.listCol[tblName.lower()].append(col[0].lower())

        # Извлекаем данные из таблицы
        self.execute("SELECT * FROM %s" % (str(tblName)))
        result = self.cursor.fetchall()
        self.listData[tblName.lower()] = []
        for row in result:
            self.listData[tblName.lower()].append(row)


    def describe(self, dbName, tblName):
        # Проверяем - существует ли указанная база данных
        if dbName.lower() not in self.listDB:
            return "Error 9" # Error 9 - попытка подключиться к несуществующей базе данных
        self.connect.select_db(dbName)
        # Проверяем - существует ли указанная таблица
        if tblName.lower() not in self.listTbl[dbName.lower()]:
            return "Error 10" # Error 10 - попытка получить данные из несуществующей таблицы
        self.execute('describe %s' % (str(tblName)))
        result = self.cursor.fetchall()
        return result

        # !!!!!!!!!! CURSOR.FETCHALL()  ВЫНЕСТИ В ОТДЕЛЬНУЮ Ф-ЦИЮ !!!!!!!!!!!!!!!!!!!!!!!! #
