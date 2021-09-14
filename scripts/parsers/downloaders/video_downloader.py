from genericpath import exists
import youtube_dl
import m3u8
import requests
import os
import random
import string
import sys
import subprocess
import glob
import time


class NativeVideoGetProtected:
    def __init__(self, download_info) -> None:
        self.video_session = download_info['session']
        self.master_playlist_url = download_info['master_playlist']
        self.get_policy = self.master_playlist_url.split('?', 1)[1]
        self.save_path = download_info['save_path']
        self.high_qual = self.filter_video_quality()
        self.temp_folder = self.make_temp_folder()
    
    def check_save_path(self):
        if len(self.save_path) > 254:
            new_name = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=7)) + ".mp4"
            if not os.path.exists(f"{self.save_path.split('/')[0]}/ev"):
                os.makedirs(f"{self.save_path.split('/')[0]}/ev")
            with open(f"{self.save_path.split('/')[0]}/ev/map.txt", "a", encoding="utf-8") as sv_check:
                sv_check.write(f"{new_name} - {self.save_path}")
            self.save_path = f"{self.save_path.split('/')[0]}/ev/{new_name}"
        else:
            if not os.path.exists(self.save_path[:self.save_path.rfind('/')]):
                os.makedirs(self.save_path[:self.save_path.rfind('/')])
    
    def make_temp_folder(self):
        temp_folder = "_" + ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=7))
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        return temp_folder
        
    def filter_video_quality(self):
        master_content = self.video_session.get(self.master_playlist_url)
        master_loaded = m3u8.loads(master_content.text)
        res = []
        for playlist in master_loaded.playlists:
            res.append(playlist.stream_info.resolution)
        res.sort(reverse=True)
        for playlist in master_loaded.playlists:
            if playlist.stream_info.resolution == res[0]:
                return playlist.uri
    
    def download_playlist_contents(self):
        hq_content = self.video_session.get(
        f"{self.master_playlist_url[:self.master_playlist_url.rfind('/')]}/{self.high_qual}?{self.get_policy}")
        with open(f'{self.temp_folder}/dump.m3u8', 'w') as dump:
            dump.write(hq_content.text)
        hq_playlist = m3u8.loads(hq_content.text)
        key = hq_playlist.segments[0].key.uri
        totalSegmentos = hq_playlist.segments[-1].uri.split(".")[0].split("-")[1]
        for segment in hq_playlist.segments:
            print(f"\r\tPlayer NATIVO! Baixando o segmento: {segment.uri.split('.')[0].split('-')[1]}/{totalSegmentos}!",
                end="", flush=True)
            uri = segment.uri
            frag = self.video_session.get(
            f"{self.master_playlist_url[:self.master_playlist_url.rfind('/')]}/{self.high_qual.split('/')[0]}/{uri}?{self.get_policy}")
            with open(f"{self.temp_folder}/" + uri, 'wb') as sfrag:
                sfrag.write(frag.content)
        fragkey = self.video_session.get(
        f"{self.master_playlist_url[:self.master_playlist_url.rfind('/')]}/{self.high_qual.split('/')[0]}/{key}?{self.get_policy}")
        with open(f"{self.temp_folder}/{key}", 'wb') as skey:
            skey.write(fragkey.content)
        print("")
    
    def save_video(self):
        self.download_playlist_contents()
        self.check_save_path()
        # TODO implement hardware acceleration detection
        #  ffmpegcmd = f'ffmpeg -hide_banner -loglevel error -v quiet -stats -allowed_extensions ALL -hwaccel cuda -i {tempFolder}/dump.m3u8 -c:v h264_nvenc -n "{aulaPath}"'
        ffmpegcmd = f'ffmpeg -hide_banner -loglevel error -v quiet -stats -allowed_extensions ALL -i {self.temp_folder}/dump.m3u8 -n "{self.save_path}"'
        print(f"Segmentos baixados, gerando o vídeo final em: {self.save_path}", flush=True)
        if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
            subprocess.run(ffmpegcmd, shell=True)
        elif sys.platform.startswith('win32'):
            subprocess.run(ffmpegcmd)

    def cleanup(self):
        self.save_video()
        for file in glob.glob(f"{self.temp_folder}/*"):
            os.remove(file)
        time.sleep(3)
        os.rmdir(self.temp_folder)


class NativeVideoPublic:
    def __init__(self) -> None:
        pass

class EmbeddedVideo:
    def __init__(self) -> None:
        pass