SHELL := /bin/bash

start:
	python -u app.py > log.txt 2>&1 & echo $$! > run.pid;

stop:
	kill `cat run.pid` && rm run.pid
