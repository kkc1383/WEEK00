from collections import defaultdict
from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, render_template_string, request, redirect, make_response
from flask.json.provider import JSONProvider
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv
import os
import json
import sys
import smtplib
from email.mime.text import MIMEText
from calendar import monthrange

app = Flask(__name__)
load_dotenv()
mongo_uri=os.getenv('MONGO_URI')
client=MongoClient(mongo_uri)
db=client.get_default_database()
app.config['SECRET_KEY']=os.getenv('SECRET_KEY')  # secret key
EMAIL_USER=os.getenv('EMAIL_USER')
EMAIL_PASSWORD=os.getenv('EMAIL_PASSWORD')

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

    duration=end-start
    total_seconds=duration.total_seconds()
    ''' 
        디버깅에 용이함을 위해 시:분이 저장되어야 할 것을 한 단계 낮추어
        분:초가 저장되게끔 바꾸었음
        나중에 실제로 서비스 할때는 60->3600으로 바꾸면 시: 분이 duration에 저장됨
    '''
    hours, remainder=divmod(int(total_seconds),3600) 
    minutes=remainder//60  # 실제로 서비스 할때는 60으로 나눈 몫이 필요함

    return f"{hours:02d}:{minutes:02d}"

def parse_duration(s):
    h,m=map(int,s.split(":"))
    return h*60+m

def to_hhmm(m): return f"{m // 60:02d}:{m%60:02d}"

def is_token_valid(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        # 필요하다면 payload 검사 (예: 만료 시간, 사용자 정보 등)
        return True
    except jwt.ExpiredSignatureError:
        return False  # 토큰이 만료됨
    except jwt.InvalidTokenError:
        return False  # 서명 위조, 잘못된 토큰 등

@app.route('/')
def home():
   return render_template('login.html')

@app.route('/application/calculate')
def calculate():
    datas=db.sleepdata.find({})
    for data in datas:
        if data['sleep_end']!=0:
            my_duration=get_duration(data['sleep_start'],data['sleep_end'])
            h,m=map(int,data['wakeup_goal'].split(":"))
            goal=data['sleep_end'].replace(hour=h, minute=m, second=0, microsecond=0)
            isAchieved=(data['sleep_end']<=goal)
        else:
            my_duration="00:00"
            isAchieved=False
        db.sleepdata.update_one({'_id':data['_id']},{'$set':{'duration':my_duration,'isAchieved':isAchieved}})
    return redirect('/application')

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
   
   # ✅ 비밀번호 길이 검사
   if not (8 <= len(pw_receive) < 15):
        return jsonify({'result': 'fail', 'msg': '비밀번호 길이가 조건에 맞지 않습니다.'})

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
    

def send_email(receiver, pw):  # email 보내기
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(EMAIL_USER, EMAIL_PASSWORD)
    msg = MIMEText(f"해당 계정의 비밀번호는: {pw} 입니다.")
    msg['Subject'] = '비밀번호 찾기 결과'
    msg['To'] = receiver
    msg['From'] = EMAIL_USER
    smtp.sendmail(EMAIL_USER, receiver, msg.as_string())
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
        now=datetime.utcnow()+timedelta(hours=9)
        access_token=jwt.encode({
            'user_id':id_receive,
            'user_name':found_user['name'],
            'exp':now+timedelta(minutes=15)
        }, app.config['SECRET_KEY'],  algorithm='HS256')
        refresh_token=jwt.encode({
            'user_id':id_receive,
            'user_name':found_user['name'],
            'exp':now+timedelta(days=7)
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
            now=datetime.utcnow()+timedelta(hours=9)
            new_access_token=jwt.encode({
                'user_id':user_id,
                'user_name':user_name,
                'exp':now+timedelta(minutes=15)
            },app.config['SECRET_KEY'],algorithm='HS256')
            return jsonify({'result':'success','access_token':new_access_token})
        else:
            return jsonify({'result':'invalid_token'}),401
    except jwt.ExpiredSignatureError:
        return jsonify({'result':'expired'}),401
    except jwt.InvalidTokenError:
        return jsonify({'result':'invalid'}),401

@app.route('/logout',methods=['POST']) # 로그아웃 
def logout():
    token=request.cookies.get('access_token')
    if not token:
        return redirect('/')
    
    try:
        decoded=jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id=decoded['user_id']
    except jwt.InvalidTokenError:
        return redirect('/')

    response=make_response(redirect('/'))
    response.set_cookie('access_token', '',expires=0)
    response.set_cookie('refresh_token','',expires=0)
    db.tokens.delete_one({'user_id':user_id})
    return response
    
@app.route('/application') # application으로 라우팅 한 부분
def application():
   token=request.cookies.get('access_token')
   if not token or not is_token_valid(token):
       return redirect('/')
   try:
       decoded=jwt.decode(token, app.config['SECRET_KEY'],algorithms=['HS256'])
       user_id=decoded['user_id']
       user_name=decoded['user_name']
       record=db.sleepdata.find_one({
        'id':user_id,
        'name':user_name,
        'sleep_end':0
       })
       if record and 'sleep_start' in record: # 수면 중이면
            is_sleeping=True
            sleep_start=record['sleep_start']
            now=datetime.utcnow()+timedelta(hours=9)
            elapsed_seconds=int((now-sleep_start).total_seconds())
       else:
           is_sleeping=False
           elapsed_seconds=0
        
       users=get_sleep_users_data(user_id)
       now=datetime.utcnow()+timedelta(hours=9)
       if 0<=now.hour<= 10: # 오늘이 늦은 새벽일 경우 sleep_end와 오늘이 다른날이기 때문에 1일을 빼줌
           yesterday_start=(now-timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)   # 어제 나의 데이터 찾기 위한 시작 지점
           threeday_group_start=(now-timedelta(days=4)).replace(hour=0,minute=0,second=0,microsecond=0)   # 최근 3일 그룹 데이터 찾기 위한 시작 지점
       else: # 어제 수면 데이터의 sleep_end는 오늘과 같은 날일 거니까
           yesterday_start=now.replace(hour=0,minute=0,second=0,microsecond=0)
           threeday_group_start=(now-timedelta(days=3)).replace(hour=0,minute=0,second=0,microsecond=0)   

       yesterday_end=yesterday_start+timedelta(days=1) # 어제 나의 데이터 찾기 위한 끝 지점
       threeday_group_end=threeday_group_start+timedelta(days=1) # 최근 3일 그룹 데이터 찾기 위한 끝 지점
       
       yesterday_data=db.sleepdata.find_one({'id':user_id,'name':user_name,'sleep_end':{'$gte':yesterday_start,'$lt':yesterday_end}})
       if yesterday_data:
           isExistYesterday=True
           sleeptime_rough=(now-yesterday_data['sleep_start']).total_seconds()
           waketime_rough=(now-yesterday_data['sleep_end']).total_seconds()
           if sleeptime_rough < (3600*24):
                sleep_trend="일찍"
           else:
                sleep_trend="늦게"
           if waketime_rough <(3600*24) :
                wake_trend="일찍"
           else:
                wake_trend="늦게"

           sleeptime_gap=abs((3600*24)-sleeptime_rough)
           sleep_hours, sleep_remainder=divmod(int(sleeptime_gap),3600) 
           sleep_minutes=sleep_remainder//60 
           sleeptime_diff=f"{sleep_hours}시간 {sleep_minutes}분"

           waketime_gap=abs((3600*24)-waketime_rough)
           wake_hours, wake_remainder=divmod(int(waketime_gap),3600) 
           wake_minutes=wake_remainder//60 
           waketime_diff=f"{wake_hours}시간 {wake_minutes}분"
       else:
           isExistYesterday=False
           sleeptime_diff=""
           sleep_trend=""
           waketime_diff=""
           wake_trend=""


       threeday_data=list(db.sleepdata.find({'sleep_end':{'$gte':threeday_group_start,'$lt':threeday_group_end}}))

       sleep_datetimes = [r['sleep_start'] for r in threeday_data if r.get('sleep_start') and isinstance(r['sleep_start'], datetime)]

       if sleep_datetimes:
            avg_seconds = sum(dt.hour * 3600 + dt.minute * 60 for dt in sleep_datetimes) // len(sleep_datetimes)
            avg_hour = avg_seconds // 3600
            avg_min = (avg_seconds % 3600) // 60
            groupsleep_avg = f"{avg_hour:02d}:{avg_min:02d}"
       else:
            groupsleep_avg = "00:00"

       wakeup_datetimes = [r['sleep_end'] for r in threeday_data if r.get('sleep_end') and isinstance(r['sleep_end'], datetime)]
       if wakeup_datetimes:
            avg_seconds = sum(dt.hour * 3600 + dt.minute * 60 for dt in wakeup_datetimes) // len(wakeup_datetimes)
            avg_hour = avg_seconds // 3600
            avg_min = (avg_seconds % 3600) // 60
            groupwake_avg = f"{avg_hour:02d}:{avg_min:02d}"
       else:
            groupwake_avg = "00:00"
       return render_template('application.html',
                              users=users,
                              user_id=user_id,
                              user_name=user_name,
                              is_sleeping=is_sleeping,
                              elapsed_seconds=elapsed_seconds,
                              sleeptime_diff=sleeptime_diff,
                              sleep_trend=sleep_trend,
                              waketime_diff=waketime_diff,
                              wake_trend=wake_trend,
                              groupsleep_avg=groupsleep_avg,
                              groupwake_avg=groupwake_avg,
                              isExistYesterday=isExistYesterday
                              )
   except jwt.ExpiredSignatureError:
       return "토큰이 만료되었습니다. 다시 로그인해주세요."
   except jwt.InvalidTokenError:
       return "유효하지 않은 토큰입니다."
   
def get_sleep_users_data(user_id):
    users= list(db.accounts.find({'id':{'$ne':user_id}})) # 모든 사용자 정보 가져오기
    sleep_status={}
    for user in users:
        record=db.sleepdata.find_one({'name':user['name'],'sleep_end':0})
        if record:
            now=datetime.utcnow()+timedelta(hours=9)
            sleep_status[user['name']]=get_duration(record['sleep_start'],now)
        else:
            sleep_status[user['name']]="00:00"
    return sleep_status

@app.route('/application/status',methods=['POST'])
def get_status():
    user_id=request.form['user_id']
    user_name=request.form['user_name']

    record=db.sleepdata.find_one({
        'id':user_id,
        'name':user_name,
        'sleep_end':0
    })
    if record and 'sleep_start' in record:
        is_sleeping=True
        sleep_start=record['sleep_start']
        now=datetime.utcnow()+timedelta(hours=9)
        elapsed_seconds=int((now-sleep_start).total_seconds())
    else:
        is_sleeping=False
        elapsed_seconds=0

    template = """
    {% if is_sleeping %}
      <h2>휴식을 종료할까요?</h2>
      <h3>좋은 아침입니다! 오늘 하루도 화이팅!</h3>
      <script>document.body.dataset.sleeping = 'true';</script>
    {% else %}
      <h2>휴식을 시작할까요?</h2>
      <h3>오늘 하루도 고생하셨습니다!</h3>
      <script>document.body.dataset.sleeping = 'false';</script>
    {% endif %}
    """
    
    return render_template_string(template,
                               is_sleeping=is_sleeping,
                               elapsed_seconds=elapsed_seconds)

@app.route('/application/refresh',methods=['POST'])
def refresh_data():
    user_id=request.form['user_id']
    sleep_users_data=get_sleep_users_data(user_id)
    return jsonify({'result':'success','users':sleep_users_data})

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
            'sleep_start':datetime.utcnow()+timedelta(hours=9),
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
    user=db.sleepdata.find_one({'id':id_receive,'name':name_receive,'sleep_end':0})
    if not user:
        return jsonify({'result':'failure'})
    sleep_end=datetime.utcnow()+timedelta(hours=9)
    duration=get_duration(user['sleep_start'],sleep_end)
    
    h,m=map(int,user['wakeup_goal'].split(":"))
    goal=sleep_end.replace(hour=h, minute=m, second=0, microsecond=0)
    isAchieved=(sleep_end<=goal)
    db.sleepdata.update_one(
        {'_id':user['_id']},
        {'$set':{'sleep_end':sleep_end,'duration':duration,'isAchieved':isAchieved}}
    )
    return jsonify({'result':'success'})


@app.route('/calender')
def calender():
    token=request.cookies.get('access_token')
    if not token or not is_token_valid(token):
        return redirect('/')
    try:
        decoded=jwt.decode(token, app.config['SECRET_KEY'],algorithms=['HS256'])
        user_id=decoded['user_id']
        user_name=decoded['user_name']
        

        # 여기서부터 이번 달 수면 데이터 처리
        now=datetime.utcnow()+timedelta(hours=9)
        year=request.args.get('year',default=now.year, type=int)
        month=request.args.get('month',default=now.month, type=int)

        prev_year, prev_month=year,month-1
        if prev_month ==0:
            prev_year-=1
            prev_month=12
        
        next_year, next_month=year,month+1
        if next_month==13:
            next_year+=1
            next_month=1

        if not year or not month:
            today=datetime.today()
            year=today.year
            month=today.month
        
        start_date=datetime(year,month,1)
        first_weekday, days_in_month=monthrange(year,month)
        end_date=datetime(year,month, days_in_month,23,59,59)

        # 총 그룹 불러오기
        all_records_rough=list(db.sleepdata.find({}))

        all_records=[]
        my_records=[]
        for record in all_records_rough:
            sleep_start=record.get('sleep_start')
            if not sleep_start:
                continue

            if 0<=sleep_start.hour<10:
                compare_date=(sleep_start-timedelta(days=1))
            else:
                compare_date=sleep_start
            
            if start_date<=compare_date<=end_date:
                all_records.append(record)

                # 그 중에 내 기록 추출하기
                if record.get('id')==user_id and record.get('name')==user_name:
                    my_records.append(record)

        
        # 이번달 내 데이터 처리 관련
        my_durations=[parse_duration(r['duration'])for r in my_records if r.get('duration') and r['duration'] != "0"]
        achieved_count=sum(1 for r in my_records if r.get('isAchieved'))

        sleep_status = {}
        for record in my_records:
            sleep_start=record.get("sleep_start")
            if not sleep_start:
                continue
            if 0<=sleep_start.hour<10:
                adjusted_date=(sleep_start-timedelta(days=1)).date()
            else:
                adjusted_date=sleep_start.date()
            key=adjusted_date.strftime('%Y-%m-%d')

            if 'isAchieved' in record and record['sleep_end']!=0:
                if record['isAchieved'] == True:
                    sleep_status[key] = 'success'
                elif record['isAchieved'] == False:
                    sleep_status[key] = 'fail'
            else:
                sleep_status[key] = ''  # or 생략 가능 (템플릿에서 get()하면 None)

        if my_durations:
            avg_min=sum(my_durations) //len(my_durations)
            max_min=max(my_durations)
            min_min=min(my_durations)
            my_stats={
                'avg_sleep':to_hhmm(avg_min),
                'goal_count':f"{achieved_count}/{days_in_month}",
                'max_sleep':to_hhmm(max_min),
                'min_sleep':to_hhmm(min_min)
            }
        else:
            my_stats={
                'avg_sleep':"00:00",
                'goal_count':f"0/{days_in_month}",
                'max_sleep':"00:00",
                'min_sleep':"00:00",
            }
        
        # 이번달 그룹 내 데이터 처리 관련
        valid_durations = [parse_duration(r['duration']) for r in all_records if r.get('duration') and r['duration'] != "0"]

        if valid_durations:
            avg_minutes = sum(valid_durations) // len(valid_durations)
            avg_sleep = f"{avg_minutes // 60:02d}:{avg_minutes % 60:02d}"
        else:
            avg_sleep = "00:00"

        # 그룹 평균 기상시간
        wakeup_datetimes = [r['sleep_end'] for r in all_records if r.get('sleep_end') and isinstance(r['sleep_end'], datetime)]

        if wakeup_datetimes:
            avg_seconds = sum(dt.hour * 3600 + dt.minute * 60 for dt in wakeup_datetimes) // len(wakeup_datetimes)
            avg_hour = avg_seconds // 3600
            avg_min = (avg_seconds % 3600) // 60
            avg_wake = f"{avg_hour:02d}:{avg_min:02d}"
        else:
            avg_wake = "00:00"

        # 그룹 가장 많이 잔 사람과 시간
        longest_record = max(
            (r for r in all_records if r.get('duration') and r['duration'] != "0"),
            key=lambda r: parse_duration(r['duration']),
            default=None
        )

        if longest_record:
            max_sleeper = longest_record['name']
            max_duration = longest_record['duration']
        else:
            max_sleeper = "N/A"
            max_duration = "00:00"
        
        user_counts = defaultdict(lambda: {'achieved': 0})

        # 각 사용자별 달성 횟수 계산
        for r in all_records:
            if not r.get('name'):
                continue
            name = r['name']
            if r.get('isAchieved'):
                user_counts[name]['achieved'] += 1

        # 가장 많이 달성한 사용자 찾기
        best_user = None
        best_count = -1

        for name, counts in user_counts.items():
            if counts['achieved'] > best_count:
                best_user = name
                best_count = counts['achieved']

        # 결과 문자열 만들기
        if best_user:
            max_goal = f"{best_user} ({best_count} / {days_in_month})"
        else:
            max_goal = "N/A"
        
        group_stats = {
            'avg_sleep': avg_sleep,
            'avg_wake': avg_wake,
            'max_sleeper': f"{max_sleeper} ({max_duration})",
            'max_goal': max_goal
        }
        return render_template('calender.html',
                            user_id=user_id,
                            user_name=user_name,
                           year=year,
                           month=month,
                           prev_year=prev_year, prev_month=prev_month,
                           next_year=next_year, next_month=next_month,
                           first_weekday=first_weekday,
                           days_in_month=days_in_month,
                           sleep_status=sleep_status,
                           my_stats=my_stats,
                           group_stats=group_stats,
                           now=now)
    except jwt.ExpiredSignatureError:
        return "토큰이 만료되었습니다. 다시 로그인해주세요."
    except jwt.InvalidTokenError:
        return "유효하지 않은 토큰입니다."
    
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


if __name__ == '__main__':  
   print(sys.executable)
   app.run('0.0.0.0', port=5000, debug=True)