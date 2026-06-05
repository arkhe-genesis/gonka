// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

interface IVeaRelay {
    function sendMessage(address target, bytes memory message) external;
}

contract CathedralKlerosBridge is Ownable {
    IVeaRelay public veaRelay;
    address public rbbTargetAddress;

    event DisputeSentToRBB(uint256 indexed disputeID, address indexed sender, bytes data);
    event VeaRelayUpdated(address oldRelay, address newRelay);
    event RBBTargetUpdated(address oldTarget, address newTarget);

    constructor(address _veaRelay, address _rbbTargetAddress) Ownable(msg.sender) {
        veaRelay = IVeaRelay(_veaRelay);
        rbbTargetAddress = _rbbTargetAddress;
    }

    function setVeaRelay(address _veaRelay) external onlyOwner {
        emit VeaRelayUpdated(address(veaRelay), _veaRelay);
        veaRelay = IVeaRelay(_veaRelay);
    }

    function setRBBTargetAddress(address _rbbTargetAddress) external onlyOwner {
        emit RBBTargetUpdated(rbbTargetAddress, _rbbTargetAddress);
        rbbTargetAddress = _rbbTargetAddress;
    }

    function sendDisputeToRBB(uint256 disputeID, bytes memory data) external {
        // Prepare the message for the destination chain
        bytes memory message = abi.encode(disputeID, msg.sender, data);

        // Send via Vea Relay to the RBB Target
        veaRelay.sendMessage(rbbTargetAddress, message);

        emit DisputeSentToRBB(disputeID, msg.sender, data);
    }
}
