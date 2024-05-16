import requests
from prefect import task, get_run_logger
import re  # For slug generation

def make_webflow_request(method, url, configurations, payload=None):
    """
    Generic function to make Webflow API requests.
    """
    logger = get_run_logger()
    headers = {
        "Authorization": "Bearer " + configurations['webflow']['api_key'],
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers)
        elif method.lower() == 'post':
            response = requests.post(url, json=payload, headers=headers)
        elif method.lower() == 'patch':
            response = requests.patch(url, json=payload, headers=headers)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None

        if response is not None and 200 <= response.status_code < 300:
            logger.info(f"Successfully executed {method.upper()} request.")
            return response.json()
        else:
            logger.error(f"Failed to {method.upper()} data: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception during {method.upper()} request: {str(e)}")
        return None

@task
def fetch_existing_webflow_items_task(configurations):
    logger = get_run_logger()
    logger.info("Fetching existing Webflow items...")
    
    url = "https://api.webflow.com/v2/collections/6596ec7b8177a44ce3ab794f/items"
    response_data = make_webflow_request('get', url, configurations)
    
    if response_data is None:
        return {}
    
    existing_items = {item['fieldData'].get('video-id'): item for item in response_data.get('items', []) if 'fieldData' in item and item['fieldData'].get('video-id')}
    
    logger.info(f"Fetched {len(existing_items)} existing Webflow items.")
    return existing_items

@task
def create_webflow_item_task(configurations, video, existing_items, bunny_link):
    logger = get_run_logger()
    logger.info(f"Creating Webflow item for video ID: {video['videoId']}")

    if video['videoId'] in existing_items:
        logger.info(f"Video ID: {video['videoId']} already exists in Webflow. Skipping creation.")
        return {"duplicate": True, "item": existing_items[video['videoId']]}

    url = "https://api.webflow.com/v2/collections/6596ec7b8177a44ce3ab794f/items"
    slug = generate_slug(video['title'])
    
    payload = {
        "isArchived": False,
        "isDraft": False,
        "fieldData": {
            "name": video['title'],
            "slug": slug,
            "publish-date": video['publishedAt'],
            "video-id": video['videoId'],
            "is-live": video['liveStatus'],
            "bunny-link": bunny_link  # Include bunny_link in the payload
        }
    }
    
    response_data = make_webflow_request('post', url, configurations, payload)
    
    if response_data is None:
        return {"duplicate": False, "error": "Failed to create item."}
    
    logger.info(f"Successfully created Webflow item for video ID: {video['videoId']} with bunny_link.")
    return {"duplicate": False, "response": response_data}

@task
def update_webflow_cms_task(cms_item_id, configurations, video, bunny_link):
    logger = get_run_logger()
    
    fetch_url = f"https://api.webflow.com/collections/{configurations['webflow']['collection_id']}/items/{cms_item_id}"
    cms_item = make_webflow_request('get', fetch_url, configurations)
    if cms_item is None or 'fields' not in cms_item:
        logger.error(f"Failed to fetch Webflow CMS item {cms_item_id}.")
        return f"Failed to fetch Webflow CMS item {cms_item_id}."

    # Check if bunny_link is already present or needs updating
    if 'bunny-link' not in cms_item['fields'] or cms_item['fields']['bunny-link'] != bunny_link:
        logger.info(f"Updating Webflow CMS item {cms_item_id} with bunny_link {bunny_link}.")

        update_url = fetch_url  # Reuse the URL for updating since it's the same
        payload = {
            "fields": {
                "bunny-link": bunny_link,  # Update bunny_link in the payload
                "_archived": False,
                "_draft": False,
                "is-live": video['liveStatus']
            }
        }

        update_response = make_webflow_request('patch', update_url, configurations, payload)

        if update_response:
            logger.info(f"Successfully updated Webflow CMS item {cms_item_id} with bunny_link.")
            return f"Updated Webflow CMS item {cms_item_id} with bunny_link."
        else:
            logger.error(f"Failed to update Webflow CMS item {cms_item_id}.")
            return f"Failed to update Webflow CMS item {cms_item_id}."
    else:
        logger.info(f"No update needed for Webflow CMS item {cms_item_id}.")
        return f"No update needed for Webflow CMS item {cms_item_id}."

def generate_slug(title):
    """
    Generates a slug from a video title by removing numbers and symbols,
    ensuring it starts with a word, excluding words that are only three letters long,
    and having only one hyphen between words.
    """
    # Remove numbers and symbols except for spaces and hyphens
    slug = re.sub(r'[^\w\s-]', '', title)
    # Split into words, exclude words that are three letters or shorter
    words = [word for word in slug.split() if len(word) > 3]
    # Join words with a single hyphen
    slug = '-'.join(words)
    # Convert to lowercase
    slug = slug.lower()
    # Ensure the slug starts with a word (alphanumeric character)
    slug = re.sub(r'^[^a-zA-Z0-9]*', '', slug)
    # Replace multiple hyphens with a single hyphen
    slug = re.sub(r'-+', '-', slug)
    return slug