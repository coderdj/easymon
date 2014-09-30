import psutil
import pymongo
import datetime
from pymongo import MongoClient
import sys, getopt
import time


def main(argv):
   dbAddr = 'xedaq01'
   node = 'unknown'
   updateFreq=10
   nodetype=0
   try:
       opts, args = getopt.getopt(sys.argv[1:],"ha:u:n:t:",["server=","update=","node=","type="])
   except getopt.GetoptError as err:
      print(err)
      print("sysmon.py -n <myname> -s <server address> -t <type> -u <update freq (s)>")
      sys.exit(2)
   for opt, arg in opts:
       if opt=='-h':
          print("sysmon.py -n <myname> -s <server address> -t <type> -u <update freq (s)>")
          sys.exit(0)
       elif opt in ("-s", "--server"):
          dbAddr=arg
       elif opt in ("-u", "--update"):
          updateFreq=arg
       elif opt in ("-n", "--node"):
          node=arg
       elif opt in ("-t", "--type"):
          nodetype=arg
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

      disk_pct = psutil.disk_usage('/')[3]

      print("CPU:  "+(str)(cpuPct))
      print("MEM:  "+(str)(memPct))      
      print("DISK: "+(str)(disk_pct))
      insertDoc = {"cpu_pct": cpuPct,
                   "mem_pct": memPct,
                   "disk_pct": disk_pct,
                   "timestamp": utc_timestamp,
                   "node": node,
                   "type": nodetype,
                   }
      collection.insert(insertDoc)
      time.sleep(updateFreq)
      

if __name__ == "__main__":
    main(sys.argv[1:])
