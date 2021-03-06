from flask import Flask, render_template, request, redirect
from bokeh.embed import components
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import Viridis11 as palette
from bokeh.layouts import row
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

@foodincomeapp.route('/', methods = ['GET'])
def index_app():
    return redirect('/houston')

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
    # return render_template('graph_raw.html', script=script, div=div)
    return redirect('/nyc')

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

    hp = row(p1, p2)

    script, div = components(hp)
    # return render_template('graph_tnorm.html', script=script, div=div)
    return redirect('/nyc')

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

def getdotplot(x, y, hdata, xname, yname, hname, xtype, ytype):
    source = ColumnDataSource(data=dict(
        x = x, y = y, hdata = hdata,
    ))
    TOOLS = "pan,wheel_zoom,reset,hover,save"
    p = figure(x_axis_label=xname, y_axis_label=yname, tools=TOOLS,\
                x_axis_type=xtype, y_axis_type=ytype)

    p.scatter('x', 'y', size=10, line_color='Black', source=source)

    hover = p.select_one(HoverTool)
    hover.point_policy = "follow_mouse"
    hover.tooltips = [
        (hname, "@hdata"),
    ]
    return p


def assembledisplay(ttime, df, t0, zipxy, cname):
    """calculate time weighted features"""
    wt = np.exp(-ttime/t0)
    timeincome = np.dot(df['sumincome'], wt)
    timefoodsize = np.dot(df['foodsize'], wt)
    timepop = np.dot(df['sumpop'], wt)

    """assembling plots for tabbed view"""
    p11 = getmapplot(zipxy, df.foodsize, cname+' number of restaurants', '# restaurants')
    p12 = getmapplot(zipxy, df.sumincome, cname+' income', 'income')
    # p22 = getmapplot(zipxy, df.sumpop, cname+' number of households', '# household')
    h1 = row(p11, p12)

    p21 = getmapplot(zipxy, df.foodsize, cname+' number of restaurants', '# restaurants')
    p22 = getmapplot(zipxy, timeincome, cname+' accessible income', 'income')
    #p32 = getmapplot(zipxy, timepop, cname+' assessible households', '# households')
    h2 = row(p21, p22)

    # p31 = figure(x_axis_label='income', y_axis_label='restaurant count')
    # p31.circle(df.sumincome, df.foodsize)
    p31 = getdotplot(df.sumincome, df.foodsize, df['zip code'], \
                    'income (USD)', 'restaurant count', 'zip code', \
                     'linear', 'linear')
    p32 = getdotplot(timeincome, df.foodsize, df['zip code'], \
                    'accessible income (USD)', 'restaurant count', 'zip code', \
                     'linear', 'linear')
    h3 = row(p31, p32)

    tab1 = Panel(child=h1, title='local income')
    tab2 = Panel(child=h2, title='accessible income')
    tab3 = Panel(child=h3, title='correlations')

    tabs = Tabs(tabs=[tab1, tab2, tab3])
    script, div = components(tabs)
    return script, div

def getcorr_t0(t0, df, ttime):
    corrs = np.zeros(shape=(t0.size, 2))
    i = 0
    for a in t0:
        wt = np.exp(-ttime/a)
        # wt[wt<0.1]=0.1
        timeincome = np.dot(df.sumincome, wt)
        timefoodzie = np.dot(df.foodsize, wt)
        rdtest = np.random.uniform(0,1,wt.shape[0])
        unitest = np.ones(shape=(rdtest.shape))
        timeuni = np.dot(unitest, wt)
        timerd = np.dot(rdtest, wt)
        corrs[i, 0] = np.corrcoef(timeincome, df.foodsize)[0, 1]
        corrs[i, 1] = np.corrcoef(timeuni, df.foodsize)[0, 1]
        i += 1
    p = figure(x_axis_label='t0 (s)', y_axis_label='Pearson correlation coefficient',\
                x_axis_type='log')
    p.scatter(t0, corrs[:,0], fill_color='Blue', line_color='Blue', \
                    legend='accessible income vs. restaurant count')
    p.line(t0, corrs[:,0], color='Blue')
    p.scatter(t0, corrs[:,1], fill_color='Red', line_color='Red', \
                    legend='accessibility vs. restaurant count')
    p.line(t0, corrs[:,1], color='Red')
    cc = np.corrcoef(df.sumincome, df.foodsize)[0,1]
    p.line(t0, cc*np.ones(shape=corrs[:,1].shape), color='Black', \
                    legend='local income vs. restaurant count')
    script, div = components(p)
    return script, div

@foodincomeapp.route('/seattle', methods = ['GET'])
def seattle_app():
    traveltime = np.loadtxt('data/ttime_sea.txt')
    foodincome = pd.read_csv('data/df_sea.csv')
    with open('data/seazip_cord.json', 'r') as f:
        try:
            cords = json.load(f)
        except ValueError:
            cords = {}

    script, div = assembledisplay(traveltime, foodincome, 500, cords, 'Seattle')

    return render_template('graph_seattle.html', script=script, div=div)

@foodincomeapp.route('/nyc', methods = ['GET'])
def nyc_app():
    traveltime = np.loadtxt('data/ttime_nyc.txt')
    foodincome = pd.read_csv('data/df_nyc.csv')
    with open('data/nyczip_cord.json', 'r') as f:
        try:
            cords = json.load(f)
        except ValueError:
            cords = {}

    script, div = assembledisplay(traveltime, foodincome, 500, cords, 'NYC')

    p = getdotplot(foodincome.sumincome, foodincome.foodsize, foodincome['zip code'], \
                    'income (USD)', 'restaurant count', 'zip code',
                    'log', 'log')
    script2, div2 = components(p)

    return render_template('graph_nyc.html', script=script, div=div, \
                            script2=script2, div2=div2)

@foodincomeapp.route('/houston', methods = ['GET'])
def houston_app():
    traveltime = np.loadtxt('data/ttime_hou.txt')
    foodincome = pd.read_csv('data/df_hou.csv')
    with open('data/houzip_cord.json', 'r') as f:
        try:
            cords = json.load(f)
        except ValueError:
            cords = {}

    script, div = assembledisplay(traveltime, foodincome, 420, cords, 'Houston')

    p1 = getmapplot(cords, np.exp(-traveltime/420)[:,0], 'weights', 'weights')
    timeuni = np.dot(np.ones(shape=(1, traveltime.shape[0])), \
                    np.exp(-traveltime/420))
    p2 = getmapplot(cords, timeuni, 'Accessibility: sum of weights', 'accessibility')
    tab1 = Panel(child=p1, title='Weights for city center')
    tab2 = Panel(child=p2, title='Accessibility map')
    tabs = Tabs(tabs=[tab1, tab2])
    script2, div2 = components(tabs)

    script3, div3 = getcorr_t0(np.arange(60, 6060, 60), foodincome, traveltime)

    return render_template('graph_houston.html', script=script, div=div, \
                            script2=script2, div2=div2, \
                            script3=script3, div3=div3)


if __name__ == "__main__":
    foodincomeapp.run(host='0.0.0.0', port=5000)
