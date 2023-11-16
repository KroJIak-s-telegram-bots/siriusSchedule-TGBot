

'''

blacklistSymbs = config['Data']['blacklistSymbs'].split()
openai.api_key = config['ChatGPT']['token']
model = config['ChatGPT']['model']
IDMIHAIL = 1419885227

[ChatGPT]
token = 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
model = gpt-3.5-turbo
blacklistSymbs = 💀 ☠ ️ 💀 💀 💀 ☠ ️ 💀 💀

def checkTextOnBlacklistSymbs(chatId, userId, admins, userText):
    if not checkPermissions(chatId, userId, admins):
        for symb in userText:
            if symb in blacklistSymbs:
                return True
    return False

#CHATGPT
def requestGPT(pmt):
    completion = openai.ChatCompletion.create(
        model=model,
        messages=[
            { 'role': 'user', 'content': pmt }
        ])
    return completion.choices[0].message.content

#это удаляет черепа
@dp.message_handler()
async def mainHandler(message: types.Message):
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if chatId != userId:
        admins = await bot.get_chat_administrators(chat_id=chatId)
    else:
        admins = None
    if checkTextOnBlacklistSymbs(chatId, userId, admins, userText):
        await bot.delete_message(chatId, messageId)
        msg = await bot.send_message(chatId, ')')
        await asyncio.sleep(3)
        await bot.delete_message(chatId, msg.message_id)
    if userId == IDMIHAIL:
        answerGPT = requestGPT(getTranslation('guard.promptGPT', [userText]))
        print(userText)
        print(f'GPT: {answerGPT}')
        if 'false' in answerGPT.lower():
            await bot.delete_message(chatId, messageId)
            msg = await bot.send_message(chatId, ')')
            await asyncio.sleep(3)
            await bot.delete_message(chatId, msg.message_id)'''

'''
#это удаляет стикеры михаила
@dp.message_handler(content_types='sticker')
async def detectstickersHandler(message: types.Message):
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if userId == IDMIHAIL:
        await bot.delete_message(chatId, messageId)
        msg = await bot.send_message(chatId, ')')
        await asyncio.sleep(3)
        await bot.delete_message(chatId, msg.message_id)

#это удаляет гифки михаила
@dp.message_handler(content_types='animation')
async def detectGIFsHandler(message: types.Message):
    chatId, userId, userName, userFullName, messageId, userText = getUserInfo(message)
    if userId == IDMIHAIL:
        await bot.delete_message(chatId, messageId)
        msg = await bot.send_message(chatId, ')')
        await asyncio.sleep(3)
        await bot.delete_message(chatId, msg.message_id)
'''