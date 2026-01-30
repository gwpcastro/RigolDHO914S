import pyvisa
import numpy as np
import matplotlib.pyplot as plt
from utils import *
from bode_plot import *

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
print(resources)



folder = "dados_x"
# Frequências logarítmicas
f_inicial, f_final = 42,85
f_base = np.logspace(np.log10(f_inicial), np.log10(f_final), num=400) #500 parece overgflow, 400 parece razoável
ganhos_db = []
fases_deg = []
ajuste1 = True
ajuste2 = True
first =True

ganhos_db = []
fases_deg = []
frequencias = []


# Ativa modo interativo
plt.ion()
fig, (ax_gain, ax_phase) = plt.subplots(2, 1, figsize=(10, 6))
line_gain, = ax_gain.plot([], [], 'o-', label='Ganho (dB)')
line_phase, = ax_phase.plot([], [], 'o-', label='Fase (°)')

ax_gain.set_ylabel("Ganho (dB)")
ax_phase.set_ylabel("Fase (°)")
ax_phase.set_xlabel("Frequência (Hz)")
ax_gain.set_xscale("log")
ax_phase.set_xscale("log")
ax_gain.grid(True, which="both", ls='--')
ax_phase.grid(True, which="both", ls='--')
ax_gain.legend()
ax_phase.legend()
# Eixo X: Frequência (log)
ax_gain.set_xlim(f_inicial, f_final)
ax_phase.set_xlim(f_inicial, f_final)
ax_gain.set_ylim(-70, 5)
ax_phase.set_ylim(-180,180) 


try:
    if not resources:
        raise Exception("Nenhum dispositivo encontrado.")
    
    # Usa o primeiro recurso da lista
    inst = rm.open_resource(resources[0])
    print("Identificação:", inst.query("*IDN?"))

    for i, f in enumerate(f_base, start=1):
        if first:
            first = False
            inst.write(":RUN")
            inst.write(":AUT")
            time.sleep(1)
        set_afg(inst=inst, freq=f, tipo="SIN", vpp=5.0, offset=2.5)
        period = 1 / f

        time_scale = period * 8  # 8 ciclos por tela (10 divs)]
        inst.write(f":TIM:SCAL {time_scale/10:.6e}")
        time.sleep(1)
        
        df = read_and_save_dual_channel(inst=inst, freq=f, coleta_num=i, folder=folder)
        tempo = arredondar_por_ordem(df["Tempo_CHAN1"].values, casas=5)
        sinal_in = arredondar_por_ordem(df["Tensão_CHAN1"].values, casas=5)
        sinal_out = arredondar_por_ordem(df["Tensão_CHAN2"].values, casas=5)
        dt = np.mean(np.diff(tempo))
        fs = 1 / dt
        ganho, fase = calcular_fft(tempo, sinal_in, sinal_out, f)
        print("Ganho:\n", ganho)
        print("Fase:\n", fase)

        ganho_db = 20 * np.log10(ganho)
        frequencias.append(f)
        ganhos_db.append(ganho_db)
        fases_deg.append(fase)

        # Atualiza os dados no gráfico
        line_gain.set_data(frequencias, ganhos_db)
        line_phase.set_data(frequencias, fases_deg)
        plt.pause(0.01)  # Tempo de atualização


    inst.close()
    plt.ioff()
    plt.show()

except Exception as e:
    print("Erro:", e)





