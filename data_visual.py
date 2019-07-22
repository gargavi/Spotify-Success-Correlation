import sqlalchemy as alch
import pandas as pd
import pymysql as psql
import matplotlib.pyplot as plt
#reading databases
from parameters import user, password, small_genre_dict, host, genres

conn = psql.connect(host=host, user=user, password=password)
connection = alch.create_engine("mysql+pymysql://" + user + ':' + password + '@localhost/' + "genre")

pandas_dataframes = {}

for key in small_genre_dict.keys():
    album_df = pd.read_sql_table(key.replace(" ", "_"), connection, index_col='Song')
    artist_database = pd.read_sql_table(str(key.replace(" ", "_")) + "_artists", connection, index_col= "Artist")
    pandas_dataframes[key] = [album_df, artist_database]

#this section deals with plotting the total genre's in one entire section

fig, axes  = plt.subplots(1, 2, figsize= (20.0, 10.0), sharey = True)

for title, df_list in pandas_dataframes.items():
    axes[0].scatter(df_list[0]["lyrics"], df_list[0]["success"])
    axes[1].scatter(df_list[0]["tempo"], df_list[0]["success"])

print(axes)
input()
fig.legend(labels = pandas_dataframes.keys())
axes[0].title.set_text("Tempo")
axes[1].title.set_text("Lyrics")
fig.suptitle("Genre Comparison")

#next step is that we want to compare each genre to the artists complete inside of it
    #need to add colors, axis labels, bigger font titles, making it generally more attractive looking graphs

for genre, df_list in pandas_dataframes.items():
    x_coor = 0
    y_coor = 0
    lyr_fig, lyr_axes = plt.subplots(4,4, figsize = (20.0, 10.0), sharex = True, sharey = True)
    suc_fig, suc_axes = plt.subplots(4, 4, figsize= (20.0, 10.0), sharex = True, sharey = True)
    lyr_axes[x_coor][y_coor].scatter(df_list[0]["lyrics"], df_list[0]["success"])
    lyr_axes[x_coor][y_coor].title.set_text("Total Genre")
    suc_axes[x_coor][y_coor].scatter(df_list[0]["tempo"], df_list[0]["success"])
    suc_axes[x_coor][y_coor].title.set_text("Total Genre")
    artist_database = df_list[1]
    for index, row in artist_database.iterrows():
        if x_coor < 3:
            x_coor += 1
        else:
            y_coor += 1
            x_coor = 0
        try:
            lyric_axes = lyr_axes[x_coor][y_coor]
            success_axes = suc_axes[x_coor][y_coor]
            temp_connect = alch.create_engine("mysql+pymysql://" + user + ':' + password + '@localhost/' + index)
            complete_artist = pd.read_sql_table("complete", temp_connect, index_col = "Song")
            lyric_axes.scatter(complete_artist["lyrics"], complete_artist["success"])
            success_axes.scatter(complete_artist["tempo"], complete_artist["success"])
        except Exception as e:
            print(index + " failed because " + str(e))
        lyric_axes.title.set_text(index.replace("_", " "))
        success_axes.title.set_text(index.replace("_", " "))

    lyr_fig.suptitle("Lyrical Comparsion for " + genre)
    suc_fig.suptitle("Tempo Comparsion for " + genre)

for genre, df_list in pandas_dataframes.items():
    #first need to get each artist and then get each album they have and create a corresponding subplot axis list for it
    subplot_dict = {'1': [1, 1], '2': [1, 2], '3': [1,3], '4': [2, 2], '5': [2, 3], '6': [2,3], '7': [2,4], '8': [2,4], '9': [3,3],
                    '10': [2,5], '11':[3,4], '12': [3,4]}
    for artist_name, row in df_list[1].iterrows():
        artist_connect = alch.create_enginer("mysql+pymysql://" + user + ":" + password + "@localhost/" + index)
        size = subplot_dict[str(len(row) + 1)]
        artist_fig, artist_axes = plt.subplots(size[0], size[1], figsize = (20.0, 10.0), sharex = True, sharey= True)
        for entry in ["complete"] + row:
            album =



#create a color list to interate over when filling up the colors of a particular figure

plt.show()

