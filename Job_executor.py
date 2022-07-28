from time import sleep
import pymongo
from datetime import datetime
import json
from bson import ObjectId

client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
db = client.get_database('total_records')

fmt = '%Y-%m-%dT%H:%M'

# remove from queue and add to executed jobs
def getJobs():
    time_now = datetime.now().strftime(fmt)
    log_data = []
    cmds_search = db.queue_jobs.find({"execution_time":time_now})
    for job in cmds_search:
        #print(json.dumps(job, indent=4))
        #log_data.append(json.dumps(job, indent=4))
        cmd_id = job["cmd_id"]
        job_id = job["_id"]
        exec_job_input = {'cmd_id': str(cmd_id), 'execution_time': time_now}
        db.queue_jobs.delete_one({"_id":job_id})
        log_data.append("Removing this job from the queue list")
        db.executed.insert_one(exec_job_input)
        log_data.append("Adding this executed job from the queue list")

    for log in log_data:
        lg = {}
        lg["type"]="Info"
        lg["log"]=log
        db.logs.insert_one(lg)


# serch for existing jobs 
if __name__ == '__main__':
    while(1):
        print("##########################################################################################")
        getJobs()
        print("##########################################################################################")
        sleep(58)
