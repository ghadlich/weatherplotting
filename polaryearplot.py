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

_year_plot_rs = np.array([])
_year_plot_rs_all = np.array([])
_year_plot_current_points = None
_year_plot_all_points = None
_year_plot_current_year = 0
_year_plot_current_day = 0

def create_max_temp_graphic(caption="Daily High Temperatures", data_dir="data", input_file="seatac.csv", output_dir="output", output_file="output.mp4", target_duration_seconds=None, gray_out_bg=True):
    """
    Creates an animated graphic of daily maximum temperatures over time.

    Args:
        caption (str, optional): The title of the graphic. Defaults to "Daily High Temperatures".
        data_dir (str, optional): The directory containing the input data file. Defaults to "data".
        input_file (str, optional): The input data file in CSV format. Defaults to "seatac.csv".
        output_dir (str, optional): The directory to save the output files. Defaults to "output".
        output_file (str, optional): The output file name. Defaults to "output.mp4".
        target_duration_seconds (int, optional): The target duration of mp4. Defaults to 10 seconds.
        gray_out_bg (bool, optional): Determines if the background should be grayed out. Defaults to True.
    """

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load the temperature data from the CSV file
    csv_filename = os.path.join(data_dir, input_file)
    data = pandas.read_csv(
        csv_filename,
        infer_datetime_format=True,
        parse_dates=['DATE'],
        usecols=['DATE', 'TMAX'])

    # Interpolate for any missing days
    data = data.interpolate()

    # Set Up Plot Limits
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

    # Put a circle in the middle
    circle = plt.Circle((0, 0), min_temp-min_temp_rounded-1, transform=ax.transData._b, color="white")
    ax.add_artist(circle)

    # Create a moving dot on the plot
    marker, = ax.plot([], [], '.', color='black')

    # Set up color maps for the line segments
    norm=plt.Normalize(
                min_temp,
                max_temp)
    cvals  = [min_temp, (max_temp-min_temp)/2, max_temp]

    tempcolors = ["blue", "mediumslateblue", "red"]

    if gray_out_bg == True:
        colors = ["silver","silver","silver"]
    else:
        colors = tempcolors

    tuples = list(zip(map(norm,cvals), colors))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", tuples)

    # Create the background line
    bg = collections.LineCollection(
        [],
        linewidth=5,
        alpha=.75,
        cmap=cmap,
        norm=norm)
    ax.add_collection(bg)

    # Create the current year line
    tuples = list(zip(map(norm,cvals), tempcolors))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", tuples)

    line = collections.LineCollection(
        [],
        linewidth=5,
        alpha=.75,
        cmap=cmap,
        norm=norm)
    ax.add_collection(line)
    title = ax.text(-0.11, 0.0, '', fontsize=20, transform=ax.transAxes)
    caption1 = ax.text(-0.11,
                    1.1,
                    caption,
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

    # Set Up Outer Boundary Note
    ax.annotate(f"{int(max_temp)}$^\circ$F",
                xy=((2.0 * np.pi * 135/360), max_temp),
                xytext=((2.0 * np.pi * 135/360), max_temp_rounded+15),
                ha='center',
                va='center',
                fontsize=15,
                arrowprops={'arrowstyle': '->', 'color' : "black"})

    # Set Up Inner Boundary Note
    ax.annotate(f"{int(min_temp)}$^\circ$F",
                xy=((2.0 * np.pi * 135/360), min_temp),
                xytext=(0, min_temp_rounded),
                ha='center',
                va='center',
                fontsize=15,
                arrowprops={'arrowstyle': '->', 'color' : "black"})

    # Set Up Outer Tick Boundary Note
    ax.annotate(f"{int(yticks[-3])}$^\circ$F",
                xy=((2.0 * np.pi * 103/360), yticks[-3]),
                xytext=((2.0 * np.pi * 103/360), max_temp_rounded+15),
                ha='center',
                va='center',
                fontsize=15,
                arrowprops={'arrowstyle': '->', 'color' : "black"})

############### Start Inline ###############
    def init():
        """
        Initializes the plot with empty arrays and text elements.

        Returns:
            tuple: A tuple containing the line, background, and title objects.
        """
        global _year_plot_rs, _year_plot_rs_all, _year_plot_current_points, _year_plot_all_points

        _year_plot_rs = np.array([])
        _year_plot_rs_all = np.array([])
        _year_plot_current_points = np.array([])
        _year_plot_all_points = np.array([])

        line.set_segments([])
        bg.set_segments([])
        title.set_text('')
        return line, title

    def animate(t):
        """Animate"""
        global _year_plot_rs, _year_plot_rs_all, _year_plot_current_year, _year_plot_current_day, _year_plot_current_points, _year_plot_all_points

        if t < data_len:

            # Split up year string into year, month, day
            # TODO: Split out data specific parsing and take tuple of data.
            date_str = data["DATE"][t].strftime('%Y-%m-%d')

            year = date_str.split("-")[0]

            if (year != _year_plot_current_year):
                _year_plot_current_year = year
                _year_plot_current_day = 0

                if len(_year_plot_current_points) > 0:
                    if len(_year_plot_all_points) == 0:
                        _year_plot_all_points = _year_plot_current_points
                    else:
                        _year_plot_all_points = np.concatenate((_year_plot_all_points, _year_plot_current_points))

                    # Calculate the background line
                    segments = np.concatenate([_year_plot_all_points[:-1], _year_plot_all_points[1:]], axis=1)
                    _year_plot_rs_all = np.append(_year_plot_rs_all, _year_plot_rs)
                    bg.set_segments(segments)
                    bg.set_array(_year_plot_rs_all)

                    # Reset the current line
                    _year_plot_current_points = np.array([])
                    _year_plot_rs = np.array([])
                    line.set_segments([])

            pbar.update(1)
            pbar.set_description(date_str, refresh=True)

            r = data["TMAX"][t]
            _year_plot_rs = np.append(_year_plot_rs, r)

            # Handle Leap Days
            if ("-02-29" in date_str):
                theta = 2.0 * np.pi * ((_year_plot_current_day-0.5)/365)
                _year_plot_current_day -= 1
            else:
                theta = 2.0 * np.pi * (_year_plot_current_day/365)

            _year_plot_current_day += 1

            if (len(_year_plot_current_points) == 0):
                _year_plot_current_points = np.array([[[theta, r]]])
            else:
                _year_plot_current_points = np.concatenate((_year_plot_current_points, np.array([[[theta, r]]])))

            segments = np.concatenate([_year_plot_current_points[:-1], _year_plot_current_points[1:]], axis=1)

            title.set_text(date_str)
            line.set_segments(segments)
            line.set_array(_year_plot_rs)
            marker.set_data([theta], [r])
        else:
            pbar.update(1)
            pbar.set_description("Finalizing...", refresh=True)

        return line, bg, title
############### End Inline ###############

    output_filename = os.path.join(output_dir, output_file)

    # How long to pause at end
    pause_seconds = 5

    # Try to match the FPS to the requested duration
    if (target_duration_seconds != None):
        data_duration_seconds = target_duration_seconds - pause_seconds
        data_frames = len(data)

        if (".mp4" in output_filename):
            fps = max(int(data_frames/data_duration_seconds), 1)

        elif (".gif" in output_filename):
            # Keep at 60, it is flaky otherwise
            fps = 60
    else:
        # Default to 60 fps
        fps = 60
    
    pause_frames = pause_seconds * fps

    ani = animation.FuncAnimation(
        fig,
        animate,
        init_func=init,
        frames=int(len(data)) + pause_frames, # Add in pause in the end
        blit=True,
        repeat=False)

    pbar = tqdm(total=(len(data) + pause_frames), position=0, leave=True, desc="Parsing Data")

    if (".mp4" in output_filename):
        writervideo = animation.FFMpegWriter(fps=fps)
        ani.save(output_filename, dpi=200, writer=writervideo)
    elif (".gif" in output_filename):
        ani.save(output_filename, dpi=200, fps=fps)

    fig.savefig(os.path.join(output_dir, output_file+".png"), dpi=200)

    pbar.set_description("Done", refresh=True)

    pbar.close()

if __name__ == "__main__":
    create_max_temp_graphic(caption='Seattle Daily High Temperatures (1948-2023)',
                            input_file="seatac.csv",
                            output_file="seatac1948_1min.mp4",
                            target_duration_seconds=65)
