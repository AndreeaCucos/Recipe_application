import pygame
import time
import requests
from PyQt5.QtWidgets import QFrame, QListWidget, QHBoxLayout, QScrollArea, QDialog, QListWidgetItem
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QStackedWidget, \
    QComboBox, QToolBar, QToolButton, QSizePolicy
from PyQt5.QtCore import Qt, QThread
import json
import re

button_name = ""
font_big = QFont("Roboto", 12)
font_small = QFont("Roboto", 9)
choices1 = []
choices2 = []
page_sound = "sounds/page-flip-01a.wav"
click_sound = "sounds/mixkit-interface-click-1126.wav"
timer_sound = "sounds/little-bell-14606.mp3"
error = "sounds/error-126627.mp3"
buttons = {}

with open("culori.json", "r") as f:
    colors = json.load(f)

primary_color = colors["primary"]
primary_lighter_color = colors["primary_lighter"]
primary_darker_color = colors["primary_darker"]
secondary_color = colors["secondary"]
supplementary_color = colors["supplementary"]
important_text_color = colors["important-text-color"]
regular_text = colors["regular-text"]


def apply_button_styles(widget, selector, type):
    if type == 'tool':
        style = f"""
            QToolButton{selector}:hover {{
                background-color: {primary_darker_color};
                color: white;
                border-radius: 5px;
            }}
        """
        widget.setStyleSheet(widget.styleSheet() + style)
    elif type == 'push':
        style = f"""
            QPushButton{selector}:hover {{
                background-color: {primary_darker_color};
                color: white;
                border-radius: 5px;
            }}
        """
        widget.setStyleSheet(widget.styleSheet() + style)


def play_sound(sound):
    pygame.init()
    sound_file = sound
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(2)
    pygame.quit()


def error_popup(text):
    dialog = QDialog()
    dialog.setWindowTitle('Error')
    dialog.setGeometry(850, 400, 200, 100)

    vbox = QVBoxLayout(dialog)
    dialog.setStyleSheet(f'background-color: {secondary_color}')
    label = QLabel(text, dialog)
    vbox.addWidget(label)
    send_text_to_backend('Error')

    play_sound(error)

    close_button = QPushButton('Close', dialog)
    close_button.setObjectName('Close')
    close_button.setStyleSheet(f'background-color: {primary_color}')

    close_button.clicked.connect(dialog.close)
    vbox.addWidget(close_button)

    dialog.setLayout(vbox)
    dialog.exec_()


def send_text_to_backend(text):
    payload = {'steps': text}
    print('sending')
    response = requests.post('http://localhost:5000/read', json=payload)
    if response.status_code != 200:
        error_popup('The steps cannot be read.')

    time.sleep(1)
    response = requests.post('http://localhost:5000/stop_reading')
    if response.status_code != 200:
        error_popup('Error while stopping.')


class MainPage(QWidget):
    def __init__(self, stackedWidget):
        super().__init__()
        self.stackedWidget = stackedWidget
        self.setObjectName('MainWindow')
        self.setStyleSheet("background-image: url(ingredients-homemade-tarte-tatin-pie-with-apples-nuts-beige"
                           "-background-french-apple-pie-selective-focus.jpg)")

        label = QLabel("Welcome to FoodFinder!", self)
        font_big.setBold(True)
        label.setFont(font_big)
        font_big.setBold(True)
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(label)

        label.setStyleSheet(f"color: {regular_text};font-style: italic")
        label.setAlignment(Qt.AlignCenter)


class SearchPage(QWidget):
    def __init__(self, stackedWidget):
        super().__init__()
        global buttons, choices1, choices2
        self.setObjectName('SearchPage')
        self.stackedWidget = stackedWidget

        frame = QFrame(self)
        frame.setGeometry(260, 130, 450, 300)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"background-color: {primary_lighter_color};border-radius: 10px;border: 1px solid black;")
        label_1 = QLabel(frame)
        label_1.setGeometry(180, 30, 100, 30)
        label_1.setText('Meal type:')
        label_1.setFont(font_small)
        label_1.setStyleSheet('border: 0px;')
        self.combo_box_1 = QComboBox(frame)
        self.combo_box_1.setObjectName('tip')
        self.combo_box_1.setGeometry(140, 70, 180, 30)
        self.combo_box_1.setStyleSheet("border-radius: 0px;border: 1px solid black;")

        choices1 = ['breakfast', 'lunch', 'dinner', 'dessert']
        self.combo_box_1.addItems(choices1)
        label_2 = QLabel(frame)
        label_2.setGeometry(180, 130, 180, 30)
        label_2.setText('Preferences:')
        label_2.setFont(font_small)
        label_2.setStyleSheet('border: 0px;')

        self.combo_box_2 = QComboBox(frame)
        self.combo_box_2.setObjectName('preferinte')
        self.combo_box_2.setGeometry(140, 170, 180, 30)
        self.combo_box_2.setStyleSheet("border-radius: 0px;border: 1px solid black;")

        self.combo_box_2.addItems(['vegetarian', 'vegan', 'low carb', 'gluten-free', 'easy'])
        choices2 = ['vegan', 'vegetarian', 'low carb', 'gluten-free', 'easy']
        self.button = QPushButton(frame)
        self.button.setText('Recipes')
        self.button.setObjectName('recipes')
        self.button.setGeometry(185, 230, 80, 30)
        self.button.setFont(font_small)
        self.button.setStyleSheet("QPushButton { border: 2px solid black; border-radius: 5px;"
                                  "background-color:" + str(primary_color) + "  }")
        apply_button_styles(self.button, "[objectName='recipes']", 'push')

        self.button.clicked.connect(self.goToRecipes)

    def goToRecipes(self):
        play_sound(click_sound)
        meal = self.combo_box_1.currentText()
        category = self.combo_box_2.currentText()
        payload = {'meal': meal, 'category': category}
        recepies = []
        response = requests.post('http://localhost:5000/get_recepies', json=payload)
        if response.status_code == 200:
            data = response.json()
            recepies = data['result']

            if not recepies:
                error_popup('Momentan nu exista retete care satisfac aceste criterii.')

            else:
                self.stackedWidget.secondPage = Recipes(self.stackedWidget, recepies)
                self.stackedWidget.addWidget(self.stackedWidget.secondPage)
                self.stackedWidget.setCurrentWidget(self.stackedWidget.secondPage)
        else:
            error_popup('Error while getting the steps.')


class Recipes(QWidget):
    def __init__(self, stackedWidget, recepies):
        super().__init__()
        self.setObjectName('Recipes')

        self.stackedWidget = stackedWidget
        self.items_per_page = 4
        self.information = recepies
        self.current_page = 1
        self.total_pages = len(recepies) // self.items_per_page + 1

        self.page_label = QLabel()
        self.page_label.setFont(font_big)
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setText(f'Page {self.current_page} of {self.total_pages}')

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.itemClicked)

        self.prev_button = QPushButton('Previous')
        self.prev_button.setObjectName('previous')
        self.next_button = QPushButton('Next')
        self.next_button.setObjectName('next')
        self.sort_button = QPushButton()
        self.sort_button.setIcon(QIcon('icons/sort-ascending.png'))
        self.sort_button.setObjectName('sort')

        # #D38E57
        self.prev_button.setStyleSheet("QPushButton { background-color:" + str(primary_color) + "  }")
        self.next_button.setStyleSheet("QPushButton { background-color:" + str(primary_color) + "  }")
        self.sort_button.setStyleSheet("QPushButton { background-color:" + str(primary_color) + "  }")
        apply_button_styles(self.prev_button, "[objectName='previous']", 'push')
        apply_button_styles(self.next_button, "[objectName='next']", 'push')
        apply_button_styles(self.sort_button, "[objectName='sort']", 'push')

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.sort_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.page_label)
        self.main_layout.addLayout(button_layout)
        self.main_layout.addWidget(self.list_widget)

        self.setLayout(self.main_layout)

        self.prev_button.clicked.connect(self.previousPage)
        self.next_button.clicked.connect(self.nextPage)
        self.sort_button.clicked.connect(self.sortAfterTime)

        self.showPage(self.current_page)

    def sortAfterTime(self):
        play_sound(click_sound)
        initial_dictionary = {}
        recipes = {}
        for info in self.information:
            parts = info.split(' - ')
            recipe = parts[0]
            time = parts[1]
            initial_dictionary[recipe] = time
            time_info = re.findall(r'\d+', time)
            total_minutes = 0
            if len(time_info) == 2:  # am ora si minute
                hours, minutes = time.split("h ")
                minutes = minutes.replace("mins", "")
                total_minutes = int(hours) * 60 + int(minutes)
            else:
                if 'h' in time:
                    hours = time.split('h')
                    total_minutes = int(hours[0]) * 60
                else:
                    minutes = time.split('mins')
                    total_minutes = int(minutes[0])
            recipes[recipe] = total_minutes
        sorted_dict = sorted(recipes.items(), key=lambda x: x[1])
        self.information = []
        for recipe in sorted_dict:
            self.information.append(f"{recipe[0]} - {initial_dictionary[recipe[0]]}")
        self.showPage(self.current_page)

    def showPage(self, page):
        start_index = (page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page

        recipes_to_display = self.information[start_index:end_index]
        self.list_widget.clear()

        for recipe in recipes_to_display:
            pieces = recipe.split(' - ')
            name_str = pieces[0]

            time_icon = QLabel()
            pixmap = QPixmap('icons/meal.png')
            pixmap = pixmap.scaled(25, 25, Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)
            time_icon.setPixmap(pixmap)
            time_icon.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            time_icon.setContentsMargins(0, 0, 0, 0)
            time_str = f'  Cooking time: {pieces[1]}'
            name_label = QLabel(name_str)
            time_label = QLabel(time_str)
            name_label.setStyleSheet(f'color: {regular_text};text-decoration: underline;')
            font_small.setPointSize(11)
            name_label.setFont(font_small)
            font_small.setPointSize(7)
            font_small.setBold(True)
            font_small.setItalic(True)
            time_label.setStyleSheet(f'color: {important_text_color}')
            time_label.setFont(font_small)
            font_small.setPointSize(9)
            font_small.setBold(False)
            font_small.setItalic(False)

            layout = QVBoxLayout()
            layout.addWidget(name_label)
            layout_orizontal = QHBoxLayout()
            layout_orizontal.addWidget(QLabel('\t'))
            layout_orizontal.addWidget(time_icon)
            layout_orizontal.addWidget(time_label)
            layout_orizontal.addStretch(0)
            layout_orizontal.setSpacing(0)
            layout.addLayout(layout_orizontal)

            widget = QWidget()
            widget.setLayout(layout)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, name_str)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

            line_widget = QFrame()
            line_widget.setFrameShape(QFrame.HLine)
            line_widget.setFrameShadow(QFrame.Sunken)
            self.list_widget.addItem(QListWidgetItem())
            self.list_widget.setItemWidget(self.list_widget.item(self.list_widget.count() - 1), line_widget)

        font_small.setPointSize(11)
        self.list_widget.setFont(font_small)
        font_small.setPointSize(9)

        self.current_page = page
        self.page_label.setText(f'Page {self.current_page} of {self.total_pages}')

        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)

        self.list_widget.update()

    def previousPage(self):
        play_sound(page_sound)
        if self.current_page > 1:
            self.showPage(self.current_page - 1)

    def nextPage(self):
        play_sound(page_sound)
        if self.current_page < self.total_pages:
            self.showPage(self.current_page + 1)

    def itemClicked(self, item):
        content = item.data(Qt.UserRole)
        print(f'here {content}')
        name = content.split('\t')[0].replace('\n', '')
        self.stackedWidget.stepsPage = Steps(self.stackedWidget, name, self.information)
        self.stackedWidget.addWidget(self.stackedWidget.stepsPage)
        self.stackedWidget.setCurrentWidget(self.stackedWidget.stepsPage)


class Steps(QWidget):
    def __init__(self, stackedWidget, name, information):
        global buttons
        super().__init__()
        self.information = information
        self.setObjectName('Steps')
        self.back_button = QPushButton('Back')
        self.back_button.setObjectName('back')
        self.back_button.setFont(font_small)
        self.back_button.setFixedSize(100, 50)
        self.back_button.setStyleSheet("QPushButton { background-color:" + str(primary_color) + "  }")
        apply_button_styles(self.back_button, "[objectName='back']", 'push')

        self.read = QPushButton()
        self.read.setIcon(QIcon('icons/microphone.png'))
        self.read.setObjectName('read')
        self.read.setFixedSize(50, 50)
        self.read.setStyleSheet("QPushButton { background-color:" + str(primary_color) + "  }")
        apply_button_styles(self.read, "[objectName='read']", 'push')

        self.stop_reading = QPushButton()
        self.stop_reading.setObjectName('stop')
        self.stop_reading.setStyleSheet("QPushButton { background-color:" + str(primary_color) + "  }")
        apply_button_styles(self.stop_reading, "[objectName='stop']", 'push')
        self.stop_reading.setIcon(QIcon('icons/microphone-with-slash-interface-symbol-for-mute-audio.png'))
        self.stop_reading.setFixedSize(50, 50)

        self.back_button.clicked.connect(self.goBackToList)
        self.read.clicked.connect(self.readSteps)
        self.stop_reading.clicked.connect(self.stopReading)
        self.read.setEnabled(True)
        self.stop_reading.setEnabled(False)
        self.read.setContentsMargins(0, 0, 0, 0)
        self.stop_reading.setContentsMargins(0, 0, 0, 0)

        self.buttons = {'back': self.back_button, 'read': self.read, 'stop': self.stop_reading}
        buttons[self.objectName()] = self.buttons
        self.stackedWidget = stackedWidget
        self.name = name
        self.ingredients, self.steps, self.image, self.nutrition, self.time_info = self.get_steps()
        print(buttons)
        self.initUI()

    def initUI(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        recipe_widget = QWidget()
        recipe_layout = QVBoxLayout(recipe_widget)
        label_name = QLabel(f'{self.name}')
        label_name.setFont(font_big)
        label_name.setAlignment(Qt.AlignCenter)
        label_name.setStyleSheet(f'color: {important_text_color};text-decoration: underline')
        recipe_layout.addWidget(label_name)
        recipe_layout.addSpacing(50)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(-1)
        button_layout.addWidget(self.read)
        button_layout.addWidget(self.stop_reading)
        recipe_layout.addLayout(button_layout)
        if self.image is not None:
            image_label = QLabel()
            image_label.setFont(font_big)
            image_pixmap = QPixmap(f'images/{self.image}')
            image_label.setPixmap(image_pixmap.scaledToWidth(200))
            image_label.setAlignment(Qt.AlignCenter)
            recipe_layout.addWidget(image_label)

        recipe_layout.addSpacing(20)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        recipe_layout.addWidget(line)
        recipe_layout.addSpacing(20)

        label_time = QLabel('Time:')
        label_time.setStyleSheet(f'color: {important_text_color}')
        font_big.setItalic(True)
        label_time.setFont(font_big)
        font_big.setItalic(False)

        time_layout = QVBoxLayout()
        time_layout.addWidget(label_time)
        for time in self.time_info:
            time_label = QLabel(f"- {time}")
            time_label.setFont(font_small)
            time_label.setWordWrap(True)
            time_layout.addWidget(time_label)
        recipe_layout.addLayout(time_layout)
        recipe_layout.addSpacing(20)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        recipe_layout.addWidget(line)

        recipe_layout.addSpacing(20)

        label = QLabel('Ingredients:')
        label.setFont(font_big)
        ingredients_layout = QVBoxLayout()
        ingredients_layout.addWidget(label)
        index = 1
        for ingredient in self.ingredients:
            ingredient_label = QLabel(f"{index}. {ingredient}")
            ingredient_label.setFont(font_small)
            ingredient_label.setWordWrap(True)
            ingredients_layout.addWidget(ingredient_label)
            index += 1
        recipe_layout.addLayout(ingredients_layout)
        recipe_layout.addSpacing(20)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        recipe_layout.addWidget(line)
        recipe_layout.addSpacing(20)

        pasi = QLabel('Steps:')
        pasi.setFont(font_big)
        steps_layout = QVBoxLayout()
        steps_layout.addWidget(pasi)
        index = 1
        for step in self.steps:
            info = step.split(': ')[1]
            step_label = QLabel(f"<b>Step {index}:</b> {info}")
            step_label.setFont(font_small)
            step_label.setWordWrap(True)
            steps_layout.addSpacing(10)
            steps_layout.addWidget(step_label)
            index += 1
        recipe_layout.addLayout(steps_layout)

        # recipe_layout.addWidget(steps_label)
        recipe_layout.addStretch()
        recipe_layout.setContentsMargins(20, 20, 20, 40)
        scroll.setWidget(recipe_widget)
        recipe_layout.addSpacing(20)

        nutrition_frame = QFrame()
        nutrition_frame.setStyleSheet(f'background-color: {supplementary_color}')
        nutrition_frame.setFrameShape(QFrame.Box)
        nutrition_frame.setFrameShadow(QFrame.Raised)
        nutrition_layout = QVBoxLayout(nutrition_frame)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        recipe_layout.addWidget(line)
        recipe_layout.addSpacing(20)
        nutrition = QLabel('Nutrition:')
        nutrition.setFont(font_big)
        nutrition_label = QLabel(self.nutrition)
        nutrition_label.setFont(font_small)
        nutrition_label.setWordWrap(True)

        nutrition_layout.addWidget(nutrition)
        nutrition_layout.addWidget(nutrition_label)

        recipe_layout.addWidget(nutrition_frame)
        recipe_layout.addStretch()
        recipe_layout.setContentsMargins(20, 20, 20, 40)
        scroll.setWidget(recipe_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        main_layout.addWidget(self.back_button)
        self.setWindowTitle('Recipe')
        self.show()

    def readSteps(self):
        steps_to_read = ''.join(self.steps)
        play_sound(timer_sound)
        response = requests.post('http://localhost:5000/read', json={'steps': steps_to_read})
        if response.status_code != 200:
            error_popup('The steps cannot be read.')
        self.stop_reading.setEnabled(True)
        self.read.setEnabled(False)

    def goBackToList(self):
        play_sound(page_sound)
        self.stackedWidget.recipesPage = Recipes(self.stackedWidget, self.information)
        self.stackedWidget.addWidget(self.stackedWidget.recipesPage)
        self.stackedWidget.setCurrentWidget(self.stackedWidget.recipesPage)

    def get_steps(self):
        payload = {'name': self.name}
        print(payload)
        response = requests.post('http://localhost:5000/get_steps', json=payload)
        if response.status_code == 200:
            data = response.json()
            print(data)
            steps = data['steps'][0].split('\\n')
            ingredients = data['ingredients'][0].split('; ')
            image = data['image']
            nutrition = '\n'.join(data['nutrition'].split('; '))
            time_info = data['time'].split('; ')
            return ingredients, steps, image, nutrition, time_info
        else:
            error_popup('I did not found the steps.')
            return []

    def stopReading(self):
        play_sound(timer_sound)
        response = requests.post('http://localhost:5000/stop_reading')
        if response.status_code != 200:
            error_popup('Error while stopping.')
        self.read.setEnabled(True)
        self.stop_reading.setEnabled(False)


class SpeechThread(QThread):
    def __init__(self, stackedWidget):
        super().__init__()
        self.quit_flag = False
        self.stackedWidget = stackedWidget
        self.main_window = self.stackedWidget.parent()

    def run(self):
        global button_name
        while not self.quit_flag:
            response = requests.post('http://localhost:5000/speech')
            transcription = response.json().get('transcription')
            if transcription:
                button_name = transcription
                print(button_name)
                if self.main_window:
                    if button_name == "search":
                        search_button = self.main_window.search_button
                        search_button.click()
                    elif button_name == "home":
                        home_button = self.main_window.home_button
                        home_button.click()
                for index in range(self.stackedWidget.count()):
                    widget = self.stackedWidget.widget(index)
                    children = widget.findChildren(QWidget)
                    for child in children:
                        if isinstance(child, QPushButton) and child.objectName() == button_name:
                            child.click()
                        if widget.objectName() == 'SearchPage':
                            if isinstance(child, QComboBox):
                                if child.objectName() == 'tip' and button_name in choices1:
                                    print('tip setat')
                                    child.clear()
                                    child.addItems(choices1)
                                    child.setCurrentText(button_name)
                                    break
                                elif child.objectName() == 'preferinte' and button_name in choices2:
                                    print('pref setata')
                                    child.clear()
                                    child.addItems(choices2)
                                    child.setCurrentText(button_name)
                                    break

    def stop(self):
        self.quit_flag = True


class MainWindow(QMainWindow):
    def __init__(self):
        global button_name
        super().__init__()
        self.stackedWidget = QStackedWidget()
        self.setWindowTitle("Recepies")
        self.setObjectName('MainWindow')
        self.resize(1000, 700)
        toolbar = QToolBar()
        self.home_button = QToolButton()
        self.home_icon = QIcon("icons/home.png")
        self.home_button.setIcon(self.home_icon)
        self.home_button.setToolTip("Home")
        self.home_button.setObjectName('Home')
        apply_button_styles(self.home_button, "#Home", 'tool')
        toolbar.addWidget(self.home_button)

        buttons["home"] = self.home_button

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        toolbar.setStyleSheet(f'background-color: {primary_color}')

        self.search_button = QToolButton()
        search_icon = QIcon("icons/transparency.png")
        self.search_button.setIcon(search_icon)
        self.search_button.setToolTip("Search")
        self.search_button.setObjectName('search')
        apply_button_styles(self.search_button, "#search", 'tool')

        toolbar.addWidget(self.search_button)
        buttons["search"] = self.search_button

        self.addToolBar(toolbar)
        self.setCentralWidget(self.stackedWidget)

        main_page = MainPage(self.stackedWidget)
        search_page = SearchPage(self.stackedWidget)
        self.search_button.clicked.connect(self.goToPage2)
        self.home_button.clicked.connect(self.goHome)

        self.stackedWidget.addWidget(main_page)
        self.stackedWidget.addWidget(search_page)

        self.setStyleSheet(f"background-color: {secondary_color};")
        self.speech_thread = SpeechThread(self.stackedWidget)
        self.speech_thread.start()

    def handleButtonHover(self):
        sender = self.sender()
        button_name = sender.objectName()
        print(button_name)

    def goHome(self):
        play_sound(click_sound)
        self.stackedWidget.setCurrentIndex(0)

    def goToPage2(self):
        play_sound(click_sound)
        self.stackedWidget.setCurrentIndex(1)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
