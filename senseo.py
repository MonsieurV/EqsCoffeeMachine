#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interface to the hacked Senseo coffee machine.

Use GPIO pin to communicate with the Senseo machine.

Released under MIT License. See LICENSE file.
"""
import time
try:
	import RPi.GPIO as GPIO
except RuntimeError:
	print("Error importing RPi.GPIO. Do you are root")

# Pin setup constants.
# Push delay to simulate a push button action.
PUSH_BTN_DELAY = 0.5
# Wired to the Senseo Power push button. High by default.
# If we put that to low it power on the machine.
PIN_POWER_SENSEO = 14
# Wired to the Senseo Short Coffee push button.
PIN_SHORT_SENSEO = 15
# Wired to the Senseo Long Coffee push button.
PIN_LONG_SENSEO = 18
# Senseo LED pin.
PIN_LED_SENSEO = 23
# Wired to the moisture sensor (to sense the water level in the Senseo tank).
PIN_MOISTURE_SENSOR = 24
# Wired to the relay for the water pump.
PIN_WATER_PUMP = 25

# Init GPIO.
GPIO.setmode(GPIO.BCM)
# Senseo button are high when not pushed.
GPIO.setup(PIN_POWER_SENSEO, GPIO.OUT)
GPIO.output(PIN_POWER_SENSEO, GPIO.HIGH)
GPIO.setup(PIN_SHORT_SENSEO, GPIO.OUT)
GPIO.output(PIN_SHORT_SENSEO, GPIO.HIGH)
GPIO.setup(PIN_LONG_SENSEO, GPIO.OUT)
GPIO.output(PIN_LONG_SENSEO, GPIO.HIGH)
GPIO.setup(PIN_LED_SENSEO, GPIO.IN)
GPIO.setup(PIN_MOISTURE_SENSOR, GPIO.IN)
# Pump is always off by default.
GPIO.setup(PIN_WATER_PUMP, GPIO.OUT)
GPIO.output(PIN_WATER_PUMP, GPIO.LOW)

class Senseo(object):
	@staticmethod
	def powerSenseo():
		GPIO.output(PIN_POWER_SENSEO, GPIO.LOW)
		time.sleep(PUSH_BTN_DELAY)
		GPIO.output(PIN_POWER_SENSEO, GPIO.HIGH)

	@staticmethod
	def makeCoffee(isShort):
		if isShort:
			print('Start a short coffee')
			GPIO.output(PIN_SHORT_SENSEO, GPIO.LOW)
			time.sleep(PUSH_BTN_DELAY)
			GPIO.output(PIN_SHORT_SENSEO, GPIO.HIGH)
		else:
			print('Start a long coffee')
			GPIO.output(PIN_LONG_SENSEO, GPIO.LOW)
			time.sleep(PUSH_BTN_DELAY)
			GPIO.output(PIN_LONG_SENSEO, GPIO.HIGH)

	@staticmethod
	def getSenseoState():
		"""Check if the Senseo machine is on or off.
		Return either:
		- ready
		- heating
		- default
		- off"""
		# Sample the LED output on 3 seconds.
		sumLeds = 0
		lastState = GPIO.input(PIN_LED_SENSEO)
		sumStateChange = 0
		for i in range(0, 3000):
			currentState = GPIO.input(PIN_LED_SENSEO)
			if currentState != lastState:
				sumStateChange = sumStateChange + 1
				lastState = currentState
			sumLeds = sumLeds + currentState
			time.sleep(0.001)
		if sumLeds < 10:
			return 'off'
		if sumLeds > 2800:
			return 'ready'
		if sumStateChange > 20:
			return 'default'
		else:
			print(sumStateChange)
			print(sumLeds)
			return 'heating'

	@staticmethod
	def enablePump():
		GPIO.output(PIN_WATER_PUMP, GPIO.HIGH)

	@staticmethod
	def disablePump():
		GPIO.output(PIN_WATER_PUMP, GPIO.LOW)

	@staticmethod
	def isTankFull():
		return GPIO.input(PIN_MOISTURE_SENSOR) == 1

	@staticmethod
	def close():
		GPIO.cleanup()
