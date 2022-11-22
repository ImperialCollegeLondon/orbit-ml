#ifndef __HLS_INT_H__
#define __HLS_INT_H__

#ifdef __VIVADO__

#include <ap_int.h>
template<int __ORBIT_N__, bool __ORBIT_B__=true>
struct ac_int: ap_int_base<__ORBIT_N__, __ORBIT_B__> {
    ac_int(): ap_int_base<__ORBIT_N__, __ORBIT_B__> () { 

    }        

    template<class __ORBIT_T__> 
    ac_int(__ORBIT_T__ X): ap_int_base<__ORBIT_N__, __ORBIT_B__> (X) { 

    }
    

    template<int __ORBIT_SIZE__>
    ac_int<__ORBIT_SIZE__, __ORBIT_B__> slc(int lsb) { return ac_int<__ORBIT_SIZE__,__ORBIT_B__>(this->range(__ORBIT_SIZE__ + lsb, lsb)); }

    template<int __ORBIT_SIZE__, bool __ORBIT_S__>
    void set_slc(int lsb, const ac_int<__ORBIT_SIZE__, __ORBIT_S__> &val) {
        this->range(lsb + __ORBIT_SIZE__ - 1, lsb) = val;

    }

    void info() {
        printf("width=%d\n", ap_int_base<__ORBIT_N__, __ORBIT_B__>::width);
        printf("sign=%d\n", ap_int_base<__ORBIT_N__, __ORBIT_B__>::sign_flag);
    }

};
#else
#include "__ac_int.h"
#endif

#endif