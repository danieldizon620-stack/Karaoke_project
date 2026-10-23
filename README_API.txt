dannyboi Karaoke v2.7 — Song Database API

Local endpoints (require X-Host-Token from GET /api/info on localhost):
GET /api/songs/search?q=... — {"songs":[{code,title,artist,language,youtube_id}]}
GET /api/songs/{code} — one song record
GET /api/queue — {"queue":[{id,code,title,artist,youtube_id}]}
POST /api/queue — JSON {"code":"..."}
DELETE /api/queue/{id} — remove item
GET /api/youtube/search?q=... — {"results":[{videoId,title,channel}]}
POST /api/songs/import — JSON {"songs":[...]} (local catalog import, max 2000 per request)

Example JSON file to import:
[{"code":"00001","title":"Example Song","artist":"Example Artist","language":"English","youtube_id":""}]

YouTube API search requires the YOUTUBE_DATA_API_KEY environment variable, a Google Cloud project with YouTube Data API v3 enabled, and internet access. No key is bundled.
This does not access VideokePH's private database. An authorized VideokePH server/API URL and permission are required to use its catalog directly.
Existing offline local karaoke files and the VideokePH browser window remain available.
