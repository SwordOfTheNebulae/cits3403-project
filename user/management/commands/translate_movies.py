import hashlib
import json
import random
import time
import requests
from django.core.management.base import BaseCommand
from user.models import Movie


class Command(BaseCommand):
    help = '将电影数据从中文转换为英文'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            type=int,
            default=0,
            help='起始ID'
        )
        parser.add_argument(
            '--batch',
            type=int,
            default=50,
            help='每批处理数量'
        )

    def handle(self, *args, **options):
        # 百度翻译API配置
        appid = '20240114001941016'  # 替换为您的百度翻译APPID
        appkey = 'jL_598xurwHfYV252ffz'  # 替换为您的百度翻译密钥

        start_id = options['start']
        batch_size = options['batch']

        self.stdout.write(f'开始从ID {start_id}翻译电影的主演和简介')

        if start_id == 0:
            # 获取电影总数
            movies = Movie.objects.all().order_by('id')
            total_movies = Movie.objects.count()
            self.stdout.write(f'共有 {total_movies} 部电影需要翻译')
        else:
            # 获取ID大于等于start_id的电影
            movies = Movie.objects.filter(id__gte=start_id).order_by('id')
            total_movies = movies.count()
            if total_movies == 0:
                self.stdout.write(self.style.WARNING(f'未找到ID大于等于{start_id}的电影'))
                return
            self.stdout.write(f'共找到 {total_movies} 部需要翻译的电影')

        # 批量获取电影
        processed = 0
        for i in range(0, total_movies, batch_size):
            batch = movies[i:i + batch_size]

            for movie in batch:
                try:
                    # 翻译电影名称
                    # if movie.name:
                    #     movie.name = self.translate_text(movie.name, appid, appkey)
                    #     time.sleep(1)  # 避免API限制

                    # 翻译导演
                    # if movie.director:
                    #     movie.director = self.translate_text(movie.director, appid, appkey)
                    #     time.sleep(1)

                    # 翻译国家
                    # if movie.country:
                    #     movie.country = self.translate_text(movie.country, appid, appkey)
                    #     time.sleep(1)

                    # 翻译主演
                    if movie.leader:
                        movie.leader = self.translate_text(movie.leader, appid, appkey)
                        time.sleep(1)

                    # 翻译简介 (内容可能较长，需要分段处理)
                    if movie.intro:
                        # 如果简介太长，可能需要分段翻译
                        intro_parts = [movie.intro[i:i + 2000] for i in range(0, len(movie.intro), 2000)]
                        translated_intro = ""
                        for part in intro_parts:
                            translated_part = self.translate_text(part, appid, appkey)
                            translated_intro += translated_part
                            time.sleep(1)
                        movie.intro = translated_intro

                    # 保存修改
                    movie.save()
                    self.stdout.write(f'已翻译电影 ID: {movie.id}, 名称: {movie.name}')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'处理电影 ID: {movie.id} 时出错: {str(e)}'))
                    # 继续处理下一条，而不是中断整个过程

            processed += batch_size
            self.stdout.write(f'已处理 {processed}/{total_movies} 部电影')

        self.stdout.write(self.style.SUCCESS('所有电影数据已成功转换为英文'))

    def translate_text(self, text, appid, appkey):
        # 如果是空文本，直接返回
        if not text or text.strip() == '':
            return text

        # 百度翻译API
        salt = random.randint(32768, 65536)
        sign = hashlib.md5((appid + text + str(salt) + appkey).encode('utf-8')).hexdigest()

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'appid': appid,
            'q': text,
            'from': 'zh',
            'to': 'en',
            'salt': salt,
            'sign': sign
        }

        # 发送请求
        try:
            response = requests.post('http://api.fanyi.baidu.com/api/trans/vip/translate',
                                     params=payload,
                                     headers=headers)
            result = response.json()

            # 检查是否有错误
            if 'error_code' in result:
                self.stdout.write(
                    self.style.ERROR(f'翻译API错误: {result["error_code"]} - {result.get("error_msg", "")}'))
                return text  # 出错时返回原文本

            # 提取翻译结果
            if 'trans_result' in result and result['trans_result']:
                translated = result['trans_result'][0]['dst']
                return translated
            else:
                return text  # 如果没有翻译结果，返回原文本

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'翻译请求异常: {str(e)}'))
            return text  # 出错时返回原文本
