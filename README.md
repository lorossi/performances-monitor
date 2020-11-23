# Performances monitor
`Because sometimes opening htop is too much work`

I wanted a quick way to check at any available moment if my RaspberryPi was overheating or the RAM was getting full, so I wrote this webpage.

For some stats *(core voltage, overheating, undervoltage)* it uses the command `vcgencmd`, so it won't work outside Raspbian. For all the others stats, *os* and *psutils* have been used, so it should work on any Linux os (I personally checked Ubuntu but every should work).

*This program won't work on Windows.* If you need to do so, you might want to look into [WSL](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux) (that's basically reverse Wine).

The code is PEP-8 compliant. The backend is based on Flask library for Python3, the frontend is written in JS with jQuery.

## Features

This (hopefully) clean and easy-on-the-eyes ui will show all the important stats about your hardware in a compact manner. As you can see in the screenshots, it features:

1. Scalable UI (works both on PC and mobile of any size)
2. Many stats shown with different background colors according to their current value. The interval and the colors can be tweaked by editing `settings.json` (found in the `src` folder)
3. Simple visualization via graph of the stats over time
4. Tap *(or click*) on a stat to see it full screen
5. Highly customizable stylesheet files thanks to an heavy usage of *CSS* vars
6. A clean, well commented code (Python code is PEP-8 compliant)
7. Full logging of errors
8. Public APIs to get all the stats about the devices (see below for more infos)
9. A cool loading GIF made completely in CSS

## Screenshots
![View on a large screen](https://github.com/lorossi/performances-monitor/blob/master/screenshots/large-screen.png)
![View on a small screen](https://github.com/lorossi/performances-monitor/blob/master/screenshots/small-screen.png)
![Fullscreen visualization on small screen](https://github.com/lorossi/performances-monitor/blob/master/screenshots/fullscreen-small-screen.png)
![Error on small screen](https://github.com/lorossi/performances-monitor/blob/master/screenshots/error-small-screen.png)

## Installation
1. Clone the repo in any folder
2. Install the required dependencies using `pip install -r requirements.txt`
3. Customize the setting file located in *src/settings.json* according to your needs
4. Run the python script via `python3 performances-monitor.py`
5. There you go! The webpage will now be viewable inside your browser

## Api endpoints
- `/api/stats?dt=[msec]` to get all the stats. The bigger the `dt` parameter is, the more the request will take but it will be more accurate
- `api/time` to get the machine current time
- `api/temperature` to get the machine current temperature

## Credits
The font used is [_Roboto_ by _Christian Robertson_.](https://github.com/google/roboto/)

Loading icon by [_loading.io_](https://loading.io/css/)

## Licensing
This project is distributed under Attribution 4.0 International (CC BY 4.0) license.
