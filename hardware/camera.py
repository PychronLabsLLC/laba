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

from pypylon import pylon


class Camera(Loggable):
    _handle = None

    def open(self):
        self._handle = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self._handle.Open()

    def close(self):
        self._handle.Close()

    def get_images(self, n=1, timeout_ms=5000):
        if n == 1:
            img = self._handle.GrabOne(timeout_ms)
            return img.Array
        else:
            self._handle.StartGrabbingMax(n)
            while self._handle.IsGrabbing():
                result = self._handle.RetrieveResult(
                    timeout_ms, pylon.TimeoutHandling_ThrowException
                )
                if result.GrabSucceeded():
                    img = result.Array
                    return img
                result.Release()


#
#
# # demonstrate some feature access
# new_width = camera.Width.GetValue() - camera.Width.GetInc()
# if new_width >= camera.Width.GetMin():
#     camera.Width.SetValue(new_width)
#
# numberOfImagesToGrab = 100
# camera.StartGrabbingMax(numberOfImagesToGrab)
#
# while camera.IsGrabbing():
#     grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
#
#     if grabResult.GrabSucceeded():
#         # Access the image data.
#         print("SizeX: ", grabResult.Width)
#         print("SizeY: ", grabResult.Height)
#         img = grabResult.Array
#         print("Gray value of first pixel: ", img[0, 0])
#
#     grabResult.Release()
# camera.Close()
# ============= EOF =============================================
