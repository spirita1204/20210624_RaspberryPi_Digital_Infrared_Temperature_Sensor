#project
import Adafruit_DHT
import sys
import time
import smbus
import RPi.GPIO as gpio
import requests
#LCD used 
sys.modules['smbus'] = smbus 
from RPLCD.i2c import CharLCD
lcd = CharLCD('PCF8574', address=0x27, port=1, backlight_enabled=True)
#DHT
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
#PIR
gpio.setmode(gpio.BCM)
PIR_IN = 14
LED_exceed = 17#left 6
LED_unexceed = 27#left 7
gpio.setup(PIR_IN, gpio.IN, gpio.PUD_UP)#set input 
gpio.setup(LED_exceed, gpio.OUT)#set output
gpio.setup(LED_unexceed, gpio.OUT)#set output
gpio.output(LED_exceed,False)
gpio.output(LED_unexceed,False)
#BUZZER
gpio.setup(22, gpio.OUT)
buzzer = gpio.PWM(22, 50)
#ULTRA_SONIC
trigger_pin = 5
echo_pin = 6
gpio.setup(trigger_pin, gpio.OUT)
gpio.setup(echo_pin, gpio.IN)
#WEB
TARGET_URL = 'localhost'

def send_trigger_pulse():
    gpio.output(trigger_pin, True)
    time.sleep(0.001)
    gpio.output(trigger_pin, False)

def wait_for_echo(value, timeout):
    count = timeout
    while gpio.input(echo_pin) != value and count > 0:
        count = count - 1

def get_distance():
    send_trigger_pulse()
    wait_for_echo(True, 5000)
    start = time.time()
    wait_for_echo(False, 5000)
    finish = time.time()
    pulse_len = finish - start
    distance_cm = pulse_len * 340 *100 /2
    return distance_cm

#detect people
def action(channel):
    lcd.clear()
    print("Motion detected")
    distance = get_distance()
    print("distance :", distance)
    if distance <= 15:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        checked = 0
        if humidity is not None and temperature is not None:
            #terminal
            print("Temp={0:0.1f} ".format(temperature))
            #lcd show information
            #turn on differ led 
            if int(temperature) >= 23:
                buzzer.start(10)
                gpio.output(LED_exceed,True)
                gpio.output(LED_unexceed,False)
                buzzer.ChangeFrequency(392)
                time.sleep(1)
                gpio.output(LED_exceed,False)
                buzzer.stop()
                checked = 1
            else :
                gpio.output(LED_exceed,False)
                gpio.output(LED_unexceed,True)
                time.sleep(1)
                gpio.output(LED_unexceed,False)
                checked = 0
            lcd.cursor_pos = (0, 0)
            lcd.clear()
            lcd.write_string("temp: {}".format(temperature))
            r = requests.get('http://{0}/web-jesse/LogRecord_GET.php?TEMP={1}&checked={2}'.format(TARGET_URL,temperature, checked))
            print("Server Return Code :", r.status_code)
            time.sleep(1)
            lcd.clear()
        else:
            print("Failed to retrieve data from sensor")
        lcd.clear()
    else:
        print("distance is too far!")
try:
    gpio.add_event_detect(PIR_IN, gpio.RISING, callback=action, bouncetime=200)
    while True:
        print("waiting the person passed by")
        lcd.clear() 
        lcd.cursor_pos = (0, 0) 
        lcd.write_string("waiting") #just test
        time.sleep(2)
except:
    gpio.cleanup()