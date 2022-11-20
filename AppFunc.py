import subprocess
import shlex
import random
import string
from datetime import datetime

def getPercent(ip):
    total=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.43.11.1.1.8.1.1")
    res=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.43.11.1.1.9.1.1")
    total=subprocess.Popen(total,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    res=subprocess.Popen(res,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    stdout_total,stderr_total = total.communicate()
    stdout_res,stderr_res = res.communicate()
    
    total=stdout_total.split()[-1].decode('utf-8')
    res=stdout_res.split()[-1].decode('utf-8')
    percentage=int((int(res)/int(total))*100)
    
    return percentage

def get_details(ip):
    from datetime import datetime
    page_com=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.43.10.2.1.4.1.1")
    ser=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.43.5.1.1.17.1")
    type=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.43.12.1.1.4.1.2")
    mod=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.25.3.2.1.3.1")
    make=shlex.split("snmpwalk -v1 -c public "+ip+" iso.3.6.1.2.1.1.1.0")

    
    


    page=subprocess.Popen(page_com,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    serl=subprocess.Popen(ser,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    Ptype=subprocess.Popen(type,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    Model=subprocess.Popen(mod,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    Brand=subprocess.Popen(make,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    
    stdout_page,stderr_page = page.communicate()
    stdout_serl,stderr_serl = serl.communicate()
    stdout_Ptype,stderr_Ptype = Ptype.communicate()
    stdout_Model,stderr_Model = Model.communicate()
    stdout_Brand,stderr_Brand = Brand.communicate()

    page
    serl
    Ptype

    pageOut=stdout_page.split()[-1].decode('utf-8')
    SN=stdout_serl.split()
    Ptyp=stdout_Ptype.split()
    P_Model=stdout_Model.split()
    P_Brand=stdout_Brand.split()

    #Decoding serial number from Byte to String
    SerNum=SN[-1].decode('utf-8')[1:-1]

    #Logic for returning PrinterType(Colour/Monochrome)
    PrinterType='Monochrome'
    if len(Ptyp)>0:
        PrinterType='Colour'

    #Method for returning Printer's Model
    PrinterModel=''
    for i in P_Model[3:]:
        i=i.decode('utf-8')
        PrinterModel+=i+'_'
    PrinterModel=PrinterModel[1:-2]

    P_Brand=P_Brand[3].decode('utf-8')[1:].upper()

    try:
        page_count=int(pageOut)
        #print("Toner Level:",val_f,"%")
        #print("Page Count:",page_count,"\n")
        lev=str(getPercent(ip))+"%"
        DT = datetime.now().replace(microsecond=0)
        l1=[lev,page_count,DT,SerNum,PrinterType,PrinterModel,P_Brand]
        return l1
    except:
        #print("Cannot Communicate with "+ip+"\n")
        '''lev="Offline"
        page_count="Offline"
        l1=[lev,page_count]'''
        return False

def make_cap(s):
    conv=[]
    s=s.split(" ")
    if len(s)>1:
        for i in range(len(s)):
            conv.append(str(s[i][0].upper()+s[i][1:]))
        return ' '.join(conv)
    else:
        conv.append(str(s[0][0].upper()+s[0][1:]))
        return conv[0]

def getPass():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(8))
    return password

def resetPassword(name,id,pwd):
    
    import smtplib

    # creates SMTP session
    s = smtplib.SMTP_SSL('smtp.gmail.com', 465)

    # start TLS for security
    #s.starttls()
    s.ehlo()
    mail='printer@flipkart.com'
    # Authentication
    s.login(mail, "FLIP@321")

    # message to be sent
    message = "Hi {name},\n\nYour password has been reset for PMT portal, please find the credentials below\n\nUsername: {id}\nNew Password: {pwd}\n\nThank You.".format(name=name,id=id,pwd=pwd)
    SUBJECT = "PMT- Password Reset"   
    TEXT = message
 
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
 
    # sending the mail    
    s.sendmail(mail, id, message)

    # terminating the session
    s.quit()
    print([name, id, pwd])


def mailPassword(name,id,pwd):
    import smtplib

    # creates SMTP session
    s = smtplib.SMTP_SSL('smtp.gmail.com', 465)

    # start TLS for security
    #s.starttls()
    s.ehlo()
    mail='printer@flipkart.com'
    # Authentication
    s.login(mail, "FLIP@321")

    # message to be sent
    message = "Hi {name},\n\nYour account has been created for PMT portal, please find the credentials below\n\nUsername: {id}\nPassword: {pwd}".format(name=name,id=id,pwd=pwd)

    SUBJECT = "PMT- Account Update | {}".format(datetime.now().strftime('%d-%b-%Y'))   
    TEXT = message
 
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
 
    # sending the mail    
    s.sendmail(mail, id, message)

    # terminating the session
    s.quit()
    print([name, id, pwd])

def getOTP():
    otp=random.randint(235146,987699)
    return otp

def mailOTP(name,id,otp):
    # Python code to illustrate Sending mail from
    # your Gmail account
    import smtplib

    # creates SMTP session
    s = smtplib.SMTP_SSL('smtp.gmail.com', 465)

    # start TLS for security
    #s.starttls()
    s.ehlo()
    mail='printer@flipkart.com'
    # Authentication
    s.login(mail, "FLIP@321")

    # message to be sent
    message = "Hi {name},\n\nYour OTP for {id} is {otp}. Use this Passcode to login secuerly.\n\nThank You".format(name=name,id=id,otp=otp)

    SUBJECT = "PMT- Login OTP | {}".format(datetime.now().strftime('%d-%b-%Y'))   
    TEXT = message
 
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
 
    # sending the mail    
    s.sendmail(mail, id, message)

    # terminating the session
    s.quit()
    print([name, id, otp])

def getUrl():
    characters = string.ascii_letters + string.digits + string.punctuation
    url = ''.join(random.choice(characters) for i in range(16))
    return url