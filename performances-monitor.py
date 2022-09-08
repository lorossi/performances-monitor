# This code is PEP-8 compliant
# I hope this is commented well enough!
# Made by Lorenzo Rossi


import os
import json
import time
import psutil
import logging
import subprocess

from datetime import datetime
from flask import Flask, render_template, request, jsonify


def load_settings(path="static/src/settings.json") -> dict[str, str | int]:
    """Load settings from file

    Args:
        path (str, optional): Settings file path. \
        Defaults to "static/src/settings.json".

    Returns:
        dict[str, str | int]
    """
    with open(path) as json_file:
        return json.load(json_file)


def run_command(command: str) -> str:
    """Run command and return the output

    Args:
        command (str): command to be run in shell

    Returns:
        str
    """
    p = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE).stdout
    return p.read().decode("utf-8").rstrip()


# returns color and max value according to the provided value
# and the color palette (found in the settings file)
def get_color(
    value: float, item: str, palette: dict[str, dict[str, str]]
) -> tuple[str, float]:
    """Returns color and max value according to the provided value and \
    the color palette

    Args:
        value (float): value to match
        item (str): item to look the color palette for
        palette (dict[str, dict[str, str]]): color palette

    Returns:
        tuple[str, float]: color and max value
    """
    color = palette["default"]["color"]  # default color
    max_value = palette["default"]["value"]  # default max

    # wanted item is not in the palette
    if item not in palette.keys():
        return color, max_value

    for color in palette[item]:
        if color == "default":
            continue

        if value <= color["value"]:
            color = color["color"]
            break  # we found it, no need to go further

    max_value = palette[item][-1]["value"]  # max value is the last
    return color, max_value


# return stats about the system
def _get_stats(
    color_palette: dict[str, dict[str, str]],
    dt: float = 1,
    ext_hdd_path: str = "/mnt/ext_hdd/",
) -> dict[str, dict[str, str | float]]:
    """Return stats about the system

    Args:
        color_palette (dict[str, dict[str, str]]): color palette
        dt (float, optional): time delta. Defaults to 1.
        ext_hdd_path (str, optional): path of external HDD. \
            Defaults to "/mnt/ext_hdd/".

    Returns:
        dict[str, dict[str, str | float]]
    """
    return_dict = {}

    # section about getting cpu usage
    try:
        value = psutil.cpu_percent(interval=dt)
        text = f"{value}%"
        color, max = get_color(value, "cpu", color_palette)
    except Exception as e:
        logging.warning("cannot read cpu percentage. error: %s", e)
        value = "-"
        text = None
        color = None
        max = 0

    return_dict["cpu"] = {"value": value, "text": text, "color": color, "max": max}

    # section about getting ram usage
    try:
        value = psutil.virtual_memory().percent
        text = f"{value}%"
        color, max = get_color(value, "ram", color_palette)
    except Exception as e:
        logging.warning("cannot read ran percentage. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["ram"] = {"value": value, "text": text, "color": color, "max": max}

    # section about getting system load (15 minutes)
    try:
        value = os.getloadavg()[2]  # 15 minutes average
        text = str(value)
        color, max = get_color(value, "load", color_palette)
    except Exception as e:
        logging.warning("cannot read cpu load. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["load"] = {"value": value, "text": text, "color": color, "max": max}

    # section about getting cpu temperature
    try:
        value = psutil.sensors_temperatures()["cpu_thermal"][0][1]
        text = f"{round(value, 1)}°C"
        color, max = get_color(value, "temperature", color_palette)
    except Exception as e:
        logging.warning("cannot read cpu temperature. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["temperature"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max,
    }

    # section about getting network load
    try:
        # total sent and received packets
        upload = psutil.net_io_counters(pernic=True)["eth0"][0]
        download = psutil.net_io_counters(pernic=True)["eth0"][1]
        time.sleep(dt)
        # calculate delta packets sent and received
        upload = psutil.net_io_counters(pernic=True)["eth0"][0] - upload
        download = psutil.net_io_counters(pernic=True)["eth0"][1] - download
        # total bytes exchanged
        total = upload + download
        # convert to MB/s
        value = total / dt / (1024 ** 2)
        text = f"{round(value, 1)} MB/s"
        color, max = get_color(value, "network", color_palette)
    except Exception as e:
        logging.warning("cannot read network load. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["network"] = {"value": value, "text": text, "color": color, "max": max}

    # section about getting free space on main memory
    try:
        command = "df / --output=pcent"
        text = run_command(command).split(" ")[1]
        value = int(text[:-1])
        color, max = get_color(value, "hdd", color_palette)
    except Exception as e:
        logging.warning("cannot read hdd space. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["hdd"] = {"value": value, "text": text, "color": color, "max": max}

    # section about getting free space on external hdd (if provided)
    try:
        command = f"df {ext_hdd_path} --output=pcent"
        text = run_command(command).split(" ")[1]
        value = int(text[:-1])
        color, max = get_color(value, "exthdd", color_palette)
    except Exception as e:
        logging.warning("cannot read exthdd space. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["exthdd"] = {"value": value, "text": text, "color": color, "max": max}

    # section about getting thermal throttling status
    # uses vcgencmd so it only works on RPi
    try:
        command = "vcgencmd get_throttled"
        # returns something like "throttling=0x..."
        output = run_command(command)[10:]  # strip the string
        int_output = int(output, 16)  # convert to number
        if int_output & 0x4:  # bit masking
            value = 3
            text = "Currently throttled"
        elif int_output & 0x8:  # bit masking
            value = 2
            text = "Soft temperature limit"
        elif int_output & 0x40000:  # bit masking
            value = 1
            text = "Throttling occurred"
        else:  # otherwise, everything is ok
            value = 0
            text = "None"

        color, max = get_color(value, "overheating", color_palette)
    except Exception as e:
        logging.warning("cannot read cpu overheating. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["overheating"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max,
    }

    # section about getting undervoltage
    # uses vcgencmd so it only works on RPi
    try:
        command = "vcgencmd get_throttled"
        # returns something like "throttling=0x..."
        output = run_command(command)[10:]  # strip the string
        int_output = int(output, 16)  # convert to number

        if int_output & 0x1:  # bit masking
            value = 2
            text = "Currently undervoltage"
        elif int_output & 0x10000:  # bit masking
            value = 1
            text = "Undervoltage occurred"
        else:  # otherwise, everything is ok
            value = 0
            text = "None"

        color, max = get_color(value, "undervoltage", color_palette)
    except Exception as e:
        logging.warning("cannot read cpu undervoltage. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["undervoltage"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max,
    }

    # section about getting core voltage
    # uses vcgencmd so it only works on RPi
    try:
        command = "vcgencmd measure_volts core"
        # returns something like "volt=0.0..."
        output = run_command(command)[5:-1]  # strip the string
        value = float(output)  # convert to number
        text = output
        color, max = get_color(value, "corevoltage", color_palette)
    except Exception as e:
        logging.warning("cannot read cpu core voltage. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["corevoltage"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max,
    }

    # section about getting active ssh connections
    try:
        command = "who"
        output = run_command(command).split("\n")[1:]
        value = len(output)
        text = str(value)
        color, max = get_color(value, "sshconnections", color_palette)
    except Exception as e:
        logging.warning("cannot read active ssh connections. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["sshconnections"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max,
    }

    # section about getting active ftp connections
    try:
        command = "netstat -n"
        output = run_command(command).split("\n")[1:]
        ips = []
        for line in output:
            # remove multiple spaces and then split every word
            line = " ".join(line.split()).split(" ")
            # check if ":21" (ftp port) in ip
            if ":21" in line[3]:
                ips.append(line[3])

        ips = list(set(ips))  # remove duplicates
        value = len(ips)
        text = str(value)
        color, max = get_color(value, "ftpconnections", color_palette)
    except Exception as e:
        logging.warning("cannot active ftp connections. error: %s", e)
        value = None
        text = "-"
        color = None
        max = 0

    return_dict["ftpconnections"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max,
    }

    return return_dict


# return stats about the network (hostname and ip)
def _get_network() -> dict[str, str]:
    """Return stats about the network (hostname and ip)

    Returns:
        dict[str, str]
    """
    try:
        command = "hostname -I"
        ip = run_command(command).split(" ")[0]
    except Exception as e:
        logging.warning("cannot read hostname. error: %s", e)
        ip = ""

    try:
        command = "hostname"
        hostname = run_command(command)
    except Exception as e:
        logging.warning("cannot read local ip. error: %s", e)
        hostname = ""

    return {"ip": ip, "hostname": hostname}


app = Flask(__name__)


# index
@app.route("/")
@app.route("/homepage")
def index():
    # now we load body background color and stats text color
    return render_template("index.html")


# error 404 page
@app.errorhandler(404)
def error_400(e):
    logging.error("error 404: %s", e)
    return (
        render_template("error.html", errorcode=404, errordescription="page not found"),
        404,
    )


# error 500 page
@app.errorhandler(Exception)
def error_500(e):
    logging.error("error 500: %s", e)
    return (
        render_template(
            "error.html", errorcode=500, errordescription="internal server error"
        ),
        500,
    )


# endpoint to get stats
@app.route("/getstats/", methods=["GET"])
def get_stats():
    # if dt parameter wasn't sent, we default it to 1 second
    try:
        # msec string to seconds
        dt = float(request.form["dt"]) / 1000
    except Exception as e:
        logging.warning("error while parsing stats dt: %s", e)
        dt = 1

    settings = load_settings()
    color_palette = settings["Colormap"]
    external_hdd_path = settings["Server"]["external_hdd_path"]
    stats = _get_stats(color_palette, ext_hdd_path=external_hdd_path, dt=dt)
    return jsonify(stats)


# endpoint to get infos about network
@app.route("/getnetwork/", methods=["GET"])
def getnetwork():
    network = _get_network()
    return jsonify(network)


# api endpoint to get stats
@app.route("/api/stats", methods=["GET"])
def api_stats():
    return_dict = {}

    started = datetime.now()
    try:
        dt = float(request.args.get("dt")) / 1000
    except Exception as e:
        logging.warning("error while parsing api stats dt: %s", e)
        dt = 1

    settings = load_settings()
    color_palette = settings["Colormap"]
    external_hdd_path = settings["Server"]["external_hdd_path"]
    stats = get_stats(color_palette, ext_hdd_path=external_hdd_path, dt=dt)
    network = _get_network()
    return_dict["stats"] = stats
    return_dict["network"] = network

    ended = datetime.now()
    elapsed = (ended - started).total_seconds() * 1000

    return_dict["info"] = {
        "time": datetime.now().isoformat(),
        "elapsed": elapsed,
        "request_ip": request.remote_addr,
        "dt": dt,
    }

    return jsonify(return_dict)


# api endpoint to get temperature
@app.route("/api/temperature", methods=["GET"])
def api_temperature():
    return_dict = {}

    started = datetime.now()
    value = psutil.sensors_temperatures()["cpu_thermal"][0][1]
    text = f"{value}°C"
    ended = datetime.now()
    elapsed = (ended - started).total_seconds() * 1000

    return_dict = {
        "time": datetime.now().isoformat(),
        "elapsed": elapsed,
        "request_ip": request.remote_addr,
        "temperature": value,
        "temperature_formatted": text,
    }

    return jsonify(return_dict)


# api endpoint to current time temperature
@app.route("/api/time", methods=["GET"])
def api_time():
    return_dict = {
        "time": datetime.now().isoformat(),
        "request_ip": request.remote_addr,
    }

    return jsonify(return_dict)


if __name__ == "__main__":
    settings = load_settings()

    verbose_logging = settings["Server"]["verbose_logging"]
    if verbose_logging:
        logging.basicConfig(
            filename="performances-monitor.log",
            level=logging.INFO,
            filemode="w",
            format="%(asctime)s %(levelname)s %(message)s",
        )
    else:
        logging.basicConfig(
            filename="performances-monitor.log",
            level=logging.ERROR,
            filemode="w",
            format="%(asctime)s %(levelname)s %(message)s",
        )

    app.run(
        host=settings["Server"]["host"],
        port=settings["Server"]["port"],
        debug=settings["Server"]["debug"],
    )
