# -*- coding: UTF-8 -*-
import ast
import json
import random
import re
import time
from PIL import Image

from config import *


def downloadCaptcha(session):
    with open("captcha.jpg", "wb") as f:
        f.write(session.get(url=captcha_url, headers=header).content)


def login(session):
    cpaptcha_switch = input("是否尝试自动识别验证码?[y/n]")
    if cpaptcha_switch == 'y' or cpaptcha_switch == 'Y':
        import muggle_ocr
        while True:
            with open("captcha.jpg", 'rb') as f:
                captcha_bytes = f.read()
                sdk = muggle_ocr.SDK(model_type=muggle_ocr.ModelType.Captcha)
                text = sdk.predict(image_bytes=captcha_bytes)
                login_data = {
                    'j_username': j_username,
                    'j_password': j_password,
                    'j_captcha': text
                }
                print("识别的验证码为:{}".format(text))
                try:
                    response = session.post(
                        url=login_url, headers=header, data=login_data).text
                    if "欢迎您" in response:
                        print("登陆成功！")
                        return "success"
                    else:
                        print("自动识别验证码失败，三秒后准备尝试重新登录!")
                        time.sleep(3)
                        return "failed"
                except Exception as e:
                    print("def login() 出现问题:" + str(e))
                    return None
    else:
        img = Image.open('captcha.jpg')
        img.show()
        login_data = {
            'j_username': j_username,
            'j_password': j_password,
            'j_captcha': input("请输入验证码:")
        }
        try:
            response = session.post(
                url=login_url, headers=header, data=login_data).text
            if "欢迎您" in response:
                print("登陆成功！")
                return "success"
            else:
                return "failed"
        except Exception as e:
            print("def login() 出现问题:" + str(e))
            return None

def getAleadyCourse(session):
    aleady_select_course_list = []
    try:
        response = session.get(
            url=aleady_select_course_url, headers=header).text
        for each in json.loads(response)['xkxx'][0]:
            aleady_select_course_list.append(json.loads(
                response)['xkxx'][0][each]['courseName'])
        return aleady_select_course_list
    except Exception as e:
        print("def getAleadyCourse() 出现问题:" + str(e))
        return None


def courseSelect(session, each_course, aleadySelectCourse):
    print("课程名:" + each_course['kcm'] + " 教师:" +
          each_course['skjs'] + " 课余量:" + str(each_course['bkskyl']))
    if each_course['bkskyl'] > 0 and courseName not in (course for course in aleadySelectCourse) and courseNum == \
            each_course['kch'] and coursekxhNum == each_course['kxh']:
        kcm = each_course['kcm']  # 课程名
        kch = each_course['kch']  # 课程号
        kxh = each_course['kxh']  # 课序号
        status = queryTeacherJL(session, kch, kxh)
        if status is None:
            return
        kcms = getKcms(kcm + "(" + kch + "@" + kxh + ")")  # 获得编码后的课程信息
        course_name = kch + "@" + kxh + "@" + selectcourse_xueqi
        tokenValue = getTokenValue(session)
        if tokenValue is None:
            return
        select_data = {
            'dealType': 5,
            'fajhh': "",
            'kcIds': course_name,
            'kcms': kcms,
            'sj': '0_0',
            'searchtj': '',
            'kclbdm': '',
            'inputCode': '',
            'tokenValue': tokenValue
        }
        try:
            c = session.post(url=select_url, data=select_data).text
            print("选课状态：", c)
            exit()
        except Exception as e:
            print("def courseSelect() 出现问题:" + str(e))
    else:
        pass


def getTokenValue(session):
    try:
        response = session.get(url=courseSelect_url, headers=header).text
        return re.compile("([a-fA-F0-9]{32})").findall(response)[0]
    except Exception as e:
        print("def getTokenValue() 出现问题:" + str(e))
        return None


def getKcms(kms):
    kcms = ""
    for each in kms:
        kcms += (str(ord(each)) + ",")
    return kcms


def getFreeCourseList(session):
    try:
        response = session.post(
            url=courseList_url, headers=header, data=list_data).content.decode()
        return ast.literal_eval(json.loads(response)['rwRxkZlList'])
    except Exception as e:
        print("def getFreeCourseList() 出现问题:" + str(e))
        return None


def queryTeacherJL(session, kch, kxh):
    data = {
        "id": selectcourse_xueqi + "@" + kch + "@" + kxh
    }
    try:
        response = session.post(url=queryTeacherJL_url,
                                data=data, headers=header).content.decode()
        if(response):
            return response
    except Exception as e:
        print("def queryTeacherJL() 出现问题:" + str(e))
        return None


def main(session):
    while True:
        # 下载验证码
        try:
            downloadCaptcha(session)
        except Exception as e:
            print("def downloadCaptcha() 出现问题:" + str(e))
            continue
        # 登录
        loginResponse = login(session)
        if loginResponse == "success":
            break
        else:
            print("登陆失败！")
    clock = 1
    while True:
        print("\n正在第{}轮选课！".format(clock))
        # 先查询已选课程
        aleadySelectCourse = getAleadyCourse(session)
        # 查询不到已选课程就重新查询
        if aleadySelectCourse is None:
            continue
        if courseName in aleadySelectCourse:
            print("你已经选择这门课了！")
            exit()
        # 然后查询要选课程的课余量
        courseList = getFreeCourseList(session)
        if courseList is None:
            continue
        # 如果这门课没有被选择开始选课
        for each_course in courseList:
            courseSelect(session, each_course, aleadySelectCourse)
        clock = clock + 1
        time.sleep(random.uniform(1.5, 3))
