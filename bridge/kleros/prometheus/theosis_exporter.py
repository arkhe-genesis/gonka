import os
import time
import json
from prometheus_client import start_http_server, Gauge
from web3 import Web3

# Configuration
RPC_URL = os.getenv("ARBITRUM_RPC_URL", "http://127.0.0.1:8545")
ORACLE_ADDRESS = os.getenv("ORACLE_ADDRESS", "0x0000000000000000000000000000000000000000")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))

# Load ABI (Assuming artifact is built)
ARTIFACT_PATH = "bridge/kleros/artifacts/bridge/kleros/contracts/PNKTheosisOracle.sol/PNKTheosisOracle.json"

# Metrics
theosis_metric = Gauge('kleros_juror_theosis_score', 'Theosis score of a qualified Kleros juror', ['juror_address'])

def get_contract(w3):
    try:
        with open(ARTIFACT_PATH, "r") as f:
            artifact = json.load(f)
        return w3.eth.contract(address=w3.to_checksum_address(ORACLE_ADDRESS), abi=artifact["abi"])
    except Exception as e:
        print(f"Error loading contract: {e}")
        return None

def main():
    print(f"Starting Theosis Exporter...")
    print(f"Target RPC: {RPC_URL}")
    print(f"Oracle Address: {ORACLE_ADDRESS}")

    start_http_server(8000)
    print("Prometheus metrics available on port 8000")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("Failed to connect to RPC")
        return

    contract = get_contract(w3)
    if not contract:
        return

    # In a real scenario, you might listen to events or have a list of jurors to poll.
    # Here we mock a list of known jurors.
    known_jurors = [
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", # Default Hardhat Account 0
        "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", # Default Hardhat Account 1
    ]

    while True:
        for juror in known_jurors:
            try:
                score = contract.functions.getJurorTheosis(w3.to_checksum_address(juror)).call()
                theosis_metric.labels(juror_address=juror).set(score)
            except Exception as e:
                print(f"Error fetching theosis for {juror}: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
