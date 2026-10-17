library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity tb_iswh_decillion_counter is end;
architecture sim of tb_iswh_decillion_counter is
 signal clk:std_logic:='0';
 signal reset,link_healthy,identity_valid,policy_allow,event_valid:std_logic:='0';
 signal event_count:std_logic_vector(255 downto 0);
 signal count_valid,quarantine,overflow:std_logic;
begin
 clk<=not clk after 5 ns;
 dut:entity work.iswh_decillion_counter port map(clk,reset,link_healthy,identity_valid,policy_allow,event_valid,event_count,count_valid,quarantine,overflow);
 process
 begin
  reset<='1';wait until rising_edge(clk);wait for 1 ns;
  assert unsigned(event_count)=0 and quarantine='1' report "reset must isolate" severity failure;
  reset<='0';event_valid<='1';
  wait until rising_edge(clk);wait for 1 ns;
  assert unsigned(event_count)=0 and quarantine='1' report "unauthorized increment" severity failure;
  link_healthy<='1';identity_valid<='1';policy_allow<='1';
  wait until rising_edge(clk);wait for 1 ns;
  assert unsigned(event_count)=1 and count_valid='1' and quarantine='0' report "authorized count failed" severity failure;
  policy_allow<='0';wait until rising_edge(clk);wait for 1 ns;
  assert unsigned(event_count)=1 and count_valid='0' and quarantine='1' report "revocation gate failed" severity failure;
  report "PASS: 256-bit counted event gate / isolation" severity note;
  wait;
 end process;
end architecture;
