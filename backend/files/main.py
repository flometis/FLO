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
# python3 -m pip install requests

from flask import Flask
from flask import request
from flask import make_response

import sqlite3
import datetime

app = Flask(__name__)

dbpath = "/tmp/Bran/queue.db"

auth_tokens = os.environ.get("AUTH_TOKEN").split(",")


@app.route('/')
def index():
    # example = os.path.abspath(os.path.dirname(
    #    sys.argv[0]))+"/example-response.json"
    # text_file = open(example, "r")
    # myjson = text_file.read().replace(
    #    "\n", "").replace("\r", "").split("####")[0]
    # text_file.close()
    myjson = "{}"
    return myjson


@app.route('/correct', methods=['GET', 'POST'])
def correct():
    global useragent

    # total_memory, used_memory, free_memory = map(
    #    int, os.popen('free -t -m').readlines()[-1].split()[1:])
    # print("RAM total,used,free: ", total_memory, used_memory, free_memory)
    # if free_memory < 100:  # we should always have at least 100MB free for the rest of the os
    #    result = {"errors": "RAM"}
    #    myjson = json.dumps(result)
    #    print("Not enough memory, stopped.")
    #    return myjson

    if request.method == 'GET':
        myjson = index()
        return myjson

    mytext = request.form['text']
    mytext = re.sub('<[^a-z]*?br>', '\n', mytext)
    mytext = re.sub('<.*?>', '', mytext, flags=re.DOTALL)
    mytext = re.sub('\n', '<br>', mytext)
    # print(mytext)
    # Bran si aspetta una riga vuota alla fine del file
    mytext = mytext + '\n'

    optin = False
    try:
        tmpoptin = request.form['optin']
        # print("Optin: "+str(tmpoptin))
        if tmpoptin == "true":
            optin = True
    except:
        pass

    myRS = request.form['ruleset']

    myobj = {"original": "", "corrections": [],
             "files": {}, "optin": str(optin)}
    myobj["original"] = mytext

    while True:
        tmpdir = tempfile.NamedTemporaryFile(dir='/tmp/Bran').name
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)
            break

    origfile = tmpdir+"/testo.txt"
    file = open(origfile, "w", encoding='utf-8')
    file.write(mytext)
    file.close()
    # TODO: forse basta questo
    reqfile = tmpdir+"/request.json"
    file = open(reqfile, "w", encoding='utf-8')
    file.write(json.dumps(request.form))
    file.close()

    token = tmpdir.replace('/tmp/Bran/', '')
    myobj = {'token': token}

    dbconn = sqlite3.connect(dbpath)
    cursor_obj = dbconn.cursor()
    query = """INSERT INTO queue(token, created_at) VALUES (?, ?);"""
    cursor_obj.execute(query, (token, datetime.datetime.now(),))
    dbconn.commit()

    # print("to correct", token)

    myjson = json.dumps(myobj)
    resp = make_response(myjson)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/todo', methods=['GET'])
def todo():
    # Verifico che la richiesta arrivi da un server autorizzato
    try:
        bearer = request.headers.get('Authorization')
        bearertoken = bearer.split()[1]
    except Exception as e:
        bearertoken = ""
    if bearertoken == "" or bearertoken not in auth_tokens:
        return "I'm a teapot", 418

    dbconn = sqlite3.connect(dbpath)
    cursor_obj = dbconn.cursor()
    cursor_obj.execute(
        "SELECT * FROM queue WHERE processed IS NULL ORDER BY created_at asc LIMIT 1")
    fetchedData = cursor_obj.fetchone()
    if fetchedData != None:
        token = fetchedData[0]
        query = "UPDATE queue SET processed = ? WHERE token = ?;"
        cursor_obj.execute(query, (datetime.datetime.now(), token,))
        dbconn.commit()

    try:
        token = token.replace("\n", "")
        if token != "":
            filein = '/tmp/Bran/' + token + '/request.json'
            text_file = open(filein, "r")
            myjson = text_file.read().replace(
                "\n", "").replace("\r", "").split("####")[0]
            text_file.close()
            myrequest = json.loads(myjson)
            # correct(token,request)

        myobj = {"token": token, "request": myrequest}
        resp = make_response(myobj)
    except Exception as e:
        print(e)
        resp = make_response({})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/done', methods=['POST'])
def done():
    # Verifico che la richiesta arrivi da un server autorizzato
    try:
        bearer = request.headers.get('Authorization')
        bearertoken = bearer.split()[1]
    except:
        bearertoken = ""
    if bearertoken == "" or bearertoken not in auth_tokens:
        return "I'm a teapot", 418

    # Mi aspetto di ricevere il results.json da un nodo di elaborazione
    try:
        token = request.values['token']
        results = json.loads(request.values['results'])
        # TODO: verificare se contiene caratteri diversi da quelli consentiti [a-zA-Z0-9\-\_]
        if '..' in token or '/' in token or '\\' in token:
            token = ''
    except:
        results = ''

    try:
        print("Got results for ", token)

        if len(results) == 0:
            error_msg = 'Empty results'
            query = "UPDATE queue SET error = ? WHERE token = ?;"
            cursor_obj.execute(query, (error_msg, token,))
            dbconn.commit()
            resp = make_response({"token": token, "error": error_msg})
        tmpfile = '/tmp/Bran/' + token + '/result.json'
        if not os.path.isfile(tmpfile):
            text_file = open(tmpfile, "w")
            text_file.write(json.dumps(results))
            text_file.close()
            dbconn = sqlite3.connect(dbpath)
            cursor_obj = dbconn.cursor()
            query = "DELETE FROM queue WHERE token = ?;"
            cursor_obj.execute(query, (token,))
            dbconn.commit()
            resp = make_response({"token": token})
    except Exception as e:
        print(e)
        resp = make_response(json.loads("{}"))
        # TODO: se ho ottenuto una risposta errata, scrivo l'errore
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/corrected', methods=['GET', 'POST'])
def corrected():
    # argomento con il nome del file temporaneo
    try:
        token = request.args['token']
        # TODO: verificare se contiene caratteri diversi da quelli consentiti [a-zA-Z0-9\-\_]
        if '..' in token or '/' in token or '\\' in token:
            token = ''
    except:
        token = ''

    try:
        tmpfile = '/tmp/Bran/' + token + '/result.json'
        if os.path.isfile(tmpfile):
            text_file = open(tmpfile, "r")
            tmpcorrs = text_file.read().replace("\n", "").replace("\r", "")
            text_file.close()
        # TODO: se il campo error è popolato, restituisco l'errore

        # myjson = json.dumps(myobj)
        resp = make_response(tmpcorrs)
    except:
        resp = make_response(json.loads("{}"))
        # TODO: rimetto in coda il token se è passato troppo tempo
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    try:
        if not os.path.exists('/tmp/Bran'):
            os.makedirs('/tmp/Bran')
    except Exception as e:
        print(e)
    dbconn = sqlite3.connect(dbpath)
    cursor_obj = dbconn.cursor()
    try:
        query = """ CREATE TABLE queue (
                    token VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    processed TIMESTAMP,
                    error VARCHAR(1024)
                ); """
        cursor_obj.execute(query)
        dbconn.commit()
    except Exception as e:
        print(e)

    app.run(debug=True, host='0.0.0.0', port=int("80"), threaded=True)
