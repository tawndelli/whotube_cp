from fastapi import APIRouter, Request
from utils.return_object import returnObject
from pydantic import BaseModel
import auth, time

router = APIRouter(prefix='/search', tags=['search'])

current_playlist_id = ''
next_page_token = ''

class vidItem(BaseModel):
    title: str
    id: str
    iframe: str

#region methods

def get_channel_thumbnail(channel_id):
    try:
        channel_info = auth.api.get_channel_info(channel_id=channel_id, parts='snippet').items[0]
        thumb_url = channel_info.snippet.thumbnails.high.url
    except:
        thumb_url = ''

    return thumb_url

def get_playlist_items(playlist_id, max_results=25):
    playlist_items = []

    items = auth.api.get_playlist_items(playlist_id=playlist_id, count=max_results, limit=max_results) 

    for vid in items.items:
        vid_title = vid.snippet.title
        if str(vid_title).lower() == 'deleted video' or str(vid_title).lower() == 'private video':
                continue
        vid_id = vid.snippet.resourceId.videoId
        try:
            thumb_url = vid.snippet.thumbnails.high.url
        except:
            thumb_url = ''

        playlist_items.append({"title": vid_title, "channel_title": vid.snippet.channelTitle, "channel_thumb_url": get_channel_thumbnail(vid.snippet.channelId), "id": vid_id, "iframe": "", "thumb_url": thumb_url})

    return playlist_items

#endregion

#region routes

@router.get('/')
async def search(keyword:str):
    search_results = []
    vids = auth.api.search(q=keyword, search_type='video', count=10).items

    for vid in vids:
        search_results.append(get_video(vid.id.videoId))

    return returnObject(message="Search Results", success=True, data=search_results, status_code=200)

@router.get('/related_search')
async def related_search(vid_title, request: Request):
    global current_playlist_id
    global next_page_token

    token = request.headers.get('Authorization')

    if vid_title == '':
        # get popular charting vids
        playlist_items = []

        try:
            popular_items = auth.api.get_videos_by_chart(chart='mostPopular', page_token=next_page_token, limit=25, count=25).items
        except Exception as ex:
            # request failed
            print(ex)
            return returnObject(message="Could not retrieve popular videos.", success=False, status_code=500)

        for vid in popular_items:
            vid_title = vid.snippet.title
            if str(vid_title).lower() == 'deleted video' or str(vid_title).lower() == 'private video':
                continue
            vid_id = vid.id
            try:
                thumb_url = vid.snippet.thumbnails.high.url
            except:
                thumb_url = ''

            playlist_items.append({"title": vid_title, "channel_title": vid.snippet.channelTitle, "channel_thumb_url": get_channel_thumbnail(vid.snippet.channelId), "id": vid_id, "iframe": "", "thumb_url": thumb_url})

        return returnObject(message="Search Results", success=True, data=playlist_items, status_code=200)
    else:
        try:
            related_playlist = auth.api.search(q=f"{vid_title}", search_type='playlist', page_token=next_page_token, limit=1, count=1)
        except Exception as ex:
            print(ex)
    
    next_page_token = related_playlist.nextPageToken 

    if len(related_playlist.items) > 0:
        current_playlist_id = related_playlist.items[0].id.playlistId
        playlist_items = get_playlist_items(current_playlist_id, max_results=25)

        return returnObject(message="Search Results", success=True, data=playlist_items, status_code=200)
    
@router.get('/get_video')
def get_video(video_id):
    start_time = time.time()
    vids = auth.api.get_video_by_id(video_id=video_id, max_width=1280).items
    if len(vids) > 0:
        vid = vids[0]
        try:
            thumb_url = vid.snippet.thumbnails.high.url
        except:
            thumb_url = ''

        return returnObject(message="Video found in {:.2f} seconds."
                        .format(time.time() - start_time), success=True, data={"title": vid.snippet.title, "description": vid.snippet.description, "channel_title": vid.snippet.channelTitle, "channel_thumb_url": get_channel_thumbnail(vid.snippet.channelId), "id": vid.id, "iframe": vid.player.embedHtml, "thumb_url": thumb_url},
                        status_code=200)
    else:
        return returnObject(message="Video not found.", success=False, status_code=500)
    
#endregion