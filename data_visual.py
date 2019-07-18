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

fig, axes  = plt.subplots(2, 1, figsize= (15.0, 10.0), sharex = True)

for title, df_list in pandas_dataframes.items():
    axes[0].scatter(df_list[0]["success"], df_list[0]["lyrics"])
    axes[1].scatter(df_list[0]["success"], df_list[0]["tempo"])


fig.legend(labels = pandas_dataframes.keys())





plt.show()

