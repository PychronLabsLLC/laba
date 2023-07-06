# ===============================================================================
# Copyright 2023 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import random

try:
    from mcculw import ul
    from mcculw.enums import (
        ULRange,
        InterfaceType,
        DigitalIODirection,
        DigitalPortType,
        TempScale,
    )
    from mcculw.device_info import DaqDeviceInfo

    CELSIUS = TempScale.CELSIUS
except (ImportError, NameError):
    CELSIUS = 0

    class UL:
        def t_in(self, *args, **kw):
            return random.random()

    ul = UL()

from hardware.communicator import Communicator


def config_first_detected_device(board_num, dev_id_list=None):
    """Adds the first available device to the UL.  If a types_list is specified,
    the first available device in the types list will be add to the UL.
    Parameters
    ----------
    board_num : int
        The board number to assign to the board when configuring the device.
    dev_id_list : list[int], optional
        A list of product IDs used to filter the results. Default is None.
        See UL documentation for device IDs.
    """
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        raise Exception("Error: No DAQ devices found")

    print("Found", len(devices), "DAQ device(s):")
    for device in devices:
        print(
            "  ",
            device.product_name,
            " (",
            device.unique_id,
            ") - ",
            "Device ID = ",
            device.product_id,
            sep="",
        )

    device = devices[0]
    if dev_id_list:
        device = next(
            (device for device in devices if device.product_id in dev_id_list), None
        )
        if not device:
            err_str = "Error: No DAQ device found in device ID list: "
            err_str += ",".join(str(dev_id) for dev_id in dev_id_list)
            raise Exception(err_str)

    # Add the first DAQ device to the UL with the specified board number
    ul.create_daq_device(board_num, device)


class MccCommunicator(Communicator):
    """
    https://github.com/mccdaq/mcculw
    """

    board_num = 0

    def load(self, config, path):
        self.board_num = self.config("board_num", 0)
        return super(MccCommunicator, self).load(config, path)

    def initialize(self, *args, **kw):
        config_first_detected_device(self.board_num)
        return True

    def a_in(self, channel, ai_range=None):
        if ai_range is None:
            ai_range = ULRange.BIP5VOLTS

        value = ul.a_in(self.board_num, channel, ai_range)
        # Convert the raw value to engineering units
        eng_units_value = ul.to_eng_units(self.board_num, ai_range, value)
        return eng_units_value

    def d_in(self, channel):
        port = self._get_port(channel)
        if port:
            bit_num = self._get_bit_num(channel)

            bit_value = ul.d_bit_in(self.board_num, port.type, bit_num)
            return bool(bit_value)

    def t_in(self, channel):
        """
        get temperature in celsius
        """
        value = ul.t_in(self.board_num, int(channel), CELSIUS)
        return value

    def d_out(self, channel, bit_value):
        channel = str(channel)
        port = self._get_port(channel)
        if port:
            bit_num = self._get_bit_num(channel)

            self.debug(
                "channel={}, bit_num={}, bit_value={}".format(
                    channel, bit_num, bit_value
                )
            )
            # if port.is_port_configurable:
            #    self.debug('configuring {} to OUT'.format(port.type))
            #    ul.d_config_port(self.board_num, port.type, DigitalIODirection.OUT)
            # Output the value to the bit

            try:
                ul.d_bit_out(self.board_num, port.type, bit_num, bit_value)
            except BaseException:
                self.debug_exception()

    def _get_bit_num(self, channel):
        channel = str(channel)
        bit_num = int(channel.split("-")[1])
        self.debug("channel={}  bit_num={}".format(channel, bit_num))
        return bit_num

    def _get_port(self, channel):
        port_id = int(str(channel).split("-")[0])
        self.debug("channel={} port={}".format(channel, port_id))

        daq_dev_info = DaqDeviceInfo(self.board_num)
        if not daq_dev_info.supports_digital_io:
            raise Exception("Error: The DAQ device does not support " "digital I/O")

        self.debug(
            "Active DAQ device: {} {}".format(
                daq_dev_info.product_name, daq_dev_info.unique_id
            )
        )

        dio_info = daq_dev_info.get_dio_info()

        for i, p in enumerate(dio_info.port_info):
            self.debug(
                "{} {} {} {} {}".format(i, p, p.type, p.num_bits, p.supports_output)
            )

        for p in dio_info.port_info:
            if int(p.type) == port_id:
                return p
        else:
            self.debug("Invalid port_id={}", port_id)

        # Find the first port that supports input, defaulting to None
        # if one is not found.
        # port = next((port for port in dio_info.port_info if port.supports_input),
        #             None)
        # if not port:
        #     raise Exception('Error: The DAQ device does not support '
        #                     'digital input')


# ============= EOF =============================================
