from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys


app = Flask(__name__)
client=MongoClient('mongodb://test:test@3.34.90.101',27017)
db=client.dbAccounts

import json
import sys

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
def post_memo():
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



if __name__ == '__main__':  
   print(sys.executable)
   app.run('0.0.0.0', port=5000, debug=True)