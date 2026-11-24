# =====================================================================
#  semaforo.sdc  ·  Restricciones únicas del curso RTL → GDSII
#  El MISMO archivo viaja a síntesis (lab04), PnR (lab05) y STA (lab06).
#
#  Reloj: 20 ns (50 MHz). A este periodo el semáforo firma limpio en los
#  tres corners (tt/ss/ff). En el lab06 se baja a 10, 2 y 1 ns para
#  "romper el timing" y encontrar la fmax.
# =====================================================================

set CLK_PERIOD 20.0
set IO_DELAY   4.0   ;# 20 % del periodo para lo que pasa fuera del chip

create_clock -name clk -period $CLK_PERIOD [get_ports clk]

# El reset es asíncrono: no se analiza como ruta de datos.
set_false_path -from [get_ports rst_n]

# Entradas de datos (el lab02 agrega ped_req: descomenta la línea).
set_input_delay $IO_DELAY -clock clk [get_ports ped_req]

# Salidas: las luces.
set_output_delay $IO_DELAY -clock clk [get_ports {red yellow green}]
