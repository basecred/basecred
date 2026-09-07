"""
Merkle Tree implementation for Base Airdrop Distributor.
Matches OpenZeppelin MerkleProof.verify logic.
"""
from typing import List, Dict, Any
from engine.keccak import keccak_256, encode_leaf

def hash_pair(a: bytes, b: bytes) -> bytes:
    """Sorted pair hashing to prevent order dependency."""
    if a < b:
        return keccak_256(a + b)
    else:
        return keccak_256(b + a)

class MerkleTree:
    def __init__(self, elements: List[Dict[str, Any]]):
        """
        elements: list of dicts with 'index', 'account', 'amount'
        """
        self.elements = elements
        self.leaves: List[bytes] = []
        for el in elements:
            leaf = encode_leaf(el["index"], el["account"], el["amount"])
            self.leaves.append(leaf)

        self.layers: List[List[bytes]] = []
        self._build_tree()

    def _build_tree(self):
        if not self.leaves:
            self.layers = [[b"\x00" * 32]]
            return

        current_layer = list(self.leaves)
        self.layers.append(current_layer)

        while len(current_layer) > 1:
            next_layer: List[bytes] = []
            for i in range(0, len(current_layer), 2):
                if i + 1 < len(current_layer):
                    parent = hash_pair(current_layer[i], current_layer[i + 1])
                else:
                    # Odd element is paired with itself or carried up
                    parent = current_layer[i]
                next_layer.append(parent)
            current_layer = next_layer
            self.layers.append(current_layer)

    @property
    def root(self) -> bytes:
        if not self.layers:
            return b"\x00" * 32
        return self.layers[-1][0]

    @property
    def root_hex(self) -> str:
        return "0x" + self.root.hex()

    def get_proof(self, index: int) -> List[str]:
        """Generates Merkle proof for element at index."""
        if index < 0 or index >= len(self.leaves):
            raise IndexError("Element index out of range")

        proof: List[bytes] = []
        current_idx = index

        for layer in self.layers[:-1]:
            is_right_node = (current_idx % 2 == 1)
            pair_idx = current_idx - 1 if is_right_node else current_idx + 1

            if pair_idx < len(layer):
                proof.append(layer[pair_idx])

            current_idx = current_idx // 2

        return ["0x" + p.hex() for p in proof]

    @staticmethod
    def verify(proof: List[bytes], root: bytes, leaf: bytes) -> bool:
        computed_hash = leaf
        for proof_element in proof:
            computed_hash = hash_pair(computed_hash, proof_element)
        return computed_hash == root
