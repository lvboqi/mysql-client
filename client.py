# -*- coding: utf-8 -*-
import sys
import sip
from pmysql import Mysql
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic

# 1. Инициализируем GUI
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        # Инициализация переменных
        self.activeTblName = None # Активная таблица
        self.activeDbName  = None # Активная БД
        self.tableTree = {}       # !!!! ОБЯЗАТЕЛЬНО ИСПОЛЬЗОВАТЬ .lower() !!!!! структура { База данных : [ таблица 1, таблица 2 ] }
        self.ms  = None           # Класс Mysql
        self.modalWindConnect = None # Модальное окно Connect'a

        self.errorLbl = None  # Принадлежит Модальному окну коннекта
        self.hostEdit = None  # Принадлежит модальному окну коннекта
        self.loginEdit = None # Принадлежит модальному окну коннекта
        self.passEdit = None  # Принадлежит модальному окну коннекта

        self.modalCreateNewDb = None # Модальное окно создания базы данных
        self.nameDbEdit = None # принадлежит модальному окну создания базы данных


        QtGui.QMainWindow.__init__(self)
        uic.loadUi('form.ui', self)
        self.setWindowIcon(QtGui.QIcon('img/ico.png'))
        # Теперь - вызываем функцию, создающую меню
        self.InitMenu()

    # Функция - создает меню, Файл, Правка, etc
    def InitMenu(self):
        # Создание тулбара
        menubar = self.menuBar()
        # Меню File
        file = menubar.addMenu(u'Файл')
        actionExit = QtGui.QAction(QtGui.QIcon(''), u'Выйти', self)
        actionConnect = QtGui.QAction(QtGui.QIcon(''), u'Подключиться', self)
        actionDisconnect = QtGui.QAction(QtGui.QIcon(''), u'Отключиться', self)
        file.addAction(actionConnect)
        file.addAction(actionDisconnect)
        file.addAction(actionExit)

        # Обработка меню
        self.connect(actionExit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
        self.connect(actionConnect,QtCore.SIGNAL('triggered()'), self._actionConnectModal)

        # Коннект при двойном клике по базе данных
        self.dbInfo.itemDoubleClicked.connect(self.loadTable)
        # Создание контекстных меню
        # Отлавливаем ПКМ по требуему элементу, и передаем его координаты в onRightClick
        self.dbInfo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # Обработка контекстных меню
        self.dbInfo.connect(self.dbInfo, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onRightClickDbInfo)
        # Обработка изменений ячеек таблицы
        self.tableW.itemChanged.connect(self.tableItemChanged)


    # Построение контекстных меню для QTreeWidget.
    def onRightClickDbInfo(self, TreeItem):
        # Определеяем, был ли клик пкм по элементу QTreeWidget или же по пустому пространству в пределах окна QTreeWidget
        try:
            self.TreeItemRc = self.dbInfo.itemAt(TreeItem).text(0)
        except:
            self.TreeItemRc = None

        # Строим контекстные меню, в зависимости от того, куда было нажатие ПКМ
        if self.dbInfo.itemAt(TreeItem) == None:
            menu = QtGui.QMenu(self)
            menu.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            menu.addAction(u'Создать новую БД',self._actionCreateDbModal)
            menu.addAction('Action 2')
            menu.exec_(QtGui.QCursor.pos(), )
            return


        if self.dbInfo.itemAt(TreeItem).parent() == None:
            menu = QtGui.QMenu(self)
            menu.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            menu.addAction(u'Создать новую БД',self._actionCreateDbModal)
            menu.addSeparator()
            menu.addAction(u'Создать таблицу')
            menu.addAction(u'Удалить базу данных', self._actionDeleteDbModal)
            menu.exec_(QtGui.QCursor.pos(), )
            return


        if self.dbInfo.itemAt(TreeItem).parent() <> None:
            menu = QtGui.QMenu(self)
            menu.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            menu.addAction(u'Создать новую таблицу')
            menu.addAction(u'Вставка')
            menu.addAction(u'Выборка из таблицы')
            menu.addAction(u'Удалить таблицу')
            menu.exec_(QtGui.QCursor.pos(), )
            return




    # Создания дерева баз данных и таблиц
    def treeDbInit(self):
        self.dbInfo.clear()
        TreeDbHeader=QtGui.QTreeWidgetItem([u"Базы данных"])
        self.dbInfo.setHeaderItem(TreeDbHeader)
        for db in self.ms.listDB:
            item = QtGui.QTreeWidgetItem(self.dbInfo, [db])
            item.setIcon(0, QtGui.QIcon('img/db_ico.png'))
            self.tableTree[db] = []
            if len(self.ms.listTbl[db.lower()]) != 0:
                for tbl in self.ms.listTbl[db.lower()]:
                    sub_item = QtGui.QTreeWidgetItem(item, [tbl])
                    sub_item.setIcon(0, QtGui.QIcon('img/table_ico.png'))
                    self.tableTree[db].append(tbl)

    # Обработчик выбора таблицы в QWTree
    def loadTable(self, item, column):
        # Прерываем выполнение tableItemChanged
        self.LoadNewTable = True
        # Определяем, какая таблица и в какой БД выбрана
        itemName   = str(item.text(column))
        parentName = str(self.dbInfo.currentItem().parent().text(0))
        # Получаем информацию из таблицы
        self.ms.getTableData(parentName, itemName)
        # Устанавливаем необходимое количество столбцов и строк
        countColumn = len(self.ms.listCol[itemName])
        countRow    = len(self.ms.listData[itemName])
        self.tableW.setColumnCount(countColumn)
        self.tableW.setRowCount(countRow)
        # Создаем заголовки столбцов
        self.tableW.setHorizontalHeaderLabels(self.ms.listCol[itemName])
        # Запоминаем активную таблицу и бд
        self.activeTblName = itemName
        self.activeDbName  = parentName
        # Заносим данные в таблицу
        j = 0
        for row in self.ms.listData[itemName]:
            for rowItem in row:
                item = QtGui.QTableWidgetItem(str(rowItem).decode('cp1251'))
                self.tableW.setItem(0, j, item)
                j += 1
        self.LoadNewTable = False

    # Функция - обновление значения ячейки
    def tableItemChanged(self, Item):
        # Если итемы меняются при загрузке таблицы - прерываем выполнение
        if self.LoadNewTable == True:
            return
        # Получаем измененное значение в таблице
        changedItem = Item.text()
        # Получаем номер строки и номер столбца, где было изменено значение
        row = Item.row()
        colNumb = Item.column()
        # Получаем название столбца, где было изменение
        columnName = self.ms.listCol[self.activeTblName][colNumb]
        # Проверяем, есть ли в этой таблице столбец с UNIQUE KEY
        atributeTbl = self.ms.describe(self.activeDbName, self.activeTblName)
        for atr in atributeTbl:
            if atr[3] == 'PRI':
                columnPriKey = atr[0]
                break
            else:
                columnPriKey = None

        # Если столбец UNIQUE KEY есть, UPDATE делаем по нему
        if columnPriKey <> columnName and columnPriKey <> None:
            ## GOVNOKOD DETECTED, SORRY ##
            #Получаем значение, хранящееся в ячейке UNIQUE KEY, требуется придумать более расово-верный способ
            i = 0
            for colName in self.ms.listCol[self.activeTblName]:
                if colName == columnPriKey:
                    columnPriKeyValue = unicode(self.tableW.item (row, i).text())
                    break
                else:
                    i += i
            self.ms.tblUpdate(self.activeDbName, self.activeTblName, [0, self.activeTblName, columnPriKey, columnPriKeyValue, columnName, changedItem])
        # Если столбец UNIQUE KEY отсутствует, заменяем данные в таблице, указав во WHERE все столбцы, и LIMIT 1
        if columnPriKey == None:
            print(u'Обновляем таблицу, используя все столбцы в таблице и используя limit 1')
            
        # Если меняется столбец UNIQUE KEY - меняем по нему же, используя старое значение
        if columnPriKey == columnName:
            print(u'Обновляем таблицу, используя все столбцы в таблице и используя limit 1')


    # Обработчик кнопки "Подключиться"
    def _actionConnect(self):
        # Если ранее было установлено соединение - закрываем его, очищаем клиент
        if self.ms:
            del self.ms
        if self.dbInfo.columnCount () <> 0:
            self.dbInfo.clear()
        # Получаем данные для подключения
        host = str(self.hostEdit.text()).decode('utf-8')
        login = str(self.loginEdit.text()).decode('utf-8')
        pas   = str(self.passEdit.text()).decode('utf-8')
        # Проверяем введенные даннаые, если не введены сервер или логин - выводим error, иначе - закрываем модальное окно
        if len(login) == 0 or len(host) == 0:
            self.errorLbl.show()
            return "Error 1"
        # Закрываем модальное окно
        self.modalWindConnect.hide()
        del self.modalWindConnect
        # Коннектимся, загружаем список баз данных, и список таблиц
        print (host+' '+login+' '+pas)
        self.ms = Mysql(host, login, pas)
        self.ms.getBDlist()
        self.ms.getTableList()
        # Строим список баз данных и таблиц
        self.treeDbInit()

    # Создание новой базы данных
    def _actionCreateDb(self):
        # Проверяем, введено ли название базы данных, проверяем на кирилицу, если всё ОК - закрываем модальное окно, иначе - выводим self.ErrorLbl
        try:
            nameDb = str(self.nameDbEdit.text()).decode('utf-8')
        except:
            self.errorLbl.setText(u'<b><h3>Недопустимые символы</b></h3>')
            self.errorLbl.show()
            return
        if len(nameDb) == 0:
            self.errorLbl.setText(u'<b><h3>Введите название</b></h3>')
            self.errorLbl.show()
            return
        # Проверяем, подключены ли мы к серверу
        if self.ms == None:
            self.errorLbl.setText(u'<b><h3>Отсутствует подключение</b></h3>')
            self.errorLbl.show()
            return
        # Создаем базу данных
        if self.ms.createNewDB(nameDb):
            # Обновляем дерево
            self.treeDbInit()
            self.modalCreateNewDb.hide()
            del self.modalCreateNewDb
        else:
            self.errorLbl.setText(u'<b><h3>Не удалось</b></h3>')
            self.errorLbl.show()
            return



    # Модальное окно коннекта к mysql
    def _actionConnectModal(self):
        # СОЗДАНИЕ МОДАЛЬНОГО ОКНА - ОБЯЗАТЕЛЬНО ВЫНЕСТИ В ОТДЕЛЬНЫЙ ФАЙЛ
        self.modalWindConnect = QtGui.QWidget(self,QtCore.Qt.Window)
        self.modalWindConnect.setWindowTitle(u'Параметры подключения') # Текст в заголовке окна
        sizeX, sizeY = (400,150) # Задаём переменные размера окна
        WinPos = QtGui.QApplication.desktop()
        posX, posY = (WinPos.width() - sizeX) // 2 ,(WinPos.height() - sizeY) // 2
        self.modalWindConnect.setGeometry(posX,posY,sizeX,sizeY)
        self.modalWindConnect.setWindowModality(QtCore.Qt.WindowModal)
        self.modalWindConnect.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        # self.modalWindConnect.setWindowFlags(QtCore.Qt.) - не работает
        # Добавление элементов
        hostLbl  = QtGui.QLabel(u'Сервер: ')
        loginLbl = QtGui.QLabel(u'Логин:  ')
        passLbl  = QtGui.QLabel(u'Пароль: ')
        self.errorLbl = QtGui.QLabel(u'<b><h3>Ошибка: заполните все поля</h3></b>')
        self.errorLbl.hide()

        self.hostEdit  = QtGui.QLineEdit()
        self.hostEdit.setText('127.0.0.1')
        self.loginEdit = QtGui.QLineEdit()
        self.loginEdit.setText('root')
        self.passEdit  = QtGui.QLineEdit()

        button    = QtGui.QPushButton(u'Соединение')

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(hostLbl, 1, 0)
        grid.addWidget(self.hostEdit, 1, 1)
        grid.addWidget(loginLbl, 2, 0)
        grid.addWidget(self.loginEdit, 2, 1)
        grid.addWidget(passLbl, 3, 0)
        grid.addWidget(self.passEdit, 3, 1)
        grid.addWidget(button, 4,0)
        grid.addWidget(self.errorLbl, 4, 1)
        self.modalWindConnect.setLayout(grid)
        self.modalWindConnect.show()
        self.connect(button, QtCore.SIGNAL('clicked()'), self._actionConnect)

    # Удаление базы данных
    def _actionDeleteDb(self):
        if self.ms.deleteDB(str(self.TreeItemRc).encode('utf-8')):
            self.treeDbInit()
            self.modalDeleteDb.hide()

    # Окно создания базы данных
    def _actionCreateDbModal(self):
        # СОЗДАНИЕ МОДАЛЬНОГО ОКНА - ОБЯЗАТЕЛЬНО ВЫНЕСТИ В ОТДЕЛЬНЫЙ ФАЙЛ
        self.modalCreateNewDb = QtGui.QWidget(self,QtCore.Qt.Window)
        self.modalCreateNewDb.setWindowTitle(u'Создание базы данных') # Текст в заголовке окна
        sizeX, sizeY = (400,80) # Задаём переменные размера окна
        WinPos = QtGui.QApplication.desktop()
        posX, posY = (WinPos.width() - sizeX) // 2 ,(WinPos.height() - sizeY) // 2
        self.modalCreateNewDb.setGeometry(posX,posY,sizeX,sizeY)
        self.modalCreateNewDb.setWindowModality(QtCore.Qt.WindowModal)
        self.modalCreateNewDb.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        # self.modalWindConnect.setWindowFlags(QtCore.Qt.) - не работает
        # Добавление элементов
        nameDbLbl  = QtGui.QLabel(u'Введите название базы данных: ')
        self.errorLbl = QtGui.QLabel(u'<b><h3>Ошибка: введите имя базы данных</h3></b>')
        self.errorLbl.hide()

        self.nameDbEdit  = QtGui.QLineEdit()
        self.nameDbEdit.setText('newDB')

        button  = QtGui.QPushButton(u'Создать')

        grid = QtGui.QGridLayout()
        grid.setSpacing(3)
        grid.addWidget(nameDbLbl, 0, 0)
        grid.addWidget(self.nameDbEdit, 0, 1)
        grid.addWidget(button, 1,1)
        grid.addWidget(self.errorLbl,1,0)

        self.modalCreateNewDb.setLayout(grid)
        self.modalCreateNewDb.show()
        self.connect(button, QtCore.SIGNAL('clicked()'), self._actionCreateDb)

    # Окно удаления базы данных
    def _actionDeleteDbModal(self):
        # СОЗДАНИЕ МОДАЛЬНОГО ОКНА - ОБЯЗАТЕЛЬНО ВЫНЕСТИ В ОТДЕЛЬНЫЙ ФАЙЛ
        self.modalDeleteDb = QtGui.QWidget(self,QtCore.Qt.Window)
        self.modalDeleteDb.setWindowTitle(u'Удаление базы данных') # Текст в заголовке окна
        sizeX, sizeY = (400,80) # Задаём переменные размера окна
        WinPos = QtGui.QApplication.desktop()
        posX, posY = (WinPos.width() - sizeX) // 2 ,(WinPos.height() - sizeY) // 2
        self.modalDeleteDb.setGeometry(posX,posY,sizeX,sizeY)
        self.modalDeleteDb.setWindowModality(QtCore.Qt.WindowModal)
        self.modalDeleteDb.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        # self.modalWindConnect.setWindowFlags(QtCore.Qt.) - не работает
        # Добавление элементов
        deleteBd  = QtGui.QLabel(u'Вы действительно хотите удалить эту базу данных?')
        self.errorLbl = QtGui.QLabel(u'<b><h3>Произошла ошибка</h3></b>')
        self.errorLbl.hide()

        # Кнопки выбора
        buttonY  = QtGui.QPushButton(u'Удалить')
        buttonN  = QtGui.QPushButton(u'Отмена')

        grid = QtGui.QGridLayout()
        grid.setSpacing(3)
        grid.addWidget(deleteBd, 0, 0)
        grid.addWidget(buttonY, 2,0)
        grid.addWidget(buttonN, 2,2)

        grid.addWidget(self.errorLbl,1,0)

        self.modalDeleteDb.setLayout(grid)
        self.modalDeleteDb.show()
        self.connect(buttonY, QtCore.SIGNAL('clicked()'), self._actionDeleteDb)
        self.connect(buttonN, QtCore.SIGNAL('clicked()'), lambda: self.modalDeleteDb.hide())




app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
if not sys.exit(app.exec_()):
    del app
