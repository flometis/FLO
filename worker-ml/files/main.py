#!/usr/bin/python3

#https://python.langchain.com/docs/concepts/embedding_models/
import os
import sys
import json

from flask import Flask
from flask import request
from flask import make_response


import numpy as np

from langchain_huggingface import HuggingFaceEmbeddings



EMBEDDING_MODEL_NAMES = os.environ.get('EMBEDDING_MODEL_NAME', "all-MiniLM-L6-v2,ArchitRastogi/bert-base-italian-embeddings,sentence-transformers/distiluse-base-multilingual-cased-v2,dbmdz/bert-base-italian-xxl-uncased,nickprock/sentence-bert-base-italian-uncased,GroNLP/gpt2-medium-italian-embeddings")
HUGGING_FACE_EMBEDDINGS_DEVICE_TYPE = os.environ.get('HUGGING_FACE_EMBEDDINGS_DEVICE_TYPE',"cpu")


doc_srcfile = "../worker/Bran/dizionario/vdb2016.txt"

app = Flask(__name__)

embeddings_models = {}
vocabularies = {}

def loadModels():
    embeddings_models = {}
    for EMBEDDING_MODEL_NAME in EMBEDDING_MODEL_NAMES.split(','):
        embeddings_models[EMBEDDING_MODEL_NAME] = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': os.environ.get('HUGGING_FACE_EMBEDDINGS_DEVICE_TYPE', "cpu")},  #cpu only
            encode_kwargs={
                'normalize_embeddings': True  # keep True to compute cosine similarity
            }
        )
        if EMBEDDING_MODEL_NAME == "GroNLP/gpt2-medium-italian-embeddings":
            #embeddings_models[EMBEDDING_MODEL_NAME].client.tokenizer.pad_token = embeddings_models[EMBEDDING_MODEL_NAME].client.tokenizer.eos_token
            embeddings_models[EMBEDDING_MODEL_NAME]._client.tokenizer.pad_token = embeddings_models[EMBEDDING_MODEL_NAME]._client.tokenizer.eos_token
    return embeddings_models

def embed_vocabulary(srcfile, EMBEDDING_MODEL_NAME):
    documents = []
    text_file = open(srcfile, "r")
    for doc in text_file.readlines():
        documents.append(doc.replace("\n", "").replace("\r", ""))
    text_file.close()

    doc_embeddings = embeddings_models[EMBEDDING_MODEL_NAME].embed_documents(
        documents
    )
    doc_dict = {}
    for d in range(len(documents)):
        doc_dict[documents[d]] = doc_embeddings[d]
    return doc_dict


def loadVocabularies():
    vocabularies = {}
    for EMBEDDING_MODEL_NAME in embeddings_models:
        if "/" in EMBEDDING_MODEL_NAME:
            doc_file = os.path.abspath(os.path.dirname(sys.argv[0])) + "/vdb2016_"+EMBEDDING_MODEL_NAME.replace("/","_")+".json"
        else:
            doc_file = os.path.abspath(os.path.dirname(sys.argv[0])) + "/vdb2016_"+EMBEDDING_MODEL_NAME+".json"
        if os.path.isfile(doc_file):
            print("Loading embedded vocabulary")
            text_file = open(doc_file, "r")
            myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
            text_file.close()
            vocabularies[EMBEDDING_MODEL_NAME] = json.loads(myjson)
        else:
            print("Embedding vocabulary")
            vocabularies[EMBEDDING_MODEL_NAME] = embed_vocabulary(doc_srcfile, EMBEDDING_MODEL_NAME)
            file = open(doc_file,"w", encoding='utf-8')
            file.write(json.dumps(vocabularies[EMBEDDING_MODEL_NAME]))
            file.close()
    return vocabularies



def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)


def get_closest(EMBEDDING_MODEL_NAME, sentence, max_results, subset = []):
    global vocabularies
    global embeddings_models
    embeddings_model = embeddings_models[EMBEDDING_MODEL_NAME]
    embedding = embeddings_model.embed_query(sentence)
    vocabulary = vocabularies[EMBEDDING_MODEL_NAME]
    doc_embeddings = {}
    if subset == []:
        doc_embeddings = vocabulary
    else:
        for voc in vocabulary:
            if voc in subset:
                doc_embeddings[voc] = vocabulary[voc]
    res_list = []
    for voc in doc_embeddings:
        similarity = cosine_similarity(embedding, doc_embeddings[voc])
        #print(voc, "Cosine Similarity:", similarity)
        res_list.append([voc, similarity])
    res_list.sort(key=lambda x: x[1], reverse=True)
    res_dict = {}
    for i in range(max_results):
        if i < len(res_list):
            res_dict[res_list[i][0]] = res_list[i][1]
    return res_dict


## API

@app.route('/')
def index():    
    myjson = "{}"
    return myjson

@app.route('/vdb/embed', methods=['POST'])
def done():
    try:
        word = request.values['word']
        context = request.values['context']
        synonyms = json.loads(request.values['synonyms'])
        max_res = int(request.values['max_res'])
        fullSyn = {}
        #print(word, context, synonyms)
        for EMBEDDING_MODEL_NAME in embeddings_models:
            close_list = get_closest(EMBEDDING_MODEL_NAME, context, max_res, synonyms)
            fullSyn[EMBEDDING_MODEL_NAME] = close_list
        resp = make_response({"word": word, "close_words": fullSyn})
    except:
        resp = make_response({})
    return resp

## Main

embeddings_models = loadModels()
vocabularies = loadVocabularies()


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int("80"), threaded=True)



