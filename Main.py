# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
from typing import Optional

import json
import requests
import random
import threading
import time

from src.data.Config import Config
from src.data.Enums import HttpUserAgent, QiangGuoXianFengBaseURL
from src.data.Question import Question
from src.utils.Captcha import QiangGuoXianFengCaptcha
from src.utils.Cipher import rsa_encrypt
from src.utils.TerminalUI import STDOUT


class QiangGuoXianFengAPI:
    class InvalidRequestError(Exception):
        def __init__(self, *args):
            super().__init__(args)

    class PassportError(Exception):
        def __init__(self, *args):
            super().__init__(args)

    class UnauthorizedError(Exception):
        def __init__(self, *args):
            super().__init__(args)

    class Undefined(str):
        def __str__(self):
            raise ValueError("This value is undefined")

    DEFAULT_TIMEOUT = 15
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1

    def __init__(
        self,
        base_url: str = Undefined(),
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: int = DEFAULT_RETRY_DELAY,
    ):
        self.base_url = base_url
        self._headers = {"User-Agent": HttpUserAgent.generate_user_agent().value}
        self._timeout = max(1, timeout)
        self._max_retries = max(1, max_retries)
        self._retry_delay = max(0, retry_delay)

    @property
    def token(self):
        return self._headers["Token"]

    def _send(self, url, data=None, no_retry=False, as_json=False, use_get=False):
        for _ in range(max(1, self._max_retries)):
            try:
                method = requests.get if use_get else requests.post
                r = method(
                    url,
                    data=data if not as_json else None,
                    json=data if as_json else None,
                    headers=self._headers,
                    timeout=self._timeout,
                )
                if r.status_code != 200:
                    raise RuntimeError(r.status_code)
                d = json.loads(r.text)
                if d["code"] == 99999:
                    return d
                elif d["code"] == 10002:
                    raise QiangGuoXianFengAPI.PassportError(d.get("msg", "Unacceptable passport"))
                elif d["code"] == 10003:
                    raise QiangGuoXianFengAPI.UnauthorizedError(d.get("msg", "Unauthorized request"))
                elif d["code"] == 20000:
                    raise QiangGuoXianFengAPI.InvalidRequestError(f"API failed with code {d['code']}")
                else:
                    raise IOError(f"API failed with code {d['code']}")
            except IOError as arg:
                if no_retry:
                    raise arg
                time.sleep(self._retry_delay)
        raise RuntimeError("Max retires exceeded")

    def _fetch_pagination(self, url, data, page_size, max_page_num=1024, **kwargs):
        rst = []
        page_num = 1
        while page_num <= max_page_num:
            data["pageNum"] = page_num
            data["pageSize"] = page_size
            d = self._send(url, data, **kwargs)
            li = d["data"]["list"]
            if not isinstance(li, (list, tuple)):
                break
            rst.extend(li)
            if len(li) < page_size:
                break
            page_num += 1
        return rst

    def get_captcha(self):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/user/getCaptcha",
            use_get=True,
        )
        return d["data"]

    def login(self, user_id, user_pwd, captcha_id, captcha_code):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/user/login",
            data={
                "userSid": user_id,
                "password": rsa_encrypt(user_pwd),
                "id": captcha_id,
                "code": captcha_code,
            },
            no_retry=True,
        )
        self._headers["Token"] = d["data"]["token"]
        return d["data"]

    def get_user_info(self, new_token=None):
        if new_token:
            self._headers["Token"] = new_token
        d = self._send(f"{self.base_url}/trainingApi/v1/user/userInfo")
        return d["data"]

    def get_lesson_list(self):
        return self._fetch_pagination(f"{self.base_url}/trainingApi/v1/lesson/myLesson", {}, 8)

    def get_video_list(self, lesson_id):
        return self._fetch_pagination(
            f"{self.base_url}/trainingApi/v1/lesson/lessonVideos",
            {"lessonId": lesson_id, "showType": 0},
            10,
            as_json=True,
        )

    def get_resource_list(self, video_id):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/lesson/lessonVideoDetail",
            data={"videoId": video_id},
        )
        return d["data"]["resourceList"]

    def get_resource_detail(self, resource_id):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/lesson/lessonVideoResourceDetail",
            data={"resourceId": resource_id},
        )
        return d["data"]

    def set_resource_progress(self, resource_id, hhmmss):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/lesson/setResourceTime",
            data={"resourceId": resource_id, "videoTime": hhmmss},
        )
        return None

    def get_lesson_exam_list(self):
        d = self._send(f"{self.base_url}/trainingApi/v1/exam/examLessonList")
        return d["data"]

    def get_lesson_exam_start(self, lesson_id, stage_id):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/exam/startLessonExam",
            data={"stageId": stage_id, "lessonId": lesson_id},
        )
        return d["data"]

    def set_exam_temp_answer(self, record_id, answer_dict):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/exam/saveExamAnswer",
            data={"recordId": record_id, "answerList": answer_dict},
            as_json=True,
        )
        return None

    def set_exam_final_answer(self, record_id, answer_dict):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/exam/submitExam",
            data={"recordId": record_id, "answerList": answer_dict},
            as_json=True,
        )
        return d["data"]

    def get_exam_report(self, record_id, right_type=-1):
        d = self._send(
            f"{self.base_url}/trainingApi/v1/exam/examRecordDetail",
            data={"recordId": record_id, "rightType": right_type},
        )
        return d["data"]


class AutoTrainer:
    PLAYING_TIME_SCALE = 0.95
    FINISHING_REPORT_TIMES = 2
    START_PLAYING_INTERVAL = 3

    def __init__(
        self,
        api: QiangGuoXianFengAPI,
        max_jobs=5,
        pass_score=60,
        report_interval=10,
        report_randomness=1,
    ):
        self.api = api
        self.max_jobs = max_jobs
        self.pass_score = pass_score
        self._threads = []
        self._now_jobs = 0
        self._report_interval = abs(report_interval)
        self._report_randomness = abs(report_randomness)

    @staticmethod
    def _second_to_hhmmss(second: float):
        second = round(second)
        h = second // 3600
        m = second % 3600 // 60
        s = second % 60
        return f"{h:02}:{m:02}:{s:02}"

    @staticmethod
    def _hhmmss_to_second(hhmmss: str):
        if not hhmmss:
            return 0
        units = (3600, 60, 1)
        return sum([round(x * y) for x, y in zip(units, map(int, hhmmss.split(":")))])

    def is_subthread_completed(self):
        for i in self._threads:
            if i.is_alive():
                return False
        return True

    def auto_login(self):
        base_url = Config.get("connection")["baseUrl"]
        token = Config.get("connection")["token"]
        if not (base_url and token):
            return False

        display_line = STDOUT.add_line(f"正在校验身份信息", 5)
        try:
            self.api.base_url = base_url
            info = self.api.get_user_info(token)

            display_line.write("请确认", 3)
            STDOUT.add_line(f"您想要继续以 `{info['userName']}` 的身份登录 {self.api.base_url} 吗？", 7)
            STDOUT.add_line(f"  Y = 是(默认), N = 忘记此账号并重新登录", 7)
            input_line = STDOUT.add_line(f"  请选择 Y/N: ", 7)
            if input().upper() == "N":
                input_line.write("  已忘记此账号", 7)
            else:
                input_line.write("  已复用此账号", 7)
                STDOUT.add_line(f"欢迎 `{info['userName']}`!", 2)
                return True
        except QiangGuoXianFengAPI.InvalidRequestError:
            display_line.write(f"未能自动登录, 服务器似乎拒绝了请求", 7)
        except QiangGuoXianFengAPI.UnauthorizedError:
            display_line.write(f"未能自动登录, 可能是登录状态已过期", 7)

        Config.set("connection", {"baseUrl": "", "token": ""})
        Config.save_config()
        return False

    def manual_login(self):
        while True:
            try:
                STDOUT.add_line("请登录", 3)
                input_line = STDOUT.add_line("  请输入账号: ", 7)
                user_id = input()
                input_line.write(f"  已选择账号: {user_id}", 7)
                input_line = STDOUT.add_line("  请输入密码: ", 7)
                user_pwd = input()
                STDOUT.remove_line(input_line)
                captcha_line = STDOUT.add_line("  正在获取验证码", 5)
                captcha = self.api.get_captcha()
                captcha_line.write("  请在弹出的窗口中查看验证码图片，然后关闭该窗口", 6)
                captcha_obj = QiangGuoXianFengCaptcha(captcha["base64Str"])
                captcha_code = captcha_obj.solve_challenge()
                info = self.api.login(user_id, user_pwd, captcha["captchaId"], captcha_code)
                break
            except QiangGuoXianFengAPI.PassportError as arg:
                STDOUT.add_line(f"  登录失败，填写有误: {arg}", 3)
            except QiangGuoXianFengAPI.InvalidRequestError as arg:
                STDOUT.add_line(f"  登录失败，意外错误：{arg}", 3)
        STDOUT.add_line(f"登录成功，欢迎 `{info['userName']}`!", 2)

        STDOUT.add_line("请确认", 3)
        STDOUT.add_line(f"您想要记住登录状态以便下次使用吗？", 7)
        STDOUT.add_line(f"  Y = 是(默认), N = 否", 7)
        input_line = STDOUT.add_line(f"  请选择 Y/N: ", 7)
        if input().upper() == "N":
            input_line.write("  已选择 否", 7)
            Config.set("connection", {"baseUrl": "", "token": ""})
            Config.save_config()
        else:
            input_line.write("  已选择 是", 7)
            Config.set("connection", {"baseUrl": self.api.base_url, "token": self.api.token})
            Config.save_config()
        return True

    def _watch(self, resource_id: int, start_time: str, total_time: str):
        self._now_jobs += 1
        progress_line = STDOUT.add_line(
            f"    (视频资源 {resource_id}) 正在准备",
            7,
        )
        try:
            start = AutoTrainer._hhmmss_to_second(start_time)
            total = AutoTrainer._hhmmss_to_second(total_time)
            for now in range(start, total, self._report_interval):
                now += (random.random() - 0.5) * 2 * self._report_randomness
                now_time = AutoTrainer._second_to_hhmmss(now)
                progress_line.write(
                    f"    (视频资源 {resource_id}) 正在观看 {now_time} / {total_time} ({now / total:.0%})",
                    7,
                )
                self.api.set_resource_progress(resource_id, AutoTrainer._second_to_hhmmss(now))
                time.sleep(self._report_interval * AutoTrainer.PLAYING_TIME_SCALE)
            progress_line.write(f"    (视频资源 {resource_id}) 正在结束观看", 7)
            for _ in range(AutoTrainer.FINISHING_REPORT_TIMES):
                self.api.set_resource_progress(resource_id, total_time)
                time.sleep(self._report_interval * AutoTrainer.PLAYING_TIME_SCALE)
            progress_line.write(f"    (视频资源 {resource_id}) 已完成", 2)
        finally:
            self._now_jobs -= 1

    def watch(self, resource: dict):
        resource_id = resource["resourceId"]
        detail = self.api.get_resource_detail(resource_id)
        start_time = detail["resource_time"]
        total_time = detail["resourceDuration"]
        waiting_line = STDOUT.add_line(f"    (视频资源 {resource_id}) 正在排队", 7)
        while self._now_jobs >= self.max_jobs:
            time.sleep(0.1)
        thread = threading.Thread(
            target=self._watch,
            name=f"AutoTrain#{resource_id}",
            args=(resource_id, start_time, total_time),
            daemon=True,
        )
        STDOUT.remove_line(waiting_line)
        thread.start()
        self._threads.append(thread)

    def watch_all(self):
        STDOUT.remove_all_lines()
        STDOUT.add_line("正在查询课程列表", 5)
        lessons = self.api.get_lesson_list()
        for l in lessons:
            STDOUT.add_line(f"(课程 {l['lessonId']}) `{l['lessonTitle']}`", 6)
            videos = self.api.get_video_list(l["lessonId"])
            for v in videos:
                STDOUT.add_line(f"  (视频 {v['videoId']}) `{v['videoTitle']}`", 6)
                if not v["complete"]:
                    resources = self.api.get_resource_list(v["videoId"])
                    for r in resources:
                        self.watch(r)
                        time.sleep(AutoTrainer.START_PLAYING_INTERVAL)
        display_line = STDOUT.add_line("请等待子线程完成任务...", 5)
        while not auto.is_subthread_completed():
            time.sleep(0.1)
        display_line.write("此项任务已完成!", 2)
        time.sleep(1)

    def do_exam(self, exam_obj: dict):
        # Get exam info
        report_id = exam_obj["recordId"]
        stage_id = exam_obj["stageId"]
        question_list = sorted(map(Question.load_from_web_data, exam_obj["questionList"]))
        # Figure out answers
        has_right_answers = {}
        guess_answers = {}
        STDOUT.add_line(f"  (考卷 {report_id}) 一共有题目 {len(question_list)} 道", 7)
        memory = Question.load_from_kv_table(Config.get("memory"))
        for q in question_list:
            for m in memory:
                if m.id == q.id:
                    has_right_answers[q.id] = m.right_answer
                    break
            if q.id not in has_right_answers:
                if q.type in [1, 2, 3]:
                    # Single=1, Multiple=2, TF=3
                    guess_this = random.choices([a.id for a in q.answers], k=2 if q.type == 2 else 1)
                    guess_answers[q.id] = "|".join(map(str, guess_this))
                else:
                    raise RuntimeError(f"Not supported question type: {q.type}")
        STDOUT.add_line(f"  (考卷 {report_id}) 记得答案的题目有 {len(has_right_answers)} 道", 7)
        # Submit exam
        my_answers = {**guess_answers, **has_right_answers}
        saved_answers = {}
        display_line = STDOUT.add_line(f"  (考卷 {report_id}) 正在填写答案", 7)
        for j, k in enumerate(my_answers.keys()):
            time.sleep(random.randint(3, 5))
            saved_answers[k] = my_answers[k]
            self.api.set_exam_temp_answer(report_id, saved_answers)
            display_line.write(f"  (考卷 {report_id}) 正在填写答案 已填写 {j + 1} 道", 7)
        time.sleep(random.randint(3, 5))
        score = self.api.set_exam_final_answer(report_id, saved_answers)["score"]
        STDOUT.add_line(f"  (考卷 {report_id}) 已交卷", 7)
        # Get right answers
        question_list_with_answer = list(map(Question.load_from_web_data, self.api.get_exam_report(report_id)["list"]))
        for q in question_list_with_answer:
            q.stage_id = stage_id
        Config.set("memory", Question.dump_to_kv_table(sorted(memory + question_list_with_answer, key=lambda x: x.id)))
        Config.save_config()
        STDOUT.add_line(f"  (考卷 {report_id}) 已保存参考答案", 7)
        if score >= self.pass_score:
            STDOUT.add_line(f"  (考卷 {report_id}) 成功通过! 分数 {score}", 2)
            return True
        else:
            STDOUT.add_line(f"  (考卷 {report_id}) 未通过! 分数 {score}", 3)
            return False

    def do_lesson_exam_all(self, max_retries: int = 5):
        STDOUT.remove_all_lines()
        STDOUT.add_line("正在查询课程考试列表", 5)
        exams = self.api.get_lesson_exam_list()
        for e in exams:
            STDOUT.add_line(f"(课程考试 {e['lessonId']}) 当前最高分 {e['maxScore']} `{e['lessonTitle']}`", 6)
            if e["maxScore"] < self.pass_score:
                for i in range(max_retries):
                    time.sleep(random.randint(1, 2))
                    # Request to start an exam
                    STDOUT.add_line(f"  开始课程考试 {e["lessonId"]} (尝试 #{i + 1})", 5)
                    exam = self.api.get_lesson_exam_start(e["lessonId"], e["stageId"])
                    if self.do_exam(exam):
                        break
                STDOUT.add_line("  已跳过此课程考试, 因为达到了最大尝试次数", 3)
            else:
                STDOUT.add_line("  已跳过此课程考试, 因为分数已达标", 2)
        STDOUT.add_line("此项任务已完成!", 2)
        time.sleep(1)


def input_validated_int(prompt: str, default_val: int, min_val: Optional[int], max_val: Optional[int]):
    input_line = STDOUT.add_line(f"  {prompt}", 7)
    input_str = input()
    if input_str:
        try:
            input_val = int(input_str)
            if min_val is not None and input_val < min_val:
                input_line.write(f"  输入的数 {input_val} 过小 ")
            elif max_val is not None and input_val > max_val:
                input_line.write(f"  输入的数 {input_val} 过大 ")
            else:
                input_line.write(str(input_val), append=True)
                return input_val
        except:
            input_line.write(f"  输入非法 ")
    input_line.write(f"已设为默认值 {default_val}", append=True)
    return default_val


if __name__ == "__main__":
    try:
        STDOUT.add_line("开始运行!", 2)

        Config.save_config()

        auto = AutoTrainer(QiangGuoXianFengAPI())

        # Login
        if not auto.auto_login():
            base_url = ""
            while not base_url:
                STDOUT.add_line("请选择目标平台", 3)
                site_map_lines = {
                    site: STDOUT.add_line(
                        f"    平台代码 {site}：网址 {QiangGuoXianFengBaseURL.of_name(site).value}",
                        7,
                    )
                    for site in QiangGuoXianFengBaseURL.all_names()
                }
                input_line = STDOUT.add_line("  请输入完整的平台代码: ", 7)
                site_code = input()
                STDOUT.remove_line(input_line)
                for site in site_map_lines:
                    if site == site_code.upper():
                        site_map_lines[site].write(
                            f"  > 平台代码 {site}：网址 {QiangGuoXianFengBaseURL.of_name(site).value}",
                            2,
                        )
                        base_url = QiangGuoXianFengBaseURL.of_name(site_code).value
                        break

            auto.api.base_url = base_url
            auto.manual_login()

        # Select tasks
        do_option1 = False
        do_option2 = False
        while not (do_option1 or do_option2):
            STDOUT.add_line("请选择任务类型", 3)
            option1 = STDOUT.add_line("    1: 视频课程", 7)
            option2 = STDOUT.add_line("    2: 课程考试", 7)

            input_line = STDOUT.add_line("  请输入任务序号，用空格分隔多个序号: ", 7)
            task_code = input()
            STDOUT.remove_line(input_line)
            do_option1 = "1" in task_code.split()
            do_option2 = "2" in task_code.split()
            if do_option1:
                option1.write("  > 1: 视频课程", 2)
            if do_option2:
                option2.write("  > 2: 课程考试", 2)

        # Set options
        STDOUT.add_line("请输入任务参数", 3)
        if do_option1:
            auto.max_jobs = input_validated_int("同时观看课程数: ", 5, 1, 20)
        if do_option2:
            auto.pass_score = input_validated_int("通过考试所需分数: ", 60, 0, None)
        STDOUT.add_line("准备完毕", 2)
        time.sleep(1)

        # Start running
        if do_option1:
            auto.watch_all()
        if do_option2:
            auto.do_lesson_exam_all()
        STDOUT.add_line(f"恭喜, 所选的所有任务已完成!", 2)
        input()
    except KeyboardInterrupt as arg:
        STDOUT.add_line(f"用户手动终止 ", 1)
        STDOUT.add_line(type(arg).__name__, 3)
        input()
    except BaseException as arg:
        STDOUT.add_line(f"发生了意外错误导致程序终止 ", 1)
        STDOUT.add_line(type(arg).__name__, 3)
        STDOUT.add_line(str(arg), 3)
        input()
        raise arg
