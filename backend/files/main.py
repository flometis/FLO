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

from flask import Flask
from flask import request

sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0]))+'/Bran')
from forms import BranCorpus

app = Flask(__name__)
allregex = []


corpuscols = {}
ignoretext = ""
dimList = []
legendaPos = {}

def loadBranData():
    global corpuscols
    global ignoretext
    global dimList
    global legendaPos
    corpuscols = {
                'TAGcorpus': [0, "Tag corpus"],
                'token': [1, "Forma grafica"],
                'lemma': [2, "Lemma"],
                'pos': [3, "Tag PoS"],
                'ner': [4, "Tag NER"],
                'feat': [5, "Morfologia"],
                'IDword': [6, "ID parola"],
                'IDphrase': [7, "ID frase"],
                'dep': [8, "Tag Dep"],
                'head': [9, "Head"]
    }
    ignoretext = "((?<=[^0-9])"+ re.escape(".")+ "|^" + re.escape(".")+ "|(?<= )"+ re.escape("-")+ "|^"+re.escape("-")+ "|"+re.escape(":")+"|(?<=[^0-9])"+re.escape(",")+"|^"+re.escape(",")+"|"+re.escape(";")+"|"+re.escape("?")+"|"+re.escape("!")+"|"+re.escape("«")+"|"+re.escape("»")+"|"+re.escape("\"")+"|"+re.escape("(")+"|"+re.escape(")")+"|^"+re.escape("'")+ "|" + re.escape("[PUNCT]") + "|" + re.escape("[SYMBOL]") + "|" + re.escape("<unknown>") + ")"
    dimList = [100,1000,5000,10000,50000,100000,150000,200000,250000,300000,350000,400000,450000,500000,1000000]
    try:
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/ud.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        legendaPos = json.loads(myjson)
    except:
        legendaPos = {"A":["aggettivo", "aggettivi", "piene"],"AP":["agg. poss", "aggettivi", "piene"],"B":["avverbio", "avverbi", "piene"],"B+PC":["avverbio+pron. clit. ", "avverbi", "piene"],"BN":["avv, negazione", "avverbi", "piene"],"CC":["cong. coord", "congiunzioni", "vuote"],"CS":["cong. sub.", "congiunzioni", "vuote"],"DD":["det. dim.", "aggettivi", "piene"],"DE":["det. esclam.", "aggettivi", "piene"],"DI":["det. indefinito", "aggettivi", "piene"],"DQ":["det. interr.", "aggettivi", "piene"],"DR":["det. Rel", "aggettivi", "piene"],"E":["preposizione", "preposizioni", "vuote"],"E+RD":["prep. art. ", "preposizioni", "vuote"],"FB":["punteggiatura - \"\" () «» - - ", "punteggiatura", "none"],"FC":["punteggiatura - : ;", "punteggiatura", "none"],"FF":["punteggiatura - ,", "punteggiatura", "none"],"FS":["punteggiatura - .?!", "punteggiatura", "none"],"I":["interiezione", "interiezioni", "vuote"],"N":["numero", "altro", "none"],"NO":["numerale", "aggettivi", "piene"],"PC":["pron. Clitico", "pronomi", "vuote"],"PC+PC":["pron. clitico+clitico", "pronomi", "vuote"],"PD":["pron. dimostrativo", "pronomi","vuote"],"PE":["pron. pers. ", "pronomi", "vuote"],"PI":["pron. indef.", "pronomi", "vuote"],"PP":["pron. poss.", "pronomi", "vuote"],"PQ":["pron. interr.", "pronomi", "vuote"],"PR":["pron. rel.", "pronomi", "vuote"],"RD":["art. Det.", "articoli", "vuote"],"RI":["art. ind.", "articoli", "vuote"],"S":["sost.", "sostantivi", "piene"],"SP":["nome proprio", "sostantivi", "piene"],"SW":["forestierismo", "altro", "none"],"T":["det. coll.)", "aggettivi", "piene"],"V":["verbo", "verbi", "piene"],"V+PC":["verbo + pron. clitico", "verbi", "piene"],"V+PC+PC":["verbo + pron. clitico + pron clitico", "verbi", "piene"],"VA":["verbo ausiliare", "verbi", "piene"],"VA+PC":["verbo ausiliare + pron.clitico", "verbi", "piene"],"VM":["verbo mod", "verbi", "piene"],"VM+PC":["verbo mod + pron. clitico", "verbi", "piene"],"X":["altro", "altro", "none"]}
    

@app.route('/')
def index():
    example = os.path.abspath(os.path.dirname(sys.argv[0]))+"/example-response.json"
    text_file = open(example, "r")
    myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
    text_file.close()
    return myjson

@app.route('/correct', methods = ['GET', 'POST'])
def correct():
    global corpuscols
    global ignoretext
    global dimList
    global legendaPos
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

    if not os.path.exists('/tmp/Bran'):
        os.makedirs('/tmp/Bran')
    tmpdir = tempfile.NamedTemporaryFile(dir="/tmp/Bran").name
    os.makedirs(tmpdir)
    origfile = tmpdir+"/testo.txt"
    file = open(origfile,"w", encoding='utf-8')
    file.write(mytext)
    file.close()
    sessionfile = tmpdir+"/testo-bran.tsv"
    
    execWithTimeout("python3 /var/www/app/Bran/main.py udpipeImport "+origfile+" it-IT n", sessionfile, 10)
    Corpus = BranCorpus.BranCorpus(corpuscols, legendaPos, ignoretext, dimList, tablewidget="cli")
    Corpus.loadPersonalCFG()
    myrecovery = False #"n"
    Corpus.CSVloader([sessionfile])
    Corpus.sessionFile = sessionfile

    # /var/www/app/Bran/main.py cerca /tmp/Bran/tmp52vjhuco/testo-bran.tsv 1 "pos[2]=A.*&&lemma[-1]=o.*" n
    
    mycol = 1
    try:
    	output = Corpus.core_misure_lessicometriche(mycol, myrecovery)
    except:
        output = ""
    output = sessionfile+"-misure_lessicometriche-token.tsv"
    mis_les = loadFromTSV(output)
    myobj["misure_lessicometriche"] = mis_les 

    mylevel = 1 
    output = sessionfile+"-densitalessicale-" + str(mylevel) + ".tsv"
    execWithTimeout('/var/www/app/Bran/main.py densitalessicale "'+sessionfile+'" '+ str(mylevel) +' n', output, 2)
    dens = loadFromTSV(output)
    myobj["densita_lessicale"] = dens


    Corpus.chiudiProgetto()

    myjson = json.dumps(myobj)
    return myjson

def execWithTimeout(mycmd, checkfile = "", mytimeout = 10):
    a = subprocess.Popen(mycmd, stdout=subprocess.PIPE, shell=True)
    starttime = time.time()
    if checkfile != "":
        while os.path.isfile(checkfile)==False:
           time.sleep(0.5)
    while a.poll():
        if (time.time() - starttime) > mytimeout:
            time.sleep(1)
            break
        else:
            time.sleep(0.5)
    try:
        subprocess.Popen.kill(a)
    except:
        #os.killpg(os.getpgid(a.pid), signal.SIGTERM)
        pass

def loadRegexFromTSV(fileName):
    global allregex
    allregex = []
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.split('\t')
            if len(row) == 3:
                allregex.append(row)

def loadFromTSV(fileName):
    table = []
    if not os.path.isfile(fileName):
        return table
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.split('\t')
            if len(row)>0:
                table.append(row)
    return table


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
    loadBranData()
    app.run(debug=True, host='0.0.0.0', port=int("80"), threaded=True)
