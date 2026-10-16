// iCalcula instruction decoder, standalone RTL simulation prototype.
// No Vortex core integration, cryptographic SERS engine or fabricated silicon.
// 32-bit instruction: [31:24] opcode [23:16] ra [15:8] rb [7:0] reserved
// ADD 0x01, MUL 0x02, MAC 0x03, STAMP 0x10, RESET_ACC 0x11
module im_icalcula_decoder(
    input wire clk,
    input wire rst,
    input wire valid,
    input wire fault_inject,
    input wire [31:0] instruction,
    input wire signed [31:0] operand_a,
    input wire signed [31:0] operand_b,
    output reg ready,
    output reg fault,
    output reg signed [31:0] result,
    output reg signed [31:0] accumulator,
    output reg [31:0] state_tag,
    output reg stamp_valid
);
    localparam OP_NOP=8'h00, OP_ADD=8'h01, OP_MUL=8'h02,
               OP_MAC=8'h03, OP_STAMP=8'h10, OP_RESET=8'h11;
    reg signed [63:0] wide_result;
    always @(posedge clk) begin
        if (rst) begin
            ready<=0;
            fault<=0;
            result<=0;
            accumulator<=0;
            state_tag<=0;
            stamp_valid<=0;
            wide_result<=0;
        end else begin
            ready<=0;
            stamp_valid<=0;
            fault<=0;
            if (valid) begin
                if (fault_inject) begin
                    fault<=1;
                    ready<=1;
                end else begin
                    case(instruction[31:24])
                      OP_NOP: ready<=1;
                      OP_ADD: begin
                          wide_result=$signed(operand_a)+$signed(operand_b);
                          if (wide_result>64'sd2147483647 || wide_result<(-64'sd2147483647-1)) fault<=1;
                          else result<=wide_result[31:0];
                          ready<=1;
                      end
                      OP_MUL: begin
                          wide_result=$signed(operand_a)*$signed(operand_b);
                          if (wide_result>64'sd2147483647 || wide_result<(-64'sd2147483647-1)) fault<=1;
                          else result<=wide_result[31:0];
                          ready<=1;
                      end
                      OP_MAC: begin
                          wide_result=$signed(operand_a)*$signed(operand_b)+$signed(accumulator);
                          if (wide_result>64'sd2147483647 || wide_result<(-64'sd2147483647-1)) fault<=1;
                          else accumulator<=wide_result[31:0];
                          ready<=1;
                      end
                      OP_RESET: begin accumulator<=0;ready<=1;end
                      OP_STAMP: begin
                          // Noncryptographic *simulation* tag. NOT a receipt signature.
                          state_tag<=result ^ accumulator ^ operand_a ^ operand_b;
                          stamp_valid<=1;ready<=1;
                      end
                      default: begin fault<=1;ready<=1;end
                    endcase
                end
            end
        end
    end
endmodule
