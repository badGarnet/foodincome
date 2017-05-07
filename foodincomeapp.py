from flask import Flask, render_template, request, redirect
from bokeh.embed import components
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Plasma256
from bokeh.io import hplot
import pandas as pd
import numpy as np

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
    
    sizes = 20*foodincome.sumpop/foodincome.sumpop.max()

    p1 = figure(title='travel time normalized income vs. restaurant count',
               x_axis_label='travel time weighted accessible income',
               y_axis_label='traivel time weighted accessible number of restaurants')
    p1.scatter(timeincome, timefoodsize, size=sizes, line_color=None)
    
    p2 = figure(title='travel time normalized random variable vs. restaurant count',
               x_axis_label='travel time weighted random variable',
               y_axis_label='traivel time weighted accessible number of restaurants')
    p2.scatter(rdtest, timefoodsize, size=sizes, line_color=None)

    hp = hplot(p1, p2)

    script, div = components(hp)
    return render_template('graph_tnorm.html', script=script, div=div)


    
if __name__ == "__main__":
    foodincomeapp.run(port=33507)
