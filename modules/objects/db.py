
class Chat():
    def __init__(self, chatId, dictChat):
        self.chatId = chatId
        self.lang = dictChat['lang']
        self.groupName = dictChat['groupName']

class User():
    def __init__(self, userId, dictUser):
        self.userId = userId
        self.login = dictUser['login']
        self.fullname = dictUser['fullname']
        self.permission = dictUser['permission']

    def isDefault(self):
        return self.permission == 'default'

    def isAdmin(self):
        return self.permission == 'admin'