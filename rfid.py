#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import MFRC522
import signal
import Adafruit_CharLCD as LCD
import time
import datetime
from bson.objectid import ObjectId
from bson.dbref import DBRef
import ConnectionDB


class RFID:

    def __init__(self):
        pass

    @staticmethod
    def save_in(mydb, id_user, dt):
        entrada = {
            "iEmpleado": [
                DBRef(collection="empleados", id=ObjectId(id_user))
            ],
            "horaEntrada": dt
        }
        entradas = mydb.entradas
        entrada_id = entradas.insert_one(entrada).inserted_id
        print("ID de la entrada: %s" % str(entrada_id))

    @staticmethod
    def save_out(mydb, id_user, dt):
        salida = {
            "iEmpleado": [
                DBRef(collection="empleados", id=ObjectId(id_user))
            ],
            "horaSalida": dt
        }
        salidas = mydb.salidas
        salida_id = salidas.insert_one(salida).inserted_id
        print("ID de la salida: %s" % str(salida_id))

    @staticmethod
    def get_user(mydb, id_card):
        user = mydb.empleados.find(
            {
                "iTarjeta.$id": ObjectId(id_card)
            }
        )
        return user

    @staticmethod
    def get_card_id(mydb, serie):
        card = mydb.tarjetas.find({"serie": serie}, {"serie": 0})
        return card


def main():
    test = RFID()
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
            #print seriec
            idc = test.get_card_id(db, seriec)
            for document in idc:
                print document['_id']
                usuario = test.get_user(db, document['_id'])
                for doc in usuario:
                    time_now = datetime.datetime.now()
                    ontime = datetime.datetime.replace(time_now, hour=8, minute=00, second=00, microsecond=0)
                    retardo = datetime.datetime.replace(time_now, hour=8, minute=15, second=00, microsecond=0)
                    if time_now <= ontime:
                        lcd.message("Estas a tiempo")
                    elif (time_now <= retardo) and (time_now > ontime):
                        lcd.message("Tienes retardo")
                    elif time_now >= retardo:
                        lcd.message("Llegas tarde")
                    #lcd.message("   Binvenido:\n" + doc['nombre'] + " " + doc['apPaterno'])
                    #test.save_in(db, doc['_id'])
            
            # Clear de screen
            time.sleep(2)
            lcd.clear()
            db.close()

if __name__ == "__main__":
    main()
