from time import sleep
import pymongo
from datetime import datetime
import json
from bson import ObjectId
import subprocess, os

client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
db = client.get_database('total_records')

fmt = '%Y-%m-%dT%H:%M'
#home_dir = '/home/matsy007/Downloads/Mesh/BLE-Mesh-Project/Commands/'
home_dir = '/home/pi/BLE/BLE-Mesh-Project/Commands/'
home_database_json = '/home/pi/Mesh_demo/nrf5sdkformeshv500src/scripts/interactive_pyaci/database/example_database.json'

# remove from queue and add to executed jobs
def getJobs():
    time_now = datetime.now().strftime(fmt)
    log_data = []

    # complete jobs that are to be done now
    cmds_search = db.queue_jobs.find({"execution_time":time_now})
    print(cmds_search)
    for job in cmds_search:
        # get the command details and chip_info
        cmd_id = job["_id"]
        cmds_search = list(db.commands.find({"_id":job["_id"]}))
        cmd = cmds_search[0]

        # update recent info
        recent_act = {}
        recent_act["time"] = time_now
        recent_act["text"] = ""
        if cmd["cmd_val"] == "1":
            recent_act["text"] = "Turned on LED 1 for "+cmd['chip_id']+" "+cmd['group_id']               
        else:
            recent_act["text"] = "Turned off LED 1 for "+cmd['chip_id']+" "+cmd['group_id'] 
        db.recent_info.insert_one(recent_act)

        # turn the entire group on or off
        if cmd['chip_id'] is "" :
            chips_search = list(db.chip_info.find({"Group_ID":cmd["group_id"]}))
            app_key = chips_search[0]["Group_ID"]
            address_handle = chips_search[0]["Group_ID_handle"]

            # update the group chip status
            filter = {'Group_ID':cmd["group_id"]}
            if cmd["cmd_val"] is "1":
                newValue = {'$set':{'Status':"ON"}}
            else:
                newValue = {'$set':{'Status':"OFF"}}
            db.chip_info.update_many(filter, newValue, upsert=False)
            
        else:
            chips_search = list(db.chip_info.find({"Chip_ID":cmd["chip_id"]}))
            app_key = chips_search[0]["Group_ID"]
            address_handle = chips_search[0]["Address_handle"]

            # update the chip status in chip_info 
            filter = {'Chip_ID':cmd["chip_id"]}
            if cmd["cmd_val"] is "1":
                newValue = {'$set':{'Status':"ON"}}
            else:
                newValue = {'$set':{'Status':"OFF"}}
            db.chip_info.update_one(filter, newValue, upsert=False)
        sleep(5)

        # log_data.append(json.dumps(job, indent=4))        
        job_id = job["_id"]
        exec_job_input = {'_id': cmd_id, 'execution_time': time_now}
        db.queue_jobs.delete_one({"_id":job_id})
        log_data.append("Removing this job from the queue list")
        db.executed.insert_one(exec_job_input)
        log_data.append("Adding this executed job from the queue list")

        # TO DO: generate the commands file here: 
        # doing it here so that even if commands if I gen file here => no race condition
        file_name = home_dir+'cmd_'+str(job_id)+'.txt'
        with open(file_name,"a") as cmd_file:
            cmd_file.write("db = MeshDB('{0}')\n".format(home_database_json))
            cmd_file.write('db.nodes\n')
            cmd_file.write('gc = GenericOnOffClient()\n')
            cmd_file.write('device.model_add(gc)\n')
            # check if you have to light entire group or chip alone
            cmd_file.write('gc.publish_set({0}, {1})\n'.format(app_key, address_handle))
            if cmd["cmd_val"] is "1":
                cmd_file.write('gc.set(True)\n')
            else:
                cmd_file.write('gc.set(False)\n')

        # TO DO: run the interactive python shell script system command
        print("Running the system command: "+file_name)
        #subprocess.run(["python3", "interactive_pyaci.py","-d", "COM8", "-l","3" ,"<",file_name])
        os.system("python3 /home/pi/Mesh_demo/nrf5sdkformeshv500src/scripts/interactive_pyaci/interactive_pyaci.py -d /dev/ttyACM0 < "+file_name)
        
        # TO DO: delete the command*.txt files too
        #subprocess.run(["rm","-rf",file_name])
        
        # prune jobs that are completed from the queue
        cmds_search = db.queue_jobs.find({"execution_time":{'$lt':time_now}})
        print(cmds_search)
        for job in cmds_search:
            cmd_id = job["_id"]
            job_id = job["_id"]
            exec_job_input = {'_id': cmd_id, 'execution_time': time_now}
            db.queue_jobs.delete_one({"_id":job_id})
            log_data.append("Removing this job from the queue list")
            db.executed.insert_one(exec_job_input)
            log_data.append("Adding this executed job from the queue list")
            # TO DO: delete the command*.txt files too


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
        sleep(25)
