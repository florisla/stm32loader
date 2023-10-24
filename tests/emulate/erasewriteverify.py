import enum
import struct
from pathlib import Path

from stm32loader.main import Stm32Loader
from stm32loader.bootloader import Stm32Bootloader

ACK = Stm32Bootloader.Reply.ACK.value


FIRMWARE_FILE = Path(__file__).parent / "../../firmware/generic_boot20_pc13.binary.bin"


Command = Stm32Bootloader.Command


class FakeConnection:

    COMMAND_RESPONSES = {
        # Return length, bootloader version, commands
        # ACK, 1, 0x05, 0x44, ACK
        Command.GET: [1, 0x05, 0x44, ACK],

        # Product ID: 0x412
        Command.GET_ID: [1, [0x04, 0x12]],
    }

    READ_RESPONSES = {
        # Read flash size.
        (0x_1FFF_F7E0, 2): [[0x00, 0x01]],

        # Read device UID.
        (0x_1FFF_F7E8, 12):  [[1, 0, 3, 2, 7, 6, 5, 4, 0xB, 0xA, 9, 8]],
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
        self.next_return.append(ACK)

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
            elif command_value == Command.READ_MEMORY.value:
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
            elif command_value == Command.EXTENDED_ERASE.value:
                pages_bytes = yield
                pages = struct.unpack(">H", pages_bytes[0:2])
                if pages == 0xFFFF:
                    # Erase all.
                    self.flash_memory[:] = 0xFF
                    self.next_return.append(ACK)
            elif command_value == Command.WRITE_MEMORY.value:
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

        return [Stm32Bootloader.Reply.ACK]


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


def erase_write_verify():
    loader = Stm32Loader()
    loader.configuration = FakeConfiguration(erase=True, write=True, verify=True, firmware_file=FIRMWARE_FILE, family=None)
    loader.connection = FakeConnection()
    loader.stm32 = Stm32Bootloader(loader.connection, device_family="F1")

    loader.read_device_id()
    loader.read_device_uid()
    loader.perform_commands()


if __name__ == "__main__":
    erase_write_verify()
