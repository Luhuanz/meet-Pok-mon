#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from asyncio import AbstractEventLoop

import websockets
import asyncio
import json
from abc import abstractmethod
from websockets.legacy.server import Serve

from utils.Thread import MyThreadFunc


class MyServer:
    def __init__(self, host="0.0.0.0", port=10000):
        self.__host = host  # ip
        self.__port = port  # 端口号
        self.__listCmd = []  # 要发送的信息的列表
        self.__server: Serve = None
        self.__event_loop: AbstractEventLoop = None
        self.__running = True
        self.__pending = None
        self.isConnect = False

    def __del__(self):
        self.stop_server()

    # 接收处理
    async def __consumer_handler(self, websocket, path):
        async for message in websocket:
            await asyncio.sleep(0.01)
            await self.__consumer(message)

    # 发送处理
    async def __producer_handler(self, websocket, path):
        while self.__running:
            await asyncio.sleep(0.01)
            message = await self.__producer()
            if message:
                await websocket.send(message)

    async def __handler(self, websocket, path):
        self.isConnect = True
        print("websocket连接上:{}".format(self.__port))
        self.on_connect_handler()
        consumer_task = asyncio.ensure_future(
            self.__consumer_handler(websocket, path)
        )  # 接收
        producer_task = asyncio.ensure_future(
            self.__producer_handler(websocket, path)
        )  # 发送
        done, self.__pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in self.__pending:
            task.cancel()
            self.isConnect = False
            print("websocket连接断开:{}".format(self.__port))
            self.on_close_handler()

    async def __consumer(self, message):
        self.on_revice_handler(message)

    async def __producer(self):
        if len(self.__listCmd) > 0:
            message = self.on_send_handler(self.__listCmd.pop(0))
            return message
        else:
            return None

    @abstractmethod
    def on_revice_handler(self, message):
        pass

    @abstractmethod
    def on_connect_handler(self):
        pass

    @abstractmethod
    def on_send_handler(self, message):
        return message

    @abstractmethod
    def on_close_handler(self):
        pass

    # 创建server
    def __connect(self):
        self.__event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__event_loop)
        self.__isExecute = True
        if self.__server:
            print("server already exist")
            return
        self.__server = websockets.serve(self.__handler, self.__host, self.__port)
        asyncio.get_event_loop().run_until_complete(self.__server)
        asyncio.get_event_loop().run_forever()

    # 往要发送的命令列表中，添加命令
    def add_cmd(self, content):
        if not self.__running:
            return
        jsonObj = json.dumps(content)
        self.__listCmd.append(jsonObj)
        # util.log('命令 {}'.format(content))

    # 开启服务
    def start_server(self):
        MyThreadFunc(func=self.__connect, args=[]).start()

    # 关闭服务
    def stop_server(self):
        self.__running = False
        self.isConnect = False
        if self.__server is None:
            return
        self.__server.ws_server.close()
        self.__server = None
        try:
            all_tasks = asyncio.all_tasks(self.__event_loop)
            for task in all_tasks:
                while not task.cancel():
                    print("无法关闭！")
            self.__event_loop.stop()
            self.__event_loop.close()
        except BaseException as e:
            print("Error: {}".format(e))


# ui端server
class WebServer(MyServer):
    def __init__(self, host="0.0.0.0", port=10000):
        super().__init__(host, port)

    def on_revice_handler(self, message):
        pass

    def on_connect_handler(self):
        self.add_cmd({"panelMsg": ""})

    def on_send_handler(self, message):
        return message

    def on_close_handler(self):
        pass


# 数字人端server
class HumanServer(MyServer):
    def __init__(self, host="0.0.0.0", port=10000):
        super().__init__(host, port)

    def on_revice_handler(self, message):
        pass

    def on_connect_handler(self):
        web_server_instance = get_web_instance()
        web_server_instance.add_cmd({"is_connect": True})

    def on_send_handler(self, message):
        # util.log(1, '向human发送 {}'.format(message))
        if not self.isConnect:
            return None
        return message

    def on_close_handler(self):
        web_server_instance = get_web_instance()
        web_server_instance.add_cmd({"is_connect": False})


# 测试
class TestServer(MyServer):
    def __init__(self, host="0.0.0.0", port=10000):
        super().__init__(host, port)

    def on_revice_handler(self, message):
        print(message)

    def on_connect_handler(self):
        print("连接上了")

    def on_send_handler(self, message):
        return message

    def on_close_handler(self):
        pass


# 单例

__instance: MyServer = None
__web_instance: MyServer = None


def new_instance(host="0.0.0.0", port=10000) -> MyServer:
    global __instance
    if __instance is None:
        __instance = HumanServer(host, port)
    return __instance


def new_web_instance(host="0.0.0.0", port=10000) -> MyServer:
    global __web_instance
    if __web_instance is None:
        __web_instance = WebServer(host, port)
    return __web_instance


def get_instance() -> MyServer:
    return __instance


def get_web_instance() -> MyServer:
    return __web_instance


# <editor-fold desc="增加判断对象是否为空">
def instance_is_connect():
    _instance = get_instance()
    if __instance is not None:
        return False
    return _instance.isConnect


def add_web_instance_cmd(content):
    """
    添加websocket消息(web)
    Args:
        content ():

    Returns:

    """
    _web_instance = get_web_instance()
    if __web_instance is not None:
        _web_instance.add_cmd(content)


def add_instance_cmd(content):
    """
    添加websocket消息(内)
    Args:
        content ():

    Returns:

    """
    _instance = get_instance()
    if __instance is not None:
        _instance.add_cmd(content)


# </editor-fold>


if __name__ == "__main__":
    testServer = TestServer(host="0.0.0.0", port=10000)
    testServer.start_server()
