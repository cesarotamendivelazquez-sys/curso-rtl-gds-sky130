# Notas del PDK · Lab01

**Nombre: C. Ander Velazquez** 
**PDK_ROOT que usé:** 
**Versión del PDK (hash de `ciel ls`):** 

## 1. Tres celdas por dentro

Llena la tabla con `./pdk_info.sh <celda>` (o `make celda CELDA=<celda>`).
La tercera celda la eliges tú.

| Celda | Área (µm²) | Ancho × Alto (µm) | Sitios unithd | Pines de señal |
| --- | --- | --- | --- | --- |
| sky130_fd_sc_hd__nand2_1 |  |  |  |  |
| sky130_fd_sc_hd__dfrtp_1 |  |  |  |  |
| (elige una) |  |  |  |  |

## 2. Corners disponibles

Uno por renglón, como aparecen en el nombre del `.lib` (por ejemplo `tt_025C_1v80`).

- 

## 3. Preguntas

1. ¿Por qué todas las celdas tienen el mismo alto?
   - 
2. Para revisar **setup** (que el reloj alcance), ¿qué corner usarías? ¿Y para **hold**? ¿Por qué?
   - 
3. El `dfrtp_1` es el flip-flop que usará el semáforo. ¿Cuántas `nand2_1` caben en su área?
   - 
