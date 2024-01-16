import psutil


def pids():
    return psutil.pids()


def process_iter():
    return [proc.as_dict(attrs=['pid', 'name', 'username']) for proc in psutil.process_iter()]


def has_app(name):
    return name in [proc.name() for proc in psutil.process_iter()]


def kill_pid(pid):
    if pid in psutil.pids():
        return psutil.Process(pid).kill()
    else:
        return False


if __name__ == '__main__':
    print(process_iter())
