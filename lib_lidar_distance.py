import smbus
import time
import paho.mqtt.client as mqtt
import json

# SDA = GPIO2
# SCA = GPIO3

global lib
global lib_mqtt_client


class Lidar_Lite():
  def __init__(self):
    self.address = 0x62
    self.distWriteReg = 0x00
    self.distWriteVal = 0x04
    self.distReadReg1 = 0x8f
    self.distReadReg2 = 0x10

  def connect(self, bus):
    try:
      self.bus = smbus.SMBus(bus)
      time.sleep(0.5)
      return 0
    except:
      return -1

  def writeAndWait(self, register, value):
    self.bus.write_byte_data(self.address, register, value);
    time.sleep(0.02)


  def readDistAndWait(self, register):
    res = self.bus.read_i2c_block_data(self.address, register, 2)
    time.sleep(0.02)
    return (res[0] << 8 | res[1])

  def getDistance(self):
    self.writeAndWait(self.distWriteReg, self.distWriteVal)
    dist = self.readDistAndWait(self.distReadReg1)
    return dist


def msw_mqtt_connect(broker_ip, port):
    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    lib_muv_topic = '/MUV/control/'+ lib['name'] + '/MICRO'
    lib_mqtt_client.subscribe(lib_muv_topic, 0)
    print(lib_muv_topic)
    lib_mqtt_client.loop_start()
   # lib_mqtt_client.loop_forever()
    return lib_mqtt_client


def on_connect(client, userdata, flags, rc):
    print('[msg_mqtt_connect] connect to ', broker_ip)


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    on_receive_from_msw(msg.topic, str(payload))


def request_to_mission(cinObj):
    con = cinObj['con']


def missionData():
    try:
        lidar = Lidar_Lite()
        connected = lidar.connect(1)
        if connected < -1:
            status = 'Disconnected'
            print("Disconnected")

        distance = lidar.getDistance()
        data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
        send_data_to_msw(data_topic, distance)
    except (TypeError, ValueError):
        print("Disconnected")
        pass


def send_data_to_msw (data_topic, obj_data):
    global lib_mqtt_client

    lib_mqtt_client.publish(data_topic, obj_data)

def on_receive_from_msw(topic, str_message):
    print('[' + topic + '] ' + str_message)
    cinObj = json.loads(str_message)
    print(cinObj)
    request_to_mission(cinObj)


if __name__ == "__main__":
    my_lib_name = 'lib_lidar_distance'

    try:
        lib = dict()
        with open(my_lib_name + '.json', 'r') as f:
            lib = json.load(f)
            lib = json.loads(lib)

    except:
        lib = dict()
        lib["name"] = my_lib_name
        lib["target"] = 'armv6'
        lib["description"] = "[name]"
        lib["scripts"] = './' + my_lib_name
        lib["data"] = ['Distance']
        lib["control"] = []
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)

        broker_ip = 'localhost'
        port = 1883
        msw_mqtt_connect(broker_ip, port)

    while True:
        missionData()
