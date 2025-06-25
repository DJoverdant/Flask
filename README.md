# <p align="center"> Sistema de Monitoramento IoT com Flask + MQTT + SQLite3 </p>

## 🧠 **Objetivo do Projeto**

Este projeto tem como **principal objetivo monitorar sensores de umidade e gás em tempo real**, além de permitir **controlar dois atuadores**: um **buzzer (emissor de som)** e um **servo motor (motor de rotação controlada)**.

A comunicação entre os dispositivos (sensores e atuadores) é feita usando o **protocolo MQTT**, e os dados são armazenados em um **banco de dados SQLite** para manter um **histórico de leituras e comandos**.

O sistema conta com uma **interface web simples** para visualizar dados e controlar os atuadores.

## 🧩 Como executar

### Requerimentos
```cmd
pip install flask
pip install paho-mqtt
pip install pysqlite3
```

### 💾 Banco de dados
Execute `db.py` para criar o banco de dados `dados.db`. 
Ele deve conter **duas tabelas**:

#### Tabela `sensores`

| timestamp   | tipo             | valor          |
| ----------- | ---------------- | -------------- |
| Data e hora | "gas"/"humidade" | Valor numérico |

#### Tabela `atuadores`

| timestamp   | dispositivo      | comando                     |
| ----------- | ---------------- | --------------------------- |
| Data e hora | "buzzer"/"servo" | Texto com o comando enviado |

Após isto, execute `app.py` para começar a rodar o site e **abra o ip localhost**:

![image](https://github.com/user-attachments/assets/97ecda6d-320b-484e-afa8-90a2cf83568b)


Então, em um simulador (como o Wokwi) ou em uma Esp32 real execute o código em micropython:

```python
from machine import Pin, PWM, ADC
from umqtt.simple import MQTTClient
import network
import dht
from time import sleep

# MQTT
MQTT_CLIENT_ID = "DJoverdant191919"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_USER      = "" 
MQTT_PASSWORD  = ""
TOPICO_SERVO   = b'André/servo'
TOPICO_BUZZER  = b'André/buzzer'
TOPICO_GAS     = b'André/gas'
TOPICO_UMID    = b'André/humidade'

# Alarme (buzzer)
buzzer_pin = Pin(17, Pin.OUT)
buzzer = PWM(buzzer_pin)
buzzer.duty(0)  # Inicia desligado pra n estourar meu timpano

# Sensor DHT22
sensor = dht.DHT22(Pin(14))

# Sensor de Gás MQ2
mq2 = ADC(Pin(32))
mq2.atten(ADC.ATTN_11DB)

# Servo Motor
servo = PWM(Pin(26), freq=50)

# Função para controle do buzzer
def alert(freq, volume):
    try:
        freq = int(freq)
        volume = int(volume)
        
        if freq == 0:
            freq = 1
        
        buzzer.freq(freq)
        buzzer.duty(volume)
    except:
        print("Erro nos parâmetros do buzzer.")

# Conversão de ângulo para servo motor
def set_angle(angle):
    try:
        angle = int(angle)
        duty = int((angle / 180) * 75 + 40)
        servo.duty(duty)
    except:
        print("Erro no ângulo do servo.")

# Recebe msg do mqtt
def callback(topic, msg):
    msg_str = msg.decode()

    print(f"[MQTT] Mensagem recebida no tópico {topic.decode()}: {msg_str}")

    if topic == TOPICO_SERVO:
        # Int entre 0 e 180
        set_angle(msg_str)

    elif topic == TOPICO_BUZZER:
        # "freq,volume"
        try:
            freq, vol = msg_str.split(",")
            alert(freq, vol)
        except:
            print("Formato inválido para buzzer.")

# Conexão WiFi
print("Conectando ao Wi-Fi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
    print(".", end="")
    sleep(0.1)
print(" Conectado!")

# Conexão MQTT
print("Conectando ao broker MQTT...", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)
client.set_callback(callback)
client.connect()
client.subscribe(TOPICO_SERVO)
client.subscribe(TOPICO_BUZZER)
print(" Conectado ao broker!")

# Loop principal
while True:

    # Verifica mensagens recebidas
    client.check_msg()

    # Le ai pai
    sensor.measure()
    umidade = sensor.humidity()
    gas = mq2.read()

    # Publica os dados diretamente no site
    client.publish(TOPICO_UMID, str(umidade))
    client.publish(TOPICO_GAS, str(gas))

    print(f"[MQTT] Publicado: umidade={umidade} | gas={gas}")
    sleep(5)
```

---





