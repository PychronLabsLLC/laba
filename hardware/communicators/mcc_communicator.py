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
    ANY = InterfaceType.ANY
except (ImportError, NameError):
    CELSIUS = 0
    ANY = 0

    class UL:
        ULError = BaseException

        def t_in(self, *args, **kw):
            return random.random()

        def ignore_instacal(self):
            pass

        def get_daq_device_inventory(self, *args, **kw):
            return []

    ul = UL()

from hardware.communicator import Communicator


class MccCommunicator(Communicator):
    """
    https://github.com/mccdaq/mcculw
    """

    board_num = 0
    device_id = 0
    device_info = None

    def load(self, config, path):
        self.board_num = self.config("board_num", 0)
        self.device_id = self.config("device_id", 0)
        return super(MccCommunicator, self).load(config, path)

    def initialize(self, *args, **kw):
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
        devices = ul.get_daq_device_inventory(ANY)
        try:
            if not devices:
                raise Exception("Error: No DAQ devices found")

            self.info(f"Found {len(devices)} DAQ device(s)")
            for device in devices:
                self.info(
                    f"  {device.product_name} ({device.unique_id}) - Device ID = {device.product_id}"
                )

            self.info(f"Using device_id: {self.device_id}")
            device = devices[self.device_id]
            # if dev_id_list:
            #     device = next(
            #         (device for device in devices if device.product_id in dev_id_list), None
            #     )
            #     if not device:
            #         err_str = "Error: No DAQ device found in device ID list: "
            #         err_str += ",".join(str(dev_id) for dev_id in dev_id_list)
            #         raise Exception(err_str)
            #
            # Add the first DAQ device to the UL with the specified board number
            ul.create_daq_device(self.board_num, device)

            self.device_info = DaqDeviceInfo(self.board_num)
            self.report_device_info()
        except ul.ULError:
            self.warning("Failed to get device info")

        return True

    def report_device_info(self):
        di = self.device_info
        self.info("-------------------- Device Info ---------------------")
        self.info(f"Board Num: {self.board_num}")
        self.info(f"Product Name: {di.product_name}")
        self.info(f"Unique ID: {di.unique_id}")
        if di.supports_digital_io:
            dio = di.get_dio_info()
            self.info(f"Number of Digital I/O Ports: {dio.num_ports}")
            for p in dio.port_info:
                self.info(f"    Port {p.type.name}")
                self.info(f"        Number of Bits: {p.num_bits}")
                self.info(f"        Supports Input: {p.supports_input}")
                self.info(f"        Supports Input Scan: {p.supports_input_scan}")
                self.info(f"        Supports Output: {p.supports_output}")
                self.info(f"        Supports Output: {p.supports_output_scan}")
                self.info(f"        Input Mask: {p.in_mask}")
                self.info(f"        Output Mask: {p.out_mask}")
                self.info(f"        First Dit: {p.first_bit}")
                self.info(f"        Is Bit Configurable: {p.is_bit_configurable}")
                self.info(f"        Is Port Configurable: {p.is_port_configurable}")

        if di.supports_temp_input:
            ai = di.get_ai_info()
            self.info(f"Number of A/D Channels: {ai.num_chans}")
            self.info(f"Number of Temp Channels: {ai.num_temp_chans}")
            self.info(f"Number of A/D Resolution: {ai.resolution}")
            self.info(f"Supports scan: {ai.supports_scan}")
            self.info(f"Supports v_in: {ai.supports_v_in}")

    def a_in(self, channel, ai_range=None):
        if ai_range is None:
            ai_range = ULRange.BIP5VOLTS

        value = ul.a_in(self.board_num, channel, ai_range)
        # Convert the raw value to engineering units
        eng_units_value = ul.to_eng_units(self.board_num, ai_range, value)
        return eng_units_value

    # def d_in(self, channel):
    #     port = self._get_port(channel)
    #     if port:
    #         bit_num = self._get_bit_num(channel)
    #
    #         bit_value = ul.d_bit_in(self.board_num, port.type, bit_num)
    #         return bool(bit_value)

    def t_in(self, channel):
        """
        get temperature in celsius
        """
        value = ul.t_in(self.board_num, int(channel), CELSIUS)
        return value

    def d_out(self, channel, bit_value, port=None):
        # channel = str(channel)
        bit_num = int(channel)

        # port = self._get_port(channel)
        # if port:
        #         bit_num = self._get_bit_num(channel)
        #
        #         self.debug(
        #             "channel={}, bit_num={}, bit_value={}".format(
        #                 channel, bit_num, bit_value
        #             )
        #         )
        #         # if port.is_port_configurable:
        #         #    self.debug('configuring {} to OUT'.format(port.type))
        #         #    ul.d_config_port(self.board_num, port.type, DigitalIODirection.OUT)
        #         # Output the value to the bit

        # porttype = DigitalPortType.FIRSTPORTA
        if port is None:
            port = DigitalPortType.FIRSTPORTA
        else:
            port = getattr(DigitalPortType, port.upper())

        try:
            ul.d_bit_out(self.board_num, port, bit_num, bit_value)
        except BaseException:
            self.debug_exception()

    #
    # def _get_bit_num(self, channel):
    #     channel = str(channel)
    #     bit_num = int(channel.split("-")[1])
    #     self.debug("channel={}  bit_num={}".format(channel, bit_num))
    #     return bit_num

    # def _get_port(self, channel):
    #     port_id = int(channel)
    #     # port_id = int(str(channel).split("-")[0])
    #     # self.debug("channel={} port={}".format(channel, port_id))
    #
    #     if not self.device_info.supports_digital_io:
    #         raise Exception("Error: The DAQ device does not support " "digital I/O")
    #
    #     self.debug(
    #         "Active DAQ device: {} {}".format(
    #             self.device_info.product_name, self.device_info.unique_id
    #         )
    #     )
    #
    #     dio_info = self.device_info.get_dio_info()
    #
    #     for i, p in enumerate(dio_info.port_info):
    #         self.debug(
    #             "{} {} {} {} {}".format(i, p, p.type, p.num_bits, p.supports_output)
    #         )
    #
    #     for p in dio_info.port_info:
    #         if int(p.type) == port_id:
    #             return p
    #     else:
    #         self.debug("Invalid port_id={}", port_id)

    # Find the first port that supports input, defaulting to None
    # if one is not found.
    # port = next((port for port in dio_info.port_info if port.supports_input),
    #             None)
    # if not port:
    #     raise Exception('Error: The DAQ device does not support '
    #                     'digital input')


# ============= EOF =============================================
