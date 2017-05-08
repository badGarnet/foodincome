from flask import Flask, render_template, request, redirect
from bokeh.embed import components
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Viridis6 as palette
from bokeh.io import hplot
from bokeh.io import show
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    LogColorMapper
)
from bokeh.models.widgets import Panel, Tabs
import pandas as pd
import numpy as np
import json

foodincomeapp = Flask(__name__)

foodincomeapp.vars={}

def getcolors(s):
    cuisines = s.unique()
    cuisinemap = np.random.choice(range(0,256), cuisines.size).tolist()
    cpal = np.array(Plasma256)[cuisinemap]
    cmap = dict(zip(cuisines, cpal))
    return s.map(cmap).tolist()

@foodincomeapp.route('/foodincomenyc', methods = ['GET'])
def main_app():
    foodincome = pd.read_csv('data/foodincomezip.csv')
    
    sizes = 20*foodincome.sumpop/foodincome.sumpop.max()

    p = figure(title='number of restaurants vs. income',
               x_axis_label='total income in a zip code area (USD)',
               y_axis_label='number of restaurants in a zip code area',
               x_axis_type='log')
    p.scatter(foodincome['sumincome'],foodincome.foodsize, size=sizes, line_color=None)
    
    script, div = components(p)
    return render_template('graph_raw.html', script=script, div=div)

@foodincomeapp.route('/foodincomenyc_tnorm', methods = ['GET'])
def tnorm_app():
    traveltime = np.loadtxt('data/traveltime.txt')
    foodincome = pd.read_csv('data/foodincomezip.csv')
    
    wt = np.exp(-(traveltime+traveltime.T)/500)
    rdtest = np.random.uniform(0, 1, wt.shape[0])
    timeincome = np.dot(foodincome['sumincome'], wt)
    timefoodsize = np.dot(foodincome['foodsize'], wt)
    timerd = np.dot(rdtest, wt)
    
    sizes = 20*foodincome.sumpop/foodincome.sumpop.max()

    p1 = figure(title='travel time normalized income vs. restaurant count',
               x_axis_label='travel time weighted accessible income',
               y_axis_label='traivel time weighted accessible number of restaurants')
    p1.scatter(timeincome, timefoodsize, size=sizes, line_color=None)
    
    p2 = figure(title='travel time normalized random variable vs. restaurant count',
               x_axis_label='travel time weighted random variable',
               y_axis_label='traivel time weighted accessible number of restaurants')
    p2.scatter(timerd, timefoodsize, size=sizes, line_color=None)

    hp = hplot(p1, p2)

    script, div = components(hp)
    return render_template('graph_tnorm.html', script=script, div=div)

def getmapplot(cord, rate, maptitle, htext):
    source = ColumnDataSource(data=dict(
        x=cord['x'],
        y=cord['y'],
        name=cord['zipcode'],
        rate=rate,
    ))
    TOOLS = "pan,wheel_zoom,reset,hover,save"
    color_mapper = LogColorMapper(palette=palette)

    p = figure(title=maptitle, tools=TOOLS, x_axis_location=None, 
        y_axis_location=None)
    p.grid.grid_line_color = None

    p.patches('x', 'y', source=source,
          fill_color={'field': 'rate', 'transform': color_mapper},
          fill_alpha=0.7, line_color="white", line_width=0.5)

    hover = p.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [
        ("Zip Code", "@name"),
        (htext, "@rate"),
    ]
    return p

@foodincomeapp.route('/seattle', methods = ['GET'])
def seattle_app():
    traveltime = np.loadtxt('data/sea_ttime.txt')
    foodincome = pd.read_csv('data/sea_foodincomezip.csv')
    with open('data/seazip_cord', 'r') as f:
        try:
            sea_cord = json.load(f)
        except ValueError:
            sea_cord = {}
    
    wt = np.exp(-traveltime/500)
    rdtest = np.random.uniform(0, 1, wt.shape[0])
    timeincome = np.dot(foodincome['sumincome'], wt)
    timefoodsize = np.dot(foodincome['foodsize'], wt)
    timerd = np.dot(rdtest, wt)

    p1 = getmapplot(sea_cord, foodincome.sumincome, 'income', 'income')
    p2 = getmapplot(sea_cord, timeincome, 'accessible income', 'accessible income')
    p3 = getmapplot(sea_cord, foodincome.foodsize, 'number of restaurants', '# restaurants')
    tab1 = Panel(child=p1, title='income')
    tab2 = Panel(child=p2, title='accessible income')
    tab3 = Panel(child=p3, title='current restaurant density')

    tabs = Tabs(tabs=[tab1, tab2, tab3])
    script, div = components(tabs)

    return render_template('graph_seattle.html', script=script, div=div)


    
if __name__ == "__main__":
    foodincomeapp.run(port=33507)
