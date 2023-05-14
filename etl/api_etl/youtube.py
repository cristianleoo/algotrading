from api_etl.etl import ETL
import datetime, csv, requests, random
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

class Youtube(ETL):
    def __init__(self, channel_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = self.api_keys["YouTube-Data-API-v3"][random.randint(0, 5)]
        self.channel_id = self.fetch_channel_id(channel_name)
        self.channel_name = channel_name
    
    # method for fetching the channel id from the channel name
    def fetch_channel_id(self, channel_name):
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={channel_name}&type=channel&key={self.api_key}"
        response = requests.get(url)
        data = response.json()
        if data["items"]:
            channel_id = data["items"][0]["snippet"]["channelId"]
            return channel_id
        else:
            return None
        
    # Replace with your own API key, channel ID, and date
    def get(self):
        api_key = self.api_keys["YouTube-Data-API-v3"][random.randint(0, 5)]
        channel_id = self.channel_id
        start_date_str = self.start_day
        end_date_str = self.end_day

        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

        # Initialize the YouTube API client
        youtube = build("youtube", "v3", developerKey=api_key)

        # Get the channel's uploads playlist ID and channel name

        channel_info = youtube.channels().list(
            part="contentDetails,snippet", id=channel_id
        ).execute()
        uploads_playlist_id = channel_info["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        channel_name = channel_info["items"][0]["snippet"]["title"]

        # Retrieve videos uploaded between the specified dates
        videos = []
        next_page_token = None
        while True:
            response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            ).execute()
            for item in response["items"]:
                published_at = item["snippet"]["publishedAt"]
                video_date = datetime.datetime.strptime(published_at[:10], "%Y-%m-%d")
                if start_date.date() <= video_date.date() <= end_date.date():
                    videos.append(item)
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
            
        # Save video data to a local CSV file
        filename = f"../data/{self.channel_name}.csv"
        fieldnames = ["created", "title", "body", "channel_name"]

        # Check if the file exists and has a header
        file_exists = False
        try:
            with open(filename, mode="r", encoding="utf-8", newline='') as csvfile:
                file_exists = bool(next(csvfile, None))
        except FileNotFoundError:
            pass
        
        # Open the file in append mode
        with open(filename, mode="a", encoding="utf-8", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            for video in videos:
                video_id = video["snippet"]["resourceId"]["videoId"]
                video_title = video["snippet"]["title"]
                uploaded_date = video["snippet"]["publishedAt"][:10]
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    transcript_text = " ".join([entry["text"] for entry in transcript])
                except:
                    transcript_text = None

                writer.writerow({
                    "created": uploaded_date,
                    "title": video_title,
                    "body": transcript_text,
                    "channel_name": channel_name,
                })