from utils.funcs import joinPath

class configCategoryObject():
    def __init__(self, config, nameCategory):
        self.config = config
        self.nameCategory = nameCategory

    def get(self, elm):
        return self.config.get(self.nameCategory, elm)

class Telegram(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Telegram')
        self.token = self.get('token')
        self.alias = self.get('alias')
        self.messageTimeout = int(self.get('messageTimeout'))
        self.ownerUserId = self.get('ownerUserId')

class Data(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Data')
        self.usersDatabasePath = self.get('usersDatabasePath')
        self.chatsDatabasePath = self.get('chatsDatabasePath')
        self.availableLangs = self.get('availableLangs')
        self.availableLangs = self.availableLangs.split(', ')
        self.defaultLang = self.get('defaultLang')
        self.timeDifference = int(self.get('timeDifference'))

class Logging():
    def __init__(self):
        self.format = '%(asctime)s %(levelname)s %(message)s'

class Path():
    def __init__(self):
        self.project = joinPath('/', *__file__.split('/')[:-2])
        self.client = joinPath(self.project, 'client')
        self.db = joinPath(self.project, 'db')
        self.config = joinPath(self.client, 'config')
        self.lang = joinPath(self.client, 'lang')
        self.logs = joinPath(self.client, 'logs')

class File():
    def __init__(self):
        self.config = 'bot.ini'
        self.database = 'default.json'

class Default():
    def __init__(self):
        self.parseMode = 'HTML'
        self.file = File()

class Schedule():
    def __init__(self):
        self.url = 'http://kaktus23.ru:81/direction?name=%D0%9D%D0%B0%D1%83%D0%BA%D0%B0'

class Cats():
    def __init__(self):
        self.url = 'https://www.randomkittengenerator.com'

class Prefix():
    def __init__(self):
        self.setGroup = 'sg.'
        self.mainMenu = 'main.'

class Callback():
    def __init__(self):
        self.prefix = Prefix()
        self.textLimit = 15

class ConstPlenty():
    def __init__(self, config=None):
        if config: self.addConstFromConfig(config)
        self.path = Path()
        self.default = Default()
        self.logging = Logging()
        self.schedule = Schedule()
        self.cats = Cats()
        self.callback = Callback()

    def addConstFromConfig(self, config):
        self.telegram = Telegram(config)
        self.data = Data(config)