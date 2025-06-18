# UniqueWordCrawler
Python based web crawler that stores a list of all unique words that it comes across and 
stores the number of occurences for any given word. It stores the result in a .bin file wich is a created from pickle.dumps so to use it use pickle.loads.

### Extra infomation

Currently it only looks at links to wikipedia to stop it venturing to dodgy sites.
Does accept words which have numbers in them, and one can decide which alphabet for example say if one wanted only words written in the german alphabet. 
