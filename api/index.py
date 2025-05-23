import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request
import requests
import copy
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("host")
DB_NAME = os.getenv("dbname")
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_PORT = os.getenv("port", "5432")
GOOGLE_API_KEY = os.getenv("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY")

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "https://cooperzagati.vercel.app"
])

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def format_address(p):
    return f"{p['address']}, {p['number']} - {p['neighborhood']}, {p['city']} - {p['state']}"

def get_google_distance(origem, destino):
    print('Johny Deep')
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": origem,
            "destination": destino,
            "key": GOOGLE_API_KEY
        }
        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == 'OK':
            leg = data['routes'][0]['legs'][0]
            distancia_km = leg['distance']['value'] / 1000
            tempo_min = leg['duration']['value'] / 60
            return distancia_km, tempo_min
    except Exception as e:
        print(f"Erro na API do Google: {e}")
    return None, None

@app.route('/gerar-matriz', methods=['POST'])
def gerar_matriz():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT id, name, address, number, neighborhood, city, state, capacity_kg FROM collection_points")
        pontos = cur.fetchall()

        inseridos = 0
        ignorados = 0

        for origem in pontos:
            for destino in pontos:
                if origem['id'] == destino['id']:
                    continue

                cur.execute("""
                    SELECT 1 FROM collection_routes_matrix
                    WHERE origem_id = %s AND destino_id = %s
                """, (origem['id'], destino['id']))
                if cur.fetchone():
                    ignorados += 1
                else:

                    if origem['id'] == 'ddc0d879-58ae-499b-b9eb-aad1671dd26c':
                        print('Hanna Montana')
                    origem_str = format_address(origem)
                    destino_str = format_address(destino)
                    distancia_km, tempo_min = get_google_distance(origem_str, destino_str)
                    if distancia_km is None or tempo_min is None:
                        continue

                    cur.execute("""
                        INSERT INTO collection_routes_matrix (origem_id, destino_id, distancia_km, tempo_min, material_estimado_kg)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        origem['id'],
                        destino['id'],
                        distancia_km,
                        tempo_min,
                        destino['capacity_kg'] or 0
                    ))
                    inseridos += 1

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "mensagem": "Matriz gerada com sucesso.",
            "inseridos": inseridos,
            "ignorados": ignorados,
            "total_pares": inseridos + ignorados
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

DIESEL_PRICE_PER_LITER = 6.14
COOPER_ID = 'ddc0d879-58ae-499b-b9eb-aad1671dd26c'

def calcular_viagens(ponto_ids, matriz, pontos_dict, capacidade, consumo_lkm):
    material_restante = {pid: pontos_dict[pid]['capacity_kg'] for pid in ponto_ids}
    viagens = []
    ordem = 1

    while any(material_restante[pid] > 0 for pid in ponto_ids):
        viagem = {
            "ordem": ordem,
            "pontos_visitados": [],
            "distancia_km": 0.0,
            "duracao_min": 0.0,
            "retorno": True
        }
        atual = COOPER_ID
        capacidade_restante = capacidade

        while capacidade_restante > 0:
            melhor_ponto = None
            melhor_match = None
            menor_custo = float('inf')

            for pid in ponto_ids:
                if material_restante[pid] <= 0:
                    continue
                match = next((r for r in matriz if r['origem_id'] == atual and r['destino_id'] == pid), None)
                if match:
                    estimado = min(material_restante[pid], capacidade_restante)
                    custo = float(match['distancia_km']) * consumo_lkm
                    if custo < menor_custo:
                        menor_custo = custo
                        melhor_ponto = pid
                        melhor_match = match

            if melhor_ponto is None:
                break

            coletado = min(material_restante[melhor_ponto], capacidade_restante)
            viagem["pontos_visitados"].append({
                "id": melhor_ponto,
                "coletado_kg": coletado,
                "distancia_km": float(melhor_match['distancia_km']),
                "duracao_min": float(melhor_match['tempo_min'])
            })
            viagem["distancia_km"] += float(melhor_match['distancia_km'])
            viagem["duracao_min"] += float(melhor_match['tempo_min'])
            capacidade_restante -= coletado
            material_restante[melhor_ponto] -= coletado
            atual = melhor_ponto

        retorno = next((r for r in matriz if r['origem_id'] == atual and r['destino_id'] == COOPER_ID), None)
        if retorno:
            viagem["distancia_km"] += float(retorno['distancia_km'])
            viagem["duracao_min"] += float(retorno['tempo_min'])

        viagens.append(viagem)
        ordem += 1

    return viagens

@app.route('/gerar-rota', methods=['POST'])
def gerar_rota():
    data = request.get_json()
    ponto_ids = data.get("ponto_ids")
    truck_id = data.get("truck_id")

    if not ponto_ids or not truck_id:
        return jsonify({"error": "ponto_ids e truck_id são obrigatórios"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    all_ids = [COOPER_ID] + ponto_ids
    placeholders = ','.join(['%s'] * len(all_ids))
    cur.execute(f"SELECT * FROM collection_points WHERE id IN ({placeholders})", all_ids)
    pontos = cur.fetchall()
    pontos_dict = {p['id']: p for p in pontos}

    cur.execute(f"""
        SELECT * FROM collection_routes_matrix
        WHERE origem_id IN ({placeholders}) AND destino_id IN ({placeholders})
    """, all_ids + all_ids)
    matriz = cur.fetchall()

    cur.execute("SELECT * FROM trucks WHERE id = %s", (truck_id,))
    caminhao = cur.fetchone()
    cur.close()
    conn.close()

    if not caminhao:
        return jsonify({"error": "Caminhão não encontrado"}), 404

    capacidade = caminhao['capacity_kg']
    consumo_lkm = float(caminhao['liter_per_kilometer'])

    viagens = calcular_viagens(ponto_ids, matriz, pontos_dict, capacidade, consumo_lkm)

    total_material = sum(sum(pv['coletado_kg'] for pv in v['pontos_visitados']) for v in viagens)
    total_distancia = sum(v['distancia_km'] for v in viagens)
    total_duracao = sum(v['duracao_min'] for v in viagens)
    litros_gastos = total_distancia * consumo_lkm
    custo_estimado = litros_gastos * DIESEL_PRICE_PER_LITER

    return jsonify({
        "viagens": viagens,
        "resumo": {
            "quantidade_viagens": len(viagens),
            "material_total_kg": round(total_material, 2),
            "distancia_total_km": round(total_distancia, 2),
            "tempo_estimado_min": round(total_duracao),
            "litros_estimados": round(litros_gastos, 2),
            "custo_estimado_reais": round(custo_estimado, 2),
            "capacidade_kg": capacidade,
            "caminhao_id": truck_id
        }
    })
