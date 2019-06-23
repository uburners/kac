import os
import time
import glob
import logging
import requests
import socket
import serial
from async_timeout import timeout


logger = logging.getLogger(__file__)


class Scanner:
    def __init__(self):
        self.enabled = False

    def connect(self):
        devices = glob.glob('/dev/serial/by-id/usb-Newland_Auto-ID_NLS_IOTC_PRDsUSBVCP_*')
        if not devices:
            raise RuntimeError('No scanners found in /dev/serial/by-id/')

        if len(devices) > 1:
            logger.warn('More than one scanner device found.')

        device = devices[0]
        logger.info('Using scanner {0!r}'.format(device))
        self.port = serial.serial_for_url(url=device, baudrate=115200)
        print(self.port)

        self.configure()

    def configure(self):
        # await self._send_config_cmd('RRDENA1')  # enable same code timeout
        # await self._send_config_cmd('RRDDUR5000')  # same code timeout 5 sec
        # await self.enable()
        self._send_config_cmd('#RRDENA1;RRDDUR5000;ILLSCN2;SCNENA1')
        self.enabled = True

    def disable(self):
        if self.enabled:
            logger.info("Disabling scanner")
            self._send_config_cmd('#SCNENA0;ILLSCN0')
            self.enabled = False

    def enable(self):
        if not self.enabled:
            logger.info("Enabling scanner")
            self._send_config_cmd('#ILLSCN2;SCNENA1')
            self.enabled = True

    def scan(self):
        self.enable()
        logger.info("Reading code from scanner")
        code = self.port.readline()
        code = code.rstrip().decode('utf-8')
        logger.info('Got {0!r} from scanner'.format(code))
        self.disable()
        return code

    def _send_config_cmd(self, cmd):
        S_PREFIX = b'\x7e\x01\x30\x30\x30\x30'
        S_SUFFIX = b'\x3b\x03'

        if isinstance(cmd, str):
            cmd = cmd.encode('utf-8')

        data = S_PREFIX + cmd + S_SUFFIX
        print('Sending {!r}'.format(data))
        self.port.write(data)
        # await self.writer.drain()
        # await self.writer.drain()
        print('Reading response')
        resp = self.port.read_until(b';\x03')
        # resp = await self.reader.readexactly(len(data)+1)
        print(repr(resp))


class ResidentAccessServer:
    def __init__(self):
        self.session = requests.Session()

    def validate(self):
        pass

    def verify_token(self, token):
        resp = self.session.get(f'https://kurenivka.com.ua/wp-json/residents/v1/validate/{token}', verify=False)
        body = resp.json()
        print(body)
        return body.get('valid', False)


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

class Gate:
    def __init__(self):
        self.turn_ccw_pin = 23
        self.turn_cw_pin = 18
        self.block_pin = 14
        self.freeentry_pin = 15
        self.sense_turn_ccw_pin = 13
        self.sense_turn_cw_pin = 19
        self.sense_ready_pin = 26
        # self.turn_cw_event = asyncio.Event(loop=loop)
        # self.turn_ccw_event = asyncio.Event(loop=loop)
        # self.ready_event = asyncio.Event(loop=loop)
        # self.not_ready_event = asyncio.Event(loop=loop)
        self.num_cw_turn_events = 0
        self.num_ccw_turn_events = 0
        self.last_cw = 0
        self.last_ccw = 0

    def connect(self):
        # await self.pi.set_mode(self.turn_cw_pin, apigpio.OUTPUT)
        # await self.pi.set_mode(self.turn_ccw_pin, apigpio.OUTPUT)
        GPIO.setup(self.turn_cw_pin, GPIO.OUT)
        GPIO.setup(self.turn_ccw_pin, GPIO.OUT)
        GPIO.setup(self.block_pin, GPIO.OUT)
        GPIO.setup(self.freeentry_pin, GPIO.OUT)

        # await self.pi.set_mode(self.sense_turn_cw_pin, apigpio.INPUT)
        # await self.pi.set_mode(self.sense_turn_ccw_pin, apigpio.INPUT)
        # await self.pi.set_mode(self.sense_ready_pin, apigpio.INPUT)
    # await pi.set_mode(BT1_GPIO, apigpio.INPUT)
    # await pi.set_mode(BT2_GPIO, apigpio.INPUT)
        # await self.pi.set_pull_up_down(self.sense_turn_cw_pin, apigpio.PUD_UP)
        # await self.pi.set_pull_up_down(self.sense_turn_ccw_pin, apigpio.PUD_UP)
        # await self.pi.set_pull_up_down(self.sense_ready_pin, apigpio.PUD_UP)
        GPIO.setup(self.sense_turn_cw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sense_turn_ccw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sense_ready_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


        GPIO.add_event_detect(self.sense_turn_cw_pin, GPIO.FALLING, callback=self.on_sense_turn_cw)
        GPIO.add_event_detect(self.sense_turn_ccw_pin, GPIO.FALLING, callback=self.on_sense_turn_ccw)


    # await pi.set_pull_up_down(BT2_GPIO, apigpio.PUD_UP)

        # await self.pi.add_callback(self.sense_turn_cw_pin, edge=apigpio.EITHER_EDGE, func=self.on_turn_cw_changed)
        # await self.pi.add_callback(self.sense_turn_ccw_pin, edge=apigpio.EITHER_EDGE, func=self.on_turn_ccw_changed)
        # await self.pi.add_callback(self.sense_ready_pin, edge=apigpio.EITHER_EDGE, func=self.on_ready_changed)

        # await self.disable()
        # if (await self.pi.read(self.sense_ready_pin) == 0):
        #     print("Ready")
        #     self.ready_event.set()
        #     self.not_ready_event.clear()
        # else:
        #     print("NOT Ready")
        #     self.ready_event.clear()
        #     self.not_ready_event.set()

        # asyncio.ensure_future(self.ready_reader())

        # self.wait_for_ready()

    def turn_cw(self):
        # await self.pi.gpio_trigger(self.turn_cw_pin, 100000) # 0.1s
        logger.info("waiting for ready")

        #logger.info("Ready %s" % await self.pi.read(self.sense_ready_pin))
        self.wait_for_ready()
        # await self.ready_event.wait()

        logger.info("got ready")

        # self.turn_cw_event.clear()
        self.num_cw_turn_events = 0

        self._pulse(self.turn_cw_pin)
        # GPIO.output(self.turn_cw_pin, GPIO.LOW)
        # time.sleep(0.1)
        # GPIO.output(self.turn_cw_pin, GPIO.HIGH)
        # await self.pi.write(self.turn_cw_pin, 0)
        # await asyncio.sleep(0.1)
        # await self.pi.write(self.turn_cw_pin, 1)

        logger.info("waiting for not ready")
        self.wait_for_not_ready()

        return True
        # try:
        #     async with timeout(1) as cm:
        #         await self.not_ready_event.wait()
        #     if cm.expired:
        #         raise asyncio.TimeoutError()
        # except asyncio.TimeoutError:
        #     logger.info("FAILED TO ACTIVATE TURN")
        # else:
        #     logger.info("got not ready")
    def signal_error(self):
        self._pulse(self.block_pin)
        time.sleep(1)
        self._pulse(self.block_pin)

    def wait_for_cw_turn(self):
        # try:
            #await asyncio.wait_for(self.ready_event.wait(), 7)
        self.wait_for_ready()

        logger.info(self.num_cw_turn_events)
        if self.num_cw_turn_events > 0:
            logger.info("TURN")
            # await asyncio.sleep(0.5)
            time.sleep(0.5)
        else:
            logger.info("TURN CANCELLED")
            return False

        return True
        # except asyncio.TimeoutError:
        #     logger.info("TURN WAIT TIMEOUT")
        # try:
        #     start = time.time()
        #     print("waiting for turn event")
        #     await asyncio.wait_for(self.turn_cw_event.wait(), 7)
        #     print("waiting for ready")
        #     rest = max(0.1, 7 - (time.time() - start))
        #     print('rest ', rest)
        #     await asyncio.wait_for(self.ready_event.wait(), rest)
        # except asyncio.TimeoutError:
        #     print("TURN CANCELLED")
        # else:
        #     print("TURN")
        # self.turn_event.clear()

    def wait_for_ready(self):
        while GPIO.input(self.sense_ready_pin) != GPIO.LOW:
            pass

    def wait_for_not_ready(self):
        while GPIO.input(self.sense_ready_pin) == GPIO.LOW:
            pass


    def on_sense_turn_cw(self, val):
        self.num_cw_turn_events += 1

    def on_sense_turn_ccw(self, val):
        self.num_ccw_turn_events += 1

    def _pulse(self, pin, duration=0.1):
        GPIO.output(pin, GPIO.LOW)
        time.sleep(duration)
        GPIO.output(pin, GPIO.HIGH)


    # @apigpio.Debounce()
    # def on_turn_cw_changed(self, gpio, level, tick):
    #     delta = tick - self.last_cw
    #     # print("CW changed ", gpio, level, tick, delta)
    #     logger.info("CW changed %s %s %s %s" % gpio, level, tick, delta)
    #     if level == 0:
    #         self.turn_cw_event.set()
    #         self.num_cw_turn_events += 1
    #     else:
    #         self.turn_cw_event.clear()
    #     self.last_cw = tick

    # # @apigpio.Debounce()
    # def on_turn_ccw_changed(self, gpio, level, tick):
    #     delta = tick - self.last_ccw
    #     # print("CCW changed ", gpio, level, tick, delta)
    #     if level == 0:
    #         self.turn_ccw_event.set()
    #     else:
    #         self.turn_ccw_event.clear()
    #     self.last_ccw = tick

    # @apigpio.Debounce()
    # def on_ready_changed(self, gpio, level, tick):
    #     pass
        # print("Ready changed ", gpio, level, tick)
        # if level == 0:
        #     print("READY")
        #     self.ready_event.set()
        #     self.not_ready_event.clear()
        # else:
        #     print("NOT ready")
        #     self.ready_event.clear()
        #     self.not_ready_event.set()




def main(gate_id):
    gate = Gate()
    scanner = Scanner()
    # server = AccessServer(loop, gate_id)
    resident_access = ResidentAccessServer()

    gate.connect()
    scanner.connect()
    # server.validate()
    resident_access.validate()

    while True:
        time.sleep(0.05)
        logger.info("Reading token")
        token = scanner.scan()

        try:
            logger.info("Checking token on website")
            if not resident_access.verify_token(token):
                logger.error('Invalid token')
                gate.signal_error()
                continue

            logger.info("Sending turn CW")
            if not gate.turn_cw():
                logger.error("Failed to send turn signal")
                continue

            logger.info("Waiting for turn")
            if gate.wait_for_cw_turn():
                logger.info("Turn completed")
            else:
                logger.error("Turn CANCELLED")
        except Exception as e:
            logger.exception('Unexpected error')

# logging.basicConfig(level=logging.INFO)

# # s = Scanner()
# # s.connect()
# # print(s.scan())


# g=Gate()
# g.connect()

# print("Starting turn")
# g.turn_cw()
# print("Started. Waiting for turn")
# g.wait_for_cw_turn()
# print("Turn completed")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(os.environ['GATE_ID'])
