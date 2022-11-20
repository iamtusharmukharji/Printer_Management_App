#! usr/bin/env python3

from flask import Flask as fk
import logging
import os
from flask import redirect, url_for, request, render_template, flash
import sqlite3
from time import sleep
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler as BS
from waitress import serve
from AppFunc import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user,UserMixin,LoginManager



query="""INSERT INTO PRINTER_CONFIG(NAME,IP,BRAND,MODEL,TYPE,SERIAL,REGION,LOCATION,LOC_CODE,DEPT,COST_CENTRE,STATUS) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);"""

#database_file=file_path = os.path.abspath(os.getcwd())+"\pmt_prod.db"




app= fk(__name__)
app.secret_key = "abc"  

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pmt_prod.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

db = SQLAlchemy(app)

class printer_db(db.Model):

        serial = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)

        ip = db.Column(db.String(80),nullable=False)
        
        name = db.Column(db.String(80),nullable=False)

        brand = db.Column(db.String(80),nullable=False)
        model = db.Column(db.String(80),nullable=False)
        printer_type = db.Column(db.String(80),nullable=False)
        region = db.Column(db.String(80),nullable=False)
        state = db.Column(db.String(80),nullable=False)
        location = db.Column(db.String(80),nullable=False)
        loc_code = db.Column(db.Integer,nullable=False)
        dept = db.Column(db.String(80),nullable=False)
        cost_center = db.Column(db.Integer,nullable=False)
        status = db.Column(db.String(80),nullable=False)
        toner=db.Column(db.String(80),nullable=True)
        page=db.Column(db.String(80),nullable=True)
        sync=db.Column(db.DATETIME,nullable=True)
        curr_stat=db.Column(db.String(80),nullable=True)


        def __init__(self,serial,ip,name,brand,model,printer_type,region,state,location,loc_code,dept,cost_center,status,toner,page,sync,curr_stat):

                self.serial= serial
                self.ip= ip
                self.name= name
                self.brand= brand
                self.model= model
                self.printer_type= printer_type
                self.region= region
                self.state=state
                self.location= location
                self.loc_code= loc_code
                self.dept= dept
                self.cost_center= cost_center
                self.status= status
                self.toner=toner
                self.page=page
                self.sync=sync
                self.curr_stat=curr_stat

class LocationConfig_DB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(80),nullable=False)
    state = db.Column(db.String(80),nullable=False)
    location = db.Column(db.String(80),nullable=False)
    loc_code = db.Column(db.Integer,nullable=False)
    entity = db.Column(db.String(80),nullable=False)
    cost_center = db.Column(db.Integer,nullable=False)
    
    def __init__(self,region,state,location,loc_code,entity,cost_center):
        self.region=region
        self.state=state
        self.location=location
        self.loc_code=loc_code
        self.entity=entity
        self.cost_center=cost_center

class Users(db.Model,UserMixin):
    UserID=db.Column(db.String(80), primary_key=True)
    Name=db.Column(db.String(80), nullable=False)
    Password=db.Column(db.String(1000),nullable=False)
    Rights=db.Column(db.Integer,nullable=False)

    def get_id(self):
        return (self.UserID)

class AuthUser(db.Model):
    UserID=db.Column(db.String(80), primary_key=True)
    Name=db.Column(db.String(80), nullable=False)
    OTP=db.Column(db.Integer,nullable=True)
    Stamp=db.Column(db.DateTime,nullable=True)

    def __init__(self,UserID,Name,OTP,Stamp):
        self.UserID=UserID
        self.Name=Name
        self.OTP=OTP
        self.Stamp=Stamp

##################################################################################################

def refresh():
    import sqlalchemy as sqli
    engine = sqli.create_engine(r'sqlite:///pmt_prod.db')
    connection = engine.connect()
    #tables=engine.table_names() # for showing tables
    meta = sqli.MetaData()
    data_table = sqli.Table('printer_db', meta, autoload=True, autoload_with=engine)# For printer_db table
    printer_info=connection.execute(sqli.select([data_table]))
    data_1 = printer_info.fetchall()
    ips=[]
    serl=[]
    for i in range(len(data_1)):
        if data_1[i][12]=='Deployed':
            ips.append(data_1[i][1])
            serl.append(data_1[i][0]) 
    club=dict(zip(serl,ips))
    #print(club)
    print('\n*************REFRESH FUNCTION CALLED***************')
    for ip in club:
        func=get_details(club[ip])
        if func==False:
            print('Connection Error for',ip,club[ip])
            update= printer_db.query.get(ip)
            if update.curr_stat=='Unsynced':
                pass
            else:
                update.curr_stat='Offline'
            
        else:
            
            update= printer_db.query.get(ip)
            update.toner=func[0]
            update.page=func[1]
            update.sync=func[2]
            update.serial=func[3]
            update.printer_type=func[4]
            update.model=func[5]
            update.brand=func[6]
            update.curr_stat='Online'
            db.session.commit()
            print(ip,club[ip],'Data Syncing Done!')
                
    print("\n###########COMPLETE##########")
auto_ref=BS(daemon=True)
auto_ref.add_job(refresh,'interval',minutes=360)
auto_ref.start()
##################################################################################################


@login_manager.user_loader
def load_user(id):
    return Users.query.get(id)

############################ Super Users ####################################
@app.before_first_request
def before_first_request():
    log_level = logging.INFO
 
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)
 
    root = os.path.dirname(os.path.abspath(__file__))
    logdir = os.path.join(root, 'logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    log_file = os.path.join(logdir, 'app.log')
    handler = logging.FileHandler(log_file)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)
 
    app.logger.setLevel(log_level)

@app.route("/admin",methods=["GET","POST"])
def Superlogin():
    if request.method=='POST':
        usr=request.form['username']
        pwd=request.form['password']

        user = Users.query.filter_by(UserID=usr).first()
        if user:
            if user.Rights==2 and check_password_hash(user.Password, pwd):
                return SU_InternalAuth(user.UserID)
                #login_user(user, remember=True)
                #return redirect(url_for('SU_home',id=user.UserID))
            else:
                ALERT="Acess Denied!"
                return render_template('SuperLogin.html',ALERT=ALERT)

        else:
            ALERT="User does not Exist!"
            return render_template('SuperLogin.html',ALERT=ALERT)



    return render_template("SuperLogin.html")


def SU_InternalAuth(id):
    from datetime import datetime
 
    authUser = AuthUser.query.filter_by(UserID=id).first()
    name = authUser.Name
    otp = getOTP()
    mailOTP(name,id,otp)
    authUser.OTP=otp
    authUser.Stamp= datetime.now()
    db.session.commit()

    return render_template('SU_userAuth.html',user=authUser)

@app.route('/authenticateadmin/<id>',methods=['POST'])
def SU_Authenticate(id):
    if request.method=='POST':
        otp = int(request.form.get('otp'))
        checkUser = AuthUser.query.filter_by(UserID=id).first()
        if otp==checkUser.OTP:
            user = Users.query.filter_by(UserID=id).first()
            login_user(user, remember=True)
            stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
            app.logger.info(f'{current_user.Name} logged In in PMT UMP {stamp}')
            return redirect(url_for('SU_home',id=user.UserID))
        else:
            ALERT="OTP does not matched!"
            return render_template('SU_userAuth.html',user=checkUser,ALERT=ALERT)


@app.route("/admin/<id>")
@login_required
def SU_home(id):
    return render_template('UserManagerHome.html',name=current_user.Name)


@app.route("/cSUh#$12rd", methods=["POST"])
@login_required
def SU_changePassword():
    if request.method=='POST':
        currUser=Users.query.filter_by(UserID=current_user.UserID).first()
        old=request.form.get('oldPass')
        print(old)
        if check_password_hash(currUser.Password, old):
            newPass=request.form.get('newPass')
            confPass=request.form.get('confPass')
            if newPass==confPass:
                currUser.Password= generate_password_hash(newPass, method='sha256')
                db.session.commit()
                stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
                app.logger.info(f'{current_user.Name} changed password {stamp}')
            else:
                return render_template('SU_Error.html',user=current_user,info="Password does not matched!" )
        else:
            return render_template('SU_Error.html',user=current_user,info= "Old password does not matched!" )

        return render_template('SU_sucess.html',user=current_user,info= "Password changed sucessfully!" )
    else:
        return redirect(url_for('SU_home',id=current_user.UserID))


@app.route("/admin/logout")
@login_required
def SU_logout():
    stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
    app.logger.info(f'{current_user.Name} logged Out from PMT UMP {stamp}')
    logout_user()
    
    return redirect(url_for('Superlogin'))


@app.route("/admin/createUser")
@login_required
def SU_createUser():
    return render_template('SUCreateUser.html',name=current_user.Name,id=current_user.UserID)


@app.route("/admin/createUser/submit", methods=["POST"])
@login_required
def SU_userSubmit():
    if request.method=="POST":
        name=request.form.get('name')
        id=request.form.get('email')
        right=int(request.form.get('rights'))
        pwd=getPass()
        try:
            
            newUser= Users(UserID=id, Name=name, Password=generate_password_hash(pwd, method='sha256'), Rights=right)
            
            db.session.add(newUser)
            db.session.commit()
            newUserAuth= AuthUser(id,name,None,None)
            db.session.add(newUserAuth)
            db.session.commit()
            mailPassword(name,id,pwd)
            stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
            app.logger.info(f'New user [UserName: {id}, Name: {name}] is created by {current_user.Name} {stamp}')
            l=[name,id,right,pwd]
            print(l)
            redirect(url_for('SU_createUser'))
        except:
            info="{} is already exist!".format(id)
            return render_template('SU_Error.html',name=current_user.Name,id=current_user.UserID,info=info)
    return redirect(url_for('SU_createUser'))

@app.route("/admin/UserInfo")
@login_required
def SU_userInfo():
    data=Users.query.all()
    url=getUrl()
    return render_template('SU_userInfo.html',user=current_user,data=data,safeUrl=url)

@app.route('/admin/UserInfo/update',methods=["POST"])
@login_required
def SU_edit():
    if request.method=='POST':
        id=request.form.get('id')
        newRight=request.form.get('right')
        user=Users.query.get(id)
        user.Rights=int(newRight)
        db.session.commit()
        stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
        app.logger.info(f'Rights of {id} has been changed to {newRight} by {current_user.Name} {stamp}')
        print('updated rights sucessfully')
        return redirect(url_for('SU_userInfo'))


@app.route('/admin/UserInfo/delete/<id>')
@login_required
def SU_delete(id):
    delUser=Users.query.get(id)
    db.session.delete(delUser)
    db.session.commit()
    delAuth=AuthUser.query.get(id)
    db.session.delete(delAuth)
    db.session.commit()
    stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
    app.logger.info(f'{id} is deleted by {current_user.Name} {stamp}')
    print('Delete User sucessfully')
    return redirect(url_for('SU_userInfo'))

@app.route('/admin/UserInfo/reset/<id>')
@login_required
def SU_reset(id):
    ResetUser=Users.query.get(id)
    pwd=getPass()
    resetPassword(ResetUser.Name,id,pwd)
    ResetUser.Password=generate_password_hash(pwd,method='sha256')
    db.session.commit()
    stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
    app.logger.info(f'Password has been reset for {id} by {current_user.Name} {stamp}')

    print('Password Reset sucessful')
    return redirect(url_for('SU_userInfo'))




############################ Standard Users ####################################

@app.route("/",methods=["GET","POST"])
def login():
    if request.method == 'POST':
        usr=request.form['username']
        pwd=request.form['password']
        user=Users.query.filter_by(UserID=usr).first()
        
        if user:
            if check_password_hash(user.Password, pwd):
                return InternalAuth(user.UserID)
                #login_user(user, remember=True)
                #return redirect(url_for('dashBoard',id=user.UserID))
            else:
                ALERT="Acess Denied!"
                return render_template('login.html',ALERT=ALERT)
        
        else:
            ALERT="User does not exist!!"
            return render_template('login.html',ALERT=ALERT)
        

    return render_template("login.html")

def InternalAuth(id):
    from datetime import datetime
 
    authUser = AuthUser.query.filter_by(UserID=id).first()
    name = authUser.Name
    otp = getOTP()
    mailOTP(name,id,otp)
    authUser.OTP=otp
    authUser.Stamp= datetime.now()
    db.session.commit()

    return render_template('UserAuth.html',user=authUser)

@app.route('/authenticate/<id>',methods=['POST'])
def Authenticate(id):
    if request.method=='POST':
        otp = int(request.form.get('otp'))
        checkUser = AuthUser.query.filter_by(UserID=id).first()
        if otp==checkUser.OTP:
            user = Users.query.filter_by(UserID=id).first()
            login_user(user, remember=True)
            stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
            app.logger.info(f'{current_user.Name} logged In {stamp}')
            return redirect(url_for('dashBoard',id=user.UserID))
        else:
            ALERT="OTP does not matched!"
            return render_template('UserAuth.html',user=checkUser,ALERT=ALERT)

@app.route('/home/<id>')
@login_required
def dashBoard(id):
    return render_template('dash_board ADMIN.html',usr=current_user.Name, user=current_user)

@app.route("/ch#$12rd", methods=["POST"])
@login_required
def changePassword():
    if request.method=='POST':
        currUser=Users.query.filter_by(UserID=current_user.UserID).first()
        old=request.form.get('oldPass')
        print(old)
        if check_password_hash(currUser.Password, old):
            newPass=request.form.get('newPass')
            confPass=request.form.get('confPass')
            if newPass==confPass:
                currUser.Password= generate_password_hash(newPass, method='sha256')
                db.session.commit()
                stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
                app.logger.info(f'{current_user.Name} changed password {stamp}')
            else:
                return render_template('ErrorADMIN.html',info="Password does not matched!" )
        else:
            return render_template('ErrorADMIN.html',info= "Old password does not matched!" )

        return render_template('sucessADMIN.html',info= "Password changed sucessfully!" )
    else:
        return redirect(url_for('homeDashADMIN'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
    app.logger.info(f'{current_user.Name} Logged Out {stamp}')
    return redirect(url_for('login'))

@app.route("/home/report")
@login_required
def reportsADMIN():
        report=printer_db.query.all()
        return render_template('report_ADMIN.html', data=report,user=current_user)

@app.route("/home/report/sync")
@login_required
def syncADMIN():
        
        try:
            refresh()
            stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
            app.logger.info(f'{current_user.Name} called Refresh function {stamp}')
            report=printer_db.query.all()
            return render_template('report_ADMIN.html', data=report)
        except Exception as e:
            e=str(e)
            print(e)
            e=e[147:-2]
            s=e.split(',')
            
            print(s[-1])
            return render_template('ErrorADMIN.html',info='Duplicate data found in database'+s[-1]+'!')

@app.route("/home/submit", methods=['POST'])
@login_required
def db_connectionADMIN():
    from datetime import datetime
 
    try:
        if request.method == 'POST':
            
                serial = request.form['serial']
                serial=serial.upper()
                ip = request.form['ip']
                name = request.form['printerName']
                loc_code = request.form['locationcode']
                dept = request.form['department']
                status = request.form['status']
                
                data=db.session.query(LocationConfig_DB).filter((LocationConfig_DB.loc_code==loc_code) & (LocationConfig_DB.entity==dept)).all()
                Loc_Data=[]
                for i in data:
                    Loc_Data.append(i)
                if len(Loc_Data)==0:
                    return render_template('ErrorADMIN.html',info= 'Location not configured in Database!' )

                val=Loc_Data[0]
                
                insert_data= printer_db(serial,ip,name,'Not Synced','Not Synced','Not Synced',val.region,val.state,val.location,loc_code,dept,val.cost_center,status,"Not Synced","Not Synced",datetime.now().replace(microsecond=0),"Unsynced")
                

                db.session.add(insert_data)
                db.session.commit()
                stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
                app.logger.info(f'{current_user.Name} configured a new printer [{serial}, {ip}, {loc_code}, {status}, {dept}] {stamp}')
                
                print("Data added in database!")
        
                return render_template('sucessADMIN.html',info='Printer has been configured in Database')

    
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print (message)
        stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
        app.logger.error(f'Error: {message}  User: {current_user.Name}  {stamp}')
                
        
        return render_template('ErrorADMIN.html',info= serial+' is already configured in Database' )


@app.route("/home/dashboard/makeChanges")
@login_required
def makeChangesADMIN():
        
    all_data = printer_db.query.all()
        
    return render_template("make_changesADMIN.html",data=all_data,user=current_user)


@app.route("/home/dashboard/makeChanges/update",methods=['POST'])
@login_required
def UpdateADMIN():
    try:

        if (request.method == 'POST'):
            serl=request.form.get('serial_no')
            update= printer_db.query.get(serl)#update in printer table
            update.name = request.form['name']
            update.ip = request.form['ip']
            entity= request.form['dept']
            L_Code= request.form['loc_code']
            data=db.session.query(LocationConfig_DB).filter((LocationConfig_DB.loc_code==L_Code) & (LocationConfig_DB.entity==entity)).all()
            Update_data=[]
            for i in data:
                Update_data.append(i)
            Updates=Update_data[0]
            
            update.dept = Updates.entity
            update.loc_code = Updates.loc_code
            update.region = Updates.region
            update.state = Updates.state
            update.location = Updates.location
            update.cost_center = Updates.cost_center
            update.status = request.form['status']
            
            db.session.commit()
            stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
            app.logger.info(f'{current_user.Name} Updated printer[Serial No.: {serl}] {stamp}')
                
            
            print("Database Updated Sucessfully!")
            return redirect(url_for('makeChangesADMIN'))
    except Exception as e:
        stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
        app.logger.error(f'Error: {e} User: {current_user.Name} {stamp}')
                
        return render_template('ErrorADMIN.html',info= "Invalid Location and Entity" )


@app.route('/home/dashboard/makeChanges/delete/<serial>')
@login_required
def delete(serial):
    printer_data = printer_db.query.get(serial)
    db.session.delete(printer_data)
    
    db.session.commit()
    stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
    app.logger.info(f'{current_user.Name} deleted printer[Serial No.: {serial}] {stamp}')
    print("Data deleted Sucessfully!")
    #flash("Employee Deleted Successfully")
 
    return redirect(url_for('makeChangesADMIN'))



@app.route("/home/dashboard")
@login_required
def homeDashADMIN():
    return render_template('dash_board ADMIN.html',usr=current_user.Name, user=current_user)


@app.route("/home/admin/config/")
@login_required
def config_printerADMIN():
    return render_template('configure ADMIN.html')


@app.route("/home/dashboard/zonewise")
@login_required
def zonewiseADMIN():
    return render_template("zonewise ADMIN.html")


@app.route('/home/dashborad/zonewise/east_report')
@login_required
def east_reportADMIN():
    data=db.session.query(printer_db).filter((printer_db.region=='East I')|(printer_db.region=='East II')).all()
    return render_template('commonReportADMIN.html',data=data)


@app.route('/home/dashborad/zonewise/west_report')
@login_required
def west_reportADMIN():
    data=db.session.query(printer_db).filter(printer_db.region=='West').all()
    return render_template('commonReportADMIN.html',data=data)


@app.route('/home/dashborad/zonewise/north_report')
@login_required
def north_reportADMIN():
    data=db.session.query(printer_db).filter(printer_db.region=='North').all()
    return render_template('commonReportADMIN.html',data=data)


@app.route('/home/dashborad/zonewise/south_report')
@login_required
def south_reportADMIN():
    data=db.session.query(printer_db).filter(printer_db.region=='South').all()
    return render_template('commonReportADMIN.html',data=data)


@app.route("/home/dashboard/loc_config")
@login_required
def makewiseADMIN():

    return render_template("makewise ADMIN.html")


#LOCATION REGISTRATION
@app.route("/home/dashboard/submit", methods=['POST'])
@login_required
def loc_configure():
    try:
        if request.method == 'POST':
                
                region = request.form['region']
                state = request.form['state']
                entity = request.form['entity']
                location = request.form['location']
                loc_code = request.form['locationcode']
                cost_center = request.form['cost_center']
                

                insert_data= LocationConfig_DB(region,state,location,loc_code,entity,cost_center)
                

                db.session.add(insert_data)
                db.session.commit()
                stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
                app.logger.info(f'{current_user.Name} configured new location [{region},{state},{location},{loc_code},{entity},{cost_center}] {stamp}')
                
                print("New Location Add!")
        
                return render_template('sucessADMIN.html',info='Loacation & Cost Code added sucessfully!')

    
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print (message)
        stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
        app.logger.error(f'Error:{message} User:{current_user.Name} {stamp}')
                
        
        return render_template('ErrorADMIN.html',info= 'Some Error occured!' )


@app.route("/home/dashboard/machinestatus")
@login_required
def location_detailsADMIN():
    loc_details=LocationConfig_DB.query.all()
    return render_template("LocTable_ADMIN.html",data=loc_details,user=current_user)

@app.route("/home/dashboard/machinestatus/update=<id>",methods=['POST'])
@login_required
def location_edit(id):
    if request.method=='POST':
        loc=LocationConfig_DB.query.get(id)
        prevLoc=[loc.region, loc.state, loc.location, loc.entity, loc.loc_code, loc.cost_center]
        loc.region=request.form.get('region')
        loc.state=request.form.get('state')
        loc.location=request.form.get('location')
        loc.entity=request.form.get('entity')
        loc.loc_code=int(request.form.get('loc_code'))
        loc.cost_center=int(request.form.get('cc'))
        db.session.commit()
        changedLoc=[loc.region, loc.state, loc.location, loc.entity, loc.loc_code, loc.cost_center]
        stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
        app.logger.info(f'{current_user.Name} changed/edited loation {prevLoc} to {changedLoc} {stamp}')
                
        return redirect(url_for('location_detailsADMIN'))

@app.route("/home/dashboard/machinestatus/delete=<id>")
@login_required
def location_delete(id):
    loc=LocationConfig_DB.query.get(id)
    prevLoc=[loc.region, loc.state, loc.location, loc.entity, loc.loc_code, loc.cost_center]
    db.session.delete(loc)
    db.session.commit()
    stamp=datetime.now().strftime('%d-%b-%y | %H:%M:%S' )
    app.logger.info(f'{current_user.Name} deleted location {prevLoc} {stamp}')
    return redirect(url_for('location_detailsADMIN'))



@app.route("/home/dashboard/colourprinters")
@login_required
def colourADMIN():
    return render_template("colour ADMIN.html")


@app.route("/home/dashboard/monochrome")
@login_required
def monochromeADMIN():
    return render_template("monochrome ADMIN.html")


@app.route('/home/dashboard/filter', methods=['POST'])
@login_required
def filterADMIN():
    string=make_cap(request.form['search'])
    data=db.session.query(printer_db).filter((printer_db.loc_code==string)|(printer_db.state==string)|(printer_db.ip==string)|(printer_db.serial==string)|(printer_db.brand==string)|(printer_db.cost_center==string)|(printer_db.status==string)|(printer_db.dept==string)).all()
    return render_template('commonReportADMIN.html',data=data)



if __name__ == "__main__":

    app.run(debug=True)
    #serve(app,host="172.20.35.243",port=5000)
        
