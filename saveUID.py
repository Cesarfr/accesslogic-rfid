#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import MFRC522
import signal
import Adafruit_CharLCD as LCD
import time
import datetime
from bson.dbref import DBRef
from ConnectionDB import ConnectionDB


class SaveUID:

    def __init__(self):
        pass

    @staticmethod
    def save_uid(mydb, uid):
        try:
            tarjeta = {
                "serie": uid,
                "estado": "inactivo"
            }
            tarjetas = mydb.tarjetas
            card_id = tarjetas.insert_one(tarjeta).inserted_id
            return "ID de la tarjeta: %s" % str(card_id)
        except IndexError:
            return "Esta tarjeta ya pertenece a alguien"


def main():
    save = SaveUID()
    connection = ConnectionDB().con
    db = connection.accesslogic
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
    print "Guardar UID de la tarjeta NFC"
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
            print seriec
            msg = save.save_uid(db, seriec)
            lcd.message(msg)
            # Clear the screen
            time.sleep(4)
            lcd.clear()

if __name__ == "__main__":
    main()
