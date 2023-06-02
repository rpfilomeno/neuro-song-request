import requests
import json
import re
import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
import googleapiclient.errors
import backoff
import traceback
import time

load_dotenv(os.path.join(os.path.realpath(os.path.dirname(__file__)), '.env'))

api_service_name = "youtube"
api_version = "v3"
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
PLAYLIST_ID = os.getenv("PLAYLIST_ID",None)
AUTHORIZATION = os.getenv("DISCORD_AUTHORIZATION",None)


MSG_ID_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'last_msg_id.txt')
VIDEOS_FILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'videos.pkl')

##########

def get_video_ids(thread_id):

	old_videoes = list()
	new_videoes = list()
	videoes = list()

	
	last_msg_id = thread_id
	if os.path.exists(VIDEOS_FILE):
		with open(VIDEOS_FILE,'rb') as fh:
			old_videoes = pickle.load(fh)

	if os.path.exists(MSG_ID_FILE):
		with open(MSG_ID_FILE,'r', encoding="utf-8") as fh:
			last_msg_id = fh.readline()

	r= gets(thread_id, last_msg_id)
	jsonn = json.loads(r.text)
	
	for item in jsonn:

		match = re.search(r"https://youtu\.be/([\w-]+)", item['content'])
		if match:
			videoes.append(match.group(1))
			print("found:",match.group(1))

		match = re.search(r"youtube\.com/watch\?v=([\w-]+)", item['content'])
		if match:
			videoes.append(match.group(1))
			print("found:",match.group(1))

	unique_videoes = list(set(videoes))

	for u in unique_videoes:
		if u not in old_videoes:
			new_videoes.append(u)
			print("new:", u)
		else:
			print("existing:", u)

	print("total found:",len(videoes))
	print("total unique:",len(unique_videoes))
	print("total new:",len(new_videoes))


	last_msg_id = jsonn[0]['id']
	
	if len(new_videoes) > 0:
		v = new_videoes + old_videoes
	else:
		v= list()

	return (last_msg_id, new_videoes, v)


##################################


def main():
	
	flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json',scopes)
	flow.run_local_server()
	youtube = googleapiclient.discovery.build( api_service_name, api_version, credentials=flow.credentials)

	#video_ids = list()
	v = list()
	last_msg_id = None

	while(True):
		if last_msg_id:
			print("saving last msg id:", last_msg_id)
			with open(MSG_ID_FILE,'w', encoding="utf-8") as fh:
				fh.write(last_msg_id)
		if v:
			print("saving videos list:", len(v), "videos")
			with open(VIDEOS_FILE,'wb') as fh:
				pickle.dump(v, fh)
		input("Press Enter to continue...")

		last_msg_id, video_ids, v = get_video_ids(PLAYLIST_ID = os.getenv("DISCORD_THREAD_ID",None))
		
		for video_id in video_ids:
			print("adding:", video_id)
			add(youtube,video_id)
			time.sleep(1)


##############################

@backoff.on_exception(backoff.expo, (requests.exceptions.ReadTimeout, requests.exceptions.HTTPError),
                          on_backoff=lambda details: print(
                              "Backing off {wait:0.1f} seconds after {tries} tries calling function {target} with args {args} and kwargs {kwargs}".format(
                                  **details)))
def gets(channelid, last_msg_id):
	try:
		headers = {
			'authorization': AUTHORIZATION
		}
		r = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages?after={last_msg_id}&limit=50', headers=headers, timeout=5)
		return r
	except Exception:
		print(traceback.format_exc())


	
@backoff.on_exception(backoff.expo, (googleapiclient.errors.HttpError),
                          on_backoff=lambda details: print(
                              "Backing off {wait:0.1f} seconds after {tries} tries calling function {target} with args {args} and kwargs {kwargs}".format(
                                  **details)))
def add(youtube, video_id):
	try:
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
	except Exception:
		print(traceback.format_exc())		


if __name__ == "__main__":
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
	main()
