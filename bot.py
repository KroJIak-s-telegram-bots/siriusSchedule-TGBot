from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hide_link
from scheduleModule import getSchedule
from configparser import ConfigParser
from bs4 import BeautifulSoup
from datetime import datetime
from database import dbWorker
import logging
import requests
import asyncio
import json

# SETTINGS
logging.basicConfig(level=logging.INFO)
config = ConfigParser()
config.read("config.ini")
token = config['Telegram']['token']
namedbFile = config['Data']['namedbFile']
nameJsonFile = config['Data']['nameJsonFile']
defaultNameNeedGroup = config['Data']['defaultNameNeedGroup']
defaultHostTime = config['Data']['defaultHostTime']
urlRandomCat = config['Data']['urlRandomCat']
defaultHostTime = list(map(int, defaultHostTime.split()))
db = dbWorker(namedbFile)
jsonFile = open(nameJsonFile, encoding='utf-8')
langJson = json.load(jsonFile)
bot = Bot(token)
dp = Dispatcher(bot=bot)
data = {}

def getUrlImgWithCat():
    response = requests.get(urlRandomCat)
    bs = BeautifulSoup(response.text, 'lxml')
    imgObject = bs.find('img', 'hot-random-image')
    url = imgObject['src'] if imgObject['src'][0] != '<' else imgObject['href']
    return url

def getTranslation(name, inserts=[]):
    text = langJson[name]
    if len(inserts) > 0:
        splitText = text.split('%{}%')
        resultText = splitText[0]
        for i, ins in enumerate(inserts, start=1):
            resultText += ins
            if i < len(splitText): resultText += splitText[i]
        return resultText
    else:
        return text


def checkPermissions(chatId, userId, admins):
    if chatId == userId: return True
    for admin in admins:
        if userId == admin.user.id:
            return True
    return False


def getMainKeyboard():
    mainKeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mainButtons = [getTranslation('button.on'), getTranslation('button.off'),
                   getTranslation('button.schedule')]
    mainKeyboard.add(*mainButtons)
    return mainKeyboard


def getUserInfo(message): return [message.chat.id,
                                  message.from_user.id,
                                  message.from_user.first_name,
                                  message.from_user.full_name,
                                  message.message_id,
                                  message.text]

def getResultTasks(chatId):
    tasks = getSchedule()
    group = tasks[db.getGroup(chatId)]
    resultText = hide_link(getUrlImgWithCat())
    resultText += f"<U>{getTranslation('schedule.message', [db.getGroup(chatId)])}</U>\n"
    for task in group:
        title = task['title']
        address = task['address']
        startTime = task['startTime']
        endTime = task['endTime']
        startAdd = '0' if len(str(startTime % 60)) == 1 else ''
        endAdd = '0' if len(str(endTime % 60)) == 1 else ''
        resultText += f'<b>{title}</b>\n'
        resultText += f'{startTime // 60}:{startAdd}{startTime % 60} — {endTime // 60}:{endAdd}{endTime % 60}\n'
        resultText += f'Место: {address}\n\n'
    return resultText

# COMMANDS
@dp.message_handler(commands=['start', 'about'])
async def startHandler(message: types.Message):
    global data
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if not db.groupExists(chatId):
        db.addGroup(chatId, defaultNameNeedGroup)
        db.addNotification(chatId, True)
        db.addTime(chatId, 22, 0)
        data[chatId] = {'flagOnly': True}
    mainKeyboard = getMainKeyboard()
    await message.answer(getTranslation('start.message', [userName]), reply_markup=mainKeyboard)

@dp.message_handler(lambda message: message.text in ['/on', getTranslation('button.on')])
async def onHandler(message: types.Message):
    global data
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins) and db.groupExists(chatId):
        db.setNotification(chatId, True)
        await message.answer(getTranslation('mention.on'))


@dp.message_handler(lambda message: message.text in ['/off', getTranslation('button.off')])
async def offHandler(message: types.Message):
    global data
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins) and db.groupExists(chatId):
        db.setNotification(chatId, False)
        await message.answer(getTranslation('mention.off'))


@dp.message_handler(commands=['setgroup'])
async def setgroupHandler(message: types.Message):
    global data
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins) and db.groupExists(chatId):
        messageSplit = userText.split()
        if len(messageSplit) > 1:
            newNameGroup = ' '.join(messageSplit[1:])
            tasks = getSchedule()
            if newNameGroup in tasks:
                db.setGroup(chatId, newNameGroup)
                await message.answer(getTranslation('setgroup.true'))
                return
        await message.answer(getTranslation('setgroup.false'))

@dp.message_handler(commands=['settime'])
async def settimeHandler(message: types.Message):
    global nameNeedGroup, data
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins) and db.groupExists(chatId):
        messageSplit = userText.split()
        if len(messageSplit) > 1:
            newTime = messageSplit[1:]
            if len(newTime) == 2 and newTime[0].isdigit() and newTime[1].isdigit():
              db.setTimeHour(chatId, newTime[0])
              db.setTimeMinute(chatId, newTime[1])
              data[chatId]['flagOnly'] = True
              await message.answer('выставлено')
              return
        await message.answer('неа')


@dp.message_handler(lambda message: message.text in ['/schedule', getTranslation('button.schedule')])
async def scheduleHandler(message: types.Message):
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins) and db.groupExists(chatId):
        await bot.send_message(chatId, getResultTasks(chatId), parse_mode='HTML')


@dp.message_handler(commands=['gettime'])
async def gettimeHandler(message: types.Message):
    global nameNeedGroup
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins):
        nowTime = datetime.now()
        timeNow = nowTime.strftime("%H:%M:%S")
        await message.answer(f'Host time: {timeNow}')

async def activeLoop():
    global data
    while True:
        chatIds = db.getChatIds()
        if chatIds is not None:
            for chatId in chatIds:
                if db.getNotification(chatId):
                    nowTime = datetime.now()
                    currentHourTime = int(nowTime.strftime("%H"))
                    currentMinuteTime = int(nowTime.strftime("%M"))
                    if (currentHourTime, currentMinuteTime) == (db.getTime(chatId)[0], db.getTime(chatId)[1]) and data[chatId]['flagOnly']:
                        data[chatId]['flagOnly'] = False
                        resultMessage = await bot.send_message(chat_id=chatId, text=getResultTasks(chatId), parse_mode='HTML')
                        if db.pinExists(chatId):
                            await bot.delete_message(chat_id=chatId, message_id=db.getPin(chatId))
                            db.setPin(chatId, resultMessage.message_id)
                        else:
                            db.addPin(chatId, resultMessage.message_id)
                        await bot.pin_chat_message(chat_id=chatId, message_id=resultMessage.message_id)
                    elif (currentHourTime, currentMinuteTime) != (db.getTime(chatId)[0], db.getTime(chatId)[1]):
                        data[chatId]['flagOnly'] = True
        await asyncio.sleep(5)


async def onStartupBot(x): asyncio.create_task(activeLoop())


def main():
    chatIds = db.getChatIds()
    if chatIds is not None:
        for chatId in chatIds: data[chatId] = {'flagOnly': True}
    executor.start_polling(dispatcher=dp, on_startup=onStartupBot)


if __name__ == '__main__':
    main()
