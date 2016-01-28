from sys import argv
from os.path import exists
from datetime import datetime
import socket
import json
from re import search
from random import choice


class Bot:
    """
    Core do boot.
    """
    STATUS_ONLINE = 'ONLINE'
    STATUS_OFFLINE = 'OFFLINE'
    COMMANDS = ('HELP', 'PING', 'HORA')
    CRITICAL_COMMANDS = ('BYE','RELOAD')

    _irc = None
    _connection_hour = None

    def __init__(self, json_file):
        # O path do arquivo fica numa variável de instância para o caso
        # de precisar chamar o __init__ manualmente.
        self.json_file = json_file
        self.setup()

    def setup(self):
        """
        Carrega as configurações do bot.
        :return:
        """
        json_data = self.get_json_data(self.json_file)

        # Realiza as checagens dos parâmetros.
        validator = BotSettingsValidator(json_data)
        validator.validate_params()
        validator.check_integrity('port')
        validator.check_type_integrity('logFile', 'file')
        validator.check_type_integrity('responsesFile', 'file')
        validator.check_type_integrity('owners', "<class 'list'>")
        validator.check_type_integrity('channels', "<class 'list'>")

        # Inicia o processo de configuração do bot.
        self.owners = json_data['owners']
        self.server = json_data['server']
        self.port = int(json_data['port'])
        self.nick = json_data['nick']
        self.password = json_data['password']
        self.channels = json_data['channels']
        self.networkWelcomeMessage = json_data['networkWelcomeMessage']
        self.responsesFile = json_data['responsesFile']
        self.responses = self.get_responses()

        if 'logFile' in json_data:
            self.log_file = json_data['logFile']

    def connect(self):
        """Conecta ao servidor."""
        self._irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._irc.connect((self.server, self.port))
        self._connection_hour = datetime.now().time()

        print(self._irc.recv(4096))

        self.log_bot_status(Bot.STATUS_ONLINE)
        self.set_nick()

    def post_connect_actions(self):
        """
        Ações a se realizar após se conectar.
        :return:
        """
        if self.channels:
            self.join(self.channels)

    def disconnect(self):
        """
        Desconecta.
        :return:
        """
        msg = 'QUIT Tchau.\r\n'
        self._irc.send(msg.encode())

    def set_nick(self):
        """Define o nick e faz a identificação no NickServ."""
        if self.password:
            password_command = 'PASS {}\r\n'.format(self.password)
            self._irc.send(password_command.encode())

        if self.nick:
            nick_command = 'NICK {}\r\n'.format(self.nick)
            self._irc.send(nick_command.encode())

            # O comando deve ser nesse formato: USER botnick algum_nome algum_nome :IRC BOT
            user_command = 'USER {} {} {} :IRC BOT\r\n'.format(self.nick, self.nick, self.nick)
            self._irc.send(user_command.encode())

    def listen(self):
        """Faz a escuta, exibe as mensagens e as salva no log."""
        while True:
            # Pega uma mensagem e formata.
            data = self._irc.recv(4096)
            line = '[{0}] {1}'.format(str(datetime.now()), str(data).replace('\\r','').replace('\\n', '\n'))
            print(line)

            # Conjunto de regex para pegar as estruturas que importam.
            if '!{}'.format(self.nick) in line:
                important_re = search('b\':\w.*', line)
                from_nick_re = search('[^b\':]\w*', important_re.group())
                channel_re = search(r'#\w[^PRIVMSG ]*\s', important_re.group())
                request_command_re = search(r'!xavierbot.*', important_re.group())
                request_command = request_command_re.group().replace('!{}'.format(self.nick), '').replace(' ', '').upper()

                from_nick = from_nick_re.group()
                channel = channel_re.group()

                msg = ''

                # Se o comando for válido...
                if request_command in self.COMMANDS:
                    if request_command == 'HELP':
                        msg = 'Eis os comandos que obedeço: {}'.format(str(self.COMMANDS).replace('\'', ''))

                    elif request_command == 'PING':
                        msg = 'PONG'

                    elif request_command == 'HORA':
                        msg = datetime.now().time().strftime('%H:%M:%S')

                elif request_command in self.CRITICAL_COMMANDS:
                    if from_nick in self.owners:
                        if request_command == 'BYE':
                            self.disconnect()
                            exit('Comando "BYE" solicitado. Então, bye.')

                        if request_command == 'RELOAD':
                            self.say_to_user_in_channel(channel, from_nick, 'Vou me reconfigurar. Guentaê!')
                            self.setup()
                            self.post_connect_actions()
                            self.say_to_user_in_channel(channel, from_nick, 'Pronto! :)')
                            continue
                    else:
                        msg = 'Você não pode solicitar esse comando. :('

                # Se o comando não for válido...
                else:
                    msg = self.get_random_response()

                # Responde um determinado comando no canal em que foi digitado.
                self.say_to_user_in_channel(channel, from_nick, msg)
                self.say_to_user_in_pvt(from_nick, msg.replace(channel, ''))

            # Só salva o log se o arquivo de log foi definido.
            if self.log_file:
                self.update_log(str(line))

            # Entra no canal apenas se a mensagem de boas vindas foi encontrada.
            # Isso significa que o comando para entrar no canal será executado
            # apenas quando o bot já estiver conectado.
            if self.networkWelcomeMessage.encode() in data:
                self.join(self.channels)

    def say_to_user_in_channel(self, channel, user, msg):
        response_msg = 'PRIVMSG {0} :{1}, {2}\r\n'.format(channel, user, msg)
        print('RESPOSTA ENVIADA: {}'.format(response_msg))
        self._irc.send(response_msg.encode())

    def say_to_user_in_pvt(self, user, msg):
        response_msg = 'PRIVMSG {0} :{1}\r\n'.format(user, msg)
        print('RESPOSTA ENVIADA: {}'.format(response_msg))
        self._irc.send(response_msg.encode())

    def join(self, channels=[]):
        """
        Entra em cada canal da lista recebida como parâmetro.
        :param channels: Lista de canais para entrar.
        :return:
        """
        if channels:
            for c in channels:
                join_command = 'JOIN #{}'.format(c) if c[0] != '#' else 'JOIN {}'.format(c)
                join_command += '\r\n'
                self._irc.send(join_command.encode())

    def get_json_data(self, json_file):
        """
        Retorna as configurações do JSON
        :param json_file:
        :return:
        """
        with open(json_file, 'r') as file:
            return json.load(file)

    def update_log(self, data):
        """
        Atualiza o arquivo de log, apenas se o arquivo de log
        foi devidamente configurado.
        :param data: Texto para salvar no arquivo.
        :return:
        """
        if not self.log_file:
            return

        with open(self.log_file, 'a') as f:
            f.write(data)

    def log_bot_status(self, status):
        """
        Salva o status do bot no arquivo de log.
        :param status: Deve ser ONLINE ou OFFLINE.
        :return:
        """
        self.update_log('#' * 30)
        self.update_log('[{0}]BOT STATUS{1}: {2}'.format(str(datetime.now()), '.' * 3, status))
        self.update_log('#' * 30)

    def get_responses(self):
        """
        Carrega as respostas contidas no arquivo de repostas.
        :return:
        """
        with open(self.responsesFile, 'r') as file:
            return file.readlines()

    def get_random_response(self):
        """
        Retorna, aleatoriamente, uma das respostas carregadas do arquivo.
        :return:
        """
        return choice(self.responses)

class BotSettingsValidator:
    """
    Validador do arquivo de congiguração JSON.
    """
    REQUIRED_PARAMS = ('owners','server', 'port',
                       'nick', 'password', 'channels',
                       'networkWelcomeMessage', 'responsesFile')

    CHECK_TYPES = ('numeric', 'file')

    def __init__(self, json_data):
        """
        :param json_data: Dicionário de configuração.
        :return:
        """
        """
        :param json_data:
        :return:
        """
        self.json_data = json_data

    def has_param(self, param):
        """
        Verifica se um parâmetro existe ou não no dicionário de configuração.
        :param param: Parâmetro a ser verificado.
        :return:
        """
        return param in self.json_data

    def _malformed_json(self, param):
        """
        Mata o programa com a mensagem de erro referenciando o parâmetro em falta.
        :param: Parâmetro em falta.
        :return:
        """
        exit('O parâmetro "{}" não foi encontrado no JSON.'.format(param))

    def _integrity_error(self, param):
        """
        Mata o programa com a mensagem de erro referenciando o parâmetro sem integridade.
        :param: Parâmetro sem integridade.
        :return:
        """
        exit('O parâmetro "{}" não possui um valor correto.'.format(param))

    def validate_params(self):
        """
        Verifica se os parâmetros obrigatórios estão definidos no dicionário.
        :return:
        """
        for param in self.REQUIRED_PARAMS:
            if param not in self.json_data:
                self._malformed_json(param)

    def check_integrity(self, param, check_type='numeric'):
        """
        Checa a integridade do valor do parâmetro.
        :param param: Parâmetro a ser checado.
        :param check_type: Tipo da checagem.
        :return:
        """
        if param in self.REQUIRED_PARAMS and check_type in self.CHECK_TYPES:

                if check_type == 'numeric':
                    if not self.json_data[param].isnumeric():
                        self._integrity_error(param)

                if check_type == 'file':
                    if not exists(self.json_data[param]):
                        self._integrity_error(param)

    def check_type_integrity(self, param, value):
        """
        Checa se o tipo do parâmetro é igual ao valor esperado.
        :param param: Parâmetro a ser checado.
        :param value: Valor esperado.
        :return:
        """
        if str(type(self.json_data[param])) == value:
            return True

        return False

if __name__ == '__main__':
    # Checa se existe o argumento do arquivo JSON.
    if len(argv) <= 1:
        print('Uso correto: python oxbot.py <params-file.json>')
        exit(0)

    # Checa se o arquivo de configuração informado existe.
    json_file_path = argv[1]
    if not exists(json_file_path):
        print('O arquivo informado não existe.')
        exit(0)

    # Bota o treco pra funcionar.
    try:
        bot = Bot(json_file_path)
        bot.connect()
        bot.listen()
    except KeyboardInterrupt:
        bot.log_bot_status(Bot.STATUS_OFFLINE)
        print('\nInterrompido por você. Tchau.')