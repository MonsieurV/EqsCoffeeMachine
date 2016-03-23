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

# User experience constants.
USER_COFFEE = '@coffee'
CMD_COFFEE = ['coffee', u'café', 'court', 'short', 'long']
CMD_READY = ['yes', u'prêt', 'ready', 'oui', 'ok']
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
last_client = None
is_brewing = False
is_ready = False

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
			Chat.talk("Woow, that's your {0}th {0} coffee!".
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
		if 'ready?' in message or u'prêt ?' in message:
			Chat.tellIfReady(user)
			return
		if any(a in message for a in CMD_READY):
			is_ready = True
			print(is_ready)
			Chat.talk('Thanks for taking care of me @{0}, I\'m ready now!'
				.format(user['name']), channel=notification['channel'])
			return
		if not any(a in message.replace(USER_COFFEE, '') for a in CMD_COFFEE):
			Chat.talk('Yes @{0}, can I help you?'.format(user['name']), 
				channel=notification['channel'])
			return
		if not Chat.isShortInMessage(message) and not Chat.isLongInMessage(message):
			Chat.talk('Here I am! Which kind of coffee do you want @{0}?'
				.format(user['name']), channel=notification['channel'])
			return
		if is_brewing:
			Chat.talk('Oh I\'m kind of busy now! Please wait a bit and I\'ll take your order @{0}.'
					.format(user['name']),
					channel=notification['channel'])
		isShort = Chat.isShortInMessage(message)
		actions.append({
			'type': 'brewAction',
			'notification': notification,
			'user': user,
			'isShort': isShort })
		last_client = action['user']
		is_ready = False

	@staticmethod
	def getNextAction():
		if len(actions) == 0:
			return None
		return actions.pop(0)

	@staticmethod
	def setIsBrewing(isBrewing):
		is_brewing = isBrewing

	@staticmethod
	def tellIfReady(user):
		"""Tell to user whether the machine is ready to brew a coffee."""
		if is_brewing:
			Chat.talk('Right now I\'m brewing a coffee for @{0}, try a bit latter.'
					.format(last_client),
					channel='@{0}'.format(user['name']))
			return
		print(is_ready)
		if is_ready:
			Chat.talk('Ready to brew! Well, that\'s what @{0} tell me.'
					.format(last_client),
					channel='@{0}'.format(user['name']))
			return
		if last_client:
			Chat.talk('I don\t know, I ask @{0} right now.'
					.format(last_client),
					channel='@{0}'.format(user['name']))
			Chat.talk('@{0} would like to know if I\'m ready to brew another coffee. Does I am? Please tell him'
					.format(user['name']),
					channel='@{0}'.format(last_client))
			# TODO Notify back between the users.
			return
		Chat.talk('Hey I don\'t know! Maybe ask on @random or simply go check.',
			channel='@{0}'.format(user['name']))
