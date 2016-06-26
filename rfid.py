#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import MFRC522
import signal
import Adafruit_CharLCD as LCD
import time
import datetime
# from bson.objectid import ObjectId
from bson.dbref import DBRef
import ConnectionDB


class RFID:

    def __init__(self):
        pass

    @staticmethod
    def save_in(mydb, id_user, dt):
        entrada = {
            "iEmpleado": [
                DBRef(collection="empleados", id=id_user)
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
                DBRef(collection="empleados", id=id_user)
            ],
            "horaSalida": dt
        }
        salidas = mydb.salidas
        salida_id = salidas.insert_one(salida).inserted_id
        print("ID de la salida: %s" % str(salida_id))

    @staticmethod
    def get_user(mydb, id_card):
        user = mydb.empleados.find_one(
            {
                "iTarjeta.$id": id_card
            }
        )
        return user

    @staticmethod
    def get_card_id(mydb, serie):
        card = mydb.tarjetas.find_one(
            {
                "serie": serie
            }, {"serie": 0}
        )
        return card

    @staticmethod
    def check_entrance(mydb, id_user, today):
        check = mydb.entradas.find_one(
            {
                "iEmpleado.$id": id_user
            }, {"horaEntrada": 1, "_id": 0}
        )
        if today >= check["horaEntrada"]:
            return True
        else:
            return False

    @staticmethod
    def get_id_inc(mydb, tpi):
        idi = mydb.tipos_incidencias.find_one(
            {
                "nombre": tpi
            }, {"nombre": 0}
        )
        return idi

    @staticmethod
    def save_incidence(mydb, id_user, today, idi):
        incidence = {
            "iEmpleado": [
                DBRef(collection="empleados", id=id_user)
            ],
            "idTIncidencia": [
                DBRef(collection="tipos_incidencias", id=idi)
            ],
            "fecha": today
        }
        incidencias = mydb.incidencias
        inc_id = incidencias.insert_one(incidence).inserted_id
        print("ID de la incidencia: %s" % str(inc_id))


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
            # print seriec
            idc = test.get_card_id(db, seriec)
            print idc['_id']
            usuario = test.get_user(db, idc['_id'])
            time_now = datetime.datetime.now()
            # Es entrada
            if test.check_entrance(db, usuario['_id'], time_now):
                salida = datetime.datetime.replace(time_now, hour=14, minute=30, second=00, microsecond=0)
                if time_now >= salida:
                    lcd.message("Hasta pronto")
                    # test.save_out(db, doc['_id'])
                else:
                    lcd.message("Aun no puedes salir")
            else:  # Es entrada
                ontime = datetime.datetime.replace(time_now, hour=8, minute=00, second=00, microsecond=0)
                retardo = datetime.datetime.replace(time_now, hour=8, minute=15, second=00, microsecond=0)
                if time_now <= ontime:
                    print("Estas a tiempo")
                    lcd.message("   Bienvenido:\n" + usuario['nombre'] + " " + usuario['apPaterno'])
                    # test.save_in(db, usuario['_id'])
                elif (time_now <= retardo) and (time_now > ontime):
                    print("Tienes retardo")
                    idi = test.get_id_inc(db, "Retardo")
                    # test.save_incidence(db, usuario['_id'], idi['_id'], time_now)
                elif time_now >= retardo:
                    print("Llegas tarde")
                    # test.save_incidence(db, usuario['_id'], time_now, idi['_id'])
            
            # Clear de screen
            time.sleep(2)
            lcd.clear()

if __name__ == "__main__":
    main()
