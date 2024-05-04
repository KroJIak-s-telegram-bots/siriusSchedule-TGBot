import requests

from utils.const import ConstPlenty

const = ConstPlenty()

class Group():
    def __init__(self, groupData):
        self.id = int(groupData['key']['id'])
        self.name = groupData['key']['name']
        self.events = [Event(eventData) for eventData in groupData['value']]

    def __str__(self):
        return f'Группа: {self.name}'

class Event():
    def __init__(self, eventData):
        self.id = int(eventData['id'])
        self.title = eventData['title']
        self.address = eventData['address']
        self.startTime = int(eventData['startTime'])
        self.endTime = int(eventData['endTime'])
        self.active = False

    def __str__(self):
        return f'Событие: {self.title}'

class Scheduler():
    def getGroups(self):
        response = requests.get(const.schedule.url)
        infoJson = response.json()
        groups = [Group(groupData) for groupData in infoJson]
        return groups

    def getGroupNames(self):
        groups = self.getGroups()
        groupNames = tuple([grp.name for grp in groups])
        return groupNames

    def getGroupByName(self, groupName):
        groups = self.getGroups()
        for grp in groups:
            if grp.name == groupName:
                return grp

if __name__ == '__main__':
    response = requests.get(const.schedule.url)
    print(response.json())
    scheduler = Scheduler()
    print(scheduler.getGroupByName('Н01').events[0].startTime)