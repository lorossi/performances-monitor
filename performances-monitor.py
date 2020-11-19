import json
import time
import psutil
import subprocess
from flask import Flask, render_template, request, jsonify, url_for

def loadSettings(path="src/settings.json"):
    with open(path) as json_file:
        settings = json.load(json_file)
    return settings

def getStats(color_palette, dt=1, default_color="#4CAF50", background_color="#E8E8E8", ext_hdd_path="/mnt/ext_hdd/"):
    return_dict = {}

    try:
        cpu_value = psutil.cpu_percent(interval=dt)
        cpu_percent = f"{psutil.cpu_percent(interval=dt)}%"
        color = color_palette["cpu"][-1]["color"]
        for color in color_palette["cpu"]:
            if cpu_value <= color["value"]:
                color = color["color"]
                break
        max = color_palette["cpu"][-1]["value"]
    except:
        cpu_percent = 0
        cpu_value = "-"
        color = default_color
        max = 0

    return_dict["cpu"] = {
        "value": cpu_value,
        "text": cpu_percent,
        "color": color,
        "max": max
    }

    try:
        ram_value = psutil.virtual_memory().percent
        ram_percent =  f"{psutil.virtual_memory().percent}%"
        color = color_palette["ram"][-1]["color"]
        for color in color_palette["ram"]:
            if ram_value <= color["value"]:
                color = color["color"]
                break
        max = color_palette["ram"][-1]["value"]
    except:
        ram_value = 0
        ram_percent = "-"
        color = default_color
        max = 0

    return_dict["ram"] = {
        "value": ram_value,
        "text": ram_percent,
        "color": color,
        "max": max
    }

    try:
        cpu_temperature_value = psutil.sensors_temperatures()['cpu_thermal'][0][1]
        cpu_temperature = f"{round(psutil.sensors_temperatures()['cpu_thermal'][0][1], 1)}°C"
        color = color_palette["temperature"][-1]["color"]
        for color in color_palette["temperature"]:
            if cpu_temperature_value <= color["value"]:
                color = color["color"]
                break
        max = color_palette["temperature"][-1]["value"]
    except:
        cpu_temperature_value = 0
        cpu_temperature = "-"
        color = default_color
        max = 0

    return_dict["temperature"] = {
        "value": cpu_temperature_value,
        "text": cpu_temperature,
        "color": color,
        "max": max
    }

    try:
        upload = psutil.net_io_counters(pernic=True)['eth0'][0]
        download = psutil.net_io_counters(pernic=True)['eth0'][1]
        time.sleep(dt)
        upload = psutil.net_io_counters(pernic=True)['eth0'][0] - upload
        download = psutil.net_io_counters(pernic=True)['eth0'][1] - download
        total = upload + download
        network_value = total / dt / (1024 ** 2)
        network = f"{round(total / dt / (1024 ** 2), 1)} MB/s"
        color = color_palette["network"][-1]["color"]
        for color in color_palette["network"]:
            if network_value <= color["value"]:
                color = color["color"]
                break
        max = color_palette["network"][-1]["value"]
    except:
        network_value = 0
        network = "-"
        color = default_color
        max = 0

    return_dict["network"] = {
        "value": network_value,
        "text": network,
        "color": color,
        "max": max
    }

    try:
        p = subprocess.Popen("df / --output=pcent".split(" "), stdout=subprocess.PIPE).stdout.read()
        free_hdd_space = p.decode("utf-8").rstrip().split(" ")[1]
        free_hdd_space_value = int(free_hdd_space[:-1])
        color = color_palette["hdd"][-1]["color"]
        for color in color_palette["hdd"]:
            if free_hdd_space_value <= color["value"]:
                color = color["color"]
                break
        max = color_palette["hdd"][-1]["value"]
    except:
        free_hdd_space_value = 0
        free_hdd_space = "-"
        color = default_color
        max = 0

    return_dict["hdd"] = {
        "value": free_hdd_space_value,
        "text": free_hdd_space,
        "color": color,
        "max": max
    }

    try:
        p = subprocess.Popen(f"df {ext_hdd_path} --output=pcent".split(" "), stdout=subprocess.PIPE).stdout.read()
        free_ext_hdd_space = p.decode("utf-8").rstrip().split(" ")[1]
        free_ext_hdd_space_value = int(free_hdd_space[:-1])
        color = color_palette["exthdd"][-1]["color"]
        for color in color_palette["exthdd"]:
            if free_hdd_space_value <= color["value"]:
                color = color["color"]
                break
        max = color_palette["exthdd"][-1]["value"]
    except Exception as e:
        print(e)
        free_ext_hdd_space_value = 0
        free_ext_hdd_space = "-"
        color = default_color
        max = 0

    return_dict["exthdd"] = {
        "value": free_ext_hdd_space_value,
        "text": free_ext_hdd_space,
        "color": color,
        "max": max
    }

    return return_dict

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
    settings = loadSettings()
    background_color = settings["Page"]["background-color"]
    default_color = settings["Page"]["default-color"]
    return render_template('index.html', background_color=background_color, default_color=default_color)

@app.route("/getstats/", methods=['POST'])
def get_stats():
    try:
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
