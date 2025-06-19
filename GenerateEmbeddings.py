import json
import ollama
import pickle
from ProgramState import *

f = open("programState.pkl", "rb")
m = pickle.loads(f.read())
f.close()

wordCounter = m.wordCounter

#Removing bad words
freqClip = 300
print("wclen", len(wordCounter))
wordCounter = {k: v for k,v in wordCounter.items() if v > freqClip}
print("wclen after clip", len(wordCounter))
totalWordFreq = sum([wordCounter[word] for word in wordCounter])
print("totalFreq:",totalWordFreq)
outputJson = {}


for idx,word in enumerate(wordCounter):
  freq = wordCounter[word]
  response = ollama.embeddings(
    model="paraphrase-multilingual:278m-mpnet-base-v2-fp16",
    prompt=word
  )
  embedding = response['embedding']
  embedding = [round(e,5) for e in embedding]
  outputJson[word] = {
    "embedding" : embedding,
    "freq" : round(freq / totalWordFreq,7)
  }
  if idx % 30 == 0:
    print(round(idx/len(wordCounter)*100.0,4),"%")
print("SAVING")
f= open("out.json","w", encoding="utf-8")
f.write(json.dumps(outputJson, indent=4))
f.close()
print("Done")