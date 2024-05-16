from prefect import flow, task, get_run_logger
from cfg.cfg import cfg
from api.youtube_api import fetch_streams_task
from api.webflow_api import fetch_existing_webflow_items_task, create_webflow_item_task, update_webflow_cms_task
from api.bunny_api import download_video_task, upload_to_bunnycdn_task, check_video_exists_in_bunnycdn
import logging

logging.basicConfig(level=logging.DEBUG)

@task
def load_configurations():
    logger = get_run_logger()
    logger.debug("Loading configurations...")
    configurations = cfg()
    logger.debug("Configurations loaded.")
    return configurations

@flow
def youtube_to_webflow_sync_flow():
    logger = get_run_logger()
    logger.debug("Starting YouTube to Webflow synchronization flow...")
    configurations = load_configurations()

    # Fetch YouTube videos with a single task
    videos = fetch_streams_task(configurations)

    # Fetch existing Webflow items
    existing_webflow_items = fetch_existing_webflow_items_task(configurations)

    # Process videos
    for video in videos:
        # Determine if the video is live or has completed based on the YouTube API response
        is_live_status = video['liveStatus']

        # Initialize bunny_link outside of the conditional blocks
        bunny_link = None

        # Check if the video already exists in BunnyCDN
        if not check_video_exists_in_bunnycdn(video['videoId'], configurations):
            # If not, download and upload to BunnyCDN
            download_video_task(video['videoId'], configurations['app']['dl_path'])
            bunny_link = upload_to_bunnycdn_task(video['videoId'], configurations['app']['dl_path'], configurations)
        else:
            # If it exists, generate the bunny_link without downloading/uploading
            bunny_link = f"https://{configurations['bunnycdn']['storage_zone']}.b-cdn.net/{video['videoId']}.mp4"

        if video['videoId'] not in existing_webflow_items:
            # Create new Webflow item with the bunny_link and is_live_status
            create_webflow_item_task(configurations, video, existing_webflow_items, bunny_link)  # Ensure correct parameter order
        else:
            # Update existing Webflow item if necessary
            existing_item = existing_webflow_items[video['videoId']]
            if is_live_status == "completed" and existing_item['fieldData']['live']:
                # Update the Webflow CMS item to reflect the change
                update_webflow_cms_task(existing_item['_id'], configurations, video, bunny_link)  # Ensure correct parameter order
                logger.debug(f"Updated Webflow item for video ID: {video['videoId']} to live: False.")

    logger.debug("YouTube to Webflow synchronization flow completed.")

if __name__ == "__main__":
    youtube_to_webflow_sync_flow()
