from traceback import format_exc
import json
import logging
from datetime import datetime, timedelta

import asyncio
from aiogram import Bot, Dispatcher, types, F
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
botConfig = getConfigObject(joinPath(const.path.config, const.default.configFile))
const.addConstFromConfig(botConfig)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.INFO, filename=joinPath(const.path.logs, getLogFileName()), filemode='w', format=const.logging.format)
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
    # print(userLogInfo)
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

# COMMANDS
@dp.message(Command('start'))
async def startHandler(message: types.Message):
    userInfo = getUserInfo(message)
    dbLocal.users.setMode(userInfo.userId, 0)
    mainKeyboard = getMainKeyboard(userInfo)
    await message.answer(getTranslation(userInfo, 'start.message', [userInfo.userFirstName]), reply_markup=mainKeyboard)

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

def isScheduleCommand(userInfo):
    return userInfo.userText in ['/schedule', f'/schedule@{const.telegram.alias}',
                                 getTranslation(userInfo, 'button.schedule')]

async def scheduleHandler(userInfo, message):
    chat = dbChats.getChat(userInfo.chatId)
    mainKeyboard = getMainKeyboard(userInfo)
    if chat.groupName is None:
        await message.answer(getTranslation(userInfo, 'schedule.error'), reply_markup=mainKeyboard)
        return
    group = scheduler.getGroupByName(chat.groupName)
    resultText = getResultTextWithSchedule(userInfo, group)
    botMessage = await message.answer(resultText, reply_markup=mainKeyboard)
    await bot.pin_chat_message(userInfo.chatId, botMessage.message_id)

def getGroupNamesInlineKeyboard():
    groupNames = scheduler.getGroupNames()
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
    inlineKeyboard = getGroupNamesInlineKeyboard()
    await message.answer(getTranslation(userInfo, 'setgroup.select'), reply_markup=inlineKeyboard)

@dp.callback_query(F.data.startswith("sg."))
async def setGroupCallback(callback: types.CallbackQuery):
    fakeMessage = FakeMessage(callback.message.chat.id, callback.from_user.id)
    userInfo = UserInfo(fakeMessage)
    chatId = callback.message.chat.id
    callbackAction = callback.data
    newGroupName = callbackAction.split('.')[1]
    dbChats.setGroupName(chatId, newGroupName)
    mainKeyboard = getMainKeyboard(userInfo)
    await callback.message.answer(getTranslation(userInfo, 'setgroup.done'), reply_markup=mainKeyboard)

def isChangeLangCommand(userInfo):
    return userInfo.userText in ['/changelang', f'/changelang@{const.telegram.alias}',
                                 getChangeLangTranslation(userInfo)]


async def changeLangHandler(userInfo, message):
    chat = dbChats.getChat(userInfo.chatId)
    availableLangs = const.data.availableLangs
    nextIndexLang = (availableLangs.index(chat.lang) + 1) % len(availableLangs)
    dbChats.setLang(userInfo.chatId, availableLangs[nextIndexLang])
    mainKeyboard = getMainKeyboard(userInfo)
    await message.answer(getTranslation(userInfo, 'lang.change'), reply_markup=mainKeyboard)


def isUnknownCommand(userInfo):
    return userInfo.userText and userInfo.userText[0] == '/'

async def unknownCommandHandler(userInfo, message):
    mainKeyboard = getMainKeyboard(userInfo)
    await message.answer(getTranslation(userInfo, 'unknown.command.message'), reply_markup=mainKeyboard)

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
        await message.answer(getTranslation(userInfo, 'unknown.command.message'))
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