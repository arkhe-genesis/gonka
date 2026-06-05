// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./CathedralKlerosBridge.sol";
import "./PNKTheosisOracle.sol";

contract CathedralKlerosBridgeWithVoting is CathedralKlerosBridge {
    PNKTheosisOracle public theosisOracle;

    event TheosisOracleUpdated(address oldOracle, address newOracle);
    event WeightedVoteCast(address indexed juror, uint256 disputeID, uint256 choice, uint256 weightedPower);

    constructor(
        address _veaRelay,
        address _rbbTargetAddress,
        address _theosisOracle
    ) CathedralKlerosBridge(_veaRelay, _rbbTargetAddress) {
        theosisOracle = PNKTheosisOracle(_theosisOracle);
    }

    function setTheosisOracle(address _theosisOracle) external onlyOwner {
        emit TheosisOracleUpdated(address(theosisOracle), _theosisOracle);
        theosisOracle = PNKTheosisOracle(_theosisOracle);
    }

    function calculateWeightedVote(address juror, uint256 baseWeight) public view returns (uint256) {
        uint256 theosisScore = theosisOracle.getJurorTheosis(juror);
        // Assuming TheosisScore is out of 1000 for multiplier (e.g. 500 = 1.5x)
        // If TheosisScore is 0, multiplier is 1x.
        // Formula: BaseWeight + (BaseWeight * theosisScore / 1000)
        uint256 theosisBonus = (baseWeight * theosisScore) / 1000;
        return baseWeight + theosisBonus;
    }

    function castVote(uint256 disputeID, uint256 choice, uint256 baseWeight) external {
        uint256 finalWeight = calculateWeightedVote(msg.sender, baseWeight);

        // Encode the vote information
        bytes memory data = abi.encode("VOTE", choice, finalWeight);

        // Send the vote to RBB Target
        bytes memory message = abi.encode(disputeID, msg.sender, data);
        veaRelay.sendMessage(rbbTargetAddress, message);

        emit WeightedVoteCast(msg.sender, disputeID, choice, finalWeight);
    }
}
