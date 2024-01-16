import logging
import time

from .server import Server
from .states import app as app_
from .states.computer import ComputerStates

from BKVisionListener.base import BaseProperty


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
        if property_.listener_server_ip:
            pass
        app_name_list = [app["name"] for app in appList]
        for process in process_iter:
            if process["name"] in app_name_list:
                print(process)
                app_name_list.remove(process["name"])
            if not app_name_list:
                break
        for app in appList:
            if app["name"] in app_name_list:
                logging.error(f"start app {app.get('name')}")
                app_.start_app(app.get("name"), app.get("folder"), app.get("args"))

        time.sleep(property_.interval)
