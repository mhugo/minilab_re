from cmsis_svd.parser import SVDParser

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_MSP, UC_ARM_REG_SP, UC_ARM_REG_PC

from capstone import *

import unicorn


parser = SVDParser.for_packaged_svd("STMicro", "STM32F103xx.svd")
dev = parser.get_device()

print("Num interrupts", dev.cpu.device_num_interrupts)
"""
for peripheral in dev.peripherals:
    print("%s @ 0x%08x" % (peripheral.name, peripheral.base_address))
    for reg in peripheral.registers:
        print(f"    {reg.name} ({reg.access}): {reg.description}")
        # for field in reg.fields:
        #    print(f"      {field.name} @{field.bit_offset}")
"""

with open("firmwares/f_121166.strip.bin", "rb") as fi:
    firmware = fi.read()

print(len(firmware))


def hook_insn(uc, addr, size, data):
    print("INSN", uc, addr, size, data)


def hook_fetch_unmapped(uc, addr, size, data):
    print("Fetch unmapped", uc, addr, size, data)


def hook_mem_access(uc, access, addr, size, value, user_data):
    # TODO implement bit banging
    if access == unicorn.UC_MEM_WRITE:
        print(f"WRITE @{addr:X}({size}) = {value} (0x{value:X})")
    elif access == unicorn.UC_MEM_READ:
        print("READ", "{:x}".format(addr), size)
        if addr == 0x80035E4:
            print("****")
            uc.mem_write(addr, b"\x00\x00\x00\x00")


cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)


def hook_code(uc, address, size, user_data):
    instrs = uc.mem_read(address, size)
    for instr in cs.disasm(instrs, address):
        print(instr)

    # print(">>> Tracing instruction at 0x%x, instruction size = 0x%x" % (address, size))


code_end = 0x08000000 + len(firmware) - 1

mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)

# Flash memory
mu.mem_map(0x00000000, len(firmware))
mu.mem_write(0x00000000, firmware)
mu.mem_map(0x08000000, len(firmware))
mu.mem_write(0x08000000, firmware)

# SRAM
mu.mem_map(0x20000000, 1024 * 1024)  # 1MB
# bit band alias from 0x22000000 to 0x23FFFFFF
mu.mem_write(0x20000000, b"\x00" * 1024 * 1024)

sp = int.from_bytes(mu.mem_read(0, 4), "little")
print("SP", "{:x}".format(sp))
mu.reg_write(UC_ARM_REG_MSP, sp)
mu.reg_write(UC_ARM_REG_SP, sp)

pc = int.from_bytes(mu.mem_read(4, 4), "little")
print("PC", "{:x}".format(pc))

mu.hook_add(unicorn.UC_HOOK_INSN, hook_insn)
mu.hook_add(unicorn.UC_HOOK_MEM_FETCH_UNMAPPED, hook_fetch_unmapped)
mu.hook_add(unicorn.UC_HOOK_MEM_READ, hook_mem_access)
mu.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_mem_access)
mu.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=0, end=code_end)

thumb_mode = pc & 1
ppc = pc & 0xFFFFFFFE
mu.reg_write(UC_ARM_REG_PC, pc)
print("PPC", "{:x}".format(ppc))
try:
    mu.emu_start(pc, code_end, timeout=0, count=320)
except unicorn.UcError as e:
    print("error", e, e.args)

print("PC", "{:x}".format(mu.reg_read(UC_ARM_REG_PC)))
