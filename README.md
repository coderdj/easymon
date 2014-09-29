easymon
=======

System monitor that puts various diagnostic values into a mongodb database. Tested with python 3.

(optional) Install virtualenv (on ubuntu):

	sudo apt-get install python3.4-dev python-virtualenv
	virtualenv -p /usr/bin/python3.4 easymon
	source easymon/bin/activate

Install:

	pip install -r requirements.txt
	screen
	python easymon.py -n nodeName

Run:

	easymon --server={serveraddr} --node={nodename}


