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
from senseo import Senseo
from brewer import Brewer
from chat import Chat
brewer = None

print('Listening to Slack...')
try:
	while True:
		# Turn off water pomp.
		Senseo.disablePump()
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
		# If the tank is not full, activate the water pump.
		if not Senseo.isTankFull():
			Senseo.enablePump()
		time.sleep(0.5)
finally:
	Senseo.disablePump()
	Senseo.close()
