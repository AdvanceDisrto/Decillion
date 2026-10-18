#include <cstdint>
#include <cmath>
#include <cstddef>
extern "C" int32_t execute_icalcula_pass(const double* values, size_t count, double* out_residual) {
  if (!values || !out_residual || count == 0 || count > 4096) return -1;
  double sum=0.0;
  for(size_t i=0;i<count;i++) { if(!std::isfinite(values[i])) return -2; sum += values[i]; }
  if(!std::isfinite(sum)) return -2;
  *out_residual=std::fabs(sum);
  return (*out_residual <= 1e-7) ? 0 : 1;
}
