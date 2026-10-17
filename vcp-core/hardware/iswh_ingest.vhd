library ieee;
use ieee.std_logic_1164.all;
-- Development fabric-facing stream after a proper vendor JESD204B RX IP core.
-- Not a SERDES, clock recovery, JESD decoder or verified AD9208 board interface.
entity iswh_ingest is
 port(clk,rst,rx_valid,rx_link_ok,policy_allow: in std_logic;
      rx_sample_a,rx_sample_b: in std_logic_vector(13 downto 0);
      out_valid: out std_logic;
      out_a,out_b: out std_logic_vector(13 downto 0));
end;
architecture rtl of iswh_ingest is
begin
 process(clk)
 begin
  if rising_edge(clk) then
   out_valid<='0';out_a<=(others=>'0');out_b<=(others=>'0');
   if rst='0' and rx_valid='1' and rx_link_ok='1' and policy_allow='1' then
    out_valid<='1';out_a<=rx_sample_a;out_b<=rx_sample_b;
   end if;
  end if;
 end process;
end;
