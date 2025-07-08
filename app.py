from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request, redirect
from flask.json.provider import JSONProvider
from datetime import datetime, timedelta
import jwt

import json
import sys
import smtplib
from email.mime.text import MIMEText
from calendar import monthrange

app = Flask(__name__)
client=MongoClient('mongodb://test:test@3.34.90.101',27017)
db=client.dbAccounts
app.config['SECRET_KEY']='1q2w3e4r!'  # secret key


class CustomJSONEncoder(json.JSONEncoder): 
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)
    
app.json = CustomJSONProvider(app)

def get_duration(start,end):

    if end<=start:
        end+=timedelta(days=1)

    duration= end-start
    total_seconds=duration.total_seconds()
    hours, remainder=divmod(int(total_seconds),3600)
    minutes=remainder//60

    return f"{hours:02d}:{minutes:02d}"




@app.route('/')
def home():
   return render_template('login.html')


@app.route('/register') # register로 라우팅 한 부분
def register():
   return render_template('register.html') # register.html로 이동

@app.route('/register/post',methods=['POST'])
def regist_account():
   id_receive=request.form['id_give']
   pw_receive=request.form['pw_give']
   name_receive=request.form['name_give']
   gender_receive=request.form['gender_give']
   email_receive=request.form['email_give']
   birth_receive=request.form['birth_give']
   account={'id':id_receive, 'pw':pw_receive, 'name':name_receive, 'gender':gender_receive, 'email':email_receive, 'birth':birth_receive}
   
   db.accounts.insert_one(account)

   return jsonify({'result':'success'})

@app.route('/find') # find로 라우팅 한 부분
def find():
   return render_template('find.html') # find.html로 이동

@app.route('/find/id', methods=['POST']) # id 찾기
def find_id():
    name_receive=request.form['name_give']
    email_receive=request.form['email_give']
    found_user=db.accounts.find_one({'name':name_receive, 'email':email_receive})
    if found_user:
        return jsonify({'result':'success','userid':found_user['id']})
    else:
        return jsonify({'result':'failure'})
    

def send_email(receiver, pw):  # email 보내기기
    smtp = smtplib.SMTP('smtp.gmail.com', 587, local_hostname='localhost')
    smtp.starttls()
    smtp.login('farvinjr104@gmail.com', 'xzyk njxn dkru cvku')
    msg = MIMEText(f"해당 계정의의 비밀번호는: {pw} 입니다.")
    msg['Subject'] = '비밀번호 찾기 결과'
    msg['To'] = receiver
    msg['From'] = 'farvinjr104@gmail.com'
    smtp.sendmail('farvinjr104@gmail.com', receiver, msg.as_string())
    smtp.quit()
    
@app.route('/find/pw', methods=['POST'])
def find_pw():
    userid_receive = request.form['userid_give']
    name_receive = request.form['name_give']
    email_receive = request.form['email_give']
    user = db.accounts.find_one({
        'id': userid_receive,
        'name': name_receive,
        'email': email_receive
    })
    if user:
        pw = user['pw']  # 주의: 평문으로 저장된 경우!
        send_email(email_receive, pw)
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail'})


@app.route('/login',methods=['POST']) # login 부분
def login():
    id_receive=request.form['userid_give']
    pw_receive=request.form['password_give']
    found_user=db.accounts.find_one({'id':id_receive})
    if found_user['pw']==pw_receive:
        access_token=jwt.encode({
            'user_id':id_receive,
            'user_name':found_user['name'],
            'exp':datetime.utcnow()+timedelta(minutes=15)
        }, app.config['SECRET_KEY'],  algorithm='HS256')
        refresh_token=jwt.encode({
            'user_id':id_receive,
            'user_name':found_user['name'],
            'exp':datetime.utcnow()+timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        db.tokens.update_one(
            {'user_id':id_receive, 'user_name':found_user['name']},
            {'$set':{'refresh_token':refresh_token}},
            upsert=True
        )
        resp=jsonify({'result':'success','access_token':access_token})
        resp.set_cookie('refresh_token',refresh_token,httponly=True,path='/refresh')
        return resp
    else:
        return jsonify({'result':'failure'})
@app.route('/refresh',methods=['POST'])
def refresh():
    refresh_token=request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'result':'no_token'}),401
    
    try:
        payload=jwt.decode(refresh_token,app.config['SECRET_KEY'],algorithms=['HS256'])
        user_id=payload['user_id']
        user_name=payload['user_name']
        stored=db.tokens.find_one({'user_id':user_id, 'user_name':user_name})
        if stored and stored['refresh_token']==refresh_token:
            new_access_token=jwt.encode({
                'user_id':user_id,
                'user_name':user_name,
                'exp':datetime.utcnow()+timedelta(minutes=15)
            },app.config['SECRET_KEY'],algorithm='HS256')
            return jsonify({'result':'success','access_token':new_access_token})
        else:
            return jsonify({'result':'invalid_token'}),401
    except jwt.ExpiredSignatureError:
        return jsonify({'result':'expired'}),401
    except jwt.InvalidTokenError:
        return jsonify({'result':'invalid'}),401
    
@app.route('/application') # application으로 라우팅 한 부분
def application():
   token=request.cookies.get('access_token')
   if not token:
       return redirect('/')
   try:
       decoded=jwt.decode(token, app.config['SECRET_KEY'],algorithms=['HS256'])
       user_id=decoded['user_id']
       user_name=decoded['user_name']
       return render_template('application.html',user_id=user_id, user_name=user_name)
   except jwt.ExpiredSignatureError:
       return "토큰이 만료되었습니다. 다시 로그인해주세요."
   except jwt.InvalidTokenError:
       return "유효하지 않은 토큰입니다."

@app.route('/application/start', methods=['POST'])
def start_sleep():
    id_receive=request.form['id_give']
    name_receive=request.form['name_give']
    wakeup_goal_receive=request.form['wakeup_goal_receive']
    checkData=db.sleepdata.find_one({'id':id_receive,'name':name_receive,'sleep_end':0})
    if not checkData :
        sleepData={
            'id':id_receive,
            'name':name_receive,
            'sleep_start':datetime.utcnow(),
            'sleep_end':0,
            'wakeup_goal':wakeup_goal_receive,
            'duration':0,
            'isAchieved':False
        }
        db.sleepdata.insert_one(sleepData)
        return jsonify({'result':'success'})
    else:
        return jsonify({'result':'failure'})

@app.route('/application/end',methods=['POST'])
def end_sleep():
    id_receive=request.form['id_give']
    name_receive=request.form['name_give']
    user=db.account.find_one({'id':id_receive,'name':name_receive,'sleep_end':0})
    sleep_end=datetime.utcnow()
    duration=get_duration(sleep_end,user['sleep_start'])
    
    h,m=map(int,user['wakeup_goal'].split(":"))
    goal=sleep_end.replace(hour=h, minute=m, second=0, microsecond=0)
    isAchieved=(sleep_end<=goal)
    db.sleepdata.update_one(
        {'_id':user['_id']},
        {'$set':{'sleep_end':sleep_end,'duration':duration,'isAchieved':isAchieved}}
    )
    return jsonify({'result':'success'})

@app.route('/application/refresh')
def refresh_duration():
    return jsonify({'result':'success'})

@app.route('/calender')
def calender():
    year=request.args.get('year',type=int)
    month=request.args.get('month',type=int)

    if not year or not month:
        today=datetime.today()
        year=today.year
        month=today.month
    
    start_date=datetime(year,month,1)
    days_in_month=monthrange(year,month)[1]
    end_date=datetime(year,month, days_in_month,23,59,59)

    user_id=
    records=list(db.sleepdata.find({
        'id':user_id,
        'sleep_start':{'$gte':start_date,'$lte':end_date}
    }))

    def parse_duration(s):
        h,m=map(int,s.split(":"))
        return h*60+m
    
    durations=[parse_duration(r['duration'])for r in records if r.get('duration') and r['duration'] != "0"]
    achieved_count=sum(1 for r in records if r.get('isAchieved'))

    if durations:
        avg_min=sum(durations) //len(durations)
        max_min=max(durations)
        min_min=min(durations)
        def to_hhmm(m): return f"{m // 60:02d}:{m%60:02d}"
        my_stats={
            'avg_sleep':to_hhmm(avg_min),
            'goal_count':achieved_count,
            'max_sleep':to_hhmm(max_min),
            'min_sleep':to_hhmm(min_min)
        }
    else:
        my_stats{
            'avg_sleep':"00:00",
            'goal_count':0,
            'max_sleep':"00:00",
            'min_sleep':"00:00",
        }
    return render_template('calender.html',
                           year=year,
                           month=month,
                           days_in_month=days_in_month,
                           my_stats=my_stats)

if __name__ == '__main__':  
   print(sys.executable)
   app.run('0.0.0.0', port=5000, debug=True)