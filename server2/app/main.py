from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

app = FastAPI(title="server2 - API Privada")

SECRET_KEY = "chave_de_assinatura_super_secreta_do_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

VALID_CLIENT_ID = "vps_id"
VALID_CLIENT_SECRET = "super_secret_key_123"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth/token")


def criar_token_jwt(data: dict) -> str:
  dados = data.copy()
  exp = datetime.now(timezone.utc) + timedelta(
      minutes=ACCESS_TOKEN_EXPIRE_MINUTES
  )
  dados.update({"exp": exp})
  return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)


async def verificar_token(token: str = Depends(oauth2_scheme)):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    cliente: str = payload.get("sub")
    if cliente is None:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
      )
    return cliente
  except JWTError:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expirado ou inválido",
    )


@app.post("/oauth/token")
async def login_for_access_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
  if (
      grant_type != "client_credentials"
      or client_id != VALID_CLIENT_ID
      or client_secret != VALID_CLIENT_SECRET
  ):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
    )

  token = criar_token_jwt(data={"sub": client_id})
  return {"access_token": token, "token_type": "bearer"}


@app.get("/dados-privados")
async def obter_dados_privados(cliente: str = Depends(verificar_token)):
  return {
      "status": "Sucesso",
      "mensagem": "Acesso autorizado na API privada!",
      "cliente": cliente,
      "dados": {"servidor": "server2", "ambiente": "rede_restrita"},
  }