import spotipy
import spotipy.util as util
import time
from spotify_lib import *
import pymysql as psql
import sqlalchemy as alch
from sqlalchemy.types import VARCHAR
import winsound
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
from parameters import small_genre_dict, host, user, password

genre_dict = small_genre_dict

frequency = 2500  # Set Frequency To 2500 Hertz
duration = 1000  # Set Duration To 1000 ms == 1 second


t_start = time.time()
username = "12123404397"
CLIENT_ID = 'f48bed994e9a4ab9a939688387022cb2'
CLIENT_SECRET = '4a31ad0a2e5540e6a8b0486cc2915ffe'
redirect_uri = 'http://localhost:8888/callback/'

genius_CLIENT_ID = '680DZzGBiTAsQSpHrMT0kYgjXixw5rZdEWX5Vd86IsXJJUXyNL0yo_MlCBI0KGC4'
genius_CLIENT_SECRET = 'IJfQSz7t_THBZBHl0yDVLmgNpC05mt1dPQgJ7XT7zIaO66mvtwEMXBJVHuYeYoO86hwNe-npM2P6ZvpVi8WPig'
genius_TOKEN  = 'VUhhrz0alO59FDXN_L86yRgzkZupQuLBOfwj5xiJYxEXfqsi7dP_7pPaFgPH2X0P'
scope = 'playlist-read-private'


#this function generates a Spotipy Instance via the token method 
def generate_host():
    token = util.prompt_for_user_token(username, scope, CLIENT_ID, CLIENT_SECRET, redirect_uri)
    if token:
        sp = spotipy.Spotify(auth=token)
        print('Generated a Spotify Class Instance')
    else:
        raise ValueError('enter valid credentials')
    return sp

client_credentials_manager = SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET)

#this method generates a Spotipy Instance using a client credentials method -> Doesn't allow user specific access 
def generate_host():
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    print('Generated a Spotify Class Instance')
    return sp

#generate the first instance of a spotify variable
sp = generate_host()

#this take a list of dictionaries and a key and finds all the data in the dicionaries that contain that key and return a list 
#containing all of them 
def get_data(key, dictionaries):
    data_comb = []
    for dict in dictionaries:
        if key in dict:
            data_comb.append(dict[key])
        else:
            data_comb.append(None)
    return data_comb


def get_total_data(artist_id, sp, standard = True):
    #returns a dictionary with the name of the album as a key and a value which is
    ## a dictionary containing each song in the album as a key and the value is a list of z-score, tempo and compression
    #parameters:
        #artist_id = the spotify uri id of an artist
        #sp = a spotipy instance 
        #standard = whether or not we want to success function to be standardized by album or not 
    artist_disc = get_album_dicography(artist_id, sp)
    total_artist_data = {}
    if standard == True:
        prime_function = z_score_album
    else:
        prime_function = album_song_pop

    for item in artist_disc.items():
        z_dict = prime_function(item[1], sp)
        temp_dict = tempo_album(item[1], sp)
        compress_dict = album_value_compress(item[1], sp, genius_TOKEN)
        songs_dict = get_album_songs(item[1], sp)
        song_data_dict = {}
        for song in songs_dict.keys():
            song_data_dict[song[:20]] = get_data(song, [z_dict, temp_dict, compress_dict])
        total_artist_data[item[0]] = song_data_dict
    return total_artist_data

#create a table in genre of every single artist and their albums and use that to iterate

#failure list records all the failures we encounter in the complete_sql_gather iterations 
failure_list = {}
#this helps us to avoid redundancy when iterating over a lot of artists if there is overlap between different genres 
all_artist_albums = {}

def complete_sql_gather(genre, sp):
    t_start = time.time()
    print(genre + ' started at time ' + str(time.time() - t_start))
    top_artist_dic = slow_top_artists(genre, genre_dict[genre], 15, sp) # all the important information to create the SQL connections
    conn = psql.connect(host=host, user=user, password=password) #creating the connection
    cursor = conn.cursor()
    large_connection = alch.create_engine("mysql+pymysql://" + user + ':' + password + '@localhost/genre')
    whole = pd.DataFrame() #whole - dataframe that'll act as the complete genre dataframe
    artist_album_dict = {}
    try:
        all_artist_albums_temp = pd.read_sql_table("all_artist_info", large_connection, index_col="Artist").to_dict('index')
        all_artist_albums= {}
        for key, value in all_artist_albums_temp.items():
            all_artist_albums[key] = value.values()
    except Exception as e:
        print(str(e))
        all_artist_albums ={}
    for artist, list2 in top_artist_dic.items(): #we iterate over all the different artists
        t_begin = time.time()
        sp1 = generate_host() #generate another spotipy instance
        print(artist)
        album_list = []
        database = artist.replace(' ', '_').replace('.', '').replace("-", "_").replace("&", "_").replace("!", "").lower()  #clean up the title as per SQL standards
        connection = alch.create_engine("mysql+pymysql://" + user + ':' + password + '@localhost/' + database)
            #create a connection to the database (doesn't actually check to see if database exists until we call it)
        if database in all_artist_albums:
            print("Database Already Completed: Adding Artist Discography to Genre")
            disc_list = [val for val in all_artist_albums[database] if str(val) != "NULL"]# get the names of all the albums
            artist_album_dict[database] = disc_list #creates a dictionary entry local only to the genre for the index table
            for i in range(len(disc_list)): #iterate through the list and read each corresponding table
                try:
                    album_df = pd.read_sql_table(database + str(i + 1), connection, index_col='Song') #read the sql table
                    album_df.index.name = 'Song' # set the index column
                    whole = pd.concat([whole, album_df], axis=0, sort=False) #append the album to the complete data album
                    print('               ' + 'album' +str(i) +': Succeeded ')
                except Exception as e:
                    print("No more Albums recorded for this artist")
                    failure_list[disc_list[i]] = e
        else:
            try:
                artist_data = get_total_data(list2[0], sp1, False) # get all the information about the artist
                cursor.execute("CREATE DATABASE IF NOT EXISTS " + database)
                number = 1
                print(artist_data.keys()) #print out the names of all the albums to see if it worth to include them
                winsound.Beep(frequency, duration)
                for album, data in artist_data.items():
                    try:
                        answer = input("Should we include " + album + " ? ") #ask whether or not we should include album in analysis
                        table_name = database + str(number)
                        if answer.lower() == "y":
                            album_df = pd.DataFrame.from_dict(data, orient='index', columns=['success', 'tempo', 'lyrics']) # create dataframe
                            album_df.index.name = 'Song'
                            whole = pd.concat([whole, album_df], axis=0, sort=False) #add dataframe to the whole genre dataframe
                            album_df.to_sql(table_name, connection, if_exists='replace', dtype={'Song': VARCHAR(25)}) # sed the info
                            if number == 1:
                                album_df.to_sql('complete', connection, if_exists='replace', dtype={'Song': VARCHAR(25)}) # start artist complete table
                            else:
                                album_df.to_sql('complete', connection, if_exists='append', dtype={'Song': VARCHAR(25)}) #extend artist complete table
                            album_list.append(table_name) #append the name of the album
                            number += 1
                            print('               ' + album + ': Succeeded ')
                        else:
                            print("Album Rejected For Inclusion")
                    except Exception as e:
                        print('               ' + album + ': Failed')
                        failure_list[album] = e
            except Exception as e:
                winsound.Beep(frequency, duration)
                print("Collection of " + database + "Information Failed because " + str(e) )
            all_artist_albums[database] = album_list
            artist_album_dict[database] = album_list

        print('Completed in: ' + str( time.time() - t_begin))
        #album_df.index.get_level_values('Song').str.len().max()
    concat_genre = genre.replace(" ", "_")
    whole.to_sql(str(concat_genre), large_connection, if_exists='replace', dtype={'Song': VARCHAR(25)})
    a = max([len(val) for val in artist_album_dict.values()])
    for vals in artist_album_dict.values():
        print(vals)
        print(type(vals))
        while len(vals) < a:
            vals.append('NULL')
    b = max([len(val) for val in all_artist_albums.values()])


    columns2 = ['album'+str(num)  for num in range(1, a+1)]
    artist_album_df = pd.DataFrame.from_dict(artist_album_dict, orient = 'index', columns = columns2 )
    artist_album_df.index.name = 'Artist'
    artist_album_df.to_sql(str(concat_genre) + '_artists', large_connection, if_exists = 'replace', dtype ={'Artist': VARCHAR(artist_album_df.index.get_level_values('Artist').str.len().max())})
    columns3 = ["album" +str(num) for num in range(1, b+1)]
    all_artist_albums_df = pd.DataFrame.from_dict(all_artist_albums, orient='index', columns = columns3)
    all_artist_albums_df.index.name="Artist"
    all_artist_albums_df.to_sql("all_artist_info", large_connection, if_exists='replace', dtype={"Artist": VARCHAR(all_artist_albums_df.index.get_level_values("Artist").str.len().max())})
    print(genre + ' completed in ' + str(time.time() - t_start))



def get_correlation(artist_id):
    artist_data = get_total_data(artist_id)
    whole = pd.DataFrame()
    for album, data in artist_data.items():
        print(album)
        album_df = pd.DataFrame.from_dict(data, orient = 'index', columns = ['success', 'tempo', 'lyrics'])
        whole = pd.concat([whole, album_df.corr(method = 'pearson')['success'].rename(album)], axis = 1, sort= False)
    print(whole)



for genre, artist in genre_dict.items():
    complete_sql_gather(genre, sp)

print(len(failure_list))

print(time.time() - t_start)

