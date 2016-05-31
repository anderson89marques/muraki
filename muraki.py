#! /home/anderson/.managerEnv/bin/python

########################################################################################
#                                                                                      #
# Muraki significa trabalho em nheengatu que é o tupi moderno que é uma lígua indígena #
#                                                                                      #
########################################################################################

#
# import paramiko
# import time
#
# ssh = paramiko.SSHClient()
#
# # para aceitar automáticamente as chaves, usar com cuidado
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect("177.126.189.65", username="devop", password="T636:6yX")
# # stdin, stdout, stderr = ssh.exec_command("ls\n")
# # print(stdout.readlines())
# channel = ssh.invoke_shell()
# channel.send('su -\n')
# while not channel.recv_ready():
#     time.sleep(1)
# print(channel.recv(1024))
#
# channel.send('mouse32\n')
# while not channel.recv_ready():
#     time.sleep(1)
# print(channel.recv(1024))
# channel.send('ls\n')
# while not channel.recv_ready():
#     time.sleep(1)
# print(channel.recv(1024).decode())
#
# channel.send('su - devop\n')
# while not channel.recv_ready():
#     time.sleep(1)
# print(channel.recv(1024).decode())
#
# channel.send('T636:6yX\n')
# while not channel.recv_ready():
#     time.sleep(1)
# print(channel.recv(1024).decode())
#
# channel.send('ls\n')
# while not channel.recv_ready():
#     time.sleep(1)
# print(channel.recv(1024).decode())
#
# ssh.close()
# # endregion
from autonomation import SSHManager

ssh = SSHManager()
ssh.connect("177.126.189.65", username="devop", password="T636:6yX")

comands = [
    "su -",
    "mouse32",
    "cd /home/devop/workspace/vendafacil/web-coadquirencia/",
    "chown devop:devop -R target",
    "su - devop",
    "cd /home/devop/workspace/vendafacil/web-coadquirencia/",
    "git status",
    "git pull origin vendafacil-prod",
    "source prepare-jvm",
    "./deploy",
]

for cmd in comands:
    if cmd == "./deploy":
        resp = ssh.exec_interative_cmd(cmd, timeout=20)  # para eu ter mais informações do deploy
    else:
        resp = ssh.exec_interative_cmd(cmd)
    #print(resp)
    print("/"*10)
ssh.close()