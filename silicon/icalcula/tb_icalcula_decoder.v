`timescale 1ns/1ps
module tb;
 reg clk=0,rst=1,valid=0,fault_inject=0;
 reg [31:0] instruction=0;
 reg signed [31:0] a=0,b=0;
 wire ready,fault,stamp_valid;
 wire signed [31:0] result,accumulator;
 wire [31:0] state_tag;
 im_icalcula_decoder dut(.clk(clk),.rst(rst),.valid(valid),
  .fault_inject(fault_inject),.instruction(instruction),
  .operand_a(a),.operand_b(b),.ready(ready),.fault(fault),
  .result(result),.accumulator(accumulator),.state_tag(state_tag),
  .stamp_valid(stamp_valid));
 always #5 clk=~clk;
 task issue(input [7:0] op,input signed [31:0] x,input signed [31:0] y,
            input inject);
 begin
   @(negedge clk);
   instruction={op,24'h0};a=x;b=y;fault_inject=inject;valid=1;
   @(posedge clk); #1;
   if(!ready) $fatal(1,"Instruction did not complete");
   @(negedge clk);valid=0;fault_inject=0;
 end
 endtask
 initial begin
  repeat(2) @(negedge clk);rst=0;
  issue(8'h01,32'sd7,32'sd5,0);
  if(result!==32'sd12 || fault) $fatal(1,"ADD mismatch");
  issue(8'h02,32'sd6,32'sd7,0);
  if(result!==32'sd42 || fault) $fatal(1,"MUL mismatch");
  issue(8'h03,32'sd3,32'sd4,0);
  if(accumulator!==32'sd12 || fault) $fatal(1,"MAC mismatch");
  issue(8'h10,32'sd2,32'sd3,0);
  if(!stamp_valid || state_tag!==(32'd42^32'd12^32'd2^32'd3)) $fatal(1,"Tag mismatch");
  issue(8'h01,32'sh7fffffff,32'sd1,0);
  if(!fault || result!==32'sd42) $fatal(1,"Overflow not trapped");
  issue(8'h02,32'sd4,32'sd5,1);
  if(!fault || result!==32'sd42) $fatal(1,"Fault injection failed");
  issue(8'hFF,0,0,0);
  if(!fault) $fatal(1,"Unknown opcode allowed");
  issue(8'h11,0,0,0);
  if(accumulator!==0) $fatal(1,"RESET failed");
  $display("iCalcula RTL TEST PASS: ADD/MUL/MAC/STAMP/overflow/fault/reset");
  $finish;
 end
 initial begin #10000; $fatal(1,"Testbench timeout");end
endmodule
