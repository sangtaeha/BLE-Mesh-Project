from crypt import methods
import queue
from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
import bcrypt

app = Flask(__name__)
app.secret_key = "testing"
client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
db = client.get_database('total_records')
records = db.register
executed_jobs = db.executed     # only contains job id's, start time, end time, interval
queue_jobs = db.queue           # contains job id, start time, end time, interval
commands = db.commands          # contains job id, cmd id, f, n, p, chipd id, group id

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
   return render_template('pages-error-404.html')

@app.route('/pages_blank')
def pages_blank():
   return render_template('pages-blank.html')

@app.route('/components')
def components():
    message=''
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('components.html', user=user)
   
@app.route('/group_view')
def group_view():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('group-view.html', user=user)

@app.route('/bluetooth_devices')
def bluetooth_devices():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('bluetooth-devices.html', user=user)

@app.route('/scheduled_jobs', methods=['post','get'])
def scheduled_jobs():
    message = ''
    print(session)
    print("Clicked on the submit button"+str(request))
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    
    # update the db and call the same template
    if request.method == "POST":
        chip_id = request.form.get("chipid")
        group_id = request.form.get("groupid")
        cmd_id = request.form.get("cmdid")
        frequency = request.form.get("frequency")
        width = request.form.get("width")
        number = request.form.get("number")
        time_now = request.form.get("timenow")
        start_time = request.form.get("starttime")
        end_time = request.form.get("endtime")
        interval = request.form.get("interval")

        print("start_time: "+start_time)
        print("end_time: "+end_time)
        print("time_now: "+time_now)
        print("interval: "+interval)
        print("chip_id: "+chip_id)

        # if job is to be run now update the executed jobs
        time_to_execute = start_time
        job_input = {'cmd_id': cmd_id, 'execution_time':time_to_execute}
        cmd_input = {'cmd_id':cmd_id, 'chip_id':chip_id, 'group_id':group_id, 'frequency' :frequency, 'width':width, number:'number'}
        print("Inserting into job db: "+str(job_input))
        print("Inserting into cmd db: "+str(cmd_input))
        db.commands.insert_one(cmd_input)
        if interval is "":
            db.executed.insert_one(job_input)

        # else add to the job queue 
        else:
            db.queue .insert_one(job_input)

    jobs = db.executed.aggregate([
                { "$sort": {"time_to_execute": 1}},
                { "$limit": 100} 
                ])
    executedjobs = jobs
    print("\nExecuted Jobs are: \n")
    for elem in executedjobs:
        print(elem)
    jobs = db.queue .aggregate([
            { "$sort": {"time_to_execute": 1}},
            { "$limit": 1} 
        ])
    jobsqueue = jobs
    print("\n Queue Jobs are: \n")
    for elem in jobsqueue:
        print(elem)
    return render_template('scheduled-jobs.html', user=user, executed=executedjobs, queuejobs=jobsqueue)
    
@app.route('/logs')
def logs():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('logs.html', user=user)

@app.route('/commands')
def commands():
    print(session)
    if "email" in session and session["email"]!="":
        user_found = records.find_one({"email": session["email"]})
        user = {'name': user_found["name"], 'email': user_found["email"], 'password': user_found["password"], 'fullname': user_found["fullname"], 'country': user_found["country"], 'address':user_found["address"], 'phone':user_found["phone"] }
        print(user)
    return render_template('commands.html', user=user)

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
   app.run(debug = True)