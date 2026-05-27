#!/usr/bin/env python3
"""
CLI ARKHE Chat — Interação local com o modelo ARKHE-OS via llama.cpp server.
Uso: python arkhe_chat.py
"""

import sys
import json
import urllib.request
import urllib.error

# Configuração do endpoint do llama.cpp server
SERVER_URL = "http://localhost:8080/completion"

def query_model(prompt: str) -> str:
    """Envia o prompt para a API do llama.cpp e retorna a resposta."""
    data = {
        "prompt": prompt,
        "n_predict": 128,
        "temperature": 0.7,
        "stop": ["\nUser:", "User:", " ARKHE:"]
    }

    req = urllib.request.Request(
        SERVER_URL,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("content", "").strip()
    except urllib.error.URLError as e:
        print(f"\n[Erro] Falha ao conectar ao servidor ARKHE-OS em {SERVER_URL}: {e}")
        print("Certifique-se de que o llama.cpp server está rodando.")
        sys.exit(1)

def main():
    print("=========================================================")
    print(" ARKHE CLI Chat — Substrato 889.4 • ARKHE Cathedral")
    print("=========================================================")
    print("Digite 'sair' ou 'exit' para encerrar a sessão.\n")

    while True:
        try:
            user_input = input("User: ")
            if user_input.strip().lower() in ["sair", "exit", "quit"]:
                print("Encerrando sessão ARKHE.")
                break

            if not user_input.strip():
                continue

            # Adiciona formatação básica de chat no prompt
            prompt = f"User: {user_input}\nARKHE:"

            # Chama a API
            response = query_model(prompt)
            print(f"ARKHE: {response}\n")

        except KeyboardInterrupt:
            print("\nEncerrando sessão ARKHE.")
            break
        except Exception as e:
            print(f"\n[Erro inesperado]: {e}")

if __name__ == "__main__":
    main()