import json
import os
import threading

import pika
from flask import Flask
import plotly.plotly as py
import plotly.graph_objs.graph_objs as gobj

app = Flask(__name__)


@app.route("/ping")
def hello():
    return "pong"


def get_pika_params():
    if 'VCAP_SERVICES' in os.environ:
        vcap_service = json.loads(os.environ['VCAP_SERVICES'])

        return pika.URLParameters(url=vcap_service['rabbitmq'][0]['credentials']['uri'])

    return pika.ConnectionParameters(host="localhost")


def receive_new_message(ch, method, properties, body):
    data = json.loads(body)
    print("EUI: %s %s - %s: %s" % (data['eui'],
                                   data['timestamp'],
                                   data['data_type'],
                                   data['payload_int']
                                   ))
    s.write(dict(x=data['timestamp'], y=data['payload_int']))


def start_listener():
    channel = connection.channel()
    channel.exchange_declare(exchange='data_log', type='fanout')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='data',
                       queue=queue_name)

    print('listener started')

    channel.basic_consume(receive_new_message,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()


if __name__ == "__main__":
    port = os.getenv('VCAP_APP_PORT', '5000')
    username = os.getenv('plotly_username')
    api_key = os.getenv('plotly_api_key')
    stream_token = os.getenv('plotly_stream_token')

    print("############################################")
    print("STARTING")
    print("############################################")

    p = py.sign_in(username,api_key)
    trace1 = gobj.Scatter(
            x=[],
            y=[],
            stream=dict(token=stream_token)
        )
    data = gobj.Data([trace1])
    print py.plot(data)
    s = py.Stream(stream_token)
    s.open()

    connection = pika.BlockingConnection(get_pika_params())
    thread = threading.Thread(target=start_listener)
    thread.setDaemon(True)
    thread.start()

    app.run(host='0.0.0.0', port=int(port))
