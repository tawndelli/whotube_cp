import auth, time, search
from fastapi import APIRouter
from utils.return_object import returnObject

router = APIRouter(prefix='/user', tags=['user'])

my_playlist_vids = []

def get_my_channel_details():
    try:
        channels = auth.client.channels.list(mine=True, return_json=True)
    except Exception as ex:
        print(ex)
        return returnObject(message="Could not retrieve user channel details.", success=False, status_code=500)
    
    channel_id = channels['items'][0]['id']
    return channel_id

def get_my_playlist_details(channel_id):
    try:
        items = auth.Api.get_playlists(self=auth.api, channel_id=channel_id).items #.client.playlists.list(channel_id=channel_id).items
        for item in items:
            if item.snippet.title == 'My Music':
                playlist_id = item.id
                break
    except Exception as ex:
        print(ex)
        return returnObject(message="Could not retrieve user playlist details.", success=False, status_code=500)

    return playlist_id

@router.get('/my_playlist_items')
def get_my_playlist_items():
    start_time = time.time()
    
    channel_id = get_my_channel_details()
    playlist_id = get_my_playlist_details(channel_id)

    next_page_token = ''

    while next_page_token != None:
        try:
            # items = auth.client.playlistItems.list(playlist_id=playlist_id, max_results=50, page_token=next_page_token)
            items = auth.api.get_playlist_items(playlist_id=playlist_id, count=50, limit=50, page_token=next_page_token)
        except Exception as ex:
            print(ex)
            return returnObject(message="Could not retrieve user playlist items.", success=False, status_code=500)

        next_page_token = items.nextPageToken 
        
        for vid in items.items:
            vid_title = vid.snippet.title
            if str(vid_title).lower() == 'deleted video' or str(vid_title).lower() == 'private video':
                continue
            vid_id = vid.snippet.resourceId.videoId
            try:
                thumb_url = vid.snippet.thumbnails.high.url
            except:
                thumb_url = ''

            my_playlist_vids.append({"title": vid_title, "channel_title": vid.snippet.videoOwnerChannelTitle, "channel_thumb_url": search.get_channel_thumbnail(vid.snippet.videoOwnerChannelId), "id": vid_id, "iframe": "", "thumb_url": thumb_url})

    return returnObject(message="Retreived my playlist items in {:.2f} seconds."
                        .format(time.time() - start_time), success=True, data=my_playlist_vids, status_code=200)
