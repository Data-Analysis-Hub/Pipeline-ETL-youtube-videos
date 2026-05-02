import requests
from itertools import batched
from dotenv import load_dotenv
from os import getenv
import json
from pathlib import Path
from time import sleep

load_dotenv('.env')
yt_key=getenv('YT_API_KEY')



auth_headers={
    'X-Goog-Api-Key': yt_key,
    'Accept': 'application/json'
    }

def get_channel_metadata():
    channel_metadata={}
    yt_channel_handle="@MavenAnalytics" # 
    channel_metadata_path="datastore/channel_metadata.json"

    if not Path(channel_metadata_path).exists():
        Path.touch(channel_metadata_path)
        p=Path(channel_metadata_path)
        yt_channel_params={'part':['contentDetails','brandingSettings','statistics','topicDetails'],'forHandle':yt_channel_handle}
        r=requests.get('https://www.googleapis.com/youtube/v3/channels',params=yt_channel_params,headers=auth_headers)
        r=r.json()['items']
        for el in r:
            main_playlist_id=el['contentDetails']['relatedPlaylists']['uploads']
            vid_count=el['statistics']['videoCount']
            channel_name=el['brandingSettings']['channel']['title']
            channel_metadata['uploads']=main_playlist_id ######### ID Upload
            channel_metadata['title']=channel_name 
            channel_metadata['videoCount']=vid_count 
        with p.open("w+") as f:
            json.dump(channel_metadata,f,indent=4)

def get_videos_ids_list():
    uploads_playlist_videos=[]
    with open('datastore/channel_metadata.json') as f:

        ########### intervals to follow & while loop flag #################
        iter_to_rate_limit=4
        big_rate_limit=120
        small_rate_limit=20
        finished=False
        ##########################
        
        upload_id=json.load(f)['uploads']
        videos_list_path="datastore/videosIds.txt"
        if not Path(videos_list_path).exists():
            p=Path(videos_list_path)
            yt_channel_params={'part':'contentDetails','maxResults':50,'playlistId':upload_id}

            while not finished:
                r=requests.get('https://www.googleapis.com/youtube/v3/playlistItems',params=yt_channel_params,headers=auth_headers)
                r=r.json()

                if not "nextPageToken" in r:
                    finished= not finished
                    if "pageToken" in yt_channel_params:
                        yt_channel_params.pop("pageToken")
                else:
                    yt_channel_params['pageToken']=r['nextPageToken']
                
                items=r['items']
                for item in items:
                    uploads_playlist_videos.append(item['contentDetails']['videoId'])
                
                if iter_to_rate_limit < 1:
                    iter_to_rate_limit=4
                    print('######################')
                    print('reached BIG RATE LIMIT')
                    print('######################')
                    sleep(big_rate_limit)
                else:
                    print('####')
                    print('reached small rate limit')
                    print('####')
                    iter_to_rate_limit-=1
                    sleep(small_rate_limit)
            print(uploads_playlist_videos)
            with p.open('w+') as f:
                for id in uploads_playlist_videos:
                    f.write(f'{id}\n')


def get_videos_metadata():
    videos_metadata=[]
    # read the txt file line by line, get the id query the API about what you need specifically, append it as a dict in the dict videos_metadata
    if not Path("datastore/videos.json").exists():
        with open('datastore/videosIds.txt') as f:
            for batch in batched(f,50):
                cleaned_batch = list(s.strip() for s in batch)
                yt_channel_params={'part':['contentDetails','snippet','statistics'],'maxResults':50,'id':cleaned_batch}
                r=requests.get('https://www.googleapis.com/youtube/v3/videos',params=yt_channel_params,headers=auth_headers)
                r=r.json()
                items=r['items']
                print(items)
                for item in items:
                    videoId = item['id']
                    title = item['snippet']['title']
                    publishedAt = item['snippet']['publishedAt']
                    duration = item['contentDetails'].get('duration',0)
                    viewCount = item['statistics'].get('viewCount', 0)
                    likeCount = item['statistics'].get('likeCount', 0)
                    commentCount = item['statistics'].get('commentCount', 0)
                    video_stat={
                        'videoId':videoId,
                        'title':title,
                        'publishedAt':publishedAt,
                        'duration':duration,
                        'viewCount':viewCount,
                        'likeCount':likeCount,
                        'commentCount':commentCount
                    }
                    videos_metadata.append(video_stat)
                print("############# rate_limit ##############")
                sleep(10)
                
            
        p=Path('datastore/videos.json')
        with p.open('w+',encoding='utf-8') as file:
            json.dump(videos_metadata,file,indent=4,ensure_ascii=False)
            

get_channel_metadata()
get_videos_ids_list()
get_videos_metadata()
