from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hide_link
from scheduleModule import getSchedule
from configparser import ConfigParser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from database import dbWorker
import logging
import requests
import asyncio
import json
from random import choice
from ast import literal_eval
from copy import copy

# SETTINGS
logging.basicConfig(level=logging.INFO)
config = ConfigParser()
config.read("config.ini")
token = config['Telegram']['token']
alias = config['Telegram']['alias']
path2DBFile = config['Data']['path2DBFile']
defaultNameNeedGroup = config['Data']['defaultNameNeedGroup']
urlRandomCat = config['Data']['urlRandomCat']
rawAvailableLangs = config['Data']['availableLangs']
defaultLang = config['Data']['defaultLang']
timeDifference = int(config['Data']['timeDifference'])
rawDefaultHostTime = config['Data']['defaultHostTime']
availableLangs = rawAvailableLangs.split(', ')
defaultHostTime = list(map(int, rawDefaultHostTime.split(':')))
db = dbWorker(path2DBFile)
bot = Bot(token)
dp = Dispatcher(bot=bot)
data = {}
goodWords = ['хороший', 'прекрасный', "отличный", 'удивительный', 'великолепный', 'замечательный', 'невероятный',
             'потрясающий', 'восхитительный', 'безупречный', 'волшебный', 'превосходный', 'идеальный', 'фантастический',
             'выдающийся', 'бесподобный', 'безмерный', 'блестящий', 'гениальный', 'доскональный', 'живописный',
             'изумительный', 'красивейший', 'лучезарный', 'магический', 'несравненный', 'обворожительный',
             'первоклассный', 'радостный', 'сказочный', 'творческий', 'уникальный', 'фееричный', 'харизматичный',
             'эффектный', 'яркий', 'незабываемый', 'необыкновенный', 'несравнимый', 'ошеломительный', 'прекраснейший',
             'чудесный', 'экстраординарный', 'радужный', 'благодарный', 'добрый', 'интересный', 'креативный', 'мудрый',
             'совершенный']


'''
        def getUrlImgWithCat():  
    response = requests.get(urlRandomCat)
    bs = BeautifulSoup(response.text, 'lxml')
    imgObjects = bs.find_all('img')
    url = imgObjects[1]['src']
    return url
'''

def getUrlImgWithCat():
    response = requests.get(urlRandomCat)
    bs = BeautifulSoup(response.text, 'lxml')
    imgObject = bs.find('img', 'hot-random-image')
    url = imgObject['src'] if imgObject['src'][0] != '<' else imgObject['href']
    return url

def getTranslation(chatId, name, inserts=[], lang=None):
    if lang is None: nameLang = db.getFromTable(chatId, 'langs')[0]
    else: nameLang = lang
    with open(f'lang/{nameLang}.json', encoding='utf-8') as langFile:
        langJson = json.load(langFile)
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


def getChangeLangTranslation(chatId):
    curLang = db.getFromTable(chatId, 'langs')[0]
    nextIndexLang = (availableLangs.index(curLang) + 1) % len(availableLangs)
    curCountryFlag = getTranslation(chatId, 'lang.countryflag')
    nextCountryFlag = getTranslation(chatId, 'lang.countryflag', lang=availableLangs[nextIndexLang])
    resultTranslation = getTranslation(chatId, 'button.changelang', [curCountryFlag, nextCountryFlag])
    return resultTranslation

def getTimeNotificationTranslation(chatId):
    curTime = db.getFromTable(chatId, 'times')
    curHour = f'0{curTime[0]}' if len(str(curTime[0])) == 1 else curTime[0]
    curMinute = f'0{curTime[1]}' if len(str(curTime[1])) == 1 else curTime[1]
    resultTranslation = getTranslation(chatId, 'button.settime', [curHour, curMinute])
    return resultTranslation

def getMainKeyboard(chatId):
    mainKeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mainButtons = [getTranslation(chatId, 'button.schedule'),
                   getTranslation(chatId, 'button.setgroup', [db.getFromTable(chatId, 'groups')[0]]),
                   getTimeNotificationTranslation(chatId),
                   getTranslation(chatId, 'button.on'), getTranslation(chatId, 'button.off'),
                   getChangeLangTranslation(chatId)]
    mainKeyboard.add(*mainButtons)
    return mainKeyboard


def getUserInfo(message):
    userInfo = {'chatId': message.chat.id,
                'userId': message.from_user.id,
                'username': message.from_user.username,
                'userFirstName': message.from_user.first_name,
                'userFullName': message.from_user.full_name,
                'messageId': message.message_id,
                'userText': message.text}
    if not db.tableExists(userInfo['userId'], 'users'):
        db.add2Table(userInfo['userId'], 'users', {'username': userInfo['username'],
                                                             'userFullName': userInfo['userFullName']})
    print(' | '.join(list(map(str, userInfo.values()))))
    return userInfo


def getResultTasks(chatId):
    schedule = getSchedule()
    nameGroup = db.getFromTable(chatId, 'groups')[0]
    if nameGroup not in schedule: return getTranslation(chatId, 'schedule.error', [nameGroup])
    group = schedule[nameGroup]
    resultText = hide_link(getUrlImgWithCat())
    resultText += f"{getTranslation(chatId, 'schedule.message', [nameGroup])}\n"
    curTime = datetime.now().timestamp() + (timeDifference * 3600 * -1)
    arrTimeAndText = []
    for task in group:
        title = task['title']
        address = task['address']
        startTime = task['startTime']
        endTime = task['endTime']
        taskText = ''
        startAdd = '0' if len(str(startTime % 60)) == 1 else ''
        endAdd = '0' if len(str(endTime % 60)) == 1 else ''
        if curTime > task['originalEndTime']: taskText += '<s>'
        taskText += f'<b>{title}</b>\n'
        taskText += f'{startTime // 60}:{startAdd}{startTime % 60} — {endTime // 60}:{endAdd}{endTime % 60}\n'
        taskText += f'Место: {address}\n\n'
        if curTime > task['originalEndTime']: taskText += '</s>'
        arrTimeAndText.append([startTime, taskText])
    arrTimeAndText = sorted(arrTimeAndText, key=lambda elms: elms[0])
    arrSortedText = list(map(lambda elms: elms[1], arrTimeAndText))
    resultText += ''.join(arrSortedText)
    return resultText

# COMMANDS
@dp.message_handler(commands=['start', 'about'])
async def startHandler(message: types.Message):
    global data
    userInfo = getUserInfo(message)
    if not db.tableExists(userInfo['chatId'], 'groups'):
        db.add2Table(userInfo['chatId'], 'groups', {'nameGroup': defaultNameNeedGroup})
        db.add2Table(userInfo['chatId'], 'notifications', {'condition': True})
        db.add2Table(userInfo['chatId'], 'times', {'hour': defaultHostTime[0],
                                               'minute': defaultHostTime[1]})
        db.add2Table(userInfo['chatId'], 'langs', {'lang': defaultLang})
        db.add2Table(userInfo['chatId'], 'messages', {'messageIds': str([])})
        data[userInfo['chatId']] = {'flagOnly': True}
    mainKeyboard = getMainKeyboard(userInfo['chatId'])
    await message.answer(getTranslation(userInfo['chatId'], 'start.message', [userInfo['userFirstName']]), reply_markup=mainKeyboard)

@dp.message_handler(lambda message: message.text in ['/schedule', f'/schedule@{alias}',
                                                     getTranslation(message.chat.id, 'button.schedule')])
async def scheduleHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins) and db.tableExists(userInfo['chatId'], 'groups'):
        resultMessage = await bot.send_message(userInfo['chatId'], getResultTasks(userInfo['chatId']), parse_mode='HTML')
        strMessageIds = db.getFromTable(userInfo['chatId'], 'messages')[0]
        messageIds = literal_eval(strMessageIds)
        messageIds.append(resultMessage.message_id)
        db.setInTable(userInfo['chatId'], 'messages', {'messageIds': str(messageIds)})

@dp.message_handler(lambda message: message.text in ['/setgroup', f'/setgroup@{alias}',
                                                     getTranslation(message.chat.id, 'button.setgroup', [db.getFromTable(message.chat.id, 'groups')[0]])])
async def setgroupHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins) and db.tableExists(userInfo['chatId'], 'groups'):
        schedule = getSchedule()
        groupNames = schedule.keys()
        keyboard = types.InlineKeyboardMarkup()
        for name in groupNames: keyboard.add(types.InlineKeyboardButton(text=name, callback_data=f'call_setgroup_{name}'))
        await message.answer(getTranslation(userInfo['chatId'], 'setgroup.select'), reply_markup=keyboard)

@dp.callback_query_handler(lambda call: 'call_setgroup' in call.data)
async def setgroupCallback(call: types.CallbackQuery):
    userInfo = getUserInfo(call.message)
    newNameGroup = call.data.split('_')[2]
    db.setInTable(userInfo['chatId'], 'groups', {'nameGroup': newNameGroup})
    mainKeyboard = getMainKeyboard(userInfo['chatId'])
    await call.message.answer(getTranslation(userInfo['chatId'], 'setgroup.true'), reply_markup=mainKeyboard)

@dp.message_handler(lambda message: message.text in ['/settime', f'/settime@{alias}',
                                                     getTimeNotificationTranslation(message.chat.id)])
async def settimeHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins) and db.tableExists(userInfo['chatId'], 'groups'):
        keyboard = types.InlineKeyboardMarkup()
        for hour in range(1, 9): keyboard.add(types.InlineKeyboardButton(text=f'{hour}:00', callback_data=f'call_settime_{hour}'))
        await message.answer(getTranslation(userInfo['chatId'], 'settime.select'), reply_markup=keyboard)

@dp.callback_query_handler(lambda call: 'call_settime' in call.data)
async def settimeCallback(call: types.CallbackQuery):
    global data
    userInfo = getUserInfo(call.message)
    newTimeHour = int(call.data.split('_')[2])
    db.setInTable(userInfo['chatId'], 'times', {'hour': newTimeHour,
                                                          'minute': 0})
    data[userInfo['chatId']]['flagOnly'] = True
    mainKeyboard = getMainKeyboard(userInfo['chatId'])
    await call.message.answer(getTranslation(userInfo['chatId'], 'settime.true'), reply_markup=mainKeyboard)


@dp.message_handler(lambda message: message.text in ['/on', f'/on@{alias}',
                                                     getTranslation(message.chat.id, 'button.on')])
async def onHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins) and db.tableExists(userInfo['chatId'], 'groups'):
        db.setInTable(userInfo['chatId'], 'notifications', {'condition': True})
        await message.answer(getTranslation(userInfo['chatId'], 'mention.on'))


@dp.message_handler(lambda message: message.text in ['/off', f'/off@{alias}',
                                                     getTranslation(message.chat.id, 'button.off')])
async def offHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins) and db.tableExists(userInfo['chatId'], 'groups'):
        db.setInTable(userInfo['chatId'], 'notifications', {'condition': False})
        await message.answer(getTranslation(userInfo['chatId'], 'mention.off'))

@dp.message_handler(lambda message: message.text in ['/changelang', f'/changelang@{alias}',
                                                     getChangeLangTranslation(message.chat.id)])
async def changelangHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins) and db.tableExists(userInfo['chatId'], 'groups'):
        curLang = db.getFromTable(userInfo['chatId'], 'langs')[0]
        nextIndexLang = (availableLangs.index(curLang) + 1) % len(availableLangs)
        db.setInTable(userInfo['chatId'], 'langs', {'lang': availableLangs[nextIndexLang]})
        mainKeyboard = getMainKeyboard(userInfo['chatId'])
        await message.answer(getTranslation(userInfo['chatId'], 'lang.change'), reply_markup=mainKeyboard)

@dp.message_handler(commands=['❤️2bot'])
async def heart2botHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['userId'] != 1419885227: await bot.send_message(userInfo['chatId'],
                                     f'{userInfo["userFullName"]}, ты {choice(goodWords)} человек. Спасибо за смену ❤️')
    else: await bot.send_message(userInfo['chatId'], 'Миш, бывает)')

@dp.message_handler(commands=['thanks'])
async def thanksHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins):
        await bot.delete_message(userInfo['chatId'], userInfo['messageId'])
        await bot.send_message(userInfo['chatId'], 'Спасибо всем за смену, я старался. ❤️')
        await bot.send_message(userInfo['chatId'], ')')

@dp.message_handler(commands=['gettime'])
async def gettimeHandler(message: types.Message):
    global nameNeedGroup
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins):
        nowTime = datetime.now()
        timeNow = nowTime.strftime("%H:%M:%S")
        nowRealTime = datetime.now() + timedelta(hours=(timeDifference * -1))
        realTimeNow = nowRealTime.strftime("%H:%M:%S")
        await message.answer(f'Host time: {timeNow} | Real time: {realTimeNow}')

@dp.message_handler(commands=['test'])
async def testHandler(message: types.Message):
    global nameNeedGroup
    userInfo = getUserInfo(message)
    if userInfo['chatId'] != userInfo['userId']: admins = await bot.get_chat_administrators(chat_id=userInfo['chatId'])
    else: admins = None
    if checkPermissions(userInfo['chatId'], userInfo['userId'], admins):
        resultMessage = await bot.send_message(chat_id=userInfo['chatId'], text=getResultTasks(userInfo['chatId']), parse_mode='HTML')

        strMessageIds = db.getFromTable(userInfo['chatId'], 'messages')[0]
        messageIds = literal_eval(strMessageIds)
        messageIds.append(resultMessage.message_id)
        db.setInTable(userInfo['chatId'], 'messages', {'messageIds': str(messageIds)})

        if db.tableExists(userInfo['chatId'], 'pins'):
            try: await bot.unpin_chat_message(chat_id=userInfo['chatId'], message_id=db.getFromTable(userInfo['chatId'], 'pins')[0])
            except: pass
            db.setInTable(userInfo['chatId'], 'pins', {'messageId': resultMessage.message_id})
        else:
            db.add2Table(userInfo['chatId'], 'pins', {'messageId': resultMessage.message_id})
        await bot.pin_chat_message(chat_id=userInfo['chatId'], message_id=resultMessage.message_id)

async def activeLoop():
    global data
    while True:
        chatIds = db.getChatIds()
        if chatIds is not None:
            for chatId in chatIds:
                nowTime = datetime.now() + timedelta(hours=(timeDifference * -1))
                if db.getFromTable(chatId, 'notifications'):
                    if ((nowTime.hour, nowTime.minute) == (db.getFromTable(chatId, 'times')[0], db.getFromTable(chatId, 'times')[1])
                            and data[chatId]['flagOnly']):
                        data[chatId]['flagOnly'] = False
                        resultMessage = await bot.send_message(chat_id=chatId, text=getResultTasks(chatId), parse_mode='HTML')

                        strMessageIds = db.getFromTable(chatId, 'messages')
                        messageIds = literal_eval(strMessageIds)
                        messageIds.append(resultMessage.message_id)
                        db.setInTable(chatId, 'messages', {'messageIds': str(messageIds)})

                        if db.tableExists(chatId, 'pins'):
                            try: await bot.unpin_chat_message(chat_id=chatId, message_id=db.getFromTable(chatId, 'pins')[0])
                            except: pass
                            db.setInTable(chatId, 'pins', {'messageId': resultMessage.message_id})
                        else:
                            db.add2Table(chatId, 'pins', {'messageId': resultMessage.message_id})
                        await bot.pin_chat_message(chat_id=chatId, message_id=resultMessage.message_id)
                    elif (nowTime.hour, nowTime.minute) != (db.getFromTable(chatId, 'times')[0], db.getFromTable(chatId, 'times')[1]):
                        data[chatId]['flagOnly'] = True
                if nowTime.hour == 0:
                    db.setInTable(chatId, 'messages', {'messageIds': str([])})
                else:
                    strMessageIds = db.getFromTable(chatId, 'messages')[0]
                    messageIds = literal_eval(strMessageIds)
                    newMessageIds = copy(messageIds)
                    newText = getResultTasks(chatId)
                    for messageId in messageIds:
                        try: await bot.edit_message_text(text=newText, chat_id=chatId, message_id=messageId, parse_mode='HTML')
                        except Exception as err:
                            if str(err) == 'Message to edit not found':
                                print(f'WARN MESSAGE ID: {messageId} | Message has been deleted')
                                newMessageIds.pop(newMessageIds.index(messageId))
                            else:
                                print(f'ERROR MESSAGE ID: {messageId} | {err}')
                    db.setInTable(chatId, 'messages', {'messageIds': str(newMessageIds)})

        await asyncio.sleep(15)

async def onStartupBot(x): asyncio.create_task(activeLoop())


def main():
    chatIds = db.getChatIds()
    if chatIds is not None:
        for chatId in chatIds: data[chatId] = {'flagOnly': True}
    executor.start_polling(dispatcher=dp, on_startup=onStartupBot)

if __name__ == '__main__':
    main()
