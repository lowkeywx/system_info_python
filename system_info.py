import psutil
import platform
import getpass
import datetime
from pynvml import *

from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI

app = FastAPI()

SYSTEM_TIME = "system_time"
SYSTEM_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SYSTEM_NAME = "system_name"
SYSTEM_VERSION = "system_version"
SYSTEM_CPU = "system_cpu"
SYSTEM_MERORY = "system_memory"
SYSTEM_DISK = "system_hard_disk"
SYSTEM_GPU = "system_gpu"
KEY_NAME = "name"
KEY_COUNT = "count"
KEY_PERCENT = "percent"
KEY_FREQ = "freq"
KEY_TOTAL = "total"
KEY_USED = "used"
KEY_FREE = "free"
KEY_STAT = "state"
KEY_VERSION = "version"
KEY_GPUS = "gpus"
KEY_MEMORY = "memory"
KEY_TEMPERATURE = "temperature"


PHYSICAL_HARD_DISK_PATH = os.getenv('PHYSICAL_HARD_DISK_PATH', '/')

class SystemInfo():
    @staticmethod
    def physical_system_time():
        """
        获取系统启用时间
        """
        return {SYSTEM_TIME: datetime.datetime.fromtimestamp(psutil.boot_time()).strftime(SYSTEM_TIME_FORMAT)}

    @staticmethod
    def physical_username():
        """
        获取当前用户名
        """
        return {
            "system_user": getpass.getuser()
        }

    @staticmethod
    def physical_platfrom_system():
        """
        获取当前机器系统
        """
        u_name = platform.uname()
        return {SYSTEM_NAME: u_name.system, SYSTEM_VERSION: u_name.version}

    @staticmethod
    def physical_cpu():
        """
        获取机器物理CPU信息
        """
        systemName = platform.system().lower()
        cpu_name = "unkown"
        if(platform.system().lower() == "linux"):
            with open('/proc/cpuinfo', 'r') as f:
                for line in f.readlines():
                    if line.startswith('model name'):
                        cpu_name = line.split(':')[1].strip()
        elif systemName == "darwin":
            pass
        else:
            import wmi
            win = wmi.WMI()
            cpulist = win.Win32_Processor()
            for cpu in cpulist:
                cpu_name = cpu.name
                break
        
        return {SYSTEM_CPU:{
                KEY_NAME: cpu_name,
                KEY_COUNT: psutil.cpu_count(logical=False),
                KEY_FREQ: psutil.cpu_freq(),
                KEY_PERCENT: psutil.cpu_percent()
                }}

    @staticmethod
    def physical_memory():
        """
        获取机器物理内存(返回字节bytes)
        """
        return {SYSTEM_MERORY:
                {
                    KEY_TOTAL: round(psutil.virtual_memory().total, 2),
                    KEY_USED: psutil.virtual_memory().used,
                    KEY_FREE:psutil.virtual_memory().free,
                    KEY_PERCENT: psutil.virtual_memory().percent
                }}

    @staticmethod
    def floating_point_precision(number, precision=4):
        return round(number, precision) * 100

    @staticmethod
    def physical_hard_disk():
        """
        获取机器硬盘信息(字节bytes)
        """
        disk_usage = psutil.disk_usage(PHYSICAL_HARD_DISK_PATH)
        return {SYSTEM_DISK: 
            {
                KEY_TOTAL:disk_usage.total, 
                KEY_USED: disk_usage.used,
                KEY_FREE: disk_usage.free,
                KEY_PERCENT: SystemInfo.floating_point_precision(disk_usage.used / disk_usage.total)
            }}

    @staticmethod
    def nvidia_info():
        nvidia_dict = {
            KEY_STAT: True,
            KEY_VERSION: "",
            KEY_COUNT: 0,
            KEY_GPUS: []
        }
        try:
            nvmlInit()
            nvidia_dict[KEY_VERSION] = nvmlSystemGetDriverVersion()
            nvidia_dict[KEY_COUNT] = nvmlDeviceGetCount()
            for i in range(nvidia_dict[KEY_COUNT]):
                handle = nvmlDeviceGetHandleByIndex(i)
                memory_info = nvmlDeviceGetMemoryInfo(handle)
                gpu = {
                    KEY_NAME: nvmlDeviceGetName(handle),
                    KEY_PERCENT: nvmlDeviceGetUtilizationRates(handle).gpu,
                    KEY_TEMPERATURE: nvmlDeviceGetTemperature(handle, 0),
                    KEY_MEMORY: {                    
                        KEY_TOTAL: memory_info.total,
                        KEY_USED: memory_info.used,
                        KEY_FREE: memory_info.free,
                        KEY_PERCENT: SystemInfo.floating_point_precision(memory_info.used/memory_info.total)
                    }
                }
                nvidia_dict[KEY_GPUS].append(gpu)
        except NVMLError as _:
            nvidia_dict[KEY_STAT] = False
        except Exception as _:
            nvidia_dict[KEY_STAT] = False
        finally:
            try:
                nvmlShutdown()
            except:
                pass
        return {SYSTEM_GPU: nvidia_dict}

    @staticmethod
    def merge(info_list):
        data = {}
        for item in info_list:
            data.update(
                item()
            )
        return data

    @staticmethod
    def computer_info():
        data = SystemInfo.merge(
            [
                SystemInfo.physical_username,
                SystemInfo.physical_platfrom_system,
                SystemInfo.physical_cpu,
                SystemInfo.physical_memory,
                SystemInfo.physical_hard_disk,
                SystemInfo.nvidia_info
            ]
        )
        return data

@app.get("/systeminfo")
def getSystemInfo():
    return SystemInfo.computer_info()

if __name__ == '__main__':
    computer = SystemInfo.computer_info()
    print(computer)
