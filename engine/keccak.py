"""
Ethereum Keccak-256 implementation in pure Python.
Used for cryptographic leaf generation, address verification, and Merkle proofs.
"""

RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008
]

ROTC = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14]
]

def _rol(x: int, s: int) -> int:
    return ((x << s) | (x >> (64 - s))) & 0xFFFFFFFFFFFFFFFF

def keccak_256(data: bytes) -> bytes:
    """Computes standard Ethereum Keccak-256 hash."""
    r = 1088 // 8
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % r != (r - 1):
        padded.append(0x00)
    padded.append(0x80)

    state = [0] * 25

    for b in range(0, len(padded), r):
        for i in range(r // 8):
            state[i] ^= int.from_bytes(padded[b + i * 8 : b + (i + 1) * 8], "little")
        for rnd in range(24):
            # Theta
            C = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
            D = [C[(x + 4) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x + y * 5] ^= D[x]
            # Rho & Pi
            B = [0] * 25
            for x in range(5):
                for y in range(5):
                    B[y + ((2 * x + 3 * y) % 5) * 5] = _rol(state[x + y * 5], ROTC[x][y])
            # Chi
            for x in range(5):
                for y in range(5):
                    state[x + y * 5] = B[x + y * 5] ^ ((~B[(x + 1) % 5 + y * 5]) & B[(x + 2) % 5 + y * 5])
            # Iota
            state[0] ^= RC[rnd]

    out = bytearray()
    for i in range(4):
        out.extend(state[i].to_bytes(8, "little"))
    return bytes(out)

def encode_leaf(index: int, account: str, amount: int) -> bytes:
    """
    Standard OpenZeppelin double-hash leaf encoding:
    keccak256(bytes.concat(keccak256(abi.encode(index, account, amount))))
    """
    # abi.encode(uint256 index, address account, uint256 amount)
    # uint256: 32 bytes big-endian
    # address: 32 bytes big-endian (zero-padded 12 bytes + 20 bytes address)
    clean_addr = account.lower().replace("0x", "")
    addr_bytes = bytes.fromhex(clean_addr)
    if len(addr_bytes) != 20:
        raise ValueError(f"Invalid address: {account}")

    index_bytes = index.to_bytes(32, byteorder="big")
    addr_padded = b"\x00" * 12 + addr_bytes
    amount_bytes = amount.to_bytes(32, byteorder="big")

    abi_encoded = index_bytes + addr_padded + amount_bytes
    inner_hash = keccak_256(abi_encoded)
    leaf_hash = keccak_256(inner_hash)
    return leaf_hash
