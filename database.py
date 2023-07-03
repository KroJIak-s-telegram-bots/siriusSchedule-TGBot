import sqlite3

class dbWorker:
	def __init__(self, databaseFile):
		self.connection = sqlite3.connect(databaseFile)
		self.cursor = self.connection.cursor()
		self.createTable('groups', (['chatId', 'INT PRIMARY KEY'], ['nameGroup', 'TEXT']))
		self.createTable('notifications', (['chatId', 'INT PRIMARY KEY'], ['condition', 'TEXT']))
		self.createTable('times', (['chatId', 'INT PRIMARY KEY'], ['hour', 'INT'], ['minute', 'INT']))

	def createTable(self, name, elements):
		with self.connection:
			command = f'CREATE TABLE IF NOT EXISTS {name}('
			for i, elm in enumerate(elements):
				ending = ','
				if i == len(elements)-1: ending = ');'
				command += f'{elm[0]} {elm[1]}{ending}'
			return self.cursor.execute(command)

	def groupExists(self, chatId):
		'''Проверка есть ли группа в бд'''
		with self.connection:
			result = self.cursor.execute('SELECT * FROM groups WHERE chatId = ?', (chatId, )).fetchall()
			return bool(len(result))

	def addGroup(self, chatId, nameGroup):
		'''Добавление название группы тг группы'''
		with self.connection:
			return self.cursor.execute('INSERT INTO groups (chatId, nameGroup) VALUES(?, ?)', (chatId, nameGroup))

	def setGroup(self, chatId, nameGroup):
		'''Выставить название группы тг группы'''
		with self.connection:
			return self.cursor.execute('UPDATE groups SET nameGroup = ? WHERE chatId = ?', (nameGroup, chatId))

	def getGroup(self, chatId):
		'''Получение название группы тг группы'''
		with self.connection:
			return self.cursor.execute('SELECT * FROM groups WHERE chatId = ?',(chatId, )).fetchone()[1]

	def getChatIds(self):
		'''Получение всех chatId'''
		with self.connection:
			return self.cursor.execute('SELECT chatId FROM groups').fetchone()

	def addNotification(self, chatId, condition):
		'''Добавление статус уведомления для тг группы'''
		with self.connection:
			return self.cursor.execute('INSERT INTO notifications (chatId, condition) VALUES(?, ?)', (chatId, str(condition)))

	def setNotification(self, chatId, condition):
		'''Выставить статус уведомления для тг группы'''
		with self.connection:
			return self.cursor.execute('UPDATE notifications SET condition = ? WHERE chatId = ?', (condition, str(chatId)))

	def getNotification(self, chatId):
		'''Получение статуса уведомлений для тг группы'''
		with self.connection:
			return self.cursor.execute('SELECT * FROM notifications WHERE chatId = ?',(chatId, )).fetchone()[1]

	def addTime(self, chatId, hour, minute):
		'''Добавление времени уведомления для тг группы'''
		with self.connection:
			return self.cursor.execute('INSERT INTO times (chatId, hour, minute) VALUES(?, ?, ?)', (chatId, hour, minute))

	def setTimeHour(self, chatId, hour):
		'''Выставить часы времени уведомления для тг группы'''
		with self.connection:
			return self.cursor.execute('UPDATE times SET hour = ? WHERE chatId = ?', (hour, chatId))

	def setTimeMinute(self, chatId, minute):
		'''Выставить минуты времени уведомления для тг группы'''
		with self.connection:
			return self.cursor.execute('UPDATE times SET minute = ? WHERE chatId = ?', (minute, chatId))

	def getTime(self, chatId):
		'''Получение времени уведомлений для тг группы'''
		with self.connection:
			return self.cursor.execute('SELECT * FROM times WHERE chatId = ?',(chatId, )).fetchone()[1:]