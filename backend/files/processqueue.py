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

pipepath = "/tmp/Bran/pipe"
branpath = os.path.abspath(os.path.dirname(sys.argv[0]))+'/Bran'

#sys.path.append()
sys.path.append(branpath)
from forms import BranCorpus



allregex = []
allfilters = []
allregex1 = []
allfilters1 = []
allregex2 = []
allfilters2 = []

vdb2016 = []
vdbAdd = []

corpuscols = {}
ignoretext = ""
dimList = []
legendaPos = {}

useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

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
    


def correct(token,request):
    global allfilters
    global allregex
    global allfilters1
    global allregex1
    global allfilters2
    global allregex2
    global corpuscols
    global ignoretext
    global dimList
    global legendaPos
    global vdb2016
    global useragent
   

    total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    print("RAM total,used,free: ", total_memory, used_memory, free_memory)
    if free_memory < 100:  #we should always have at least 100MB free for the rest of the os
        result = {"errors": "RAM"}
        myjson = json.dumps(result)
        print("Not enough memory, stopped.")
        return myjson

    
    mytext = request['text']
    mytext = re.sub('<[^a-z]*?br>', '\n', mytext)
    mytext = re.sub('<.*?>', '', mytext, flags = re.DOTALL)
    mytext = re.sub('\n', '<br>', mytext) 
    #print(mytext)
    mytext = mytext + '\n' #Fix temporaneo: Bran si aspetta una riga vuota alla fine del file

    optin = False
    try:
        tmpoptin = request['optin']
        print("Optin: "+str(tmpoptin))
        if tmpoptin == "true":
            optin = True
    except:
        pass

    myRS = request['ruleset']

    if myRS == "etr":
        allregex = allregex2
        allfilters = allfilters2
        print("using ruleset 2")
    else:
        allregex = allregex1
        allfilters = allfilters1
        print("using ruleset 1")

    myobj = {"original": "","corrections": [], "files":{}, "optin": str(optin)}
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

    execWithTimeout("python3 " + branpath + "/main.py udpipeImport "+origfile+" it-IT n", sessionfile, 10)
    Corpus = BranCorpus.BranCorpus(corpuscols, legendaPos, ignoretext, dimList, tablewidget="cli")
    Corpus.loadPersonalCFG()
    myrecovery = False #"n"
    Corpus.CSVloader([sessionfile])
    Corpus.sessionFile = sessionfile
    
    myobj["files"]["corpus"] = loadFromTXT(sessionfile)

    if optin:
        if not os.path.exists('/var/www/app/BranKeep'):
            os.makedirs('/var/www/app/BranKeep')
        keepdir = tempfile.NamedTemporaryFile(dir="/var/www/app/BranKeep").name
        os.makedirs(keepdir)
        optinfile = keepdir+"/corpus.tsv"
        os.system("cp " +sessionfile+" "+optinfile)

    mycol = 1
    try:
    	output = Corpus.core_misure_lessicometriche(mycol, myrecovery)
    except:
        output = ""
    output = sessionfile+"-misure_lessicometriche-token.tsv"
    mis_les = loadFromTSV(output)
    myobj["misure_lessicometriche"] = mis_les 
    myobj["files"]["misure_lessicometriche"] = loadFromTXT(output)

    mylevel = 2 
    output = sessionfile+"-densitalessicale-" + str(mylevel) + ".tsv"
    execWithTimeout(branpath + '/main.py densitalessicale "'+sessionfile+'" '+ str(mylevel) +' n', output, 2)
    dens = loadFromTSV(output)
    myobj["files"]["densitalessicale2"] = loadFromTXT(output)
    mylevel = 1
    output = sessionfile+"-densitalessicale-" + str(mylevel) + ".tsv"
    execWithTimeout(branpath + '/main.py densitalessicale "'+sessionfile+'" '+ str(mylevel) +' n', output, 2)
    dens1 = loadFromTSV(output)
    dens.extend(dens1[1:])
    myobj["densita_lessicale"] = dens
    myobj["files"]["densitalessicale1"] = loadFromTXT(output)

    doignpunct = "Y"
    myfilterGulp = "''"
    output = sessionfile+"-gulpease-.tsv"
    execWithTimeout(branpath + '/main.py gulpease "'+sessionfile+'" ' + str(doignpunct) + ' ' + str(myfilterGulp) +' n', output, 2)
    gulp = loadFromTSV(output)
    myobj["gulpease"] = gulp
    myobj["files"]["gulpease"] = loadFromTXT(output)
    
    column = 2
    output = sessionfile+"-occorrenze-lemma.tsv"
    execWithTimeout(branpath + '/main.py occorrenze "'+sessionfile+'" ' + str(column) +' n', output, 2)
    occorrenzeLemmi = loadFromTSV(output)
    myobj["lemmi"] = occorrenzeLemmi
    myobj["files"]["lemmi"] = loadFromTXT(output)

    rebuiltText, tokenList = rebuildText(sessionfile)
    myobj["original"] = rebuiltText
    
    allcorrs = []

    #myobj["correctionsFilter"] = []
    for myfilter in allfilters:
        mycorrections = findBranFilter(sessionfile, rebuiltText, myfilter[0], myfilter[1], myfilter[2])
        for mycorr in mycorrections:
            #myobj["correctionsFilter"].append(mycorr)
            if "aux:pass" in myfilter[0] or "expl:impers" in myfilter[0]:
                mycorr["end"] = mycorr["end"]+1
            mycorr["start"] = tokenList[mycorr["start"]][0]
            mycorr["end"] = tokenList[mycorr["end"]][1]
            try:
                mycorr["category"] = myfilter[3]
                if myfilter[3] == "":
                    mycorr["category"] = "generic"
            except:
                mycorr["category"] = "generic"
            allcorrs.append(mycorr)

    Corpus.chiudiProgetto()

    #myobj["correctionsRe"] = []
    for myregex in allregex:
        mycorrections = findRegex(rebuiltText, myregex[0], myregex[1], myregex[2])
        for mycorr in mycorrections:
            #myobj["correctionsRe"].append(mycorr)
            try:
                mycorr["category"] = myregex[3]
                if myfilter[3] == "":
                    mycorr["category"] = "generic"
            except:
                mycorr["category"] = "generic"
            allcorrs.append(mycorr)
    
    myobj["files"]["sinonimi"] = {}
    corpustsv = loadFromTSV(sessionfile)
    for i in range(len(corpustsv)):
        lemma =corpustsv[i][2]
        #fix udpipe errors
        lemma = re.sub("iscere$","ire", lemma)
        if lemma not in vdb2016 and lemma not in vdbAdd and bool(re.match('.*[^a-z].*', lemma))==False and len(lemma)>3:
            mycorr = {}
            mycorr["start"] = tokenList[i][0]
            mycorr["end"] = tokenList[i][1]
            #https://it.wiktionary.org/w/api.php?action=parse&page=retribuzione&format=json&prop=wikitext&formatversion=2
            synonims = []
            S = requests.Session()
            URL = "https://it.wiktionary.org/w/api.php"
            PARAMS = {
                "action": "parse",
                "page": str(lemma),
                "format": "json",
                "prop":"wikitext",
                "formatversion":"2"
            }
            R = S.get(url=URL, params=PARAMS)
            DATA = R.json()
            try:
                wikitxt = DATA["parse"]["wikitext"].replace("\n","")
                myobj["files"]["sinonimi"][str(lemma)] = wikitxt
                synStart = wikitxt.index("{{-sin-}}")
                synEnd = wikitxt.index("{{-", synStart+8)
                synstr = wikitxt[synStart:synEnd]
                synstrclean = re.sub(re.escape("{")+".*?"+re.escape("}"),"",synstr.lower())
                synonims = re.split("]+",re.sub("[^a-z\]]","",synstrclean).replace(" ", ""))
            except:
                synonims = []
            mycorr["recommendedText"] = "Prova a utilizzare "
            mycorr["explanation"] = "La parola " + corpustsv[i][1] + " non è nel Vocabolario di Base"
            mycorr["synonims"] = synonims
            mycorr["category"] = "synonims"
            allcorrs.append(mycorr)

    #sort corrections (avoid nested corrections)
    tmpcorrs = []
    while len(allcorrs)>0:
        smaller = [0,len(rebuiltText)]
        for i in range(len(allcorrs)):
            if allcorrs[i]["start"] < smaller[1]:
                smaller[0] = i
                smaller[1] = allcorrs[i]["start"]
        tmpcorrs.append(allcorrs.pop(smaller[0]))

    #merge close corrections
    for i in range(len(tmpcorrs)-1, 0, -1):
        if bool(tmpcorrs[i]["start"] == (tmpcorrs[i-1]["end"]+1) or tmpcorrs[i]["start"] == tmpcorrs[i-1]["end"]) and tmpcorrs[i-1]["explanation"] == tmpcorrs[i]["explanation"] and tmpcorrs[i-1]["recommendedText"] == tmpcorrs[i]["recommendedText"]:
            tmpcorrs[i-1]["end"] = tmpcorrs[i]["end"]
            tmpcorrs.pop(i)

    #clean up nested corrections
    myobj["correctionsNested"] = []
    nestedCorrectionsPresent = True
    while nestedCorrectionsPresent:
        nestedCorrectionsPresent = False
        for i in range(len(tmpcorrs)-1):
            try:
                if tmpcorrs[i]["category"] == "lunghezza" or tmpcorrs[i]["category"] == "invio":
                    tmpcorrs[i]["end"] = tmpcorrs[i]["start"]
                if tmpcorrs[i+1]["start"] < tmpcorrs[i]["end"]:
                    myobj["correctionsNested"].append(tmpcorrs.pop(i+1))
                    nestedCorrectionsPresent = True
            except:
                #print("Error in correctionsNested")
                pass

    #merge again close corrections
    for i in range(len(tmpcorrs)-1, 0, -1):
        if bool(tmpcorrs[i]["start"] == (tmpcorrs[i-1]["end"]+1) or tmpcorrs[i]["start"] == tmpcorrs[i-1]["end"]) and tmpcorrs[i-1]["explanation"] == tmpcorrs[i]["explanation"] and tmpcorrs[i-1]["recommendedText"] == tmpcorrs[i]["recommendedText"]:
            tmpcorrs[i-1]["end"] = tmpcorrs[i]["end"]
            tmpcorrs.pop(i)

    myobj["corrections"] = tmpcorrs
    
    print(myobj)

    myjson = json.dumps(myobj)
    fileout = '/tmp/Bran/' + token + '/result.json'
    file = open(fileout,"w", encoding='utf-8')
    file.write(myjson)
    file.close()
    print("DONE processing "+token)
    #resp = make_response(myjson)
    #resp.headers['Access-Control-Allow-Origin'] = '*'
    #return resp
    return
    

def execWithTimeout(mycmd, checkfile = "", mytimeout = 10):
    print("Running: "+ str(mycmd))
    redirect = " &> /dev/null"
    a = subprocess.Popen(mycmd + redirect, stdout=subprocess.PIPE, shell=True)
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
            row = line.replace("\n","").split('\t')
            if len(row) == 4:
                tallregex.append(row)
    return tallregex

def loadFiltersFromTSV(fileName):
    tallfilters = []
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.replace("\n","").split('\t')
            if len(row) == 4:
                tallfilters.append(row)
    return tallfilters

def loadFromTSV(fileName):
    table = []
    if not os.path.isfile(fileName):
        print("File not found: "+fileName)
        return table
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            row = line.split('\t')
            if len(row)>0:
                table.append(row)
    return table

def loadFromTXT(fileName):
    try:
        text_file = open(fileName, "r", encoding='utf-8')
        lines = text_file.read()
        text_file.close()
    except:
        lines = ""
    return lines

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
    cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", filtertext)[:50]
    output = sessionfile + "-cerca-" + hkey + "-filtro-" + cleanedfilter + ".tsv"
    #print('/var/www/app/Bran/main.py cerca "'+sessionfile+'" '+ str(mycol) + ' "' + filtertext +'" n')
    #print(output)
    execWithTimeout(branpath + '/main.py cerca "'+sessionfile+'" '+ str(mycol) + ' "' + filtertext +'" n', output, 4)
    res = loadFromTSV(output)
    #print(res)
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
 
    vdb2016 = []
    with open(branpath+"/dizionario/vdb2016.txt", "r", encoding='utf-8') as ins:
        for line in ins:
            vdb2016.append(line.replace("\n", ""))
    vdbAdd = ["dal","il"]
    
    loadBranData()
    #Read from pipe
    while True:
        with open(pipepath) as fifo:
            for line in fifo:
                token = line.replace("\n","")
                print(token)
                filein = '/tmp/Bran/' + token + '/request.json'
                text_file = open(filein, "r")
                myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
                text_file.close()
                request = json.loads(myjson)
                correct(token,request)
    
