#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Control Equisense Coffee Machine from Slack.

Released under MIT License. See LICENSE file.
By Yoan Tournade <yoan@ytotech.com>
"""
import time
from slackclient import SlackClient

SLACK_TOKEN = 'xoxp-3070297167-3879679928-27980816180-4db831a2a0'
USER_COFFEE = '@uslackbot'
CMD_COFFEE = 'coffee'
COFFEE_SHORT = 'short'
COFFEE_LONG = 'long'

slack = SlackClient(SLACK_TOKEN)
if not slack.rtm_connect():
	raise RuntimeError('Invalid token')

def talk(message, channel='#hackathon_eqs'):
	slack.api_call(
		"chat.postMessage", channel=channel, text=message,
		username='Eqs Coffee Machine', icon_emoji=':coffee:'
	)

print('Listening to Slack...')
while True:
	notifications = slack.rtm_read()
	# [{u'text': u'coin', u'ts': u'1458399795.000050', u'user': u'U03RVKZTA',
	# u'team': u'T03228R4X', u'type': u'message', u'channel': u'C0Q2FPFQD'}]
	for notification in notifications:
		if notification['type'] != 'message' and not 'text' in notification:
			continue
		print(notification)
		message = notification['text'].lower()
		if not USER_COFFEE in message or not CMD_COFFEE in message:
			continue
		if not COFFEE_LONG in message and not COFFEE_SHORT in message:
			talk('Here I am! Which kind of coffee do you want?')
		if COFFEE_SHORT in message:
			talk('Short coffee ordered!')
		if COFFEE_LONG in message:
			talk('A long coffee for a long day!')
	time.sleep(1)
