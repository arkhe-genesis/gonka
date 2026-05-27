# Usando uma imagem base leve, já com python, ou ubuntu para instalar llama.cpp
FROM ubuntu:22.04

# Instalar dependências necessárias para buildar o llama.cpp
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Clonar e buildar llama.cpp (server)
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    make llama-server

# Expor a porta que o llama.cpp server usa por padrão
EXPOSE 8080

# Copiar o modelo gguf (assumindo que já foi convertido e está na raiz do contexto)
# NOTA: O modelo precisará ser copiado ou montado via volume ao rodar o container
# COPY arkhe-os.gguf /app/arkhe-os.gguf

# Configurar o entrypoint para rodar o servidor
# Por padrão, vamos apontar para o modelo montado ou copiado
ENTRYPOINT ["/app/llama.cpp/llama-server"]
CMD ["-m", "/app/arkhe-os.gguf", "--host", "0.0.0.0", "--port", "8080"]