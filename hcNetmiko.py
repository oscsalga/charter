import paramiko
from netmiko import ConnectHandler, NetMikoAuthenticationException, NetMikoTimeoutException
import datetime
import time
import multiprocessing
import sys
import json
import re

with open('equipos') as f:
    ips = f.read().splitlines()


port = 22
username = 'p3121751'
password = 'Ximena12.'
date_time = datetime.datetime.now().strftime("%Y-%m-%d")
"""commands = ["show ver | in  'kickstart:|system:'", "show vrf | ex VRF | ex Up",
            "show license usage | ex * | ex --- | ex Feat | ex Coun | sed '/^$/d'",
            "show module | ex Sw | ex MAC | ex -- | ex to | ex Ports | ex ok | ex active | ex standby | sed '/^$/d'",
            "show diagnostic result module all | inc '> F'",
            "show system internal mts buffer summa | ex node |  cut -f 3-0",
            "show int desc | ex -- |  egrep 'Eth|Po' | ex Port | cut -d ' ' -f 1 | sed 's/\s*/show int br | egrep -w  /' | vsh | in down",
            "show port-channel summary | in SD | cut -d ' ' -f 1 | sed 's/\s*/show int port-channel / ' | vsh | in down | ex watch",
            "show vpc br | in status | in fail", "show system resources | in idle | head lines 1",
            "show fex | ex Online | ex FEX | ex Number | ex ----------------",
            "show ip bgp summary vrf all | inc '^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}).*'"]"""

archivo = "salida.txt"
commands = ["show license usage | ex * | ex --- | ex Feat | ex Cou"]


def conectar(ip):
    try:
        tunnel = ConnectHandler(device_type="cisco_nxos", ip=ip, password=password,
                                port=port, username=username, banner_timeout=200000,
                                timeout=2000)
        if tunnel.is_alive():
            return tunnel

    except Exception as e:
        # print(str(e))
        pass


def ejecutar_comando(tunnel, comando):
    output = ""
    try:
        output = tunnel.send_command(comando, expect_string="#", max_loops=5000, delay_factor=5000, read_timeout=150)
        # output = tunnel.send_command(comando, expect_string="#", delay_factor=5)

    except Exception as e:
        print(e)
    return output


def exact_Match(phrase, words):
    b = r'(\s|^|$)'
    for word in words:
        if re.match(b + word + b, phrase, flags=re.IGNORECASE) == None:
            continue
        else:
            return True


def run(ip):
    try:
        with multiprocessing.Pool(processes=5) as pool:
            pool.map(main, ip)

    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        pass


def main(ip):
    out = []

    tunnel = conectar(ip)

    if tunnel:
        print("*" * 50)
        print("*** HC ***")
        print("*" * 50)
        print("\n")
        print('Hostname: ' + ip)
        for cmd in commands:

            try:
                output = ejecutar_comando(tunnel, cmd)

                if "command at" not in output:
                    if "ver" in cmd:
                        print("*** VERSION ***")
                        versiones = re.findall("\d.*", output)
                        print(f'Hostname: {ip} System {versiones[1]} Kickstart: {versiones[0]}')
                        out.append(f'Hostname: {ip} System {versiones[1]} Kickstart: {versiones[0]}')
                        out.append("*" * 50)
                        print("*" * 50)
                        print("\n")

                    if "show vrf" in cmd:
                        if output:
                            print("*** VRF ***")
                            print(ip)
                            out.append("*** VRF ***")
                            for x in output.splitlines():
                                lista = x.split()
                                if lista[2] == "Down":
                                    print(f"VRF: {output[0]} State: {output[2]} Reason: {' '.join(output[3:])}")
                                    out.append(f"VRF: {output[0]} State: {output[2]} Reason: {' '.join(output[3:])}")
                            print("\n")

                    if "show license usage" in cmd:
                        if output:
                            for x in output.splitlines():
                                lista = x.split()
                                if lista[-1] != "-":
                                    print("*** LICENSE ***")
                                    out.append("*** LICENSE ***")
                                    print(f"License: {output[0]} State: {output[-1]}")
                                    out.append(f"License: {output[0]} State: {output[-1]}")
                                    print("\n")

                    if "show module" in cmd:
                        if output:
                            print("*** MODULE ***")
                            out.append("*** MODULE ***")
                            for x in output.splitlines():
                                if x:
                                    print(x)
                                    out.append(x)
                        print("\n")

                    if "diagnostic" in cmd:
                        if output:
                            print("*** DIAGNOSTIC ***")
                            print(output)
                            out.append("*** DIAGNOSTIC ***")
                            out.append(output)
                            print("\n")
                    if "show system internal mts" in cmd:
                        if output:
                            for x in output.split():
                                if int(x) > 99:
                                    print("*** SYSTEM INTERNAL MTS ***")
                                    out.append("*** SYSTEM INTERNAL MTS ***")
                                    print(x)
                                    out.append(x)
                                    print("\n")
                    if "show int desc" in cmd:
                        if output:
                            print("*** SHOW INT [BRIEF-DESC] ***")
                            out.append("*** SHOW INT [BRIEF-DESC] ***")
                            print(output)
                            out.append(output)
                            print("\n")

                    if "show port-channel summary" in cmd:
                        if output:
                            print("*** PORT-CHANNEL SUMMARY ***")
                            print(output)
                            out.append("*** PORT-CHANNEL SUMMARY ***")
                            out.append(output)
                            print("\n")

                    if "show vpc br" in cmd:
                        if output:
                            print("*** VPC BRIEF ***")
                            out.append("*** VPC BRIEF ***")
                            print(output)
                            out.append(output)
                            print("\n")

                    if "show system resources" in cmd:
                        if output:
                            for x in output.splitlines():
                                lista = x.split()
                                if float(lista[-2].replace("%", "")) < 60.0:
                                    print("*** SYSTEM RESOURCES ***")
                                    out.append("*** SYSTEM RESOURCES ***")
                                    print(" ".join(lista[-2:]))
                                    out.append(" ".join(lista[-2:]))
                                    print("\n")

                    if "show fex" in cmd:
                        if output:
                            for x in output.splitlines():
                                if x:
                                    print("*** FEX ***")
                                    out.append("*** FEX ***")
                                    print(x)
                                    out.append(x)
                                    print("\n")

                    if "show ip bgp summary vrf all" in cmd:
                        if output:
                            for x in output.splitlines():
                                lista = x.split()
                                if lista[-1] != "Idle":
                                    print("*** BGP ***")
                                    out.append("*** BGP ***")
                                    print(output)
                                    out.append(output)
                                    print("\n")

            except Exception as e:
                print(e)
                with open(ip + ".txt", "a") as f:
                    f.write(str(e) + "\n")
                pass
        with open(ip + ".txt", "a") as f:
            if out:
                for x in out:
                    f.write(x + "\n\n")

    out.append("*" * 80)
    tunnel.disconnect()


if __name__ == '__main__':
    run(ips)

#  show vrf | json
#  show license usage | json
#  show ver | in  "kickstart:|system:"     \d.*
#  show mod   [a-zA-Z]+?(?=\s*?[^\w]*?$)
#  show diagnostic result module all | inc "> F"
#  show system internal mts buffer summa | ex node |  cut -f 3-0
#  show int desc | ex -- |  egrep "Eth|Po" | ex Port | cut -d " " -f 1 | sed 's/\s*/show int br | egrep -w  /' | vsh | in down
#  show port-channel summary | in SD | cut -d " " -f 1 | sed 's/\s*/show int port-channel / ' | vsh | in "No operational"
#  show vpc br | json
#  show system resources | json
#  FALTA show ip bgp summary vrf all | inc [0-9,1-3].[0-9,1-3].[0-9,1-3]
#  FALTA show ipv6 bgp summary vrf all | inc [a-f0-9,1-4]:[a-f0-9,1-4]
#  show fex | json


# show env todo lo de abajo


data = """{
  "fandetails": {
    "TABLE_faninfo": {
      "ROW_faninfo": [
        {
          "fanname": "Chassis-1", 
          "fanmodel": "N5548P-FAN", 
          "fanhwver": "--", 
          "fanstatus": "ok"
        }, 
        {
          "fanname": "Chassis-2", 
          "fanmodel": "N5548P-FAN", 
          "fanhwver": "--", 
          "fanstatus": "ok"
        }, 
        {
          "fanname": "PS-1", 
          "fanmodel": "--", 
          "fanhwver": "--", 
          "fanstatus": "absent"
        }, 
        {
          "fanname": "PS-2", 
          "fanmodel": "N55-PAC-750W", 
          "fanhwver": "--", 
          "fanstatus": "ok"
        }
      ]
    }, 
    "fan_filter_status": "NotSupported"
  }, 
  "TABLE_tempinfo": {
    "ROW_tempinfo": {
      "tempmod": "1", 
      "sensor": "Outlet", 
      "majthres": "67", 
      "minthres": "58", 
      "curtemp": "29", 
      "alarmstatus": "ok"
    }
  }, 
  "powersup": {
    "voltage_level": 12, 
    "TABLE_psinfo": {
      "ROW_psinfo": [
        {
          "psnum": 1, 
          "psmodel": "------------", 
          "watts": "0.00", 
          "amps": "0.00", 
          "ps_status": "absent"
        }, 
        {
          "psnum": 2, 
          "psmodel": "N55-PAC-750W", 
          "watts": "780.00", 
          "amps": "65.00", 
          "ps_status": "ok"
        }
      ]
    }, 
    "TABLE_mod_pow_info": {
      "ROW_mod_pow_info": [
        {
          "modnum": "1", 
          "mod_model": "N5K-C5548P-SUP", 
          "watts_requested": "468.00", 
          "amps_requested": "39.00", 
          "watts_alloced": "468.00", 
          "amps_alloced": "39.00", 
          "modstatus": "powered-up"
        }, 
        {
          "modnum": "3", 
          "mod_model": "N55-DL2", 
          "watts_requested": "24.00", 
          "amps_requested": "2.00", 
          "watts_alloced": "24.00", 
          "amps_alloced": "2.00", 
          "modstatus": "powered-up"
        }
      ]
    }, 
    "power_summary": {
      "ps_redun_mode": "redundant", 
      "ps_redun_op_mode": "Non-redundant", 
      "tot_pow_capacity": "780.00", 
      "reserve_sup": "468.00", 
      "pow_used_by_mods": "24.00", 
      "available_pow": "288.00"
    }
  }
}"""

"""print(find_values('fanstatus', data))
print(find_values('ps_status', data))
print(find_values('modstatus', data))
print(find_values('alarmstatus', data))"""
