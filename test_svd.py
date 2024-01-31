from cmsis_svd.parser import SVDParser


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
