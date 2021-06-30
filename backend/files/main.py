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
allfilters = []
allregex1 = []
allfilters1 = []
allregex2 = []
allfilters2 = []

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
    global allfilters
    global allregex
    global allfilters1
    global allregex1
    global allfilters2
    global allregex3
    global corpuscols
    global ignoretext
    global dimList
    global legendaPos
    if request.method == 'GET':
        myjson = index()
        return myjson

    mytext = request.form['text']
    mytext = re.sub('<(?!\s*\/*\s*br\s*\/*\s*/?>)[^<>]*>','', mytext)

    myRS = request.form['ruleset']

    if myRS == "etr":
        allregex = allregex2
        allfilters = allfilters2
        print("using ruleset 2")
    else:
        allregex = allregex1
        allfilters = allfilters1
        print("using ruleset 1")

    myobj = {"original": "","corrections": []}
    myobj["original"] = mytext

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

    mycol = 1
    try:
    	output = Corpus.core_misure_lessicometriche(mycol, myrecovery)
    except:
        output = ""
    output = sessionfile+"-misure_lessicometriche-token.tsv"
    mis_les = loadFromTSV(output)
    myobj["misure_lessicometriche"] = mis_les 

    mylevel = 2 
    output = sessionfile+"-densitalessicale-" + str(mylevel) + ".tsv"
    execWithTimeout('/var/www/app/Bran/main.py densitalessicale "'+sessionfile+'" '+ str(mylevel) +' n', output, 2)
    dens = loadFromTSV(output)
    mylevel = 1
    output = sessionfile+"-densitalessicale-" + str(mylevel) + ".tsv"
    execWithTimeout('/var/www/app/Bran/main.py densitalessicale "'+sessionfile+'" '+ str(mylevel) +' n', output, 2)
    dens1 = loadFromTSV(output)
    dens.extend(dens1[1:])
    myobj["densita_lessicale"] = dens

    doignpunct = "Y"
    myfilterGulp = "''"
    output = sessionfile+"-gulpease-.tsv"
    execWithTimeout('/var/www/app/Bran/main.py gulpease "'+sessionfile+'" ' + str(doignpunct) + ' ' + str(myfilterGulp) +' n', output, 2)
    gulp = loadFromTSV(output)
    myobj["gulpease"] = gulp

    rebuiltText, tokenList = rebuildText(sessionfile)
    myobj["original"] = rebuiltText
    
    allcorrs = []

    #myobj["correctionsFilter"] = []
    for myfilter in allfilters:
        mycorrections = findBranFilter(sessionfile, rebuiltText, myfilter[0], myfilter[1], myfilter[2])
        for mycorr in mycorrections:
            #myobj["correctionsFilter"].append(mycorr)
            mycorr["start"] = tokenList[mycorr["start"]][0]
            mycorr["end"] = tokenList[mycorr["end"]][1]
            allcorrs.append(mycorr)

    Corpus.chiudiProgetto()

    #myobj["correctionsRe"] = []
    for myregex in allregex:
        mycorrections = findRegex(rebuiltText, myregex[0], myregex[1], myregex[2])
        for mycorr in mycorrections:
            #myobj["correctionsRe"].append(mycorr)
            allcorrs.append(mycorr)


    #sort and clean up corrections (avoid nested corrections)
    tmpcorrs = []
    while len(allcorrs)>0:
        smaller = [0,len(rebuiltText)]
        for i in range(len(allcorrs)):
            if allcorrs[i]["start"] < smaller[1]:
                smaller[0] = i
                smaller[1] = allcorrs[i]["start"]
        tmpcorrs.append(allcorrs.pop(smaller[0]))

    myobj["correctionsNested"] = []
    for i in range(len(tmpcorrs)-1):
        try:
            if tmpcorrs[i+1]["start"] < tmpcorrs[i]["end"]:
                myobj["correctionsNested"].append(tmpcorrs.pop(i+1))
        except:
            pass

    #merge close corrections
    for i in range(len(tmpcorrs)-1, 0, -1):
        if tmpcorrs[i]["start"] == (tmpcorrs[i-1]["end"]+1) and tmpcorrs[i-1]["explanation"] == tmpcorrs[i]["explanation"] and tmpcorrs[i-1]["recommendedText"] == tmpcorrs[i]["recommendedText"]:
            tmpcorrs[i-1]["end"] = tmpcorrs[i]["end"]
            tmpcorrs.pop(i)

    myobj["corrections"] = tmpcorrs

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
    tallregex = []
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.split('\t')
            if len(row) == 3:
                tallregex.append(row)
    return tallregex

def loadFiltersFromTSV(fileName):
    tallfilters = []
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.split('\t')
            if len(row) == 3:
                tallfilters.append(row)
    return tallfilters

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

def rebuildText(sessionfile):
    fulltext = ""
    tokenTable = [] #for every token, start and end char
    mycorpus = loadFromTSV(sessionfile)
    mycol = 1 #token
    for row in mycorpus:
        tstart = len(fulltext)
        fulltext = fulltext + row[mycol] + " "
        fulltext = remUselessSpaces(fulltext) 
        if fulltext[tstart-1] != " ":
            tstart = tstart - 1
        if fulltext[-1] != " ":
            fulltext = fulltext + " "
        tend = tstart + len(row[mycol]) #len(fulltext)-1
        tokenTable.append([tstart,tend])
    return (fulltext, tokenTable)

def remUselessSpaces(tempstring):
    punt = " (["+re.escape(".,;!?)")+ "])"
    tmpstring = re.sub(punt, "\g<1>", tempstring, flags=re.IGNORECASE)
    punt = "(["+re.escape("'’(")+ "]) "
    tmpstring = re.sub(punt, "\g<1>", tmpstring, flags=re.IGNORECASE|re.DOTALL)
    return tmpstring

def findBranFilter(sessionfile, mytext, filtertext, recommendedText, explanation):
    # /var/www/app/Bran/main.py cerca /tmp/Bran/tmp52vjhuco/testo-bran.tsv 1 "pos[2]=A.*&&lemma[-1]=o.*" n
    mycorrections = []
    hkey = "token"
    mycol = 1
    cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", filtertext)
    output = sessionfile + "-cerca-" + hkey + "-filtro-" + cleanedfilter + ".tsv"
    print('/var/www/app/Bran/main.py cerca "'+sessionfile+'" '+ str(mycol) + ' "' + filtertext +'" n')
    print(output)
    execWithTimeout('/var/www/app/Bran/main.py cerca "'+sessionfile+'" '+ str(mycol) + ' "' + filtertext +'" n', output, 4)
    res = loadFromTSV(output)
    print(res)
    for i in range(len(res)):
        if i == 0:
            continue
        mycorr = {"start": 0, "end": 0, "recommendedText": "", "explanation": ""}
        mycorr["start"] = int(res[i][1])
        mycorr["end"] = int(res[i][2])
        mycorr["recommendedText"] = recommendedText.replace("\n","").replace("\\n","")
        mycorr["explanation"] = explanation
        mycorrections.append(mycorr)
    return mycorrections


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
    allregex1 = loadRegexFromTSV(os.path.abspath(os.path.dirname(sys.argv[0]))+"/regex_plain.tsv")
    allfilters1 = loadFiltersFromTSV(os.path.abspath(os.path.dirname(sys.argv[0]))+"/filters_plain.tsv")
    allregex2 = loadRegexFromTSV(os.path.abspath(os.path.dirname(sys.argv[0]))+"/regex_etr.tsv")
    allfilters2 = loadFiltersFromTSV(os.path.abspath(os.path.dirname(sys.argv[0]))+"/filters_etr.tsv")

    loadBranData()
    app.run(debug=True, host='0.0.0.0', port=int("80"), threaded=True)
