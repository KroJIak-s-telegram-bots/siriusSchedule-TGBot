import requests

clearTime = 1688360400000-28800000 # 00:00 3 июля

def getSchedule():
    response = requests.get('http://kaktus23.ru:81/direction?name=%D0%9D%D0%B0%D1%83%D0%BA%D0%B0')
    dataJson = response.json()
    data = {}
    for group in dataJson:
        nameGroup = group['key']['name']
        data[nameGroup] = []
        for task in group['value']:
            startNormalTime = ((task['startTime']-clearTime)//1000) // 60
            endNormaltime = ((task['endTime']-clearTime)//1000) // 60
            data[nameGroup].append({'title': task['title'],
                                    'startTime': startNormalTime,
                                    'endTime': endNormaltime,
                                    'address': task['address']})
    return data

if __name__ == '__main__':
    getSchedule()