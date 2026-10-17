library ieee;
use ieee.std_logic_1164.all;
-- Fabric-side packet gate, NOT LoRa PHY, PQC verifier, quantum co-processor, or truth oracle.
entity iswh_mesh_gate is
 port(clk, reset, packet_ready, link_healthy, identity_valid, policy_allow: in std_logic;
      rx_data: in std_logic_vector(63 downto 0);
      tx_data: out std_logic_vector(63 downto 0);
      tx_valid, network_isolate: out std_logic);
end entity;
architecture rtl of iswh_mesh_gate is
 type state_t is (ISOLATED, IDLE, QUARANTINED);
 signal state:state_t := ISOLATED;
begin
 process(clk)
 begin
  if rising_edge(clk) then
   tx_data <= (others=>'0');tx_valid<='0';network_isolate<='1';
   if reset='1' then
    state<=ISOLATED;
   elsif link_healthy='0' or identity_valid='0' or policy_allow='0' then
    state<=QUARANTINED;
   else
    case state is
     when ISOLATED => state<=IDLE;
     when IDLE =>
      network_isolate<='0';
      if packet_ready='1' then
       tx_data<=rx_data;tx_valid<='1';
      end if;
     when QUARANTINED => state<=ISOLATED;
    end case;
   end if;
  end if;
 end process;
end architecture;
