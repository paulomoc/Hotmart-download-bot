# coding=utf-8
import requests
import json
import re
import os

from bs4 import BeautifulSoup

import youtube_dl
import m3u8
import random
import string
import sys
import subprocess
import glob
import time

download_success = False

class NativeVideoGetProtected:
    def __init__(self, download_info) -> None:
        self.video_session = download_info['session']
        self.master_playlist_url = download_info['master_playlist']
        self.get_policy = self.master_playlist_url.split('?', 1)[1]
        self.save_path = download_info['save_path']
        self.high_qual = self.filter_video_quality()
        self.temp_folder = None
        self.finished = False
    
    def video_exists(self):
        if os.path.isfile(self.save_path):
            self.finished = True
            self.cleanup()
        else:
            self.save_video()
    
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
        self.temp_folder = temp_folder
        
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
        
        if hq_content.status_code != 200:
            self.cleanup()
        
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
            
            if frag.status_code != 200:
                self.cleanup()
            
            with open(f"{self.temp_folder}/" + uri, 'wb') as sfrag:
                sfrag.write(frag.content)
        fragkey = self.video_session.get(
        f"{self.master_playlist_url[:self.master_playlist_url.rfind('/')]}/{self.high_qual.split('/')[0]}/{key}?{self.get_policy}")
        
        if fragkey.status_code != 200:
            self.cleanup()
        
        with open(f"{self.temp_folder}/{key}", 'wb') as skey:
            skey.write(fragkey.content)
        print("")
    
    def save_video(self):
        self.make_temp_folder()
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
        self.cleanup()

    def cleanup(self):
        try:
            for file in glob.glob(f"{self.temp_folder}/*"):
                os.remove(file)
            time.sleep(3)
            os.rmdir(self.temp_folder)
        except:
            pass
        global download_success
        download_success = self.finished


class NativeVideoPublic:
    def __init__(self) -> None:
        pass

class EmbeddedVideo:
    def __init__(self, download_info) -> None:
        youtube_dl.utils.std_headers['Referer'] = download_info['referer']
        self.video_url = download_info['video_url']
        self.save_path = download_info['save_path']
        self.finished = False

    def video_exists(self):
        if os.path.isfile(self.save_path):
            self.finished = True
        else:
            self.save_video()
    
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
    
    def save_video(self):
        self.check_save_path()
        ydl_opts = {"format": "best",
            'retries': 8,
            'fragment_retries': 6,
            'quiet': True,
            "outtmpl": self.save_path}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.video_url])

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



def normalize_str(normalize_me):
    return " ".join(re.sub(r'[<>:!"/\\|?*]', '', normalize_me)
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
        self.current_media_name = None
        self.player_auth = {"CloudFront-Policy": "", 
                            "CloudFront-Signature": "", 
                            "CloudFront-Key-Pair-Id": ""}
        self.auth_hotmart = self.create_session()
        self.original_names = self.use_orig_names()
        self.downloadable_courses_list = self.retrieve_downloadable_list()
        self.start_course_download()

    def use_orig_names(self):
        choice = input("Você gostaria de usar os nomes originais dos vídeos? s/n\n")
        if choice.lower() in ['s', 'si', 'sim', 'ism', 'smi', 'y', 'ye', 'yes', 'yse', 'eys']:
            return True
        else:
            return False
    
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

                product['name'] = normalize_str(course_name)

                downloadable_courses.append(product)
            except KeyError:
                continue
        return downloadable_courses

    def start_course_download(self):
        clear_screen()
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

    def filter_cookies(self, cookies):
        for cookie in cookies:
            if cookie['path'].endswith("hls/"):
                self.player_auth[cookie['name']] = cookie['value']
    
    def retrieve_native_player_lesson(self, lesson_videos: list=[]):
        for index, media in enumerate(lesson_videos, start=1):
            if media['mediaType'] != "VIDEO":
                input("Por favor contate o dev informando que não é um type video! Enter para continuar.")
                continue
            
            video_getter = self.auth_hotmart
            player = video_getter.get(media['mediaSrcUrl']).text
            info = json.loads(BeautifulSoup(
                                player, features="html.parser")
                                .find("script", {"id":"__NEXT_DATA__"}).text)
            self.course_stats['video_seconds'] += info['props']['pageProps']['playerData']['mediaDuration']
            
            self.filter_cookies(info['props']['pageProps']['playerData']['cookies'])

            for asset in info['props']['pageProps']['playerData']['assets']:
                download_info = {'master_playlist': f"{asset['url']}?Policy={self.player_auth['CloudFront-Policy']}&Signature={self.player_auth['CloudFront-Signature']}&Key-Pair-Id={self.player_auth['CloudFront-Key-Pair-Id']}",
                'save_path': f"Cursos/{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/{index}. {normalize_str(media['mediaName'].rsplit('.', 1)[0]) if self.original_names else 'parte'}.mp4",
                'session': self.auth_hotmart}
                global download_success
                while not download_success:
                    NativeVideoGetProtected(download_info).video_exists()
                    if not download_success:
                        print(f"{Colors.Red}Desconectado, redefinindo sessão!")
                        self.auth_hotmart = self.create_session()
                download_success = False

    def retrieve_embedded_lesson(self, player_html):
        try:
            external_source = None
            page_html = BeautifulSoup(player_html['content'], features="html.parser")
            video_iframe = page_html.findAll("iframe")
            for index, media in enumerate(video_iframe, start=1):
                # TODO Mesmo trecho de aula longa zzz

                file_path = os.path.dirname(os.path.abspath(__file__))
                save_path = f"{file_path}/Cursos/{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/{index}. ext.mp4"


                media_src = media.get("src")
                
                if 'player.vimeo' in media_src:
                    external_source = f"{Colors.Cyan}Vimeo{Colors.Reset}"
                    if "?" in media_src:
                        video_url = media_src.split("?")[0]
                    else:
                        video_url = media_src
                    if video_url[-1] == "/":
                        video_url = video_url.split("/")[-1]

                elif 'vimeo.com' in media_src:
                    external_source = f"{Colors.Cyan}Vimeo{Colors.Reset}"
                    vimeoID = media_src.split('vimeo.com/')[1]
                    if "?" in vimeoID:
                        vimeoID = vimeoID.split("?")[0]
                    video_url = "https://player.vimeo.com/video/" + vimeoID

                elif "wistia" in media_src:
                    # TODO Implementar Wistia
                    external_source = None
                    # fonteExterna = f"{Colors.Yellow}Wistia{Colors.Reset}"
                    # Preciso de um curso que tenha aula do Wistia para ver como tá sendo dado
                    # :( Ajuda noix Telegram: @katomaro
                    print("Wistia! Entra em contato no Telegram pfv")

                elif "youtube.com" in media_src or "youtu.be" in media_src:
                    fonteExterna = f"{Colors.Red}YouTube{Colors.Reset}"
                    video_url = media_src

                course_subdomain = self.course_info['resource']['subdomain']

                download_info = {'video_url': video_url,
                'save_path': save_path,
                'referer': f"https://{course_subdomain}.club.hotmart.com/"}

                if external_source is not None:
                    print(f"{Colors.Magenta}Baixando aula externa de fonte: {fonteExterna}!")
                    try:
                        EmbeddedVideo(download_info).video_exists()
                    except:
                        print(f"{Colors.Red}O vídeo é uma Live Agendada, ou, foi apagado!{Colors.Reset}")
                        with open(f"Cursos/{self.course_info['name']}/erros.txt", "a", encoding="utf-8") as elog:
                            elog.write(f"{video_url} - {self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/{index}. ext.mp4")

        except:
            print("Ou não tem aula externa ou deu algum erro aí, abre issue descrevendo que depois vejo")

    def save_text(self, content, c_type):
        f_name = 'a'
        f_type = 'a'
        if c_type == 'd':
            f_type = 'ed'
            f_name = 'desc.html'
        elif c_type == 'l':
            f_type = 'el'
            f_name = 'links.html'
        file_path = os.path.dirname(os.path.abspath(__file__))
        lesson_path = f"{file_path}/Cursos/{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/{f_name}"
            
        
        if len(lesson_path) > 254:
            if not os.path.exists(f"Cursos/{self.course_info['name']}/{f_type}"):
                os.makedirs(f"Cursos/{self.course_info['name']}/{f_type}")
            temp_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            with open(f"Cursos/{self.course_info['name']}/{f_type}/list.txt", "a", encoding="utf-8") as safelist:
                safelist.write(f"{temp_name} = {self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/{f_name}\n")
            lesson_path = f"Cursos/{self.course_info['name']}/{f_type}/{temp_name}.html"

        if not os.path.exists(lesson_path[:lesson_path.rfind('/')]):
            os.makedirs(lesson_path[:lesson_path.rfind('/')])

        if not os.path.isfile(lesson_path):
            if c_type == 'd':
                with open(lesson_path, "w", encoding="utf-8") as desct:
                    desct.write(content)
            elif c_type == 'l':
                for link in content:
                    with open(lesson_path, "a", encoding="utf-8") as linkz:
                        linkz.write(f'''<p><a href="{link['articleUrl']}">{link['articleName']}</a></p>''')

    def save_attachment(self, attachment):
        file_path = os.path.dirname(os.path.abspath(__file__))
        lesson_path = f"{file_path}/Cursos/{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/Materiais/{attachment['fileName']}"
        if len(lesson_path) > 254:
            if not os.path.exists(f"Cursos/{self.course_info['name']}/et"):
                os.makedirs(f"Cursos/{self.course_info['name']}/et")
            temp_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            with open(f"Cursos/{self.course_info['name']}/et/list.txt", "a", encoding="utf-8") as safelist:
                safelist.write(
                    f"{temp_name} = {self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/Materiais/{attachment['fileName']}\n")
            lesson_path = f"Cursos/{self.course_info['name']}/et/{temp_name}.{attachment['fileName'].split('.')[-1]}"

        if not os.path.exists(f"Cursos/{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/Materiais"):
            os.makedirs(f"Cursos/{self.course_info['name']}/{self.course_stats['current_module']}/{self.course_stats['current_lesson']}/Materiais")

        if not os.path.isfile(lesson_path):
            try:
                att_getter = self.auth_hotmart
                anexo = att_getter.get(
                    f"https://api-club.hotmart.com/hot-club-api/rest/v3/attachment/{attachment['fileMembershipId']}/download").json()
                anexo = requests.get(anexo['directDownloadUrl'])
            except KeyError:
                vrum = requests.session()
                vrum.headers.update(self.auth_hotmart.headers)
                lambdaUrl = anexo['lambdaUrl']
                vrum.headers['token'] = anexo['token']
                anexo = requests.get(vrum.get(lambdaUrl).text)
                del vrum
            with open(lesson_path, 'wb') as ann:
                ann.write(anexo.content)
                print(f"{Colors.Magenta}Anexo baixado com sucesso!{Colors.Reset}")
        else:
            print("Anexo já existente!")
    
    
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
            f"{module['moduleOrder']}. {normalize_str(module['name'])}"
            for lesson in module['pages']:
                if self.course_stats['count_lesson'] % 10 == 0:
                    clear_screen()
                self.course_stats['count_lesson'] += 1
                self.course_stats['current_lesson'] = \
                    f"{lesson['pageOrder']}. {normalize_str(lesson['name'])}"
                print(f"Curso {self.count_downloadable_course}/{self.download_course_quantity}: {self.course_info['name']}; Verificando o {Colors.Cyan}Módulo {self.course_stats['count_module']}{Colors.Reset}/{Colors.Blue}{self.course_stats['total_modules']}{Colors.Reset}; {Colors.Cyan}Aula {self.course_stats['count_lesson']}{Colors.Reset}/{Colors.Blue}{self.course_stats['total_lessons']}{Colors.Reset}")
                lesson_info = self.retrieve_lesson_info(lesson['hash'])
                # video lessons
                try:
                    self.retrieve_native_player_lesson(lesson_info['mediasSrc'])
                except KeyError:
                    self.retrieve_embedded_lesson(lesson_info['content'])
                # lesson descriptions/textual lessons
                try:
                    if lesson_info['content'].strip() != '':
                        self.save_text(lesson_info['content'], 'd')
                        print(f"{Colors.Magenta}Descrição encontrada e salva!{Colors.Reset}")
                except KeyError:
                    print("Sem Descrição!")
                # Complementary Readings
                try:
                    if lesson_info['complementaryReadings']:
                        self.save_text(lesson_info['complementaryReadings'], 'l')
                        print(f"{Colors.Magenta}Link Complementar encontrado e salvo!{Colors.Reset}")
                except KeyError:
                    print("Sem Leitura Complementar!")
                # Attachments
                try:
                    for att in lesson_info['attachments']:
                        print(f"{Colors.Magenta}Tentando baixar o anexo: {Colors.Red}{att['fileName']}{Colors.Reset}")
                        self.save_attachment(att)
                except KeyError:
                    print("Sem Anexos!")

    def goodbye(self):
        with open(f'Cursos/{self.course_info["name"]}/info.txt', 'w') as info:
            info.write(f"""Curso baixado utilizando o Katomart!\n
            Ao iniciar o download o curso possuia {self.course_stats['total_modules']} módulos,
            dos quais {self.course_stats['locked_modules']} estavam bloqueados.\n
            Por outro lado, o mesmo possuia {self.course_stats['total_lessons']},
            das quais {self.course_stats['locked_lessons']} estavam bloqueadas.
            Foram baixados {self.course_stats['video_seconds']} segundos de vídeo nativo da plataforma.""")


HotmartClub()