#!/usr/bin/env python3
import sys
import re
import progressbar
import argparse
from colorama import init, Fore

init()
progressbar.streams.wrap_stdout()
progressbar.streams.wrap_stderr()
parser = argparse.ArgumentParser()
parser.add_argument('-o', action='store_true', help="Output everything")
parser.add_argument('-no', action='store_true', help="Output nothing")
parser.add_argument('-m', action='store_true', help="Output by Maven only")
parser.add_argument('-i', action='store_true', help="Output INFOS produced by Maven")
parser.add_argument('-w', action='store_true', help="Output WARNINGS produced by Maven")
parser.add_argument('-dc', action='store_true', help="Disable all console colouring")
parser.add_argument('-e', action='store_true', help="Output everything after ERROR produced by Maven")
parser.add_argument('-t', action='store_true', help="Write estimated finish time. ☕️ or ⚔️ ? https://xkcd.com/303/")
parser.add_argument('-n', action='store_true', help="Output artifact names built by Maven")
args = parser.parse_args()
output = args.o
nothing = args.no
maven = args.m
info = args.i
warn = args.w or info
artifacts = args.n
absolute_time = args.t
after_error = args.e
disable_colour = args.dc


def get_colour(colour):
    if disable_colour:
        return ""
    return colour


error_c = "[" + get_colour(Fore.LIGHTRED_EX) + "ERROR" + get_colour(Fore.RESET) + "]"
info_c = "[" + get_colour(Fore.CYAN) + "INFO" + get_colour(Fore.RESET) + "]"
warning_c = "[" + get_colour(Fore.YELLOW) + "WARNING" + get_colour(Fore.RESET) + "]"

error_m = "\[ERROR\]" if maven else "ERROR"
warning_m = "\[WARNING\]" if maven else "WARN"
info_m = "\[INFO\]" if maven else "INFO"

bar_format = \
    [
        "Maven build: ",
        get_colour(Fore.YELLOW),
        progressbar.Percentage(),
        get_colour(Fore.RESET),
        " ",
        progressbar.Counter(format='(%(value)d of %(max_value)d)'),
        get_colour(Fore.LIGHTGREEN_EX),
        progressbar.GranularBar(markers=" ▏▎▍▌▋▊▉█"),
        get_colour(Fore.RESET),
        " ",
        progressbar.Timer(),
        " ",
        get_colour(Fore.MAGENTA),
        progressbar.AbsoluteETA(format='Finishes: %(eta)s', format_finished='Finished at %(eta)s')
        if absolute_time else progressbar.AdaptiveETA(),
        get_colour(Fore.RESET)
    ]


def outputline(line):
    sys.stdout.write(line.replace("[ERROR]", error_c).replace("[INFO]", info_c).replace("[WARNING]", warning_c))

def match():
    count = 0
    bar = None
    error = False
    current_max = 0

    for line in sys.stdin:
        outputted = nothing

        if not outputted:
            match_error = re.findall(error_m, line)
            if len(match_error) > 0 or (error & after_error):
                error = True
                outputted = True
                outputline(line)

        if warn and not outputted:
            match_warn = re.findall(warning_m, line)
            if len(match_warn) > 0:
                outputted = True
                outputline(line)

        if info and not outputted:
            match_info = re.findall(info_m, line)
            if len(match_info) > 0:
                outputted = True
                outputline(line)

        if output and not outputted:
            outputline(line)

        matched = re.findall("\[\d+/\d+\]", line)
        if len(matched) > 0:
            if artifacts:
                nline = line.strip("[INFO] ")
                art = find_between(nline, "Building", "[")
                fline = "{}  {}".format("⚒️️", nline.replace(art, get_colour(Fore.CYAN) + art + get_colour(Fore.RESET)))
                sys.stdout.write(fline)
            prog = matched[0][1:len(matched[0]) - 1]
            fraction = prog.split("/")
            if bar is None or int(fraction[1]) != current_max:
                current_max = int(fraction[1])
                bar = progressbar.ProgressBar(
                    widgets=bar_format,
                    widget_kwargs={'samples': 2},
                    max_value=current_max,
                    redirect_stdout=True)
            count += 1

            # Corner case to allow for chained mvn, or if build resumed then sync
            if count > current_max:
                count = int(fraction[0])

        if bar is not None:
            bar.update(count)

    if bar is not None and not error:
        bar.finish()

    sys.stderr.flush()
    progressbar.streams.flush()


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


if __name__ == "__main__":
    try:
        match()
    except KeyboardInterrupt:
        progressbar.streams.unwrap_stdout()
