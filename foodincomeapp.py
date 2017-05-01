from flask import Flask, render_template, request, redirect
from bokeh.embed import components
from bokeh.plotting import figure, output_file, show
import pandas as pd
import numpy as np

foodincomeapp = Flask(__name__)

foodincomeapp.vars={}

@foodincomeapp.route('/index', methods = ['GET'])
def foodincomeapp():
    traveltime = np.loadtxt('data/traveltime.txt')
    foodincome = pd.read_csv('data/foodincome.csv')
    
    wt = np.exp(-(traveltime+traveltime.T)/2000)
    timeincome = np.dot((foodincome.fillna(foodincome.sumincome.mean())).sumincome, wt)
    p = figure(title='number of restaurants vs. income',
               x_axis_label='total income in a zip code area (USD)',
               y_axis_label='number of restaurants')
    p.scatter(timeincome, foodincome.foodsize)
    
    script, div = components(p)
    return render_template('graph.html', script=script, div=div)

    
if __name__ == '__main__':
    foodincomeapp.run(port=33507)