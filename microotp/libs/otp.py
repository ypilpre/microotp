#
# otp.py
# MicroPython One Time Password Generator
# Copyright (C) 2016 Guido Dassori <guido.dassori@gmail.com>
# MIT License
#
#
# Inspired by https://github.com/pyotp/pyotp
# Copyright (C) 2011-2016 Mark Percival <m@mdp.im>,
# Nathan Reynolds <email@nreynolds.co.uk>, and PyOTP contributors


from gc import collect


class OTP(object):
    # TODO remove hex data around
    def __init__(self, s, digits=6):
        self.digits = digits
        self.secret = s

    def generate_otp(self, input):
        if input < 0:
            raise ValueError()
        from hmac import new
        from sha1 import sha1
        _bytestring = self.int_to_bytestring(input)
        hasher = new(self.secret, _bytestring, sha1)
        del sha1, new, self.secret, _bytestring
        collect()
        digest = hasher.digest()
        del hasher
        collect()
        hmac_hash = bytearray(digest)
        offset = hmac_hash[-1] & 0xf
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))
        str_code = str(code % 10 ** self.digits)
        while len(str_code) < self.digits:
            str_code = '0' + str_code
        del code, offset, hmac_hash
        collect()
        return str_code

    @staticmethod
    def int_to_bytestring(i, padding=8):
        result = bytearray()
        while i != 0:
            result.append(i & 0xFF)
            i >>= 8
        _bytearray = bytes(bytearray(reversed(result)))
        res = b'\0' * (padding - len(_bytearray)) + _bytearray
        del result, _bytearray
        return res


class TOTP(OTP):
    def __init__(self, *args, **kwargs):
        self.interval = kwargs.pop('interval', 30)
        super(TOTP, self).__init__(*args, **kwargs)

    def now(self):
        from utime import time
        _now = self.timecode(int(time()))
        del time
        collect()
        res = self.generate_otp(_now)
        del _now
        collect()
        return res

    def timecode(self, for_time):
        TIME_OFFSET = 946681200
        for_time += TIME_OFFSET
        return for_time // self.interval


class HOTP(OTP):
    def at(self, count):
        return self.generate_otp(count)

    def verify(self, otp, counter):
        return str(otp) == str(self.at(counter))