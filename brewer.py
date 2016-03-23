#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Control the coffee brewing process in a dedicated thread.

The thread is spammed to do a coffee. There can be only
on instance of this thread running at the time,
but that's the main app.py that is responsible
to enforce that.

Released under MIT License. See LICENSE file.
"""
import threading
import time
from senseo import Senseo
from chat import Chat

class Brewer(threading.Thread):
	def __init__(self, isShort, channel, user):
		threading.Thread.__init__(self)
		self.isShort = isShort
		self.channel = channel
		self.user = user

	def run(self):
		# Start the coffee making sequence.
		if self.isShort:
			Chat.talk('One short coffee ordered!', channel=self.channel)
		else:
			Chat.talk('A long coffee for a long day: that\'s on the way!',
				channel=self.channel)
		if Senseo.getSenseoState() == 'default':
			Chat.talk('Problem Ouston! Where\'s the water?',
				channel=self.channel)
			return
		if Senseo.getSenseoState() == 'off':
			print('Powering the Senseo machine')
			Senseo.powerSenseo()
		print('Wait for the machine to be ready')
		hasError = False
		for i in range(0, 25):
			state = Senseo.getSenseoState()
			if state == 'ready':
				break
			if state == 'default':
				# Double check.
				if Senseo.getSenseoState() == 'default':
					Chat.talk('Problem Ouston! Where\'s the water?',
						channel=self.channel)
					hasError = True
					break
		if hasError:
			return
		if state != 'ready':
			print(state)
			Chat.talk('Arg! I\'m dying! Help me! Is there any water remaining?',
				channel=self.channel)
			return
		Senseo.makeCoffee(self.isShort)
		print('Wait for the coffee to be ready')
		if self.isShort:
			time.sleep(25)
			Chat.talk("Your coffee is ready @{0}. :coffee: Short but strong, enjoy it!"
				.format(self.user['name']), channel=self.channel)
			Chat.addCoffeeForUser(self.user['name'], 'short', channel=self.channel)
		else:
			time.sleep(42)
			Chat.talk("Your long coffee is ready @{0}. Hope you'll like it!"
				.format(self.user['name']), channel=self.channel)
			Chat.addCoffeeForUser(self.user['name'], 'long', channel=self.channel)
		print('Shut down the Senseo machine')
		Senseo.powerSenseo()
