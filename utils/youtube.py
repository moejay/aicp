import http.client
import httplib2
from typing import Optional
import random
import time
import logging
from dataclasses import dataclass, field

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow


httplib2.RETRIES = 1
MAX_RETRIES = 10

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = "Missing client secrets file"

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

logging.basicConfig(level=logging.INFO)


@dataclass
class Options:
    file: str
    title: str = "Test Title"
    description: str = "Test Description"
    category: str = "22"
    tags: list[str] = field(default_factory=list)
    privacy_status: str = VALID_PRIVACY_STATUSES[0]


def get_authenticated_service():
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        scope=YOUTUBE_UPLOAD_SCOPE,
        message=MISSING_CLIENT_SECRETS_MESSAGE,
    )

    storage = Storage("oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()),
    )


def initialize_upload(youtube, options):
    tags = options.tags

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category,
        ),
        status=dict(privacyStatus=options.privacy_status),
    )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True),
    )

    return resumable_upload(insert_request)


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            logging.info("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if "id" in response:
                    logging.info(
                        f"Video id '{response['id']}' was successfully uploaded."
                    )
                    return f"https://www.youtube.com/watch?v={response['id']}"
                else:
                    logging.error(
                        f"The upload failed with an unexpected response: {response}"
                    )
                    return None
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"A retriable error occurred: {e}"

        if error is not None:
            logging.error(error)
            retry += 1
            if retry > MAX_RETRIES:
                logging.error("No longer attempting to retry.")
                return None

            max_sleep = 2**retry
            sleep_seconds = random.random() * max_sleep
            logging.info(f"Sleeping {sleep_seconds} seconds and then retrying...")
            time.sleep(sleep_seconds)


def upload_video(options: Options):
    youtube = get_authenticated_service()
    return initialize_upload(youtube, options)


def get_all_videos_for_channel(channel_id: str):
    """Retrieve videos for a specific channel id"""
    youtube = get_authenticated_service()
    last_page_token = None
    all_videos = []
    while True:
        response = (
            youtube.search()
            .list(
                part="snippet",
                channelId=channel_id,
                maxResults=50,
                pageToken=last_page_token,
                type="video",
            )
            .execute()
        )

        all_videos.extend(response["items"])
        if "nextPageToken" not in response:
            break
        last_page_token = response["nextPageToken"]

    return all_videos


def get_all_comments_for_video(video_id: str):
    """Retrieve comments for a specific video id"""
    youtube = get_authenticated_service()
    last_page_token = None
    all_comments = []
    while True:
        response = (
            youtube.commentThreads()
            .list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=last_page_token,
            )
            .execute()
        )

        all_comments.extend(response["items"])
        if "nextPageToken" not in response:
            break
        last_page_token = response["nextPageToken"]
    return all_comments


def filter_comments_with_no_reply_from_user(comments: list[dict], userDisplayName: str):
    """Filter comments with no reply from user"""
    comments_with_no_reply_from_user = []
    for comment in comments:
        replies = comment["replies"]["comments"] if "replies" in comment else []
        my_replies = [
            reply
            for reply in replies
            if reply["snippet"]["authorDisplayName"] == userDisplayName
        ]

        if not my_replies:
            comments_with_no_reply_from_user.append(comment)
    return comments_with_no_reply_from_user


def reply_to_comment(comment_id, text):
    """Reply to a comment"""
    youtube = get_authenticated_service()
    youtube.comments().insert(
        part="snippet",
        body=dict(
            snippet=dict(
                parentId=comment_id,
                textOriginal=text,
            )
        ),
    ).execute()
    print("Replied to comment successfully")
