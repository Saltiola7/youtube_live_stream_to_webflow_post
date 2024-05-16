from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from prefect import task, get_run_logger
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

def fetch_live_streams(configurations):
    """
    Fetch live streams and include their raw liveBroadcastContent status.
    """
    logger = get_run_logger()
    logger.debug("Starting to fetch live streams...")
    
    youtube = build('youtube', 'v3', developerKey=configurations['youtube']['api_key_gorilla'])
    channel_id = configurations['youtube']['channel_id_test']
    published_after = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    videos = []
    page_token = None
    while True:
        logger.debug("Fetching page of streams...")
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=50,
            order="date",
            pageToken=page_token,
            publishedAfter=published_after,
            type="video",
            eventType=None  # Fetch all types of events
        )
        response = request.execute()

        video_ids = [item['id']['videoId'] for item in response['items']]
        if video_ids:
            details_request = youtube.videos().list(
                part="snippet,liveStreamingDetails",
                id=",".join(video_ids)
            )
            details_response = details_request.execute()

            for item in details_response['items']:
                videos.append({
                    'videoId': item['id'],
                    'title': item['snippet']['title'],
                    'publishedAt': item['snippet']['publishedAt'],
                    'liveStatus': item['snippet'].get('liveBroadcastContent', 'none')  # Directly use liveBroadcastContent
                })

        page_token = response.get('nextPageToken')
        if not page_token:
            break

    logger.debug(f"Finished fetching streams. Total fetched: {len(videos)}")
    return videos

@task
def fetch_streams_task(configurations):
    return fetch_live_streams(configurations)