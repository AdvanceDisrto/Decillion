#include "im_crossplane.h"
#include <algorithm>
#include <cstring>
#include <vector>

// Deterministic software mesh emulator. Digest is SHA-256 through a
// self-contained portable implementation; this does NOT create a signature.
namespace {
constexpr uint32_t K[64] = {
0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
};
inline uint32_t rr(uint32_t v,unsigned n){return (v>>n)|(v<<(32-n));}
void compress(uint32_t h[8],const uint8_t* p){
 uint32_t w[64];
 for(int i=0;i<16;i++)w[i]=(uint32_t(p[4*i])<<24)|(uint32_t(p[4*i+1])<<16)|(uint32_t(p[4*i+2])<<8)|p[4*i+3];
 for(int i=16;i<64;i++)w[i]=(rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>10))+w[i-7]+(rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>3))+w[i-16];
 uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],z=h[7];
 for(int i=0;i<64;i++){
  uint32_t t1=z+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^((~e)&g))+K[i]+w[i];
  uint32_t t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));
  z=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
 }
 h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=z;
}
}
extern "C" int im_core_version(void){return IM_CORE_ABI_VERSION;}
extern "C" int im_digest_bytes(const uint8_t* data,size_t len,uint8_t out[32]){
 if(!out||(!data&&len)||len>16*1024*1024)return -1;
 uint32_t h[8]={0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u};
 for(size_t i=0;i+64<=len;i+=64)compress(h,data+i);
 const size_t remaining=len%64;
 uint8_t block[128]={0};
 if(remaining)std::memcpy(block,data+len-remaining,remaining);
 block[remaining]=0x80;
 uint64_t bits=uint64_t(len)*8;
 size_t bytes=remaining<56?64:128;
 for(int i=0;i<8;i++)block[bytes-1-i]=uint8_t(bits>>(i*8));
 compress(h,block);if(bytes==128)compress(h,block+64);
 for(int i=0;i<8;i++)for(int j=0;j<4;j++)out[4*i+j]=uint8_t(h[i]>>(24-j*8));
 return 0;
}
extern "C" int im_simulate_mesh(uint32_t nodes,uint32_t packets,uint32_t dropout_every,im_mesh_stats* out){
 if(!out||nodes<2||nodes>20000||packets>200000||dropout_every==1)return -1;
 std::memset(out,0,sizeof(*out));out->abi_version=IM_CORE_ABI_VERSION;out->node_count=nodes;
 out->simulated_packets=packets;
 uint32_t active=0;
 for(uint32_t i=0;i<nodes;i++)if(dropout_every && ((i+1)%dropout_every==0))out->disconnected_nodes++;else active++;
 if(!active)return -1;
 for(uint32_t i=0;i<packets;i++){
  uint32_t id=(i*2654435761u)%nodes;
  for(uint32_t x=0;x<nodes;x++){uint32_t candidate=(id+x)%nodes;if(!dropout_every||((candidate+1)%dropout_every!=0)){id=candidate;break;}}
  out->aggregate_state=(out->aggregate_state^((uint64_t(id)<<32)|i))*1099511628211ull;
  out->delivered_simulated++;
 }
 return 0;
}
