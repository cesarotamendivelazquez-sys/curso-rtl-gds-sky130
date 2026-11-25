// =====================================================================
//  formal_top.v  ·  Envoltorio formal del semáforo (lab03, parte 4 · Gelatina)
//  Instancia TU semaforo y le pone la propiedad, SIN tocar el RTL.
//
//  - ped_req es una entrada LIBRE: el solver la mueve como quiera, en
//    cualquier ciclo (así prueba todas las formas de apretar el botón).
//  - Un reset en el primer ciclo, para arrancar desde un estado válido.
//  - Propiedad de seguridad: NUNCA hay dos luces encendidas a la vez
//    (la misma del checker del TB base y de cocotb, ahora como assert).
// =====================================================================
module formal_top (input wire clk, input wire rst_n, input wire ped_req);

    wire red, yellow, green;

    semaforo dut (
        .clk(clk), .rst_n(rst_n), .ped_req(ped_req),
        .red(red), .yellow(yellow), .green(green)
    );

    // arranque: reset activo el primer ciclo, luego corre normal
    reg f_started = 1'b0;
    always @(posedge clk) f_started <= 1'b1;
    always @(posedge clk) begin
        if (!f_started) assume (!rst_n);
        else            assume ( rst_n);
    end

    // propiedad: una sola luz encendida, siempre (fuera de reset)
    always @(posedge clk)
        if (f_started && rst_n)
            assert (red + yellow + green == 1);

endmodule
