import paramiko
import datetime
import time
import multiprocessing
import sys
import re
import pandas as pd
import os
import time
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map


with open('equipos') as f:
    ips = f.read().splitlines()

port = 22
username = 'admin'
password = 'cisco!123'

date_time = datetime.datetime.now().strftime("%Y-%m-%d")
commands = ["show ver | in  'kickstart:|system:'",
            "show vrf | ex VRF | ex Up",
            "show license usage | ex * | ex --- | ex Feat | ex Coun",
            "show module | ex Sw | ex MAC | ex -- | ex to | ex Ports | ex ok | ex active | ex standby | sed '/^$/d'",
            "show diagnostic result module all | inc '> F'",
            "show system internal mts buffer summa | ex node |  cut -f 3-0",
            "show int desc | ex -- |  egrep 'Eth|Po' | ex Port | cut -d ' ' -f 1 | sed 's/\s*/show int br | egrep -w  /' | vsh | in down",
            "show port-channel summary | in SD | cut -d ' ' -f 1 | sed 's/\s*/show int port-channel / ' | vsh | in down | ex watch",
            "show vpc br | in status | in fail", "show system resources | in idle | head lines 1",
            "show fex | ex Online | ex FEX | ex Number | ex ----------------",
            "show ip bgp summary vrf all | inc '^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}).*'",
            "show fabricpath isis interface br | in Up | ex Interface"]


archivo = "salida.txt"

#commands = ["show license usage | ex * | ex --- | ex Feat | ex Coun"]


def combinar():
    output_excel = r'all_excels.xlsx'
    excel_files = [os.path.join(root, file) for root, folder, files in os.walk(".") for file in files if
                   file.endswith(".xlsx")]

    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:

        for excel in excel_files:
            sheet_name = str(excel).replace(".xlsx", "").replace("./", "")
            if output_excel in excel:
                continue
            df = pd.read_excel(excel, engine="openpyxl")
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            workbook = writer.book
            worksheet = writer.sheets[str(sheet_name)]
            formato = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
            titulo = workbook.add_format({'bg_color': '19b2e7'})
            worksheet.conditional_format(0, 0, 0, worksheet.dim_colmax,
                                         {'criteria': ">", 'value': -1, 'type': 'cell', 'format': titulo})
            format = workbook.add_format({'text_wrap': True})

            # Setting the format column A-B width to 50.
            worksheet.set_column('A:B', 70, format)

def run(ip):
    try:
        with multiprocessing.Pool(processes=20) as pool:
            process_map(main, ip)
            #pool.map(main, ip)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        pass
        #print(e)


def auto_width_columns(df, worksheet, formato):
    for s, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).str.len().max(), len(col) + 2)
        worksheet.set_column(s, s, column_len, formato)


def main(ip):
    out = []
    ssh = None
    tunnel = False
    df = {'Command': commands}
    df = pd.DataFrame(df, columns=['Command', 'Value'])



    try:

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username, password, timeout=90,
                    allow_agent=False,
                    look_for_keys=False)
        time.sleep(10)
        tunnel = ssh.get_transport().is_alive()
    except paramiko.AuthenticationException as e:
        print(ip, e)
        with open(archivo + "-" + str(date_time) + ".txt", "a") as f:
            f.write(ip + ' No se conecta\n\n')

    if tunnel:

        path = ip + ".xlsx"  # NOMBRE DEL OUTPUT FILE
        writer = pd.ExcelWriter(path, engine='xlsxwriter')
        """print("*" * 50)
        print("*** HC ***")
        print("*" * 50)
        print("\n")
        print(f"Hostname: {ip}")"""

        for indice, cmd in enumerate(commands):
            cell = []


            try:
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
                outlines = stdout.readlines()
                time.sleep(2)
                output = ''.join(outlines)

                if "error" not in output:
                    if output:
                        if "show ver" in cmd:
                            #print("*** VERSION ***")
                            versiones = re.findall("\d.*", output)
                            #print(f'Hostname: {ip} System {versiones[1]} Kickstart: {versiones[0]}')
                            out.append(f'Hostname: {ip} System {versiones[1]} Kickstart: {versiones[0]}')
                            out.append("*" * 50)
                            #print("*" * 50)
                            df.at[indice, 'Value'] = f"System {versiones[1]} Kickstart: {versiones[0]}"
                            #print("\n")

                        if "show vrf" in cmd:

                            if output.splitlines():
                                #print("*** VRF ***")
                                out.append("*** VRF ***")
                                for x in output.splitlines():
                                    lista = x.split()
                                    if lista:
                                        if lista[2] == "Down":
                                            cell.append(f"VRF: {lista[0]} State: {lista[2]} Reason: {' '.join(lista[3:])}")
                                            #print(f"VRF: {lista[0]} State: {lista[2]} Reason: {' '.join(lista[3:])}")
                                            out.append(
                                                f"VRF: {lista[0]} State: {lista[2]} Reason: {' '.join(lista[3:])}")
                                df.at[indice, 'Value'] = '\n'.join(cell)
                                #print("\n")

                        if "show license usage" in cmd:

                            flag = True
                            for x in output.splitlines():
                                lista = x.split()
                                if lista:
                                    if lista[-1] != "-":
                                        if flag:
                                            #print("*** LICENSE ***")
                                            out.append("*** LICENSE ***")
                                        #print(f"License: {lista[0]} State: {lista[-1]}")
                                        out.append(f"License: {lista[0]} State: {lista[-1]}")
                                        cell.append(f"License: {lista[0]} State: {lista[-1]}")
                                        flag = False
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                        if "show module" in cmd:

                            #print("*** MODULE ***")
                            out.append("*** MODULE ***")
                            for x in output.splitlines():
                                if x:
                                    #print(x)
                                    out.append(x)
                                    cell.append(x)
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                        if "diagnostic" in cmd:
                            #print("*** DIAGNOSTIC ***")
                            #print(output)
                            out.append("*** DIAGNOSTIC ***")
                            out.append(output)
                            cell.append(output)
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                        if "show system internal mts" in cmd:
                            for x in output.split():
                                if int(x) > 99:
                                    #print("*** SYSTEM INTERNAL MTS ***")
                                    out.append("*** SYSTEM INTERNAL MTS ***")
                                    #print(x)
                                    out.append(x)
                                    cell.append(x)
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                        if "show int desc" in cmd:
                            #print("*** SHOW INT [BRIEF-DESC] ***")
                            out.append("*** SHOW INT [BRIEF-DESC] ***")
                            #print(output)
                            out.append(output)
                            df.at[indice, 'Value'] = output
                            #print("\n")

                        if "show port-channel summary" in cmd:
                            #print("*** PORT-CHANNEL SUMMARY ***")
                            #print(output)
                            out.append("*** PORT-CHANNEL SUMMARY ***")
                            out.append(output)
                            df.at[indice, 'Value'] = output
                            #print("\n")

                        if "show vpc br" in cmd:
                            #print("*** VPC BRIEF ***")
                            out.append("*** VPC BRIEF ***")
                            #print(output)
                            out.append(output)
                            df.at[indice, 'Value'] = output
                            #print("\n")

                        if "show system resources" in cmd:
                            for x in output.splitlines():
                                lista = x.split()
                                if lista:
                                    if float(lista[-2].replace("%", "")) < 60.0:
                                        #print("*** SYSTEM RESOURCES ***")
                                        out.append("*** SYSTEM RESOURCES ***")
                                        #print(" ".join(lista[-2:]))
                                        out.append(" ".join(lista[-2:]))
                                        cell.append(" ".join(lista[-2:]))
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                        if "show fex" in cmd:
                            #print("*** FEX ***")
                            out.append("*** FEX ***")
                            #print(" ".join(output.splitlines()))
                            out.append(" ".join(output.splitlines()))
                            df.at[indice, 'Value'] = '\n'.join(output.splitlines())
                            #print("\n")

                        if "show ip bgp summary vrf all" in cmd:
                            for x in output.splitlines():
                                lista = x.split()
                                if "Idle" in lista:
                                    #print("*** BGP ***")
                                    out.append("*** BGP ***")
                                    #print(" ".join(lista))
                                    out.append(" ".join(lista))
                                    cell.append(" ".join(lista))
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                        if "show fabricpath isis interface br | in Up | ex Interface" in cmd:
                            for x in output.splitlines():
                                lista = x.split()
                                if "Up/Ready" not in lista:
                                    #print("*** FABRICPATH TOPOLOGY ***")
                                    out.append("*** FABRICPATH TOPOLOGY ***")
                                    #print(" ".join(lista))
                                    out.append(" ".join(lista))
                                    cell.append(" ".join(lista))
                            df.at[indice, 'Value'] = '\n'.join(cell)
                            #print("\n")

                else:
                    with open("ERROR.txt", "a") as f:
                        f.write(ip + "# " + " " + cmd + " " + "\n")
            except Exception as e:
                #print(e)
                with open("ERROR.txt", "a") as f:
                    f.write(ip + "# " + " " + cmd + " " + "\n")

        out.append("*" * 80)
        ssh.close()
        if len(out) > 4:
            with open(ip + ".txt", "a") as f:
                if out:
                    for x in out:
                        f.write(x + "\n")
                f.write("\n")

            df.to_excel(writer, sheet_name=ip, index=False)
            workbook = writer.book
            worksheet = writer.sheets[ip]

            writer.save()


if __name__ == '__main__':
    run(ips)
    #r = process_map(main, ips, max_workers=20)
    combinar()
