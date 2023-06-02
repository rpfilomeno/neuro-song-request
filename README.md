# Neurosama HQ Song Request

Playlist: https://www.youtube.com/playlist?list=PLYBGY593fNqrDRydSC0OR_MquxqqAW5oE

- This adds Youtube video links  found on a Discord thread to a Youtube playlist.
- Removes duplicates
- Manual throttle/advance coz Google developer account API qouta sucks

## Requirements

- Get your download client_secrets.json from: https://console.cloud.google.com/ under Project-name > Credentials and also set tester allowed.
- Get yout Discord token authorization by following: https://www.androidauthority.com/get-discord-token-3149920/
- Get your Thread Id by following: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-

## Roadmap

- Regex greedy match all link in one message
- Throttle using milisecs delay (stop hitting developer account qouta)
- Merge loop inserting to Youtube playlist with reading from Discord
- Windows One-click installer with miniconda