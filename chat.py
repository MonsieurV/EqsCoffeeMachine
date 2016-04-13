#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manage the chatting part of the Eqs Coffee Machine.

Currently integrated with Slack.

Released under MIT License. See LICENSE file.
"""
from slackclient import SlackClient
# Add your Slack API token in a token.py file:
# SLACK_TOKEN = 'YOUR_SLACK_API_TOKEN'
from token import SLACK_TOKEN
import json
import datetime

# User experience constants.
USER_COFFEE = '@coffee'
CMD_COFFEE = ['coffee', u'café', 'court', 'short', 'long']
CMD_DISABLE = ['disable', 'sleep']
CMD_ENABLE = ['enable', 'wake_up']
COFFEE_SHORT = ['short', 'court']
COFFEE_LONG = ['long']
FILE_PROCESSED = 'processed.json'
PROCESSED_MESSAGES = []
IS_DISABLED = False
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

# Connect to Slack.
slack = SlackClient(SLACK_TOKEN)
actions = []
if not slack.rtm_connect():
	raise RuntimeError('Invalid token')


class Chat(object):
	@staticmethod
	def talk(message, channel='#hackathon_eqs'):
		slack.api_call(
			"chat.postMessage", channel=channel, text=message,
			username='Eqs Coffee Machine', icon_emoji=':coffee:'
		)

	@staticmethod
	def addCoffeeForUser(user, short_long, channel='#hackathon_eqs'):
		# Init the dict.
		if 'short' not in COFFEE_STATS:
			COFFEE_STATS['short'] = {}
			COFFEE_STATS['short']['total'] = 0
		if 'long' not in COFFEE_STATS:
			COFFEE_STATS['long'] = {}
			COFFEE_STATS['long']['total'] = 0
		if user not in COFFEE_STATS:
			COFFEE_STATS[user] = {}
			COFFEE_STATS[user]['short'] = 0
			COFFEE_STATS[user]['long'] = 0
			Chat.talk("First coffee for @{0}! Thumbs up from the HackEQS team! :+1:"
				.format(user), channel=channel)
		# Update the dict.
		COFFEE_STATS[short_long]['total'] = COFFEE_STATS[short_long]['total'] + 1
		COFFEE_STATS[user][short_long] = COFFEE_STATS[user][short_long] + 1
		if COFFEE_STATS[user][short_long] % 10 == 0:
			Chat.talk("Woow, that's your {0}th {1} coffee!".
				format(COFFEE_STATS[user][short_long], short_long), channel=channel)
		with open(FILE_STATS, 'wb') as f:
			json.dump(COFFEE_STATS, f)

	@staticmethod
	def setMessageAsProcessed(messageId):
		PROCESSED_MESSAGES.append(messageId)
		with open(FILE_PROCESSED, 'wb') as f:
			json.dump(PROCESSED_MESSAGES, f)

	@staticmethod
	def isShortInMessage(message):
		return any(a in message for a in COFFEE_SHORT)

	@staticmethod
	def isLongInMessage(message):
		return any(a in message for a in COFFEE_LONG)

	@staticmethod
	def getNotifications():
		return slack.rtm_read()

	@staticmethod
	def processNotification(notification):
		global IS_DISABLED
		if notification['type'] != 'message' or 'text' not in notification:
			return
		message = notification['text'].lower()
		if not USER_COFFEE in message or 'user' not in notification:
			return
		print(notification)
		if notification['ts'] in PROCESSED_MESSAGES:
			print('Already processed, ignore')
			return
		Chat.setMessageAsProcessed(notification['ts'])
		user = slack.api_call('users.info', user=notification['user']).get('user')
		if any(a in message for a in CMD_ENABLE):
			print "enable"
			IS_DISABLED = False
			Chat.talk('Hey Hey Hey! I missed you so much!',
				channel=notification['channel'])
			return

		if any(a in message for a in CMD_DISABLE):
			IS_DISABLED = True
			Chat.talk('Alright! I think it is time to sleep...',
				channel=notification['channel'])
			return

		if datetime.datetime.today().weekday() > 5 or datetime.datetime.today().hour > 20 or datetime.datetime.today().hour < 8 or IS_DISABLED:
			Chat.talk('I am on holiday :grin: Go ahead and prepare it by yourself!',
				channel=notification['channel'])
			return
		if not any(a in message.replace(USER_COFFEE, '') for a in CMD_COFFEE):
			Chat.talk('Yes @{0}, can I help you?'.format(user['name']),
				channel=notification['channel'])
			return
		if not Chat.isShortInMessage(message) and not Chat.isLongInMessage(message):
			Chat.talk('Here I am! Which kind of coffee do you want @{0}?'
				.format(user['name']), channel=notification['channel'])
			return
		isShort = Chat.isShortInMessage(message)
		actions.append({
			'type': 'brewAction',
			'notification': notification,
			'user': user,
			'isShort': isShort })

	@staticmethod
	def getNextAction():
		if len(actions) == 0:
			return None
		return actions.pop(0)
