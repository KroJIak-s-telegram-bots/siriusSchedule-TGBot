import time
from os.path import join as joinPath

from configparser import ConfigParser

def getConfigObject(botConfigPath):
    config = ConfigParser()
    config.read(botConfigPath)
    return config

def getLocalTime(format):
    localTime = time.localtime()
    match format:
        case 0: return time.strftime('%H:%M:%S', localTime)
        case 1: return time.strftime('%d_%m_%y_%H_%M_%S', localTime)

def getFullLocalTime():
    currentTime = getLocalTime(0)
    hour, minute, second = map(int, currentTime.split(':'))
    fullLocalTime = hour * 3600 + minute * 60 + second
    return fullLocalTime

def getLogFileName():
    localTime = getLocalTime(1)
    resultName = f'log_{localTime}.log'
    return resultName