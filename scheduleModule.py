import requests
from datetime import datetime, timedelta
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")
timeDifference = int(config['Data']['timeDifference'])

def getSchedule():
    response = requests.get('http://kaktus23.ru:81/direction?name=%D0%9D%D0%B0%D1%83%D0%BA%D0%B0')
    dataJson = response.json()
    data = {}
    for group in dataJson:
        nameGroup = group['key']['name']
        data[nameGroup] = []
        for task in group['value']:
            startDate = datetime.fromtimestamp(task['startTime'] / 1000) + timedelta(hours=(timeDifference * -1))
            endDate = datetime.fromtimestamp(task['endTime'] / 1000) + timedelta(hours=(timeDifference * -1))
            originalStartTime = task['startTime'] / 1000 + (timeDifference * 3600 * -1)
            originalEndTime = task['endTime'] / 1000 + (timeDifference * 3600 * -1)
            startNormalTime = startDate.hour * 60 + startDate.minute
            endNormaltime = endDate.hour * 60 + endDate.minute
            data[nameGroup].append({'title': task['title'],
                                    'startTime': startNormalTime,
                                    'endTime': endNormaltime,
                                    'originalStartTime': originalStartTime,
                                    'originalEndTime': originalEndTime,
                                    'address': task['address']})
    return data

if __name__ == '__main__':
    getSchedule()