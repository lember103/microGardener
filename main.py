#TODO
# web server
# stop pump if exception 

import network
import urequests
import ujson
import machine
import utime
import sys
import os

from machine import Pin
from creds import ssid, pw, appid

def output_to_file(output):
    print(output)
    f = open('data.txt', 'a')
    f.write(output)
    f.write('\n')
    f.close()

def wlan_connect():
    # activate the interface
    wlan.active(True)
    if not wlan.isconnected():
        output_to_file('connecting to wlan...')
        wlan.connect(ssid, pw)
        while not wlan.isconnected():
            pass
    output_to_file('wlan connected')
    output_to_file(str(wlan.ifconfig()))
    wlan.config(reconnects=5)
    
def wlan_disconnect():
    wlan.disconnect()
    wlan.active(False)
    output_to_file('wlan disconnected') 
    
def set_datetime():
    # get datetime from api in json
    res = urequests.get(url='http://worldtimeapi.org/api/timezone/Europe/Berlin')
    # create json obj
    json = ujson.loads(res.text)
    # get values from json
    dt      = json['datetime']
    year    = int(dt[:4])
    month   = int(dt[5:7])
    day     = int(dt[8:10])
    weekday = json['day_of_week']
    hours   = int(dt[11:13])
    minutes = int(dt[14:16])
    seconds = int(dt[17:19])
    subseconds = 0
    # set rtc
    rtc.datetime((year, month, day, weekday, hours, minutes, seconds, subseconds))
    output_to_file('datetime is {0}'.format(rtc.datetime()))
    
def get_weather_forecast():
    # get weather data from api in json
    res = urequests.get("https://api.openweathermap.org/data/2.5/onecall?lat=52.50368426455495&lon=13.49911801532067&units=metric&exclude=current,minutely,hourly,alerts&appid=" + appid)
    # create json obj
    json = ujson.loads(res.text)
    # get forecast for the current day
    ndf = json['daily'][0]
    # get max temp
    mtemp = ndf['temp']['max']
    output_to_file('max temp for the day is {0}'.format(mtemp))
    return mtemp

def get_timer():
    res = urequests.get("https://micro-gardener.herokuapp.com/api/timer")
    json = ujson.loads(res.text)
    return json
    
def run_pump(t):
    '''
    runtime t in seconds
    '''
    output_to_file('run pump for {0} seconds'.format(t))
    p5 = Pin(5, Pin.OUT)
    p5.value(1)
    
    deadline = utime.ticks_add(utime.ticks_ms(), (int)(t * 1000))
    while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
        if get_timer()["stopPump"]:
            break
        else:
            utime.sleep(1)

    p5.value(0)
    
def min_to_ms(t):
    return t * 60000

def h_to_ms(t):
    return t * 3.6 * 10**6

def sleep_until(t):
    '''
    sets esp32 to deepsleep until t
    t is hourly time, e.g. 17 is 17:00
    '''
    # get current hourly time and minutes
    th = rtc.datetime()[4]
    tm = rtc.datetime()[5]
    # calc time difference dt and dm in ms
    if t > th:
        dt = h_to_ms(t - th - 1)
    else:
        dt = h_to_ms(24 - th + t -1)
    dm = min_to_ms(60 - tm)
    # set deepsleep
    output_to_file('going to sleep until {0}:00'.format(t))
    machine.deepsleep(int(dt+dm))
    
def water_the_plants(mtemp):
    if mtemp < 25:
        run_pump(t=600)
    elif mtemp >= 25 and mtemp < 30:
        run_pump(t=900)
    else:
        run_pump(t=1200)        
    

##main
wlan = network.WLAN(network.STA_IF)
wlan_connect()


while True:
    
    pumpTimer = get_timer()
    print(pumpTimer)
    
    if not pumpTimer["done"]:
        run_pump(pumpTimer["minutes"] * 60)
        
    else:
        utime.sleep(1)
        print("sleep")

    
















