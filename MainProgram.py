import requests
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urljoin, urlparse
import re
import multiprocessing
from multiprocessing import Manager, Lock
import time
import pickle

SAVE_EVERY = 10 * 60
PS_SAVE_FILE = "programStateRU.pkl"
INFO_EVERY = 1 * 60
BATCH = 100
NUM_WORKERS = multiprocessing.cpu_count()
MAX_LINKS = BATCH * NUM_WORKERS + 100

class ProgramState():
  def __init__(self):
    self.wordCounter = Counter()
    self.toVisit = [r"https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0"]
    self.visited = [] 
    self.LANG = "ru"
  def Run(self):
    m = multiprocessing.Manager()
    rq = m.Queue()
    saveStartTimer = time.time()
    infoStartTimer = time.time()
    while True:
      pList = []
      startTime = time.time()
      for coreId in range(NUM_WORKERS):
        linkList = self.toVisit[:BATCH]
        self.toVisit = self.toVisit[BATCH:]
        self.visited += linkList
        #If empty create no more processes
        if not linkList: break
        p = multiprocessing.Process(target=self.Worker, args=(rq, coreId, linkList))
        p.start()
        pList.append(p)
      for p in pList:
        p.join()      
      for _ in range(len(pList)):
        wc, newLinks = rq.get()
        self.wordCounter.update(wc)
        for url in newLinks:
          if len(self.toVisit) >= MAX_LINKS:
            break
          if url not in self.toVisit and url not in self.visited:
            self.toVisit.append(url)
      endTime = time.time()
      #Perodical save self
      if time.time() - saveStartTimer >= SAVE_EVERY:
        saveStartTimer = time.time()
        print("SAVING STATE")
        f = open(PS_SAVE_FILE, "wb")
        f.write(pickle.dumps(self))
        f.close()
        #So dont save multiple times in same second
      #Perodically print infomation
      if time.time() - infoStartTimer >= INFO_EVERY:
        infoStartTimer = time.time()
        print("\n--INFO--")
        print("toVisit,",len(self.toVisit), "visited",len(self.visited), "wcLength", len(self.wordCounter),
        "least common", self.wordCounter.most_common()[:-5-1:-1], "most common", self.wordCounter.most_common(5))
        print("Time per batch", endTime - startTime, " Untill next save ", SAVE_EVERY - (time.time() - saveStartTimer))
  def Worker(self,rq, coreId, linkList):
    def is_valid_link(href):
      if not href:
        return False
      if not href.startswith("/wiki/"):
        return False
      if ':' in href:  # Skip special pages
        return False
      #if self.LANG not in href:
      #  return False
      return True
    def SplitCamleCase(text):
      LATIN_UPPER = r"A-Z"
      LATIN_LOWER = r"a-z"
      CYRILLIC_UPPER = r"А-ЯЁ" # Ё is U+0401, not in A-Я (U+0410-U+042F)
      CYRILLIC_LOWER = r"а-яё" # ё is U+0451, not in а-я (U+0430-U+044F)

      # Combined character classes for any letter (upper or lower, Latin or Cyrillic)
      #ANY_LETTER = f"[{LATIN_UPPER}{LATIN_LOWER}{CYRILLIC_UPPER}{CYRILLIC_LOWER}]"
      LOWER_CASE_ONLY = f"[{LATIN_LOWER}{CYRILLIC_LOWER}]"
      UPPER_CASE_ONLY = f"[{LATIN_UPPER}{CYRILLIC_UPPER}]"


      # Pattern adapted without \p{}
      # ^                     - Start of the word
      # {ANY_LETTER}          - First character, any letter
      # {LOWER_CASE_ONLY}* - Zero or more lowercase letters
      # {UPPER_CASE_ONLY}     - One uppercase letter (the inner capital)
      # {ANY_LETTER}* - Zero or more any letters till the end
      # $                     - End of the word
      #pattern = rf"^{ANY_LETTER}{LOWER_CASE_ONLY}*{UPPER_CASE_ONLY}{ANY_LETTER}*$"

      # In this case, re.U is not strictly necessary for explicit ranges like [A-Z], [а-я]
      # but it doesn't hurt and is good practice if mixing with other Unicode-aware patterns.
      #return re.search(pattern, text, flags=re.U) is not None
      #return re.sub(rf'({ANY_LETTER}{LOWER_CASE_ONLY})({UPPER_CASE_ONLY}{ANY_LETTER})', r'\1 \2',text,flags=re.U)
      #return re.split(rf'(?={UPPER_CASE_ONLY})', text)
      return re.sub(rf'({LOWER_CASE_ONLY})({UPPER_CASE_ONLY})', r'\1 \2', text)


    def extract_links_and_words(url):
      try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
          return set(), Counter()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Extract links
        links = set()
        for a in soup.find_all("a", href=True):
          href = a['href']
          if is_valid_link(href):
            full_url = urljoin(url, href)
            links.add(full_url)
        # Extract words
        text = soup.get_text()
        if self.LANG == "en":
          validLetterRange = r'[a-z]'
        elif self.LANG == "ru":
          validLetterRange = r'[\u0430-\u044f\u0451]'
        else:
          print("Invalid language ", self.LANG)
        words = re.findall(r'\b'+validLetterRange+r'+\b', SplitCamleCase(text).lower())
        #for idx in range(len(words)-1, -1, -1):
        #  if hasInnerCapital(words[idx]):
        #    words.pop(idx)
        word_counts = Counter(words)
        return links, word_counts
      except Exception as e:
        print("Error occured when trying to fetch url=",url, "E = ",e)
        return set(), Counter()
    try:
      #print("Starting")
      toVisit = []
      wc = Counter()
      for url in linkList:
        links, words = extract_links_and_words(url)
        toVisit += links
        wc.update(words)
      rq.put((wc, toVisit))
      #print("Done")
    except:
      print("Process has incured an exception!!!!")
      #So program does not stall
      rq.put((Counter(), []))

if __name__ == "__main__":
  
  ps = None
  try:
    f = open(PS_SAVE_FILE, "rb")
    ps = pickle.loads(f.read())
    f.close()
  except:
    print("Failed to load program state so starting a new press enter to continue")
    input()
    ps = ProgramState()

  ps.Run()

