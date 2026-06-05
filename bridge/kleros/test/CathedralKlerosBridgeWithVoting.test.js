const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CathedralKlerosBridgeWithVoting", function () {
  let pnkTheosisOracle, cathedralKlerosBridgeWithVoting, mockVeaRelay;
  let owner, juror, rbbTargetAddress;

  beforeEach(async function () {
    [owner, juror, rbbTargetAddress] = await ethers.getSigners();

    const MockVeaRelay = await ethers.getContractFactory("MockVeaRelay");
    mockVeaRelay = await MockVeaRelay.deploy();
    await mockVeaRelay.waitForDeployment();

    const PNKTheosisOracle = await ethers.getContractFactory("PNKTheosisOracle");
    pnkTheosisOracle = await PNKTheosisOracle.deploy();
    await pnkTheosisOracle.waitForDeployment();

    const CathedralKlerosBridgeWithVoting = await ethers.getContractFactory("CathedralKlerosBridgeWithVoting");
    cathedralKlerosBridgeWithVoting = await CathedralKlerosBridgeWithVoting.deploy(
      await mockVeaRelay.getAddress(),
      rbbTargetAddress.address,
      await pnkTheosisOracle.getAddress()
    );
    await cathedralKlerosBridgeWithVoting.waitForDeployment();
  });

  it("Should correctly initialize oracle address", async function () {
    expect(await cathedralKlerosBridgeWithVoting.theosisOracle()).to.equal(await pnkTheosisOracle.getAddress());
  });

  it("Should calculate base weight when Theosis score is 0", async function () {
    const baseWeight = 1000;
    const weightedVote = await cathedralKlerosBridgeWithVoting.calculateWeightedVote(juror.address, baseWeight);
    expect(weightedVote).to.equal(baseWeight);
  });

  it("Should apply a multiplier based on the oracle's theosis score", async function () {
    const theosisScore = 500; // 50% bonus
    await pnkTheosisOracle.updateJurorTheosis(juror.address, theosisScore);

    const baseWeight = 1000;
    // Expected: 1000 + (1000 * 500 / 1000) = 1500
    const expectedWeight = 1500;

    const weightedVote = await cathedralKlerosBridgeWithVoting.calculateWeightedVote(juror.address, baseWeight);
    expect(weightedVote).to.equal(expectedWeight);
  });

  it("Should emit a WeightedVoteCast event on castVote", async function () {
    const theosisScore = 500; // 50% bonus
    await pnkTheosisOracle.updateJurorTheosis(juror.address, theosisScore);

    const disputeID = 1;
    const choice = 2; // e.g., 2 options, user picks option 2
    const baseWeight = 1000;
    const finalWeight = 1500;

    await expect(cathedralKlerosBridgeWithVoting.connect(juror).castVote(disputeID, choice, baseWeight))
      .to.emit(cathedralKlerosBridgeWithVoting, "WeightedVoteCast")
      .withArgs(juror.address, disputeID, choice, finalWeight);
  });
});
