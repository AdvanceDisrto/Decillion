library ieee;
use ieee.std_logic_1164.all;
entity tb_iswh_mesh_gate is end;
architecture sim of tb_iswh_mesh_gate is
 signal clk:std_logic:='0';
 signal reset,packet_ready,link_healthy,identity_valid,policy_allow:std_logic:='0';
 signal rx_data,tx_data:std_logic_vector(63 downto 0):=(others=>'0');
 signal tx_valid,network_isolate:std_logic;
begin
 clk<=not clk after 5 ns;
 dut:entity work.iswh_mesh_gate port map(clk,reset,packet_ready,link_healthy,identity_valid,policy_allow,rx_data,tx_data,tx_valid,network_isolate);
 process
 begin
  reset<='1';wait until rising_edge(clk);wait for 1 ns;
  assert network_isolate='1' and tx_valid='0' report "reset must isolate" severity failure;
  reset<='0';link_healthy<='1';identity_valid<='1';policy_allow<='1';packet_ready<='1';rx_data<=x"0123456789ABCDEF";
  wait until rising_edge(clk);wait for 1 ns;
  assert tx_valid='0' report "no transmission before ready" severity failure;
  wait until rising_edge(clk);wait for 1 ns;
  assert tx_valid='1' and tx_data=x"0123456789ABCDEF" report "authorized data transfer failed" severity failure;
  policy_allow<='0';wait until rising_edge(clk);wait for 1 ns;
  assert network_isolate='1' and tx_valid='0' and tx_data=x"0000000000000000" report "gate failed to blank" severity failure;
  policy_allow<='1';wait until rising_edge(clk);wait for 1 ns;
  assert tx_valid='0' report "quarantine released too soon" severity failure;
  wait until rising_edge(clk);wait for 1 ns;
  assert tx_valid='0' report "isolation recovery too soon" severity failure;
  wait until rising_edge(clk);wait for 1 ns;
  assert tx_valid='1' report "authorized recovery failed" severity failure;
  report "PASS: mesh policy gate isolation, authorization, recovery" severity note;
  wait;
 end process;
end architecture;
