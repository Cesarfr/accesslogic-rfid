#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import MFRC522
import signal
import Adafruit_CharLCD as LCD
import time


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
MIFAREReader = MFRC522.MFRC522()

# Configure the GPIOs of the LCD are connected
lcd = LCD.Adafruit_CharLCD(rs=26, en=19, d4=13, d5=6, d6=5, d7=27, cols=16, lines=2)

# Clear de screen
lcd.clear()

# Welcome message
print "Bienvenido al ejemplo de lectura de tarjetas NFC"
print("Presiona Ctrl-C para cerrar")

time.sleep(1)

print "Listo!"

# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:

    # Scan for cards
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Tarjeta detectada"

    # Get the UID of the card
    (status, uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        # Print UID in the LCD
        lcd.message("Card read UID:\n" + str(uid[0]) + "," + str(uid[1]) + ","+str(uid[2]) + "," + str(uid[3]))

        # This is the default key for authentication
        key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

        # Check if authenticated
        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_Read(8)
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print "Authentication error"

        # Clear de screen
        time.sleep(2)
        lcd.clear()
