from flask import Flask, render_template_string, request, redirect, url_for
import threading
import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
from time import sleep

app = Flask(__name__)

# Globais
sensor_data = {
    'humidade': '',
    'gas': ''
}

# MQTT
MQTT_BROKER = 'broker.mqttdashboard.com' 
MQTT_PORT = 1883
TOPICOS_SUB = ['André/humidade', 'André/gas']
TOPICOS_PUB = {
    'buzzer': 'André/buzzer',
    'servo': 'André/servo'
}

# Inicializa o cliente MQTT
client = mqtt.Client()

#Salva no dados.db
def salvar_sensor(tipo, valor):
    with sqlite3.connect("dados.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO sensores (timestamp, tipo, valor) VALUES (?, ?, ?)", (data, tipo, valor))
        conn.commit()

def salvar_atuador(dispositivo, comando):
    with sqlite3.connect("dados.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO atuadores (timestamp, dispositivo, comando) VALUES (?, ?, ?)", (data, dispositivo, comando))
        conn.commit()

# Callback
def on_connect(client, userdata, flags, rc):
    print(f'Conectado ao broker MQTT com código: {rc}')
    for topico in TOPICOS_SUB:
        client.subscribe(topico)
        print(f'Subscrito ao tópico: {topico}')

# Callback de recebimento de mensagens
def on_message(client, userdata, msg):
    
    payload = msg.payload.decode()
    print(f'Recebido: {msg.topic} -> {payload}')
    
    if msg.topic == 'André/humidade':
        salvar_sensor('humidade', payload)
        sensor_data['humidade'] = payload

    elif msg.topic == 'André/gas':
        salvar_sensor('gas', payload)
        sensor_data['gas'] = payload

# Inicia o loop MQTT em uma thread separada
def mqtt_loop():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# Thread para o MQTT
mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

# Página principal
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head><title>Monitoramento</title><meta http-equiv="refresh" content="60"></head>
<body>
    <p>Umidade: {{ humidade }}</p>
    <p>Gás: {{ gas }}</p>

    <hr>
    <h2>Buzzer</h2>
    <form action="/buzzer" method="post">
        Frequência: <input type="number" name="frequencia" required><br>
        Volume: <input type="number" name="volume" required><br>
        <input type="submit" value="Enviar">
    </form>

    <h2>Servo</h2>
    <form action="/servo" method="post">
        Ângulo: <input type="number" name="angulo" required><br>
        <input type="submit" value="Enviar">
    </form>
    </br>

    <a href="/historico/sensores">Ver histórico de sensores</a><br>
    <a href="/historico/atuadores">Ver histórico de atuadores</a>
</body>
</html>
"""

HTML_TABELA = """
<!DOCTYPE html>
<html>
<head><title>Histórico</title></head>
<body>
    <h1>{{ titulo }}</h1>
    <table border="1">
        <tr>{% for h in cabecalho %}<th>{{ h }}</th>{% endfor %}</tr>
        {% for linha in dados %}
        <tr>{% for item in linha %}<td>{{ item }}</td>{% endfor %}</tr>
        {% endfor %}
    </table>
    <br><a href="/">Voltar</a>
</body>
</html>
"""

# Rota principal
@app.route('/')
def index():
    return render_template_string(HTML_INDEX, humidade=sensor_data['humidade'],gas=sensor_data['gas'])

# Buzzer
@app.route('/buzzer', methods=['POST'])
def controle_buzzer():
    freq = request.form.get('frequencia')
    vol = request.form.get('volume')
    mensagem = f'{freq},{vol}'
    client.publish(TOPICOS_PUB['buzzer'], mensagem)
    salvar_atuador("buzzer", mensagem)

    print(f'Comando enviado para buzzer: {mensagem}')
    return redirect(url_for('index'))

# Servo motor
@app.route('/servo', methods=['POST'])
def controle_servo():
    angulo = request.form.get('angulo')
    client.publish(TOPICOS_PUB['servo'], angulo)
    salvar_atuador("servo", angulo)

    print(f'Comando enviado para servo: {angulo}')
    return redirect(url_for('index'))

@app.route('/historico/sensores')
def historico_sensores():
    with sqlite3.connect("dados.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT timestamp, tipo, valor FROM sensores ORDER BY timestamp DESC LIMIT 20")
        dados = cur.fetchall()
        
    return render_template_string(HTML_TABELA, titulo="Histórico dos Sensores", cabecalho=["Data", "Tipo", "Valor"], dados=dados)

@app.route('/historico/atuadores')
def historico_atuadores():
    with sqlite3.connect("dados.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT timestamp, dispositivo, comando FROM atuadores ORDER BY timestamp DESC LIMIT 20")
        dados = cur.fetchall()

    return render_template_string(HTML_TABELA, titulo="Histórico dos Atuadores", cabecalho=["Data", "Dispositivo", "Comando"], dados=dados)

while True:
    data = datetime.now().strftime("%d/%m %X")
    if __name__ == '__main__':
        app.run(debug=True)
