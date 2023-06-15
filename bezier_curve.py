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

"""
adapted from https://stackoverflow.com/questions/12643079/b%C3%A9zier-curve-fitting-with-scipy
"""

import numpy as np
from scipy.special import comb


def bernstein_poly(i, n, t):
    """
    The Bernstein polynomial of n, i as a function of t
    """

    return comb(n, i) * (t ** (n - i)) * (1 - t) ** i


def bezier_curve(points, nsamples=1000):
    """
    Given a set of control points, return the
    bezier curve defined by the control points.

    points should be a list of lists, or list of tuples
    such as [ [1,1],
              [2,3],
              [4,5], ..[Xn, Yn] ]
     nsamples is the number of time steps, defaults to 1000

     See http://processingjs.nihongoresources.com/bezierinfo/
    """

    n_points = len(points)
    # x_points = np.array([p[0] for p in points])
    # y_points = np.array([p[1] for p in points])
    x_points, y_points = np.array(points).T

    t = np.linspace(0.0, 1.0, nsamples)

    polynomial_array = np.array(
        [bernstein_poly(i, n_points - 1, t) for i in range(0, n_points)]
    )

    xvals = np.dot(x_points, polynomial_array)
    yvals = np.dot(y_points, polynomial_array)

    return xvals, yvals


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import csv

    curvepath = "/Users/jross/laba/curves/curve_rates.csv"
    nsteps = 100
    curvename = 3
    invert = True
    with open(curvepath, "r") as rfile:
        reader = csv.reader(rfile, delimiter=",")
        rows = [row for row in reader]
        control_points = rows[curvename - 1]
        # self.debug(f'using control points {control_points}')
        n = len(control_points) + 1
        control_points = [
            ((i + 1) / n, float(cp) / 100) for i, cp in enumerate(control_points)
        ]
        control_points.insert(0, (0, 0))
        control_points.append((1, 1))
        xs, ys = bezier_curve(control_points, nsteps + 1)
        if invert:
            ys = [1 - yi for yi in ys]

        for i, (x, y) in enumerate(zip(xs, ys)):
            print(i, x, y)
        plt.plot(xs, ys)
        plt.show()
# ============= EOF =============================================
