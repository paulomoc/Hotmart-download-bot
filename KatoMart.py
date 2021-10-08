# coding=utf-8
import requests
import json
import re
import os

from bs4 import BeautifulSoup


from genericpath import exists
import youtube_dl
import m3u8
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


def clear_screen():
    os.system("clear||cls")


class Colors:
    """ANSI Escape codes for the console output with colors and rich text.

    How to use: print(f"Total errors this run: {Cores.Red if a > 0 else Cores.Green}{a}")
    Read more also: 
        * https://en.wikipedia.org/wiki/ANSI_escape_code
        * https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
        * https://gist.github.com/arlm/f624561b2cd3f53cb26112f3e48f97cd
        * https://www.ecma-international.org/publications-and-standards/standards/ecma-48/

    Attributes:
        Reset (str): Reset colors.
        Bold (str): Makes text bold.
        Underline (str): Underlines text.
        Red (str): Red foreground text.
        Green (str): Green foreground text.
        Yellow (str): Yellow foreground text.
        Blue (str): Blue foreground text.
        Magenta (str): Magenta foreground text.
        Cyan (str): Cyan foreground text.
        bgRed (str): Red background.
        bgGreen (str): Green background.
        bgYellow (str): Yellow background.
        bgBlue (str): Blue background.
        bgMagenta (str): Magenta background.
        bgCyan (str): Cyan background.
        bgWhite (str): White background.
    """
    
    Reset = '\u001b[0m'
    """Reset colors ANSI Escape code.
    """
    Bold = '\u001b[1m'
    """Makes text bold ANSI Escape code.
    """
    Underline = '\u001b[4m'
    """Underlines text ANSI Escape code.
    """

    Red = '\u001b[31m'
    """Red foreground text ANSI Escape code.
    """
    Green = '\u001b[32m'
    """Green foreground text ANSI Escape code.
    """
    Yellow = '\u001b[33m'
    """Yellow foreground text ANSI Escape code.
    """
    Blue = '\u001b[34m'
    """Blue foreground text ANSI Escape code.
    """
    Magenta = '\u001b[35m'
    """Magenta foreground text ANSI Escape code.
    """
    Cyan = '\u001b[36m'
    """Cyan foreground text ANSI Escape code.
    """

    bgRed = '\u001b[41m'
    """Red background ANSI Escape code.
    """
    bgGreen = '\u001b[42m'
    """Green background ANSI Escape code.
    """
    bgYellow = '\u001b[43m'
    """Yellow background ANSI Escape code.
    """
    bgBlue = '\u001b[44m'
    """Blue background ANSI Escape code.
    """
    bgMagenta = '\u001b[45m'
    """Magenta background ANSI Escape code.
    """
    bgCyan = '\u001b[46m'
    """Cyan background ANSI Escape code.
    """
    bgWhite = '\u001b[47m'
    """White background ANSI Escape code.
    """



class NormalizeString:
    def __init__(self, string_to_normalize: str="") -> None:
        self.normalize_me = string_to_normalize
        self.normalize()
    
    def normalize(self):
        return " ".join(re.sub(r'[<>:!"/\\|?*]', '', self.normalize_me)
                        .strip()
                        .replace('\t', '')
                        .replace('\n', '')
                        .replace('.', '')
                        .split(' '))


class HotmartClub:
    def __init__(self) -> None:
        clear_screen()
        self.USER_EMAIL = self.get_user_email()
        self.USER_PASSWORD = self.get_user_password()
        self.GET_TOKEN_URL = 'https://api.sparkleapp.com.br/oauth/token'
        self.PRODUCTS_API = \
        'https://api-sec-vlc.hotmart.com/security/oauth/check_token'
        self.HOTMART_API = 'https://api-club.hotmart.com/hot-club-api/rest/v3'
        self.USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        ' AppleWebKit/537.36 (KHTML, like Gecko)'
        ' Chrome/91.0.4472.106 Safari/537.36'
        )
        self.download_course_quantity = 0
        self.count_downloadable_course = 0
        self.course_info = None
        self.course_json = None
        self.course_stats = {'total_modules': 0,
                            'locked_modules': 0,
                            'count_module': 0,
                            'total_lessons': 0,
                            'locked_lessons': 0,
                            'count_lesson': 0,
                            'current_module': None,
                            'current_lesson': None,
                            'current_video': None,
                            'video_seconds': 0}
        self.auth_hotmart = self.create_session()
        self.downloadable_courses_list = self.retrieve_downloadable_list()
        self.start_course_download()

    def get_user_email(self) -> str:
        print(f"Qual o seu email da {Colors.Yellow}Hotmart{Colors.Reset}?")
        while True:
            try:
                email = input("email: ")
                if "@" not in email:
                    raise Exception
                else:
                    return email
            except Exception:
                print("Opa, parece que você não entrou um email válido!")
                continue
    
    def get_user_password(self) -> str:
        print(f"Qual a sua senha da {Colors.Yellow}Hotmart{Colors.Reset}?")
        while True:
            try:
                senha = input("senha: ")
                if senha is not None or senha != "":
                    return senha
                else:
                    raise Exception
            except Exception:
                print("Opa, não parece que você informou uma senha válida!")
                continue
    
    def auth_get_token(self) -> str:
        self.auth_hotmart.headers['user-agent'] = self.USER_AGENT
        post_data = {'username': self.USER_EMAIL, 'password': self.USER_PASSWORD,
        'grant_type': 'password'}
        auth_token = self.auth_hotmart.post(self.GET_TOKEN_URL, data=post_data) \
                                .json()['access_token']
        try:
            return auth_token
        except KeyError:
            print("Email/Senha incorretos! Ou o bot pode estar desatualizado!")
            exit(1)
    
    def create_session(self) -> object:
        self.auth_hotmart = requests.session()
        auth_token = self.auth_get_token()
        self.auth_hotmart.headers.clear()
        headers = {'user-agent': self.USER_AGENT,
                    'authorization': f"Bearer {auth_token}"}
        if self.course_info is not None:
            course_subdomain = self.course_info['resource']['subdomain']
            course_url = f"https://{course_subdomain}.club.hotmart.com"
            headers['origin'] = course_url
            headers['referer'] = course_url
            headers['accept'] = 'application/json, text/plain, */*'
            headers['club'] = course_subdomain
            headers['pragma'] = 'no-cache'
            headers['cache-control'] = 'no-cache'
        self.auth_hotmart.headers.update(headers)
        return self.auth_hotmart
    
    def retrieve_downloadable_list(self) -> None:
        token = self.auth_hotmart.headers['authorization'].split(" ")[1]
        products = self.auth_hotmart.get(self.PRODUCTS_API, 
                                params={'token': token}).json()['resources']
        
        downloadable_courses =[]
        for product in products:
            try:
                if product['resource']['status'] != "ACTIVE" or \
                     "STUDENT" not in product['roles']:
                    continue

                subdomain = product['resource']['subdomain']
                product_url = f'https://{subdomain}.club.hotmart.com'

                self.auth_hotmart.headers['origin'] = product_url
                self.auth_hotmart.headers['referer'] = product_url
                self.auth_hotmart.headers['club'] = subdomain

                course_name = self.auth_hotmart \
                    .get(f'{self.HOTMART_API}/membership?attach_token=false') \
                    .json()['name']

                product['name'] = NormalizeString(course_name).normalize()

                downloadable_courses.append(product)
            except KeyError:
                continue
        return downloadable_courses

    def start_course_download(self):
        print(f"Cursos disponíveis para {Colors.Green}download{Colors.Reset}:")
        for index, course in enumerate(self.downloadable_courses_list, start=1):
            print(f"{index} - {course['name']}")
        while True:
            try:
                download_choice = int(input("Qual curso deseja baixar?"+
                f" {Colors.Magenta}(0 para baixar TODOS!){Colors.Reset}\n")) - 1
                if download_choice > len(self.downloadable_courses_list) or \
                download_choice < -1:

                    raise TypeError
                else:
                    break
            except TypeError:
                print(f"{Colors.Red}{Colors.Bold}Indique um número!{Colors.Reset}")
                continue
        
        if download_choice > -1:
            self.download_course_quantity = 1
            self.course_info = self.downloadable_courses_list[download_choice]
            self.parse_course_info()
        else:
            self.download_course_quantity = len(self.downloadable_courses_list)
            for course in self.downloadable_courses_list:
                self.course_info = course
                self.parse_course_info()

    def count_course_resources(self):
        for module in self.course_json['modules']:
            self.course_stats['total_modules'] += 1
            if module['locked']:
                self.course_stats['locked_modules'] +=1
            for lesson in module['pages']:
                self.course_stats['total_lessons'] += 1
                if lesson['locked']:
                    self.course_stats['locked_lessons'] += 1

    def retrieve_lesson_info(self, page_hash: str=""):
        lesson_getter = self.auth_hotmart
        return lesson_getter.get(f'{self.HOTMART_API}/page/{page_hash}').json()

    def retrieve_native_player_lesson(self, lesson_videos: list=[]):
        for index, media in enumerate(lesson_videos, start=1):
            if media['mediaType'] != "VIDEO":
                continue
            video_getter = self.auth_hotmart
            player = video_getter.get(media['mediaSrcUrl']).text
            info = json.loads(BeautifulSoup(player, features="html.parser") \
            .find(text=re.compile("window.playerConfig"))[:-1].split(" ", 2)[2])
            self.course_stats['video_seconds'] += info['player']['mediaDuration']
            for asset in info['player']['assets']:
                download_info = {'master_playlist': f"{asset['url']}?{info['player']['cloudFrontSignature']}",
                'save_path': f"{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/{index}. {NormalizeString(media['mediaName']).normalize()}.mp4",
                'session': self.auth_hotmart}
                NativeVideoGetProtected(download_info).cleanup()

    def retrieve_embedded_links(self):
        pass


    def parse_course_info(self):
        self.count_downloadable_course += 1
        clear_screen()
        self.auth_hotmart = self.create_session()
        self.course_json = self.auth_hotmart.get(
                                    f'{self.HOTMART_API}/navigation').json()
        self.count_course_resources()
        for module in self.course_json['modules']:
            self.course_stats['count_module'] += 1
            self.course_stats['current_module'] = \
            f"{module['moduleOrder']}. {NormalizeString(module['name']).normalize()}"
            for lesson in module['pages']:
                if self.course_stats['count_lesson'] % 5 == 0:
                    clear_screen()
                self.course_stats['count_lesson'] += 1
                self.course_stats['current_lesson'] = \
                    f"{lesson['pageOrder']}. {NormalizeString(lesson['name']).normalize()}"
                print(f"Curso {self.count_downloadable_course}/{self.download_course_quantity}: {self.course_info['name']};;; Verificando o {Colors.Cyan}Módulo {self.course_stats['count_module']}{Colors.Reset}/{Colors.Blue}{self.course_stats['total_modules']}{Colors.Reset}; {Colors.Cyan}Aula {self.course_stats['count_lesson']}{Colors.Reset}/{Colors.Blue}{self.course_stats['total_lessons']}{Colors.Reset}")
                lesson_info = self.retrieve_lesson_info(lesson['hash'])
                try:
                    self.retrieve_native_player_lesson(lesson_info['mediasSrc'])
                except KeyError:
                    pass
                    # self.retrieve_embedded_links()

HotmartClub()