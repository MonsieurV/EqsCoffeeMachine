#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Control Equisense Coffee Machine from Slack.

Released under MIT License. See LICENSE file.
By Yoan Tournade <yoan@ytotech.com>
and Cyril Fougeray <cyril.fougeray@gmail.com>

TODO
* Get friendly state of machine from Slack
  Ask a person after it have made a coffee if the machine is ready
  for the next coffee (mug + pod)
* Get technical state of machine from Slack: ready, default, heating
* Fill tank 60 seconds after a default
* If there are 2 succesive default throw an alert: "No more water?"
* Produce a video of a typical day at Equisense with the Eqs Coffee Machine.
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
import json

# User experience constants.
USER_COFFEE = '@coffee'
CMD_COFFEE = ['coffee', u'café', 'court', 'short', 'long']
COFFEE_SHORT = ['short', 'court']
COFFEE_LONG = ['long']
FILE_PROCESSED = 'processed.json'
PROCESSED_MESSAGES = []
try:
	with open(FILE_PROCESSED) as f:
		PROCESSED_MESSAGES = json.load(f)
except IOError:
	pass
FILE_STATS = 'stats.json'
COFFEE_STATS = {}
try:
	with open(FILE_STATS) as f:
		COFFEE_STATS = json.load(f)
except IOError:
	pass
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

def addCoffeeForUser(user, short_long):
	# Init the dict.
	if 'short' not in COFFEE_STATS:
		COFFEE_STATS['short'] = {}
		COFFEE_STATS['short']['total'] = {}
	if 'long' not in COFFEE_STATS:
		COFFEE_STATS['long'] = {}
		COFFEE_STATS['long']['total'] = {}
	if user not in COFFEE_STATS:
		COFFEE_STATS[user] = {}
		COFFEE_STATS[user]['short'] = 0
		COFFEE_STATS[user]['long'] = 0
		talk("First coffee for @{0}! Thumbs up from the HackEQS team! :+1:"
			.format(user))
	# Update the dict.
	COFFEE_STATS[short_long]['total'] = COFFEE_STATS[short_long]['total'] + 1
	COFFEE_STATS[user][short_long] = COFFEE_STATS[user][short_long] + 1
	if COFFEE_STATS[user][short_long] % 10 == 0:
		talk("Woow, that's your {0}th {0} coffee!".
			format(COFFEE_STATS[user][short_long], short_long))
	with open(FILE_STATS, 'wb') as f:
		json.dump(COFFEE_STATS, f)

def setMessageAsProcessed(messageId):
	PROCESSED_MESSAGES.append(messageId)
	with open(FILE_PROCESSED, 'wb') as f:
		json.dump(PROCESSED_MESSAGES, f)

print('Listening to Slack...')
try:
	while True:
		# Turn off water pomp.
		GPIO.output(PIN_WATER_PUMP, GPIO.LOW)
		notifications = slack.rtm_read()
		for notification in notifications:
			if notification['type'] != 'message' or 'text' not in notification:
				continue
			message = notification['text'].lower()
			if not USER_COFFEE in message or 'user' not in notification:
				continue
			print(notification)
			if notification['ts'] in PROCESSED_MESSAGES:
				print('Already processed, ignore')
				continue
			setMessageAsProcessed(notification['ts'])
			user = slack.api_call('users.info', user=notification['user']).get('user')
			if not any(a in message.replace(USER_COFFEE, '') for a in CMD_COFFEE):
				talk('Yes @{0}, can I help you?'.format(user['name']),
					channel=notification['channel'])
				continue
			if not isShortInMessage(message) and not isLongInMessage(message):
				talk('Here I am! Which kind of coffee do you want @{0}?'
					.format(user['name']), channel=notification['channel'])
				continue
			isShort = isShortInMessage(message)
			if isShort:
				talk('One short coffee ordered!', channel=notification['channel'])
			else:
				talk('A long coffee for a long day: that\'s on the way!',
					channel=notification['channel'])
			# Start the coffee making sequence.
			if getSenseoState() == 'default':
				talk('Problem Ouston! Where\'s the water?',
					channel=notification['channel'])
				continue
			if getSenseoState() == 'off':
				print('Powering the Senseo machine')
				powerSenseo()
			print('Wait for the machine to be ready')
			hasError = False
			for i in range(0, 25):
				state = getSenseoState()
				if getSenseoState() == 'ready':
					break
				if getSenseoState() == 'default':
					# Double check.
					if getSenseoState() == 'default':
						talk('Problem Ouston! Where\'s the water?',
							channel=notification['channel'])
						hasError = True
						break
			if hasError:
				continue
			if state != 'ready':
				print(state)
				talk('Arg! I\'m dying! Help me!',
					channel=notification['channel'])
				continue
			makeCoffee(isShort)
			print('Wait for the coffee to be ready')
			if isShort:
				time.sleep(22)
				talk("Your coffee is ready @{0}. :coffee: Short but strong, enjoy it!"
					.format(user['name']), channel=notification['channel'])
				addCoffeeForUser(user['name'], 'short')
			else:
				time.sleep(40)
				talk("Your long coffee is ready @{0}. Hope you'll like it!"
					.format(user['name']), channel=notification['channel'])
				addCoffeeForUser(user['name'], 'long')
			print('Shut down the Senseo machine')
			powerSenseo()
		# If the tank is not full, activate the water pump.
		GPIO.output(PIN_WATER_PUMP, GPIO.input(PIN_MOISTURE_SENSOR))
		time.sleep(0.5)
finally:
	GPIO.output(PIN_WATER_PUMP, GPIO.LOW)
	GPIO.cleanup()
