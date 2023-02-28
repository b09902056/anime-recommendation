from elasticsearch import Elasticsearch
import json
import sys
import os
import pickle

##############################################
ELASTIC_PASSWORD = "jAg8JL=khMSu04l+MrAp"

client = Elasticsearch(
    "https://localhost:9200",
    ca_certs="./http_ca.crt",
    basic_auth=("elastic", ELASTIC_PASSWORD),
)
##############################################

with open('anime-list.json') as f:
    data = json.load(f)
dataN = len(data)
# print('dataN =', dataN) # 3000
def no_special(title):
    valid = [' ', ',', '.', "'"]
    title_no_special = ""
    for i in range(len(title)):
        if (not title[i].isalpha()) and (not title[i].isnumeric()) and (title[i] not in valid):
            title_no_special += ' '
        else:
            title_no_special += title[i]
    return title_no_special

def upload_data(id):
    title = data[id]['title']
    title_no_special = no_special(title)
    english_title = data[id]['english_title']
    english_title_no_special = no_special(english_title)

    doc = {
        'title': title,
        'english_title': english_title,
        'title_no_special': title_no_special,
        'english_title_no_special': english_title_no_special,
        'synopsis': data[id]['synopsis'],
        'synopsis_keyword': data[id]['synopsis_keyword'],
        'genres': data[id]['genres'],
        'score': data[id]['score'],
        'rank': data[id]['rank'],
        'popularity': data[id]['popularity']
    }

    resp = client.index(index="anime", id=id, document=doc)
    # print(id, resp['result'])

def upload_all_data():
    print(f'uploading {dataN} data...')
    for i in range(dataN):
        upload_data(i)

def get_data(id):
    return client.get(index="anime", id=id)

def delete_data(id):
    client.delete(index="anime", id=id)
def delete_all_data():
    print(f'deleting {dataN} data...')
    for i in range(dataN):
        delete_data(i)

def search(query, printHit=True):
    resp = client.search(index="anime", query=query, size=10)
    if printHit:
        print("Got %d Hits:" % resp['hits']['total']['value'])
    return resp['hits']['hits']
def recommend():
    sorted_genres = sorted(user_genres.items(), key=lambda x: -x[1]) 
    sorted_theme = sorted(user_theme.items(), key=lambda x: -x[1]) 
    sorted_demographic = sorted(user_demographic.items(), key=lambda x: -x[1])
    query_list = []
    for i in range(min(3, len(sorted_genres))):
        query_list.append(sorted_genres[i][0])
    for i in range(min(3, len(sorted_theme))):
        query_list.append(sorted_theme[i][0])
    for i in range(min(1, len(sorted_demographic))):
        query_list.append(sorted_demographic[i][0])

    if len(query_list) == 0:
        print('score  popularity  title')
        print('-----------------------------------------------')
        for i in range(10):
            score = str(data[i]["score"])
            popularity = str(data[i]["popularity"])
            print(score, end = '   ')
            for j in range(4-len(score)):
                print(' ', end = '')
            print(f"#{popularity}       ", end = '')
            for j in range(4-len(popularity)):
                print(' ', end = '')
            print(data[i]["english_title"])

        return
    query_string = "(" + query_list[0] + ")"
    for i in range(1, len(query_list)):
        query_string += " OR (" + query_list[i] + ")"

    query = {"bool" : {
        "should" : [
            {
            "query_string": {
                "query": query_string,
                "fields": ["genres"]
            }
            },
        ],
        }
    }
    hits = search(query, False)
    print('score  popularity  title')
    print('-----------------------------------------------')
    for hit in hits:
        # print(round(hit['_score'], 4), hit["_source"]["english_title"])
        score = str(hit["_source"]["score"])
        popularity = str(hit["_source"]["popularity"])
        print(score, end = '   ')
        for j in range(4-len(score)):
            print(' ', end = '')
        print(f"#{popularity}       ", end = '')
        for j in range(4-len(popularity)):
            print(' ', end = '')
        print(hit["_source"]["english_title"])

# query = {"bool" : {
#       "should" : [
#         {
#           "query_string": {
#             "query": "girlfriend",
#             "fields": ["english_title"]
#           }
#         },
#       ],
#     }
# }
# hits = search(query)
# for hit in hits:
#     print(round(hit['_score'], 4), hit["_source"]["english_title"])

def add(name):
    name_no_special = no_special(name)
    query = {"bool" : {
        "should" : [
            {
            "query_string": {
                "query": name_no_special,
                "fields": ["english_title_no_special", "title_no_special"]
            }
            },
        ],
        }
    }
    hits = search(query, False)
    for hit in hits:
        if (name == hit["_source"]["english_title"]):
            animeList.add(name)
            score = round(hit["_source"]["score"], 2)
            for genre in hit['_source']['genres']:
                if genre in Genres:
                    if genre in user_genres:
                        user_genres[genre] += score
                    else:
                        user_genres[genre] = score
                    user_genres[genre] = round(user_genres[genre], 2)
                elif genre in Demographic:
                    if genre in user_demographic:
                        user_demographic[genre] += score
                    else:
                        user_demographic[genre] = score
                    user_demographic[genre] = round(user_demographic[genre], 2)
                else:
                    if genre in user_theme:
                        user_theme[genre] += score
                    else:
                        user_theme[genre] = score
                    user_theme[genre] = round(user_theme[genre], 2)

            print(f'Successfully add "{name}"')
            return

    print(f'No anime "{name}". Please input the correct name.')

def remove(name):
    if name not in animeList:
        print(f'"{name}" is not in your list')
    else:
        animeList.remove(name)
        # remove anime from user feature
        name_no_special = no_special(name)
        query = {"bool" : {
            "should" : [
                {
                "query_string": {
                    "query": name_no_special,
                    "fields": ["english_title_no_special", "title_no_special"]
                }
                },
            ],
            }
        }
        hits = search(query, False)
        for hit in hits:
            if (name == hit["_source"]["english_title"]):
                score = round(hit["_source"]["score"], 2)
                for genre in hit['_source']['genres']:
                    if genre in Genres:
                        user_genres[genre] -= score
                        user_genres[genre] = round(user_genres[genre], 2)
                        if user_genres[genre] <= 0:
                            del user_genres[genre]
                    elif genre in Demographic:
                        user_demographic[genre] -= score
                        user_demographic[genre] = round(user_demographic[genre], 2)
                        if user_demographic[genre] <= 0:
                            del user_demographic[genre]
                    else:
                        user_theme[genre] -= score
                        user_theme[genre] = round(user_theme[genre], 2)
                        if user_theme[genre] <= 0:
                            del user_theme[genre]

                print(f'Successfully remove "{name}"')
                return



def ls():
    print(f'{len(animeList)} anime in your list:')
    for name in animeList:
        print(name)

def searchName(name):
    name_no_special = no_special(name)
    query = {"bool" : {
        "should" : [
            {
            "query_string": {
                "query": name_no_special,
                "fields": ["english_title_no_special", "title_no_special"]
            }
            },
        ],
        }
    }
    hits = search(query)
    for hit in hits:
        # print(round(hit['_score'], 4), hit["_source"]["english_title"])
        print(hit["_source"]["english_title"])

def print_userfeature():
    sorted_genres = sorted(user_genres.items(), key=lambda x: -x[1]) 
    sorted_theme = sorted(user_theme.items(), key=lambda x: -x[1]) 
    sorted_demographic = sorted(user_demographic.items(), key=lambda x: -x[1])
    print('Genres:', sorted_genres)
    print('Theme:', sorted_theme)
    print('Demographic:', sorted_demographic)
    query_list = []
    for i in range(min(3, len(sorted_genres))):
        query_list.append(sorted_genres[i][0])
    for i in range(min(3, len(sorted_theme))):
        query_list.append(sorted_theme[i][0])
    for i in range(min(1, len(sorted_demographic))):
        query_list.append(sorted_demographic[i][0])
    print('query list:', query_list)

def save(user_name):
    with open('./users/'+user_name+'/anime.pkl', 'wb') as f:
        pickle.dump(animeList, f)
    with open('./users/'+user_name+'/genres.pkl', 'wb') as f:
        pickle.dump(user_genres, f)
    with open('./users/'+user_name+'/theme.pkl', 'wb') as f:
        pickle.dump(user_theme, f)
    with open('./users/'+user_name+'/demographic.pkl', 'wb') as f:
        pickle.dump(user_demographic, f)
    print(f'User {user_name} saved')


Demographic = {'Josei', 'Kids', 'Seinen', 'Shoujo', 'Shounen'}
Genres = {'Action', 'Adventure', 'Avant Garde', 'Award Winning', 'Boys Love',
            'Comedy', 'Drama', 'Fantasy', 'Girls Love', 'Gourmet',
            'Horror', 'Mystery', 'Romance', 'Sci-Fi', 'Slice of Life',
            'Sports', 'Supernatural', 'Suspense'}



if not os.path.exists('./users'):
    os.mkdir('./users')
print('Login')
user_name = input("User Name: ")

animeList = set()
user_genres = {}
user_theme = {}
user_demographic = {}
if os.path.exists('./users/' + user_name):
    with open('./users/'+user_name+'/anime.pkl', 'rb') as f:
        animeList = pickle.load(f)
    with open('./users/'+user_name+'/genres.pkl', 'rb') as f:
        user_genres = pickle.load(f)
    with open('./users/'+user_name+'/theme.pkl', 'rb') as f:
        user_theme = pickle.load(f)
    with open('./users/'+user_name+'/demographic.pkl', 'rb') as f:
        user_demographic = pickle.load(f)
else:
    os.mkdir('./users/' + user_name)


while 1:
    Input = input("$ ")
    if Input.find(' ') == -1:
        if Input == 'exit':
            sys.exit()
        elif Input == 'ls':
            ls()
        elif Input == 'recommend':
            recommend()
        elif Input == 'save':
            save(user_name)
        else:
            print('wrong instruction') 

    else:
        type = Input[:Input.find(' ')]
        name = Input[Input.find(' ')+1:]

        if type == 'search':       
            searchName(name)
        elif type == 'add':
            add(name)
        elif type == 'remove':
            remove(name)
        elif type == 'user' and name == 'feature':
            print_userfeature()
        elif type == 'elasticsearch' and name == 'upload':
            upload_all_data()
        elif type == 'elasticsearch' and name == 'delete':
            delete_all_data()
        else:
            print('wrong instruction')

    print()
