import os
import sys
import csv
import requests
import time
import re
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QProgressBar, QFileDialog
from PyQt5.uic import loadUi


class Login(QMainWindow):
    def __init__(self):
        super(Login, self).__init__()
        loadUi('login.ui', self)
        self.setWindowTitle("Cardmarket Stats")
        self.loginButton.clicked.connect(self.onButtonClick)
        self.passwordField.setEchoMode(QtWidgets.QLineEdit.Password)
        self.statusLabel.setAlignment(QtCore.Qt.AlignCenter)

    def onButtonClick(self):
        self.loginButton.setEnabled(False)
        username = self.usernameField.text()
        password = self.passwordField.text()
        setUserPass(username, password)
        self.statusLabel.setText('Logging in')
        self.log = LoginExternal()
        self.log.textChanged.connect(self.onLogTextChanged)
        self.log.screenChanged.connect(self.switchScreen)

        self.log.start()

    def onLogTextChanged(self, value):
        self.statusLabel.setText(value)

    def switchScreen(self):
        mainScreen = MainScreen()
        widget.addWidget(mainScreen)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class MainScreen(QMainWindow):
    def __init__(self):
        super(MainScreen, self).__init__()
        loadUi('mainUI.ui', self)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.setWindowTitle("Cardmarket Stats")
        self.startButton.clicked.connect(self.onButtonClick)
        self.progress.setValue(0)
        self.progress.setMaximum(99)
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.toolButton.setObjectName("toolButtonOpenDialog")
        self.toolButton.clicked.connect(self._open_file_dialog)
        self.lineEdit.setText('{}'.format(dir_path))
        self.lineEdit.setEnabled(False)
        self.lineEdit.setObjectName("lineEdit")

    def onButtonClick(self):
        self.startButton.setEnabled(False)
        dropDownOption = str(self.dropDown.currentText())
        setDropDown(dropDownOption)
        self.calc = External()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.textChanged.connect(self.onTextChanged)
        self.calc.start()

    def _open_file_dialog(self):
        directory = str(QtWidgets.QFileDialog.getExistingDirectory())
        filepath = '{}'.format(directory) + '/'
        saveDirectory = str(os.path.join(
            str(filepath), 'cardmarket-orders.csv'))
        setSaveDirectory(saveDirectory)
        self.lineEdit.setText(saveDirectory)

    def _set_text(self, text):
        return text

    def onCountChanged(self, value):
        self.progress.setValue(value)

    def onTextChanged(self, value):
        self.status.setText(value)


def login(self, username, password, s):
    login_page = connectivityLink(
        self, 'https://www.cardmarket.com/Login', 'getPage', s, '')
    soup = BeautifulSoup(login_page.content, 'lxml')
    token = soup.find("input", {"name": "__cmtkn"})["value"]
    connectivityLink(
        self, 'https://www.cardmarket.com/en/PostGetAction/User_Login', 'postLogin', s, token)


def connectivityLink(self, link, type, s, token):
    unsuccessfulPOST = True
    payload = {
        'username': username,
        'userPassword': password,
        '__cmtkn': token,
        'referalPage': '/en/Login'}
    while unsuccessfulPOST == True:
        try:
            if type == 'getPage':
                page = s.get(link)
                return page
            if type == 'postLogin':
                page = s.post(link, data=payload)
                return page
        except:
            time.sleep(5)
        else:
            unsuccessfulPOST = False


def setOrderLinks(od):
    global orderLinks
    orderLinks = od
    return


def setUserPass(us, pa):
    global username, password
    username = us
    password = pa
    return


def setDropDown(dd):
    global dropDownOption
    dropDownOption = dd
    return


def setSaveDirectory(sd):
    global saveDirectory
    saveDirectory = sd
    return


class LoginExternal(QThread):
    textChanged = pyqtSignal(str)
    screenChanged = pyqtSignal(str)

    def transactions(self, s):

        intervalCount = 1
        orderLinks = []

        while True:
            try:
                transaction_home = connectivityLink(
                    self, 'https://www.cardmarket.com/en/Pokemon/Account/Transactions/Details', 'getPage', s, '')
                soup = BeautifulSoup(transaction_home.text, 'lxml')
                startDate = soup.find(
                    'option', {'value': '3'}).attrs['data-start-date']
                endDate = soup.find(
                    'option', {'value': '3'}).attrs['data-end-date']
                transaction_page = connectivityLink(self, 'https://www.cardmarket.com/en/Pokemon/Account/Transactions/Details?interval=3&startDate=' +
                                                    startDate + '&endDate=' + endDate + '&category=purchase&subCategories[]=BUY&perSite=20&site=' + str(intervalCount), 'getPage', s, '')
                soup = BeautifulSoup(transaction_page.text, 'lxml')
                pageCount = soup.find(
                    "span", class_='mx-1').text.split()  # 'Page x of y'
            except:
                self.textChanged.emit(
                    'Encountered error - Restart with correct username and password')
                continue
            else:
                tds = soup.find_all('td', class_='d-none d-lg-table-cell')
                for td in tds:
                    for a in td.find_all('a'):
                        url = a.get('href')
                        if 'Orders' in url:
                            orderLinks.append(url)
                intervalCount += 1
                if (pageCount[1] == pageCount[3]):
                    break
        return orderLinks

    def run(self):
        with requests.Session() as s:
            self.textChanged.emit('Logging in')
            login(self, username, password, s)
            self.textChanged.emit('Fetching details (please be patient)')
            orderLinks = self.transactions(s)
            setOrderLinks(orderLinks)
            self.screenChanged.emit('Changed')


class External(QThread):

    countChanged = pyqtSignal(int)
    textChanged = pyqtSignal(str)

    def conditionTest(self, condition):
        if condition == '1':
            return 'Mint'
        elif condition == '2':
            return 'Near Mint'
        elif condition == '3':
            return 'Excellent'
        elif condition == '4':
            return 'Good'
        elif condition == '5':
            return 'Light Played'
        elif condition == '6':
            return 'Played'
        elif condition == '7':
            return 'Poor'
        else:
            return 'Unknown'

    def languageTest(self, language):
        if language == '1':
            return 'English'
        elif language == '2':
            return 'French'
        elif language == '3':
            return 'German'
        elif language == '4':
            return 'Spanish'
        elif language == '5':
            return 'Italian'
        elif language == '6':
            return 'S-Chinese'
        elif language == '7':
            return 'Japanese'
        elif language == '8':
            return 'Portuguese'
        elif language == '9':
            return 'Russian'
        elif language == '10':
            return 'Korean'
        elif language == '11':
            return 'T-Chinese'
        elif language == '12':
            return 'Dutch'
        elif language == '13':
            return 'Polish'
        elif language == '14':
            return 'Czech'
        elif language == '15':
            return 'Hungarian'

    def nameTest(self, name):
        if '\u25c7' in name:
            newName = name.replace('\u25c7', 'prism')
            return newName
        elif '\u03b4' in name:
            newName = name.replace('\u03b4', 'delta')
            return newName
        elif '\u0394' in name:
            newName = name.replace('\u0394', 'delta')
            return newName
        else:
            return name

    def run(self):

        self.countChanged.emit(0)
        self.textChanged.emit('Getting Orders')
        with requests.Session() as s:
            login(self, username, password, s)
            count = 0
            listCount = len(orderLinks)

            orderList = []
            while True:
                try:
                    orderNumber = ''.join(
                        x for x in orderLinks[count] if x.isdigit())
                    self.textChanged.emit(
                        'Proccessing order ' + str(orderNumber))
                    order_page = connectivityLink(
                        self, 'https://www.cardmarket.com' + orderLinks[count], 'getPage', s, '')
                    soup = BeautifulSoup(order_page.content, 'lxml')
                    orderStatus = soup.find('a', {'href': re.compile(
                        '/en/.*/Orders/Purchases/.*'), 'property': 'item'}).span.text
                    orderType = soup.find(
                        'div', {'class': 'category-subsection'}).div.h3.text
                except:
                    if count >= listCount:
                        break
                    else:
                        self.textChanged.emit('Encountered error - retrying')
                        continue
                if((dropDownOption != 'All' and orderStatus != dropDownOption) or 'Singles' not in orderType):
                    count += 1
                    percentage = int(100 * (count/listCount))
                    self.countChanged.emit(percentage)
                    continue

                table = soup.find('tbody')
                articles = table.find_all('tr')
                orderUser = soup.find(
                    'a', {'href': re.compile('/en/.*/Users/.*')})
                for article in articles:

                    attributes = article.attrs
                    rarity = article.find(
                        'span', class_=re.compile('rarity-symbol .*'))
                    if rarity is None:
                        rarity = article.find(
                            'a', class_=re.compile('rarity-symbol .*'))

                    articleDetails = {
                        'Name': self.nameTest(attributes['data-name']),
                        'Condition': self.conditionTest(attributes['data-condition']),
                        'Language': self.languageTest(attributes['data-language']),
                        'Rarity': rarity.attrs['title'],
                        'Price': attributes['data-price'],
                        'Quantity': attributes['data-amount'],
                        'Expansion': attributes['data-expansion-name'],
                        'Order Number': orderNumber,
                        'Seller': orderUser.text
                    }
                    orderList.append(articleDetails)

                self.textChanged.emit('Proccessing order ' + str(orderNumber))
                count += 1
                percentage = int(100 * (count/listCount))
                self.countChanged.emit(percentage)
                if count == listCount:
                    break
            self.textChanged .emit('Converting to CSV ')
            with open(saveDirectory, 'w') as f:
                write = csv.writer(f)
                write.writerow(['Name', 'Condition', 'Language', 'Rarity',
                                'Price', 'Quantity', 'Expansion', 'Order Number', 'Seller'])
                orderNumber = 0
                while(orderNumber < len(orderList)):
                    write.writerow([str((orderList[orderNumber])['Name']), str((orderList[orderNumber])['Condition']), str((orderList[orderNumber])['Language']), str((orderList[orderNumber])['Rarity']), str(
                        (orderList[orderNumber])['Price']), str((orderList[orderNumber])['Quantity']), str((orderList[orderNumber])['Expansion']), str((orderList[orderNumber])['Order Number']), str((orderList[orderNumber])['Seller'])])
                    orderNumber += 1

            self.textChanged.emit('Finished')


app = QApplication(sys.argv)
mainwindow = Login()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedWidth(503)
widget.setFixedHeight(606)
widget.show()

app.exec_()

app.quit()
sys.exit()
