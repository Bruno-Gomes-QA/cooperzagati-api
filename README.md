# ♻️ Cooperzagati API

A API da plataforma **Cooperzagati** é responsável por toda a lógica de otimização de rotas, geração de matrizes de distância e integração com serviços externos, como o Google Maps. Criada para dar suporte à logística de coleta seletiva da cooperativa de Taboão da Serra, esta aplicação facilita a organização e execução das coletas de recicláveis.

---

## 🚀 Tecnologias

- Python 3.12
- Flask 3
- PostgreSQL + PostGIS
- psycopg2
- dotenv
- Google Maps Directions API
- Vercel Serverless Functions

---

## 📦 Instalação Local

```bash
git clone https://github.com/seu-usuario/cooperzagati-api.git
cd cooperzagati-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crie o arquivo `.env` com as variáveis:

```
host=<SEU_HOST>
dbname=<SEU_DB>
user=<SEU_USUARIO>
password=<SUA_SENHA>
port=5432
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<SUA_CHAVE_GOOGLE>
```

Para rodar localmente:

```bash
vercel dev
```

---

## 📌 Endpoints

### 🔄 `POST /gerar-matriz`

Gera a matriz de distância entre todos os pontos cadastrados.

#### 📥 Corpo da requisição
Sem parâmetros.

#### 🧠 O que faz:
- Busca todos os pontos de coleta.
- Para cada par (origem → destino), calcula tempo e distância via Google.
- Salva no banco a relação `origem_id`, `destino_id`, `distancia_km`, `tempo_min`, `material_estimado_kg`.

---

### 📍 `POST /gerar-rota`

Calcula a melhor rota de coleta com base em:

- Pontos selecionados
- Capacidade do caminhão
- Consumo por km

#### 📥 Corpo da requisição

```json
{
  "truck_id": "uuid-do-caminhao",
  "ponto_ids": [
    "uuid-do-ponto1",
    "uuid-do-ponto2",
    "..."
  ]
}
```

#### 📤 Resposta

```json
{
  "rota": [
    {
      "ponto_id": "uuid",
      "material_estimado_kg": 1000,
      "distancia_km": 3.2,
      "duracao_min": 12,
      "retorno": false
    },
    ...
  ],
  "resumo": {
    "material_total_kg": 4000,
    "distancia_total_km": 10.5,
    "tempo_estimado_min": 40,
    "litros_estimados": 2.5,
    "custo_estimado_reais": 15.75,
    "capacidade_utilizada_percent": 80.0,
    "pontos_nao_visitados": []
  }
}
```

---

## 🛠️ Funcionalidades

- 🔄 Geração da matriz de rotas
- 📦 Cálculo da rota ideal
- ⛽ Cálculo de consumo de diesel e custo
- 📍 Identificação de pontos não visitados por falta de capacidade
- 🧭 Inclusão explícita do retorno à cooperativa na rota

---

## 🤝 Contribuindo

1. Faça um fork
2. Crie uma branch: `git checkout -b minha-feature`
3. Commit: `git commit -m 'Minha feature'`
4. Push: `git push origin minha-feature`
5. Abra um Pull Request

---

## 📄 Licença

Este projeto é open-source sob a licença MIT.

---

💚 Feito com propósito: transformar a reciclagem em uma prática mais inteligente, tecnológica e acessível.