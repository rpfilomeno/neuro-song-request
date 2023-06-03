import os
import youtube_dl
import pickle
import backoff
from queue import Queue
from threading import Thread
from pytube import Playlist
from dotenv import load_dotenv

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth



load_dotenv(os.path.join(os.path.realpath(os.path.dirname(__file__)), '.env'))
VIDEOS_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'sync.pkl')
CACHE_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'cache.pkl')
spotify_token = os.getenv("SPOTIFY_TOKEN",None)
spotify_user_id = os.getenv("SPOTIFY_USER",None)

#######

@backoff.on_exception(backoff.expo, (Exception),
                          on_backoff=lambda details: print(
                              "search backing off {wait:0.1f} seconds after {tries} tries.".format(**details)))
def search_wrapper(sp,track):
	return sp.search(track, limit=1)

def search_worker(q,  i, sp,  uris):
	while True:
		track = q.get()

		try:
			results = search_wrapper(sp,track)
			songs = results['tracks']['items']
			uri = songs[0].get("uri",None)

			if uri:
				uris.append(uri)
				print('Thread #',i,'processed:', uri, q.unfinished_tasks)
			else:
				print('Thread #',i,' no info:', track, q.unfinished_tasks)
		except:
			print("error occured while searching:", track)
		
		q.task_done()

def get_spotify_uri(sp, song_info):
	uris = []
	q = Queue()

	for i in range(16):
		worker = Thread(target=search_worker, args=(q, i, sp, uris))
		worker.daemon = True
		worker.start()

	for track, artist in song_info:
		q.put(track)

	q.join()

	return uris

##########

@backoff.on_exception(backoff.expo, (Exception),
                          on_backoff=lambda details: print(
                              "search backing off {wait:0.1f} seconds after {tries} tries.".format(**details)))
def ytdl_wrapper(url):
	return youtube_dl.YoutubeDL({}).extract_info(url, download=False)

def extract_worker(q, i, info):
	while True:
		url = q.get()

		try:
			details = ytdl_wrapper(url)
			track, artist = details.get('track',None), details.get('artist',None)

			if(track):
				info.append((track, artist))		 
				print('Thread #',i,'processed:', track, artist, q.unfinished_tasks)
			else:
				print('Thread #',i,' no info:', url, q.unfinished_tasks)

		except:
			print("error occured while reading:", url)
		
		q.task_done()
		

def extract_song_from_yt(urls):

	info = []
	q = Queue()
	for i in range(16):
		worker = Thread(target=extract_worker, args=(q,i,info))
		worker.daemon = True
		worker.start()
	
	for url in urls:
		q.put(url)
	
	q.join()

	return info


############



@backoff.on_exception(backoff.expo, (Exception),
                          on_backoff=lambda details: print(
                              "search backing off {wait:0.1f} seconds after {tries} tries.".format(**details)))
def add_wrapper(sp,playlist_id, chunk):
	sp.playlist_add_items(playlist_id, chunk)




###########

def split(list_a, chunk_size):
	for i in range(0, len(list_a), chunk_size):
		yield list_a[i:i + chunk_size]



if __name__ == "__main__":
	username = os.getenv("SPOTIFY_USER",None)
	client_id = os.getenv("SPOTIFY_CLIENT_ID",None)
	client_secret = os.getenv("SPOTIFY_CLIENT_SECRET",None)
	scope = "playlist-modify-public"
	to_playlist_id = os.getenv("SPOTIFY_PLAYLIST",None)
	#sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv("SPOTIFY_CLIENT_ID",None),
    #                                                       client_secret=os.getenv("SPOTIFY_CLIENT_SECRET",None)))

	token = util.prompt_for_user_token(username,scope,client_id,client_secret,redirect_uri='http://localhost:8888/spotify/callback')
	sp = spotipy.Spotify(auth=token)


	


	if os.path.exists(VIDEOS_FILE):
		with open(VIDEOS_FILE,'rb') as fh:
			song_info = pickle.load(fh)
			print('loading from save:',VIDEOS_FILE,'delete this to start new')
	else:
		playlist_url = 'https://www.youtube.com/playlist?list=' + os.getenv("PLAYLIST_ID",None)
		print('fetching playlist:', playlist_url)
		urls = Playlist(playlist_url)
		print('found:',len(urls),' videos')
		song_info = extract_song_from_yt(urls)

		if song_info:
			print("saving list:", len(song_info), "videos")
			with open(VIDEOS_FILE,'wb') as fh:
				pickle.dump(song_info, fh)




	if os.path.exists(CACHE_FILE):
		with open(CACHE_FILE,'rb') as fh:
			uris = pickle.load(fh)
			print('loading', len(uris), 'ytack from cache:',CACHE_FILE,'delete this to start new')	
	else:
		uris = get_spotify_uri(sp, song_info)
		if uris:
			print("saving to cache:", len(uris), "tracks")
			with open(CACHE_FILE,'wb') as fh:
				pickle.dump(uris, fh)
	print('tracks loaded from cache:', len(uris))
	playlistTracks = sp.playlist_tracks(to_playlist_id,limit=50)
	while playlistTracks:
		for i, playlistTrack in enumerate(playlistTracks['items']):
			uri = playlistTrack['track']['uri']
			if uri in uris:
				uris.remove(uri)
				print('dedupped:', uri)
		if playlistTracks.get('next', False):
			playlistTracks = sp.next(playlistTracks)
		else:
			playlistTracks = None
	
	print('new tracks to be added:', len(uris))


	# adding new song playlist
	chunk_uris = list(split(uris, 50))
	for chunk in chunk_uris:
		add_wrapper(sp, to_playlist_id, chunk)
