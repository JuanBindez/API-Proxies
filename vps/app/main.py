from fastapi import FastAPI, HTTPException, status
import httpx
import os

app = FastAPI(title="Servidor 1 - Proxy / BFF")

# Endereços e configurações do Servidor 2 (API Privada)
SERVIDOR2_URL = os.getenv("SERVIDOR2_URL", "https://192.168.100.2:8080")
CLIENT_ID = os.getenv("CLIENT_ID", "servidor1_id")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "super_secret_key_123")
CERT_PATH = "/app/certs/servidor2.crt"


async def obter_token_oauth(client: httpx.AsyncClient) -> str:
    """Solicita um token temporário OAuth 2.0 no Servidor 2."""
    try:
        response = await client.post(
            f"{SERVIDOR2_URL}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Falha ao autenticar com a API Privada (Servidor 2).",
            )
        return response.json().get("access_token")
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de conexão com o Servidor 2: {exc}",
        )


@app.get("/consulta-privada")
async def consulta_privada():
    """Endpoint público acessível pela sua máquina real.

    Atua como Proxy/BFF redirecionando para o Servidor 2.
    """
    # Cria o cliente HTTP configurado para confiar no certificado SSL do Servidor 2
    async with httpx.AsyncClient(verify=CERT_PATH, timeout=10.0) as client:
        # Step 1: Obter Token temporário
        token = await obter_token_oauth(client)

        # Step 2: Fazer a requisição à API privada usando o token
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resposta_servidor2 = await client.get(
                f"{SERVIDOR2_URL}/dados-privados", headers=headers
            )

            if resposta_servidor2.status_code != 200:
                raise HTTPException(
                    status_code=resposta_servidor2.status_code,
                    detail="Servidor 2 recusou a requisição dos dados.",
                )

            # Retorna a resposta tratada para a sua máquina real
            return {
                "mensagem": "Dados obtidos com sucesso do Servidor 2!",
                "origem": "Servidor 1 (Proxy)",
                "dados_servidor2": resposta_servidor2.json(),
            }
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erro na comunicação com o Servidor 2: {exc}",
            )