import paramiko
import datetime
import time
import multiprocessing
import sys
import collections

with open('equipos') as f:
    ips = f.read().splitlines()

port = 22
username = 'admin'
password = 'cisco!123'
date_time = datetime.datetime.now().strftime("%Y-%m-%d")
commands = ['show vpc | in fabricpath', "show fex", 'show ip int br | in Vlan | ex Vlan1']
archivo = "salida.txt"


def line_prepender(filename, line):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip("\r\n") + '\n' + content + "\n")


def run(ip):
    try:
        with multiprocessing.Pool(processes=5) as pool:
            pool.map(main, ip)

    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        pass


def main(ip):
    mensaje = ""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password, timeout=30,
                    disabled_algorithms=dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"]),
                    allow_agent=False,
                    look_for_keys=False)
        time.sleep(5)
        for indice, cmd in enumerate(commands):
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            time.sleep(2)
            outlines = stdout.readlines()
            resp = ''.join(outlines)
            print(ip, cmd)
            if not resp or "error" in resp:  # IF RESP IS EMPTY OR COMMAND NOT FOUND
                mensaje += "No tiene: " + cmd + "\n"
            else:
                #print("Si tiene: " + cmd)
                mensaje += "Si tiene: " + cmd + "\n"

        time.sleep(5)
        with open(archivo + "-" + str(date_time) + ".txt", "a") as f:
            f.write(ip + "\n")
            f.write(mensaje + "\n")
        ssh.close()

    except Exception as e:
        print(ip, e)
        with open(archivo + "-" + str(date_time) + ".txt", "a") as f:
            f.write(ip + ' No se conecta\n\n')


if __name__ == '__main__':
    run(ips)
    cont = []
    line_prepender(archivo + "-" + str(date_time) + ".txt", "\n\n")
    line_prepender(archivo + "-" + str(date_time) + ".txt", "*" * 50)
    with open(archivo + "-" + str(date_time) + ".txt", 'r+') as searchfile:  # r+ (read and append)
        for line in searchfile:
            for cmd in commands:
                if "No tiene: " + cmd in line:
                    cont.append(cmd)
    res = {i: cont.count(i) for i in cont}

    for key in res:
        #print(key, '->', res[key])
        line_prepender(archivo + "-" + str(date_time) + ".txt", "*** " + key + ' -> ' + str(res[key]) + " ***")
    line_prepender(archivo + "-" + str(date_time) + ".txt", "              TOTAL (NO TIENE)")
    line_prepender(archivo + "-" + str(date_time) + ".txt", "*" * 50)