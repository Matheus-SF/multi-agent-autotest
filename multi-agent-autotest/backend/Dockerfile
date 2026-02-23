FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para o Docker-in-Docker
# (o backend precisa chamar o Docker para spawnar o sandbox)
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do backend
COPY . .

# Expõe a porta do uvicorn
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]