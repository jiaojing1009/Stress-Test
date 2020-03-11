#!/usr/bin/python
# # -*- coding: UTF-8 -*-
from concurrent.futures import ThreadPoolExecutor
import requests
import time
import json
from requests import exceptions

executor = ThreadPoolExecutor(max_workers=127)


# 封装结果集
class Result:
    def __init__(self, successRequest, failureRequest, response, totalTs):
        self.successRequest = successRequest  # 成功的请求数
        self.failureRequest = failureRequest  # 失败的请求数
        self.response = response  # 请求结果
        self.totalTs = totalTs  # 总共耗时


result = Result(0, 0, '', 0)  # 初始化结果（成功的请求数，失败的请求数，请求结果）


def run():
    # 通过exceptions异常来判断请求是否成功
    try:
        t = time.time()
        now = int(round(t * 1000))
        payload = {'ts': now, 'url': 'http://www.pyimagesearch.com/wp-content/uploads/2015/01/google_logo.png'}
        response = requests.post("http://127.0.0.1:5000/testB", data=json.dumps(payload), timeout=3)  # 发起网络请求
        result.response = response
        if 'ts_diff' not in response.json() and 'error' not in response.json():
            print("Json数据格式异常")
            result.failureRequest = result.failureRequest + 1
    except exceptions.Timeout as e:
        print('请求超时')
        result.failureRequest = result.failureRequest + 1
        # print('请求超时：' + str(e.message))

    except exceptions.HTTPError as e:
        print('http请求错误')
        result.failureRequest = result.failureRequest + 1
        # print('http请求错误:' + str(e.message))

    except exceptions.URLRequired as e:
        print('URL缺失异常')
        result.failureRequest = result.failureRequest + 1
        # print('URL缺失异常:' + str(e.message))

    else:
        if response.status_code == 200:
            # 如果请求数量不足 batch_size 则输出error错误
            if 'error' in response.json():
                print("请求错误:" + str(response.json()['error']))
                result.failureRequest = result.failureRequest + 1

            else:
                print('请求耗时:' + str(response.json()['ts_diff'])) \

                result.totalTs = result.totalTs + float(response.json()['ts_diff']) # 记录ts_diff总共耗时
                result.successRequest = result.successRequest + 1  # 记录成功的请求次数
                pass
            # 如果请求数量过多，导致B服务器队列过长，则输出busy
            if 'busy' in result.response.json():
                print(str(response.json()['busy']))
        else:
            result.failureRequest = result.failureRequest + 1
            print('请求错误：' + str(response.status_code) + ',' + str(response.reason))
    # 当返回的请求数量达到 2000 个时，计算出QPS
    if result.successRequest + result.failureRequest == 2000:
        endTime = time.time()
        endTime = int(round(endTime * 1000))
        QBS = float(result.successRequest / (endTime - starTime))
        print("===========结果============")
        print("总共执行时间:" + str(endTime - starTime) + "ms")
        print("成功的请求总数为: " + str(result.successRequest))
        print("失败的请求总数为: " + str(result.failureRequest))
        print("平均ts_diff为:" + str(float(result.totalTs / 2000)) + "ms")
        print("QPS为: " + str(QBS * 1000))


def createThreading():
    for i in range(2000):
        print("-----------in-----------")
        # 当请求数量过多时，sleep3秒
        if 'busy' in result.response:
            time.sleep(3)
        t = executor.submit(run)


if __name__ == '__main__':
    starTime = time.time()
    starTime = int(round(starTime * 1000))
    createThreading()
    # run()
