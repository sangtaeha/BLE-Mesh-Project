from crypt import methods
from tokenize import group
from flask import Flask, render_template, request, url_for, redirect, session
import pymongo, bcrypt, json, queue
from datetime import datetime
from datetime import timedelta
from bson import ObjectId
import subprocess, signal, os
from time import sleep
import igraph as ig
import json
import urllib3
import plotly as py
import plotly.graph_objs as go
import serial.tools.list_ports
myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]

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
#home_dir = '/home/matsy007/Downloads/Mesh/BLE-Mesh-Project/Commands/'
home_dir = os.getcwd() + '/Commands/'
home_database_json = os.getcwd()+'/scripts/interactive_pyaci/database/example_database.json'
##############################################################################
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
        return "", ""

@app.route('/sign_out', methods=['post','get'])
def sign_out(user=""):
    print(session)
    session["email"]=""
    message=''
    print("Called sign out")
    try:
        if request.method == "POST":
            print("Received post message")
            return redirect(url_for(''))
        return redirect(url_for('pages_login'))
    except:
        return render_template('error.html')

def create_graph():
    data = []
    f=open("./Mesh_demo.json","r")
    data=json.load(f)

    N = len(data)

    Edges=[]
    for i in range(N):
        for j in range(N):
            Edges.append([i, j])

    G=ig.Graph(Edges, directed=False)

    group = []
    labels = []
    for item in data:
        group.append(int(item["Group_ID"]))
        labels.append(item["Name"])

    layt=G.layout('kk', dim=3)

    Xn=[layt[k][0] for k in range(N)]# x-coordinates of nodes
    Yn=[layt[k][1] for k in range(N)]# y-coordinates
    Zn=[layt[k][2] for k in range(N)]# z-coordinates
    Xe=[]
    Ye=[]
    Ze=[]
    for e in Edges:
        Xe+=[layt[e[0]][0],layt[e[1]][0], None]# x-coordinates of edge ends
        Ye+=[layt[e[0]][1],layt[e[1]][1], None]
        Ze+=[layt[e[0]][2],layt[e[1]][2], None]

    trace1=go.Scatter3d(x=Xe, y=Ye, z=Ze, mode='lines', line=dict(color='rgb(125,125,125)', width=1), hoverinfo='none')
    trace2=go.Scatter3d(x=Xn, y=Yn, z=Zn, mode='markers', name='Mesh Nodes', marker=dict(symbol='circle', 
            size=6, color=group, colorscale='Viridis', 
            line=dict(color='rgb(50,50,50)', width=0.5)), 
            text=labels, hoverinfo='text')
    axis=dict(showbackground=False, showline=False, zeroline=False, showgrid=False, showticklabels=False, title='' )

    layout = go.Layout(
            title="",
            width=1000,
            height=1000,
            showlegend=False,
            scene=dict(
                xaxis=dict(axis),
                yaxis=dict(axis),
                zaxis=dict(axis),
            ),
        margin=dict(
            t=100
        ),
        hovermode='closest',
        annotations=[
            dict(
            showarrow=False,
                text="",
                xref='paper',
                yref='paper',
                x=0,
                y=0.1,
                xanchor='left',
                yanchor='bottom',
                font=dict(
                size=14
                )
                )
            ],    )

    data=[trace1, trace2]
    fig=go.Figure(data=data, layout=layout)
    js_str = py.offline.plot(fig, include_plotlyjs=False, output_type='div')
    js_str = js_str.strip("<div>")
    js_str = js_str.strip("</div>")
    return js_str

@app.route('/home_page', methods=['post','get'])
def home_page(user=""):
    print("called home page")
    print(session)
    try:
        if "email" in session and session["email"]!="":
            user_found = records.find_one({"email": session["email"]})
            user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
            js_string = create_graph()
            print(js_string)
            recent_info=[]
            time_now = datetime.now().strftime(fmt)
            jobs = list(db.recent_info.find({"time":{'$lt':time_now}}).limit(10).sort('time', -1))
            for job in jobs:
                print(job["text"])
                recent_activity = {}
                recent_activity["time"] = delta_to_string(datetime.now() - datetime.strptime(job["time"], fmt))
                recent_activity["text"] = job["text"]
                recent_info.append(recent_activity)
            return render_template('index.html', user=user, js=js_string, recents=recent_info)
        else:
            return redirect(url_for('pages_login')) 
    except:
        return render_template('error.html', message="Try again")  

@app.route('/pages_faq', methods=['post','get'])
def pages_faq():
    print(session)
    try:
        if "email" in session and session["email"]!="":
            user_found = records.find_one({"email": session["email"]})
            user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
            print(user)
            return render_template('pages-faq.html', user=user)
        else:
            return redirect(url_for('pages_login'))
    except:
        return redirect(url_for('pages_login'))

@app.route('/users_profile', methods=['post','get'])
def users_profile():
    print(session)
    try:
        if "email" in session and session["email"]!="":
            user_found = records.find_one({"email": session["email"]})
            user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
            print(user)
            return render_template('users-profile.html', user=user)
        else:
            return redirect(url_for('pages_login'))
    except:
        return redirect(url_for('pages_login'))
            

@app.route('/pages_contact', methods=['post','get'])
def pages_contact():
    print(session)
    try:
        if "email" in session and session["email"]!="":
            user_found = records.find_one({"email": session["email"]})
            user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
            print(user)
            return render_template('pages-contact.html', user=user)
        else:
            return redirect(url_for('pages_login'))
    except:
        return redirect(url_for('pages_login'))

@app.route('/pages_register', methods=['post','get'])
def pages_register():
    message=''
    
    try:
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
                message = 'Passwords should match! Try again'
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
    except:
        return render_template('error.html')  

@app.route('/', methods=['post','get'])
@app.route('/pages_login', methods=['post','get'])
def pages_login():
    message=''
    print("Called pages_login")
    print(session)
    if "email" in session and session["email"]!="":
        js_string = create_graph()
        print(js_string)
        recent_info=[]
        time_now = datetime.now().strftime(fmt)
        jobs = list(db.recent_info.find({"time":{'$lt':time_now}}).limit(10).sort('time', -1))
        for job in jobs:
            print(job["text"])
            recent_activity = {}
            recent_activity["time"] = delta_to_string(datetime.now() - datetime.strptime(job["time"], fmt))
            recent_activity["text"] = job["text"]
            recent_info.append(recent_activity)
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
        return render_template('index.html', user=user, js=js_string, recents=recent_info)
    try:
        if request.method == "POST":
            user = request.form.get("username")
            password = request.form.get("password")        
            user_found = records.find_one({"name": user})
            if user_found:
                passwordcheck = user_found['password']            
                if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                    print("Password matched")
                    session["email"] = user_found["email"]
                    user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
                    js_string = create_graph()
                    recent_info=[]
                    time_now = datetime.now().strftime(fmt)
                    jobs = list(db.recent_info.find({"time":{'$lt':time_now}}).limit(10).sort('time', -1))
                    for job in jobs:
                        print(job["text"])
                        recent_activity = {}
                        recent_activity["time"] = delta_to_string(datetime.now() - datetime.strptime(job["time"], fmt))
                        recent_activity["text"] = job["text"]
                        recent_info.append(recent_activity)
                    return render_template('index.html', user=user, js=js_string, recents=recent_info)
                else:
                    if "email" in session:
                        user_found = records.find_one({"email": session["email"]})
                        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
                        print("else case")
                        session["email"] = user_found["email"]
                        return render_template('index.html', user=user)
                    message = 'Wrong password'
                    print("Wrong password")
                    return render_template('pages-login.html', message=message)
            else:
                message = 'User found'
                return render_template('pages-login.html', message=message)
        return render_template('pages-login.html')
    except:
        return render_template('error.html', message="Error found, please check and login again")  

@app.route('/pages_error_404', methods=['post','get'])
def pages_error_404():
    try:
        f = open("./Mesh_demo.json")
        data = json.load(f)
        groups = {}
        for chip in data:
            db.chip_info.insert_one(chip)
            if chip["Group_ID"] in groups:
                grp = groups[chip["Group_ID"]]
                grp["chip_info"].append(chip["Chip_ID"])
                groups[chip["Group_ID"]] = grp
            else:
                grp = {"Group_ID":chip["Group_ID"], "Group_handle": chip["Group_ID_handle"], "chip_info":[chip["Chip_ID"]] }
                groups[chip["Group_ID"]]=grp
        
        # insert groups dict to db
        for (grp_id, grp_info) in groups.items():
            db.group_info.insert_one(grp_info)
        return render_template('pages-error-404.html')
    except:
        return render_template('error.html')  

@app.route('/pages_blank', methods=['post','get'])
def pages_blank():
   return render_template('pages-blank.html')

# Code for running the job immediately
def run_group_change(chip_id, old_group_id, new_group_id):
    chips_search = list(db.chip_info.find({"Chip_ID":chip_id}))
    chip = chips_search[0]
        
    device_key = chip["Dev_key_handle"]
    unicast_address = chip["Unicast_address_index"]
    address_handle = chip["Address_handle"]

    # TO DO: create the file    
    file_name = home_dir+'cmd_'+str(chip_id)+'_'+str(old_group_id)+'_'+str(new_group_id)+'.txt'
    with open(file_name,"a") as cmd_file:
        cmd_file.write("db = MeshDB('{0}')\n".format(home_database_json))
        cmd_file.write('cc = ConfigurationClient(db)\n')
        cmd_file.write('cc.force_segmented = True\n')
        cmd_file.write('device.model_add(cc)\n')
        cmd_file.write('cc.publish_set({0}, {1})\n'.format(device_key, address_handle))
        cmd_file.write('cc.model_app_unbind(db.nodes[{0}].unicast_address, {1}, mt.ModelId(0x1000))\n'.format(unicast_address, old_group_id))
        cmd_file.write('cc.model_app_bind(db.nodes[{0}].unicast_address, {1}, mt.ModelId(0x1000))\n'.format(unicast_address, new_group_id))
        cmd_file.write('cc.model_subscription_add(db.nodes[{0}].unicast_address, 0xc001, mt.ModelId(0x1000))\n'.format(unicast_address))

    # TO DO: run the interactive python shell script system command
    print("Changing the group from: {0} to {1} and file is: {2} ".format(old_group_id, new_group_id, file_name))

    #subprocess.run(["python3", "interactive_pyaci.py","-d", "COM8", "-l","3" ,"<",file_name])
    cmd_to_run = "python3 " + os.getcwd() + "/scripts_to_execute_commands/interactive_pyaci/interactive_pyaci.py -d /dev/ttyACM0 < "+file_name
    os.system(cmd_to_run)

    # TO DO: delete the command*.txt files too
    #subprocess.run(["rm","-rf",file_name])

# Handle individual components 
@app.route('/component/<string:chip_id>', methods=['GET','POST'])
def component(chip_id):
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    else:
        return redirect(url_for('pages_login'))

    try:
        if request.method == "POST":
            updated_cmd = {}
            updated_job = {}
            chip = request.form.get("todocmd")
            print("Chip_id is "+chip_id)
            chip_name = request.form.get("chipName")
            old_group_id = list(db.chip_info.find({"Chip_ID":chip_id}))[0]["Group_ID"]
            new_group_id = request.form.get("groupID")
            print(new_group_id)

            # update the chip_info 
            if (old_group_id == new_group_id)  or (new_group_id == ""):
                print("Same value")
                return redirect(url_for('components'))
            else:
                filter = {'Chip_ID':chip_id}
                newValue = {'$set':{'Group_ID':new_group_id}}
                db.chip_info.update_one(filter, newValue, upsert=False)

                # update the group_info too
                chip_info = list(db.group_info.find({"Group_ID":old_group_id}))[0]["chip_info"]
                chip_info.remove(chip_id)
                db.group_info.update_one({"Group_ID":old_group_id}, {'$set':{'chip_info':chip_info}}, upsert=False)
                
                # add this chip to new group
                chip_info = list(db.group_info.find({"Group_ID":new_group_id}))[0]["chip_info"]
                chip_info.append(chip_id)
                db.group_info.update_one({"Group_ID":new_group_id}, {'$set':{'chip_info':chip_info}}, upsert=False)
                
                # run group change command on Pi
                run_group_change(chip_id, old_group_id, new_group_id)

                return redirect(url_for('components'))

        print(chip_id)
        chip_info = db.chip_info.find_one({"Chip_ID":chip_id})
        return render_template('chip_info.html', user=user, chip_info=chip_info)
    except:
        return render_template('error.html')  

@app.route('/components', methods=['post','get'])
def components():
    message=''
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    else:
        return redirect(url_for('pages_login'))
        
    try:
        chips = db.chip_info.find()
        chip_info = []
        for chip in chips:
            chip_info.append(chip)
        return render_template('components.html', user=user, chips=chip_info)
    except:
        return render_template('error.html', message="This Functionality is disabled")  
   
@app.route('/group_view', methods=['post','get'])
def group_view():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    else:
        return redirect(url_for('pages_login'))
        
    try:
        groups = db.group_info.find()
        chips = db.chip_info.find()
        chip_info = {}
        for chip in chips:
            chip_info[chip["Chip_ID"]] = chip
        
        group_info = []
        for group in groups:
            group_info.append(group)
        print(group_info)
        return render_template('group-view.html', user=user, group_info=group_info, chip_info=chip_info)
    except:
        return render_template('error.html')  

@app.route('/bluetooth_devices', methods=['post','get'])
def bluetooth_devices():
    print(session)
    if request.method == 'POST':
        # get the number of nodes input
        decimal_input = request.form['decimal_input']
        
        #iterate through all the ports and identify the correct port, check for Captial 'C'=> could be /dev/ttyACM0 or /dev/ttyACM1
        for i in range(len(myports)):
            if (myports[i][0].find('C') != -1):
                path_input = myports[i][0]
                break
        #path_input = request.form['path_input']
        print("Device Connected is - ", path_input)
        command = ['python3', '/home/pi/nrf5sdkformeshv500src/scripts/interactive_pyaci/interactive_pyaci.py', '-d', path_input, '-n', decimal_input]

        try:
            # Execute the script with blocking call
            subprocess.run(command, check=True)
            print("Provisioning is successful")
            db.chip_info.delete_many({})
            print("Chip info cleaned")
            return redirect(url_for('pages_login'))
        except subprocess.CalledProcessError as e:
            return f"Provisioning failed: {e}"
    else:
        if "email" in session and session["email"]!="":
            user_found = records.find_one({"email": session["email"]})
            user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
            print(user)
            return render_template('bluetooth-devices.html', user=user)
        else:
            return redirect(url_for('pages_login'))
        


# Code for running the job immediately
def run_command(cmd_id):
    try:
        cmds_search = list(db.commands.find({"_id":cmd_id}))
        print(cmd_id)
        cmd = cmds_search[0]
        print(cmd)

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

        # TO DO: create the file    
        file_name = home_dir+'cmd_'+str(cmd_id)+'.txt'
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
        cmd_to_run = "python3 " + os.getcwd()+ "/scripts_to_execute_commands/interactive_pyaci/interactive_pyaci.py -d /dev/ttyACM0 < "+file_name
        os.system(cmd_to_run)

        # TO DO: delete the command*.txt files too
        #subprocess.run(["rm","-rf",file_name])
    except:
        return render_template('error.html')  

# TO DO: While scheduling the jobs itself create the commands.txt file
@app.route('/scheduled_jobs', methods=['post','get'])
def scheduled_jobs():
    message = ''
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    else:
        return redirect(url_for('pages_login'))
        
    # update the db and call the same 
    try:
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
                    print("Scheduling Immediately")
                    #TO DO: run_command()
                    run_command(cmd_id)
                    db.executed.insert_one(job_input)
                    recent_act = {}
                    recent_act["time"] = time_to_execute
                    recent_act["text"] = ""
                    if cmd_val == "1":
                        if chip_id is "":
                            recent_act["text"] = "Turned on LED 1 for Group: "+group_id 
                        elif group_id is "":
                            recent_act["text"] = "Turned on LED 1 for Chip: "+chip_id 
                        else:
                            recent_act["text"] = "Turned on LED 1 for Chip: "+chip_id + " and group: " +group_id
                    else:
                        if chip_id is "":
                            recent_act["text"] = "Turned off LED 1 for Group: "+group_id 
                        elif group_id is "":
                            recent_act["text"] = "Turned off LED 1 for Chip: "+chip_id 
                        else:
                            recent_act["text"] = "Turned off LED 1 for Chip: "+chip_id + " and group: " +group_id
                    db.recent_info.insert_one(recent_act)
            
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
                        print("Scheduling Immediately")
                        # TO DO: run_command()
                        run_command(cmd_id)
                        db.executed.insert_one(job_input)
                        recent_act = {}
                        recent_act["time"] = time_to_execute
                        recent_act["text"] = ""
                        if cmd_val == "1":
                            recent_act["text"] = "Turned on LED 1 for "+chip_id+" "+group_id               
                        else:
                            recent_act["text"] = "Turned off LED 1 for "+chip_id+" "+group_id
                        db.recent_info.insert_one(recent_act)
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
            if time_curr >= job["execution_time"]:
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
    except:
        return render_template('error.html', message="This functionality is disabled")        
    
@app.route('/logs', methods=['post','get'])
def logs():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    else:
        return redirect(url_for('pages_login'))
        
    try:
        logs = db.logs.find()
        return render_template('logs.html', user=user, logs = logs)
    except:
        return render_template('error.html')  

# handle individual command edit
@app.route('/command/<string:cmd_id>', methods=['GET','POST'])
def command(cmd_id):
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    else:
        return redirect(url_for('pages_login'))
        
    try:
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
            updated_job["execution_time"] = time_now

            # update the db: queue(update) and commands(replace)
            db.commands.replace_one({"_id":ObjectId(cmd_id)}, updated_cmd, upsert=True)
            db.queue_jobs.replace_one({"_id":ObjectId(cmd_id)}, updated_job, upsert=True)

            return redirect(url_for('commands'))


        print(cmd_id)
        commands = db.commands.find_one({"_id":ObjectId(cmd_id)})
        jobs = db.queue_jobs.find_one({"cmd_id":cmd_id})
        return render_template('edit-command.html', user=user, commands=commands, jobs=jobs)
    except:
        return render_template('error.html',message="Please re check the input")  

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
    else:
        return redirect(url_for('pages_login'))
        
    try:
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
            main_command["cmd_id"] = str(command["_id"])
            duration = datetime.strptime(job["execution_time"], fmt)-datetime.now()
            print(duration)
            main_command["time"], main_command["font"] = delta_to_string(duration)
            commands.append(main_command)

        return render_template('commands.html', user=user, commands=commands)
    except:
        return render_template('error.html', message="Command error please re-schedule")  

@app.route('/tables_general', methods=['post','get'])
def tables_general():
   return render_template('tables-general.html')

@app.route('/tables_data', methods=['post','get'])
def tables_data():
   return render_template('tables-data.htmll')

@app.route('/charts_chartjs', methods=['post','get'])
def charts_chartjs():
   return render_template('charts-chartjs.html')

@app.route('/charts_apexcharts', methods=['post','get'])
def charts_apexcharts():
   return render_template('charts-apexcharts.html')

@app.route('/charts_echarts', methods=['post','get'])
def charts_echarts():
   return render_template('charts-echarts.html')

@app.route('/icons_bootstrap', methods=['post','get'])
def icons_bootstrap():
   return render_template('icons-bootstrap.html')

@app.route('/icons_remix', methods=['post','get'])
def icons_remix():
   return render_template('icons-remix.html')

@app.route('/icons_boxicons', methods=['post','get'])
def icons_boxicons():
   return render_template('icons-boxicons.html')

if __name__ == '__main__':
    # running the python job_executor script endlessly
    #subprocess.Popen(
    #    ['/usr/bin/python3','/home/matsy007/Downloads/Mesh/BLE-Mesh-Project/Job_executor.py'],
    #    stdin=subprocess.DEVNULL,
    #    stdout = open('job_logs.out','a'),
    #    stderr = subprocess.STDOUT,
    #    start_new_session=True
    #)
    
    app.run(host="0.0.0.0", debug = True)