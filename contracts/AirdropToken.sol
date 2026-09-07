// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title BaseDrop Token ($BASED)
 * @notice Standard ERC-20 token for the Base Airdrop platform.
 */
contract AirdropToken {
    string public constant name = "BaseDrop Token";
    string public constant symbol = "BASED";
    uint8 public constant decimals = 18;
    uint256 public totalSupply;

    address public owner;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "AirdropToken: caller is not owner");
        _;
    }

    constructor(uint256 initialSupply) {
        owner = msg.sender;
        _mint(msg.sender, initialSupply);
    }

    function transfer(address recipient, uint256 amount) external returns (bool) {
        _transfer(msg.sender, recipient, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool) {
        uint256 currentAllowance = allowance[sender][msg.sender];
        if (currentAllowance != type(uint256).max) {
            require(currentAllowance >= amount, "AirdropToken: transfer amount exceeds allowance");
            unchecked {
                allowance[sender][msg.sender] = currentAllowance - amount;
            }
        }
        _transfer(sender, recipient, amount);
        return true;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "AirdropToken: zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function _transfer(address sender, address recipient, uint256 amount) internal {
        require(sender != address(0), "AirdropToken: transfer from zero address");
        require(recipient != address(0), "AirdropToken: transfer to zero address");
        require(balanceOf[sender] >= amount, "AirdropToken: insufficient balance");

        unchecked {
            balanceOf[sender] -= amount;
            balanceOf[recipient] += amount;
        }
        emit Transfer(sender, recipient, amount);
    }

    function _mint(address account, uint256 amount) internal {
        require(account != address(0), "AirdropToken: mint to zero address");
        totalSupply += amount;
        unchecked {
            balanceOf[account] += amount;
        }
        emit Transfer(address(0), account, amount);
    }
}
