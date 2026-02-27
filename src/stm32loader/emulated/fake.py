import struct

from stm32loader.bootloader import Stm32Bootloader


class FakeConnection:

    ACK = Stm32Bootloader.Reply.ACK.value
    Command = Stm32Bootloader.Command

    COMMAND_RESPONSES = {
        # Return length, bootloader version, commands
        # Version 5, 0x0=GET 0x01=GET_VERSION 0x02=GET_ID 0x11=READ_MEMORY 0x31=WRITE_MEMORY
        # 0x43=ERASE 0x44=EXTENDED_ERASE
        Command.GET: [7, 0x05, [0x0, 0x01, 0x02, 0x11, 0x31, 0x43, 0x44], ACK],
        # Product ID: 0x422
        Command.GET_ID: [1, [0x04, 0x22]],
    }

    READ_RESPONSES = {
        # Read flash size, F1.
        (0x_1FFF_F7E0, 2): [[0x00, 0x01]],

        # Read flash size, F3.
        (0x_1FFF_F7CC, 2): [[0x00, 0x01]],

        # Read device UID, F1.
        (0x_1FFF_F7E8, 12):  [[1, 0, 3, 2, 7, 6, 5, 4, 0xB, 0xA, 9, 8]],

        # Read device UID, F3.
        (0x_1FFF_F7AC, 12): [[1, 0, 3, 2, 7, 6, 5, 4, 0xB, 0xA, 9, 8]],

        # Read Bootloader ID.
        (0x_1FFF_F796, 1): [0x41],
    }

    def __init__(self):
        self.next_return = []
        self.timeout = 2
        self.receiver = self.receive()

        self.flash_offset = 0x_0800_0000
        self.flash_size = 2 * 1024 * 1024
        self.flash_memory = bytearray(2 * 1024 * 1024)

        # Start coroutine.
        next(self.receiver)

    def ack(self):
        self.next_return.append(self.ACK)

    def receive(self):
        while True:
            # Receive a command coming in.
            command_bytes = yield
            command_value = struct.unpack("B", command_bytes)[0]

            # Receive CRC byte.
            yield
            self.ack()

            if command_value in self.COMMAND_RESPONSES:
                self.next_return.extend(self.COMMAND_RESPONSES[command_value])
            elif command_value == self.Command.READ_MEMORY.value:
                # Receive address with CRC.
                address_bytes = yield
                address = struct.unpack(">I", address_bytes[0:4])[0]
                self.ack()

                # Receive number of bytes
                length_bytes = yield
                length = struct.unpack("B", length_bytes)[0] + 1

                # Receive CRC
                yield
                self.ack()

                # Set up data to respond.
                if self.flash_offset <= address < self.flash_offset + self.flash_size:
                    # Return flash data.
                    flash_offset = address - self.flash_offset
                    self.next_return.append(list(self.flash_memory[flash_offset: flash_offset + length]))
                else:
                    self.next_return.extend(self.READ_RESPONSES[(address, length)])
            elif command_value == self.Command.EXTENDED_ERASE.value:
                pages_bytes = yield
                pages = struct.unpack(">H", pages_bytes[0:2])
                if pages == 0xFFFF:
                    # Erase all.
                    self.flash_memory[:] = 0xFF
                    self.next_return.append(self.ACK)
            elif command_value == self.Command.WRITE_MEMORY.value:
                address_bytes = yield
                address = struct.unpack(">I", address_bytes[0:4])[0]
                size_bytes = yield
                byte_count = struct.unpack("B", size_bytes)[0] + 1
                data = yield
                crc = yield

                assert len(data) == byte_count, f"Length does not match byte count: {len(data)} vs {byte_count}"

                # Record data in flash memory.
                flash_offset = address - 0x_0800_0000
                self.flash_memory[flash_offset: flash_offset + byte_count] = data
            else:
                raise NotImplementedError()

    def write(self, data):
        # Send to coroutine.
        self.receiver.send(data)

    def read(self, length=1):
        if self.next_return:
            value = self.next_return.pop(0)
            if isinstance(value, int):
                return [value]
            return value

        return [self.ACK]


class FakeConfiguration:

    def __init__(self, erase, write, verify, firmware_file, family=None):
        self.erase = erase
        self.write = write
        self.verify = verify
        self.data_file = firmware_file
        self.unprotect = False
        self.protect = False
        self.length = None
        self.verbosity = 5
        self.address = 0x_0800_0000
        self.go_address = None
        self.family = family

