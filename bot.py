from aiogram import Bot, Dispatcher, executor, types
from scheduleModule import getSchedule
from configparser import ConfigParser
from datetime import datetime
from database import dbWorker
import logging
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
db = dbWorker(namedbFile)
jsonFile = open(nameJsonFile, encoding='utf-8')
langJson = json.load(jsonFile)
bot = Bot(token)
dp = Dispatcher(bot=bot)
data = {}


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
            print('TRUE')
            return True
    print('FALSE')
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
    global nameNeedGroup, data
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


@dp.message_handler(lambda message: message.text in ['/schedule', getTranslation('button.schedule')])
async def scheduleHandler(message: types.Message):
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkPermissions(chatId, userId, admins) and db.groupExists(chatId):
        await bot.send_message(chatId, getResultTasks(chatId), parse_mode='Markdown')


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


#МУТ МИХАИЛА
'''
@dp.message_handler()
async def mainHandler(message: types.Message):
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if (userId == 1419885227 and len(userText) < 3) or (userId == 1419885227 and random.randint(1, 100) < 90):
        await bot.delete_message(chatId, messageId)
        msg = await bot.send_message(chatId, ')')
        await asyncio.sleep(5)
        await bot.delete_message(chatId, msg.message_id)'''


def getResultTasks(chatId):
    tasks = getSchedule()
    group = tasks[db.getGroup(chatId)]
    resultText = f"_{getTranslation('schedule.message', [db.getGroup(chatId)])}_\n"
    for task in group:
        title = task['title']
        address = task['address']
        startTime = task['startTime']
        endTime = task['endTime']
        startAdd = '0' if len(str(startTime % 60)) == 1 else ''
        endAdd = '0' if len(str(endTime % 60)) == 1 else ''
        resultText += f'*{title}*\n'
        resultText += f'{startTime // 60}:{startAdd}{startTime % 60} — {endTime // 60}:{endAdd}{endTime % 60}\n'
        resultText += f'Место: {address}\n\n'
    return resultText


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
                    if currentHourTime == db.getTime(chatId)[0] and currentMinuteTime == db.getTime(chatId)[1] and \
                            data[chatId]['flagOnly']:
                        data[chatId]['flagOnly'] = False
                        resultMessage = await bot.send_message(chatId, getResultTasks(chatId), parse_mode='Markdown')
                        await bot.pin_chat_message(chat_id=resultMessage.chat.id, message_id=resultMessage.message_id)
                    elif currentHourTime != db.getTime(chatId)[0] or currentMinuteTime != db.getTime(chatId)[1]:
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
