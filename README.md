easymon
=======

Author: Daniel Coderre, LHEP, University of Bern
Date  : 30.09.2014

Brief
-----

System monitor that puts various diagnostic values into a mongodb database. 
A monitoring script can then be deployed to read the database and raise an 
alarm if certain conditions are met. These conditions are defined by the user 
in an ini file. 

Requirements
------------

psutil version 2.1.1
pymongo version 2.7.1

Tested with python 3.4. 

Installation of Monitor Script
------------------------------

Install this on each PC that should be monitored. The node name should 
be unique.

(optional) Install virtualenv (on ubuntu):

	sudo apt-get install python3.4-dev python-virtualenv
	virtualenv -p /usr/bin/python3.4 easymon
	source easymon/bin/activate

Install:

	pip install -r requirements.txt
	screen
	python easymon.py -n nodeName

Run:

	easymon --server={serveraddr} --node={nodename} --type={int}


Installation of Master Script
-----------------------------

Ideally install this on the database PC (or any PC with access to the DB).

(optional) Install virtualenv (commands for ubuntu):
	   
	 sudo apt-get install python3.4-dev python-virtualenv
	 virtualenv -p /usr/bin/python3.4 easymon
	 source easymon/bin/activate

Install:
	
	pip install -r requirements.txt
	
Run:
	python easymon_master.py --ini={inipath}


Ini file format
---------------	

The ini file allows you to set warning and error limits for nodes
based on type. The type is just an integer. Below is a suggested assignement
for type IDs:

    	 1 - DAQ Master
	 2 - DAQ Slave
	 3 - Mongodb buffer
	 4 - Web server
	 5 - Event builder node
	 
You can then set thresholds for warnings or errors based on the type and 
one of three measurables (CPU, MEM, DISK). 

The syntax is as follows:

    	 [warnings]
    	 2 MEM60      # create a warning for DAQ slaves over 60% memory
	 3 DISK70     # raise a warning for disk usage over 70% on buffer
	 [errors]
	 2 MEM80      # raise an error for DAQ slaves over 80% memory
	 3 DISK90     # raise an error for disk usage over 90% on buffer

You can additionally defined a frequency in seconds. A warning or error is 
only thrown the first time a node goes over threshold. In order for the 
warning or error to be thrown again the machine has to be under threshold for
at least 'n' seconds. The 'n' is defined by the frequency parameter:
   	 
	[config]
	freq: 3600 # max 1 warning per PC per hour

Lastly the database address, name, and collection should be defined.
       
       [config]
       dbaddr: localhost
       dbname: online
       collname: sysmon
