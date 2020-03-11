#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flask import request, Flask
import queue
import json
import time
import re
import threading
import numpy as np
import urllib.request
import cv2
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


app = Flask(__name__)

q = queue.Queue(2000)  # 建立一个队列长度为1000，较长的队列可以作为缓冲
executor = ThreadPoolExecutor(max_workers=127)  # 线程池
process = ProcessPoolExecutor(10)
# lock = threading.Lock

# 封装数据
class Item:
    def __init__(self, event, data, feedback):
        self.event = event
        self.data = data
        self.feedback = feedback


# 接收线程请求
@app.route('/testB', methods=['POST'])
def getRequest():
    event = threading.Event()  # 创建一个事件管理标志
    if 'ts' not in json.loads(request.get_data()) or 'url' not in json.loads(request.get_data()):
        print("请求中的数据有误")
    item = Item(event, request.get_data(), "NULL")  # 初始化线程请求
    # print("收到了")
    q.put(item)
    # print(q.qsize())
    if q.qsize() >= 800:  # 判断队列长度是否过长
        item.feedback = {
            'busy': '请求数量过于密集'
        }
        return item.feedback
    event.wait()  # 线程阻塞
    return item.feedback


# 处理线程请求
def revQueue(batch_size):
    flag = 0  # flag 用于标记 距离上一次执行AI操作的时间
    nowTime = time.time()
    nowTime = int(round(nowTime * 1000))
    while 1:
        if flag == 0:
            nowTime = time.time()
            nowTime = int(round(nowTime * 1000))

        # 当请求队列长度大于batch_size，进行统一处理
        if q.qsize() >= batch_size:
            rev = queue.Queue(batch_size)
            for i in range(batch_size):
                item = q.get()
                rev.put(item)
            pass
            tt = executor.submit(handleAI, rev, batch_size)  # 进行AI处理
            flag = 0  # 重置flag为0，重新获取当前时间

            # 当接收 不到batch_size数量请求，或者长时间没执行AI处理时
        else:
            flag = 1
            afterTime = time.time()
            afterTime = int(round(afterTime * 1000))  # 获取时间差
            if afterTime - nowTime >= 1000:  # 大于1500毫秒时 返回错误信息
                print("超时处理")
                for i in range(q.qsize()):
                    item = q.get()
                    feedback = {
                        'error': '请求数量未满足需求'
                    }
                    item.feedback = feedback
                    event = item.event
                    event.set()  # 唤醒线程
                flag = 0  # 重置flag为0，重新获取当前时间
                pass


# AI处理
def handleAI(queue, batch_size):
    # handle AI
    print("---------- handle AI Start-----------")
    print("---------------- AI ----------------")
    print("-----------handle AI OK--------------")
    for x in range(batch_size):
        item = queue.get()
        data = str(item.data, 'utf-8')
        data = re.sub('\'', '\"', data)
        data = json.loads(data)
        # 耗时操作
        url = data['url']
        resp = urllib.request.urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        rects = data['ts']
        rects = int(rects)
        t = time.time()
        now = int(round(t * 1000))
        # 封装返回的数据
        feedback = {
            'rec_ts': rects,
            'resp_ts': now,
            'ts_diff': now - rects
        }
        item.feedback = feedback
        event = item.event
        event.set()  # 唤醒线程


if __name__ == '__main__':

    #` 最多创建10个进程执行getRequest方法
    for i in range(10):
        process.submit(getRequest)

    t = threading.Thread(target=revQueue, args=(10,))  # 创建线程执行
    t.setDaemon(True)
    t.start()
    app.run(threaded=True)
