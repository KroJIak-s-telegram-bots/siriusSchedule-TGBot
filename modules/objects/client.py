
class FakeChat():
    def __init__(self, chatId):
        self.id = chatId

class FakeFromUser():
    def __init__(self, userId, username, userFirstName, userFullName):
        self.id = userId
        self.username = username
        self.first_name = userFirstName
        self.full_name = userFullName

class FakeMessage():
    def __init__(self, chatId=None, userId=None, username=None, userFirstName=None, userFullName=None, messageId=None, userText=None):
        self.chat = FakeChat(chatId)
        self.from_user = FakeFromUser(userId, username, userFirstName, userFullName)
        self.message_id = messageId
        self.text = userText

class UserInfo():
    def __init__(self, message):
        self.chatId = message.chat.id
        self.userId = message.from_user.id
        self.username = message.from_user.username
        self.userFirstName = message.from_user.first_name
        self.userFullName = message.from_user.full_name
        self.messageId = message.message_id
        self.userText = message.text

    def __str__(self):
        resultStr = ' | '.join(list(map(str, (self.chatId, self.userId, self.username, self.userFirstName,
                     self.userFullName, self.messageId, self.userText))))
        return resultStr