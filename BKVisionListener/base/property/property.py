import os
import yaml

from BKVisionListener import CONFIG


class BaseProperty(object):
    def __init__(self, yaml_path: str):
        def _load_yaml(yaml_url):
            with open(yaml_url, 'r', encoding=CONFIG.ENCODE) as f:
                yaml_dict_ = yaml.load(f, Loader=yaml.FullLoader)
                if yaml_dict_.get('extends', None):
                    extends = yaml_dict_.pop('extends')
                    extends_path = os.path.join(self.dir_path, extends)
                    extends_dict = _load_yaml(extends_path)
                    extends_dict.update(yaml_dict_)
                    yaml_dict_ = extends_dict
                return yaml_dict_

        if os.path.isdir(yaml_path):
            yaml_path = os.path.join(yaml_path, "config.yaml")
        self.dir_path = os.path.dirname(yaml_path)
        if os.path.exists(yaml_path) is False:
            raise FileNotFoundError(f"File {yaml_path} not found")
        self.yaml_path = yaml_path
        self.yaml_dict = _load_yaml(self.yaml_path)
        self.interval = self.yaml_dict.get("interval", 5)
        self.listener_server_ip = self.yaml_dict.get("server_ip",None)
        self.listener_server_port = self.yaml_dict.get("server_port",8089)
        self.listener_app = self.yaml_dict.get("app",[])
        self.listener_disk = self.yaml_dict.get("disk",[])
        self.maxDiskSize = self.yaml_dict.get("maxDiskSize",95)
        self.run_status = True
