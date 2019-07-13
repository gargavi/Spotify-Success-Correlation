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



def generate_host():
    token = util.prompt_for_user_token(username, scope, CLIENT_ID, CLIENT_SECRET, redirect_uri)
    if token:
        sp = spotipy.Spotify(auth=token)
        print('Generated a Spotify Class Instance')
    else:
        raise ValueError('enter valid credentials')
    return sp

client_credentials_manager = SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET)


def generate_host():
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    print('Generated a Spotify Class Instance')
    return sp


sp = generate_host()

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

#dictionary for popular (not necessarily the top artists for a particular genre



failure_list = {}
def complete_sql_gather(genre, sp):
    #get all the relevant artists
    print(genre + ' started at time ' + str(time.time() - t_start))
    top_artist_dic = slow_top_artists(genre, genre_dict[genre], 10, sp)
    # all the important information to create the SQL connections
    #creating the connection
    conn = psql.connect(host=host, user=user, password=password)
    cursor = conn.cursor()
    #whole - dataframe that'll act as the complete genre dataframe
    whole = pd.DataFrame()
    #artist_album_dict - creates in index table
    artist_album_dict = {}
    for artist, list2 in top_artist_dic.items():
        t_begin = time.time()
        sp1 = generate_host()
        print(artist)
        database = artist.replace(' ', '_').replace('.', '').lower()
        connection = alch.create_engine("mysql+pymysql://" + user + ':' + password + '@localhost/' + database)
        try:
            cursor.execute("USE " + database)
            print("Database Already Existed: Adding Artist Discography to Genre")
            discography = get_album_dicography(list2[0], sp)
            disc_list = list(discography.keys())
            artist_album_dict[database] = disc_list
            for i in range(len(disc_list)):
                try:
                    album_df = pd.read_sql_table(database + str(i + 1), connection, index_col='Song')
                    album_df.index.name = 'Song'
                    whole = pd.concat([whole, album_df], axis=0, sort=False)
                    print('               ' + 'album' +str(i) +': Succeeded ')
                except Exception as e:
                    print("No more Albums recorded for this artist")
                    failure_list[disc_list[i]] = e
        except:
            print("Database Doesn't Exist Yet: Creating Artist Database")
            cursor.execute("CREATE DATABASE IF NOT EXISTS " + database)
            number = 1
            artist_data = get_total_data(list2[0], sp1, False)
            artist_album_dict[database] = list(artist_data.keys())
            print(artist_data.keys())
            winsound.Beep(frequency, duration)
            for album, data in artist_data.items():
                try:
                    answer = input("Should we include " + album + " ? ")
                    table_name = database + str(number)
                    if answer.lower() == "y":
                        album_df = pd.DataFrame.from_dict(data, orient='index', columns=['success', 'tempo', 'lyrics'])
                        album_df.index.name = 'Song'
                        whole = pd.concat([whole, album_df], axis=0, sort=False)
                        album_df.to_sql(table_name, connection, if_exists='replace', dtype={'Song': VARCHAR(25)})
                        if number == 1:
                            album_df.to_sql('complete', connection, if_exists='replace', dtype={'Song': VARCHAR(25)})
                        else:
                            album_df.to_sql('complete', connection, if_exists='append', dtype={'Song': VARCHAR(25)})
                        number += 1
                        print('               ' + album + ': Succeeded ')
                    else:
                        print("Album Rejected For Inclusion")
                except Exception as e:
                    print('               ' + album + ': Failed')
                    failure_list[album] = e
        print('Completed in: ' + str( time.time() - t_begin))
        #album_df.index.get_level_values('Song').str.len().max()
    large_connection = alch.create_engine("mysql+pymysql://" + user + ':' + password + '@localhost/genre')
    concat_genre = genre.replace(" ", "_")
    whole.to_sql(str(concat_genre), large_connection, if_exists='replace', dtype={'Song': VARCHAR(25)})
    a = max([len(val) for val in artist_album_dict.values()])
    for vals in artist_album_dict.values():
        while len(vals) < a:
            vals.append('NULL')

    columns2 = ['album'+str(b)  for b in range(1, a+1)]
    artist_album_df = pd.DataFrame.from_dict(artist_album_dict, orient = 'index', columns = columns2 )
    artist_album_df.index.name = 'Artist'
    artist_album_df.to_sql(str(concat_genre) + '_artists', large_connection, if_exists = 'replace', dtype ={'Artist': VARCHAR(artist_album_df.index.get_level_values('Artist').str.len().max())})
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

#send_to_sql('spotify:artist:73sIBHcqh3Z3NyqHKZ7FOL')
#get_correlation('spotify:artist:73sIBHcqh3Z3NyqHKZ7FOL')