// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 value) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @dev OpenZeppelin MerkleProof library
 */
library MerkleProof {
    function verify(bytes32[] memory proof, bytes32 root, bytes32 leaf) internal pure returns (bool) {
        return processProof(proof, leaf) == root;
    }

    function processProof(bytes32[] memory proof, bytes32 leaf) internal pure returns (bytes32) {
        bytes32 computedHash = leaf;
        for (uint256 i = 0; i < proof.length; i++) {
            computedHash = _hashPair(computedHash, proof[i]);
        }
        return computedHash;
    }

    function _hashPair(bytes32 a, bytes32 b) private pure returns (bytes32) {
        return a < b ? _efficientKeccak256(a, b) : _efficientKeccak256(b, a);
    }

    function _efficientKeccak256(bytes32 a, bytes32 b) private pure returns (bytes32 value) {
        assembly {
            mstore(0x00, a)
            mstore(0x20, b)
            value := keccak256(0x00, 0x40)
        }
    }
}

/**
 * @title MerkleDistributor
 * @notice Distributes ERC20 tokens to eligible Base accounts using Merkle proofs.
 */
contract MerkleDistributor {
    address public immutable token;
    bytes32 public immutable merkleRoot;
    address public owner;

    // Packed bitmap to track claimed indices with minimum gas
    mapping(uint256 => uint256) private claimedBitMap;

    event Claimed(uint256 indexed index, address indexed account, uint256 amount);
    event EmergencyWithdraw(address indexed to, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "MerkleDistributor: caller is not owner");
        _;
    }

    constructor(address token_, bytes32 merkleRoot_) {
        token = token_;
        merkleRoot = merkleRoot_;
        owner = msg.sender;
    }

    function isClaimed(uint256 index) public view returns (bool) {
        uint256 claimedWordIndex = index / 256;
        uint256 claimedBitIndex = index % 256;
        uint256 claimedWord = claimedBitMap[claimedWordIndex];
        uint256 mask = (1 << claimedBitIndex);
        return claimedWord & mask == mask;
    }

    function _setClaimed(uint256 index) private {
        uint256 claimedWordIndex = index / 256;
        uint256 claimedBitIndex = index % 256;
        claimedBitMap[claimedWordIndex] = claimedBitMap[claimedWordIndex] | (1 << claimedBitIndex);
    }

    function claim(
        uint256 index,
        address account,
        uint256 amount,
        bytes32[] calldata merkleProof
    ) external {
        require(!isClaimed(index), "MerkleDistributor: Drop already claimed.");

        // Verify the merkle proof
        bytes32 node = keccak256(bytes.concat(keccak256(abi.encode(index, account, amount))));
        require(MerkleProof.verify(merkleProof, merkleRoot, node), "MerkleDistributor: Invalid proof.");

        // Mark it claimed and send the token
        _setClaimed(index);
        require(IERC20(token).transfer(account, amount), "MerkleDistributor: Transfer failed.");

        emit Claimed(index, account, amount);
    }

    // Allows owner to retrieve leftover tokens after the airdrop period
    function emergencyWithdraw(address to) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(IERC20(token).transfer(to, balance), "MerkleDistributor: Transfer failed.");
        emit EmergencyWithdraw(to, balance);
    }
}
