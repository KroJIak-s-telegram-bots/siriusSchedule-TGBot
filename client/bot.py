from traceback import format_exc
import json
import logging
from datetime import datetime, timedelta

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types.chat_member_administrator import ChatMemberAdministrator
from aiogram.filters import Filter
from aiogram.filters.command import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.utils.markdown import hide_link

from modules.objects.client import UserInfo, FakeMessage
from modules.schedule import Scheduler
from modules.cats import getUrlImgWithCat
from utils.const import ConstPlenty
from utils.funcs import getConfigObject, joinPath, getLogFileName
from db.database import dbUsersWorker, dbChatsWorker, dbLocalWorker

# SETTINGS
const = ConstPlenty()
botConfig = getConfigObject(joinPath(const.path.config, const.default.file.config))
const.addConstFromConfig(botConfig)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO, filename=joinPath(const.path.logs, getLogFileName()), filemode='w', format=const.logging.format)
dbUsers = dbUsersWorker(joinPath(const.path.db, const.data.usersDatabasePath))
dbChats = dbChatsWorker(joinPath(const.path.db, const.data.chatsDatabasePath))
dbLocal = dbLocalWorker()
bot = Bot(const.telegram.token, default=DefaultBotProperties(parse_mode=const.default.parseMode))
dp = Dispatcher()
scheduler = Scheduler()

def getTranslation(userInfo, key, inserts=[], lang=None):
    chat = dbChats.getChat(userInfo.chatId)
    user = dbUsers.getUser(userInfo.userId)
    try:
        if not lang: lang = chat.lang
        with open(joinPath(const.path.lang, f'{lang}.json'), encoding='utf-8') as langFile:
            langJson = json.load(langFile)
        text = langJson[key]
        if not inserts: return text
        for ins in inserts: text = text.replace('%{}%', str(ins), 1)
        return text
    except Exception:
        if user.isAdmin(): return getTranslation(userInfo, 'error.message', [format_exc()])
        else: return getTranslation(userInfo, 'error.message', ['wwc...'])

def getUserInfo(message):
    userInfo = UserInfo(message)
    if not dbUsers.isUserExists(userInfo.userId):
        permissions = dbUsers.getPermissions()
        dbUsers.addNewUser(userInfo.userId, userInfo.username, userInfo.userFullName, permissions[0])
    if not dbChats.isChatExists(userInfo.chatId):
        dbChats.addNewChat(userInfo.chatId, const.data.defaultLang)
    if not dbLocal.users.isUserExists(userInfo.userId):
        dbLocal.users.addNewUser(userInfo.userId)
    if not dbLocal.chats.isChatExists(userInfo.chatId):
        dbLocal.chats.addNewChat(userInfo.chatId)
    userLogInfo = f'{userInfo} | {str(dbLocal.users.db[str(userInfo.userId)])}'
    logging.info(userLogInfo)
    print(userLogInfo)
    return userInfo

def getChangeLangTranslation(userInfo):
    chat = dbChats.getChat(userInfo.chatId)
    availableLangs = const.data.availableLangs
    nextIndexLang = (availableLangs.index(chat.lang) + 1) % len(availableLangs)
    curCountryFlag = getTranslation(userInfo, 'lang.countryflag')
    nextCountryFlag = getTranslation(userInfo, 'lang.countryflag', lang=availableLangs[nextIndexLang])
    resultTranslation = getTranslation(userInfo, 'button.changelang', [curCountryFlag, nextCountryFlag])
    return resultTranslation

def getMainKeyboard(userInfo):
    chat = dbChats.getChat(userInfo.chatId)
    mainButtons = []
    mainButtons.append([types.KeyboardButton(text=getTranslation(userInfo, 'button.schedule'))])
    mainButtons.append([types.KeyboardButton(text=getTranslation(userInfo, 'button.setgroup', [chat.groupName]))])
    mainButtons.append([types.KeyboardButton(text=getChangeLangTranslation(userInfo))])
    mainKeyboard = types.ReplyKeyboardMarkup(keyboard=mainButtons, resize_keyboard=True)
    return mainKeyboard

def getUserNameWithUrl(userInfo):
    return f'<a href="tg://user?id={userInfo.userId}">{userInfo.userFirstName}</a>'

async def isGroupAdmin(userInfo):
    if userInfo.chatId == userInfo.userId: return True
    chatMember = await bot.get_chat_member(userInfo.chatId, userInfo.userId)
    return chatMember.status == ChatMemberAdministrator

async def notGroupAdminHandler(userInfo, message):
    botMessage = await message.answer(getTranslation(userInfo, 'permissions.group.admin'))
    await bot.delete_message(userInfo.chatId, userInfo.messageId)
    await asyncio.sleep(const.telegram.messageTimeout)
    await bot.delete_message(userInfo.chatId, botMessage.message_id)

# COMMANDS
@dp.message(Command('start'))
async def startHandler(message: types.Message):
    userInfo = getUserInfo(message)
    dbLocal.users.setMode(userInfo.userId, 0)
    lastBotStartMessageId = dbLocal.chats.getLastBotStartMessageId(userInfo.chatId)
    if lastBotStartMessageId is not None: await bot.delete_message(userInfo.chatId, lastBotStartMessageId)
    mainKeyboard = getMainKeyboard(userInfo)
    userNameWithUrl = getUserNameWithUrl(userInfo)
    botMessage = await message.answer(getTranslation(userInfo, 'start.message', [userNameWithUrl]), reply_markup=mainKeyboard)
    await bot.delete_message(userInfo.chatId, userInfo.messageId)
    dbLocal.chats.setLastBotStartMessageId(userInfo.chatId, botMessage.message_id)

def getNormalTime(milliseconds):
    dtObject = datetime.fromtimestamp(milliseconds / 1000)
    newStartTime = dtObject + timedelta(hours=const.data.timeDifference)
    return newStartTime

def getResultTextWithSchedule(userInfo, group):
    resultText = hide_link(getUrlImgWithCat())
    resultText += getTranslation(userInfo, 'schedule.message', [group.name])
    resultText += '\n'
    eventTextList = []
    for event in group.events:
        currentTime = datetime.now()
        newStartTime = getNormalTime(event.startTime)
        newEndTime = getNormalTime(event.endTime)
        eventText = f'<b>{event.title}</b>\n'
        eventText += f"{newStartTime.strftime('%H:%M')} — {newEndTime.strftime('%H:%M')}\n"
        eventText += f'Место: {event.address}\n\n'
        if currentTime >= newStartTime: eventText = f'<s>{eventText}</s>'
        eventTextList.append((event.startTime, eventText))
    sortedEventTextList = sorted(eventTextList, key=lambda x: x[0])
    sortedEventTextList = list(map(lambda x: x[1], sortedEventTextList))
    resultText += ''.join(sortedEventTextList)
    return resultText

class pinFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.pinned_message is not None

@dp.message(pinFilter())
async def pinnedMessageHandler(message: types.Message):
    userInfo = getUserInfo(message)
    user = dbUsers.getUser(userInfo.userId)
    if user.login == const.telegram.alias:
        await bot.delete_message(userInfo.chatId, userInfo.messageId)

def isScheduleCommand(userInfo):
    return userInfo.userText in ['/schedule', f'/schedule@{const.telegram.alias}',
                                 getTranslation(userInfo, 'button.schedule')]

async def scheduleHandler(userInfo, message):
    chat = dbChats.getChat(userInfo.chatId)
    if chat.groupName is None:
        botMessage = await message.answer(getTranslation(userInfo, 'schedule.error'))
        await asyncio.sleep(const.telegram.messageTimeout)
        await bot.delete_message(userInfo.chatId, botMessage.message_id)
    else:
        group = scheduler.getGroupByName(chat.groupName)
        resultText = getResultTextWithSchedule(userInfo, group)
        botMessage = await message.answer(resultText)
        await bot.pin_chat_message(userInfo.chatId, botMessage.message_id)
    await bot.delete_message(userInfo.chatId, userInfo.messageId)

def getShortenGroupName(name):
    limit = const.callback.textLimit
    if len(name) <= limit:
        return name
    resultName = name[  :(limit // 2 - 1)] + '...' + name[-(limit // 2 + 2):]
    return resultName

def getGroupNamesInlineKeyboard():
    groupNames = scheduler.getGroupNames()
    groupNames = tuple(list(map(getShortenGroupName, groupNames)))
    callbackPrefix = const.callback.prefix.setGroup
    inlineButtons = [[types.InlineKeyboardButton(text=name, callback_data=callbackPrefix + name)]
                     for name in groupNames]
    inlineKeyboard = InlineKeyboardMarkup(inline_keyboard=inlineButtons)
    return inlineKeyboard

def isSetGroupCommand(userInfo):
    chat = dbChats.getChat(userInfo.chatId)
    return userInfo.userText in ['/setgroup', f'/setgroup@{const.telegram.alias}',
                                 getTranslation(userInfo, 'button.setgroup', [chat.groupName])]

async def setGroupHandler(userInfo, message):
    if not await isGroupAdmin(userInfo):
        await notGroupAdminHandler(userInfo, message)
        return
    lastBotMessageId = dbLocal.chats.getLastBotMessageId(userInfo.chatId)
    if lastBotMessageId is not None: await bot.delete_message(userInfo.chatId, lastBotMessageId)
    inlineKeyboard = getGroupNamesInlineKeyboard()
    botMessage = await message.answer(getTranslation(userInfo, 'setgroup.select'), reply_markup=inlineKeyboard)
    dbLocal.chats.setLastBotMessageId(userInfo.chatId, botMessage.message_id)
    await bot.delete_message(userInfo.chatId, userInfo.messageId)
    lastBotStartMessageId = dbLocal.chats.getLastBotStartMessageId(userInfo.chatId)
    mainKeyboard = getMainKeyboard(userInfo)
    await bot.edit_message_reply_markup(userInfo.chatId, lastBotStartMessageId, reply_markup=mainKeyboard)

@dp.callback_query(F.data.startswith(const.callback.prefix.setGroup))
async def setGroupCallback(callback: types.CallbackQuery):
    chatId = callback.message.chat.id
    userId = callback.from_user.id
    callbackAction = callback.data
    fakeMessage = FakeMessage(chatId, userId)
    userInfo = getUserInfo(fakeMessage)
    newGroupName = callbackAction.split('.')[1]
    dbChats.setGroupName(chatId, newGroupName)
    lastBotMessageId = dbLocal.chats.getLastBotMessageId(chatId)
    botMessage = await callback.message.answer(getTranslation(userInfo, 'setgroup.done'))
    await bot.delete_message(chatId, lastBotMessageId)
    await asyncio.sleep(const.telegram.messageTimeout)
    await bot.delete_message(chatId, botMessage.message_id)
    dbLocal.chats.setLastBotMessageId(chatId, None)

def isChangeLangCommand(userInfo):
    return userInfo.userText in ['/changelang', f'/changelang@{const.telegram.alias}',
                                 getChangeLangTranslation(userInfo)]

async def changeLangHandler(userInfo, message):
    if not await isGroupAdmin(userInfo):
        await notGroupAdminHandler(userInfo, message)
        return
    chat = dbChats.getChat(userInfo.chatId)
    availableLangs = const.data.availableLangs
    nextIndexLang = (availableLangs.index(chat.lang) + 1) % len(availableLangs)
    dbChats.setLang(userInfo.chatId, availableLangs[nextIndexLang])
    botMessage = await message.answer(getTranslation(userInfo, 'lang.change'))
    await bot.delete_message(userInfo.chatId, userInfo.messageId)
    await asyncio.sleep(const.telegram.messageTimeout)
    await bot.delete_message(userInfo.chatId, botMessage.message_id)
    lastBotStartMessageId = dbLocal.chats.getLastBotStartMessageId(userInfo.chatId)
    mainKeyboard = getMainKeyboard(userInfo)
    await bot.edit_message_reply_markup(userInfo.chatId, lastBotStartMessageId, reply_markup=mainKeyboard)

def isUnknownCommand(userInfo):
    return userInfo.userText and userInfo.userText[0] == '/'

async def unknownCommandHandler(userInfo, message):
    botMessage = await message.answer(getTranslation(userInfo, 'unknown.command.message'))
    await asyncio.sleep(const.telegram.messageTimeout)
    await bot.delete_message(userInfo.chatId, botMessage.message_id)

@dp.message()
async def mainHandler(message: types.Message):
    userInfo = getUserInfo(message)
    userMode = dbLocal.users.getMode(userInfo.userId)

    if isScheduleCommand(userInfo):
        await scheduleHandler(userInfo, message)
        return

    elif isSetGroupCommand(userInfo):
        await setGroupHandler(userInfo, message)
        return

    elif isChangeLangCommand(userInfo):
        await changeLangHandler(userInfo, message)
        return

    elif isUnknownCommand(userInfo):
        await unknownCommandHandler(userInfo, message)
        return

    elif userMode > 0:
        match userMode:
            case 1: pass
        return

async def mainTelegram():
    await dp.start_polling(bot)

def main():
    asyncio.run(mainTelegram())

if __name__ == '__main__':
    main()