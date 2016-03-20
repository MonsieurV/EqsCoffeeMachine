#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Control Equisense Coffee Machine from Slack.

Released under MIT License. See LICENSE file.
By Yoan Tournade <yoan@ytotech.com>
"""
import time
from slackclient import SlackClient
try:
	import RPi.GPIO as GPIO
except RuntimeError:
	print("Error importing RPi.GPIO. Do you are root")
# Add your Slack API token in a token.py file:
# SLACK_TOKEN = 'YOUR_SLACK_API_TOKEN'
from token import SLACK_TOKEN

# User experience constants.
USER_COFFEE = '@coffee'
CMD_COFFEE = ['coffee', u'café', 'court', 'short', 'long']
COFFEE_SHORT = ['short', 'court']
COFFEE_LONG = ['long']
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
GPIO.setup(PIN_POWER_SENSEO, GPIO.OUT)
GPIO.output(PIN_POWER_SENSEO, GPIO.HIGH)
GPIO.setup(PIN_SHORT_SENSEO, GPIO.OUT)
GPIO.output(PIN_SHORT_SENSEO, GPIO.HIGH)
GPIO.setup(PIN_LONG_SENSEO, GPIO.OUT)
GPIO.output(PIN_LONG_SENSEO, GPIO.HIGH)
GPIO.setup(PIN_LED_SENSEO, GPIO.IN)
GPIO.setup(PIN_MOISTURE_SENSOR, GPIO.IN)
GPIO.setup(PIN_WATER_PUMP, GPIO.OUT)
GPIO.output(PIN_WATER_PUMP, GPIO.LOW)

def powerSenseo():
	GPIO.output(PIN_POWER_SENSEO, GPIO.LOW)
	time.sleep(PUSH_BTN_DELAY)
	GPIO.output(PIN_POWER_SENSEO, GPIO.HIGH)

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

def getSenseoState():
	"""Check if the Senseo machine is on or off.
	Return either:
	- ready
	- heating
	- default
	- off"""
	# Sample the LED output on 4 seconds.
	# sumLeds = 0
	# for i in range(0, 4000):
	# 	sumLeds = sumLeds + GPIO.input(PIN_LED_SENSEO)
	# 	time.sleep(0.001)
	# print('LEDs: ' + str(sumLeds))

	# Read for 2 seconds.
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
	if sumLeds > 2900:
		return 'ready'
	if sumStateChange > 20:
		return 'default'
	else:
		return 'heating'

print(getSenseoState())
# Connect to Slack.
slack = SlackClient(SLACK_TOKEN)
if not slack.rtm_connect():
	raise RuntimeError('Invalid token')

def talk(message, channel='#hackathon_eqs'):
	slack.api_call(
		"chat.postMessage", channel=channel, text=message,
		username='Eqs Coffee Machine', icon_emoji=':coffee:'
	)

def isShortInMessage(message):
	return any(a in message for a in COFFEE_SHORT)

def isLongInMessage(message):
	return any(a in message for a in COFFEE_LONG)

print('Listening to Slack...')
try:
	while True:
		# Turn off water pomp.
		GPIO.output(PIN_WATER_PUMP, GPIO.LOW)
		notifications = slack.rtm_read()
		for notification in notifications:
			if notification['type'] != 'message' or not 'text' in notification:
				continue
			print(notification)
			message = notification['text'].lower()
			if not USER_COFFEE in message or not any(a in message for a in CMD_COFFEE):
				continue
			if not isShortInMessage(message) and not isLongInMessage(message):
				talk('Here I am! Which kind of coffee do you want?')
				continue
			isShort = isShortInMessage(message)
			if isShort:
				talk('One short coffee ordered!')
			else:
				talk('A long coffee for a long day: that\'s on the way!')
			# Start the coffee making sequence.
			if getSenseoState() == 'default':
				talk('Problem Ouston! Where\'s the water?')
				continue
			if getSenseoState() == 'off':
				print('Powering the Senseo machine')
				powerSenseo()
			print('Wait for the machine to be ready')
			for i in range(0, 15):
				state = getSenseoState()
				if getSenseoState() == 'ready':
					break
			if state != 'ready':
				talk('Arg! I\'m dying! Help me!')
				continue
			makeCoffee(isShort)
			print('Wait for the coffee to be ready')
			time.sleep(40)
			print('Shut down the Senseo machine')
			powerSenseo()
		# If the tank is not full, activate the water pump.
		GPIO.output(PIN_WATER_PUMP, not GPIO.input(PIN_MOISTURE_SENSOR))
		time.sleep(1)
finally:
	GPIO.output(PIN_WATER_PUMP, GPIO.LOW)
	GPIO.cleanup()
