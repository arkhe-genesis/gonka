import os
import json
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
from eth_account import Account

# Setup Web3 targeting Arbitrum (or any specific network RPC)
RPC_URL = os.getenv("ARBITRUM_RPC_URL", "http://127.0.0.1:8545")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("Missing PRIVATE_KEY environment variable.")

account = Account.from_key(PRIVATE_KEY)
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))

def deploy_contract(contract_name, *args):
    artifact_path = f"bridge/kleros/artifacts/bridge/kleros/contracts/{contract_name}.sol/{contract_name}.json"
    with open(artifact_path, "r") as f:
        artifact = json.load(f)

    contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])

    print(f"Deploying {contract_name}...")

    tx_hash = contract.constructor(*args).transact({"from": account.address})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"{contract_name} deployed at: {receipt.contractAddress}")
    return receipt.contractAddress

def main():
    print(f"Connected to RPC: {RPC_URL}")
    print(f"Deployer Address: {account.address}")

    # Real addresses should be provided via ENV or config
    vea_relay_address = os.getenv("VEA_RELAY_ADDRESS", "0x0000000000000000000000000000000000000000")
    rbb_target_address = os.getenv("RBB_TARGET_ADDRESS", "0x0000000000000000000000000000000000000000")

    if vea_relay_address == "0x0000000000000000000000000000000000000000":
        # Deploy Mock Vea Relay for testnet/development
        vea_relay_address = deploy_contract("MockVeaRelay")

    oracle_address = deploy_contract("PNKTheosisOracle")

    bridge_address = deploy_contract("CathedralKlerosBridge", vea_relay_address, rbb_target_address)

    bridge_voting_address = deploy_contract("CathedralKlerosBridgeWithVoting", vea_relay_address, rbb_target_address, oracle_address)

    print("Deployment completed successfully.")

if __name__ == "__main__":
    main()
