library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
-- Wide event counter testbed. Not 10^33 operations/sec, quantum or neutrino hardware.
entity iswh_decillion_counter is
 port(clk,reset,link_healthy,identity_valid,policy_allow,event_valid: in std_logic;
      event_count:out std_logic_vector(255 downto 0);
      count_valid,quarantine,overflow:out std_logic);
end entity;
architecture rtl of iswh_decillion_counter is
 signal counter:unsigned(255 downto 0):=(others=>'0');
 signal blocked:std_logic:='1';
begin
 process(clk)
 begin
  if rising_edge(clk) then
   count_valid<='0';overflow<='0';blocked<='1';
   if reset='1' then
    counter<=(others=>'0');
   elsif link_healthy='1' and identity_valid='1' and policy_allow='1' then
    blocked<='0';
    if event_valid='1' then
     if counter=(counter'range => '1') then
      overflow<='1';
     else
      counter<=counter+1;
      count_valid<='1';
     end if;
    end if;
   end if;
  end if;
 end process;
 event_count<=std_logic_vector(counter);
 quarantine<=blocked;
end architecture;
