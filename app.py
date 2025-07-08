from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request, redirect
from flask.json.provider import JSONProvider
import jwt
import datetime

import json
import sys
import smtplib
from email.mime.text import MIMEText

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
            'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=15)
        }, app.config['SECRET_KEY'],  algorithm='HS256')
        refresh_token=jwt.encode({
            'user_id':id_receive,
            'exp':datetime.datetime.utcnow()+datetime.timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        db.tokens.update_one(
            {'user_id':id_receive},
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

        stored=db.tokens.find_one({'user_id':user_id})
        if stored and stored['refresh_token']==refresh_token:
            new_access_token=jwt.encode({
                'user_id':user_id,
                'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=15)
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
       return render_template('application.html',user_id=user_id)
   except jwt.ExpiredSignatureError:
       return "토큰이 만료되었습니다. 다시 로그인해주세요."
   except jwt.InvalidTokenError:
       return "유효하지 않은 토큰입니다."


if __name__ == '__main__':  
   print(sys.executable)
   app.run('0.0.0.0', port=5000, debug=True)