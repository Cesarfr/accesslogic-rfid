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
        try:
            check = list(mydb.entradas.find(
                {
                    "iEmpleado.$id": id_user
                }, {"horaEntrada": 1, "_id": 0}
            ).sort("horaEntrada", -1).limit(1))

            print "Entrada DB: %s" % check[0]["horaEntrada"]
            print "Hoy: %s" % today
            if check[0]["horaEntrada"] <= today:
                return False
            else:
                return True
        except IndexError:
            print "No hay registros de entrada"
            return True

    @staticmethod
    def check_exit(mydb, id_user, today):
        try:
            check = list(mydb.salidas.find(
                {
                    "iEmpleado.$id": id_user
                }, {"horaSalida": 1, "_id": 0}
            ).sort("horaSalida", -1).limit(1))
            print "Hora de salida: %s" % check[0]["horaSalida"]
            if check[0]["horaSalida"] < today:
                return False
            else:
                return True
        except IndexError:
            print "No hay registros de salida"
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

            ontime = datetime.datetime.replace(time_now, hour=14, minute=24, second=00, microsecond=0)
            retardo = datetime.datetime.replace(time_now, hour=14, minute=25, second=00, microsecond=0)
            salida = datetime.datetime.replace(time_now, hour=14, minute=26, second=00, microsecond=0)

            if time_now <= ontime:
                lcd.message("   Bienvenido:\n" + usuario['nombre'] + " " + usuario['apPaterno'])
                test.save_in(db, usuario['_id'], time_now)
            elif (time_now <= retardo) and (time_now > ontime):
                lcd.message("Tienes retardo:\n" + usuario['nombre'] + " " + usuario['apPaterno'])
                idi = test.get_id_inc(db, "Retardo")
                test.save_in(db, usuario['_id'], time_now)
                test.save_incidence(db, usuario['_id'], time_now, idi['_id'])
            elif (time_now >= retardo) and (time_now < salida):
                lcd.message("Llegas tarde:\n" + usuario['nombre'] + " " + usuario['apPaterno'])
                idi = test.get_id_inc(db, "Falta")
                test.save_in(db, usuario['_id'], time_now)
                test.save_incidence(db, usuario['_id'], time_now, idi['_id'])
            elif time_now >= salida:
                if test.check_exit(db, usuario['_id'], time_now):
                    lcd.message("Ya checaste\nsalida")
                else:
                    lcd.message("Hasta pronto\n" + usuario['nombre'] + " " + usuario['apPaterno'])
                    test.save_out(db, usuario['_id'], time_now)
            else:
                lcd.message("Aun no es hora \nde salida")
            
            # Clear de screen
            time.sleep(4)
            lcd.clear()

if __name__ == "__main__":
    main()
