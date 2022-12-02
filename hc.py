import paramiko
import datetime
import time
import multiprocessing
import sys
import re
import pandas as pd
import os
import time
from tqdm.contrib.concurrent import process_map  # or thread_map


with open('equipos') as f:
    ips = f.read().splitlines()

port = 22
username = 'admin'
password = 'CXlabs.123'

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
            "show fabricpath isis interface br | in Up | ex Interface",
            "show jsjb jje"]


archivo = "salida.txt"
output_excel = r'all_excels.xlsx'
#commands = ["show license usage | ex * | ex --- | ex Feat | ex Coun"]


def combinar():

    excel_files = [os.path.join(root, file) for root, folder, files in os.walk(".") for file in files if
                   file.endswith(".xlsx")]
    excl_list = []


    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:

        for excel in excel_files:
            if output_excel in excel:
                continue

            df = pd.read_excel(excel, engine="openpyxl")
            excl_list.append(df)
        excl_merged = pd.concat(excl_list, axis=1)
        excl_merged.to_excel(writer, sheet_name="MASTER", index=False)
        excl_merged.insert(0, "Commands", "commands")
        excl_merged.to_excel(writer, sheet_name="MASTER", index=False)


        workbook = writer.book
        worksheet = writer.sheets["MASTER"]
        formato = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        titulo = workbook.add_format({'bg_color': '19b2e7'})
        format = workbook.add_format({'text_wrap': True})
        worksheet.conditional_format(0, 0, 0, worksheet.dim_colmax,
                                     {'criteria': ">", 'value': -1, 'type': 'cell', 'format': titulo})

        #print(len(excl_merged.axes[1]) - 1)
        worksheet.set_column(0, len(excl_merged.axes[1]) - 1, 70, format)









def run(ip):
    try:
        with multiprocessing.Pool(processes=20) as pool:
            #pool.map(main, ip)
            r = process_map(main, ips, max_workers=30)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(e)


def auto_width_columns(df, worksheet, formato):
    for s, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).str.len().max(), len(col) + 2)
        worksheet.set_column(s, s, column_len, formato)


def main(ip):
    out = []
    ssh = None
    tunnel = False


    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if "10" in ip:
            password = "cisco!123"
        else:
            password = "CXlabs.123"
        ssh.connect(ip, port, username, password, timeout=200,
                    allow_agent=False,
                    look_for_keys=False)
        time.sleep(2)
        tunnel = ssh.get_transport().is_alive()
    except paramiko.AuthenticationException as e:
        print(ip, e)
        with open(archivo + "-" + str(date_time) + ".txt", "a") as f:
            f.write(ip + ' No se conecta\n\n')

    if tunnel:
        #df = {'Command': commands}
        df = pd.DataFrame(columns=[ip])
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
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=200)
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
                            df.at[indice, ip] = f"Version: \nSystem {versiones[1]} Kickstart: {versiones[0]}"
                            #print("\n")

                        if "show vrf" in cmd:
                            if output.splitlines():
                                #print("*** VRF ***")
                                out.append("*** VRF ***")
                                for x in output.splitlines():
                                    lista = x.split()
                                    if lista:
                                        if lista[2] == "Down":
                                            cell.append(f"{lista[0]} State: {lista[2]} Reason: {' '.join(lista[3:])}")
                                            #print(f"VRF: {lista[0]} State: {lista[2]} Reason: {' '.join(lista[3:])}")
                                            out.append(
                                                f"VRF: {lista[0]} State: {lista[2]} Reason: {' '.join(lista[3:])}")
                                if out:
                                    df.at[indice, ip] = "VRF in Down State:\n" + '\n'.join(cell)
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
                                        cell.append(f"{lista[0]} State: {lista[-1]}")
                                        flag = False

                            if cell:
                                mensaje = "License Issues:"
                            else:
                                mensaje = "Pass"

                            df.at[indice, ip] = mensaje + "\n" + '\n'.join(cell)
                            #print("\n")

                        if "show module" in cmd:

                            #print("*** MODULE ***")
                            out.append("*** MODULE ***")
                            for x in output.splitlines():
                                if x:
                                    #print(x)
                                    out.append(x)
                                    cell.append(x)
                            df.at[indice, ip] = '\n'.join(cell)
                            #print("\n")

                        if "diagnostic" in cmd:
                            #print("*** DIAGNOSTIC ***")
                            #print(output)
                            out.append("*** DIAGNOSTIC ***")
                            out.append(output)
                            cell.append(output)
                            df.at[indice, ip] = '\n'.join(cell)
                            #print("\n")

                        if "show system internal mts" in cmd:
                            for x in output.split():
                                if int(x) > 99:
                                    #print("*** SYSTEM INTERNAL MTS ***")
                                    out.append("*** SYSTEM INTERNAL MTS ***")
                                    #print(x)
                                    out.append(x)
                                    cell.append(x)
                            if cell:
                                df.at[indice, ip] = '\n'.join(cell)
                            else:
                                df.at[indice, ip] = "Pass"
                            #print("\n")

                        if "show int desc" in cmd:
                            #print("*** SHOW INT [BRIEF-DESC] ***")
                            out.append("*** SHOW INT [BRIEF-DESC] ***")
                            #print(output)
                            out.append(output)
                            df.at[indice, ip] = output
                            #print("\n")

                        if "show port-channel summary" in cmd:
                            #print("*** PORT-CHANNEL SUMMARY ***")
                            #print(output)
                            out.append("*** PORT-CHANNEL SUMMARY ***")
                            out.append(output)
                            df.at[indice, ip] = output
                            #print("\n")

                        if "show vpc br" in cmd:
                            #print("*** VPC BRIEF ***")
                            out.append("*** VPC BRIEF ***")
                            #print(output)
                            out.append(output)
                            cell.append(output)
                            df.at[indice, ip] = output
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
                                    else:
                                        cell.append("Pass")
                            df.at[indice, ip] = '\n'.join(cell)
                            #print("\n")

                        if "show fex" in cmd:
                            #print("*** FEX ***")
                            out.append("*** FEX ***")
                            #print(" ".join(output.splitlines()))
                            out.append(" ".join(output.splitlines()))
                            df.at[indice, ip] = '\n'.join(output.splitlines())
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
                            df.at[indice, ip] = '\n'.join(cell)
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
                            df.at[indice, ip] = '\n'.join(cell)
                            #print("\n")
                    else:
                        df.at[indice, ip] = "Pass"

                else:
                    df.at[indice, ip] = "NOT ASSIGN"
                    with open("ERROR.txt", "a") as f:
                        f.write(ip + "# " + " " + cmd + " " + "\n")
            except Exception as e:
                print(e)
                df.at[indice, ip] = "Pass"
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

            writer.save()



if __name__ == '__main__':
    start = time.perf_counter()
    run(ips)
    combinar()
    finish = time.perf_counter()
    print('\nFinish ' + str(round(finish - start, 2)) + ' second(s)')
