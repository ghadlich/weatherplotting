#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2021 Grant Hadlich
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE. 
#
# Portions adapted from https://github.com/wvangeit/ClimateTunnel

import os
import datetime

import numpy as np
import pandas

import matplotlib
matplotlib.use('Agg')

import matplotlib.animation as animation
import matplotlib.collections as collections
import matplotlib.pyplot as plt

plt.style.use('ggplot')

from tqdm.auto import tqdm

rs = np.array([])
thetas = np.array([])
current_year = 0
current_day = 0

def create_max_temp_graphic(data_dir="data", input_file="seatac.csv", output_dir="output", output_file="output.mp4"):

    os.makedirs(output_dir, exist_ok=True)

    csv_filename = os.path.join(data_dir, input_file)
    data = pandas.read_csv(
        csv_filename,
        infer_datetime_format=True,
        parse_dates=['DATE'],
        usecols=['DATE', 'TMAX'])

    # Interpolate for any missing days
    data = data.interpolate()

    min_temp = np.min(data["TMAX"])
    min_temp_rounded = 5 * round((min_temp-15)/5)

    max_temp = np.max(data["TMAX"])
    max_temp_rounded = 5 * round((max_temp+5)/5)

    data_len = len(data['TMAX'])

    # Set Up Plot Basics
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_subplot(1, 1, 1, projection='polar')
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2.0)

    marker, = ax.plot([], [], '.', alpha=.001, ms=10, mfc='black')
    line = collections.LineCollection(
        [],
        linewidth=5,
        alpha=.5,
        cmap=plt.get_cmap('coolwarm'),
        norm=plt.Normalize(
            min_temp,
            max_temp))
    ax.add_collection(line)
    title = ax.text(-0.11, 0.0, '', fontsize=20, transform=ax.transAxes)
    caption1 = ax.text(-0.11,
                    1.1,
                    'Seattle Daily High Temperatures',
                    fontsize=20,
                    transform=ax.transAxes)
    caption2 = ax.text(-0.11,
                    1.025,
                    'Source: https://www.ncdc.noaa.gov/\n'
                    'GitHub: https://github.com/ghadlich/weatherplotting',
                    fontsize=10,
                    transform=ax.transAxes)

    ax.set_ylim([min_temp, max_temp])
    ax.xaxis.set_tick_params(pad=10)

    month_ticks = np.array([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334])/365
    ax.set_xticks(2.0 * np.pi * month_ticks)
    ax.set_xticklabels(['Jan',
                        'Feb',
                        'Mar',
                        'Apr',
                        'May',
                        'Jun',
                        'Jul',
                        'Aug',
                        'Sep',
                        'Oct',
                        'Nov',
                        'Dec'], fontsize=18)

    # Set up axes ticks
    yticks = [min_temp_rounded, min_temp]
    yticklabel = ["", ""]

    for i in range(-100,150,10):
        if (i > min_temp and i < max_temp):
            yticks.append(i)
            yticklabel.append("")

    yticks.append(max_temp)
    yticks.append(max_temp_rounded)
    yticklabel.append("")
    yticklabel.append("")

    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabel)
    ax.set_rlabel_position(135)
    ax.xaxis.set_tick_params(pad=10)
    #ax.yaxis.set_tick_params(pad=45)

    # Set Up Outer Boundary
    ax.annotate(f"{int(max_temp)}$^\circ$F", 
                xy=((2.0 * np.pi * 135/360), max_temp), 
                xytext=((2.0 * np.pi * 135/360), max_temp_rounded+15), 
                ha='center', 
                va='center',
                fontsize=15,
                arrowprops={'arrowstyle': '->', 'color' : "black"})

    # Set Up Inner Boundary
    ax.annotate(f"{int(min_temp)}$^\circ$F", 
                xy=((2.0 * np.pi * 135/360), min_temp), 
                xytext=(0, min_temp_rounded), 
                ha='center', 
                va='center',
                fontsize=15,
                arrowprops={'arrowstyle': '->', 'color' : "black"})

    def init():
        """Init"""
        global rs, thetas

        rs = np.array([])
        thetas = np.array([])

        line.set_segments([])
        title.set_text('')
        return line, title

    def animate(t):
        """Animate"""
        global rs, thetas, current_year, current_day

        if t < data_len:

            # Split up year string into year, month, day
            date_str = data["DATE"][t].strftime('%Y-%m-%d')

            year = date_str.split("-")[0]

            if (year != current_year):
                current_year = year
                current_day = 0

            pbar.update(1)
            pbar.set_description(date_str, refresh=True)

            r = data["TMAX"][t]
            rs = np.append(rs, r)

            # Handle Leap Days
            if ("-02-29" in date_str):
                theta = 2.0 * np.pi * ((current_day-0.5)/365)
                current_day -= 1
            else:
                theta = 2.0 * np.pi * (current_day/365)

            current_day += 1

            thetas = np.append(thetas, theta)

            points = np.array([thetas, rs]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)

            title.set_text(date_str)
            line.set_segments(segments)
            line.set_array(rs)
            marker.set_data(thetas, rs)
        else:
            pbar.set_description("Saving...", refresh=True)

        return line, title


    ani = animation.FuncAnimation(
        fig,
        animate,
        init_func=init,
        frames=int(len(data)) + 180,
        blit=True,
        repeat=False)

    pbar = tqdm(total=len(data), position=0, leave=True, desc="Parsing Data")

    writervideo = animation.FFMpegWriter(fps=60)
    output_filename = os.path.join(output_dir, output_file)
    ani.save(output_filename, dpi=200, writer=writervideo)

    pbar.set_description("Done", refresh=True)

    pbar.close()

if __name__ == "__main__":
    create_max_temp_graphic(input_file="seatac.csv", output_file="output.mp4")