import sqlite3

class dbWorker:
	def __init__(self, databaseFile):
		self.connection = sqlite3.connect(databaseFile)
		self.cursor = self.connection.cursor()
		self.createTable('groups', (['chatId', 'INT PRIMARY KEY'], ['nameGroup', 'TEXT']))
		self.createTable('notifications', (['chatId', 'INT PRIMARY KEY'], ['condition', 'TEXT']))
		self.createTable('times', (['chatId', 'INT PRIMARY KEY'], ['hour', 'INT'], ['minute', 'INT']))
		self.createTable('pins', (['chatId', 'INT PRIMARY KEY'], ['messageId', 'INT']))
		self.createTable('langs', (['chatId', 'INT PRIMARY KEY'], ['lang', 'TEXT']))
		self.createTable('messages', (['chatId', 'INT PRIMARY KEY'], ['messageIds', 'TEXT']))
		self.createTable('users', (['chatId', 'INT PRIMARY KEY'], ['username', 'TEXT'], ['userFullName', 'TEXT']))

	def createTable(self, name, elms):
		with self.connection:
			command = f'CREATE TABLE IF NOT EXISTS {name}('
			for i, elm in enumerate(elms):
				ending = ','
				if i == len(elms)-1: ending = ');'
				command += f'{elm[0]} {elm[1]}{ending}'
			return self.cursor.execute(command)

	def getChatIds(self):
		'''Получение всех chatId'''
		with self.connection:
			return list(map(lambda x: x[0], self.cursor.execute("""SELECT chatId FROM groups""").fetchall()))

	def tableExists(self, chatId, name):
		'''Проверка есть ли группа в бд'''
		with self.connection:
			result = self.cursor.execute(f"""SELECT * FROM {name} WHERE chatId = {chatId}""").fetchall()
			return bool(len(result))

	def add2Table(self, chatId, name, elms):
		'''Добавление название группы тг группы'''
		with self.connection:
			keys = ", ".join(elms.keys())
			rawValues = [str(chatId)]
			for value in elms.values():
				resValue = f"'{value}'" if isinstance(value, str) else str(value)
				rawValues.append(resValue)
			values = ', '.join(rawValues)
			return self.cursor.execute(f"""INSERT INTO {name} (chatId, {keys}) VALUES({values})""")

	def setInTable(self, chatId, name, elm):
		'''Выставить название группы тг группы'''
		with self.connection:
			key = list(elm.keys())[0]
			value = f"'{elm[key]}'" if isinstance(elm[key], str) else str(elm[key])
			return self.cursor.execute(f"""UPDATE {name} SET {key} = {value} WHERE chatId = {chatId}""")

	def getFromTable(self, chatId, name):
		'''Получение название группы тг группы'''
		with self.connection:
			return self.cursor.execute(f"""SELECT * FROM {name} WHERE chatId = {chatId}""").fetchone()[1:]