from sys import argv
from os.path import exists
from datetime import datetime
import socket
import json


class Bot:

    STATUS_ONLINE = 'ONLINE'
    STATUS_OFFLINE = 'OFFLINE'

    _irc = None

    def __init__(self, server='irc.freenode.net', port=6667, nick=None, password=None,
                 channels=None, networkWelcomeMessage=None, log_file=None):
        """
        Construtor que recebe os argumentos necessários para fazer a
        conexão ser bem sucedida.
        :param server: Servidor para se conectar.
        :param port: Porta do servidor.
        :param nick: Nick do bot.
        :param password: Senha do bot.
        :param channels: Lista de canais para se conectar.
        :param log_file: Arquivo de log.
        :return:
        """
        self.server = server
        self.port = port
        self.nick = nick
        self.password = password
        self.channels = channels
        self.networkWelcomeMessage = networkWelcomeMessage
        self.log_file = log_file

    def cmd(self, param):
        """Executa o comando recebido como parâmetro."""
        cmd = '{}\r\n'.format()
        self._irc.send(cmd.encode())

    def connect(self):
        """Conecta ao servidor."""
        self._irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._irc.connect((self.server, self.port))

        print(self._irc.recv(4096))

        self.log_bot_status(Bot.STATUS_ONLINE)

        self.set_nick()

        if self.channels:
            self.join(self.channels)

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
            data = self._irc.recv(4096)
            log_line = '[{0}] {1}'.format(str(datetime.now()), str(data).replace('\\r','').replace('\\n', '\n'))

            print(log_line)

            if self.log_file:
                self.update_log(str(log_line))

            if self.networkWelcomeMessage.encode() in data:
                self.join(self.channels)

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


def malformed_json(param, not_expected_msg=False):
    if not_expected_msg:
        exit('O parâmetro "{}" no JSON tem um valor inválido.'.format(param))

    exit('O parâmetro "{}" não foi encontrado no JSON.'.format(param))

if __name__ == '__main__':
    if len(argv) <= 1:
        print('Uso correto: python oxbot.py <params-file.json>')
        exit(0)

    json_file_path = argv[1]
    if not exists(json_file_path):
        print('O arquivo informado não existe.')
        exit(0)

    json_data = None
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)

    if 'server' not in json_data:
        malformed_json('server')

    if 'server' not in json_data or not json_data['port'].isnumeric():
        malformed_json('port')

    if 'nick' not in json_data:
        malformed_json('nick')

    if 'password' not in json_data:
        malformed_json('password')

    if 'channels' not in json_data:
        malformed_json('channels')
    else:
        if str(type(json_data['channels'])) != "<class 'list'>":
            malformed_json('channels', True)

    if 'networkWelcomeMessage' not in json_data:
        malformed_json('networkWelcomeMessage')

    bot = Bot()
    bot.server = json_data['server']
    bot.port = int(json_data['port'])
    bot.nick = json_data['nick']
    bot.password = json_data['password']
    bot.channels = json_data['channels']
    bot.networkWelcomeMessage = json_data['networkWelcomeMessage']

    if 'logFile' in json_data:
        bot.log_file = json_data['logFile']

    try:
        bot.connect()
        bot.listen()
    except KeyboardInterrupt:
        bot.log_bot_status(Bot.STATUS_OFFLINE)
        print('\nInterrompido por você.')