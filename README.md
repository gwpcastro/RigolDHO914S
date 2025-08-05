# RigolDHO914S
This repository aims to describe and implement Standard Commands for Programmable Instruments (SCPI) communication over the Universal Serial Bus (USB) with the Rigol DHO914S oscilloscope to acquire low-noise, high-resolution Bode diagrams for the analysis of signals and systems.

![Rigol DHO914S](images/rigol.webp)

The Rigol DHO914S is a 12-bit digital oscilloscope with a maximum analog bandwidth of 125 MHz and four analog input channels. It features a real-time sampling rate of up to 1.25 GSa/s and a memory depth of 50 Mpts. The device integrates several advanced functions, including an arbitrary function generator (AFG), Bode plot analysis, histogram measurements, digital signal analysis, and more.

One of the problems encountered was related to the Bode plot diagram. The oscilloscope itself includes a built-in Bode plot function. However, when analyzing the plotted results, small undulations — resembling ripples or fringes — were observed in both the gain (dB) and the phase (°) curves.

![Bode fringes](images/Bode_fringe.png)
