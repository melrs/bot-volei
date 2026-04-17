import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

HORARIOS_MONITORADOS = {
    0: ("17:00", "20:00"),
    2: ("17:00", "22:00"),
    5: ("08:00", "20:00"),
}

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DICIONARIO_DIAS = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo"
}

def hora_para_minutos(hora_str):
    h, m = map(int, hora_str.split(":"))
    return h * 60 + m

def dentro_do_intervalo(hora_str, dia):
    if dia not in HORARIOS_MONITORADOS:
        return False

    inicio_str, fim_str = HORARIOS_MONITORADOS[dia]

    minutos = hora_para_minutos(hora_str)
    inicio = hora_para_minutos(inicio_str)

    if fim_str:
        fim = hora_para_minutos(fim_str)
        return inicio <= minutos <= fim
    else:
        return minutos >= inicio
    
def dia_da_semana(data_str):
    data = datetime.strptime(data_str, "%d/%m/%Y")
    return data.weekday()

def get_url():
    hoje = datetime.now().strftime("%Y-%m-%d")

    return f"https://api-reservadeespaco.curitiba.pr.gov.br/api/v1/espacos-fisicos/questionario/resultado?AtividadeId=21&NucleoId=1&EquipamentoUrbanoId=5549&PesquisarProximos=true&QuantidadePessoas=10&DataReferencia={hoje}&Pagina=1&QuantidadeResultados=1"

def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Telegram não configurado:", msg)
        return

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

def checar():
    url = get_url()
    url_reserva = "https://reservadeespaco-curitibaemmovimento.curitiba.pr.gov.br/questionario"
    print("🔗 URL:", url)

    res = requests.get(url)
    agendas = res.json()["data"][0]["agendas"]
    msg = None

    for agenda in agendas:
        dia = dia_da_semana(agenda["data"])

        if dia not in HORARIOS_MONITORADOS:
            continue
        horas_map = {}
        for h in agenda["horas"]:
            horas_map.setdefault(h["hora"], []).append(h["disponivel"])

        for hora, lista in horas_map.items():
            if dentro_do_intervalo(hora, dia) and any(lista):
                msg = f"✅ {DICIONARIO_DIAS[dia]} - {agenda['data']} às {hora}"
                print(msg)
                enviar_telegram(msg)
            else:
                print(f"❌ Indisponível: {DICIONARIO_DIAS[dia]} {agenda['data']} {hora}")
    if msg:
        enviar_telegram(f"🔗 Link: {url_reserva}")

if __name__ == "__main__":
    checar()