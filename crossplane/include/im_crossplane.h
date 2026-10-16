#ifndef IM_CROSSPLANE_H
#define IM_CROSSPLANE_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
// Stable portable C ABI shared by Android NDK and Apple Clang.
// No OS privileges, hardware access, SIM bypass or direct-radio APIs.
#define IM_CORE_ABI_VERSION 1
typedef struct {
  uint32_t abi_version;
  uint32_t node_count;
  uint32_t simulated_packets;
  uint32_t delivered_simulated;
  uint32_t disconnected_nodes;
  uint64_t aggregate_state;
} im_mesh_stats;
int im_core_version(void);
int im_simulate_mesh(uint32_t nodes, uint32_t packets, uint32_t dropout_every,
                     im_mesh_stats* out);
int im_digest_bytes(const uint8_t* data, size_t len, uint8_t out[32]);
#ifdef __cplusplus
}
#endif
#endif
