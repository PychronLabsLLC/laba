# ===============================================================================
# Copyright 2023 ross
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
import socket

from hardware.communicator import EthernetCommunicator


class TcpCommunicator(EthernetCommunicator):
    def open(self):
        self.handle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.handle.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,
                               self.configobj.get('keep_alive', 0))

        addr = (self.configobj.get('host', 'localhost'), self.configobj.get('port', 8000))
        self.handle.settimeout(self.configobj.get('timeout', 3))
        try:
            self.handle.connect(addr)
        except ConnectionRefusedError:
            self.warning(f"Failed connecting to {addr}")
            self.handle = None

        return True

# ============= EOF =============================================
