from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys


app = Flask(__name__)
client=MongoClient('mongodb://test:test@3.34.90.101',27017)
db=client.dbjungle

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
   return render_template('index.html')

@app.route('/memo/read',methods=['GET'])
def read_memos():
    result=list(db.memos.find({}).sort('likes',-1))
    return jsonify({'result':'success','memos_list':result})

@app.route('/memo/post',methods=['POST'])
def post_memo():
   title_receive=request.form['title_give']
   text_receive=request.form['text_give']
   likes_receive=request.form['likes_give']

   memo={'title':title_receive, 'text':text_receive, 'likes':int(likes_receive)}
   
   db.memos.insert_one(memo)

   return jsonify({'result':'success'})

@app.route('/memo/delete', methods=['POST'])
def delete_memo():
    id_receive=request.form['id_give']
    db.memos.delete_one({'_id':ObjectId(id_receive)})

    return jsonify({'result': 'success'})

@app.route('/memo/like', methods=['POST'])
def like_memo():
    id_receive=request.form['id_give']
    memo=db.memos.find_one({'_id':ObjectId(id_receive)})
    new_likes=int(memo['likes'])+1
    db.memos.update_one({'_id':ObjectId(id_receive)},{'$set':{'likes':new_likes}})

    return jsonify({'result': 'success'})

@app.route('/memo/edit', methods=['POST'])
def edit_memo():
    id_receive=request.form['id_give']
    title_receive=request.form['title_give']
    text_receive=request.form['text_give']
    db.memos.update_one({'_id':ObjectId(id_receive)},{'$set':{'title':title_receive, 'text':text_receive}})

    return jsonify({'result': 'success'})


if __name__ == '__main__':  
   print(sys.executable)
   app.run('0.0.0.0', port=5000, debug=True)