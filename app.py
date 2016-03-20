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

USER_COFFEE = '@coffee'
CMD_COFFEE = ['coffee', u'café', 'court', 'short', 'long']
COFFEE_SHORT = ['short', 'court']
COFFEE_LONG = ['long']
PIN_SHORT = 26
PIN_LONG = 21

coffee_counter = {}

# Init GPIO.
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_SHORT, GPIO.OUT)
GPIO.setup(PIN_LONG, GPIO.OUT)
# Connect to Slack.
slack = SlackClient(SLACK_TOKEN)
if not slack.rtm_connect():
	raise RuntimeError('Invalid token')

def talk(message, channel='#hackathon_eqs'):
	slack.api_call(
		"chat.postMessage", channel=channel, text=message,
		username='Eqs Coffee Machine', icon_emoji=':coffee:'
	)

def isShort(message):
	return any(a in message for a in COFFEE_SHORT)

def isLong(message):
	return any(a in message for a in COFFEE_LONG)

def addCoffeeForUser(user, short_long):
	if user not in coffee_counter:
		coffee_counter[user] = {}
		coffee_counter[user]['short'] = 0
		coffee_counter[user]['long'] = 0
		talk("First coffee for @" + user + "! Thumbs up from the HackEQS team! :+1:")

	coffee_counter[user][short_long] = coffee_counter[user][short_long] + 1

	if coffee_counter[user][short_long] % 10 == 0:
		talk("Woow, that's your " + coffee_counter[user][short_long] + "th " + short_long + " coffee!")

print('Listening to Slack...')
try:
	while True:
		notifications = slack.rtm_read()
		for notification in notifications:
			if notification['type'] != 'message' or not 'text' in notification:
				continue
			print(notification)
			message = notification['text'].lower()
			user = slack.api_call(
				"users.info", user=notification['user']
			)
			if not USER_COFFEE in message or not any(a in message for a in CMD_COFFEE):
				continue
			if not isShort(message) and not isLong(message):
				talk('Here I am! Which kind of coffee do you want @'+ user['user']['name']+'?')
			if isShort(message):
				talk('One short coffee ordered!')
				GPIO.output(PIN_SHORT, GPIO.HIGH)
				time.sleep(1)
				GPIO.output(PIN_SHORT, GPIO.LOW)
				talk("Your short coffee is ready @" + user['user']['name'] + ". Short but strong, enjoy it!")
				addCoffeeForUser(user['user']['name'], 'short')
			if isLong(message):
				talk('A long coffee for a long day: that\'s on the way!')
				GPIO.output(PIN_LONG, GPIO.HIGH)
				time.sleep(1)
				GPIO.output(PIN_LONG, GPIO.LOW)
				talk("Your long coffee is ready @" + user['user']['name'] + ". Enjoy it!")
				addCoffeeForUser(user['user']['name'], 'long')
		time.sleep(1)
finally:
	GPIO.cleanup()
