// =====================================================================
//  tb_ped_req.v  ·  Revisor del lab02: el botón peatonal (ped_req)
//  NO LO MODIFIQUES: make entrega revisa que esté igual que en el curso.
//
//  Especificación que revisa:
//    - Sin botón, el semáforo hace verde -> amarillo -> rojo como siempre.
//    - Si ped_req = 1 en un flanco de reloj estando en VERDE, en ese
//      mismo flanco pasa a AMARILLO (lo ves en el siguiente tick).
//    - En amarillo y en rojo, ped_req se ignora.
//
//  Cómo revisa: un modelo de referencia corre junto al diseño y en cada
//  ciclo se comparan las luces. Si difieren, dice en qué caso y cuándo.
// =====================================================================
`timescale 1ns/1ps
module tb_ped_req;

    // Tiempos distintos a los del TB base (y al default del RTL) a propósito.
    localparam integer TG = 6, TY = 2, TR = 4;

    reg  clk = 1'b0, rst_n = 1'b0, ped_req = 1'b0;
    wire red, yellow, green;

    semaforo #(.T_GREEN(TG), .T_YELLOW(TY), .T_RED(TR), .CW(8)) dut (
        .clk(clk), .rst_n(rst_n), .ped_req(ped_req),
        .red(red), .yellow(yellow), .green(green)
    );

    always #10 clk = ~clk;                       // 20 ns, como el SDC

    // ---- Modelo de referencia ------------------------------------------
    localparam [1:0] V = 2'd0, A = 2'd1, R = 2'd2;
    reg [1:0] m_st;
    integer   m_cnt;

    function integer dura(input [1:0] s);
        case (s)
            V:       dura = TG;
            A:       dura = TY;
            default: dura = TR;
        endcase
    endfunction

    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin
            m_st <= V; m_cnt <= 0;
        end else if (m_cnt == dura(m_st) - 1 || (m_st == V && ped_req)) begin
            m_st <= (m_st == R) ? V : m_st + 2'd1;  m_cnt <= 0;
        end else
            m_cnt <= m_cnt + 1;

    function [8*8-1:0] nombre(input [2:0] ryg);
        case (ryg)
            3'b100:  nombre = "rojo";
            3'b010:  nombre = "amarillo";
            3'b001:  nombre = "verde";
            default: nombre = "invalido";
        endcase
    endfunction

    wire [2:0] esperado = (m_st == V) ? 3'b001 : (m_st == A) ? 3'b010 : 3'b100;

    // ---- Comparación en cada flanco de bajada ----------------------------
    reg [8*28-1:0] caso = "arranque";
    integer err_caso = 0, err_total = 0, casos = 0, casos_mal = 0;

    always @(negedge clk) if (rst_n) begin
        if ({red, yellow, green} !== esperado) begin
            if (err_caso < 3)
                $display("    [%0d ns] %0s: esperaba %0s y salio %0s (r=%b a=%b v=%b, ped_req=%b)",
                         $time, caso, nombre(esperado), nombre({red, yellow, green}),
                         red, yellow, green, ped_req);
            err_caso  = err_caso + 1;
            err_total = err_total + 1;
        end
    end

    task cierra;
        begin
            if (casos > 0) begin
                if (err_caso == 0) $display("  [ OK ] %0s", caso);
                else begin
                    $display("  [MAL ] %0s (%0d ciclos distintos al modelo)", caso, err_caso);
                    casos_mal = casos_mal + 1;
                end
            end
        end
    endtask

    // Cada caso arranca de cero (reset a diseño y modelo): un error en un
    // caso no contamina a los siguientes.
    task empieza(input [8*28-1:0] n);
        begin
            cierra;
            @(negedge clk); #2 rst_n = 1'b0; #4 rst_n = 1'b1;
            caso = n; err_caso = 0; casos = casos + 1;
        end
    endtask

    task ticks(input integer n);
        begin repeat (n) @(negedge clk); end
    endtask

    // Un pulso de 1 ciclo, de flanco de bajada a flanco de bajada.
    task pulso;
        begin ped_req = 1'b1; @(negedge clk); ped_req = 1'b0; end
    endtask

    // Espera (en flanco de bajada) a que el modelo esté en el estado s con cnt = c.
    task espera(input [1:0] s, input integer c);
        begin
            @(negedge clk);
            while (!(m_st == s && m_cnt == c)) @(negedge clk);
        end
    endtask

    initial begin
        $display("== tb_ped_req: verde %0d, amarillo %0d, rojo %0d ticks ==", TG, TY, TR);
        #25 rst_n = 1'b1;

        empieza("sin boton (2 vueltas)");       ticks(2 * (TG + TY + TR));
        empieza("boton al inicio del verde");   espera(V, 1);      pulso; ticks(TY + TR + 2);
        empieza("boton al final del verde");    espera(V, TG - 2); pulso; ticks(TY + TR + 2);
        empieza("boton en amarillo (ignorar)"); espera(A, 0);      pulso; ticks(TY + TR + 2);
        empieza("boton en rojo (ignorar)");     espera(R, 1);      pulso; ticks(TR + 2);
        empieza("boton sostenido");             ped_req = 1'b1;    ticks(3 * (TY + TR + 1)); ped_req = 1'b0;
        empieza("reset en medio del verde");    espera(V, 2);      #3 rst_n = 1'b0; #40 rst_n = 1'b1; ticks(TG + 2);
        empieza("boton al azar (300 ticks)");
        repeat (300) begin ped_req = ($random % 4 == 0); @(negedge clk); end
        ped_req = 1'b0;
        cierra;

        if (err_total == 0)
            $display(">>> PASS: ped_req cumple (%0d casos)", casos);
        else
            $display(">>> FAIL: %0d de %0d casos con diferencias", casos_mal, casos);
        $finish;
    end

    initial begin #200000; $display(">>> FAIL: tiempo agotado"); $finish; end

endmodule
