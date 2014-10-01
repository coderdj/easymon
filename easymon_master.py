import psutil
import pymongo
import datetime
from pymongo import MongoClient
import sys, getopt
import time
import ConfigParser

def main(argv):


    # Get command line option
    ini_path = "options.ini"
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:",["ini="])
    except getopt.GetoptError as err:
        print err
        sys.exit(2)
    for opt, arg in opts:
        if opt=='-h':
            print ("python easymon_master.py --ini={ini file}")
            sys.exit(0)
        elif opt in ( "-i", "--ini"):
            ini_path = arg
    
            
    # Defaults
    freq = 3600
    dbaddr = 'localhost'
    dbname = 'online'
    warnings = {}
    errors = {}

    # Timers ensure error spam doesn't happen
    warnings['timers'] = {}
    errors['timers'] = {}

    # Read ini file into options variables
    config = ConfigParser.ConfigParser()
    config.read( ini_path )
    if config.has_section( 'config' ):
        if config.has_option( 'config', 'dbaddr' ):
            dbaddr = config.get( 'config', 'dbaddr' )
        if config.has_option( 'config', 'dbname' ):
            dbname = config.get( 'config', 'dbname' )
        if config.has_option( 'config', 'freq' ):
            freq = config.getint( 'config', 'freq' )
    if config.has_section( 'warnings' ):
        for option in config.options( 'warnings' ):
            if option not in warnings:
                warnings[option] = {}
            opt = config.get('warnings',option)
            if opt[:-2] == 'MEM':
                warnings[option]['MEM'] = int(opt[3:])
            elif opt[:-2] == 'CPU':
                warnings[option]['CPU'] = int(opt[3:])
            elif opt[:-2] == 'DISK':
                warnings[option]['DISK'] = int(opt[4:])
    if config.has_section('errors'):
        for option in config.options('errors'):
            if option not in errors:
                errors[option] = {}
            opt = config.get('errors', option)
            if opt[:-2] == 'MEM':
                errors[option]['MEM'] = int(opt[3:])
            elif opt[:-2] == 'CPU':
                errors[option]['CPU'] = int(opt[3:])
            elif opt[:-2] == 'DISK':
                errors[option]['DISK'] = int(opt[4:])
        

    # Connect to DB
    try:
        mongoClient = MongoClient(dbaddr)
    except RuntimeError:
        print("Error connecting to mongodb server. Check your options.")
        return
    db = mongoClient[dbname]
    collection = db.sysmon
    
    # Keep looking for the most recent doc from each node
    while (1):

        # Get lsit of nodes in str format
        unodes = collection.distinct('node')
        nodes = []
        for item in unodes:
            nodes.append(str(item))

        for node in nodes:
            mostRecent = collection.find({'node':node}).sort('timestamp').limit(1)[0]
            # Check error fields
            if mostRecent['type'] in errors:
                for key,value in errors[mostRecent['type'] ].items() :
                    
                    if key == 'MEM':
                        comp = mostRecent['mem_pct']
                    elif key == 'CPU':
                        comp = mostRecent['cpu_pct']
                    else:
                        comp = mostRecent['disk_pct']
                    
                    # If there's a timer for this key there was already an alarm
                    # check to see if it should be lifted
                    if node in errors['timers'] and key in errors['timers'][node]:
                        
                        # If value below threshold check to see if timer should be lifted  
                        if comp < value and ( datetime.datetime.now() - errors['timers'][node][key] ).total_seconds() > freq:
                            errors['timers'][node].pop( key, 0)
                        # If value above threshold check to see if timer old enough to throw error
                        if comp > value and ( datetime.datetime.now() - errors['timers'][node][key] ).total_seconds() > freq:
                            errors['timers'][node][key] = datetime.datetime.now()
                            errstr = "ERROR! " + key + " is " + str(comp) + "% and threshold is " + str(value) + "%" + " for " + node
                            print errstr
                            MakeAlert(3, key, comp, value, db, node)

                    # There's no timer so just check
                    else:
                        
                        if comp > value:
                            if node not in errors['timers']:
                                errors['timers'][node] = {}
                            errors['timers'][node][key] = datetime.datetime.now()                            
                            errstr = "ERROR! " + key + " is " + str(comp) + "% and threshold is " + str(value) + "% for node " + node
                            print errstr
                            MakeAlert(3, key, comp, value, db, node)

                        
            # Check warning fields
            if mostRecent['type'] in warnings:
                for key,value in warnings[mostRecent['type'] ].items() :
                    
                    if key == 'MEM':
                        comp = mostRecent['mem_pct']
                    elif key == 'CPU':
                        comp = mostRecent['cpu_pct']
                    else:
                        comp = mostRecent['disk_pct']

                    # Check if there's an active error for this key. If so skip
                    if node in errors['timers'] and key in errors['timers'][node]:
                        continue
                    
                   
                    # Check if there's an active warning for this key
                    if node in warnings['timers'] and key in warnings['timers'][node]:
                   
                        # Check if timer can be lifted
                        if comp < value and ( datetime.datetime.now() - warnings['timers'][node][key] ).total_seconds() > freq:
                            warnings['timers'][node].pop(key, 0)
                        
                        # If value is above threshold check to see if timer is old enough to throw error
                        if comp > value and (datetime.datetime.now() - warnings['timers'][node][key]).total_seconds() > freq:
                            warnings['timers'][node][key] = datetime.datetime.now()
                            errstr = "WARNING! " + key + " is " + str(comp) + "% and threshold is " + str(value) + "% for node " + node
                            print errstr
                            MakeAlert(2, key, comp, value, db, node)
                    # There's no timers so just check threshold
                    else:
                        if comp > value:
                            if node not in warnings['timers']:
                                warnings['timers'][node] = {}
                            warnings['timers'][node][key] = datetime.datetime.now()
                            errstr = "WARNING! " + key + " is " + str(comp) + "% and threshold is " + str(value) + "% for node " + node
                            print errstr
                            MakeAlert(2, key, comp, value, db, node)

        time.sleep(5)
                
        
def MakeAlert(priority, thevar, theval, thresh, db, node):
    '''
    Create and alert and a lot message and put them into the database. In case of a class 3 alert (fatal error) 
    stop the DAQ wtih an appropriate message
    '''

    commentstring = "SystemMonitor warns that variable " + thevar + " has a value of " + str(theval) + ", which is above threshold " + str(thresh) + " for node " + node

    # In case of an error, stop the DAQ
    if priority == 3:
         commentstring = "SystemMonitor has stopped the DAQ because variable " + thevar + " has a value of " + str(theval) + ", which is above threshold " + str(thresh) + " for node " + node

         commandcollection = db.daqcommands
         commandDoc = {"command": "Stop",
                       "name"   : "SystemMonitor",
                       "comment": commentstring}
         commandcollection.insert(commandDoc)
    
    # Create an alert
    alertcollection = db.alerts
    mostRecent = alertcollection.find().sort('idnum', pymongo.DESCENDING).limit(1)
    if mostRecent.count() > 0:
        newid = mostRecent[0]['idnum'] + 1
    else:
        newid = 0
    alertInsert = {"idnum": newid,
                   "priority": priority,
                   "timestamp": datetime.datetime.now(),
                   "sender" : "SystemMonitor",
                   "addressed": False,
                   "message" : commentstring
                   }
    alertcollection.insert(alertInsert)

    # Finally log the thing
    logcollection = db.log
    logmessage = "Alert " + str(newid) + " has been created with message: " + commentstring
    loginsert = {"message": logmessage,
                 "priority": priority, 
                 "time" : datetime.datetime.now(),
                 "user" : "SystemMonitor"}
    logcollection.insert(loginsert)
    

if __name__ == "__main__":
    main(sys.argv[1:])

