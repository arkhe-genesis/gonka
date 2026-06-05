const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PNKTheosisOracle & CathedralKlerosBridge", function () {
  let pnkTheosisOracle, cathedralKlerosBridge;
  let owner, user, veaRelayMock, rbbTargetAddress;

  beforeEach(async function () {
    [owner, user, veaRelayMock, rbbTargetAddress] = await ethers.getSigners();

    const PNKTheosisOracle = await ethers.getContractFactory("PNKTheosisOracle");
    pnkTheosisOracle = await PNKTheosisOracle.deploy();
    await pnkTheosisOracle.waitForDeployment();

    const CathedralKlerosBridge = await ethers.getContractFactory("CathedralKlerosBridge");
    cathedralKlerosBridge = await CathedralKlerosBridge.deploy(
      veaRelayMock.address,
      rbbTargetAddress.address
    );
    await cathedralKlerosBridge.waitForDeployment();
  });

  describe("PNKTheosisOracle", function () {
    it("Should allow the owner to update juror theosis", async function () {
      const theosisScore = 500;
      await expect(pnkTheosisOracle.updateJurorTheosis(user.address, theosisScore))
        .to.emit(pnkTheosisOracle, "TheosisUpdated")
        .withArgs(user.address, theosisScore);

      expect(await pnkTheosisOracle.getJurorTheosis(user.address)).to.equal(theosisScore);
    });

    it("Should revert if non-owner tries to update juror theosis", async function () {
      await expect(
        pnkTheosisOracle.connect(user).updateJurorTheosis(user.address, 500)
      ).to.be.revertedWithCustomError(pnkTheosisOracle, "OwnableUnauthorizedAccount");
    });
  });

  describe("CathedralKlerosBridge", function () {
    it("Should set initial Vea Relay and RBB Target", async function () {
      expect(await cathedralKlerosBridge.veaRelay()).to.equal(veaRelayMock.address);
      expect(await cathedralKlerosBridge.rbbTargetAddress()).to.equal(rbbTargetAddress.address);
    });

    it("Should allow owner to update Vea Relay", async function () {
      const newVeaRelay = user.address;
      await expect(cathedralKlerosBridge.setVeaRelay(newVeaRelay))
        .to.emit(cathedralKlerosBridge, "VeaRelayUpdated")
        .withArgs(veaRelayMock.address, newVeaRelay);

      expect(await cathedralKlerosBridge.veaRelay()).to.equal(newVeaRelay);
    });

    it("Should allow sending a dispute to RBB", async function () {
      // Mocking the relay is hard without an actual mock contract, but we can verify the event
      // However, our bridge tries to call the mock, so we need to set a proper mock
      // Since veaRelayMock is just an EOA, the call `sendMessage` will fail because it's not a contract with that function.

      // Let's create a dummy MockVeaRelay
      const MockVeaRelay = await ethers.getContractFactory(
        "MockVeaRelay"
      );
      const mockRelay = await MockVeaRelay.deploy();
      await mockRelay.waitForDeployment();

      await cathedralKlerosBridge.setVeaRelay(await mockRelay.getAddress());

      const disputeID = 1;
      const data = ethers.toUtf8Bytes("Test Dispute");

      await expect(cathedralKlerosBridge.connect(user).sendDisputeToRBB(disputeID, data))
        .to.emit(cathedralKlerosBridge, "DisputeSentToRBB")
        .withArgs(disputeID, user.address, data);
    });
  });
});
