import requests
import json
import re

from bs4 import BeautifulSoup
from utils.prettifiers import Colors as C
from utils.prettifiers import ClearScreen
from utils.fix_paths import NormalizeString
from downloaders.video_downloader import NativeVideoGetProtected
from downloaders.video_downloader import EmbeddedVideo

class HotmartClub:
    def __init__(self) -> None:
        ClearScreen()
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
        print(f"Qual o seu email da {C.Yellow}Hotmart{C.Reset}?")
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
        print(f"Qual a sua senha da {C.Yellow}Hotmart{C.Reset}?")
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
        print(f"Cursos disponíveis para {C.Green}download{C.Reset}:")
        for index, course in enumerate(self.downloadable_courses_list, start=1):
            print(f"{index} - {course['name']}")
        while True:
            try:
                download_choice = int(input("Qual curso deseja baixar?"+
                f" {C.Magenta}(0 para baixar TODOS!){C.Reset}\n")) - 1
                if download_choice > len(self.downloadable_courses_list) or \
                download_choice < -1:

                    raise TypeError
                else:
                    break
            except TypeError:
                print(f"{C.Red}{C.Bold}Indique um número!{C.Reset}")
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
        ClearScreen()
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
                    ClearScreen()
                self.course_stats['count_lesson'] += 1
                self.course_stats['current_lesson'] = \
                    f"{lesson['pageOrder']}. {NormalizeString(lesson['name']).normalize()}"
                print(f"Curso {self.count_downloadable_course}/{self.download_course_quantity}: {self.course_info['name']};;; Verificando o {C.Cyan}Módulo {self.course_stats['count_module']}{C.Reset}/{C.Blue}{self.course_stats['total_modules']}{C.Reset}; {C.Cyan}Aula {self.course_stats['count_lesson']}{C.Reset}/{C.Blue}{self.course_stats['total_lessons']}{C.Reset}")
                lesson_info = self.retrieve_lesson_info(lesson['hash'])
                try:
                    self.retrieve_native_player_lesson(lesson_info['mediasSrc'])
                except KeyError:
                    pass
                    # self.retrieve_embedded_links()






HotmartClub()