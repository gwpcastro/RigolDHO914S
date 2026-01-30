import numpy as np
import matplotlib.pyplot as plt
import pyvisa   
import pandas as pd
import time
import os

folder = "dados_x           "

def set_afg(inst, tipo="SIN", freq=1000, vpp=5, offset=0.0,phase=0,  enable=True):
    inst.write_termination = '\n'
    inst.read_termination = '\n'

    # Ordem correta para evitar erro remoto
    inst.write(f":SOUR:FUNC {tipo}")           # Sempre primeiro
    # inst.write(f":SOUR:OUTP:STAT OFF")         # Desliga antes de configurar
    # inst.write(":SOUR:LOAD INF")               # Evita divisão por 2
    inst.write(f":SOUR:FREQ {freq}")
    inst.write(f":SOUR:VOLT:AMPL {vpp}")
    inst.write(f":SOUR:VOLT:OFFS {offset}")
    inst.write(f":SOUR:PHAS {phase}")
    # inst.write(f":SOUR:OUTP:STAT {'ON' if enable else 'OFF'}")
    inst.write(":RUN")


    print("AFG configurado para:", tipo)
    print(f"Freq: {freq:.2f} Hz — Vpp: {vpp} V — Offset: {offset} V")
    print("Saída ativa:", inst.query(":SOUR:OUTP:STAT?").strip())

def read_and_plot(inst):
    inst.write_termination = '\n'
    inst.read_termination = '\n'
    inst.timeout = 10000

    print("IDN:", inst.query("*IDN?"))

    inst.write(":STOP")  # Para aquisição para evitar dados inconsistentes
    inst.write(":WAV:SOUR CHAN1")
    inst.write(":WAV:MODE NORM")
    inst.write(":WAV:FORM BYTE")
    inst.write(":WAV:POINTS 1000")
    time.sleep(0.5)
    print("erro")
    yinc = inst.query(":WAV:YINC?")
    print(yinc)
    yinc = float(yinc)
    print("depoois erro")
    yoff = 0

    yorig = float(inst.query(":WAV:YOR?"))
    xinc = float(inst.query(":WAV:XINC?"))
    xorig = float(inst.query(":WAV:XOR?"))




    inst.write(":WAV:DATA?")
    try:
        raw = inst.read_raw()
    except pyvisa.VisaIOError as e:
        print("Erro de leitura:", e)
        return

    if raw[0:1] == b'#':
        header_len = int(raw[1:2])
        data_start = 2 + header_len
        data = raw[data_start:]
    else:
        data = raw

    samples = np.frombuffer(data, dtype=np.uint8)
    voltages = (samples - yoff) * yinc
    voltages = voltages - np.mean(voltages)
    times = np.arange(len(voltages)) * xinc + xorig

    # Salva CSV usando pandas
    df = pd.DataFrame({
        "Tempo (s)": times,
        "Tensão (V)": voltages
    })
    df.to_csv("onda2_CH1_pandas.csv", index=False)

    plt.plot(times[:-2], voltages[:-2])
    plt.xlabel("Tempo [s]")
    plt.ylabel("Tensão [V]")
    plt.title("Canal 1 - Rigol DHO914S")
    plt.grid(True)
    plt.show()

    # set_afg(inst=inst)
    time.sleep(10)
    inst.write("*RST")



def read_waveform(inst, canal="CHAN1"):
    inst.write(f":WAV:SOUR {canal}")
    inst.write(":WAV:MODE NORM")
    inst.write(":WAV:FORM BYTE")
    inst.write(":WAV:POINTS 1000")

    yinc = float(inst.query(":WAV:YINC?"))
    yoff = 0
    yorig = float(inst.query(":WAV:YOR?"))
    xinc = float(inst.query(":WAV:XINC?"))
    xorig = float(inst.query(":WAV:XOR?"))

    inst.write(":WAV:DATA?")
    raw = inst.read_raw()
    if raw[0:1] == b'#':
        header_len = int(raw[1:2])
        data_start = 2 + header_len
        data = raw[data_start:]
    else:
        data = raw

    samples = np.frombuffer(data, dtype=np.uint8)
    voltages = (samples - yoff) * yinc
    voltages -= np.mean(voltages)
    times = np.arange(len(voltages)) * xinc + xorig

    return times, voltages


def read_dual_channel(inst, f, A=1.0):
    inst.write(":STOP")
    inst.write(":WAV:MODE NORM")
    inst.write(":WAV:FORM BYTE")
    inst.write(":WAV:POINTS 1000")

    canais = {}
    for ch in [1, 2]:
        inst.write(f":WAV:SOUR CHAN{ch}")
        yinc = float(inst.query(":WAV:YINC?"))
        yorig = float(inst.query(":WAV:YOR?"))
        xinc = float(inst.query(":WAV:XINC?"))
        xorig = float(inst.query(":WAV:XOR?"))

        inst.write(":WAV:DATA?")
        raw = inst.read_raw()
        if raw[0:1] == b'#':
            header_len = int(raw[1:2])
            data_start = 2 + header_len
            data = raw[data_start:]
        else:
            data = raw

        samples = np.frombuffer(data, dtype=np.uint8)
        voltages = (samples - yorig) * yinc
        voltages = voltages - np.mean(voltages)
        times = np.arange(len(voltages)) * xinc + xorig
        canais[ch] = voltages

    # Demodulação coerente
    u = canais[1]
    y = canais[2]
    t = times
    ref = np.exp(-1j * 2 * np.pi * f * t)
    z = y * ref
    z_medio = np.mean(z)

    ganho = 2 * np.abs(z_medio) / A
    fase_rad = np.angle(z_medio)
    fase_deg = np.rad2deg(fase_rad)
    ganho_db = 20 * np.log10(ganho)

    return ganho_db, fase_deg


def read_and_save_dual_channel(inst, freq, coleta_num=1, folder=folder):
    """
    Lê os canais CHAN1 e CHAN2 do osciloscópio Rigol e salva em CSV.

    Parâmetros:
    - inst: objeto PyVISA do osciloscópio
    - freq: frequência atual (para nomear o arquivo)
    - coleta_num: número sequencial da coleta
    - folder: pasta onde salvar os arquivos CSV
    """
    time.sleep(1)
    inst.write_termination = '\n'
    inst.read_termination = '\n'
    inst.timeout = 10000

    inst.write(":STOP")  # Para aquisição

    canais = ["CHAN1", "CHAN2"]
    dados = {}

    for canal in canais:
        inst.write(f":WAV:SOUR {canal}")
        inst.write(":WAV:MODE NORM")
        inst.write(":WAV:FORM BYTE")
        inst.write(":WAV:POINTS 1000")

        yinc = float(inst.query(":WAV:YINC?"))
        yoff = 0  # Assume zero
        yorig = float(inst.query(":WAV:YOR?"))
        xinc = float(inst.query(":WAV:XINC?"))
        xorig = float(inst.query(":WAV:XOR?"))

        inst.write(":WAV:DATA?")
        try:
            raw = inst.read_raw()
        except Exception as e:
            print(f"Erro ao ler {canal}: {e}")
            return

        if raw[0:1] == b'#':
            header_len = int(raw[1:2])
            data_start = 2 + header_len
            data = raw[data_start:]
        else:
            data = raw

        samples = np.frombuffer(data, dtype=np.uint8)
        voltages = (samples - yoff) * yinc
        voltages = voltages - np.mean(voltages)  # Remove offset DC
        times = np.arange(len(voltages)) * xinc + xorig

        dados[f"Tempo_{canal}"] = times[:-2]
        dados[f"Tensão_{canal}"] = voltages[:-2]




    # Cria a pasta se não existir
    os.makedirs(folder, exist_ok=True)
    nome_arquivo = f"{folder}/coleta_{coleta_num}_freq_{int(freq)}Hz.csv"

    df = pd.DataFrame(dados)
    df.to_csv(nome_arquivo, index=False)

    print(f"Salvo: {nome_arquivo}")
    return df

def ajustar_escala_vertical(inst, canal="CHAN2"):
    inst.write(":STOP")
    inst.write(f":{canal}:DISP ON")
    inst.write(f":{canal}:PROB 1")  # sonda 1X para escala correta

    inst.write(f":WAV:SOUR {canal}")
    inst.write(":WAV:MODE NORM")
    inst.write(":WAV:FORM BYTE")
    inst.write(":WAV:POINTS 500")

    yinc = float(inst.query(":WAV:YINC?"))
    yorig = float(inst.query(":WAV:YOR?"))

    inst.write(":WAV:DATA?")
    raw = inst.read_raw()
    if raw[0:1] == b'#':
        header_len = int(raw[1:2])
        data_start = 2 + header_len
        data = raw[data_start:]
    else:
        data = raw

    samples = np.frombuffer(data, dtype=np.uint8)
    voltages = samples * yinc + yorig

    vpp = np.max(voltages) - np.min(voltages)
    nivel_medio = np.mean(voltages)

    if vpp < 1e-3:
        vpp = 1e-3

    margem = 0.5
    vdiv = vpp / (8 * margem)

    # Limita o valor dentro do intervalo aceito
    vdiv = max(0.0002, min(vdiv, 10))

    inst.write(f":{canal}:SCAL {vdiv:.6e}")
    inst.write(f":{canal}:OFFS {nivel_medio:.6f}")
    inst.write(f":{canal}:POS 0")
    inst.write(":RUN")

    real_scale = inst.query(f":{canal}:SCAL?")
    print(f"Escala aplicada no {canal}: {real_scale.strip()}")
    print(f"Offset aplicado no {canal}: {nivel_medio:.6f}")

