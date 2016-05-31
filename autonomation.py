import logging
import time
import paramiko
from colorama import Fore, init, Style


# usar um contextManager depois
class SSHManager:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.logger = logging.getLogger("SSHManager")
        self.channel = None
        self.hostname = None
        self.username = None
        self.password = None
        #init()

        fmt = '%(asctime)s MySSH:%(funcName)s:%(lineno)d %(message)s'
        format = logging.Formatter(fmt)
        handler = logging.StreamHandler()
        handler.setFormatter(format)
        self.logger.addHandler(handler)
        self.info = self.logger.info

    def connect(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

        print("{} Conectando {}@{}".format(Fore.GREEN, self.username, self.hostname))
        Style.RESET_ALL
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=self.hostname, username=self.username, password=self.password)
            self.channel = self.ssh.invoke_shell()  # abrindo o interative shell
            print(Fore.BLACK + "conexão realizada com sucesso!\n")
        except Exception as e:
            print("Falhou: {}".format(e.__str__()))

    def get_answer_msg(self, resposta, cmd):
        """trata a mensagem de resposta do comando executado"""

        # Busco na resposta o final do comando executado porque depois disso é o resultado do comando executado
        # caracters_to_match = cmd[len(cmd)-3:-1]  # se o comando tiver menos que três caracteres vai ter problema
        # len_carac_to_match = len(caracters_to_match)
        len_resp = len(resposta)
        # pos_init = resposta.rfind(caracters_to_match, 0, len_resp-1)
        pos_fim = resposta.rfind("\n", 0, len_resp)

        # r = resposta[pos_init + len_carac_to_match + 1: pos_fim]  # aqui encontrado a resposta do comnado executad
        r = resposta[pos_fim:].strip()
        # print("Cacete: {}".format(r))
        if r and len(r) > 0:
            # print("Rzinho%r" % r.lower())
            if r.lower() == "password:" or r.lower()[len(r)-1] in "$#" or r.lower in ["(y/n)", "(S/n)"]:
                return True
        elif not r and resposta:
            # print("Rzao: %r" % resposta.strip().lower())
            if resposta.strip().lower()[len(resposta.strip().lower())-1] in "$#":
                return True

        return False

    # pode ser interessante criar outro método que não use o invoke_shell do channel mas sim o exec_command do ssh
    def exec_interative_cmd(self, cmd, timeout=2):
        """Executa comandos no bash da máquina logada
           É usado o invoke_shell para executar tais comando.
           :param cmd: comando bash linux passado como parâmetro
           :param timeout: pode ser utilizado um timeout diferente para cada comando afim de ter mais informações
           de respostas do servidor.
           :return reposta do servidor aos comandos
        """

        print("Executando command: {}".format(cmd))
        buffer = []
        try:
            rcv_timeout = timeout
            interval_lenght = 0.1
            self.channel.send(cmd + "\n")
            # acho que vou ter de usar aqui o que usei para formatar a saída como controle
            # para fazer o break. o foda é saber quando parar
            # a o parar poder ser quando aparecer como ultimo o usuário logado como no exemplo -> devop@alog01:~$
            # derepente o padrão é terminar com # ou $ para saber vou ter de testar.
            resp = None
            auxresp = None
            while True:
                if self.channel.recv_ready():
                    # self.channel.recv(2000) retorna um string vazia quer dizer que a stream foi fechada
                    # pode ser uma saída para tirar o timeout
                    resp = self.channel.recv(2000).decode()
                    # print("RESP: {}".format(resp))
                    buffer.append(resp)  # channel.recv recebe bytes como resposta do server
                rcv_timeout -= interval_lenght

                if resp and self.get_answer_msg(resp, cmd):
                    print("{}".format(resp))
                    break
                else:
                    if resp != auxresp:
                        auxresp = resp
                        print("{}".format(auxresp))
                    # print("Time : %r" % rcv_timeout)
                    if rcv_timeout < 0:
                        rcv_timeout = 1
                    time.sleep(rcv_timeout)

        except Exception as e:
            print("Falhou: {}".format(e.__str__()))

        output = '\n'.join(buffer)
        return output

    def close(self):
        print("Fechando Conexão")
        self.ssh.close()