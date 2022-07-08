from time import sleep
import Kostal_Interface
import MyStrom_Interface
import HardyBarth_Interface
#import GUI

settings = {}

def switchOnDevice(devicePar, powerPar):
    devicePar = devicePar.get('Interface').StartDevice(devicePar, powerPar)

    return devicePar


def switchOffDevice(devicePar):
    devicePar = devicePar.get('Interface').StopDevice(devicePar)

    return devicePar


def switchOffAllRunningDevices(devicesPar):
    for i in range(len(devicesPar)):
        if devicesPar[i]['Active'] and (devicesPar[i]['Auto'] == "Auto"):
            devicesPar[i] = switchOffDevice(devicesPar[i])

    return devicesPar


def powerBypass(devicesPar):
    if devicesPar[0]['currAmps'] != devicesPar[0]['maxParValue']:
        devicesPar = switchOnDevice(devicesPar[0], devicesPar[0]['maxParValue'])

    return devicesPar


def checkDeviceRunning(devicePar):
    return devicePar.get('Interface').checkDeviceRunning(devicePar)


def identifyDeviceToSwitchOn(devicesPar, availablePowerPar, currBatPar):
    global limitBatCap
    bestDeviceDeltaW = 99999
    bestDeviceW = 0
    bestDeviceI = -1
    # identify best device to switch on

    for i in range(len(devicesPar)):
        deviceW = 0
        if not (devicesPar[i]['Active'] and (devicesPar[i][
                                                 'Auto'] == "Auto")):  # ToDo if adjustable Device is active but not on full Power!!! It will not change!!!
            if devicesPar[i]['adjustablePower']:
                for j in range(devicesPar[i]["minParValue"], devicesPar[i]["maxParValue"]):
                    deviceW = j * devicesPar[i]['WperA']
                    if (deviceW > availablePowerPar) and (j > devicesPar[i]["minParValue"]):
                        deviceW = (j - 1) * devicesPar[i]['WperA']
                        break
                    elif (deviceW <= availablePowerPar) and (j == devicesPar[i]["maxParValue"]):
                        deviceW = j * devicesPar[i]['WperA']
            else:
                deviceW = devicesPar[i]['StartAt']

            if ((availablePowerPar - deviceW) >= 0) and ((availablePowerPar - deviceW) < bestDeviceDeltaW):
                bestDeviceDeltaW = availablePowerPar - deviceW
                bestDeviceW = deviceW
                bestDeviceI = i
    if bestDeviceI >= 0:
        if devicesPar[bestDeviceI]['adjustablePower']:
            devicesPar[bestDeviceI] = switchOnDevice(devicesPar[bestDeviceI],
                                                     (bestDeviceW / devicesPar[bestDeviceI]['WperA']))
        else:
            devicesPar[bestDeviceI] = switchOnDevice(devicesPar[bestDeviceI], 0)
        limitBatCap = currBatPar
    return devicesPar


def identifyDeviceToSwitchOff(devicesPar, availablePowerPar):
    saveW = 100000
    saveI = -1
    # identify best device to switch off
    for i in range(len(devicesPar)):
        if devicesPar[i]['adjustablePower'] and devicesPar[i]['Active'] and (devicesPar[i]['Auto'] == "Auto"):
            currSaveW = devicesPar[i]['currAmps'] * devicesPar[i]['WperA']
        elif devicesPar[i]['Active']:
            currSaveW = devicesPar[i]['StartAt']
        else:
            continue

        currSaveW += availablePowerPar

        if saveW > abs(currSaveW):
            saveW = abs(currSaveW)
            saveI = i

    devicesPar[saveI] = switchOffDevice(devicesPar[saveI])

    return devicesPar


def initValues():
    global settings
    settings["limitBatCap"] = 50
    settings["minBatCap"] = 10

    #global minBatCap
    #minBatCap = 10
    #global batUsage
    #batUsage = 10

    list1 = list()
    list2 = []
    list1.append(1)
    list1.append(2)

    global devices
    #devices = []
    devices = list()
    devices.append({'Name': 'Wallbox',
                    'StartAt': 3500,
                    'Active': False,
                    'IP': 'ecb1',
                    'Interface': HardyBarth_Interface,
                    'adjustablePower': True,
                    'minParValue': 6,
                    'maxParValue': 16,
                    'parName': "manualmodeamp",
                    'currAmps': 0,
                    'WperA': 500
                    })
    devices.append({'Name': 'MyStromPool',
                    'StartAt': 350,
                    'Active': False,
                    'IP': '192.168.178.105',
                    'Interface': MyStrom_Interface,
                    'adjustablePower': False
                    })
    devices.append({'Name': 'MyStromWP',
                    'StartAt': 550,
                    'Active': False,
                    'IP': '192.168.178.104',
                    'Interface': MyStrom_Interface,
                    'adjustablePower': False
                    })
    #adjustable Devices
    #devices[0]["adjustablePower"] = True
    #devices[0]["minParValue"] = 6
    #devices[0]["maxParValue"] = 16
    #devices[0]["parName"] = "manualmodeamp"
    #devices[0]["currAmps"] = 0
    #devices[0]["WperA"] = 500


if __name__ == '__main__':
    #devices = {}
    # initValues(devices)
    initValues()
    limitBatCap = settings["limitBatCap"]
    minBatCap = settings["minBatCap"]
    # limitBatCap = 100
    # minBatCap = 10

    while True:
    # available Values:
    # KostalValues['PV generation']
    # KostalValues['Battery Usage']
    # KostalValues['Home Consumption']
    # KostalValues['Power to grid']
    # KostalValues['Battery %']
    # KostalValues['Battery temp']
        Values = Kostal_Interface.updateRelevantValues("192.168.178.93")
        if len(Values) > 1:
            KostalValues = Values

        # for elements in KostalValues:
        # print (elements + ": " + KostalValues[elements])
        # print (elements + ": " + str(KostalValues[elements]))

        print("Time\tfromPV\tfromBat\tVerbr,\tEinsp.\tBat%\tWallbox\tBat.Temp")
        print(str(round(KostalValues['PV generation'], 1)) + "\t" +
              str(round(KostalValues['Battery Usage'], 1)) + "\t" +
              str(round(KostalValues['Home Consumption'], 1)) + "\t" +
              str(round(KostalValues['Power to grid'], 1)) + "\t" +
              str(round(KostalValues['Battery %'], 1)) + "%\t" +
              str(round(KostalValues['Battery temp'], 1)) + "°C")

        availablePower = KostalValues['PV generation'] - KostalValues['Home Consumption']
        # Debug!!!
        # availablePower = int(input("DEBUG: Verfügbare Leistung angeben!"))
        # KostalValues['Battery %'] = int(input("DEBUG: Akt. Batt Ladestand angeben!"))

        if KostalValues['Battery %'] <= minBatCap:
            # Use Power From Grid
            devices = powerBypass(devices)
            print("run lowBattery Bypass")
        elif KostalValues['Battery %'] <= 50:
            # ChargeOnly if not Running
            if KostalValues['Battery %'] < limitBatCap:
                devices = switchOffAllRunningDevices(devices)
            print("no Power On")
        elif availablePower < 300:
            # No Power from PV use BatCap until buffer empty
            if KostalValues['Battery %'] < limitBatCap:
                devices = identifyDeviceToSwitchOff(devices, availablePower)
            print("available Power: " + str(availablePower))
        else:
            devices = identifyDeviceToSwitchOn(devices, availablePower, KostalValues['Battery %'])

            # Power On next Device
        # sleep(5)

        #return (KostalValues)
