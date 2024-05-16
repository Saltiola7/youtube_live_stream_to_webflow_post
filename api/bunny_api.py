from prefect import task, get_run_logger
import os
import requests
from yt_dlp import YoutubeDL
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

@task
def download_video_task(video_id, dl_path):
    logger = get_run_logger()
    logger.debug(f"Starting download for video ID: {video_id}...")
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(dl_path, f'{video_id}.mp4'),
        'retries': 10,
        'socket_timeout': 60,
        'verbose': True,
        'merge_output_format': 'mp4'
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        logger.debug(f"Successfully downloaded video ID: {video_id}.")
    except Exception as e:
        logger.error(f"Failed to download video ID: {video_id}. Error: {e}")
        raise

@task
def upload_to_bunnycdn_task(video_id, dl_path, configurations):
    logger = get_run_logger()
    logger.debug(f"Uploading video ID: {video_id} to BunnyCDN...")
    
    file_path = os.path.join(dl_path, f"{video_id}.mp4")
    upload_url = f"https://la.storage.bunnycdn.com/{configurations['bunnycdn']['storage_zone']}/{video_id}.mp4"
    headers = {
        'AccessKey': configurations['bunnycdn']['api_key'],
        'Content-Type': 'application/octet-stream'
    }
    try:
        with open(file_path, 'rb') as video_file:
            response = requests.put(upload_url, headers=headers, data=video_file)
            response.raise_for_status()
        logger.debug(f"Successfully uploaded video ID: {video_id} to BunnyCDN.")
        return upload_url
    except Exception as e:
        logger.error(f"Failed to upload video ID: {video_id} to BunnyCDN. Error: {e}")
        raise

def check_video_exists_in_bunnycdn(video_id, configurations):
    """
    Check if a video with the given video_id already exists in BunnyCDN.
    """
    url = f"https://la.storage.bunnycdn.com/{configurations['bunnycdn']['storage_zone']}/"
    headers = {
        "accept": "application/json",
        "AccessKey": configurations['bunnycdn']['api_key']
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for item in data:
            if item['ObjectName'] == f"{video_id}.mp4":
                return True
    return False