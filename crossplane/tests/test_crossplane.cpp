#include "im_crossplane.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <chrono>
int main(){
 assert(im_core_version()==1);
 uint8_t d[32]={0};assert(im_digest_bytes((const uint8_t*)"abc",3,d)==0);
 const uint8_t expected[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,
 0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
 assert(std::memcmp(d,expected,32)==0);
 im_mesh_stats first{},again{};
 auto start=std::chrono::steady_clock::now();
 assert(im_simulate_mesh(20000,20000,2,&first)==0);
 assert(im_simulate_mesh(20000,20000,2,&again)==0);
 assert(first.disconnected_nodes==10000);
 assert(first.delivered_simulated==20000);
 assert(first.aggregate_state==again.aggregate_state);
 assert(im_simulate_mesh(20000,20000,1,&again)!=0);
 auto ms=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start).count();
 std::printf("PASS 20000 synthetic mixed Android/iOS nodes; %u dropped; %u synthetic packet assignments; %lld ms; NO LIVE RADIO\n",first.disconnected_nodes,first.delivered_simulated,(long long)ms);
 return 0;
}
