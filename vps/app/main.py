from fastapi import FastAPI, HTTPException, status
import httpx
import os

app = FastAPI(title="VPS - API Proxy")

# Endereço interno do server2 e credenciais
SERVER2_URL = os.getenv("SERVER2_URL", "https://192.168.100.2:8080")
CLIENT_ID = os.getenv("CLIENT_ID", "vps_id")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "super_secret_key_123")
CERT_PATH = "/app/certs/server2.crt"


async def obter_token_oauth(client: httpx.AsyncClient) -> str:
    """Solicita um token temporário OAuth 2.0 no server2."""
    try:
        response = await client.post(
            f"{SERVER2_URL}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Falha ao autenticar com a API Privada (server2).",
            )
        return response.json().get("access_token")
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro de conexão com o server2: {exc}",
        )


@app.get("/consulta-privada")
async def consulta_privada():
    """Endpoint público acessível pela máquina real."""
    import ssl

    ssl_context = ssl.create_default_context(cafile=CERT_PATH)
    ssl_context.check_hostname = False

    async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
        # 1. Obter Token no server2
        token = await obter_token_oauth(client)

        # 2. Acessar endpoint protegido no server2
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resposta_server2 = await client.get(
                f"{SERVER2_URL}/dados-privados", headers=headers
            )

            if resposta_server2.status_code != 200:
                raise HTTPException(
                    status_code=resposta_server2.status_code,
                    detail="server2 recusou a requisição dos dados.",
                )

            return {
                "mensagem": "Dados obtidos com sucesso do server2!",
                "origem": "VPS (Proxy)",
                "dados_server2": resposta_server2.json(),
            }
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erro na comunicação com o server2: {exc}",
            )