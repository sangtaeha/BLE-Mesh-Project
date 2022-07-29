from crypt import methods
from flask import Flask, render_template, request, url_for, redirect, session
import pymongo, bcrypt, json, queue
from datetime import datetime
from datetime import timedelta
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "testing"
client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
db = client.get_database('total_records')
records = db.register
#executed_jobs = db.executed     # only contains job id's, start time, end time, interval
#queue_jobs = db.queue           # contains job id, start time, end time, interval
#commands = db.commands          # contains job id, cmd id, f, n, p, chipd id, group id


# for formatting time delta
fmt = '%Y-%m-%dT%H:%M'
def delta_to_string(duration):
    days, seconds = duration.days, duration.seconds
    weeks = max(days // 7, 0)
    months = max(weeks // 4, 0)
    years = max(months // 12, 0)
    days = max(days%7, 0)
    hours = max(seconds//3600, 0)
    minutes = max((seconds %3600)//60, 0)
    seconds = max((seconds % 60), 0)
    
    print("{} years, {} months, {} days, {} weeks, {} hours, {} seconds, {} minutes".format(years, months, days, weeks, hours, seconds, minutes))

    if years>0:
        return "{} years".format(years), "bi bi-circle-fill activity-badge text-danger align-self-start"
    elif months>0:
        return "{} months".format(months), "bi bi-circle-fill activity-badge text-warning align-self-start"
    elif weeks>0:
        return "{} weeks".format(weeks), "bi bi-circle-fill activity-badge text-primary align-self-start"
    elif days>0:
        return "{} days".format(days), "bi bi-circle-fill activity-badge text-info align-self-start"
    elif hours>0:
        return "{} hrs".format(hours), "bi bi-circle-fill activity-badge text-success align-self-start"
    elif minutes>0:
        return "{} mins".format(minutes), "bi bi-circle-fill activity-badge text-muted align-self-start"
    elif seconds>0:
        return "{} secs".format(seconds), "bi bi-circle-fill activity-badge text-danger align-self-start"
    else:
        return ""

@app.route('/sign_out')
def sign_out(user=""):
    session["email"]=""
    session.pop("email", None)
    return render_template('pages-login.html', user=user)

@app.route('/home_page')
def home_page(user=""):
   return render_template('index.html', user=user)

@app.route('/pages_faq')
def pages_faq():
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('pages-faq.html', user=user)

@app.route('/users_profile')
def users_profile():
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('users-profile.html', user=user)

@app.route('/pages_contact')
def pages_contact():
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('pages-contact.html', user=user)

@app.route('/pages_register', methods=['post','get'])
def pages_register():
    message=''
    
    if request.method == "POST":
        fullname = request.form.get("name")
        user = request.form.get("username")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        address = request.form.get("address")
        country = request.form.get("country")
        phone = request.form.get("phone")
        
        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})
        print(user)

        if user_found:
            message = 'There already is a user by that name'
            print(message)
            return render_template('pages-register.html', message=message)
        
        if email_found:
            message = 'This email already exists in database'
            print(message)
            return render_template('pages-register.html', message=message)
        
        if password1 != password2:
            message = 'Passwords should match!'
            print(message)
            return render_template('pages-register.html', message=message)
        else:
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            user_input = {'name': user, 'email': email, 'password': hashed, 'fullname': fullname, 'country':country, 'address':address, 'phone':phone }
            print(user_input)

            records.insert_one(user_input)
            session['email'] = email

            return render_template('index.html', user=user_input)
            
    return render_template('pages-register.html')

@app.route('/', methods=['post','get'])
def pages_login():
    message=''
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
        return render_template('index.html', user=user)

    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
    
        user_found = records.find_one({"name": user})

        if user_found:
            passwordcheck = user_found['password']            
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = user_found["email"]
                user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
                print(user)
                return render_template('index.html', user=user)
            else:
                if "email" in session:
                    user_found = records.find_one({"email": session["email"]})
                    user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
                    print(user)
                    return render_template('index.html', user=user)
                message = 'Wrong password'
                return render_template('pages-login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('pages-login.html', message=message)
    return render_template('pages-login.html')

@app.route('/pages_error_404')
def pages_error_404():
    f = open("./Mesh_demo.json")
    data = json.load(f)
    groups = {}
    for chip in data:
        chip["Status"]="ON"
        db.chip_info.insert_one(chip)
        if chip["Group_ID"] in groups:
            grp = groups[chip["Group_ID"]]
            grp["chip_info"][chip["Chip_ID"]] = chip
            groups[chip["Group_ID"]] = grp
        else:
            grp = {"Group_ID":chip["Group_ID"], "Group_handle": chip["Group_ID_handle"], "chip_info":{ chip["Chip_ID"]:chip } }
            groups[chip["Group_ID"]]=grp
    
    # insert groups dict to db
    for (grp_id, grp_info) in groups.items():
        db.group_info.insert_one(grp_info)
    return render_template('pages-error-404.html')

@app.route('/pages_blank')
def pages_blank():
   return render_template('pages-blank.html')

# Handle individual components 
@app.route('/component/<string:chip_id>', methods=['GET','POST'])
def component(chip_id):
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)

    print(chip_id)
    chip_info = db.chip_info.find_one({"Chip_ID":chip_id})
    return render_template('chip_info.html', user=user, chip_info=chip_info)

@app.route('/components')
def components():
    message=''
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    chips = db.chip_info.find()
    chip_info = []
    for chip in chips:
        chip_info.append(chip)
    return render_template('components.html', user=user, chips=chip_info)
   
@app.route('/group_view')
def group_view():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    groups = db.group_info.find()
    group_info = []
    for group in groups:
        group_info.append(group)
    print(group_info)
    return render_template('group-view.html', user=user, group_info=group_info)

@app.route('/bluetooth_devices')
def bluetooth_devices():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('bluetooth-devices.html', user=user)

# TO DO: While scheduling the jobs itself create the commands.txt file
@app.route('/scheduled_jobs', methods=['post','get'])
def scheduled_jobs():
    message = ''
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    # update the db and call the same 
    time_curr = datetime.now().strftime(fmt)    # string object
    log_data = []
    if request.method == "POST":
        cmd = request.form.get("todocmd")
        if "on" in cmd:
            cmd_val = "1"
        else:
            cmd_val = "0"
        chip_id = request.form.get("chipid")
        group_id = request.form.get("groupid")
        time_now = request.form.get("timenow")
        start_time = request.form.get("starttime")
        end_time = request.form.get("endtime")
        interval = request.form.get("interval")
        print(interval)

        # immediate scheduling
        if interval is "":
            time_to_execute = time_now
            cmd_input = {'chip_id': chip_id, 'group_id': group_id, 'cmd_val': cmd_val}
            log_data.append(json.dumps(cmd_input))
            cmd_id = db.commands.insert_one(cmd_input).inserted_id
            job_input = {'_id': cmd_id, 'execution_time': time_to_execute}        
            #log_data.append(json.dumps(job_input))

            # check the timestamp for execution
            if (time_to_execute > time_curr):
                log_data.append("Scheduling and adding to the queue of jobs that needs to be executed")
                db.queue_jobs.insert_one(job_input)
            else:
                log_data.append("Scheduling Immediately")
                db.executed.insert_one(job_input)
        
        # this is scheduling periodic intervals
        else:
            new_time = (datetime.strptime(start_time, fmt)+timedelta(seconds=int(interval))).strftime(fmt)
            while(end_time >= new_time):
                print(new_time)
                time_to_execute = new_time
                cmd_input = {'chip_id': chip_id, 'group_id': group_id, 'cmd_val': cmd_val}
                log_data.append("recursive adding"+json.dumps(cmd_input))
                cmd_id = db.commands.insert_one(cmd_input).inserted_id
                job_input = {'_id': cmd_id, 'execution_time': time_to_execute} 
                #log_data.append(json.dumps(job_input))

                # check the timestamp for execution
                if (time_to_execute > time_curr):
                    log_data.append("Scheduling and adding to the queue of jobs that needs to be executed")
                    db.queue_jobs.insert_one(job_input)
                else:
                    log_data.append("Scheduling Immediately")
                    db.executed.insert_one(job_input)
                
                # update the time
                new_time = (datetime.strptime(time_to_execute, fmt)+timedelta(seconds=int(interval))).strftime(fmt)
        
    # filling recent activity: jobs done so far section
    jobs = db.executed.aggregate([
                { "$sort": {"execution_time": -1}},
                { "$limit": 7} 
                ])
    executedjobs = jobs
    user_execute = []
    for job in executedjobs:
        job_exec = {}
        if time_curr < job["execution_time"]:
            continue
        log_data.append('\nJob with ID: \n'.format(str(job["_id"])))
        time_delta = delta_to_string(datetime.now() - datetime.strptime(job["execution_time"], fmt))
        job_exec["time"], job_exec["font"] = time_delta
        cmds_search = list(db.commands.find({"_id":job["_id"]}))
        if len(cmds_search) != 0:
            job_exec["chip_id"] = cmds_search[0]["chip_id"]
            job_exec["group_id"] = cmds_search[0]["group_id"]
            job_exec["cmd_val"] = cmds_search[0]["cmd_val"]
            user_execute.append(job_exec)
            log_data.append(json.dumps(job_exec))
    
    # filling recent activity: jobs in queue section
    jobs = db.queue_jobs.aggregate([
            { "$sort": {"execution_time": 1}},
            { "$limit": 7} 
        ])
    jobsqueue = jobs
    user_queue=[]
    for job in jobsqueue:
        print(job)
        job_exec = {}
        if time_curr > job["execution_time"]:
            continue
        job_exec["time"],job_exec["font"] = delta_to_string(datetime.strptime(job["execution_time"], fmt) - datetime.now())
        log_data.append('\nJob with ID: \n'.format(str(job["_id"])))
        cmds_search = db.commands.find({"_id":job["_id"]})
        job_exec["chip_id"] = cmds_search[0]["chip_id"]
        job_exec["group_id"] = cmds_search[0]["group_id"]
        job_exec["cmd_val"] = cmds_search[0]["cmd_val"]
        user_queue.append(job_exec)
        log_data.append(json.dumps(job_exec))

    for log in log_data:
        lg = {}
        lg["type"]="Info"
        lg["log"]=log
        db.logs.insert_one(lg)
    return render_template('scheduled-jobs.html', user=user, executed=user_execute, queuejobs=user_queue)
    
@app.route('/logs')
def logs():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    logs = db.logs.find()
    return render_template('logs.html', user=user, logs = logs)

# handle individual command edit
@app.route('/command/<string:cmd_id>', methods=['GET','POST'])
def command(cmd_id):
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    if request.method == "POST":
        updated_cmd = {}
        updated_job = {}
        cmd_id = request.form.get("todocmd")
        print("Changed val: {0}".format(cmd_id))
        chip_id = request.form.get("chipid")
        group_id = request.form.get("groupid")
        cmd_val = request.form.get("cmd_val")
        time_now = request.form.get("timenow")
        start_time = request.form.get("starttime")
        end_time = request.form.get("endtime")
        interval = request.form.get("interval")

        updated_cmd["chip_id"] = chip_id
        updated_cmd["group_id"] = group_id
        updated_cmd["cmd_val"] = cmd_val
        updated_job["cmd_id"] = cmd_id
        updated_job["execution_time"] = time_now

        # update the db: queue(update) and commands(replace)
        db.commands.replace_one({"_id":ObjectId(cmd_id)}, updated_cmd, upsert=True)
        db.queue_jobs.replace_one({"cmd_id":cmd_id}, updated_job, upsert=True)

        return redirect(url_for('commands'))


    print(cmd_id)
    commands = db.commands.find_one({"_id":ObjectId(cmd_id)})
    jobs = db.queue_jobs.find_one({"cmd_id":cmd_id})
    return render_template('edit-command.html', user=user, commands=commands, jobs=jobs)
    

# display only commands that are yet to be executed
# allow modifying the commands
# server side pagination
@app.route('/commands', methods=['GET','POST'])
def commands():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    queued_jobs = db.queue_jobs.aggregate([
            { "$sort": {"execution_time": 1}},
            { "$limit": 10} 
        ])
    commands=[]

    for job in queued_jobs:
        main_command={}
        time_curr = datetime.now().strftime(fmt)
        if time_curr > job["execution_time"]:
            continue
        command = db.commands.find_one({"_id":job["_id"]})
        main_command["chip_id"] = command["chip_id"]
        main_command["group_id"] = command["group_id"]
        main_command["cmd_val"] = command["cmd_val"]
        main_command["_id"] = str(command["_id"])
        duration = datetime.strptime(job["execution_time"], fmt)-datetime.now()
        print(duration)
        main_command["time"], main_command["font"] = delta_to_string(duration)
        commands.append(main_command)

    return render_template('commands.html', user=user, commands=commands)

@app.route('/tables_general')
def tables_general():
   return render_template('tables-general.html')

@app.route('/tables_data')
def tables_data():
   return render_template('tables-data.htmll')

@app.route('/charts_chartjs')
def charts_chartjs():
   return render_template('charts-chartjs.html')

@app.route('/charts_apexcharts')
def charts_apexcharts():
   return render_template('charts-apexcharts.html')

@app.route('/charts_echarts')
def charts_echarts():
   return render_template('charts-echarts.html')

@app.route('/icons_bootstrap')
def icons_bootstrap():
   return render_template('icons-bootstrap.html')

@app.route('/icons_remix')
def icons_remix():
   return render_template('icons-remix.html')

@app.route('/icons_boxicons')
def icons_boxicons():
   return render_template('icons-boxicons.html')

if __name__ == '__main__':
   app.run(host="0.0.0.0", debug = True)