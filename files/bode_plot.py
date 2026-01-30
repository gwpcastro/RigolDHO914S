import os
import numpy as np
import matplotlib.pyplot as plt
import re
import pandas as pd
from monte_carlo_simulation_low_pass import *
from scipy.signal import butter, filtfilt
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt
from fxpmath import Fxp

folder = "dados_x"

def filtro_passabanda(y, freq, fs, largura_relativa=0.1, ordem=1):
    """
    Filtra o sinal y com um filtro passa-banda Butterworth centrado em 'freq'.

    Parâmetros:
        y: sinal a ser filtrado
        freq: frequência central (Hz)
        fs: taxa de amostragem (Hz)
        largura_relativa: largura relativa da banda (ex: 0.05 → ±5%)
        ordem: ordem do filtro (quanto maior, mais seletivo)

    Retorna:
        sinal filtrado
    """
    nyq = fs / 2
    largura = largura_relativa * freq
    low = (freq - largura) / nyq
    high = (freq + largura) / nyq

    if low <= 0:
        low = 1e-6  # Evita erro

    b, a = butter(ordem, [low, high], btype='band')
    return filtfilt(b, a, y)

def arredondar_por_ordem(x, casas=4):
    x = np.asarray(x)
    potencias = np.floor(np.log10(np.abs(x) + 1e-20))  # evitar log(0)
    escalado = x / (10 ** potencias)
    arredondado = np.round(escalado, casas)
    return arredondado * (10 ** potencias)

def demodular(t,x, y, freq):
    """
    x: sinal de entrada (CHAN1)
    y: sinal de saída (CHAN2)
    freq: frequência do sinal (Hz)
    """
    # t = np.linspace(0, len(x) / freq, len(x), endpoint=False)

    cosseno = np.cos(2 * np.pi * freq * t)
    seno = -np.sin(2 * np.pi * freq * t)
    referencia = cosseno + 1j * seno

    z = y * referencia

    # Média para remover harmônicos e ruído
    z_mean = np.mean(z)


    Z = 2 * np.mean(z)  # demodulação coerente
    A = 2 * np.mean(x * cosseno)  # amplitude entrada

    ganho = abs(Z) / A
    fase = np.angle(Z, deg=True)


    # Cálculo de ganho e fase
    ganho = 2 * np.abs(z_mean) / A
    fase_rad = np.angle(z_mean)
    fase_deg = np.rad2deg(fase_rad)


    return ganho, fase_deg

def demodular(t, x, y, freq):
    referencia = np.exp(-1j * 2 * np.pi * freq * t)
    z = y * referencia
    Z = 2 * np.mean(z)
    A = 2 * np.mean(x * np.cos(2 * np.pi * freq * t))
    ganho = np.abs(Z) / A
    fase_deg = np.angle(Z, deg=True)
    return ganho, fase_deg

def demodulacao_coerente(t, x, y, freq):
    dt = np.mean(np.diff(t))
    
    # Referência senoidal
    ref_cos = np.cos(2 * np.pi * freq * t)
    ref_sin = np.sin(2 * np.pi * freq * t)

    # Normalização
    norm = 2 / len(t)

    # Produto interno entre sinais e referências
    X_cos = np.sum(x * ref_cos) * norm
    X_sin = np.sum(x * ref_sin) * norm
    Y_cos = np.sum(y * ref_cos) * norm
    Y_sin = np.sum(y * ref_sin) * norm

    # Sinais complexos
    Xf = X_cos - 1j * X_sin
    Yf = Y_cos - 1j * Y_sin

    ganho = np.abs(Yf) / np.abs(Xf)
    fase = np.angle(Yf / Xf, deg=True)

    return ganho, fase


def calcular_fft(t, x, y, freq):
    dt = np.mean(np.diff(t))
    fs = 1 / dt  # taxa de amostragem

    N = len(t)
    X = np.fft.fft(x * np.hanning(N))
    Y = np.fft.fft(y * np.hanning(N))
    freqs = np.fft.fftfreq(N, d=dt)

    # encontra índice mais próximo da frequência de interesse
    idx = np.argmin(np.abs(freqs - freq))

    Xf = X[idx]
    Yf = Y[idx]

    ganho = np.abs(Yf) / np.abs(Xf)
    fase = np.angle(Yf / Xf, deg=True)

    return ganho, fase

if __name__ == '__main__':
    folder = folder
    frequencias = []
    ganhos_db = []
    fases_deg = []

    for nome in os.listdir(folder):
        if not nome.endswith(".csv"):
            continue

        caminho = os.path.join(folder, nome)
        match = re.search(r"freq_(\d+)Hz", nome)
        if not match:
            continue

        freq = int(match.group(1))
        df = pd.read_csv(caminho)

        # tempo = df["Tempo_CHAN1"].values
        # sinal_in = df["Tensão_CHAN1"].values
        # sinal_out = df["Tensão_CHAN2"].values

        tempo = arredondar_por_ordem(df["Tempo_CHAN1"].values, casas=5)
        sinal_in = arredondar_por_ordem(df["Tensão_CHAN1"].values, casas=5)
        sinal_out = arredondar_por_ordem(df["Tensão_CHAN2"].values, casas=5)
    

        # ganho, fase = demodular(tempo,sinal_in, sinal_out, freq)
        # ganho_db = 20 * np.log10(ganho)
        dt = np.mean(np.diff(tempo))
        fs = 1 / dt

        # sinal_filtrado = filtro_passabanda(y=sinal_out, freq=freq, fs=fs)

        # FFT ou demodulação coerente usa sinal_filtrado
        # ganho, fase = demodulacao_coerente(tempo, sinal_in, sinal_filtrado, freq)

        ganho, fase = calcular_fft(tempo, sinal_in, sinal_out, freq)
        # ganho, fase = demodulacao_coerente(tempo, sinal_in, sinal_out, freq)

        ganho_db = 20 * np.log10(ganho)

        frequencias.append(freq)
        ganhos_db.append(ganho_db)
        fases_deg.append(fase)

    # Ordenar por frequência
    ordem = np.argsort(frequencias)
    frequencias = np.array(frequencias)[ordem]
    ganhos_db = np.array(ganhos_db)[ordem]
    fases_deg = np.array(fases_deg)[ordem]

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    max_db = max(ganhos_db)
    min_db = min(ganhos_db)
    ax1.semilogx(frequencias, ganhos_db, 'x-', markersize =4)
    ax1.set_ylabel("Ganho (dB)", fontsize = 25)
    ax1.grid(True, which="both", ls="--")
    ax1.set_ylim(min_db - 0.1*(max_db-min_db), max_db + 0.1*(max_db-min_db))
    # Linha vertical em 17 kHz
    ax1.axvline(18.2e3, color='red', linestyle='--', linewidth=1)
    ax1.text(18.2e3, ax1.get_ylim()[1], "18.4 kHz", color='red', fontsize=8,
             ha='right', va='top', rotation=90)
    ax1.tick_params(direction='in', which = 'both',width = 1.1,length =4,labelsize=14)

    max_ph= max(fases_deg)
    min_ph = min(fases_deg)
    ax2.semilogx(frequencias, fases_deg, 'x-', color='orange', markersize =4)
    ax2.set_xlabel("Frequência (Hz)", fontsize =25)
    ax2.set_ylabel("Fase (graus)", fontsize =25)
    ax2.set_ylim(min_ph - 0.1*(max_ph-min_ph), max_ph + 0.1*(max_ph-min_ph))
    ax2.grid(True, which="both", ls="--")

    # Linha vertical em 17 kHz também no gráfico de fase
    ax2.axvline(18.2e3, color='red', linestyle='--', linewidth=1)
    ax2.text(18.2e3, ax2.get_ylim()[1], "18.4 kHz", color='red', fontsize=8,
             ha='right', va='top', rotation=90)
    ax2.tick_params(direction='in', which = 'both',width = 1.1,length =4,labelsize=14)


    plt.suptitle("Diagramas de Bode - Computador Pessoal",fontsize = 50 )    
    plt.tight_layout()
    plt.show()


    # ---------------------------
    #       Plot unificado
    # ---------------------------

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    # Ganho
    ax1.fill_between(f_sim, gain_min, gain_max, color='lightblue', alpha=0.5, label='Banda 95% Monte Carlo')
    ax1.semilogx(f_sim, gain_median, 'b-', label='Mediana Monte Carlo')
    ax1.semilogx(frequencias, ganhos_db, 'ko', label='Experimental')
    ax1.set_ylabel("Ganho (dB)")
    ax1.set_ylim(-60, 5)
    ax1.grid(True, which="both", ls="--")
    ax1.legend()

    # Fase
    ax2.fill_between(f_sim, phase_min, phase_max, color='lightcoral', alpha=0.5, label='Banda 95% Monte Carlo')
    ax2.semilogx(f_sim, phase_median, 'r-', label='Mediana Monte Carlo')
    ax2.semilogx(frequencias, fases_deg, 'ko', label='Experimental')
    ax2.set_ylabel("Fase (graus)")
    ax2.set_xlabel("Frequência (Hz)")
    ax2.set_ylim(-120, 10)
    ax2.grid(True, which="both", ls="--")
    ax2.legend()

    plt.suptitle("Diagrama de Bode: Medidas Experimentais vs Simulação Monte Carlo")
    plt.tight_layout()
    plt.show()



    def modelo_bode_1ordem(f, fc):
        return 20 * np.log10(1 / np.sqrt(1 + (f / fc)**2))


    # Ajuste do modelo ao ganho experimental (em dB)
    popt, pcov = curve_fit(modelo_bode_1ordem, frequencias, ganhos_db, p0=[1e3], bounds=(10, 1e10))
    fc_estimado = popt[0]

    # Curva ajustada
    frequencias_fit = np.logspace(np.log10(min(frequencias)), np.log10(max(frequencias)), 500)
    ganho_fit = modelo_bode_1ordem(frequencias_fit, fc_estimado)


