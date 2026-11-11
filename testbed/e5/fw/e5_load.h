/* E5 graded timing regressions, inserted at the top of the step function by mutate_e5.py.
 * ALU ladder: n x "add r12, r12, #0" (1 cycle each on Cortex-M4, 1 instruction under QEMU).
 * DIV ladder: n x dependent "vdiv.f32" (14 cycles each on Cortex-M4F, 1 instruction under QEMU).
 * On the host (SIL) both expand to nothing: SIL cannot see timing, by construction. */
#ifndef E5_LOAD_H
#define E5_LOAD_H
#if defined(__arm__)
#define E5_LOAD_ALU(n) __asm volatile(".rept " #n "\n\tadd r12, r12, #0\n\t.endr" ::: "r12")
#define E5_LOAD_DIV(n) __asm volatile("vmov.f32 s14, #1.0\n\tvmov.f32 s15, #1.0\n\t.rept " #n \
                                      "\n\tvdiv.f32 s15, s15, s14\n\t.endr" ::: "s14", "s15")
#else
#define E5_LOAD_ALU(n) ((void)0)
#define E5_LOAD_DIV(n) ((void)0)
#endif
#endif
