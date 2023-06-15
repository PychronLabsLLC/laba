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
import glob
import logging
import os
import shutil
from datetime import datetime
from logging.handlers import RotatingFileHandler

HANDLERS = []
MONTH_NAMES = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]


def setup():
    from paths import paths

    shandler = logging.StreamHandler()
    HANDLERS.append(shandler)

    name = datetime.now().strftime("%Y%m%d-%H.%M.%S")
    p = os.path.join(paths.logs_dir, f"{name}.log")

    rhandler = RotatingFileHandler(p, maxBytes=1e8, backupCount=50)

    HANDLERS.append(rhandler)

    fmt = "%(name)-40s: %(asctime)s %(levelname)-9s (%(threadName)-10s) %(message)s"
    fmtter = logging.Formatter(fmt)
    root = logging.getLogger()
    for h in HANDLERS:
        h.setFormatter(fmtter)
        h.setLevel(logging.DEBUG)
        root.addHandler(h)

    # archive old logs
    now = datetime.now()
    for p in glob.glob(os.path.join(paths.logs_dir, "*.log")):
        result = os.stat(p)
        mt = result.st_mtime
        creation_date = datetime.fromtimestamp(mt)
        if (now - creation_date).days > 30:
            archive(paths.logs_dir, os.path.basename(p))


def archive(root, p):
    today = datetime.today()
    month_idx = today.month
    month = MONTH_NAMES[month_idx - 1]
    year = today.year
    arch = os.path.join(root, "archive")
    if not os.path.isdir(arch):
        os.mkdir(arch)

    yarch = os.path.join(arch, str(year))
    if not os.path.isdir(yarch):
        os.mkdir(yarch)

    mname = f"{month_idx:02d}-{month}"
    march = os.path.join(yarch, mname)
    if not os.path.isdir(march):
        os.mkdir(march)

    src = os.path.join(root, p)
    dst = os.path.join(march, p)
    print(march, p)
    print(f"Archiving {p:15s} to ./archive/{year}/{mname}")
    try:
        shutil.move(src, dst)
    except Exception as e:
        print(f"Failed archiving {src} to {dst}. e={e}")


# ============= EOF =============================================
