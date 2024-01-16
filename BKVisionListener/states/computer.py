import psutil
import pynvml
import ctypes


class CpuStates:
    def __init__(self):
        pass

    @property
    def cpu(self):
        cpu_times = psutil.cpu_times()
        cpu_times = {
            "user": cpu_times.user,
            "system": cpu_times.system,
            "idle": cpu_times.idle,
            "interrupt": cpu_times.interrupt,
            "dpc": cpu_times.dpc
        }
        cpu_times_percent = psutil.cpu_times_percent()
        cpu_times_percent = {
            "user": cpu_times_percent.user,
            "system": cpu_times_percent.system,
            "idle": cpu_times_percent.idle,
            "interrupt": cpu_times_percent.interrupt,
            "dpc": cpu_times_percent.dpc
        }
        cpu_stats = psutil.cpu_stats()
        cpu_stats = {
            "ctx_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "soft_interrupts": cpu_stats.soft_interrupts,
            "syscalls": cpu_stats.syscalls
        }
        return {
            "cpu_times": cpu_times,
            "cpu_percent": psutil.cpu_percent(),
            "cpu_times_percent": cpu_times_percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_stats": cpu_stats,
            "cpu_freq": psutil.cpu_freq()
        }

    def __dict__(self):
        return self.cpu


class MemoryStates:

    @property
    def memory(self):
        virtual_memory = psutil.virtual_memory()
        virtual_memory = {
            "total": virtual_memory.total,
            "available": virtual_memory.available,
            "percent": virtual_memory.percent,
            "used": virtual_memory.used,
            "free": virtual_memory.free,
        }
        swap_memory = psutil.swap_memory()
        swap_memory = {
            "total": swap_memory.total,
            "used": swap_memory.used,
            "free": swap_memory.free,
            "percent": swap_memory.percent,
            "sin": swap_memory.sin,
            "sout": swap_memory.sout
        }
        return {
            "virtual_memory": virtual_memory,
            "swap_memory": swap_memory
        }

    def __dict__(self):
        return self.memory


class DiskStates:

    @property
    def disk(self):
        disk_partitions = psutil.disk_partitions()
        disk_usages = {}
        for disk in disk_partitions:
            diskDevice = psutil.disk_usage(disk.device)
            diskDevice = {
                "total": diskDevice.total,
                "used": diskDevice.used,
                "free": diskDevice.free,
                "percent": diskDevice.percent
            }
            disk_usages[disk.device] = diskDevice

        disk_io_counters = psutil.disk_io_counters(perdisk=True)
        disk_io_countersDict = {}
        for disk_io in disk_io_counters:
            disk_ioV = disk_io_counters[disk_io]
            disk_ioV = {
                "read_count": disk_ioV.read_count,
                "write_count": disk_ioV.write_count,
                "read_bytes": disk_ioV.read_bytes,
                "read_time": disk_ioV.read_time,
                "write_time": disk_ioV.write_time
            }
            disk_io_countersDict[disk_io] = disk_ioV

        return {
            "disk_io_counters": disk_io_countersDict,  # IO 计数
            "disk_partitions": disk_partitions,
            "disk_usage": disk_usages
        }

    def __dict__(self):
        return self.disk


class NetworkStates:
    def __init__(self):
        pass

    @property
    def network(self):
        return {
            "net_io_counters": {k: {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            } for k, net_io in psutil.net_io_counters(pernic=True).items()
            },
            "net_if_addrs": {
                k: [{
                    "family": net_if.family.name,
                    "address": net_if.address,
                    "netmask": net_if.netmask,
                    "broadcast": net_if.broadcast,
                    "ptp": net_if.ptp
                } for net_if in net_ifs]
                for k, net_ifs in psutil.net_if_addrs().items()
            },
            "net_if_stats": psutil.net_if_stats()
        }

    def __dict__(self):
        return self.network


class GpuStates:
    def __init__(self):
        pass

    @property
    def gpu(self):
        pynvml.nvmlInit()
        deviceCount = pynvml.nvmlDeviceGetCount()
        gpuList = []
        for i in range(deviceCount):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpuList.append({
                "name": pynvml.nvmlDeviceGetName(handle),
                "memory": {
                    "total": memory_info.total,
                    "used": memory_info.used,
                    "free": memory_info.free
                },
                "utilization": {
                    "gpu": utilization.gpu,
                    "memory": utilization.memory
                },
                "temperature": pynvml.nvmlDeviceGetTemperature(handle, 0),
                "power": pynvml.nvmlDeviceGetPowerUsage(handle) / 100,
                "fan": pynvml.nvmlDeviceGetFanSpeed(handle)
            })
        pynvml.nvmlShutdown()
        return gpuList

    def __dict__(self):
        return self.gpu


class ScreenStates:

    @property
    def screen(self):
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        screen_log_pixels = gdi32.GetDeviceCaps(user32.GetDC(0), 88)
        scale_factor = screen_log_pixels / 96
        return {
            "screen_size": {
                "width": user32.GetSystemMetrics(0),
                "height": user32.GetSystemMetrics(1)
            },
            "screen_log_pixels": screen_log_pixels,
            "scale_factor": scale_factor
        }

    def __dict__(self):
        return self.screen


class OthersStates:

    @property
    def others(self):
        return {
            "users": psutil.users(),
            "boot_time": psutil.boot_time()
        }

    def __dict__(self):
        return self.others


class ComputerStates:

    @property
    def cpu(self):
        return CpuStates().cpu

    @property
    def memory(self):
        return MemoryStates().memory

    @property
    def disk(self):
        return DiskStates().disk

    @property
    def network(self):
        return NetworkStates().network

    @property
    def gpu(self):
        return GpuStates().gpu

    @property
    def others(self):
        return OthersStates().others

    @property
    def screen(self):
        return ScreenStates().screen

    def __dict__(self):
        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "network": self.network,
            "gpu": self.gpu,
            "screen": self.screen,
            "others": self.others
        }


if __name__ == '__main__':
    print(ComputerStates().__dict__())
