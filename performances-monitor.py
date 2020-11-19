import json
import time
import psutil
import subprocess
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

    # section about getting cpu load
    try:
        cpu_value = psutil.cpu_percent(interval=dt)
        cpu_percent = f"{psutil.cpu_percent(interval=dt)}%"
        color, max = getColor(cpu_value, "cpu", color_palette)
    except:
        cpu_percent = None
        cpu_value = "-"
        color = default_color
        max = 0

    return_dict["cpu"] = {
        "value": cpu_value,
        "text": cpu_percent,
        "color": color,
        "max": max
    }

    # section about getting ram load
    try:
        ram_value = psutil.virtual_memory().percent
        ram_percent =  f"{psutil.virtual_memory().percent}%"
        color, max = getColor(ram_value, "ram", color_palette)
    except:
        ram_value = None
        ram_percent = "-"
        color = default_color
        max = 0

    return_dict["ram"] = {
        "value": ram_value,
        "text": ram_percent,
        "color": color,
        "max": max
    }

    # section about getting cpu temperature
    try:
        cpu_temperature_value = psutil.sensors_temperatures()['cpu_thermal'][0][1]
        cpu_temperature = f"{round(psutil.sensors_temperatures()['cpu_thermal'][0][1], 1)}°C"
        color, max = getColor(cpu_temperature_value, "temperature", color_palette)
    except:
        cpu_temperature_value = None
        cpu_temperature = "-"
        color = default_color
        max = 0

    return_dict["temperature"] = {
        "value": cpu_temperature_value,
        "text": cpu_temperature,
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
        network_value = total / dt / (1024 ** 2)
        network = f"{round(total / dt / (1024 ** 2), 1)} MB/s"
        color, max = getColor(network_value, "network", color_palette)
    except:
        network_value = None
        network = "-"
        color = default_color
        max = 0

    return_dict["network"] = {
        "value": network_value,
        "text": network,
        "color": color,
        "max": max
    }

    # section about getting free space on main memory
    try:
        p = subprocess.Popen("df / --output=pcent".split(" "), stdout=subprocess.PIPE).stdout.read()
        free_hdd_space = p.decode("utf-8").rstrip().split(" ")[1]
        free_hdd_space_value = int(free_hdd_space[:-1])
        color, max = getColor(free_hdd_space_value, "hdd", color_palette)
    except:
        free_hdd_space_value = None
        free_hdd_space = "-"
        color = default_color
        max = 0

    return_dict["hdd"] = {
        "value": free_hdd_space_value,
        "text": free_hdd_space,
        "color": color,
        "max": max
    }

    # section about getting free space on external hdd (if provided)
    try:
        p = subprocess.Popen(f"df {ext_hdd_path} --output=pcent".split(" "), stdout=subprocess.PIPE).stdout.read()
        free_ext_hdd_space = p.decode("utf-8").rstrip().split(" ")[1]
        free_ext_hdd_space_value = int(free_hdd_space[:-1])
        color, max = getColor(free_ext_hdd_space_value, "exthdd", color_palette)
    except:
        free_ext_hdd_space_value = None
        free_ext_hdd_space = "-"
        color = default_color
        max = 0

    return_dict["exthdd"] = {
        "value": free_ext_hdd_space_value,
        "text": free_ext_hdd_space,
        "color": color,
        "max": max
    }

    # section about getting thermal throttling status
    try:
        p = subprocess.Popen("vcgencmd get_throttled".split(" "), stdout=subprocess.PIPE).stdout.read()
        # returns something like "throttling=0x..."
        output = p.decode("utf-8").rstrip()[10:] # strip the string
        int_output = int(output, 16) # convert to number
        if (int_output == 0): # if zero, everthing is ok
            overheating_value = 0
            overheating_text = "none"
        elif (int_output & 0x4): # bit masking
            overheating_value = 3
            overheating_text = "currently throttled"
        elif (int_output & 0x8): # bit masking
            overheating_value = 2
            overheating_text = "soft temperature limit"
        elif (int_output & 0x40000): # bit masking
            overheating_value = 1
            overheating_text = "throttling occurred"

        color, max = getColor(overheating_value, "overheating", color_palette)
    except:
        overheating_value = None
        overheating_text = "-"
        color = default_color
        max = 0

    return_dict["overheating"] = {
        "value": overheating_value,
        "text": overheating_text,
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


app = Flask(__name__)
@app.route('/')
@app.route('/homepage')
def index():
    settings = loadSettings() #loads background_color
    # now we load body background color and stats text color
    background_color = settings["Page"]["background-color"]
    return render_template('index.html', background_color=background_color)

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

@app.route("/getnetwork/", methods=['POST'])
def get_network():
    network = getNetwork()
    return jsonify(network)

if __name__ == '__main__':
    settings = loadSettings()
    app.run(host=settings["Server"]["host"],
            port=settings["Server"]["port"],
            debug=settings["Server"]["debug"])
