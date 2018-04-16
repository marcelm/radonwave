# Radonwave

This tool reads the current radon level from the “Airthings Wave”
radon detector *without* using the official smartphone app.

The official app cannot export radon levels to an external file. This tool
allows you to create such a file.

**Note:** Don’t expect a finished product here. The tool and the README serve
mainly as a way to document how to interface with the Wave.


# Limitations

It may be possible that the Wave must be connected to the official app at least
once before you can use this program, so you will probably not get around
registering an account with Airthings.

The radon level history stored on the Wave itself cannot be accessed
with this program. To get around this, I run it continuously on a Raspberry Pi
that connects regularly to the radon detector.

Make sure you install the latest firmware. The Wave and also this script were
very unstable until I installed firmware from Feb. 21, 2018.

# Hardware requirements

* An Airthings Wave
* A Bluetooth adapter that supports Bluetooth Low Energy (BLE).


# Installing software requirements

You need:

* The bluez software
* Python 3
* The `bluepy` Python library

The following will install the above on Debian/Ubuntu/Raspbian (it will install
the `bluepy` Python library into a virtualenv):

    sudo apt install build-essential python3-venv python3-pip libglib2.0-dev bluez
    python3 -m venv env
    env/bin/pip install bluepy

# Running

After the above, scan for your Wave device with

    sudo hcitool lescan

This should list the device addresses of all Bluetooth devices that are nearby.
The Wave probably has a device address that starts with 98:07:2D.

It may be more comfortabe to use an app on your smartphone that can scan for
Bluetooth Low Energy devices. It doesn’t matter as long as you find out
what the device address is.

Finally, you can run the program:

    env/bin/python3 radonwave.py ADDRESS

Replace ADDRESS with the device address that you found out above.


# Notes

* The [nRF Connect app](https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp&hl=en)
  was very helpful. It allows to connect to the device via Bluetooth Low Energy (BLE)
  and browse the services that are available.
* GATT (part of Bluetooth) specifies some standard “characteristics”.
  The Wave offers the standard *temperature* and *humidity* characteristics.
  This is very easy to see in nRF Connect.
* Radon levels are reported in two different characteristics. Characteristics
  even come with proper descriptions, so this is also easy to spot from nRF
  Connect.

# Reading temperature and humidity with gatttool

```
$ sudo gatttool -I -b YOUR-DEVICE-ADDRESS
[98:07:2D:xx:yy:zz][LE]> connect
Attempting to connect to 98:07:2D:xx:yy:zz
Connection successful
[98:07:2D:xx:yy:zz][LE]> char-read-uuid 00002a6e-0000-1000-8000-00805f9b34fb
handle: 0x0022   value: 1c 07
```

The two bytes 1c and 07 were returned. To convert to temperature,
swap them (0x071c), convert to decimal (1820) and divide by 100:
The temperature is 18.2°C.

It is similar for humidity:
```
char-read-uuid 00002a6f-0000-1000-8000-00805f9b34fb
handle: 0x0026   value: 68 10
```
The value 0x1068 was returned, which is 4200 in decimal. Divide by 100
to get 42% relative humidity.

# Radon level characteristics

There are two characteristics:

* “Radon conc. average” is available by reading the characteristic b42e0a4c-ade7-11e4-89d3-123b93f75cba.
* “Radon conc. 1 day” is available by reading the characteristic b42e01aa-ade7-11e4-89d3-123b93f75cba.

That is, you can read the values with `char-read-uuid` and using the above number.
Again, two bytes are returned that need to be swapped, but they must not be
divided by 100. The unit is Bq/m³.

“Radon conc. average” is identical to the value that the app reports as current
radon level. This value is updated every 60 minutes. If you reset the Wave, a
zero is reported during the first 60 minutes. It seems that measurements are
actually even slower: When I moved the device from the basement to a place
outside the house, it took 24 hours until the value reported here had dropped
from over 500 to 17.

I am not quite sure what the value “Radon conc. 1 day” is. After a reset,
the value reported here was identical to the “Radon conc. average” value for
the first 24 hours and then started to differ. It is possibly some type of
long-term average: After we had radon mitigation installed, the value has been
dropping very slowly. It is not the same as the 48 hour, month or year average
as reported by the app, but probably closer to three months.


# Other notes

* The Wave also reports the current time as a Bluetooth characteristic. This is
  quite likely synchronized by the app.

* If your Bluetooth adapter seems not to work, you may need to unblock it:

    sudo apt install rfkill
    sudo rfkill unblock bluetooth
