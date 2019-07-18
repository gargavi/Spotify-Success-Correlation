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
    #theoretically should be a 4 X 4 figure with 15 artist plots and 1 genre plot

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


plt.show()

