// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

contract PNKTheosisOracle is Ownable {
    mapping(address => uint256) public theosisScores;

    event TheosisUpdated(address indexed juror, uint256 score);

    constructor() Ownable(msg.sender) {}

    function updateJurorTheosis(address juror, uint256 score) external onlyOwner {
        theosisScores[juror] = score;
        emit TheosisUpdated(juror, score);
    }

    function getJurorTheosis(address juror) external view returns (uint256) {
        return theosisScores[juror];
    }
}
