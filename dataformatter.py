class DataFormatter(object):
    """
    Formats bits and bytes into human readable format.
    Currently only works up to Terabits / Terabytes.
    """
    KILO = 1024

    @classmethod
    def format_bits(self, bits):
        bits = float(bits)
        if (bits / self.KILO) < 1.0:
            bits = '%6.2f bits' % bits
        elif (bits / self.KILO**2) < 1.0:
            bits = '%6.2f Kbits' % (bits / self.KILO)
        elif (bits / self.KILO**3) < 1.0:
            bits = '%6.2f Mbits' % (bits / self.KILO**2)
        elif (bits / self.KILO**4) < 1.0:
            bits = '%6.2f Gbits' % (bits / self.KILO**3)
        else:
            bits = '%6.2f Tbits' % (bits / self.KILO**4)
        return bits

    @classmethod
    def format_bytes(self, bytes):
        bytes = float(bytes)
        if (bytes / self.KILO) < 1.0:
            bytes = '%6.2f bytes' % bytes
        elif (bytes / self.KILO**2) < 1.0:
            bytes = '%6.2f Kbytes' % (bytes / self.KILO)
        elif (bytes / self.KILO**3) < 1.0:
            bytes = '%6.2f Mbytes' % (bytes / self.KILO**2)
        elif (bytes / self.KILO**4) < 1.0:
            bytes = '%6.2f Gbytes' % (bytes / self.KILO**3)
        else:
            bytes = '%6.2f Tbytes' % (bytes / self.KILO**4)
        return bytes
