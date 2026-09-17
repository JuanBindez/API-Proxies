from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

app = FastAPI(title="server2 - API Privada")

# Configurações de Segurança e OAuth 2.0
SECRET_KEY = "chave_de_assinatura_super_secreta_do_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

# Credenciais do cliente cadastrado (vps)
VALID_CLIENT_ID = "vps_id"
VALID_CLIENT_SECRET = "super_secret_key_123"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth/token")


def criar_token_jwt(data: dict) -> str:
    dados_para_codificar = data.copy()
    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    dados_para_codificar.update({"exp": expiracao})
    return jwt.encode(dados_para_codificar, SECRET_KEY, algorithm=ALGORITHM)


async def verificar_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        cliente: str = payload.get("sub")
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        return cliente
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED detail="Token expirado ou inválido"
        )


@app.post("/oauth/token")
async def login_for_access_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    """Endpoint que gera o Token JWT para o vps."""
    if (
        grant_type != "client_credentials"
        or client_id != VALID_CLIENT_ID
        or client_secret != VALID_CLIENT_SECRET
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou grant_type incorreto",
        )

    access_token = criar_token_jwt(data={"sub": client_id})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/dados-privados")
async def obter_dados_privados(cliente: str = Depends(verificar_token)):
    """Endpoint ultra restrito que apenas o vps acessa com o token."""
    return {
        "status": "Sucesso",
        "mensagem": "Você acessou a API privada com sucesso!",
        "autorizado_para": cliente,
        "dados_sensiveis": {
            "servidor": "server2",
            "ambiente": "rede_privada_interna",
        },
    }