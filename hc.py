import paramiko
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
commands = ["show ver | in  'kickstart:|system:'", "show vrf | ex VRF | ex Up", "show license usage | ex * | ex --- | ex Feat | ex Coun",
            "show module | ex Sw | ex MAC | ex -- | ex to | ex Ports | ex ok | ex active | ex standby | sed '/^$/d'", 
            "show diagnostic result module all | inc '> F'", "show system internal mts buffer summa | ex node |  cut -f 3-0",
            "show int desc | ex -- |  egrep 'Eth|Po' | ex Port | cut -d ' ' -f 1 | sed 's/\s*/show int br | egrep -w  /' | vsh | in down",
            "show port-channel summary | in SD | cut -d ' ' -f 1 | sed 's/\s*/show int port-channel / ' | vsh | in 'No operational'",
            "show vpc br | in status | in fail", "show system resources | in idle | head lines 1",
            "show fex | ex Online | ex FEX | ex Number | ex ----------------"]


archivo = "salida.txt"

def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[id])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict) # Return value ignored.
    return results



def line_prepender(filename, line):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip("\r\n") + '\n' + content + "\n")


def exact_Match(phrase, words):
    b = r'(\s|^|$)'
    for word in words:
        if re.match(b + word + b, phrase, flags=re.IGNORECASE) == None:
            continue
        else:
            return True


def returnNotMatches(a, b):
    return [x for x in b if x not in a]


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
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password, timeout=90,
                    allow_agent=False,
                    look_for_keys=False)
        time.sleep(10)
        print("*" * 50)
        print("*** HC ***")
        print("*" * 50)
        print("\n")
        out.append('Hostname: ' + ip)
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
            time.sleep(2)
            outlines = stdout.readlines()
            resp = ''.join(outlines)

            if "Cmd exec error" not in resp:
                if "ver" in cmd:
                    print("*** VERSION ***")
                    versiones = re.findall("\d.*", resp)
                    print(f'System {versiones[1]} Kickstart: {versiones[0]}')
                    out.append("*** VERSION ***")
                    out.append(f'System {versiones[1]} Kickstart: {versiones[0]}')
                    print("\n")

                if "vrf" in cmd:
                    if resp:
                        print("*** VRF ***")
                        out.append("*** VRF ***")
                        for x in resp.splitlines():
                            output = x.split()
                            if output[2] == "Down":
                                print(f"VRF: {output[0]} State: {output[2]} Reason: {' '.join(output[3:])}")
                                out.append(f"VRF: {output[0]} State: {output[2]} Reason: {' '.join(output[3:])}")
                        print("\n")

                if "show license usage" in cmd:
                    if resp:
                        for x in resp.splitlines():
                            output = x.split()
                            if output[-1] != "-":
                                print("*** LICENSE ***")
                                out.append("*** LICENSE ***")
                                print(f"License: {output[0]} State: {output[-1]}")
                                out.append(f"License: {output[0]} State: {output[-1]}")
                                print("\n")

                if "show module" in cmd:
                    if resp:
                        for x in resp.splitlines():
                            if x:
                                print("*** MODULE ***")
                                out.append("*** MODULE ***")
                                print(x)
                                out.append(x)
                    print("\n")

                if "diagnostic" in cmd:
                    if resp:
                        print("*** DIAGNOSTIC ***")
                        print(resp)
                        out.append("*** DIAGNOSTIC ***")
                        out.append(resp)
                        print("\n")
                if "show system internal mts" in cmd:
                    for x in resp.split():
                        if int(x) > 99:
                            print("*** SYSTEM INTERNAL MTS ***")
                            out.append("*** SYSTEM INTERNAL MTS ***")
                            print(x)
                            out.append(x)
                            print("\n")
                if "show int desc" in cmd:
                    if resp:
                        print("*** SHOW INT [BRIEF-DESC] ***")
                        out.append("*** SHOW INT [BRIEF-DESC] ***")
                        print(resp)
                        out.append(resp)
                        print("\n")

                if "show port-channel summary" in cmd:
                    if resp:
                        print("*** PORT-CHANNEL SUMMARY ***")
                        print(resp)
                        out.append("*** PORT-CHANNEL SUMMARY ***")
                        out.append(resp)
                        print("\n")

                if "show vpc br" in cmd:
                    if resp:
                        print("*** VPC BRIEF ***")
                        out.append("*** VPC BRIEF ***")
                        print(resp)
                        out.append(resp)
                        print("\n")

                if "show system resources" in cmd:
                    for x in resp.splitlines():
                        output = x.split()
                        if float(output[-2].replace("%", "")) < 60.0:
                            print("*** SYSTEM RESOURCES ***")
                            out.append("*** SYSTEM RESOURCES ***")
                            print(" ".join(output[-2:]))
                            out.append(" ".join(output[-2:]))
                            print("\n")

                if "show fex" in cmd:
                    for x in resp.splitlines():
                        if x:
                            print("*** FEX ***")
                            out.append("*** FEX ***")
                            print(x)
                            out.append(x)
                            print("\n")
        ssh.close()

    except Exception as e:
        print(ip, e)
        with open(archivo + "-" + str(date_time) + ".txt", "a") as f:
            f.write(ip + ' No se conecta\n\n')

    with open(ip + ".txt", "a") as f:
        for x in out:
            f.write(x + "\n\n")


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
