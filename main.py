import requests
import json
import re
import pickle
import os
from pytube import Playlist
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
import googleapiclient.errors
import backoff
import traceback
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.realpath(os.path.dirname(__file__)), '.env'))

api_service_name = "youtube"
api_version = "v3"
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
PLAYLIST_ID = os.getenv("PLAYLIST_ID",None)
AUTHORIZATION = os.getenv("DISCORD_AUTHORIZATION",None)


MSG_ID_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'last_msg_id.txt')
VIDEOS_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'videos.pkl')

##########

def extract_videos_id(subject):
	m = tuple()
	for match in re.findall(r"youtube\.com/watch\?v=([\w-]+)|https://youtu\.be/([\w-]+)", subject):
		m = m + match
	return [x for x in list(m) if x]


@backoff.on_exception(backoff.expo, (Exception),
    on_backoff=lambda details: print("Backing off {wait:0.1f} seconds after {tries} tries calling get_videos_id_playlist()".format(**details)))
def get_playlist_vids(playlist_id):
	video_ids = list()
	playlist_url = 'https://www.youtube.com/playlist?list=' + playlist_id
	print('fetching playlist:', playlist_url)
	v = Playlist(playlist_url)
	for u in v:
		video_ids += extract_videos_id(u)
	return video_ids

@backoff.on_exception(backoff.expo, (Exception),
    on_backoff=lambda details: print("Backing off {wait:0.1f} seconds after {tries} tries calling get_discord_vids".format(**details)))
def get_discord_vids(channelid, last_msg_id):
		discord_vids = list()
		headers = {'authorization': AUTHORIZATION}
		r = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages?after={last_msg_id}&limit=50', headers=headers, timeout=5)
		try:
			messages = json.loads(r.text)	
			last_msg_id = messages[0]['id']
			for item in messages:
				dvids = extract_videos_id(item['content'])
				print(item['id'],':',item['content'],'-',dvids)
				discord_vids+=dvids
			return discord_vids, last_msg_id
		
		except:
			print('no messages found on discord')
			return list(), last_msg_id




def get_vids(thread_id):

	last_msg_id = thread_id
	if os.path.exists(MSG_ID_FILE):
		with open(MSG_ID_FILE,'r', encoding="utf-8") as fh:
			last_msg_id = fh.readline()

	
	discord_vids, last_msg_id = get_discord_vids(thread_id, last_msg_id)
	#playlist_vids = get_playlist_vids(os.getenv("PLAYLIST_ID",None))
	#new_vids = [x for x in discord_vids if x not in playlist_vids]
	new_vids = list(set(discord_vids))

	#print("playlist count:",len(playlist_vids))
	#print("total found:",len(discord_vids))
	print("total new:",len(new_vids))

	return (new_vids, last_msg_id)

@backoff.on_exception(backoff.expo, (googleapiclient.errors.HttpError),
    on_backoff=lambda details: print("Backing off {wait:0.1f} seconds after {tries} tries add_vids()".format(**details)))
def add_vids(youtube, video_id):
	r = youtube.playlistItems().insert(
			part="snippet",
			body={
				"snippet": {
					"playlistId": PLAYLIST_ID, #an actual playlistid
					"position": 0,
					"resourceId": {
					"kind": "youtube#video",
					"videoId": video_id
					}
				}
			}
		).execute()
	print(r)
	

def main():
	
	flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json',scopes)
	flow.run_local_server()
	youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=flow.credentials)

	

	cache_vids = list()
	if os.path.exists(VIDEOS_FILE):
		with open(VIDEOS_FILE,'rb') as fh:
			cache_vids = pickle.load(fh)
			print('loading from cache:',VIDEOS_FILE,'delete this to start new')

	new_vids=list()
	last_msg_id = None

	while(True):
		if last_msg_id:
			print("saving last msg id:", last_msg_id)
			with open(MSG_ID_FILE,'w', encoding="utf-8") as fh:
				fh.write(last_msg_id)
				print('saved last msg id', last_msg_id)

		if new_vids:
			cache_vids += new_vids
			print("saving cache:", len(cache_vids))
			with open(VIDEOS_FILE,'wb') as fh:
				pickle.dump(cache_vids, fh)

		new_vids, last_msg_id = get_vids(os.getenv("DISCORD_THREAD_ID",None))

		# check against cache for those region blocked videos, cannot add to playlist
		new_vids = [x for x in new_vids if x not in cache_vids]


		for video_id in new_vids:
			add_vids(youtube,video_id)
			time.sleep(1)

if __name__ == "__main__":
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
	main()
