import time
import multiprocessing
import re

import speech_recognition as sr
import pyttsx3
from flask import Flask, jsonify, request
import pyodbc
import config

app = Flask(__name__)
conn = pyodbc.connect(
    f'Driver={config.sql};Server={config.server};Database={config.database};UID={config.username};PWD={config.password};Trusted_Connection=True;')
running = False


@app.route('/stopListening', methods=['GET'])
def stop_running():
    global running
    running = False
    return jsonify({'raspuns': 'stopped'})


@app.route('/speech', methods=['POST'])
def speech_endpoint():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            transcription = recognizer.recognize_google(audio)
            response = {
                "success": True,
                "error": None,
                "transcription": transcription
            }
        except sr.RequestError:
            response = {
                "success": False,
                "error": "API unavailable",
                "transcription": None
            }
        except sr.UnknownValueError:
            response = {
                "success": False,
                "error": "Unable to recognize speech",
                "transcription": None
            }
    return jsonify(response)


@app.route('/read_text', methods=['POST'])
def read_text_back():
    engine2 = pyttsx3.init()
    data = request.get_json()
    text = data['text']
    engine2.say(text)
    engine2.runAndWait()
    engine2.stop()


@app.route('/get_recepies', methods=["POST"])
def get_recepies():
    data = request.get_json()
    meal = data['meal']
    category = data['category']
    print(meal)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, name, time FROM Recepies WHERE meal='{meal}' and category='{category}'")
    rows = cursor.fetchall()
    check = True
    recepies = []
    if rows is None:
        check = False
    else:
        for row in rows:

            pieces = row[2].split('; ')
            prep_time_str = pieces[0].split(': ')[1]
            cook_time_str = pieces[1].split(': ')[1]
            total_time = ''
            cook_time_number = re.findall(r'\d+', cook_time_str)
            prep_time_number = re.findall(r'\d+', prep_time_str)
            if 'h' in cook_time_str and 'h' in prep_time_str:
                total = int(prep_time_number[0]) + int(cook_time_number[0])
                total_time = str(total) + 'h'
            elif 'mins' in prep_time_str and 'h' in cook_time_str:
                total_time = f"{cook_time_number[0]}h {prep_time_number[0]}mins"
            elif 'h' in prep_time_str and 'mins' in cook_time_str:
                total_time = f"{prep_time_number[0]}h {cook_time_number[0]}mins"
            elif 'mins' in prep_time_str and 'mins' in cook_time_str:
                total = int(prep_time_number[0]) + int(cook_time_number[0])
                hours = total // 60
                minutes = total % 60
                if hours > 0:
                    if minutes == 0:
                        total_time = f"{hours}h"
                    else:
                        total_time = f"{hours}h {minutes}mins"
                else:
                    total_time = f"{minutes}mins"
            recepies.append(f"{row[1]} - {total_time}")
    return jsonify({'result': recepies})


@app.route('/get_steps', methods=["POST"])
def get_steps():
    data = request.get_json()
    name = data['name']
    print('back')
    cursor = conn.cursor()
    cursor.execute(f"SELECT ingrediente, recipe, imagePath, nutrition, time FROM Recepies WHERE name='{name}'")
    rows = cursor.fetchall()
    check = True
    steps = []
    ingredients = []
    image = ""
    nutrition = ''
    time = ''
    if rows is None:
        check = False
    else:
        for row in rows:
            ingredients.append(row[0])
            steps.append(row[1])
            image = row[2]
            nutrition = row[3]
            time = row[4]
    return jsonify({'ingredients': ingredients, 'steps': steps, 'image': image, 'nutrition': nutrition, 'time': time})


engine = pyttsx3.init()

process = None


def read(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    while True:
        time.sleep(1)


@app.route('/read', methods=['POST'])
def start():
    global process
    if process is None or not process.is_alive():
        text = request.get_json()['steps']
        process = multiprocessing.Process(target=read, args=[text])
        process.start()
    return ''


@app.route('/stop_reading', methods=['POST'])
def stop():
    global process
    if process is not None and process.is_alive():
        process.terminate()
    return ''


# stop_flag = False
#
#
# @app.route('/read', methods=['POST'])
# def read():
#     global stop_flag
#     data = request.get_json()
#     steps = data['steps']
#
#     stop_flag = False
#
#     def speak_steps():
#         for step in steps:
#             print(step)
#             print(stop_flag)
#             if stop_flag:
#                 engine.stop()
#             else:
#                 engine.say(step)
#
#         engine.runAndWait()
#         engine.stop()
#     threading.Thread(target=speak_steps).start()
#
#     return jsonify({'message': 'Speaking steps...'}), 200
#
#
# @app.route('/stop_reading', methods=['POST'])
# def stop():
#     global stop_flag
#     stop_flag = True
#     # engine.stop()
#     return jsonify({'stop_flag': stop_flag}), 200


@app.route('/text_to_speech', methods=["POST"])
def text_to_speech():
    print('here')
    data = request.get_json()
    text = data['input']
    print(text)
    engine = pyttsx3.init()
    res = ""
    try:
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        engine.runAndWait()
        res = "OK"
    except RuntimeError:
        res = "wait"

    return jsonify({'result': str(res)})


if __name__ == '__main__':
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    engine = pyttsx3.init()
    app.run()
