from crypt import methods
from flask import Flask, render_template, request, url_for, redirect, session
import pymongo, bcrypt, json, queue
from datetime import datetime
from datetime import timedelta
from bson import ObjectId
import subprocess, signal, os
from time import sleep

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
home_dir = '/home/pi/BLE/BLE-Mesh-Project/Commands/'
home_database_json = '/home/pi/Mesh_demo/nrf5sdkformeshv500src/scripts/interactive_pyaci/database/example_database.json'

##############################################################################
# Adding the interactive shell code here
import sys, json

if sys.version_info < (3, 5):
    print(("ERROR: To use {} you need at least Python 3.5.\n" +
           "You are currently using Python {}.{}").format(sys.argv[0], *sys.version_info))
    sys.exit(1)

import logging, time
import IPython
import os
import colorama

from argparse import ArgumentParser
import traitlets.config

from aci.aci_uart import Uart
from aci.aci_utils import STATUS_CODE_LUT
from aci.aci_config import ApplicationConfig
import aci.aci_cmd as cmd
import aci.aci_evt as evt

from mesh import access
from mesh.provisioning import Provisioner, Provisionee  # NOQA: ignore unused import
from mesh import types as mt                            # NOQA: ignore unused import
from mesh.database import MeshDB                        # NOQA: ignore unused import
from models.config import ConfigurationClient           # NOQA: ignore unused import
from models.generic_on_off import GenericOnOffClient    # NOQA: ignore unused import


LOG_DIR = os.path.join(os.path.dirname(sys.argv[0]), "log")

USAGE_STRING = \
    """
    {c_default}{c_text}To control your device, use {c_highlight}d[x]{c_text}, where x is the device index.
    Devices are indexed based on the order of the COM ports specified by the -d option.
    The first device, {c_highlight}d[0]{c_text}, can also be accessed using {c_highlight}device{c_text}.

    Type {c_highlight}d[x].{c_text} and hit tab to see the available methods.
""" # NOQA: Ignore long line
USAGE_STRING += colorama.Style.RESET_ALL

FILE_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s: %(message)s"
STREAM_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s: %(message)s"
COLOR_LIST = [colorama.Fore.MAGENTA, colorama.Fore.CYAN,
              colorama.Fore.GREEN, colorama.Fore.YELLOW,
              colorama.Fore.BLUE, colorama.Fore.RED]
COLOR_INDEX = 0


def configure_logger(device_name):
    global options
    global COLOR_INDEX

    logger = logging.getLogger(device_name)
    logger.setLevel(logging.DEBUG)

    stream_formatter = logging.Formatter(
        COLOR_LIST[COLOR_INDEX % len(COLOR_LIST)] + colorama.Style.BRIGHT
        + STREAM_LOG_FORMAT
        + colorama.Style.RESET_ALL)
    COLOR_INDEX = (COLOR_INDEX + 1) % len(COLOR_LIST)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(options.log_level)
    logger.addHandler(stream_handler)
    return logger


class Interactive(object):
    DEFAULT_APP_KEY = bytearray([0xAA] * 16)
    DEFAULT_SUBNET_KEY = bytearray([0xBB] * 16)
    DEFAULT_VIRTUAL_ADDRESS = bytearray([0xCC] * 16)
    DEFAULT_STATIC_AUTH_DATA = bytearray([0xDD] * 16)
    DEFAULT_LOCAL_UNICAST_ADDRESS_START = 0x0001
    CONFIG = ApplicationConfig(
        header_path=os.path.join(os.path.dirname(sys.argv[0]),
                                 ("../../examples/serial/include/"
                                  + "nrf_mesh_config_app.h")))
    PRINT_ALL_EVENTS = True

    def __init__(self, acidev):
        self.acidev = acidev
        self._event_filter = []
        self._event_filter_enabled = True
        self._other_events = []

        self.logger = configure_logger(self.acidev.device_name)
        self.send = self.acidev.write_aci_cmd

        # Increment the local unicast address range
        # for the next Interactive instance
        self.local_unicast_address_start = (
            self.DEFAULT_LOCAL_UNICAST_ADDRESS_START)
        Interactive.DEFAULT_LOCAL_UNICAST_ADDRESS_START += (
            self.CONFIG.ACCESS_ELEMENT_COUNT)

        self.access = access.Access(self, self.local_unicast_address_start,
                                    self.CONFIG.ACCESS_ELEMENT_COUNT)
        self.model_add = self.access.model_add

        # Adding the packet recipient will start dynamic behavior.
        # We add it after all the member variables has been defined
        self.acidev.add_packet_recipient(self.__event_handler)

    def close(self):
        self.acidev.stop()

    def events_get(self):
        return self._other_events

    def event_filter_add(self, event_filter):
        self._event_filter += event_filter

    def event_filter_disable(self):
        self._event_filter_enabled = False

    def event_filter_enable(self):
        self._event_filter_enabled = True

    def device_port_get(self):
        return self.acidev.serial.port

    def quick_setup(self):
        self.send(cmd.SubnetAdd(0, bytearray(self.DEFAULT_SUBNET_KEY)))
        self.send(cmd.AppkeyAdd(0, 0, bytearray(self.DEFAULT_APP_KEY)))
        self.send(cmd.AddrLocalUnicastSet(
            self.local_unicast_address_start,
            self.CONFIG.ACCESS_ELEMENT_COUNT))

    def __event_handler(self, event):
        if self._event_filter_enabled and event._opcode in self._event_filter:
            # Ignore event
            return
        if event._opcode == evt.Event.DEVICE_STARTED:
            self.logger.info("Device rebooted.")

        elif event._opcode == evt.Event.CMD_RSP:
            if event._data["status"] != 0:
                self.logger.error("{}: {}".format(
                    cmd.response_deserialize(event),
                    STATUS_CODE_LUT[event._data["status"]]["code"]))
            else:
                text = str(cmd.response_deserialize(event))
                if text == "None":
                    text = "Success"
                self.logger.info(text)
        else:
            if self.PRINT_ALL_EVENTS and event is not None:
                self.logger.info(str(event))
            else:
                self._other_events.append(event)


def start_ipython(options):
    colorama.init()
    comports = options.devices
    d = list()

    # Print out a mini intro to the interactive session --
    # Start with white and then magenta to keep the session white
    # (workaround for a bug in ipython)
    colors = {"c_default": colorama.Fore.WHITE + colorama.Style.BRIGHT,
              "c_highlight": colorama.Fore.YELLOW + colorama.Style.BRIGHT,
              "c_text": colorama.Fore.CYAN + colorama.Style.BRIGHT}

    print(USAGE_STRING.format(**colors))

    if not options.no_logfile and not os.path.exists(LOG_DIR):
        print("Creating log directory: {}".format(os.path.abspath(LOG_DIR)))
        os.mkdir(LOG_DIR)

    for dev_com in comports:
        d.append(Interactive(Uart(port=dev_com,
                                  baudrate=options.baudrate,
                                  device_name=dev_com.split("/")[-1])))

    device = d[0]
    send = device.acidev.write_aci_cmd  # NOQA: Ignore unused variable

    # Set iPython configuration
    ipython_config = traitlets.config.get_config()
    if options.no_logfile:
        ipython_config.TerminalInteractiveShell.logstart = False
        ipython_config.InteractiveShellApp.db_log_output = False
    else:
        dt = datetime.datetime()
        logfile = "{}/{}-{}-{}-{}_interactive_session.log".format(
            LOG_DIR, dt.yy(), dt.dayOfYear(), dt.hour(), dt.minute())

        ipython_config.TerminalInteractiveShell.logstart = True
        ipython_config.InteractiveShellApp.db_log_output = True
        ipython_config.TerminalInteractiveShell.logfile = logfile

    ipython_config.TerminalInteractiveShell.confirm_exit = False
    ipython_config.InteractiveShellApp.multiline_history = True
    ipython_config.InteractiveShellApp.log_level = logging.DEBUG

    IPython.embed(config=ipython_config)
    for dev in d:
        dev.close()
    raise SystemExit(0)

def script_main_func():
    comports = options.devices
    global d
    global device
    global cc
    global mesh_db

    d = list()
    for dev_com in comports:
        d.append(Interactive(Uart(port=dev_com,baudrate=options.baudrate,device_name=dev_com.split("/")[-1])))

    device = d[0]
    mesh_db = MeshDB('/home/pi/Mesh_demo/nrf5sdkformeshv500src/scripts/interactive_pyaci/database/example_database.json')
    

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

@app.route('/pages_blank')
def pages_blank():
   return render_template('pages-blank.html')

# Code for running the job immediately
def run_group_change(chip_id, old_group_id, new_group_id):
    chips_search = list(db.chip_info.find({"Chip_ID":chip_id}))
    chip = chips_search[0]
        
    device_key = chip["Dev_key_handle"]
    unicast_address_id = chip["Unicast_address_index"]
    address_handle = chip["Address_handle"]


    # TO DO: create the file    
    file_name = home_dir+'cmd_'+str(chip_id)+'_'+str(old_group_id)+'_'+str(new_group_id)+'.txt'
    #with open(file_name,"a") as cmd_file:
    #    cmd_file.write("db = MeshDB('{0}')\n".format(home_database_json))
    #    cmd_file.write('cc = ConfigurationClient(db)\n')
    #    cmd_file.write('cc.force_segmented = True\n')
    #    cmd_file.write('device.model_add(cc)\n')
    #    cmd_file.write('cc.publish_set({0}, {1})\n'.format(device_key, address_handle))
    #    cmd_file.write('cc.model_app_unbind(db.nodes[{0}].unicast_address, {1}, mt.ModelId(0x1000))\n'.format(unicast_address, old_group_id))
    #    cmd_file.write('cc.model_app_bind(db.nodes[{0}].unicast_address, {1}, mt.ModelId(0x1000))\n'.format(unicast_address, new_group_id))
    #   cmd_file.write('cc.model_subscription_add(db.nodes[{0}].unicast_address, 0xc001, mt.ModelId(0x1000))\n'.format(unicast_address))

    # TO DO: run the interactive python shell script system command
    print("Changing the group from: {0} to {1} and file is: {2} ".format(old_group_id, new_group_id, file_name))

    #subprocess.run(["python3", "interactive_pyaci.py","-d", "COM8", "-l","3" ,"<",file_name])
    #os.system("python3 /home/pi/Mesh_demo/nrf5sdkformeshv500src/scripts/interactive_pyaci/interactive_pyaci.py -d /dev/ttyACM4 < "+file_name)

    # Let's directly execute the APIS
    print(mesh_db.nodes[27])
    cc = ConfigurationClient(mesh_db)
    cc.force_segmented = True
    device.model_add(cc)
    print("########################################################")
    cc.publish_set(35, 28)
    print("########################################################")
    cc.model_app_unbind(mesh_db.nodes[int(unicast_address_id)].unicast_address, int(old_group_id), mt.ModelId(0x1000))
    time.sleep(12)
    print("########################################################")
    out = json.loads(json.dumps(mesh_db.nodes[27]))
    elems = out["elements"][0]["models"]
    for model in elems:
        if model["modelId"] == "1000":
            mod = model["bind"]
            if old_group_id in mod:
                cc.model_app_unbind(mesh_db.nodes[int(unicast_address_id)].unicast_address, int(old_group_id), mt.ModelId(0x1000))
    cc.model_app_bind(mesh_db.nodes[int(unicast_address_id)].unicast_address, int(new_group_id), mt.ModelId(0x1000))
    out = json.loads(json.dumps(mesh_db.nodes[27]))
    elems = out["elements"][0]["models"]
    for model in elems:
        if model["modelId"] == "1000":
            mod = model["bind"]
            if new_group_id not in mod:
                cc.model_app_bind(mesh_db.nodes[int(unicast_address_id)].unicast_address, int(new_group_id), mt.ModelId(0x1000))

    print("########################################################")
    for dev in d:
        dev.close()

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
    chips = db.chip_info.find()
    chip_info = {}
    for chip in chips:
        chip_info[chip["Chip_ID"]] = chip
    
    group_info = []
    for group in groups:
        group_info.append(group)
    print(group_info)
    return render_template('group-view.html', user=user, group_info=group_info, chip_info=chip_info)

@app.route('/bluetooth_devices')
def bluetooth_devices():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('bluetooth-devices.html', user=user)

# Code for running the job immediately
def run_command(cmd_id):
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
    os.system("python3 /home/pi/Mesh_demo/nrf5sdkformeshv500src/scripts/interactive_pyaci/interactive_pyaci.py -d /dev/ttyACM4 < "+file_name)

    # TO DO: delete the command*.txt files too
    #subprocess.run(["rm","-rf",file_name])

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
                print("Scheduling Immediately")
                #TO DO: run_command()
                run_command(cmd_id)
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
                    print("Scheduling Immediately")
                    # TO DO: run_command()
                    run_command(cmd_id)
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
        updated_job["execution_time"] = time_now

        # update the db: queue(update) and commands(replace)
        db.commands.replace_one({"_id":ObjectId(cmd_id)}, updated_cmd, upsert=True)
        db.queue_jobs.replace_one({"_id":ObjectId(cmd_id)}, updated_job, upsert=True)

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
        main_command["cmd_id"] = str(command["_id"])
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

@app.route('/icons_bootstrap')#print("####")
def icons_bootstrap():
   return render_template('icons-bootstrap.html')

@app.route('/icons_remix')
def icons_remix():
   return render_template('icons-remix.html')

@app.route('/icons_boxicons')
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
    parser = ArgumentParser(
        description="nRF5 SDK for Mesh Interactive PyACI")
    parser.add_argument("-d", "--device",
                        dest="devices",
                        nargs="+",
                        required=True,
                        help=("Device Communication port, e.g., COM216 or "
                              + "/dev/ttyACM0. You may connect to multiple "
                              + "devices. Separate devices by spaces, e.g., "
                              + "\"-d COM123 COM234\""))
    parser.add_argument("-b", "--baudrate",
                        dest="baudrate",
                        required=False,
                        default='115200',
                        help="Baud rate. Default: 115200")
    parser.add_argument("--no-logfile",
                        dest="no_logfile",
                        action="store_true",
                        required=False,
                        default=False,
                        help="Disables logging to file.")
    parser.add_argument("-l", "--log-level",
                        dest="log_level",
                        type=int,
                        required=False,
                        default=3,
                        help=("Set default logging level: "
                              + "1=Errors only, 2=Warnings, 3=Info, 4=Debug"))
    options = parser.parse_args()

    if options.log_level == 1:
        options.log_level = logging.ERROR
    elif options.log_level == 2:
        options.log_level = logging.WARNING
    elif options.log_level == 3:
        options.log_level = logging.INFO
    else:
        options.log_level = logging.DEBUG
    script_main_func()
    app.run(host="0.0.0.0", debug = True)
