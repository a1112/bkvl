import psutil
from pathlib import Path
import subprocess


def pids():
    return psutil.pids()


def process_iter():
    return [proc.as_dict(attrs=['pid', 'name',
                                "exe","cmdline","status","create_time","cwd"]) for proc in psutil.process_iter()]


def kill_pid(pid):
    if pid in psutil.pids():
        return psutil.Process(pid).kill()
    else:
        return False


def start_app(name,dir_path,args):
    print(dir_path)
    print(name)
    print(args)
    subprocess.Popen([str(Path(dir_path)/name),args])
    return True


if __name__ == '__main__':
    print(process_iter())
