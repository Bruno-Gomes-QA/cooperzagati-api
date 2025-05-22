curl -X POST http://localhost:3000/gerar-rota \
  -H "Content-Type: application/json" \
  -d '{
    "truck_id": "ac998938-f13b-4abe-a751-ade3e4798722",
    "ponto_ids": [
      "083dd700-5bc7-4c68-8a5d-92ef7bf34842",
      "94b96e00-155c-4d14-8896-e35077ff7af6",
      "7c71f0c1-8bf8-4ebc-9358-cbf9ac1b073c"
    ]
  }'