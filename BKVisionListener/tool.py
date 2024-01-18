import logging
import os
import shutil
import time

from BKVisionListener.server import Server
from BKVisionListener.states import app as app_
from BKVisionListener.states.computer import ComputerStates

from BKVisionListener.base import BaseProperty


def is_root_path(path):
    # 对于Unix-like系统
    if os.name == 'posix':
        return path == "/"

    # 对于Windows系统
    elif os.name == 'nt':
        return os.path.abspath(path) == path and path.endswith(":\\")
    # 其他系统（不太常见）
    else:
        raise NotImplementedError("Unsupported operating system")


def delete_oldest_items(folder_path, n):
    # 获取文件夹中所有项目的路径及其修改时间
    items = [(os.path.join(folder_path, item), os.path.getmtime(os.path.join(folder_path, item))) for item in
             os.listdir(folder_path)]

    # 根据修改时间对项目进行排序
    items.sort(key=lambda x: x[1])

    # 删除最早的n个项目
    for item, _ in items[:n]:
        if os.path.isfile(item):
            os.remove(item)
        elif os.path.isdir(item):
            shutil.rmtree(item)
        logging.debug(f"Deleted: {item}")


def resolver(config):
    property_ = config
    if isinstance(config, str):
        property_ = BaseProperty(config)

    if property_.listener_server_ip:
        Server(property_.listener_server_ip, property_.listener_server_port).start()

    appList = []
    if property_.listener_app:
        appList = property_.listener_app
    while property_.run_status:
        computerStates = ComputerStates().__dict__()
        process_iter = app_.process_iter()
        app_name_list = [app["name"] for app in appList]
        for process in process_iter:
            if process["name"] in app_name_list:
                app_name_list.remove(process["name"])
            if not app_name_list:
                break
        for app in appList:
            if app["name"] in app_name_list:
                logging.error(f"start app {app.get('name')}")
                app_.start_app(app.get("name"), app.get("folder"), app.get("args"))

        def get_disk_usage(disk_path):
            total, used, free = shutil.disk_usage(disk_path)
            # 计算使用率
            usage_percent = (used / total) * 100
            return usage_percent

        # 使用示例

        for disk in property_.listener_disk:
            path = disk.get("path")

            if is_root_path(path):
                logging.error(f"root path {path} not support")
                continue

            clean = disk.get("clean")
            if get_disk_usage(path) > property_.maxDiskSize:
                # 根据时间排序，删除最早的文件
                delete_oldest_items(path, clean)

        time.sleep(property_.interval)
