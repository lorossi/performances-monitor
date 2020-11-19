import os
import json
import time
import psutil
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify, url_for

# loads settings from settings file
def loadSettings(path="src/settings.json"):
    with open(path) as json_file:
        settings = json.load(json_file)
    return settings

# returns color and max value according to the provided value
# and the color palette (found in the settings file)
def getColor(value, item, palette):
    color = palette[item][-1]["color"] # default color, in case it's not found
    for color in palette[item]:
        if value <= color["value"]:
            color = color["color"]
            break # we found it, no need to go further
    max = palette[item][-1]["value"] # max value is the one related to last color
    return color, max

# return stats about the system
def getStats(color_palette, dt=1, default_color="#4CAF50", background_color="#E8E8E8", ext_hdd_path="/mnt/ext_hdd/"):
    return_dict = {}

    # section about getting cpu usage
    try:
        value = psutil.cpu_percent(interval=dt)
        text = f"{psutil.cpu_percent(interval=dt)}%"
        color, max = getColor(value, "cpu", color_palette)
    except:
        value = "-"
        text = None
        color = default_color
        max = 0

    return_dict["cpu"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting ram usage
    try:
        value = psutil.virtual_memory().percent
        text =  f"{psutil.virtual_memory().percent}%"
        color, max = getColor(value, "ram", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["ram"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting system load (15 minutes)
    try:
        value = os.getloadavg()[2] # 15 minutes
        text = str(os.getloadavg()[2])
        color, max = getColor(value, "load", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["load"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting cpu temperature
    try:
        value = psutil.sensors_temperatures()['cpu_thermal'][0][1]
        text = f"{round(psutil.sensors_temperatures()['cpu_thermal'][0][1], 1)}°C"
        color, max = getColor(value, "temperature", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["temperature"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting netwok load
    try:
        # total sent and received packets
        upload = psutil.net_io_counters(pernic=True)['eth0'][0]
        download = psutil.net_io_counters(pernic=True)['eth0'][1]
        time.sleep(dt)
        # calculate delta packets sent and received
        upload = psutil.net_io_counters(pernic=True)['eth0'][0] - upload
        download = psutil.net_io_counters(pernic=True)['eth0'][1] - download
        # total bytes exchanged
        total = upload + download
        # convert to MB/s
        value = total / dt / (1024 ** 2)
        text = f"{round(total / dt / (1024 ** 2), 1)} MB/s"
        color, max = getColor(value, "network", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["network"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting free space on main memory
    try:
        p = subprocess.Popen("df / --output=pcent".split(" "), stdout=subprocess.PIPE).stdout.read()
        text = p.decode("utf-8").rstrip().split(" ")[1]
        value = int(text[:-1])
        color, max = getColor(value, "hdd", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["hdd"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting free space on external hdd (if provided)
    try:
        p = subprocess.Popen(f"df {ext_hdd_path} --output=pcent".split(" "), stdout=subprocess.PIPE).stdout.read()
        text = p.decode("utf-8").rstrip().split(" ")[1]
        value = int(text[:-1])
        color, max = getColor(value, "exthdd", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["exthdd"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting thermal throttling status
    # uses vcgencmd so it only works on RPi
    try:
        p = subprocess.Popen("vcgencmd get_throttled".split(" "), stdout=subprocess.PIPE).stdout.read()
        # returns something like "throttling=0x..."
        output = p.decode("utf-8").rstrip()[10:] # strip the string
        int_output = int(output, 16) # convert to number
        if (int_output & 0x4): # bit masking
            value = 3
            text = "Currently throttled"
        elif (int_output & 0x8): # bit masking
            value = 2
            text = "Soft temperature limit"
        elif (int_output & 0x40000): # bit masking
            value = 1
            text = "Throttling occurred"
        else: # otherwise, everthing is ok
            value = 0
            text = "None"

        color, max = getColor(value, "overheating", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["overheating"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting undervoltage
    # uses vcgencmd so it only works on RPi
    try:
        p = subprocess.Popen("vcgencmd get_throttled".split(" "), stdout=subprocess.PIPE).stdout.read()
        # returns something like "throttling=0x..."
        output = p.decode("utf-8").rstrip()[10:] # strip the string
        int_output = int(output, 16) # convert to number

        if (int_output & 0x1): # bit masking
            value = 2
            text = "Currently undervoltage"
        elif (int_output & 0x10000): # bit masking
            value = 1
            text = "Undervoltage occurred"
        else: # otherwise, everthing is ok
            value = 0
            text = "None"

        color, max = getColor(value, "undervoltage", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["undervoltage"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting core voltage
    # uses vcgencmd so it only works on RPi
    try:
        p = subprocess.Popen("vcgencmd measure_volts core".split(" "), stdout=subprocess.PIPE).stdout.read()
        # returns something like "volt=0.0..."
        output = p.decode("utf-8").rstrip()[5:-1] # strip the string
        value = float(output) # convert to number
        text = output
        color, max = getColor(value, "corevoltage", color_palette)
    except:
        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["corevoltage"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting active ssh connections
    try:
        p = subprocess.Popen("who", stdout=subprocess.PIPE).stdout.read()
        output = p.decode("utf-8").rstrip().split("\n")[1:]
        value = len(output)
        text = str(len(output))
        color, max = getColor(value, "sshconnections", color_palette)
    except:

        value = None
        text = "-"
        color = default_color
        max = 0

    return_dict["sshconnections"] = {
        "value": value,
        "text": text,
        "color": color,
        "max": max
    }

    # section about getting active ftp connections
    try:
        p = subprocess.Popen("netstat -n".split(" "), stdout=subprocess.PIPE).stdout.read()
        output = p.decode("utf-8").rstrip().split("\n")[1:]
        vlue = 0
        for line in output:
            # remove multiple spaces and then split every word
            line = " ".join(line.split()).split(" ")
            # check if ":21" (ftp port) in ip
            if ":21" in line[3]:
                vlue += 1

        text = str(vlue)
        color, max = getColor(vlue, "sshconnections", color_palette)
    except:

        vlue = None
        text = "-"
        color = default_color
        max = 0

    return_dict["ftpconnections"] = {
        "value": vlue,
        "text": text,
        "color": color,
        "max": max
    }

    return return_dict

# return stats about the netwok (hostname and ip)
def getNetwork():
    try:
        p = subprocess.Popen("hostname -I".split(" "), stdout=subprocess.PIPE).stdout.read()
        ip = p.decode("utf-8").rstrip().split(" ")[0]
    except:
        ip = ""

    try:
        p = subprocess.Popen("hostname", stdout=subprocess.PIPE).stdout.read()
        hostname = p.decode("utf-8").rstrip()
    except:
        hostname = ""

    return {
        "ip": ip,
        "hostname": hostname
    }

# return system time


app = Flask(__name__)

# index
@app.route('/')
@app.route('/homepage')
def index():
    settings = loadSettings() #loads background_color
    # now we load body background color and stats text color
    background_color = settings["Page"]["background-color"]
    return render_template('index.html', background_color=background_color)

# endpoint to get stats
@app.route("/getstats/", methods=['POST'])
def get_stats():
    # if dt parameter wasn't sent, we default it to 1 second
    try:
        # msec string to seconds
        dt = float(request.form['dt']) / 1000
    except:
        dt  = 1

    settings = loadSettings()
    background_color = settings["Page"]["background-color"]
    default_color = settings["Page"]["default-color"]
    color_palette = settings["Colormap"]
    external_hdd_path = settings["Server"] ["external_hdd_path"]
    stats = getStats(color_palette, ext_hdd_path=external_hdd_path, background_color=background_color, default_color=default_color, dt=dt)
    return jsonify(stats)

# get stats api
@app.route("/api/stats", methods=['GET'])
def api_stats():
    started = datetime.now();
    try:
        dt = float(request.args.get("dt")) / 1000
    except:
        dt = 1

    return_dict = {}

    settings = loadSettings()
    background_color = settings["Page"]["background-color"]
    default_color = settings["Page"]["default-color"]
    color_palette = settings["Colormap"]
    external_hdd_path = settings["Server"] ["external_hdd_path"]
    stats = getStats(color_palette, ext_hdd_path=external_hdd_path, background_color=background_color, default_color=default_color, dt=dt)
    network = getNetwork()
    return_dict["stats"] = stats;
    return_dict["network"] = network;

    ended = datetime.now()
    elapsed = (ended - started).total_seconds() * 1000

    return_dict["info"] = {
        "time": datetime.now().isoformat(),
        "elapsed": elapsed,
        "request_ip": request.remote_addr,
        "dt": dt
    }

    return jsonify(return_dict)

# get time api
@app.route("/api/time", methods=['GET'])
def api_stats():
    return_dict["info"] = {
        "time": datetime.now().isoformat(),
        "request_ip": request.remote_addr,
    }

    return jsonify(return_dict)

# get system time api

# endpoint to get infos about network
@app.route("/getnetwork/", methods=['POST'])
def get_network():
    network = getNetwork()
    return jsonify(network)



if __name__ == '__main__':
    settings = loadSettings()
    app.run(host=settings["Server"]["host"],
            port=settings["Server"]["port"],
            debug=settings["Server"]["debug"])
