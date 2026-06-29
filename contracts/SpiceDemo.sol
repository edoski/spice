// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract SpiceDemo {
    event Ping(
        address indexed sender,
        uint256 indexed runId,
        uint256 blockNumber,
        uint256 timestamp
    );

    function ping(uint256 runId) external {
        emit Ping(msg.sender, runId, block.number, block.timestamp);
    }
}
