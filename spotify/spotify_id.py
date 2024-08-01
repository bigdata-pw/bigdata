import string

BASE62_DIGITS = string.digits + string.ascii_lowercase + string.ascii_uppercase


class SpotifyIdError(Exception): ...


class SpotifyId:
    SIZE = 16
    SIZE_BASE16 = 32
    SIZE_BASE62 = 22

    def __init__(self, id: int):
        self.id = id

    @classmethod
    def from_base62(cls, src: str):
        if len(src) != cls.SIZE_BASE62:
            raise SpotifyIdError(
                f"Invalid length. Got {len(src)}, expected {cls.SIZE_BASE62}"
            )

        dst = 0
        for c in src:
            if "0" <= c <= "9":
                p = ord(c) - ord("0")
            elif "a" <= c <= "z":
                p = ord(c) - ord("a") + 10
            elif "A" <= c <= "Z":
                p = ord(c) - ord("A") + 36
            else:
                raise SpotifyIdError(f"InvalidId. Unexpected character: {c}")

            dst = dst * 62 + p

        return cls(dst)

    @classmethod
    def from_base16(cls, src: str):
        if len(src) != cls.SIZE_BASE16:
            raise SpotifyIdError(
                f"Invalid length. Got {len(src)}, expected {cls.SIZE_BASE16}"
            )

        id = int(src, 16)
        return cls(id)

    def to_base16(self):
        return self.id.to_bytes(self.SIZE, byteorder="big").hex()

    def to_base62(self):
        dst = [0] * self.SIZE_BASE62
        n = self.id

        for shift in [96, 64, 32, 0]:
            carry = (n >> shift) & 0xFFFFFFFF

            for i in range(len(dst)):
                carry += dst[i] << 32
                dst[i] = carry % 62
                carry //= 62

            while carry > 0:
                dst.append(carry % 62)
                carry //= 62

        dst = [BASE62_DIGITS[b] for b in dst]
        dst.reverse()

        return "".join(dst)

    def to_raw(self):
        return self.id.to_bytes(self.SIZE, byteorder="big")


track_id = "5JmLWkNrgjgyVqRuXTqtre"
gid = SpotifyId.from_base62(track_id).to_base16()
assert SpotifyId.from_base16(gid).to_base62() == track_id
print(f"track id: {track_id} <-> gid: {gid}")
