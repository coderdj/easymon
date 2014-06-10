import psutil
import pymongo
import datetime
from pymongo import MongoClient
import sys, getopt
import time


def main(argv):
   dbAddr = 'xedaq00'
   node = 'unknown'
   updateFreq=10
   try:
       opts, args = getopt.getopt(sys.argv[1:],"ha:u:n:",["server=","update=","node="])
   except getopt.GetoptError as err:
      print(err)
      print("sysmon.py -n <myname> -s <server address> -u <update freq (s)>")
      sys.exit(2)
   for opt, arg in opts:
       if opt=='-h':
          print("sysmon.py -n <myname> -s <server address> -u <update freq (s)>")
          sys.exit(0)
       elif opt in ("-s", "--server"):
          dbAddr=arg
       elif opt in ("-u", "--update"):
          updateFreq=arg
       elif opt in ("-n", "--node"):
          node=arg
   print("DB: "+dbAddr)
   print("Freq: "+ (str)(updateFreq))
   print("Node: "+(str)(node))

    #define mongodb interface
    #    print args
   try:
      mongoClient = MongoClient(dbAddr)
   except RuntimeError:
      print("Error connecting to mongodb server")
      return
   db=mongoClient['online']
   collection = db.sysmon
   collection.ensure_index("timestamp", expireAfterSeconds=360)
   while(1):
      cpuPct=psutil.cpu_percent()
      mem = psutil.virtual_memory()
      memPct = mem.percent
      
      timestamp = datetime.datetime.now()
      utc_timestamp=datetime.datetime.utcnow()

      print("CPU: "+(str)(cpuPct))
      print("MEM: "+(str)(memPct))      
      insertDoc = {"cpu_pct": cpuPct,
                   "mem_pct": memPct,
                   "timestamp": utc_timestamp,
                   "node": node,
                   }
      collection.insert(insertDoc)
      time.sleep(updateFreq)
      

if __name__ == "__main__":
    main(sys.argv[1:])