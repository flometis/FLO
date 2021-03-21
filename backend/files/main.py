#!/usr/bin/python3


import sys
import os
import os.path
import json
import re

from flask import Flask
from flask import request

app = Flask(__name__)
allregex = []

@app.route('/')
def index():
    example = os.path.abspath(os.path.dirname(sys.argv[0]))+"/example-response.json"
    text_file = open(example, "r")
    myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
    text_file.close()
    return myjson

@app.route('/correct', methods = ['GET', 'POST'])
def correct():
    if request.method == 'GET':
        myjson = index()
        return myjson

    mytext = request.form['text']
    mytext = re.sub('<(?!\s*\/*\s*br\s*\/*\s*/?>)[^<>]*>','', mytext)

    myobj = {"original": "","corrections": []}
    myobj["original"] = mytext
    
    for myregex in allregex:
        mycorrections = findRegex(mytext, myregex[0], myregex[1], myregex[2])
        for mycorr in mycorrections:
            myobj["corrections"].append(mycorr)

    myjson = json.dumps(myobj)
    return myjson

def loadRegexFromTSV(fileName):
    global allregex
    allregex = []
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.split('\t')
            if len(row) == 3:
                allregex.append(row)

def findRegex(mytext, pattern, recommendedText, explanation):
    mycorrections = []
    for m in re.finditer(pattern, mytext):
        mycorr = {"start": 0, "end": 0, "recommendedText": "", "explanation": ""}
        mycorr["start"] = m.start(0) 
        mycorr["end"] = m.end(0) 
        mycorr["recommendedText"] = re.sub(pattern, recommendedText, m.group(0)) 
        mycorr["explanation"] = explanation
        mycorrections.append(mycorr)
    return mycorrections

if __name__ == '__main__':
    loadRegexFromTSV(os.path.abspath(os.path.dirname(sys.argv[0]))+"/regex.tsv")
    app.run(debug=True, host='0.0.0.0', port=int("80"), threaded=True)
