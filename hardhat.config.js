require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.24",
  paths: {
    sources: "./bridge/kleros/contracts",
    tests: "./bridge/kleros/test",
    cache: "./bridge/kleros/cache",
    artifacts: "./bridge/kleros/artifacts"
  }
};
