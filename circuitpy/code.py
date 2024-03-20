# SPDX-FileCopyrightText: 2024 claus@freifunk-siegburg.de
#
# SPDX-License-Identifier: MIT

"""CircuitPython Xenon/Argon/Boron sysinfo, onboard LEDs, BLE Colourpicker toggeling USB.HID command Terminal to different OS """

import board
import os
import gc
import busio
import digitalio
import analogio
import microcontroller
import time
import adafruit_rgbled
import adafruit_bmp280

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
#from adafruit_hid.consumer_control_code import ConsumerControlCode

# USB.HID device keyboard and mouse emulation
# Pay attention on Keyboard using EN-US Keymapping, therefore input-strings sometimes look strange for german output
m = Mouse(usb_hid.devices)
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(kbd)

#
# USB.HID
#
# toggle switch for activation of USB.HID
# usbhid default from settings-file:
defaultusbhid = os.getenv("usbhid")
print("USB.HID Default from settings.toml file: ")
usbhid = 0
if defaultusbhid == 1:
    print("HID Service enabled\n")
else:
    print("HID Service disabled\n")
usbhid = defaultusbhid



#
# myOS:
#
# 0=openwrt [tested on stable-3.9.0 gluon Freifunk Firmware from RSK with openwrt base]
# 1=Linux Desktop [testet on Mint 21.3]
# 2=Windows Desktop [tested on 10/11]
# 3=MacOS Desktop [tested on Sonoma 14.4]
# 4=generic keyboard/mouse test
#

# Desktop Systems: runs out-of-the-box and opens/closes new Terminal Window on host and sends echo commands to it as proof of concept.
#
#         openwrt: has no default screen, so keyboard is not attached to a terminal and /dev/input/eventX has no effect on any console
#                  needs kernel modules for usb.vfat, usb.hid, usb.cdc etc. and triggerhappy package for keyboard-parsing
#                  optional uci vfat automount setting to make it work
#                  minicom package is helpful
#                  keep a look on flash space available on router - should provide 8MB as minimum like 1043ndV2 does
#                  preparation: create a file named 'sensors' in directory /etc/config with the following content:
#                  config circuitpython
#		                option disabled '0'
#		                option cputemp '0'
#		                option voltage '0'
#		                option charging '0'
#
#         generic: Just send Text and move mouse and don't care which App receives the input
#                  So better open a textpad and keep mouse focus on it before acticvating USB.HID by means of BLE-colourpicker

myOS = 0

defaultmyOS = os.getenv("myOS")
print("myOS Default from settings.toml file: ")
print(defaultmyOS)
print("\n")
myOS = defaultmyOS

sensorvalue=""


#
# BMP280 Sensor
#
defaultbmpsensor = os.getenv("bmp280Sensor")
print("BMP280 Default from settings.toml file: ")
print(defaultbmpsensor)
print("\n")
bmpsensor = defaultbmpsensor

# Power Battery Charging Status
vbat_voltage = analogio.AnalogIn(board.VOLTAGE_MONITOR)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536




# CHG: 0=charging, 1=no charging
charge = digitalio.DigitalInOut(board.CHARGE_STATUS)
charge.direction = digitalio.Direction.INPUT

# Bluetooth BLE name: CIRCUITPYabcd

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.color_packet import ColorPacket

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

ble = BLERadio()
uart_service = UARTService()
advertisement = ProvideServicesAdvertisement(uart_service)
nodename = ble.name

# Blue onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# RGB onboard LED
pixel_pin = board.RGB_LED_RED
pixel_pin2 = board.RGB_LED_GREEN
pixel_pin3 = board.RGB_LED_BLUE
rgbled = adafruit_rgbled.RGBLED(pixel_pin, pixel_pin2, pixel_pin3, invert_pwm = True)
rgbled.color = (0, 0, 255)

#
# i2C scan - makes no sense without device connected
#
# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)
# A reset line may be required if there is no auto-reset circuitry
#reset_pin = DigitalInOut(board.D5)
i2c.try_lock()
print("\nI2C devices found: ", [hex(i) for i in i2c.scan()])
i2c.unlock()

if bmpsensor:
    # Lets initialize
    print("Initializing BMP280 Sensor ...")
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c,address=0x76)
    # change this to match the location's pressure (hPa) at sea level
    bmp280.sea_level_pressure = 1013.25


while True:
    print("Hello, World!\n\n")
    # Show Platform Info and Pin-Mapping
    print("Running CircuitPython Version: "+os.uname().version+" on: "+os.uname().machine)
    # CPU Temperatur
    cpucelsius = microcontroller.cpu.temperature
    cpufahrenheit = cpucelsius * (9/5) +32
    print("CPU Temp: {:.2f}C".format(cpucelsius))
    print("CPU Temp: {:.2f}F\n".format(cpufahrenheit))

    # Power and Battery charging status
    battery_voltage = get_voltage(vbat_voltage)
    print("voltage: {:.2f}".format(battery_voltage))
    if charge.value:
       print("Battery not charging.")
    else:
       print("Battery charging.")

    # Show free memory
    freemem=gc.mem_free()
    print( "\nFree Memory: "+ str(freemem) )

    # Show free Diskspace
    fs_stat = os.statvfs('/')
    print("Disk size in MB", fs_stat[0] * fs_stat[2] / 1024 / 1024)
    print("Free space in MB", fs_stat[0] * fs_stat[3] / 1024 / 1024)


    # BLE
    # Advertise when not connected.
    ble.start_advertising(advertisement)

    # Lets check PINs on board
    print("Board Pin-Mapping:")
    for pin in dir(microcontroller.pin):
         if isinstance(getattr(microcontroller.pin, pin), microcontroller.Pin):
             print("".join(("microcontroller.pin.", pin, "\t")), end=" ")
             for alias in dir(board):
                 if getattr(board, alias) is getattr(microcontroller.pin, pin):
                    print("".join(("", "board.", alias)), end=" ")
         print()
    print("\n")

    if bmpsensor:
        # BMP 280 Values
        temp = bmp280.temperature - 4.1 # Chinaclone of BMP280 gives wrong results - lets correct
        displaytemp=("Temperature: %0.1f C"% temp)
        print(displaytemp)
        displaypressure=("Pressure: %0.1f hPa" % bmp280.pressure)
        print(displaypressure)
        print("Altitude = %0.2f meters" % bmp280.altitude)



    while not ble.connected:
        print(nodename + " waits for BLE connect.")
        if usbhid:
            print("USB.HID active.... starting")
            if myOS ==0:
                # set disabled flag to 0
                # complete string: "uci set sensors.@circuitpython[0].disabled=0\n"
 		        # with openwrt we have no terminal on host,
                # but triggerhappy daemon parses input and Keypress-Shortcuts for us.
                # Lets assume values like:
                #
                # sensors is running - lets set uci sensors flag
                kbd.press(Keycode.F1)
                kbd.release_all()
                # let uci commit sensors
                kbd.press(Keycode.U)
                kbd.release_all()
                # lets clear sensorvalue on openwrt
                kbd.press(Keycode.BACKSPACE)
                kbd.release_all()
                #
                #CPU Temp: 23.50C
                #
                mytemp = "{:.2f}".format(cpucelsius)
                temps = mytemp.split('.')  # create a list named 'words'
                print("Sending CPU-Temp value over usb.hid ....\n")
                print(temps[0])
                layout.write(temps[0])
                print(".")
                kbd.press(Keycode.PERIOD)
                kbd.release_all()
                print(temps[1])
                layout.write(temps[1])
                print("\n")
                # letz write uci value
                kbd.press(Keycode.C)
                kbd.release_all()
                # let uci commit sensors
                kbd.press(Keycode.U)
                kbd.release_all()
                # lets clear sensorvalue on openwrt
                kbd.press(Keycode.BACKSPACE)
                kbd.release_all()
                #
                #voltage: 2.97
                #
                myvoltage = "{:.2f}".format(battery_voltage)
                volts = myvoltage.split('.')
                print("Sending Voltage value over usb.hid ....\n")
                print(volts[0])
                layout.write(volts[0])
                print(".")
                kbd.press(Keycode.PERIOD)
                kbd.release_all()
                print(volts[1])
                layout.write(volts[1])
                print("\n")
                # letz write uci value
                kbd.press(Keycode.V)
                kbd.release_all()
                # let uci commit sensors
                kbd.press(Keycode.U)
                kbd.release_all()
                # lets clear sensorvalue on openwrt
                kbd.press(Keycode.BACKSPACE)
                kbd.release_all()


                #Battery not charging.
                # that's easy, cause 0/1 switch
                if charge.value:
                    # print("Battery not charging.")
                    # set true
                    kbd.press(Keycode.PAGE_DOWN)
                    kbd.release_all()

                else:
                    #print("Battery charging.")
                    # set false
                    kbd.press(Keycode.PAGE_UP)
                    kbd.release_all()

                # let uci commit sensors
                    kbd.press(Keycode.U)
                    kbd.release_all()

                # lets clear sensorvalue on openwrt
                kbd.press(Keycode.BACKSPACE)
                kbd.release_all()

		if bmpsensor:
                    #
		    # BME280 Sensor
                    #
                     # Temperature 
                     mytemp = bmp280.temperature - 4.1 # Chinaclone of BMP280 gives wrong results - lets correct
                     bmptemp = "%0.1f"% mytemp
        	     bmp280temp = bmptemp.split('.') 
                     print("Sending BMP280 Temperature value over usb.hid ....\n")
                     print(bmp280temp[0])
                     layout.write(bmp280temp[0])
                     print(".")
                     kbd.press(Keycode.PERIOD)
                     kbd.release_all()
                     print(bmp280temp[1])
                     layout.write(bmp280temp[1])
                     print("\n")
                     # letz write uci value
                     kbd.press(Keycode.T)
                     kbd.release_all()
                     # let uci commit sensors
                     kbd.press(Keycode.U)
                     kbd.release_all()
                     # lets clear sensorvalue on openwrt
                     kbd.press(Keycode.BACKSPACE)
                     kbd.release_all()
 


                     # Pressure 
                     mypressure = "%0.1f" % bmp280.pressure
                     tmppress = mypressure.split('.')
                     print("Sending BMP280 Pressure value over usb.hid ....\n")
                     print(tmppress[0])
                     layout.write(tmppress[0])
                     print(".")
                     kbd.press(Keycode.PERIOD)
                     kbd.release_all()
                     print(tmppress[1])
                     layout.write(tmppress[1])
                     print("\n")
                     # letz write uci value
                     kbd.press(Keycode.P)
                     kbd.release_all()
                     # let uci commit sensors
                     kbd.press(Keycode.U)
                     kbd.release_all()
                     # lets clear sensorvalue on openwrt
                     kbd.press(Keycode.BACKSPACE)
                     kbd.release_all()

 

 
		



            if myOS == 1:
                #
                # Linux Desktop shell example
                #
                # start a new terminal with CTRL+Alt+T
                #
                # You can also control press and release actions separately.
                kbd.press(Keycode.CONTROL, Keycode.ALT, Keycode.T)
                kbd.release_all()
                # show directory content
                time.sleep(2)
                #layout.write("ls\n")
                #layout.write("ps ax\n")

                # Power and Battery charging status

                battery_voltage = get_voltage(vbat_voltage)
                valvoltage = "echo Battarz voltage is {:.2f}".format(battery_voltage)

                layout.write(valvoltage)
                layout.write("\n")
                if charge.value:
                    layout.write("echo Batterz not charging.")
                    layout.write("\n")
                else:
                    layout.write("echo Batterz charging.")
                    layout.write("\n")
                time.sleep(10)

            if myOS == 2:
                #
                #
                # Windows Command Shell
                #
                # start a new command shell
                kbd.send(Keycode.WINDOWS, Keycode.R)
                time.sleep(0.11)
                layout.write("cmd\n")
                time.sleep(3)
                #layout.write("dir\n")
                # Power and Battery charging status
                battery_voltage = get_voltage(vbat_voltage)
                valvoltage = "echo Battarz voltage is {:.2f}".format(battery_voltage)

                layout.write(valvoltage)
                layout.write("\n")
                if charge.value:
                    layout.write("echo Batterz not charging.")
                    layout.write("\n")
                else:
                    layout.write("echo Batterz charging.")
                    layout.write("\n")
                time.sleep(10)


            if myOS == 3:
                # start a new terminal with CTRL+Alt+T
                #
                # You can also control press and release actions separately.
                # Lets use searchlight
                kbd.press(Keycode.COMMAND, Keycode.SPACE)
                kbd.release_all()
                # show directory content
                time.sleep(5)
                layout.write("terminal\n")
                time.sleep(5)
                #layout.write("top\n")
                #time.sleep(10)
                # Power and Battery charging status
                battery_voltage = get_voltage(vbat_voltage)
                valvoltage = "echo Battarz voltage is {:.2f}".format(battery_voltage)

                layout.write(valvoltage)
                layout.write("\n")
                if charge.value:
                    layout.write("echo Batterz not charging.")
                    layout.write("\n")
                else:
                    layout.write("\necho 'Batterz charging.\n'")
                    layout.write("\n")
                time.sleep(10)

            if myOS ==4:
                # default mouse and keyboard
                #
                # Type 'moving mouse.' followed by Enter (a newline).
                layout.write(nodename + " moving mouse.\n")
                # Move the mouse diagonally to the upper left.
                m.move(-100, -100, 0)
        else:
            print("USB.HID inactive.... doing nothing")
        led.value = True
        rgbled.color = (255, 0, 0)
        time.sleep(1)
        led.value = False
        rgbled.color = (0, 255, 0)
        time.sleep(1)
        led.value = True
        rgbled.color = (0, 0, 255)
        if usbhid:
           print("USB.HID active part2")
           if myOS ==4:
               #
               # default mouse and keyboard
               #
               # Type 'moving mouse.' followed by Enter (a newline).
               layout.write(nodename + " moving mouse back.\n")
               # Move the mouse diagonally to the upper left.
               m.move(100, 100, 0)
        time.sleep(1)
        led.value = False
        rgbled.color = (255, 255, 255)
        time.sleep(1)
        if usbhid:
            print ("USB.Hid active - cleaning up")
            # embedded
            if myOS == 0:
                print("USB.HID no cleanup needed")
            # Linux
            if myOS == 1:
                layout.write("\nexit\n")
            # windows
            if myOS == 2:
                # Lets use keyboard shortcut
                kbd.press(Keycode.ALT, Keycode.F4)
                kbd.release_all()
                time.sleep(5)

            # MacOS
            if myOS == 3:
                # Lets use keyboard shortcut
                kbd.press(Keycode.COMMAND, Keycode.Q)
                kbd.release_all()
                time.sleep(5)
                # send return for confirm closing process window
                layout.write("\n")
                time.sleep(10)

            # generic
            if myOS ==4:
                # default mouse and keyboard
                # delete the 61 chars printed before
                #  BACKSPACE = 42
                counter = (x for x in range(61))
                for x in counter:
                    # Press and release BACKSPACE.
                    kbd.press(Keycode.BACKSPACE)
                    time.sleep(.09)
                    kbd.release(Keycode.BACKSPACE)
        pass

    ble.stop_advertising()

    while ble.connected:

       # print("BLE is connected")
        if uart_service.in_waiting:
            packet = Packet.from_stream(uart_service)
            if isinstance(packet, ColorPacket):
                print(packet.color)
                rgbled.color = (packet.color)
            if usbhid:
                usbhid = 0
                print("USB.HID switched to inactive.")
                # for openwrt only
                if myOS == 0:
                     # lets switch uci flag to inactive
                     # sensors is running - lets set uci sensors flag
		     kbd.press(Keycode.F2)
                     kbd.release_all()
                     # let uci commit sensors
                     kbd.press(Keycode.U)
                     kbd.release_all()
            else:
                usbhid = 1
                print("USB.HID switched to active.")
                # for openwrt only
                if myOS == 0:
                     # lets switch uci flag to inactive
                     # sensors is running - lets set uci sensors flag
                     kbd.press(Keycode.F1)
                     kbd.release_all()
                     # let uci commit sensors
                     kbd.press(Keycode.U)
                     kbd.release_all()
