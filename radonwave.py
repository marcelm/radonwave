#!/usr/bin/env python3
import sys
import time
from struct import unpack
from bluepy import btle
import time
from argparse import ArgumentParser
import json


class CouldNotConnectError(Exception):
    pass


class Measurement:
    def __init__(self, humidity, temperature, radon_avg, radon_1day, accel, brightness, humidity2):
        self.humidity = humidity
        self.temperature = temperature
        self.radon_avg = radon_avg
        self.radon_1day = radon_1day
        self.accel = accel
        self.brightness = brightness
        self.humidity2 = humidity2


def connect_and_read(device_address):
    try:
        dev = btle.Peripheral(device_address)
    except btle.BTLEException as e:
        raise CouldNotConnectError()

    if False:
        print('Services')
        for service in dev.services:
            print(service)

        print('Characteristics')
        for ch in dev.getCharacteristics():
            print(ch.getHandle(), ch.uuid, ch.propertiesToString())

    service = dev.getServiceByUUID(btle.UUID('b42e1f6e-ade7-11e4-89d3-123b93f75cba'))

    temperature = humidity = radon_avg = radon_1day = accel = brightness = humidity2 = None
    for ch in service.getCharacteristics():
        name = ch.uuid.getCommonName()
        if name == 'Temperature':
            value = unpack('h', ch.read())[0]
            temperature = value / 100
        elif name == 'Humidity':
            value = unpack('h', ch.read())[0]
            humidity = value/100
        elif name == 'b42e0a4c-ade7-11e4-89d3-123b93f75cba':
            # Description: 'Radon conc. avg.'
            value = unpack('h', ch.read())[0]
            radon_avg = value
        elif name == 'b42e01aa-ade7-11e4-89d3-123b93f75cba':
            # Description: 'Radon conc. 1 day'
            value = unpack('h', ch.read())[0]
            radon_1day = value
        elif name == 'b42e1096-ade7-11e4-89d3-123b93f75cba':
            # Description: 'Accel. Light 5m'
            brightness, accel = unpack('BB', ch.read())
        elif name == 'b42e1348-ade7-11e4-89d3-123b93f75cba':
            # Description: 'Status info'
            # Seems to be identical to humidity
            humidity2 = unpack('h', ch.read())[0] / 100
    dev.disconnect()
    return Measurement(humidity=humidity, temperature=temperature,
        radon_avg=radon_avg, radon_1day=radon_1day, accel=accel,
        brightness=brightness, humidity2=humidity2)


def main():
    parser = ArgumentParser()
    parser.add_argument('--wait', default=1200, type=int,
        help='Seconds to wait between queries. Do not choose this too low as the '
        'radon levels are only updated once every 60 minutes. Set to 0 to query '
        'only once. Default: 1200 '
        '(20 minutes)')
    parser.add_argument('--mqtt', help='MQTT server')
    parser.add_argument('--topic', help='MQTT topic')
    parser.add_argument('--username', help='MQTT user name')
    parser.add_argument('--password', help='MQTT password. Ignored if no username given.')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port. Default: %(default)s')
    parser.add_argument('device_address', metavar='BLUETOOTH-DEVICE-ADDRESS')
    args = parser.parse_args()
    device_address = args.device_address

    if args.mqtt and not args.topic:
        parser.error('Provide also a --topic when you use --mqtt')
    if args.mqtt:
        try:
            import paho.mqtt.client as mqtt
            client = mqtt.Client()
            if args.username:
                client.username_pw_set(args.username, password=args.password)
            client.connect(args.mqtt, port=args.port)
            assert client
        except Exception as e:  # unsure which exceptions connect can cause, so need to catch everything
            print('Could not connect to MQTT broker:', e, file=sys.stderr)
            client = None
    else:
        client = None
    while True:
        try:
            measurement = connect_and_read(device_address)
        except CouldNotConnectError:
            print('Could not connect', file=sys.stderr)
        except btle.BTLEException as e:
            print('Bluetooth error:', e, file=sys.stderr)
        else:  # no exception occurred
            print('{time}\t{temperature:.2f}\t{humidity:.2f}\t{radon_avg}\t{radon_1day}\t{brightness}\t{accel:02X}'.format(
                time=time.strftime('%Y-%m-%d %H:%M:%S'),
                **vars(measurement)
                ), sep='\t')
            sys.stdout.flush()
            if client:
                data = {
                    'temperature': measurement.temperature,
                    'humidity': measurement.humidity,
                    'radon': measurement.radon_1day,
                    'brightness': measurement.brightness,
                }
                client.publish(args.topic, json.dumps(data))
        if args.wait == 0:
            break
        time.sleep(args.wait)
    if client:
        client.disconnect()


if __name__ == '__main__':
    main()
