import json
import os
import shutil

from utils.funcs import joinPath
from modules.objects.db import Chat, User
from utils.const import ConstPlenty

const = ConstPlenty()

class dbWorker():
    def __init__(self, databasePath, defaultDBFileName=const.default.file.database):
        folderPath = databasePath.split('/')
        self.fileName = folderPath.pop(-1)
        self.folderPath = '/'.join(folderPath)
        if not self.isExists():
            shutil.copyfile(joinPath(self.folderPath, defaultDBFileName),
                            joinPath(self.folderPath, self.fileName))

    def isExists(self):
        files = os.listdir(self.folderPath)
        return self.fileName in files

    def get(self):
        with open(joinPath(self.folderPath, self.fileName)) as file:
            dbData = json.load(file)
        return dbData

    def save(self, dbData):
        with open(joinPath(self.folderPath, self.fileName), 'w', encoding='utf-8') as file:
            json.dump(dbData, file, indent=4, ensure_ascii=False)

class dbLocalWorker():
    def __init__(self):
        self.users = dbLocalUsersWorker()
        self.chats = dbLocalChatsWorker()

class dbLocalUsersWorker():
    def __init__(self):
        self.db = {}

    def isUserExists(self, userId):
        return str(userId) in self.db

    def addNewUser(self, userId):
        self.db[str(userId)] = dict(mode=0)

    def setMode(self, userId, mode):
        self.db[str(userId)]['mode'] = mode

    def getMode(self, userId):
        return self.db[str(userId)]['mode']

class dbLocalChatsWorker():
    def __init__(self):
        self.db = {}

    def isChatExists(self, chatId):
        return str(chatId) in self.db

    def addNewChat(self, chatId):
        self.db[str(chatId)] = dict(lastBotMessageId=None,
                                    lastBotStartMessageId=None)

    def setLastBotMessageId(self, chatId, messageId):
        self.db[str(chatId)]['lastBotMessageId'] = messageId

    def getLastBotMessageId(self, chatId):
        return self.db[str(chatId)]['lastBotMessageId']

    def setLastBotStartMessageId(self, chatId, messageId):
        self.db[str(chatId)]['lastBotStartMessageId'] = messageId

    def getLastBotStartMessageId(self, chatId):
        return self.db[str(chatId)]['lastBotStartMessageId']

class dbUsersWorker(dbWorker):
    def getUserIds(self):
        dbData = self.get()
        userIds = tuple(dbData['users'].keys())
        return userIds

    def getPermissions(self):
        dbData = self.get()
        permissions = tuple(dbData['permissions'].values())
        return permissions

    def isUserExists(self, userId):
        dbData = self.get()
        return str(userId) in dbData['users']

    def addNewUser(self, userId, login, fullname, permission='default'):
        dbData = self.get()
        newUser = dict(login=login,
                       fullname=fullname,
                       permission=permission)
        dbData['users'][str(userId)] = newUser
        self.save(dbData)

    def getUser(self, userId):
        dbData = self.get()
        dictUser = dbData['users'][str(userId)]
        user = User(str(userId), dictUser)
        return user

    def setInUser(self, userId, key, value):
        dbData = self.get()
        dbData['users'][str(userId)][str(key)] = value
        self.save(dbData)

class dbChatsWorker(dbWorker):
    def getChatIds(self):
        dbData = self.get()
        chatIds = tuple(dbData.keys())
        return chatIds

    def isChatExists(self, chatId):
        dbData = self.get()
        return str(chatId) in dbData

    def addNewChat(self, chatId, lang):
        dbData = self.get()
        newChat = dict(lang=lang,
                       groupName=None)
        dbData[str(chatId)] = newChat
        self.save(dbData)

    def getChat(self, chatId):
        dbData = self.get()
        dictChat = dbData[str(chatId)]
        chat = Chat(str(chatId), dictChat)
        return chat

    def setInChat(self, chatId, key, value):
        dbData = self.get()
        dbData[str(chatId)][str(key)] = value
        self.save(dbData)

    def setLang(self, chatId, lang):
        self.setInChat(chatId, 'lang', lang)

    def setGroupName(self, chatId, groupName):
        self.setInChat(chatId, 'groupName', groupName)