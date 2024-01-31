import sys
import codecs
if len(sys.argv) < 3:
    print("Argument: bin_file output_file")
    sys.exit(1)

header_start = bytes.fromhex("041C6A04")

filename = sys.argv[1]
output_filename = sys.argv[2]
i = 0
with open(filename, "rb") as fi:
    data = fi.read()
    with open(output_filename, "wb") as fo:
        while i < len(data)-4:
            if data[i:i+4] == header_start:
                print("OK", "%04x" % i, codecs.encode(data[i:i+18], "hex"), "CRC", codecs.encode(data[i+18+0x400:i+18+0x400+12], "hex"))
                fo.write(data[i+18:i+18+0x400])
            i += 1
