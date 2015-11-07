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
    print("EUI: %s %s - %s: %s" % (data['DevEUI'],
                                   data['Time'],
                                   data['FPort'],
                                   data['payload_hex']
                                   ))
    s.write(dict(x=data['Time'], y= int(data['payload_hex'],16)))
    #print("michi does something :D")


def start_listener():
    channel = connection.channel()
    channel.exchange_declare(exchange='data_log', type='fanout')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='data_log',
                       queue=queue_name)

    print('listener started')

    channel.basic_consume(receive_new_message,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()


if __name__ == "__main__":
    port = os.getenv('VCAP_APP_PORT', '5000')

    print("############################################")
    print("STARTING")
    print("############################################")

    p = py.sign_in('vosermi', 'newpassword')
    trace1 = gobj.Scatter(
            x=[],
            y=[],
            stream=dict(token='newpassword')
        )
    data = gobj.Data([trace1])
    py.plot(data)
    s = py.Stream('newpassword')
    s.open()

    connection = pika.BlockingConnection(get_pika_params())
    thread = threading.Thread(target=start_listener)
    thread.setDaemon(True)
    thread.start()

    app.run(host='0.0.0.0', port=int(port))
