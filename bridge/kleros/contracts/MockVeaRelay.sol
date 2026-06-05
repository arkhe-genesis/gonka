// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./CathedralKlerosBridge.sol";

contract MockVeaRelay is IVeaRelay {
    event MessageSent(address target, bytes message);

    function sendMessage(address target, bytes memory message) external {
        emit MessageSent(target, message);
    }
}
