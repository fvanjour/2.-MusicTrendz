from django.shortcuts import render
# from django.http import HttpResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

playlist_id_global = "37i9dQZEVXbMDoHDwVN2tF"
playlist_id_sweden = "37i9dQZEVXbLoATJ81JYXz"


def get_spotify_instance():
    """Creates a connection to Spotify API and returns an instance of Spotify class"""

    # Set up credentials by obtaining a client ID and client secret from the Spotify Developer Dashboard
    client_id = '37a0f04e90f54ea38ff06ba7473d8ffd'
    client_secret = 'd904795e86c5486da53db07dd05991ac'

    # Create an instance of the spotipy.Spotify class and authenticate using credentials
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify_instance = spotipy.Spotify(auth_manager=auth_manager)

    return spotify_instance


sp = get_spotify_instance()


def home(request):
    """Renders Home Page and returns list of dictionaries for """

    playlist_tracks_global = get_playlist_tracks(playlist_id_global, sp)
    playlist_tracks_sweden = get_playlist_tracks(playlist_id_sweden, sp)
    return render(request, 'home.html',
                  {'playlist_id_global': playlist_id_global, 'playlist_tracks_global': playlist_tracks_global,
                   'playlist_id_sweden': playlist_id_sweden, 'playlist_tracks_sweden': playlist_tracks_sweden})


def artist(request, artist_id):
    """Render Artist Page and return dictionary of artist details and list of dictionaries of top tracks"""
    artist_details = get_artist_details(artist_id, sp)
    artist_top_tracks = get_artist_top_tracks(artist_id, sp)
    return render(request, 'artist.html', {'artist_details': artist_details, 'artist_top_tracks': artist_top_tracks})


def album(request, album_id):
    """Render Album Page and return dictionary of album details"""
    album_details = get_album_details(album_id, sp)
    return render(request, 'album.html', {'album_details': album_details})


def track(request, track_id):
    """Render Track Page and return dictionary of track details"""
    track_details = get_track_details(track_id, sp)
    audio_features = get_audio_features(track_id, sp)
    return render(request, 'track.html', {'track_details': track_details, 'audio_features': audio_features})


def analysis(request):
    """Render Analysis Page """

    # Top Artists plot

    global_artists = get_playlist_artists(playlist_id_global, sp)
    df_global_artists = pd.DataFrame(global_artists, columns=["Artist"])
    gvalue_counts = df_global_artists.value_counts().reset_index()
    gvalue_counts.columns = ['Artist', '# of Songs']
    gvalue_counts = gvalue_counts.loc[gvalue_counts["# of Songs"] > 1]

    sweden_artists = get_playlist_artists(playlist_id_sweden, sp)
    df_sweden_artists = pd.DataFrame(sweden_artists, columns=["Artist"])
    svalue_counts = df_sweden_artists.value_counts().reset_index()
    svalue_counts.columns = ['Artist', '# of Songs']
    svalue_counts = svalue_counts.loc[svalue_counts["# of Songs"] > 1]

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))

    ax1 = sns.barplot(y='Artist', x='# of Songs', data=gvalue_counts, ax=axes[0])
    axes[0].set_title('Global')
    for index, value in enumerate(gvalue_counts["# of Songs"]):
        ax1.text(value, index, str(value), color='black', ha="left", va="center", fontsize=10)

    ax2 = sns.barplot(y='Artist', x='# of Songs', data=svalue_counts, ax=axes[1])
    axes[1].set_title('Sweden')
    for index, value in enumerate(svalue_counts["# of Songs"]):
        ax2.text(value, index, str(value), color='black', ha="left", va="center", fontsize=10)

    fig.suptitle('Top Artists within the Top 50 Songs', fontsize=16)
    plt.tight_layout()
    fig.subplots_adjust(top=0.88)
    fig.savefig('hello/static/plot1.png')

    # Audio Features plots

    playlist_tracks_global = get_playlist_tracks(playlist_id_global, sp)
    playlist_tracks_sweden = get_playlist_tracks(playlist_id_sweden, sp)

    global_list = [i["ID"] for i in playlist_tracks_global]
    sweden_list = [i["ID"] for i in playlist_tracks_sweden]

    audio_features_global = get_audio_features(global_list, sp)
    audio_features_sweden = get_audio_features(sweden_list, sp)

    df_global = pd.DataFrame(audio_features_global)
    df_sweden = pd.DataFrame(audio_features_sweden)

    df_global.drop(columns="Track ID", inplace=True)
    df_sweden.drop(columns="Track ID", inplace=True)

    df_global["Region"] = "Global"
    df_sweden["Region"] = "Sweden"

    df_combined = pd.concat([df_global, df_sweden], ignore_index=True)

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 8))

    sns.barplot(x='Region', y="Valence", data=df_combined, ax=axes[0, 0])
    axes[0, 0].set_title('Valence')

    sns.barplot(x='Region', y="Tempo", data=df_combined, ax=axes[0, 1])
    axes[0, 1].set_title('Tempo')

    sns.violinplot(x='Region', y="Danceability", data=df_combined, ax=axes[1, 0])
    axes[1, 0].set_title('Danceability')

    sns.boxplot(x='Region', y="Energy", data=df_combined, ax=axes[1, 1])
    axes[1, 1].set_title('Energy')

    fig.suptitle('Audio Features comparison', fontsize=16)
    plt.tight_layout()
    fig.subplots_adjust(top=0.88)
    fig.savefig('hello/static/plot2.png')

    return render(request, 'analysis.html')


def get_playlist_tracks(playlist_id, spotify_instance, limit=None):
    """Fetches the track ids based on the playlist id. Returns a list of dictionaries of playlist details"""

    # Fetch the json data using Spotify API

    results = spotify_instance.playlist_items(playlist_id, limit=limit)

    # Create empty list to store the extracted information
    track_ids = []

    # Iterate over the playlist items and extract the track ids
    for item in results['items']:
        track1 = item['track']
        track_dict = {"ID": track1["id"], "Name": track1["name"],
                      "Duration": milliseconds_to_min_sec(track1["duration_ms"]), "Artists": [],
                      "AlbumID": track1["album"]["id"], "Image": track1["album"]["images"][2]["url"]}
        ctr = 0
        for artist1 in track1["artists"]:
            track_dict["Artists"].append((artist1["id"], artist1["name"]))
            ctr += 1
        if ctr == 1:
            track_dict["Artists"] = (track1["artists"][0]["id"], track1["artists"][0]["name"])
        track_ids.append(track_dict)

    return track_ids


def get_artist_details(artist_id, spotify_instance):
    """Fetches the artist details based on artist id. Returns a dictionary of artist details"""

    # Fetch the json data using Spotify API
    results = spotify_instance.artist(artist_id)

    # Create dictionary to store the extracted information
    artist_details = {"ID": artist_id, "Name": results["name"], "Popularity": results["popularity"],
                      "Followers": int_to_kmb(results["followers"]["total"]), "Genres": results["genres"],
                      "URL": results["external_urls"]["spotify"], "Images": results["images"]}

    return artist_details


def get_artist_top_tracks(artist_id, spotify_instance):
    """Fetches the top tracks based on the artist id. Returns a list of dictionaries of track ids and track name"""

    # Fetch the json data using Spotify API
    results = spotify_instance.artist_top_tracks(artist_id)

    # Create empty list to store the extracted information
    top_tracks_details = []

    # Iterate over the top tracks data and extract the track ids
    for top_track in results['tracks']:
        track_dict = dict()
        track_dict["ID"] = top_track['id']
        track_dict["Name"] = top_track['name']
        track_dict["Duration"] = milliseconds_to_min_sec(top_track['duration_ms'])
        track_dict["AlbumID"] = top_track['album']['id']
        track_dict["AlbumName"] = top_track['album']['name']
        top_tracks_details.append(track_dict)

    return top_tracks_details


def get_album_details(album_id, spotify_instance):
    """Fetches the album details based on album id. Returns a dictionary of album details"""

    # Fetch the json data using Spotify API
    results = spotify_instance.album(album_id)

    # Create dictionary and store the extracted information
    album_details = {"ID": album_id, "Name": results["name"], "Type": results["album_type"], "Label": results["label"],
                     "ReleaseDate": results["release_date"], "TotalTracks": results["total_tracks"],
                     "Popularity": results["popularity"], "Genres": results["genres"],
                     "URL": results["external_urls"]["spotify"], "Images": results["images"], "Tracks": [],
                     "Artists": []}
    ctr = 0
    for album_artist in results["artists"]:
        album_details["Artists"].append((album_artist["id"], album_artist["name"]))
        ctr += 1
    if ctr == 1:
        album_details["Artists"] = (results["artists"][0]["id"], results["artists"][0]["name"])

    ctr = 0
    for album_track in results["tracks"]["items"]:
        album_details["Tracks"].append((album_track["id"], album_track["name"],
                                        milliseconds_to_min_sec(album_track["duration_ms"])))
        ctr += 1
    if ctr == 1:
        album_details["Tracks"] = (results["tracks"]["items"][0]["id"], results["tracks"]["items"][0]["name"],
                                   milliseconds_to_min_sec(results["tracks"]["items"][0]["duration_ms"]))

    return album_details


def get_track_details(track_id, spotify_instance):
    """Fetches the track details based on track id. Returns a dictionary of track details"""

    # Fetch the json data using Spotify API
    results = spotify_instance.track(track_id)

    # Create dictionary and store the extracted information
    track_details = {"ID": track_id, "Name": results["name"], "AlbumName": results["album"]["name"],
                     "AlbumID": results["album"]["id"], "Duration": milliseconds_to_min_sec(results["duration_ms"]),
                     "Popularity": results["popularity"], "URL": results["external_urls"]["spotify"],
                     "Images": results["album"]["images"], "Artists": []}
    ctr = 0
    for td_artist in results["artists"]:
        track_details["Artists"].append((td_artist["id"], td_artist["name"]))
        ctr += 1
    if ctr == 1:
        track_details["Artists"] = (results["artists"][0]["id"], results["artists"][0]["name"])

    return track_details


def get_audio_features(track_ids, spotify_instance):
    """Fetches the track audio features based on track ids. Returns a list of dictionaries of track audio features"""

    # Fetch the json data using Spotify API
    results = spotify_instance.audio_features(track_ids)

    # Create empty list to store the extracted information
    tracks_audio_features = []

    # Extract the relevant information
    for af_track in results:
        taf_dict = {"Track ID": af_track["id"], "Danceability": af_track["danceability"], "Energy": af_track["energy"],
                    "Tempo": af_track["tempo"], "Valence": af_track["valence"]}
        tracks_audio_features.append(taf_dict)

    return tracks_audio_features


def get_playlist_artists(playlist_id, spotify_instance, limit=None):
    """Fetches the artists names based on the playlist id. Returns a list of artist names"""

    # Fetch the json data using Spotify API

    results = spotify_instance.playlist_items(playlist_id, limit=limit)

    # Create empty list to store the extracted information
    artist_names = []

    # Iterate over the playlist items and extract the track ids
    for item in results['items']:
        track2 = item['track']
        for artist2 in track2["artists"]:
            artist_names.append(artist2["name"])

    return artist_names


def milliseconds_to_min_sec(ms):
    # Convert milliseconds to total seconds
    total_seconds = ms // 1000

    # Divide total seconds to get minutes and seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes}:{seconds:02}"


def int_to_kmb(value):
    if abs(value) >= 10**9:  # Billion
        return "{:.1f}B".format(value / 10**9)
    elif abs(value) >= 10**6:  # Million
        return "{:.1f}M".format(value / 10**6)
    elif abs(value) >= 10**3:  # Thousand
        return "{:.1f}K".format(value / 10**3)
    else:
        return str(value)
