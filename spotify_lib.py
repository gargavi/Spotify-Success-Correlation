import numpy as np
import requests
from bs4 import BeautifulSoup
#credit to Will Soares for online API code for GENIUS

def get_popularity(track_id, sp):
    #gets popularity of a single song given its track_id and an spotipy object
    #Arguments:
        #track_id = String, uri of a track
        #sp = Spotify class object created by Spotipy library
    return sp.track(track_id)['popularity']

def get_artist_name(album_id, sp):
    #gets the name of the primary artist given the album name
    #Arguments:
        #album_id = String, uri of an album
        #sp = Spotify class object created by Spotipy library
    return sp.album(album_id)['artists'][0]['name']

def get_album_dicography(artist_id, sp):
    #gets the entire discography (without repeats) of an artist given their artist_id
    #Arguments:
        #artist_id = String, uri of an artist
        #sp = Spotify class object created by Spotipy library
    albums = sp.artist_albums(artist_id, album_type = 'album', country = 'US')['items']
    album_disc = {}
    for album in albums:
        album_name = album['name']
        if album_name not in album_disc.keys():
            id = album['id']
            album_disc[album_name] = id

    return album_disc

def get_album_popularity(album_id, sp):
    #returns the overall popularity of an album
    #Arguments:
        #album_id = String, uri of an album
        # sp = Spotify class object created by Spotipy library
    return sp.album(album_id)['popularity']

def get_album_type(album_id, sp):
    return sp.album(album_id)['type']

def get_artist_disc_popularity(artist_id, sp):
    #returns a dictionary with the name of the artist's albums and the popularity of each album
    #Arguments
        # #artist_id = String, uri of an artist
        # sp = Spotify class object created by Spotipy library
    album_disc = get_album_dicography(artist_id, sp)
    popularity_dict = {}
    for item in album_disc.items():
        popularity_dict[item[0]] = get_album_popularity(item[1], sp)
    return popularity_dict

def get_album_songs(album_id, sp):
    #gets all the songs of a single album
    #Arguments;
        #album_id = String, uri of an album
        # sp = Spotify class object created by Spotipy library
    song_dict = {}
    for song in sp.album_tracks(album_id)['items']:
        song_dict[song['name']]= song['id']
    return song_dict

def get_song_pop(track_id, sp):
    #gets the popularity of a single song (detemrined by spotify)
    #Arguments:
        #track_id = String, uri of a track
        # sp = Spotify class object created by Spotipy library
    return sp.track(track_id)['popularity']

def album_song_pop(album_id, sp):
    #returns a dictionary with the name of the song as a key and the popularity of it given an album
    #Arguments:
        #album_id = String, uri of an album
        # sp = Spotify class object created by Spotipy library
    song_dict = get_album_songs(album_id, sp)
    pop_dict = {}
    for song in song_dict.items():
        pop_dict[song[0]] = get_song_pop(song[1], sp)
    return pop_dict

def z_score_album(album_id, sp):
    #given an album, return a dictionary of every song and the z-score of the song's popularity
    # Arguments:
        # album_id = String, uri of an album
        # sp = Spotify class object created by Spotipy library
    pop_dict = album_song_pop(album_id, sp)
    z_dict = {}
    mean = np.mean(list(pop_dict.values()))
    st_dev = np.std(list(pop_dict.values()))
    for song in pop_dict.items():
        z_dict[song[0]] = (song[1] - mean) / st_dev
    return z_dict

def tempo_song(track_id, sp):
    #gives a song's tempo
    # Arguments:
        # track_id = String, uri of a track
        # sp = Spotify class object created by Spotipy library
    return sp.audio_features(track_id)[0]['tempo']

def tempo_album(album_id, sp):
    #gives a dictionary for every song in an album with the name as the key and the tempo of song as value
    # Arguments:
        # album_id = String, uri of an album
        # sp = Spotify class object created by Spotipy library
    song_dict = get_album_songs(album_id, sp)
    temp_dict = {}
    for song in song_dict.items():
        temp_dict[song[0]] = tempo_song(song[1], sp)
    return temp_dict

def request_song_info(song_title, artist_name, token):
    #the first part of starting the Genius API search form (modified from William Soares article)
    #Arguments:
        #song_title = String, title of the song as close as it is written in general context
        #artist_name = String, name of the artist as close as it is written in general context
        #token = Genius Token for access to its  API
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + token}
    search_url = base_url + '/search'
    data = {'q': song_title + ' ' + artist_name}
    response = requests.get(search_url, data=data, headers=headers)
    return response

def helper_lyric_retrieval(song_title, artist_name, token):
    #helper function to get the lyrics for a song of of Genius
    #Arguments:
        #song_title = String, title of the song as close as it is written in general context
        #artist_name = String, name of the artist as close as it is written in general context
        #token = Genius Token for access to its API
    response = request_song_info(song_title, artist_name, token)
    json = response.json()
    for hit in json['response']['hits']:
        if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
            remote_song_info = hit
            return remote_song_info

def lyric_retrieval(song_title, artist_name, token):
    #function to get the lyrics for a song off of Genius utilizing a search query (needs internet connection)
    song_info = helper_lyric_retrieval(song_title, artist_name, token)
    if song_info:
        url = song_info['result']['url']
        page = requests.get(url)
        html_object = BeautifulSoup(page.text, 'html.parser')
        lyrics = html_object.find('div', class_ = 'lyrics').get_text()
        return lyrics
    return None


def value_compress(uncompressed):
    #takes a list of lyrics and compresses them down and sees the amount of reduction that the song gets
    #the closer the value is to 0 the more compression the song got (i.e a song wiht 100% repetition would get a
    #return value of .000000000001
    """Compress a string to a list of output symbols."""
    uncompressed = uncompressed.replace("'", "").replace(" ' ", "")
    # Build the dictionary.
    dict_size = 256
    dictionary = dict((chr(i), i) for i in range(dict_size))
    w = ""
    result = []
    for c in uncompressed:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            try:
                result.append(dictionary[w])
            except:
                a = 1
            # Add wc to the dictionary.
            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    # Output the code for w.
    if w:
        result.append(dictionary[w])
    return len(result)/len(uncompressed)

def album_value_compress(album_id, sp, token):
    song_dict = get_album_songs(album_id, sp)
    compress_dict = {}
    for song in song_dict.items():
        lyrics = lyric_retrieval(song[0], get_artist_name(album_id, sp), token)
        if lyrics:
            compress_dict[song[0]] = value_compress(lyrics)
    return compress_dict

def get_related_artists(genre, starting_artist, n, sp):
    #gets the 'top' n artists for any particular genre; in reality this function uses a starting point and gets a list of
    #n artists all of who are related to the artist and share the stated genre.
    #Arguments:
        #genre = string of a genre
        #starting_artist = string of a uri of an artist
        #n = the length of dictionary that you want
        #sp = Spotify object created by Spotipy function
    artist_dict = {}
    if genre not in sp.artist(starting_artist)['genre']:
        return 'ERROR: artist not part of genre'
    def helper_func(artist):
        nonlocal artist_dict
        if len(artist_dict) > n:
            return artist_dict
        if genre in sp.artist(artist)['genres']:
            print(len(artist_dict))
            artist_dict[sp.artist(artist)['name']] = [sp.artist(artist)['id'], sp.artist(artist)['followers']['total']]
            for artist in sp.artist_related_artists(artist)['artists']:
                if artist['name'] not in artist_dict:
                    helper_func(artist['uri'])

    helper_func(starting_artist)
    return artist_dict

def quick_get_top_artists(genre, starting_artist, min_pop, min_follow, n, sp, id=True, follow = True):
    artist_dict = {}
    if genre not in sp.artist(starting_artist)['genres'] or (
            int(sp.artist(starting_artist)['popularity']) < min_pop and sp.artists(starting_artist)['followers']['total'] > min_follow):
        return 'ERROR: artist not relevant enough in genre'
    def helper_func(artist):
        nonlocal artist_dict
        if len(artist_dict) < n:
            if id and follow:
                artist_dict[sp.artist(artist)['name']] = [sp.artist(artist)['id'], sp.artist(artist)['followers']['total']]
            elif follow:
                artist_dict[sp.artist(artist)['name']] = sp.artist(artist)['followers']['total']
            elif id:
                artist_dict[sp.artist(artist)['name']] = sp.artist(artist)['id']
            else:
                artist_dict[sp.artist(artist)['name']] = sp.artist(artist)['popularity']
            related = sp.artist_related_artists(artist)
            for new_artist in related['artists']:
                if new_artist['name'] not in artist_dict and genre in new_artist['genres'] and (
                        new_artist['popularity'] > min_pop or new_artist['followers']['total'] > min_follow):
                    helper_func(new_artist['uri'])
    helper_func(starting_artist)
    return artist_dict

def slow_top_artists(genre, starting_artist, n, sp):
    assert n < 100
    #if n == 1:
        #return quick_get_top_artists(genre, starting_artist, 0, 0, n, sp)
    long_dict = quick_get_top_artists(genre, starting_artist, 0, 0, 1000, sp)
    long_dict2 = dict(long_dict)
    for key, value in long_dict2.items():
        if type(value[1]) != int:
            del long_dict[key]
    top_artist = list(reversed(sorted(long_dict, key = lambda x: long_dict[x][1])))[:n]
    for key in long_dict2.keys():
        if key not in top_artist and key in long_dict:
            del long_dict[key]
    return long_dict


###############################DATA VISUALIZATION FUNCTIONS##############################

