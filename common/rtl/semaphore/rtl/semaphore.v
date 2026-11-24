`timescale 1ns / 1ps
// El archivo se llama semaphore.v por compatibilidad con el repo del evento;
// el módulo se llama semaforo. Excepción de lint revisada y aceptada:
/* verilator lint_off DECLFILENAME */
// =====================================================================
//  semaphore.v  ·  Ejemplo guía "Galletas y Postres: el camino de chips"
//  Cápsula 2 (Churros / RTL). Este MISMO archivo alimenta los dos flujos:
//    - Open source : Yosys, Icarus, OpenROAD...
//    - Comercial   : Synopsys Design Compiler / Siemens Questa...
//  y también la implementación en la MinyPLD (MAX V) vía Quartus.
//
//  Semáforo de 3 estados (verde -> amarillo -> rojo -> verde) tipo Moore.
//  RTL puro y sintetizable: describe el QUÉ, no el CÓMO.
// =====================================================================
module semaforo #(
    parameter integer T_GREEN  = 5,   // ticks en verde
    parameter integer T_YELLOW = 2,   // ticks en amarillo
    parameter integer T_RED    = 5,   // ticks en rojo
    parameter integer CW       = 8    // ancho del contador (ojo: MinyPLD = 80 LE)
)(
    input  wire clk,
    input  wire rst_n,                // reset asíncrono, activo en bajo
    input  wire ped_req,              // botón peatonal, activo en alto
    output reg  red,
    output reg  yellow,
    output reg  green
);

    // ---- Codificación de estados --------------------------------------
    localparam [1:0] S_GREEN  = 2'd0,
                     S_YELLOW = 2'd1,
                     S_RED    = 2'd2;

    reg [1:0]    state, next_state;
    reg [CW-1:0] cnt;                 // cuánto llevamos en el estado actual
    reg [CW-1:0] limit;               // cuántos ticks dura el estado actual

    // ---- ¿Cuánto dura el estado actual? -------------------------------
    //  (de cada parámetro se toman solo los CW bits de abajo)
    always @(*) begin
        case (state)
            S_GREEN:  limit = T_GREEN[CW-1:0];
            S_YELLOW: limit = T_YELLOW[CW-1:0];
            S_RED:    limit = T_RED[CW-1:0];
            default:  limit = T_RED[CW-1:0];
        endcase
    end

    // ---- Lógica de siguiente estado (el anillo) -----------------------
    always @(*) begin
        case (state)
            S_GREEN:  next_state = S_YELLOW;
            S_YELLOW: next_state = S_RED;
            S_RED:    next_state = S_GREEN;
            default:  next_state = S_GREEN;
        endcase
    end

    // ---- Registro de estado + contador --------------------------------
    //  Se avanza si se acabó el tiempo, o si piden paso estando en verde.
    wire avanza = (cnt == limit - 1'b1) || (state == S_GREEN && ped_req);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_GREEN;
            cnt   <= {CW{1'b0}};
        end else if (avanza) begin
            state <= next_state;      // avanza al siguiente color
            cnt   <= {CW{1'b0}};
        end else begin
            cnt   <= cnt + 1'b1;      // sigue contando
        end
    end

    // ---- Salidas (Moore: dependen solo del estado) --------------------
    always @(*) begin
        red = 1'b0; yellow = 1'b0; green = 1'b0;
        case (state)
            S_GREEN:  green  = 1'b1;
            S_YELLOW: yellow = 1'b1;
            S_RED:    red    = 1'b1;
            default:  red    = 1'b1;
        endcase
    end

endmodule
