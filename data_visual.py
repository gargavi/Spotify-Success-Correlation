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
    #make the two elements, two subplots instead of two figures

plt.figure(figsize=(10.0, 10.0))

plt.figure(2, figsize=(10.0, 10.0))

for title, df_list in pandas_dataframes.items():
    plt.figure(1)
    plt.plot(df_list[0]["success"], df_list[0]["lyrics"], ".")
    plt.figure(2)
    plt.plot(df_list[0]["success"], df_list[0]["tempo"], ".")

plt.figure(1)
plt.legend(labels= pandas_dataframes.keys(), loc = "upper right")

plt.figure(2)
plt.legend(labels= pandas_dataframes.keys() ,loc="upper right")





plt.show()

