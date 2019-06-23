import os
import time
import glob
import asyncio
import apigpio
import logging
import aiohttp
import socket
import serial_asyncio
from async_timeout import timeout

# BT1_GPIO = 18
# BT2_GPIO = 23


logger = logging.getLogger(__file__)


# def on_input(gpio, level, tick):
#     print('on_input {} {} {}'.format(gpio, level, tick))


# S_PREFIX=b'\x7e\x01\x30\x30\x30\x30'
# S_SUFFIX=b'\x3b\x03'


class Scanner:
    def __init__(self, loop):
        self.enabled = False

    async def connect(self):
        devices = glob.glob('/dev/serial/by-id/usb-Newland_Auto-ID_NLS_IOTC_PRDsUSBVCP_*')
        if not devices:
            raise RuntimeError('No scanners found in /dev/serial/by-id/')

        if len(devices) > 1:
            logger.warn('More than one scanner device found.')

        device = devices[0]
        logger.info('Using scanner {0!r}'.format(device))
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=device, baudrate=115200)

        await self.configure()

    async def configure(self):
        # await self._send_config_cmd('RRDENA1')  # enable same code timeout
        # await self._send_config_cmd('RRDDUR5000')  # same code timeout 5 sec
        # await self.enable()
        await self._send_config_cmd('#RRDENA1;RRDDUR5000;ILLSCN2;SCNENA1')
        self.enabled = True

    async def disable(self):
        if self.enabled:
            await self._send_config_cmd('#SCNENA0;ILLSCN0')
            self.enabled = False

    async def enable(self):
        if not self.enabled:
            await self._send_config_cmd('#ILLSCN2;SCNENA1')
            self.enabled = True

    async def scan(self):
        await self.enable()
        code = await self.reader.readline()
        code = code.rstrip().decode('utf-8')
        logger.info('Got {0!r} from scanner'.format(code))
        await self.disable()
        return code

    async def _send_config_cmd(self, cmd):
        S_PREFIX = b'\x7e\x01\x30\x30\x30\x30'
        S_SUFFIX = b'\x3b\x03'

        if isinstance(cmd, str):
            cmd = cmd.encode('utf-8')

        data = S_PREFIX + cmd + S_SUFFIX
        print('Sending {!r}'.format(data))
        self.writer.write(data)
        await self.writer.drain()
        await self.writer.drain()
        print('Reading response')
        resp = await self.reader.readuntil(b';\x03')
        # resp = await self.reader.readexactly(len(data)+1)
        print(repr(resp))


class ResidentAccessServer:
    def __init__(self, loop):
        self.conn = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=False)
        self.session = aiohttp.ClientSession(loop=loop, connector=self.conn)

    async def validate(self):
        pass

    async def verify_token(self, token):
        async with self.session.get(f'https://dk.uburners.com/wp-json/residents/v1/validate/{token}') as resp:
            body = await resp.json()
            print(body)
            return body.get('valid', False)


class AccessServer:
    def __init__(self, loop, gate_id):
        self.session = aiohttp.ClientSession(loop=loop)
        self.gate_id = gate_id

    async def validate(self):
        pass

    # async def verify_token(self, token):
    #     params = {'turngate_id': self.gate_id, 'token': token}
    #     print(params)
    #     async with self.session.post('http://kac.lan:8000/api/v1/validate_token', params=params) as resp:
    #         body = await resp.json()
    #         print(body)
    #         return body.get('status') == 'ok'

    # async def process_token(self, token):
    #     params = {'turngate_id': self.gate_id, 'token': token}
    #     async with self.session.post('http://kac.lan:8000/api/v1/process_token', params=params) as resp:
    #         body = await resp.json()
    #         return body.get('status') == 'ok'

    async def start(self, token):
        params = {'turngate_id': self.gate_id, 'token': token}
        print(params)
        async with self.session.post('http://kac.lan:8000/api/v1/access/start', params=params) as resp:
            body = await resp.json()
            print(body)
            return body.get('status') == 'ok'

    async def complete(self, token):
        params = {'turngate_id': self.gate_id, 'token': token}
        async with self.session.post('http://kac.lan:8000/api/v1/access/complete', params=params) as resp:
            body = await resp.json()
            return body.get('status') == 'ok'

    async def cancel(self, token):
        params = {'turngate_id': self.gate_id, 'token': token}
        async with self.session.post('http://kac.lan:8000/api/v1/access/cancel', params=params) as resp:
            body = await resp.json()
            return body.get('status') == 'ok'

    async def close(self):
        await self.session.close()
        self.session = None


class Gate:
    def __init__(self, loop):
        self.pi = apigpio.Pi(loop)
        self.turn_cw_pin = 23
        self.turn_ccw_pin = 18
        self.sense_turn_cw_pin = 13
        self.sense_turn_ccw_pin = 19
        self.sense_ready_pin = 26
        self.turn_cw_event = asyncio.Event(loop=loop)
        self.turn_ccw_event = asyncio.Event(loop=loop)
        self.ready_event = asyncio.Event(loop=loop)
        self.not_ready_event = asyncio.Event(loop=loop)
        self.num_cw_turn_events = 0
        self.last_cw = 0
        self.last_ccw = 0

    async def connect(self, address=('127.0.0.1', 8888)):
        await self.pi.connect(address)

        await self.pi.set_mode(self.turn_cw_pin, apigpio.OUTPUT)
        await self.pi.set_mode(self.turn_ccw_pin, apigpio.OUTPUT)
        await self.pi.set_mode(self.sense_turn_cw_pin, apigpio.INPUT)
        await self.pi.set_mode(self.sense_turn_ccw_pin, apigpio.INPUT)
        await self.pi.set_mode(self.sense_ready_pin, apigpio.INPUT)
    # await pi.set_mode(BT1_GPIO, apigpio.INPUT)
    # await pi.set_mode(BT2_GPIO, apigpio.INPUT)
        await self.pi.set_pull_up_down(self.sense_turn_cw_pin, apigpio.PUD_UP)
        await self.pi.set_pull_up_down(self.sense_turn_ccw_pin, apigpio.PUD_UP)
        await self.pi.set_pull_up_down(self.sense_ready_pin, apigpio.PUD_UP)
    # await pi.set_pull_up_down(BT2_GPIO, apigpio.PUD_UP)

        await self.pi.add_callback(self.sense_turn_cw_pin, edge=apigpio.EITHER_EDGE, func=self.on_turn_cw_changed)
        await self.pi.add_callback(self.sense_turn_ccw_pin, edge=apigpio.EITHER_EDGE, func=self.on_turn_ccw_changed)
        await self.pi.add_callback(self.sense_ready_pin, edge=apigpio.EITHER_EDGE, func=self.on_ready_changed)

        # await self.disable()
        # if (await self.pi.read(self.sense_ready_pin) == 0):
        #     print("Ready")
        #     self.ready_event.set()
        #     self.not_ready_event.clear()
        # else:
        #     print("NOT Ready")
        #     self.ready_event.clear()
        #     self.not_ready_event.set()

        asyncio.ensure_future(self.ready_reader())

    async def turn_cw(self):
        # await self.pi.gpio_trigger(self.turn_cw_pin, 100000) # 0.1s
        logger.info("waiting for ready")

        logger.info("Ready %s" % await self.pi.read(self.sense_ready_pin))
        await self.ready_event.wait()

        logger.info("got ready")

        self.turn_cw_event.clear()
        self.num_cw_turn_events = 0
        await self.pi.write(self.turn_cw_pin, 0)
        await asyncio.sleep(0.1)
        await self.pi.write(self.turn_cw_pin, 1)

        logger.info("waiting for not ready")
        try:
            async with timeout(1) as cm:
                await self.not_ready_event.wait()
            if cm.expired:
                raise asyncio.TimeoutError()
        except asyncio.TimeoutError:
            logger.info("FAILED TO ACTIVATE TURN")
        else:
            logger.info("got not ready")

    async def wait_for_cw_turn(self):
        try:
            await asyncio.wait_for(self.ready_event.wait(), 7)

            logger.info(self.num_cw_turn_events)
            if self.num_cw_turn_events > 0:
                logger.info("TURN")
                await asyncio.sleep(0.5)
            else:
                logger.info("TURN CANCELLED")
        except asyncio.TimeoutError:
            logger.info("TURN WAIT TIMEOUT")
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

    # @apigpio.Debounce()
    def on_turn_cw_changed(self, gpio, level, tick):
        delta = tick - self.last_cw
        # print("CW changed ", gpio, level, tick, delta)
        logger.info("CW changed %s %s %s %s" % gpio, level, tick, delta)
        if level == 0:
            self.turn_cw_event.set()
            self.num_cw_turn_events += 1
        else:
            self.turn_cw_event.clear()
        self.last_cw = tick

    # @apigpio.Debounce()
    def on_turn_ccw_changed(self, gpio, level, tick):
        delta = tick - self.last_ccw
        # print("CCW changed ", gpio, level, tick, delta)
        if level == 0:
            self.turn_ccw_event.set()
        else:
            self.turn_ccw_event.clear()
        self.last_ccw = tick

    # @apigpio.Debounce()
    def on_ready_changed(self, gpio, level, tick):
        pass
        # print("Ready changed ", gpio, level, tick)
        # if level == 0:
        #     print("READY")
        #     self.ready_event.set()
        #     self.not_ready_event.clear()
        # else:
        #     print("NOT ready")
        #     self.ready_event.clear()
        #     self.not_ready_event.set()

    async def ready_reader(self):
        while True:
            val = await self.pi.read(self.sense_ready_pin)
            if val == 0:
                print("READY")
                self.ready_event.set()
                self.not_ready_event.clear()
            else:
                print("NOT ready")
                self.ready_event.clear()
                self.not_ready_event.set()




async def main(loop, gate_id):
    gate = Gate(loop)
    scanner = Scanner(loop)
    server = AccessServer(loop, gate_id)
    resident_access = ResidentAccessServer(loop)

    await gate.connect()
    await scanner.connect()
    await server.validate()
    await resident_access.validate()

    while True:
        logger.info("Reading token")
        token = await scanner.scan()

        try:
            logger.info("Checking token on website")
            if True: #await resident_access.verify_token(token):
                logger.info("Sending turn CW")
                if not await gate.turn_cw():
                    logger.error("Failed to send turn signal")
                    continue

                logger.info("Waiting for turn")
                if await gate.wait_for_cw_turn():
                    logger.info("Turn completed")
                else:
                    logger.error("Turn CANCELLED")
            else:
                logger.error('Invalid token')
        except Exception as e:
            logger.exception('Unexpected error')

        # try:
        #     if not (await server.start(token)):
        #         logging.warn('Server disallowed access for {0!r}'.format(token))
        #         continue

        #     logging.warn('Server allowed access for {0!r}'.format(token))

        #     print("Sending turn CW")
        #     if not await gate.turn_cw():
        #         await server.cancel(token)
        #         continue

        #     print("Waiting for turn")
        #     if await gate.wait_for_cw_turn()
        #         print("Turn completed")
        #         await server.complete(token)
        #     else:
        #         await server.cancel(token)
        #     # try:
        #     #     await gate.wait_for_turn()
        #     #     # await server.process_token(token)
        #     # finally:
        #     #     await gate.disable()
        # except Exception as e:
        #     logger.exception('Unexpected error')
        #     await server.cancel(token)


#import serial_asyncio
# reader, writer = await serial_asyncio.open_serial_connection(url='/dev/serial/by-id/usb-Newland_Auto-ID_NLS_IOTC_PRDsUSBVCP_FC8JA433-if00', baudrate=115200)


# async def subscribe(pi):
#     print("Subscribing")
#     await pi.set_mode(BT1_GPIO, apigpio.INPUT)
#     await pi.set_mode(BT2_GPIO, apigpio.INPUT)

#     await pi.set_pull_up_down(BT1_GPIO, apigpio.PUD_UP)
#     await pi.set_pull_up_down(BT2_GPIO, apigpio.PUD_UP)

#     await pi.add_callback(BT1_GPIO, edge=apigpio.EITHER_EDGE,
#                           func=on_input)
#     # await pi.add_callback(BT1_GPIO, edge=apigpio.RISING_EDGE,
#     #                       func=on_input)
#     await pi.add_callback(BT2_GPIO, edge=apigpio.RISING_EDGE,
#                           func=on_input)
#     print("Subscribed")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    # pi = apigpio.Pi(loop)
    # address = ('127.0.0.1', 8888)
    # loop.run_until_complete(pi.connect(address))
    loop.run_until_complete(main(loop, os.environ['GATE_ID']))

    loop.run_forever()
