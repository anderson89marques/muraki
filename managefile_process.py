######################
#                    #
# pip install pyyaml #
#                    #
######################

import configparser
import yaml
from autonomation import SSHManager  # acho que deveria ser automation
from jinja2 import Template

# change user command
CHU_CMD = "su - {}"


class LoadFile:
    """Classe responsável por ler os arquivos .yaml e o arquivos de host.ini
       e resolver as expressões com o jinja2
    """
    def __init__(self):
        self.configparser = configparser.ConfigParser()

    def safe_load(self, file):
        with open(file, "r") as f:
            managefile = yaml.safe_load(f)

        return managefile

    def get_host_data(self, host):
        if "ip" and "username" and "password" in host:
            resp = host.split(" ")
            host_dict = {}

            if resp:
                if "ip" in resp[0]:
                    rp = resp[0].split("=")
                    host_dict[rp[0]] = rp[1]

                if "username" in resp[1]:
                    rp = resp[1].split("=")
                    host_dict[rp[0]] = rp[1]

                if "password" in resp[2]:
                    rp = resp[2].split("=")
                    host_dict[rp[0]] = rp[1]

        return host_dict

    def load_host_file(self):
        self.configparser.read("/etc/muraki/hosts.ini")

    def get_all_hosts(self):
        self.load_host_file()
        hs = []
        try:
            for section in self.configparser.sections():
                for conf in self.configparser[section]:
                    hs.append(self.get_host_data(self.configparser[section][conf]))
        except Exception as e:
            print(e.__str__())

        return hs

    def get_hosts(self, section):
        self.load_host_file()  # carrega os hosts.ini
        hs = []
        try:
            for conf in self.configparser[section]:
                hs.append(self.get_host_data(self.configparser[section][conf]))
        except Exception as e:
            print(e.__str__())

        return hs

    def exclui_barras_duplas(self, vars):
        for ind, var in enumerate(vars):
            for key, value in var.items():
                if "\\" in value:
                    var[key] = value.replace("\\", "")
                    vars[ind] = var

        return vars

    def vars_proccess_template(self, remote, vars):
        """Processando as expressions languages das variáveis(vars)"""

        print("**** processing template vars ***\n")

        variables = self.exclui_barras_duplas(vars)
        up = {}

        for var in variables:
            up.update(var)
            for key, value in var.items():
                if "{{" in value:
                    temp = Template(value)
                    var[key] = temp.render(up)
                    up[key] = var[key]
                    if "cmd" in var[key]:
                        v = remote.vars_exec_comand(var)
                        var[key] = v[key]
                        up[key] = var[key]
                        #remote.remote_conn.close()

        return variables

    def tasks_proccess_template(self, tasks, variables):
        """Processando as expressions languages das variáveis(vars)"""

        print("**** proccessing template tasks ****\n")

        vars = {k: v for var in variables for k, v in var.items()}

        for task in tasks:
            for key, value in task.items():
                if "{{" in value:
                    temp = Template(value)
                    task[key] = temp.render(vars)

        return tasks


class ExecComand:
    """classe responsável por executar os camandos definidos nos arquivos .yaml"""
    def __init__(self, host=None):
        self._remote_conn = None
        self.remote_conn = host

    @property
    def remote_conn(self):
        return self._remote_conn

    @remote_conn.setter
    def remote_conn(self, host):
        if not self.remote_conn:
            self._remote_conn = self._connect_host(host)

    def _connect_host(self, host) -> SSHManager:
        ssh = SSHManager()
        #ssh.connect("177.126.189.65", username="devop", password="T636:6yX")
        ssh.connect(hostname=host["ip"], username=host["username"], password=host["password"])
        return ssh

    def process_tasks(self, tasks):
        for task in tasks:
            self.exec_task(task)  # passando a tarefa para a função que irá trata-la

        self.remote_conn.close()

    def shell(self, task) -> str:
        return self.remote_conn.exec_interative_cmd(task)

    def copy(self, task):
        print(task)
        src_dest = task.split(" ")

        if len(src_dest) == 2:
            src = src_dest[0].split("=")[1]
            dest = src_dest[1].split("=")[1]
            print(src)
            print(dest)
            cmd = "cp {src} {dest}".format(src=src, dest=dest)
            return self.shell(cmd)
        else:
            raise Exception("Dados estão errados!")

    def wget(self):
        pass

    def vars_exec_comand(self, var):
        print("**** executing comands vars ****")

        for key, value in var.items():
            if "cmd" in value:
                print(value)
                k, cmd = value.split("=")
                try:
                    resp = self.shell(cmd)
                    r = self.get_answer_msg(resp, cmd)
                    var[key] = r.strip()
                except Exception as e:
                    print(e)

        return var

    def exec_task(self, task):
        """chama os executores de cada comando"""

        print(task['description'])
        if "change_user" in task:
            user = self.get_user_data(task['change_user'])
            self.change_user(user)
        elif "shell" in task:
            r = self.shell(task["shell"])
            resp = self.get_answer_msg(r, task["shell"])
            # if resp:
                # print("Result >\n{}".format(resp))  # trata a mensagem de resposta da execução do comando
        elif "copy" in task:
            r = self.copy(task["copy"])
            resp = self.get_answer_msg(r, task["copy"])
            # if resp:
                # print("Result >\n{}".format(resp))
        print("\n")  # só para formatar melhor

    def get_user_data(self, param) -> dict:
        """extraíndo os dados do usuário
        :param param: vem no formato name=user_name passwd=user_password
        """

        if 'name' in param and 'passwd' in param:
            l = param.split(" ")
            l_n = l[0].split("=")
            l_p = l[1].split("=")
            return {'name': l_n[1], 'password': l_p[1]}

    def change_user(self, user):
        self.remote_conn.exec_interative_cmd(CHU_CMD.format(user['name']))
        # aqui se não tiver o user password deve pedir para o usuário digitar a senha(Ainda por implementar)
        if user.get('password'):
            self.remote_conn.exec_interative_cmd(user['password'])

    def get_answer_msg(self, resposta, cmd):
        """trata a mensagem de resposta do comando executado"""

        # Busco na resposta o final do comando executado porque depois disso é o resultado do comando executado
        caracters_to_match = cmd[len(cmd)-3:-1]  # se o comando tiver menos que três caracteres vai ter problema
        len_carac_to_match = len(caracters_to_match)
        len_resp = len(resposta)
        pos_init = resposta.rfind(caracters_to_match, 0, len_resp-1)
        pos_fim = resposta.rfind("\n", 0, len_resp)

        r = resposta[pos_init + len_carac_to_match + 1: pos_fim]  # aqui encontrado a resposta do comnado executad

        return r


def process():
    load_file = LoadFile()
    managefile = load_file.safe_load("/home/anderson/PycharmProjects/muraki/teste.yaml")
    print(managefile)
    # para lê o arquivo de hosts vou usar o ConfigParser

    # quando criar o contextManger substituir por with fora do for

    for manage in managefile:
        if manage["hosts"] == "all":
            # para cada host será executado aquelas tarefas, lá também deve ser passado login e senha
            # deve retornar uma lista de mapas com os dados necessários, ip, username, password de cada host
            hosts = load_file.get_all_hosts()
        else:
            hosts = load_file.get_hosts(manage["hosts"])

        print("HOSTS: {}".format(hosts))
        for host in hosts:
            remote_host = ExecComand(host)
            if manage.get('vars'):
                variables = load_file.vars_proccess_template(remote_host, manage['vars'])  # templating dos vars
                tasks = load_file.tasks_proccess_template(manage['tasks'], variables)      # templating das tasks
            else:
                tasks = manage['tasks']

            remote_host.process_tasks(tasks)
process()