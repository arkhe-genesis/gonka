const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  // Deploy Vea Relay Mock for this example. In prod, you'd use a deployed Vea Relay address.
  const MockVeaRelay = await hre.ethers.getContractFactory("MockVeaRelay");
  const veaRelay = await MockVeaRelay.deploy();
  await veaRelay.waitForDeployment();
  console.log("MockVeaRelay deployed to:", await veaRelay.getAddress());

  // RBB Target Address - assuming a mock or placeholder for Arbitrum -> RBB
  const rbbTargetAddress = deployer.address; // Change in prod
  console.log("Using RBB Target Address:", rbbTargetAddress);

  // Deploy PNKTheosisOracle
  const PNKTheosisOracle = await hre.ethers.getContractFactory("PNKTheosisOracle");
  const pnkTheosisOracle = await PNKTheosisOracle.deploy();
  await pnkTheosisOracle.waitForDeployment();
  console.log("PNKTheosisOracle deployed to:", await pnkTheosisOracle.getAddress());

  // Deploy CathedralKlerosBridge
  const CathedralKlerosBridge = await hre.ethers.getContractFactory("CathedralKlerosBridge");
  const cathedralKlerosBridge = await CathedralKlerosBridge.deploy(
    await veaRelay.getAddress(),
    rbbTargetAddress
  );
  await cathedralKlerosBridge.waitForDeployment();
  console.log("CathedralKlerosBridge deployed to:", await cathedralKlerosBridge.getAddress());

  // Deploy CathedralKlerosBridgeWithVoting
  const CathedralKlerosBridgeWithVoting = await hre.ethers.getContractFactory("CathedralKlerosBridgeWithVoting");
  const cathedralKlerosBridgeWithVoting = await CathedralKlerosBridgeWithVoting.deploy(
    await veaRelay.getAddress(),
    rbbTargetAddress,
    await pnkTheosisOracle.getAddress()
  );
  await cathedralKlerosBridgeWithVoting.waitForDeployment();
  console.log("CathedralKlerosBridgeWithVoting deployed to:", await cathedralKlerosBridgeWithVoting.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
