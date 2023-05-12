#!/usr/bin/python3


import sys
import os
import os.path
import json
import re
import tempfile
import time
import subprocess
import signal
import requests
#python3 -m pip install requests

from flask import Flask
from flask import request
from flask import make_response

app = Flask(__name__)
pipepath = "/tmp/Bran/pipe"

@app.route('/')
def index():
    example = os.path.abspath(os.path.dirname(sys.argv[0]))+"/example-response.json"
    text_file = open(example, "r")
    myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
    text_file.close()
    return myjson

@app.route('/correct', methods = ['GET', 'POST'])
def correct():
    global useragent
   

    total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    print("RAM total,used,free: ", total_memory, used_memory, free_memory)
    if free_memory < 100:  #we should always have at least 100MB free for the rest of the os
        result = {"errors": "RAM"}
        myjson = json.dumps(result)
        print("Not enough memory, stopped.")
        return myjson

    if request.method == 'GET':
        myjson = index()
        return myjson

    mytext = request.form['text']
    mytext = re.sub('<[^a-z]*?br>', '\n', mytext)
    mytext = re.sub('<.*?>', '', mytext, flags = re.DOTALL)
    mytext = re.sub('\n', '<br>', mytext) 
    #print(mytext)
    mytext = mytext + '\n' #Fix temporaneo: Bran si aspetta una riga vuota alla fine del file

    optin = False
    try:
        tmpoptin = request.form['optin']
        print("Optin: "+str(tmpoptin))
        if tmpoptin == "true":
            optin = True
    except:
        pass

    myRS = request.form['ruleset']

    if myRS == "etr":
        #allregex = allregex2
        #allfilters = allfilters2
        print("using ruleset 2")
    else:
        #allregex = allregex1
        #allfilters = allfilters1
        print("using ruleset 1")

    myobj = {"original": "","corrections": [], "files":{}, "optin": str(optin)}
    myobj["original"] = mytext

    if not os.path.exists('/tmp/Bran'):
        os.makedirs('/tmp/Bran')
    tmpdir = tempfile.NamedTemporaryFile(dir='/tmp/Bran').name
    os.makedirs(tmpdir)
    origfile = tmpdir+"/testo.txt"
    file = open(origfile,"w", encoding='utf-8')
    file.write(mytext)
    file.close()
    #TODO: forse basta questo
    reqfile = tmpdir+"/request.json"
    file = open(reqfile,"w", encoding='utf-8')
    file.write(json.dumps(request.form))
    file.close()
    sessionfile = tmpdir+"/testo-bran.tsv"
    
    token = tmpdir.replace('/tmp/Bran/','')
    myobj = {'token': token} 
    with open(pipepath, "w") as p:
        p.write(token+"\n")

    myjson = json.dumps(myobj)
    resp = make_response(myjson)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
    #return myjson

@app.route('/corrected', methods = ['GET', 'POST'])
def corrected():
    #TODO: prendere argomento con il nome del file temporaneo
    try:
        mytoken = request.args['token']
        #TODO: verificare se contiene caratteri diversi da quelli consentiti [a-zA-Z0-9\-\_]
        if '..' in mytoken or '/' in mytoken or '\\' in mytoken:
            mytoken = ''
    except:
        mytoken = ''
        
    try:
         tmpfile = '/tmp/Bran/' + mytoken + '/result.json'
         text_file = open(tmpfile, "r")
         tmpcorrs = text_file.read().replace("\n", "").replace("\r", "")
         text_file.close()
         
         #myjson = json.dumps(myobj)
         resp = make_response(tmpcorrs)
    except:
        resp = make_response(json.loads("{}"))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__': 
    try:
        if not os.path.exists('/tmp/Bran'):
            os.makedirs('/tmp/Bran')
        os.mkfifo(pipepath)
    except Exception as e:
        print(e)
        
    app.run(debug=True, host='0.0.0.0', port=int("80"), threaded=True)
