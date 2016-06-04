#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import MFRC522
import signal
import Adafruit_CharLCD as LCD
import time
from pymongo import MongoClient
import datetime
from bson.objectid import ObjectId


class RFID:

    # def __init__(self):  # special method __init__
    #     self.gg = ""

    @staticmethod
    def get_db():
        client = MongoClient(host="localhost", port=27017)
        db = client["accesslogic"]
        return db

    @staticmethod
    def save_in(mydb, id_user):
        entrada = {
            "iEmpleado": {
                "$ref": "empleados",
                "$id": id_user
            },
            "horaEntrada": datetime.datetime.now()
        }
        entradas = mydb.entradas
        entrada_id = entradas.insert_one(entrada).inserted_id
        print("ID de la entrada: %s" % str(entrada_id))

    @staticmethod
    def save_out(mydb, id_user):
        salida = {
            "iEmpleado": {
                "$ref": "empleados",
                "$id": id_user
            },
            "horaSalida": datetime.datetime.now()
        }
        salidas = mydb.salidas
        salida_id = salidas.insert_one(salida).inserted_id
        print("ID de la salida: %s" % str(salida_id))

    @staticmethod
    def get_user(mydb, id_card):
        user = mydb.posts.find(
            {
                "iTarjeta.$id": ObjectId(id_card)
            }
        )
        return user

    @staticmethod
    def get_card_id(mydb, serie):
        card = mydb.posts.find({"serie": serie}, {"serie": 0})
        return card


def main():
    test = RFID()
    db = test.get_db()
    continue_reading = True

    # Capture SIGINT for cleanup when the script is aborted
    def end_read(signal, frame):
        global continue_reading
        print "Ctrl+C capturado, Finalizando lectura."
        continue_reading = False
        GPIO.cleanup()

    # Hook the SIGINT
    signal.signal(signal.SIGINT, end_read)

    # Create an object of the class MFRC522
    reader = MFRC522.MFRC522()

    # Configure the GPIOs of the LCD
    lcd = LCD.Adafruit_CharLCD(rs=26, en=19, d4=13, d5=6, d6=5, d7=27, cols=16, lines=2)

    # Clear de screen
    lcd.clear()

    # Welcome message
    print "Bienvenido al ejemplo de lectura de tarjetas NFC"
    print "Presiona Ctrl-C para cerrar"

    time.sleep(1)

    print "Listo!"

    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while continue_reading:

        # Scan for cards
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

        # If a card is found
        if status == reader.MI_OK:
            print "Tarjeta detectada"

        # Get the UID of the card
        (status, uid) = reader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == reader.MI_OK:

            # Print UID in the LCD
            seriec = str(uid[0]) + "," + str(uid[1]) + "," + str(uid[2]) + "," + str(uid[3])
            idc = test.get_card_id(db, seriec)
            usuario = test.get_user(db, idc)

            lcd.message("   Binvenido:\n" + usuario['nombre'] + " " + usuario['aPaterno'])
            # # This is the default key for authentication
            # key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            #
            # # Select the scanned tag
            # reader.MFRC522_SelectTag(uid)
            #
            # # Authenticate
            # status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, 8, key, uid)
            #
            # # Check if authenticated
            # if status == reader.MI_OK:
            #     reader.MFRC522_Read(8)
            #     reader.MFRC522_StopCrypto1()
            # else:
            #     print "Authentication error"

            # Clear de screen
            time.sleep(2)
            lcd.clear()

if __name__ == "__main__":
    main()
