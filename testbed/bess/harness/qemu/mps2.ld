/* QEMU mps2-an386: SSRAM1 at 0x0 (code + data, writable in QEMU), SSRAM2 at 0x20000000 (stack/heap). */
MEMORY
{
  RAM0 (rwx) : ORIGIN = 0x00000000, LENGTH = 4M
  RAM1 (rwx) : ORIGIN = 0x20000000, LENGTH = 4M
}
ENTRY(Reset_Handler)
SECTIONS
{
  .text : {
    KEEP(*(.vectors))
    *(.text*)
    KEEP(*(.init))
    KEEP(*(.fini))
    *(.rodata*)
    . = ALIGN(4);
  } > RAM0
  .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } > RAM0
  .ARM.exidx : { __exidx_start = .; *(.ARM.exidx*) __exidx_end = .; } > RAM0
  .preinit_array : { PROVIDE_HIDDEN(__preinit_array_start = .); KEEP(*(.preinit_array)) PROVIDE_HIDDEN(__preinit_array_end = .); } > RAM0
  .init_array : { PROVIDE_HIDDEN(__init_array_start = .); KEEP(*(SORT(.init_array.*))) KEEP(*(.init_array)) PROVIDE_HIDDEN(__init_array_end = .); } > RAM0
  .fini_array : { PROVIDE_HIDDEN(__fini_array_start = .); KEEP(*(.fini_array)) PROVIDE_HIDDEN(__fini_array_end = .); } > RAM0
  .data : { *(.data*) . = ALIGN(4); } > RAM0
  .bss : { __bss_start__ = .; *(.bss*) *(COMMON) . = ALIGN(4); __bss_end__ = .; } > RAM0
  end = .;
  __end__ = .;
  __StackTop = ORIGIN(RAM1) + LENGTH(RAM1);
}
