# Neurosama HQ Song Request

Discord thread: https://discord.com/channels/574720535888396288/1095957005816045618

Youtube Playlist: https://www.youtube.com/playlist?list=PLYBGY593fNqrDRydSC0OR_MquxqqAW5oE

Spotify Playlist: https://open.spotify.com/playlist/2VnWtNEhVo9IUA5TbBL8zh


- This adds Youtube video links  found on a Discord thread to a Youtube playlist.
- Removes duplicates
- Manual throttle/advance coz Google developer account API qouta sucks
- Sync the Youtube Playlist to Spotify playlist

## Requirements

- Python >= 3.11
- Install dependencies `pip install -r requirements.txt --pre`
- Get your download Youtube API client_secrets.json from: https://console.cloud.google.com/ under Project-name > Credentials and also set tester allowed.
- Get yout Discord token authorization by following: https://www.androidauthority.com/get-discord-token-3149920/
- Get your Thread Id by following: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-
- Get your Spotify AI credentials from https://developer.spotify.com/ and set test user under User Management tab
## Roadmap

- Regex greedy match all link in one message
- Throttle using milisecs delay (stop hitting developer account qouta)
- Merge loop inserting to Youtube playlist with reading from Discord
- Windows One-click installer with miniconda

## Contibutions

- Fork this repository and create a merge request.
- Add suggestion to Issue tracker.
