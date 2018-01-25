#!/usr/bin/env python3
import sys
import time
from struct import unpack
from bluepy import btle


def main():
	if len(sys.argv) != 2:
		print('Error: Need Bluetooth device address as parameter')
		sys.exit(1)
	device_address = sys.argv[1]
	try:
		dev = btle.Peripheral(device_address)
	except btle.BTLEException as e:
		print('Could not connect', file=sys.stderr)
		sys.exit(1)

	# Humidity: 00002a6f-0000-1000-8000-00805f9b34fb
	# Temperature: ...
	# Radon conc. average: b42e0a4c-ade7-11e4-89d3-123b93f75cba
	# Radon conc. 1 day: b42e01aa-ade7-11e4-89d3-123b93f75cba

	if False:
		print('Services')
		for service in dev.services:
			print(service)

		print('Characteristics')
		for ch in dev.getCharacteristics():
			print(ch.getHandle(), ch.uuid, ch.propertiesToString())

	service = dev.getServiceByUUID(btle.UUID('b42e1f6e-ade7-11e4-89d3-123b93f75cba'))

	temperature = humidity = radon_avg = radon_1day = accel = humidity2 = None
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
			accel = unpack('H', ch.read())[0]
		elif name == 'b42e1348-ade7-11e4-89d3-123b93f75cba':
			# Description: 'Status info'
			# Seems to be identical to humidity
			humidity2 = unpack('h', ch.read())[0] / 100

	print('{time}\t{temperature:.2f}\t{humidity:.2f}\t{radon_avg}\t{radon_1day}\t{accel:04X}\t{humidity2:.2f}'.format(
			time=time.strftime('%Y-%m-%d %H:%M:%S'),
			temperature=temperature,
			humidity=humidity,
			radon_avg=radon_avg,
			radon_1day=radon_1day,
			accel=accel,
			humidity2=humidity2),
		sep='\t')

	dev.disconnect()


if __name__ == '__main__':
	main()
