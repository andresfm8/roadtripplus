# RoadTrip+

This is a road trip planner website allowing you to create a trip by adding destinations to view on a map. You will also be able to view a summary of your road trip which includes the total time and distance of the trip. 

:round_pushpin:Check it out: domain here

# :motorway:Motivation

We were interested in creating an organized and easy to use road trip planner to make planning more fun. 

# :gear:Setup
## Installation

Make sure you have python3 and pip installed


Create and activate virtual environment using virtualenv
```bash
$ python -m venv python3-virtualenv
$ source python3-virtualenv/bin/activate
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all dependencies

```bash
pip install -r requirements.txt
```

## Usage

Create a .env file using the example.env template

Start flask development server
```bash
$ export FLASK_ENV=development
$ flask run
```
# :rocket:Deployment on AWS
![aws instance](https://user-images.githubusercontent.com/73494041/130258333-d9f74283-d158-4cab-9194-8f07d3ed9bb8.PNG)


# :world_map:Features

* A Google Maps which displays a customizable route
* A trip summary including the total time and distance of the trip

# :computer:Technologies

* Front-End: HTML, CSS
* Back-End: Python, Flask
