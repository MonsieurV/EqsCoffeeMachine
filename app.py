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
* Produce a video of a typical day at Equisense with the Eqs Coffee Machine.
"""
import time
from senseo import Senseo
from brewer import Brewer
from chat import Chat
from tank import Tank
brewer = None
tank = None

print('Listening to Slack...')
try:
	while True:
		for notification in Chat.getNotifications():
			Chat.processNotification(notification)
		while True:
			action = Chat.getNextAction()
			if action is None:
				break
			if brewer and brewer.isAlive():
				Chat.talk('Oh I\'m kind of busy now! Please wait a bit and I\'ll take your order @{0}.'
					.format(action['user']['name']),
					channel=action['notification']['channel'])
				continue
			# Spam a brewing process.
			brewer = Brewer(action['isShort'], action['notification']['channel'],
				action['user'])
			brewer.start()
		if not tank or not tank.isAlive():
			# Spam a tank check process.
			tank = Tank()
			tank.start()
		time.sleep(0.5)
finally:
	Senseo.disablePump()
	Senseo.close()
