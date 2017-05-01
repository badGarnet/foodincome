from flask import Flask, render_template, request, redirect
from bokeh.embed import components
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Plasma256
import pandas as pd
import numpy as np

foodincomeapp = Flask(__name__)

foodincomeapp.vars={}

@foodincomeapp.route('/foodincomenyc', methods = ['GET'])
def main_app():
    foodincome = pd.read_csv('data/foodincome.csv')
    
    cuisines = foodincome.max_cuisine_description.unique()
    cuisinemap = np.random.choice(range(0,256), cuisines.size).tolist()
    cpal = np.array(Plasma256)[cuisinemap]
    sizes = 20*foodincome.sumpop/foodincome.sumpop.max()

    p = figure(title='number of restaurants vs. income',
               x_axis_label='total income in a zip code area (USD)',
               y_axis_label='number of restaurants',
               x_axis_type="log", x_range=[10**7, 10**11])
    p.scatter(foodincome.fillna(foodincome.sumincome.mean()), 
              foodincome.foodsize, size=sizes, 
              fill_color=cpal, line_color=None)
    
    script, div = components(p)
    return render_template('graph_raw.html', script=script, div=div)

@foodincomeapp.route('/foodincomenyc_tnorm', methods = ['GET'])
def tnorm_app():
    traveltime = np.loadtxt('data/traveltime.txt')
    foodincome = pd.read_csv('data/foodincome.csv')
    
    wt = np.exp(-(traveltime+traveltime.T)/2000)
    timeincome = np.dot((foodincome.fillna(foodincome.sumincome.mean())).sumincome, wt)
    cuisines = foodincome.max_cuisine_description.unique()
    cuisinemap = np.random.choice(range(0,256), cuisines.size).tolist()
    cpal = np.array(Plasma256)[cuisinemap]
    sizes = 20*foodincome.sumpop/foodincome.sumpop.max()

    p = figure(title='number of restaurants vs. income',
               x_axis_label='travel time weighted accessible income',
               y_axis_label='number of restaurants',
               x_axis_type="log")
    p.scatter(timeincome, foodincome.foodsize, size=sizes, fill_color=cpal, 
              line_color=None)
    
    script, div = components(p)
    return render_template('graph_tnorm.html', script=script, div=div)


    
if __name__ == "__main__":
    foodincomeapp.run(port=33507)