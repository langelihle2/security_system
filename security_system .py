#!/usr/bin/python3
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
import sys
sys.path.append('/home/pi/MFRC522-python')
import MFRC522
import signal
import MySQLdb
from RPLCD import CursorMode
from RPLCD import CharLCD
from time import sleep
import time
import random

GPIO.setmode(GPIO.BOARD)              # set up BCM GPIO numbering
GPIO.setup(32,GPIO.OUT)
GPIO.setup(36,GPIO.OUT)
GPIO.setup(8,GPIO.OUT)

global data
data = 0
temp = []
global counter
enteredPassword = []
password = [1,2,3,4]
counter = 0
incorrectpwd = 0
global tracking
tracking = 0
collectpwd = [5]
escape = 0

#configure lcd pins
lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[33, 31, 29, 40],numbering_mode=GPIO.BOARD)

# Set up input pin
GPIO.setup(3, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(38, GPIO.IN,pull_up_down=GPIO.PUD_UP)

#Text file for storing new generated password and records for triggured alarm
fo = open("foo.txt", "w")
triggered = open("Alarm.txt", "w")



lcd.write_string("welcome!!")

def buttonPressed():
    lcd.clear()
    global password
    global enteredPassword
    global counter
    global escape
    counter = 0
    global incorrectpwd
    global temp
lcd.cursor_mode = CursorMode.line
    lcd.write_string(u'Enter pwd:')

#two dimensional array storing each key
    MATRIX = [[1,2,3,'A'],
             [4,5,6,'B'],
             [7,8,9,'C'],
             ['*',0,'#','D']]


#assign rows and columns to different pins
    ROW = [7,11,12,13]
    COL = [15,16,18,36]

#set columns as outputs
    for j in range(4):
        GPIO.setup(COL[j], GPIO.OUT)
        GPIO.output(COL[j], 1)

#configure rows as input with internal pull up resistors
    for i in range(4):
        GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)
    escape +=1
    if(escape < 3 ):
            del temp[:]
            del enteredPassword[:]

    while(True):
            if(counter < 4):
               for j in range(4):
                     GPIO.output(COL[j],0)                                                  #clear input pin
                     for i in range(4):
                              if GPIO.input(ROW[i]) == 0:
                                    enteredPassword.append(MATRIX[i][j])                     #add the pressed key to the list
                                    print "{}".format(enteredPassword)
                                    lcd.write_string(u'{}'.format(MATRIX[i][j]))
                                    counter += 1
                                    time.sleep(0.2)
                                    while(GPIO.input(ROW[i]) == 0):                         #while key is pressed do nothing
                                            pass
                     GPIO.output(COL[j],1)
            else:
                break                             #break out of the loop after 4 inputs

    temp = enteredPassword
    return temp

#cllback function interrupt function for keypad
def decide(channel):
    global tracking
    for i in range(3):                                        #assign three attempts
         collectpwd = buttonPressed()
         global incorrectpwd
         if(password == collectpwd):
              del password[:]
              del collectpwd[:]
              del enteredPassword[:]
              lcd.clear()
              lcd.write_string("Access granted!")
              GPIO.output(32,1)                      #signal to open gate
              sleep(1)
              GPIO.output(32,0)
              lcd.clear()
              for j in range(4):
                   password.append(random.randint(0,9))             #generate new password
                   print(password)
                   fo.write( "{}".format(password))                #print new password to the text file
              break
         #break 
         #incorrect password
         else:
            lcd.clear()
            del collectpwd[:]
            tracking += 1
            lcd.write_string("Access denied!")
            counter = 0
            sleep(2)
            lcd.clear()
            if(tracking == 3):
                GPIO.output(8,1)                #TRIGGER ALARM
                sleep(1)
                GPIO.output(8,0)
                tracking = 0
                lcd.clear()
                lcd.write_string("Intruder Alert !!!")
                triggered.write("Incorrect password caused alarming : Time : %s" %time.strftime("%H:%M:%S"))
         break
#         break 

#callback function for rfid reader
def rfid(channel):
  db = MySQLdb.connect("localhost","pi","raspberry","mydb")                    #connect to database
    global data

    a = db.cursor()

    # Create an object of the class MFRC522
    MIFAREReader = MFRC522.MFRC522()

    lcd.clear()
    lcd.write_string("Place your card")
    lcd.cursor_pos = (1, 3)
    lcd.write_string("on rfid!!")

    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while True:

            # Scan for cards    
            (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

            # If a card is found
            if status == MIFAREReader.MI_OK:
                print "Card detected"
    
            # Get the UID of the card
            (status,uid) = MIFAREReader.MFRC522_Anticoll()

            # If we have the UID, continue
            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:

                serialnumber = uid[0],uid[1],uid[2],uid[3]

                sql = "SELECT * FROM propertyDatabase user WHERE serialnumber = serialnumber";
 
                a.execute(sql)
                data = a.fetchone()
                print data
                if(data > 0):                                #if serial number is found
                    print "You may enter"
                    lcd.clear()
                    lcd.write_string("Access Granted!!")
                else:
                    print ("denied access")
                    lcd.clear()
                    lcd.write_string("Access Denied!!")
                    sleep(2) 
                    lcd.clear()
                    print "Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3])
                    sleep(0.5)
                    break    

#interrupts
GPIO.add_event_detect(3, GPIO.RISING, callback=decide, bouncetime=150) 
GPIO.add_event_detect(38, GPIO.RISING, callback=rfid, bouncetime=150)
try:
  while True:              #loop for ever
     sleep(0.5)         
finally:                   # run on exit
    GPIO.cleanup()         # clean up
    print "All cleaned up."
