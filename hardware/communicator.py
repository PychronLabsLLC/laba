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
from loggable import Loggable


def convert(m):
    if m is None:
        return "None"
    return "".join(
        [
            c if (ascii(c) and not ord(c) in (10, 13)) else f"[{ord(c)}]"
            for c in m
        ]
    )


class Communicator(Loggable):
    handle = None
    simulation = True

    def open(self):
        pass

    def tell(self, msg, *args, **kw):
        msg = self._prep_message(msg)
        self._tell(msg, *args, **kw)
        self._log_tell(msg)

    def ask(self, msg, *args, **kw):
        msg = self._prep_message(msg)
        resp = self._ask(msg, *args, **kw)
        self._log_response(msg, resp)

        return resp

    def _prep_message(self, msg):
        wt = self.configobj.get("write_terminator")
        if wt:
            if wt == "CR":
                wt = "\r"
            elif wt == "LF":
                wt = "\n"
            elif wt == "CRLF":
                wt = "\r\n"

        if wt and not msg.endswith(wt):
            msg = f"{msg}{wt}"
        return msg

    def _log_tell(self, msg):
        self.debug(f'tell {convert(msg)}')

    def _log_response(self, msg, resp):
        self.debug(f"{convert(msg)}=>{resp}")

    def _tell(self, *args, **kw):
        raise NotImplementedError

    def _ask(self, *args, **kw):
        raise NotImplementedError

    def bootstrap(self):
        try:
            if self.open():
                self.simulation = False
        except BaseException:
            self.debug(f"failed bootstrap {self}")
            self.debug_exception()


class EthernetCommunicator(Communicator):
    def _ask(self, msg, *args, **kw):
        if not self.handle:
            self.warning("No handle")
            return

        if isinstance(msg, str):
            msg = msg.encode("utf-8")

        self.handle.send(msg)

        rt = self.configobj.get("read_terminator")
        if rt:
            return self._read_terminator(rt)
        else:
            return self._read_bytes()

    def _read_terminator(self, rt):
        buf = []
        while True:
            c = self.handle.recv(1)
            if c == rt:
                break
            buf.append(c)
        return "".join(buf)

    def _read_bytes(self, bytes=1024):
        return self.handle.recv(bytes)


class TelnetCommunicator(Communicator):
    pass


class ZmqCommunicator(Communicator):
    pass

# ============= EOF =============================================
