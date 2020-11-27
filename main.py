import wifimgr as wm

wlan = wm.get_connection()

if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("ESP OK")
from machine import Pin
import network
import time
from umqtt.robust import MQTTClient
import sys
import os
import ujson
import urequests
data2send = {
            "type": "note",
            "title": "Msg From NodeMCU",
            "body": "",
            }
API_KEY = 'api key'

pb_headers = {
'Access-Token': API_KEY,
'Content-Type': 'application/json',
'Host': 'api.pushbullet.com'
}
def notify(custom_msg):
    data2send["body"] = custom_msg
    r = urequests.post('https://api.pushbullet.com/v2/pushes', data=ujson.dumps(data2send), headers=pb_headers)
    time.sleep(5)
def call_back_routine(feed, msg):
    print('Received Data:  feed = {}, Msg = {}'.format(feed, msg))
    if ADAFRUIT_IO_FEEDNAME2 in feed :
        action = str(msg, 'utf-8')
        if action == 'ON':
            pin2.value(0)
        elif action == 'OFF':
            pin2.value(1)
        print('action = {} '.format(action))
    if ADAFRUIT_IO_FEEDNAME3 in feed:
        a = int(str(msg, 'utf-8'))
        threshold_notify.append(a)
        print('threshold={}'.format(threshold_notify))
    if ADAFRUIT_IO_FEEDNAME4 in feed:
        a = int(str(msg, 'utf-8'))
        threshold_water.append(a)
        print('threshold={}'.format(a))

ADAFRUIT_IO_URL = b'io.adafruit.com'
ADAFRUIT_USERNAME = b'Username here'
ADAFRUIT_IO_KEY = b'adafruit IO key here'
ADAFRUIT_IO_FEEDNAME1 = b'Moisture'
ADAFRUIT_IO_FEEDNAME2 = b'switch'
ADAFRUIT_IO_FEEDNAME3 = b'threshold'
ADAFRUIT_IO_FEEDNAME4 = b'threshold_water'
MESUREMENT_INTERVAL = 5
notification_interval = 3600
threshold_notify = [400]
threshold_water = [230]

# create a random MQTT clientID
random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_'+str(random_num), 'utf-8')


client = MQTTClient(client_id=mqtt_client_id,
                    server=ADAFRUIT_IO_URL,
                    user=ADAFRUIT_USERNAME,
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)

#ADAFRUIT_USERNAME/feeds/ADAFRUIT_IO_FEEDNAME1
mqtt_feedname1 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME1), 'utf-8')
mqtt_feedname2 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME2), 'utf-8')
mqtt_feedname3 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME3), 'utf-8')
mqtt_feedname4 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME4), 'utf-8')

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('ssid', 'password')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    try:
        client.connect()
    except Exception as e:
        print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
        sys.exit()


def Send_Data(tTemp) :
    client.publish(mqtt_feedname1,bytes(str(tTemp), 'utf-8'), qos=0)
def switch_0ff(off):
    client.publish(mqtt_feedname2, bytes(str(off), 'utf-8'), qos=0)
pin2 = Pin(4, Pin.OUT)
pin2.value(1)

def main():
    wlan = wm.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        while True:
            pass  # you shall not pass :D
    try:
        client.connect()
    except Exception as e:
        print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
        sys.exit()
    #do_connect()
    last_mesurement_time = 0
    client.set_callback(call_back_routine)
    client.subscribe(mqtt_feedname2)
    client.subscribe(mqtt_feedname3)
    client.subscribe(mqtt_feedname4)
    last_notification = time.time()-3610
    switch_0ff("off")
    while True:
        if (not wlan.isconnected()):
            wlan = wm.get_connection()
            client.connect()
            client.set_callback(call_back_routine)
            client.subscribe(mqtt_feedname2)
            client.subscribe(mqtt_feedname3)
            client.subscribe(mqtt_feedname4)

            if wlan is None:
                print("Could not initialize the network connection.")
                while True:
                    pass  # you shall not pass :D
        client.check_msg()
        i=len(threshold_notify)
        if i==0:
            i=1
        j = len(threshold_notify)
        if j == 0:
            j = 1
        current_time = time.time()
        if current_time - last_mesurement_time > MESUREMENT_INTERVAL:
            adc = machine.ADC(0)
            print('Moisture:', adc.read())
            Send_Data(adc.read())
            if adc.read()>threshold_notify[i-1] and last_notification+notification_interval<current_time:
                print(threshold_notify[i-1])
                notify("The soil is dry its time to turn on water.")
                last_notification=current_time
            if pin2.value()==0 and adc.read()<threshold_water[j-1]:
                pin2.value(1)
                switch_0ff("off")
            last_mesurement_time = current_time




if __name__ == '__main__':
    main()
