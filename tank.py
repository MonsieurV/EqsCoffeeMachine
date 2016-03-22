#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manage the Eqs Coffee Machine pump and tank.

Check the level of the tank and enable the pump when required.

Released under MIT License. See LICENSE file.
"""
import threading
import time
from senseo import Senseo

class Tank(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		try:
			# Check if Tank if empty.
			if Senseo.getSenseoState() != 'default':
				return
			# TODO Add an emergency security.
			# If the tank is full, disable the water pump whatever happened.
			# if Senseo.isTankFull():
			# 	print('Tank is full')
			# 	Senseo.disablePump()
			# 	return
			# Pump for 60 seconds.
			print('Pump for 60 seconds')
			Senseo.enablePump()
			time.sleep(60)
			print('End of pumping process')
			Senseo.disablePump()
			time.sleep(2)
		finally:
			Senseo.disablePump()