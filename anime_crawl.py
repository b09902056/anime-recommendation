# !pip install requests
# !pip install bs4

# !pip install keybert
# !pip install multi_rake
# !pip install summa
# !pip install yake

import requests
from bs4 import BeautifulSoup
import string
import json

import torch
from keybert import KeyBERT
from multi_rake import Rake
from summa import keywords
import yake

min_word = 1
max_word = 1
topN = 5

keybert_model = KeyBERT(model='all-mpnet-base-v2')
rake = Rake(max_words=max_word)
kw_extractor = yake.KeywordExtractor(top=topN, stopwords=None, n=max_word)

url = 'https://myanimelist.net/topanime.php?type=bypopularity&limit='
headers = {'user-agent': 'Mozilla/5.0'}

animes = []
anime_per_page = 50 # max=50
pages = 60 # number of animes = pages * anime_per_page

for page in range(pages):
  url1 = url + str(page*50)
  r1 = requests.get(url1, headers=headers)
  if r1.status_code == requests.codes.ok:
    soup1 = BeautifulSoup(r1.text, 'html.parser')
    animeList = soup1.find_all('tr', class_='ranking-list', limit=anime_per_page)
    for animeI in animeList:
      url2 = animeI.find('a').get('href')
      r2 = requests.get(url2, headers=headers)
      if r2.status_code == requests.codes.ok:
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        anime = {}
        title = soup2.find('h1', class_='title-name h1_bold_none').string
        english_title = soup2.find('p', class_='title-english title-inherit') 
        if english_title != None:
          english_title = english_title.string
        else:
          english_title = title
        #print('title:', title)
        print('english title:', english_title)
        synopsis = soup2.find('p', itemprop='description').text
        synopsis = synopsis[:synopsis.find('[Written')-3]
        synopsis = synopsis.replace('\n', '')
        synopsis = synopsis.replace('\r', ' ')
        synopsis = synopsis.replace('"', '')
        #print('synopsis:', synopsis)

        # keyBert
        if 0:
          keywords1 = keybert_model.extract_keywords(synopsis, keyphrase_ngram_range=(min_word, max_word), stop_words='english', top_n=topN)
          keywords2 = keybert_model.extract_keywords(synopsis, keyphrase_ngram_range=(min_word, max_word), stop_words='english', use_maxsum=True, nr_candidates=20, top_n=topN)
          keywords3 = keybert_model.extract_keywords(synopsis, keyphrase_ngram_range=(min_word, max_word), stop_words='english', use_mmr=True, diversity=0.7, top_n=topN)
          print(list(dict(keywords1).keys()))
          print(list(dict(keywords2).keys()))
          print(list(dict(keywords3).keys()))
        # rake
        if 0:
          keywords4 = rake.apply(synopsis)[:topN]
          print(list(dict(keywords4).keys()))
        # TextRank
        if 0:
          keywords5 = keywords.keywords(synopsis, scores=True)[:topN]
          print(list(dict(keywords5).keys()))
        # yake
        if 1:
          keywords6 = kw_extractor.extract_keywords(synopsis)
          #print([k[0] for k in keywords6])

        synopsis_keyword = [k[0] for k in keywords6]
        print('synopsis keyword:', synopsis_keyword)
        
        genres = soup2.find_all('span', itemprop='genre')
        genres = [g.text for g in genres]
        # demographic = genres.pop()
        #print('genres:', genres)
        #print('demographic:', demographic)

        stats = soup2.find('div', class_='stats-block po-r clearfix')
        for i in range(10):
          className = 'score-label score-' + str(i)
          s = stats.find('div', class_=className)
          if s != None:
            score = float(s.text)
        #print('score:', score)

        rank = stats.find('span', class_='numbers ranked').text
        if rank.find('#') == -1:
          rank = -1
        else:
          rank = int(rank[rank.find('#')+1:])
        #print('rank:', rank)
        popularity = stats.find('span', class_='numbers popularity').text
        popularity = int(popularity[popularity.find('#')+1:])
        #print('popularity:', popularity)

        print()

        anime['title'] = title
        anime['english_title'] = english_title
        anime['synopsis'] = synopsis
        anime['synopsis_keyword'] = synopsis_keyword
        anime['genres'] = genres
        anime['score'] = score
        anime['rank'] = rank
        anime['popularity'] = popularity
        animes.append(anime)

animes_json = json.dumps(animes)
print(len(animes))
with open("./anime-list.json", "w") as outfile:
    outfile.write(animes_json)
