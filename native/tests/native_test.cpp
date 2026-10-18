#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <cstddef>
#include <cstdint>
extern "C" int32_t execute_icalcula_pass(const double*, size_t, double*);
int main(){
 double out=999; double ok[]={1.,-1.,0.};
 assert(execute_icalcula_pass(ok,3,&out)==0&&out==0);
 double fail[]={1.,0.}; assert(execute_icalcula_pass(fail,2,&out)==1&&out==1);
 double nan[]={std::numeric_limits<double>::quiet_NaN()};
 assert(execute_icalcula_pass(nan,1,&out)==-2);
 assert(execute_icalcula_pass(nullptr,1,&out)==-1);
 assert(execute_icalcula_pass(ok,0,&out)==-1);
 std::cout<<"5 assertions passed\n";
}
