# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import json
import requests
import random
import threading
import time

from src.Captcha import QiangGuoXianFengCaptcha
from src.Cipher import rsa_encrypt
from src.Enums import HttpUserAgent, QiangGuoXianFengBaseURL
from src.GlobalMethods import print, input

class QiangGuoXianFengAPI:
    class BadAuthorizationError(Exception):
        def __init__(self, *args):
            super().__init__(args)

    class UnauthorizedError(Exception):
        def __init__(self, *args):
            super().__init__(args)

    class FatalAPIError(Exception):
        def __init__(self, *args):
            super().__init__(args)

    def __init__(self, base_url, timeout=3):
        self._headers = {'User-Agent': HttpUserAgent.generate_user_agent().value}
        self._base_url = base_url
        self._timeout = timeout

    def _send(self, url, data=None, max_retries=1, as_json=False, use_get=False):
        for _ in range(max(1, max_retries)):
            try:
                method = requests.get if use_get else requests.post
                r = method(url,
                           data=data if not as_json else None,
                           json=data if as_json else None,
                           headers=self._headers,
                           timeout=self._timeout)
                if r.status_code != 200:
                    raise RuntimeError(r.status_code)
                d = json.loads(r.text)
                if d['code'] == 99999:
                    return d
                elif d['code'] == 10002:
                    raise QiangGuoXianFengAPI.BadAuthorizationError(d.get('msg', "Authorization failed"))
                elif d['code'] == 10003:
                    raise QiangGuoXianFengAPI.UnauthorizedError(d.get('msg', "Permission denied"))
                elif d['code'] == 20000:
                    raise QiangGuoXianFengAPI.FatalAPIError(f"API failed with code {d['code']}")
                else:
                    raise IOError(f"API failed with code {d['code']}")
            except IOError as arg:
                time.sleep(self._timeout)
        raise RuntimeError("Max retires exceeded")

    def _fetch_pagination(self, url, data, page_size, max_page_num=1024, **kwargs):
        rst = []
        page_num = 1
        while page_num <= max_page_num:
            data['pageNum'] = page_num
            data['pageSize'] = page_size
            d = self._send(url, data, **kwargs)
            li = d['data']['list']
            if not isinstance(li, (list, tuple)):
                break
            rst.extend(li)
            if len(li) < page_size:
                break
            page_num += 1
        return rst

    def get_captcha(self):
        d = self._send(f"{self._base_url}/trainingApi/v1/user/getCaptcha",
                       max_retries=3,
                       use_get=True)
        return d['data']

    def login(self, user_id, user_pwd, captcha_id, captcha_code):
        d = self._send(f"{self._base_url}/trainingApi/v1/user/login",
                       data={'userSid': user_id, 'password': rsa_encrypt(user_pwd),
                             'id': captcha_id, 'code': captcha_code})
        self._headers['Token'] = d['data']['token']
        return d['data']

    def get_lesson_list(self):
        return self._fetch_pagination(f"{self._base_url}/trainingApi/v1/lesson/myLesson",{},
                                      8)

    def get_video_list(self, lesson_id):
        return self._fetch_pagination(f"{self._base_url}/trainingApi/v1/lesson/lessonVideos",
                                      {'lessonId': lesson_id, 'showType': 0},
                                      10,
                                      as_json=True)

    def get_resource_list(self, video_id):
        d = self._send(f"{self._base_url}/trainingApi/v1/lesson/lessonVideoDetail",
                       data={'videoId': video_id})
        return d['data']['resourceList']

    def get_resource_detail(self, resource_id):
        d = self._send(f"{self._base_url}/trainingApi/v1/lesson/lessonVideoResourceDetail",
                       data={'resourceId': resource_id})
        return d['data']

    def set_resource_progress(self, resource_id, hhmmss):
        d = self._send(f"{self._base_url}/trainingApi/v1/lesson/setResourceTime",
                       max_retries=10,
                       data={'resourceId': resource_id, 'videoTime': hhmmss})
        return None

    def get_lesson_exam_list(self):
        d = self._send(f"{self._base_url}/trainingApi/v1/exam/examLessonList")
        return d['data']

    def get_lesson_exam_start(self, lesson_id, stage_id):
        d = self._send(f"{self._base_url}/trainingApi/v1/exam/startLessonExam",
                       max_retries=3,
                       data={'stageId': stage_id, 'lessonId': lesson_id})
        return d['data']

    def set_exam_temp_answer(self, record_id, answer_dict):
        d = self._send(f"{self._base_url}/trainingApi/v1/exam/saveExamAnswer",
                       data={'recordId': record_id, 'answerList': answer_dict},
                       as_json=True)
        return None

    def set_exam_final_answer(self, record_id, answer_dict):
        d = self._send(f"{self._base_url}/trainingApi/v1/exam/submitExam",
                       data={'recordId': record_id, 'answerList': answer_dict},
                       as_json=True)
        return d['data']

    def get_exam_report(self, record_id, right_type=-1):
        d = self._send(f"{self._base_url}/trainingApi/v1/exam/examRecordDetail",
                       data={'recordId': record_id, 'rightType': right_type})
        return d['data']

class AutoTrainer:
    PLAYING_TIME_SCALE = 0.95
    FINISHING_REPORT_TIMES = 2
    START_PLAYING_INTERVAL = 3

    def __init__(self, api:QiangGuoXianFengAPI, max_jobs=10, report_interval=10, report_randomness=1):
        self.api = api
        self._threads = []
        self._right_answers = {}
        self._max_jobs = max_jobs
        self._now_jobs = 0
        self._report_interval = abs(report_interval)
        self._report_randomness = abs(report_randomness)

    @staticmethod
    def _second_to_hhmmss(second:int):
        second = round(second)
        h = second // 3600
        m = second % 3600 // 60
        s = second % 60
        return f"{h:02}:{m:02}:{s:02}"

    @staticmethod
    def _hhmmss_to_second(hhmmss:str):
        if not hhmmss:
            return 0
        units = (3600, 60, 1)
        return sum([round(x * y) for x, y in zip(units, map(int, hhmmss.split(':')))])

    def is_subthread_completed(self):
        for i in self._threads:
            if i.is_alive():
                return False
        return True

    def manual_login(self):
        while True:
            try:
                print("请登录", c=3)
                user_id = input("  请输入账号: ", c=7)
                user_pwd = input("  请输入密码: ", c=7)
                print("  正在获取验证码", c=5)
                captcha = self.api.get_captcha()
                print("    请在弹出的窗口中查看验证码图片，然后关闭该窗口", c=6)
                captcha_obj = QiangGuoXianFengCaptcha(captcha['base64Str'])
                captcha_code = captcha_obj.solve_challenge()
                info = self.api.login(user_id, user_pwd, captcha['captchaId'], captcha_code)
                break
            except QiangGuoXianFengAPI.BadAuthorizationError as arg:
                print(f"  登录失败，填写有误: {arg}", c=3)
            except QiangGuoXianFengAPI.FatalAPIError as arg:
                print(f"  登录失败，意外错误：{arg}", c=3)
        print(f"  登录成功，欢迎`{info['userName']}`!", c=2)

    def _watch(self, resource_id:int, start_time:str, total_time:str):
        self._now_jobs += 1
        try:
            start = AutoTrainer._hhmmss_to_second(start_time)
            total = AutoTrainer._hhmmss_to_second(total_time)
            for now in range(start, total, self._report_interval):
                now += (random.random() - 0.5) * 2 * self._report_randomness
                now_time = AutoTrainer._second_to_hhmmss(now)
                print(f"  (视频资源 {resource_id}) 正在观看 {now_time} / {total_time} ({now / total:.0%})", c=7)
                self.api.set_resource_progress(resource_id, AutoTrainer._second_to_hhmmss(now))
                time.sleep(self._report_interval * AutoTrainer.PLAYING_TIME_SCALE)
            print(f"  (视频资源 {resource_id}) 正在结束观看", c=7)
            for _ in range(AutoTrainer.FINISHING_REPORT_TIMES):
                self.api.set_resource_progress(resource_id, total_time)
                time.sleep(self._report_interval * AutoTrainer.PLAYING_TIME_SCALE)
            print(f"  (视频资源 {resource_id}) 已完成", c=2)
        finally:
            self._now_jobs -= 1

    def watch(self, resource:dict):
        while self._now_jobs >= self._max_jobs:
            time.sleep(0.1)
        resource_id = resource['resourceId']
        detail = self.api.get_resource_detail(resource_id)
        start_time = detail['resource_time']
        total_time = detail['resourceDuration']
        thread = threading.Thread(target=self._watch,
                                  name=f"AutoTrain#{resource_id}",
                                  args=(resource_id, start_time, total_time),
                                  daemon=True)
        thread.start()
        self._threads.append(thread)

    def watch_all(self):
        print("正在查询课程列表", c=5)
        lessons = self.api.get_lesson_list()
        for l in lessons:
            print(f"(课程 {l['lessonId']}) `{l['lessonTitle']}`", c=6)
            videos = self.api.get_video_list(l['lessonId'])
            for v in videos:
                print(f"  (视频 {v['videoId']}) {'已完成' if v['complete'] else ''} `{v['videoTitle']}`", c=6)
                if not v['complete']:
                    resources = self.api.get_resource_list(v['videoId'])
                    for r in resources:
                        self.watch(r)
                        time.sleep(AutoTrainer.START_PLAYING_INTERVAL)

    @staticmethod
    def _find_by_property(collection, property_name, property_value):
        for i in collection:
            if i[property_name] == property_value:
                return i
        return None

    def do_lesson_exam(self, lesson_exam:dict, expected_error=2, pass_score=80, max_retries=5):
        for i in range(max_retries):
            time.sleep(1)
            # Request to start an exam
            lesson_id = lesson_exam['lessonId']
            stage_id = lesson_exam['stageId']
            print(f"  开始课程考试 {lesson_id} (尝试 #{i + 1})", c=5)
            exam = self.api.get_lesson_exam_start(lesson_id, stage_id)
            report_id = exam['recordId']
            question_list = sorted(exam['questionList'], key=lambda x:x['questionId'])
            # Figure out answers
            has_right_answers = {}
            guess_answers = {}
            print(f"  (考卷 {report_id}) 一共有题目 {len(question_list)} 道", c=7)
            for q in question_list:
                question_id = q['questionId']
                if question_id in self._right_answers:
                    has_right_answers[question_id] = self._right_answers[question_id]
                else:
                    if q['questionType'] in [1, 2, 3]:
                        # Single=1, Multiple=2, TF=3
                        guess_this = random.choices([a['answerId'] for a in q['answerList']],
                                                    k=2 if q['questionType'] == 2 else 1)
                        guess_answers[question_id] = '|'.join(map(str, guess_this))
                    else:
                        raise RuntimeError(f"Not supported question type: {q['questionType']}")
            print(f"  (考卷 {report_id}) 记得答案的题目有 {len(has_right_answers)} 道")
            while len(guess_answers) <= expected_error:
                k, v = random.choice(tuple(has_right_answers.items()))
                has_right_answers.pop(k)
                q = AutoTrainer._find_by_property(question_list, 'questionId', k)
                guess_answers[k] = random.choice([a['answerId'] for a in q['answerList']])
            # Submit exam
            my_answers = {**guess_answers, **has_right_answers}
            saved_answers = {}
            print(f"  (考卷 {report_id}) 正在填写答案 (需要等待约 {len(my_answers) * 4} 秒)", c=7)
            for k, v in my_answers.items():
                saved_answers[k] = v
                self.api.set_exam_temp_answer(report_id, saved_answers)
                time.sleep(random.randint(3, 5))
            print(f"  (考卷 {report_id}) 正在结束考试", c=7)
            rst = self.api.set_exam_final_answer(report_id, saved_answers)
            # Get report
            print(f"  (考卷 {report_id}) 正在获取参考答案", c=7)
            question_list_with_answer = self.api.get_exam_report(report_id)['list']
            for qa in question_list_with_answer:
                self._right_answers[qa['questionId']] = qa['rightAnswer']
            if rst['score'] >= pass_score:
                print(f"  (考卷 {report_id}) 成功通过! 分数 {rst['score']} (尝试 #{i + 1})", c=2)
                break
            else:
                print(f"  (考卷 {report_id}) 未通过! 分数 {rst['score']} (尝试 #{i + 1})", c=3)

    def do_lesson_exam_all(self, pass_score=80):
        print("正在查询课程考试列表", c=5)
        exams = self.api.get_lesson_exam_list()
        for e in exams:
            print(f"(课程考试 {e['lessonId']}) 当前最高分 {e['maxScore']} `{e['lessonTitle']}`", c=6)
            if e['maxScore'] < pass_score:
                self.do_lesson_exam(e, pass_score=pass_score)

if __name__ == '__main__':
    try:
        print("开始运行!", c=2)

        while True:
            print("请选择目标平台", c=3)
            for site in QiangGuoXianFengBaseURL.all_names():
                print(f"  - 平台代码 {site}：网址 {QiangGuoXianFengBaseURL.of_name(site).value}", c=7)
            site_code = input("  请输入完整的平台代码: ", c=7)
            if QiangGuoXianFengBaseURL.contains_name(site_code):
                break

        base_url = QiangGuoXianFengBaseURL.of_name(site_code).value

        while True:
            print("请选择任务类型", c=3)
            print("  1=视频课程, 2=课程考试, 3=全选", c=7)
            task_code = input("  请输入序号: ", c=7)
            if task_code in ["1", "2", "3"]:
                break

        DEFAULT_MAX_CONCURRENT = 5
        try:
            print("请设置任务参数", c=3)
            max_concurrent = int(input(f"  同时观看课程数: ", c=7))
            assert 1 <= max_concurrent <= 20
        except:
            max_concurrent = DEFAULT_MAX_CONCURRENT
            print(f"  已设为默认值 {DEFAULT_MAX_CONCURRENT}", c=7)

        auto = AutoTrainer(QiangGuoXianFengAPI(base_url), max_jobs=max_concurrent)
        auto.manual_login()

        if task_code in ["1", "3"]:
            auto.watch_all()
        if task_code in ["2", "3"]:
            auto.do_lesson_exam_all()
        while not auto.is_subthread_completed():
            time.sleep(0.1)
        print("恭喜，所选的任务已完成!", c=2)
        input()
    except KeyboardInterrupt as arg:
        print("用户手动终止", c=1)
        print(type(arg).__name__, c=3)
        input()
    except BaseException as arg:
        print("发生了意外错误导致程序终止", c=1)
        print(type(arg).__name__, c=3)
        print(arg, c=3)
        input()
        raise arg
