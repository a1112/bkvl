import psutil
import pynvml



class ComputerStutas:
    def __init__(self):
        self.cpu = self.getCpuInfo()
        self.memory = self.getMemoryInfo()
        self.gpu = self.getGpuInfo()
        self.disk = self.getDiskInfo()

    def getCpuInfo(self):
        return {
            "cpu_times": psutil.cpu_times(),
            "cpu_percent": psutil.cpu_percent(),
            "cpu_times_percent": psutil.cpu_times_percent(),
            "cpu_count": psutil.cpu_count(),
            "cpu_stats": psutil.cpu_stats(),
            "cpu_freq": psutil.cpu_freq()
        }

    def getMemoryInfo(self):
        return {
            "virtual_memory": psutil.virtual_memory(),
            "swap_memory": psutil.swap_memory()
        }

    def getGpuInfo(self):
        pynvml.nvmlInit()
        gpuInfoList = []
        for i in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            gpuInfo = {}
            gpuInfo["name"] = pynvml.nvmlDeviceGetName(handle)
            gpuInfo["memory"] = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpuInfo["utilization"] = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpuInfo["temperature"] = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            gpuInfo["power"] = pynvml.nvmlDeviceGetPowerUsage(handle)
            gpuInfo["fan"] = pynvml.nvmlDeviceGetFanSpeed(handle)
            gpuInfo["clock"] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            gpuInfo["clock_mem"] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            gpuInfo["clock_max"] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            gpuInfo["clock_mem_max"] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            gpuInfo["clock_min"] = pynvml.nvmlDeviceGetMinClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)