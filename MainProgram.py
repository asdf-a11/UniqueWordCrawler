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
MAX_PAGES_TO_VISIT = 300_000

from ProgramState import *

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

