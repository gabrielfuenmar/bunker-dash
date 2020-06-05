"""
Created on Tue May 26 21:58:04 2020

Author: Gabriel Fuentes Lezcano
"""
import pandas as pd
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime as dt
import numpy as np
from random import shuffle
import dash_auth
import os

USERNAME=os.environ.get("USERNAME_DEFAULT", None)
PWD=os.environ.get("PASSWORD_DEFAULT", None)

VALID_USERNAME_PASSWORD_PAIRS={USERNAME:PWD}
MAPBOX_TOKEN=os.environ.get('MAPBOX_TOKEN', None)

####
valid_colors=["#CF5C60","#717ECD","#4AB471","#F3AE4E","#D96383","#4EB1CB"]
shuffle(valid_colors)
valid_dash=['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot']

##Databases
####
df = pd.read_csv('data/bunkering_ops_mediterranean.csv', parse_dates=True)
df["start_of_service"]=pd.to_datetime(df["start_of_service"])
df["vessel_inside_port"]=pd.to_datetime(df["vessel_inside_port"])
##Sentence case
df["bunkering_port"]=df.bunkering_port.str.title()
# ##Remove the ports with less than 30 observations
test=df.bunkering_port.value_counts().reset_index()
df=df[df.bunkering_port.isin(test["index"][test.bunkering_port>30])].reset_index(drop=True)


brent_df=pd.read_csv("data/brent-daily.csv")
brent_df["Date"]=pd.to_datetime(brent_df["Date"])

ports_positions=pd.read_csv('data/ports_positions.csv')

##Waiting time generation and barge age
df=df.assign(waiting_time=df.start_of_service-df.vessel_inside_port,
              barge_age_at_op=df.start_of_service[0].year-df.BargeBuilt)

df["waiting_time"]=df.waiting_time/np.timedelta64(1,"h")

barges=df.sort_values(by=["start_of_service"]).drop_duplicates(subset=["barge_imo"],keep="last").copy()

##Service time and Waiting time function
def stats_graph(graph="service",fr="01-01-2014",to="01-06-2019",port=["full"],type_vessel=["full"],*args):  
    '''Generates a plotly graph to be used in dash
    Input: 
        fr; From date (datetime dd-mm-YYYY). Default 01-01-2014
        to; To date (datetime dd-mm-YYYY)
        graph; type of graph, from service or waiting
        port; ports filter. Full has all the ports higher than 100 observations
        Returns. Plotly Graph'''
    date_from=pd.to_datetime(fr)
    date_to=pd.to_datetime(to)
    
    df_in=df[df.start_of_service.between(date_from,date_to)].copy()
    if "full" not in type_vessel:
        df_in=df_in[df_in.ConType.isin(type_vessel)]
        
    if "full" in port:
        summary=df_in.bunkering_port.value_counts().reset_index().rename(columns={"index":"bunkering_port","bunkering_port":"count"})
    else:
        summary=df_in.bunkering_port[df_in.code.isin(port)].value_counts().reset_index().rename(columns={"index":"bunkering_port","bunkering_port":"count"})
      
    not_valid=summary[summary["count"]<30]
    summary=summary[summary["count"]>=30]    
    
    if summary.shape[0]==0:
        if graph=="service":
            modal_ex=html.Div([# modal div
                          html.Div([html.H4("Not enough sample to build distributions. Adjust your selection.",
                                            style={'textAlign': 'center',"font-size":"21px","position":"absolute","top":"20%" })],className='modal-content'),
                          html.Button('Close', id='modal-close-button',className="button-modal")
                          ],id='modal',className='modal')
            return [modal_ex]
    else:
        hist_times=[]
        times_labels=[]
        for n in summary["bunkering_port"].unique().tolist():
            df_iter=df_in[df_in.bunkering_port=="{}".format(n)].copy()
            if graph=="service":
                #Outliers remove
                df_iter=df_iter[df_iter.service_time<=df_iter.service_time.quantile(0.95)]
                hist_times.append(df_iter.service_time.tolist())
            elif graph=="waiting":
                ##Outlier remove
                df_iter=df_iter[df_iter.waiting_time<=df_iter.waiting_time.quantile(0.95)]
                ##After 12 hours for waiting time replaced by 12 hours
                df_iter["waiting_time"]=np.where(df_iter.waiting_time>13,13,df_iter.waiting_time)
                hist_times.append(df_iter.waiting_time.tolist())          
            times_labels.append(n)
            
        fig_service= ff.create_distplot(hist_times, times_labels, colors=valid_colors[0:summary.shape[0]],histnorm='probability density',show_rug=False, show_hist=False)
        
        ##Dict of annotations change for value of >9
        annotations_variable={"service":dict(x=0.93,y=-0.19,showarrow=False,text="Hours",xref="paper",yref="paper"),
                                  "waiting":dict(x=1.0,y=-0.19,showarrow=False,text=">13",xref="paper",yref="paper")}
                
        if graph=="service":
            annotations_variable=[annotations_variable.get("service")]
        elif graph=="waiting":
            annotations_variable=[annotations_variable.get("service"),annotations_variable.get("waiting")]
        ##Graphs layout + axis title as annotation
        fig_service.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)",
                                    "paper_bgcolor": "rgba(0, 0, 0, 0)"},
                                      showlegend=False,
                                      margin=dict(l=0,r=0,b=0,t=0),
                                      font=dict(family="Open Sans Light",size=12,color="#d8d8d8"),
                                      annotations=annotations_variable)         
        ##Axes colors                          
        fig_service.update_xaxes(showline=True, zerolinewidth=1, zerolinecolor='white',gridcolor="rgba(255,255,255,0.05)")
        fig_service.update_yaxes(automargin=True,rangemode="tozero",showline=True, zerolinewidth=1, zerolinecolor='white',gridcolor="rgba(255,255,255,0.05)")     
         
        ##Line colors and plot 
        ##Layout for 1 record
        if summary.shape[0]==1:
            fig_service.update_layout({'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}})
                                       
            if graph=="service":   
                fig_service.update_traces(hovertemplate='Hours: %{x:.1f}<extra></extra>',marker=dict(color="#F3AE4E"),fill="tozeroy",line=dict(width=3))               
            elif graph=="waiting":
                fig_service.update_traces(hovertemplate='Hours: %{x:.1f}<extra></extra>',marker=dict(color="#4ABA71"),fill="tozeroy",line=dict(width=3))
        
        ##Layout for more than 1 record
        elif summary.shape[0]>1 and summary.shape[0]<=5:      
            fig_service.update_layout({'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}},
                                      showlegend=True)
            ##Hovertext and hovertemplate
            fig_service.update_traces(hovertemplate='Hours: %{x}<extra></extra>')
            if graph=="service":                  
                fig_service.update_traces(fill="tozeroy",line=dict(width=1))               
            elif graph=="waiting":
                fig_service.update_traces(fill="tozeroy",line=dict(width=1))
        
        ##Separate returns as to provide differents id's, Header and modal if needed.
        if graph=="service":                                           
            fig_service_ex=dcc.Graph(id='service',
                                      config={'displayModeBar': False},
                                      animate=False,
                                      figure=fig_service,
                                      style={"height": "22vh","width" : "100%","display": "block",'align-items': 'stretch'})
            ##If a port was removed from selectin then inform user
            if not_valid.shape[0]!=0:
                ##Ordered list of div for modal.
                ports_list_div=[html.H4("{};".format(i)) for i in not_valid.bunkering_port]
                header_mod=[html.H3('The following port(s) are not included to the graph (small sample):')]
                not_valid_list=header_mod+ports_list_div
                modal_ex=html.Div([# modal div
                               html.Div(not_valid_list,className='modal-content'),
                               html.Button('Close', id='modal-close-button',className="button-modal")
                                ],id='modal',style={'textAlign': 'center', },className='modal')
                return [html.H2("Service time"),fig_service_ex, modal_ex]
            else:
                modal_ex=html.Div([html.Button('Close', id='modal-close-button',className="button-modal")
                                ],id='modal',className='modal-fake')
    
                return [html.H2("Service time"),fig_service_ex,modal_ex]
               
        elif graph=="waiting":
            fig_service_ex=dcc.Graph(id='waiting',
                                      config={'displayModeBar': False},
                                      animate=False,
                                      figure=fig_service,
                                      style={"height": "22vh","width" :"100%","display": "block",'align-items': 'stretch'})
                   
            return [html.H2("Waiting time"),fig_service_ex]
        
def ranking(fr="01-01-2014",to="01-06-2019",port=["full"],type_vessel=["full"],*args): 
    '''Generates a ranking of ports to be used in dash
    Input: 
        fr; From date (datetime dd-mm-YYYY). Default 01-01-2014
        to; To date (datetime dd-mm-YYYY)
        port; ports filter. Full has all the ports higher than 100 observations
        type_vessel. Full as it includes all the vessel
        Returns. Plotly Graph'''
        
        ##Datetime
    date_from=pd.to_datetime(fr)
    date_to=pd.to_datetime(to)
        
    df_in=df[df.start_of_service.between(date_from,date_to)].copy()
    
    #Filters
    if "full" not in port:
        df_in=df_in[df_in.code.isin(port)]
    if "full" not in type_vessel:
        df_in=df_in[df_in.ConType.isin(type_vessel)]
    
    port_count=df_in.bunkering_port.value_counts().reset_index().rename(columns={"index":'bunkering_port',"bunkering_port":"ops"})
    ##Percentage
    port_count=port_count.assign(percentage=(port_count.ops/df_in.shape[0])*100).reset_index().rename(columns={"index":'number'})
    port_count["number"]=port_count["number"]+1
    
    ##Get top 5
    port_count=port_count[port_count.number<=5]
    
    ##Graph construction and hovertext
    fig_ranking = go.Figure(go.Bar(
            x=port_count.percentage,
            y=port_count.number,
            text=port_count.bunkering_port.str.title(),
            hovertext=port_count.ops,
            hovertemplate='Operations: %{hovertext}. Perc: %{x:.2f}<extra></extra>',
            orientation='h'))
    
    ##Graphs layout
    fig_ranking.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)",
                                "paper_bgcolor": "rgba(0, 0, 0, 0)",
                                'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}},
                              showlegend=False,
                              margin=dict(l=0,r=0,b=0,t=0),
                              font=dict(family="Open Sans Light",size=12,color="#d8d8d8"),
                              annotations=[dict(x=0.93,y=-0.1,showarrow=False,text="%",xref="paper",yref="paper")])
    
    #X axis
    fig_ranking.update_xaxes(showline=True,gridcolor="rgba(255,255,255,0.05)")
    ##Y axis
    fig_ranking.update_xaxes(showline=False)
    ##Plots + text
    fig_ranking.update_traces(marker_color="#717ecd", marker_line_color='black',
                  marker_line_width=0.5,textposition='auto',
                  textfont_family="Open Sans Light",textfont_color="#d8d8d8")
    ##Axes colors                          
    fig_ranking.update_yaxes(autorange="reversed")    
    ##DCC Graph
    fig_ranking_ex=dcc.Graph(id='ranking',
                              config={'displayModeBar': False},
                              animate=False,
                              figure=fig_ranking,
                              style={"height": "37vh","width" : "100%","display": "block",'align-items': 'stretch'})
    
    return [html.H2("Top 5 ports"),fig_ranking_ex]
      
def barges(fr="01-01-2014",to="01-06-2019",port=["full"],type_vessel=["full"],*args):  
    '''Works the age at ops density of barges
    Input: 
        fr; From date (datetime dd-mm-YYYY). Default 01-01-2014
        to; To date (datetime dd-mm-YYYY)
        port; ports filter. Full has all the ports higher than 100 observations
        type_vessel. Full as it includes all the vessel
        Returns. Plotly Graph'''
        
    ##Datetime
    date_from=pd.to_datetime(fr)
    date_to=pd.to_datetime(to)
        
    df_in=df[df.start_of_service.between(date_from,date_to)].copy()
    ##False values
    df_in=df_in[df_in.barge_age_at_op>0]
    #Filters
    if "full" not in port:
        df_in=df_in[df_in.code.isin(port)]
    if "full" not in type_vessel:
        df_in=df_in[df_in.ConType.isin(type_vessel)]
        
    ##Graph construction, hovertext and bin setting
    fig_barges = go.Figure(data=[go.Histogram(x=df_in.barge_age_at_op,xbins=dict(size=2),
                                              marker_color="#CF5C60",marker_line_width=1,
                                              hovertemplate='Age: %{x}. Observations: %{y}<extra></extra>')])
    
    ##Graphs layout
    fig_barges.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)",
                                "paper_bgcolor": "rgba(0, 0, 0, 0)",
                                'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}},
                              showlegend=False,
                              margin=dict(l=0,r=0,b=0,t=0),
                              font=dict(family="Open Sans Light",size=12,color="#d8d8d8"),
                              annotations=[dict(x=0.93,y=-0.09,showarrow=False,text="Years",xref="paper",yref="paper")])
    #Y axis
    fig_barges.update_yaxes(showline=True,gridcolor="rgba(255,255,255,0.05)")
    ##DCC Graph
    fig_barges_ex=dcc.Graph(id='barges_age',
                              config={'displayModeBar': False},
                              animate=False,
                              figure=fig_barges,
                              style={"height": "37vh","width" : "100%","display": "block",'align-items': 'stretch'})
    
    return [html.H2("Barge age at operation"),fig_barges_ex]

def brent(fr="01-01-2014",to="01-06-2019"):
    '''Brent graph
    Input: 
        fr; From date (datetime dd-mm-YYYY). Default 01-01-2014
        to; To date (datetime dd-mm-YYYY)
        Returns. Plotly Graph'''
        
    ##Datetime
    date_from=pd.to_datetime(fr)
    date_to=pd.to_datetime(to)
        
    df_in=brent_df[brent_df.Date.between(date_from,date_to)].copy()  
    #Graph construction
    figure_brent=go.Figure([go.Scatter(x=df_in['Date'], y=df_in['Price'],
                                        marker_color="#2A94D6")])
      ##Graphs layout
    figure_brent.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)",
                                "paper_bgcolor": "rgba(0, 0, 0, 0)",
                                'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}},
                              showlegend=False,
                              margin=dict(l=0,r=0,b=0,t=0),
                              font=dict(family="Open Sans Light",size=12,color="#d8d8d8"))
    
    
    #Y axis
    figure_brent.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
    #X axis
    figure_brent.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    
    ##DCC Graph
    fig_brent_ex=dcc.Graph(id='brent',
                              config={'displayModeBar': False},
                              animate=False,
                              figure=figure_brent,
                              style={"height": "22vh","width" : "100%","display": "block",'align-items': 'stretch'})
    
    return [html.H2("Brent price"),fig_brent_ex]

def bunker_map(port=["full"],*args):
    ports_positions_in=ports_positions[ports_positions.PortCode.isin(df.code.unique())][["BE PORT_NA","PortCode","Lat","Long"]].reset_index(drop=True).copy()
    ports_positions_in=ports_positions_in.assign(colors='#CF5C60')
    if "full" not in port:
        ports_positions_in["colors"]=np.where(ports_positions_in.PortCode.isin(port),"#F3AE43",
                                              ports_positions_in["colors"])  

    ##Maps construction
    map_data=go.Figure(go.Scattermapbox(lat=ports_positions_in.Lat, lon=ports_positions_in.Long,
                        mode="markers",hovertext=ports_positions_in["BE PORT_NA"],selectedpoints=[],
                        selected={'marker':{'color': '#CF5C60'}},
                        text=ports_positions_in.PortCode,hovertemplate='%{hovertext}<extra></extra>',
                        marker=go.scattermapbox.Marker(size=12,color=ports_positions_in.colors,opacity=None))) 
       
    center_map=dict(lat=37.00,lon=18.00)
    zoom_map=3
    
    ##Map prueba
    map_data.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)",
                                "paper_bgcolor": "rgba(0, 0, 0, 0)",
                                'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}},
                            margin=dict(l=0,r=0,b=0,t=0),
                            autosize=True,hovermode='closest',
                            mapbox_style="white-bg",clickmode="event+select",
                            mapbox=dict(bearing=0,
                                        center=center_map,zoom=zoom_map))
    # #Map layout
    # map_data.update_layout({"plot_bgcolor": "rgba(0, 0, 0, 0)",
    #                             "paper_bgcolor": "rgba(0, 0, 0, 0)",
    #                             'hoverlabel':{'bgcolor':'rgb(223, 232, 243)'}},
    #                         margin=dict(l=0,r=0,b=0,t=0),
    #                         autosize=True,hovermode='closest',clickmode="event+select",
    #                         mapbox_style='mapbox://styles/gabrielfuenmar/ckaocvlug34up1iqvowltgs5p',
    #                         mapbox=dict(bearing=0,accesstoken=MAPBOX_TOKEN,
    #                                     center=center_map,zoom=zoom_map))


    #DCC Graph
    map_data_ex=dcc.Graph(id='map',                            
                              animate=True,
                              figure=map_data,
                              style={"height": "55vh","width" : "100%","display": "block",'align-items': 'stretch'})
    
    return [map_data_ex]
    

##Dropdown and filters
def header_dropdown():
        port_dropdown=dcc.Dropdown(id='ports-dropdown',
        options=[{'label': row["bunkering_port"].title(),'value': row["code"]} \
        for index,row in df.drop_duplicates(subset=["bunkering_port"]).iterrows()],
        placeholder="Port/s (max 5)",multi=True)
        
    
        type_dropdown=dcc.Dropdown(id='types-dropdown',
        options=[{'label': row.title(),'value': row} \
        for row in df.dropna(subset=["ConType"]).ConType.unique()],
        placeholder="Vessel type(s)",multi=True)
    
        date_start=dcc.DatePickerSingle(
        id='date-picker-start',
        min_date_allowed=dt(2014, 1, 1),
        max_date_allowed=dt(2019, 6, 1),
        initial_visible_month=dt(2014, 1, 1),
        display_format='DD-MM-YYYY',
        placeholder="01-01-2014")

        date_end=dcc.DatePickerSingle(
        id='date-picker-end',
        min_date_allowed=dt(2014, 1, 1),
        max_date_allowed=dt(2019, 6, 1),
        initial_visible_month=dt(2019, 6, 1),
        display_format='DD-MM-YYYY',
        placeholder="01-06-2019")
        
        return [html.H1("BUNKER ANALYTICS"),html.Div([date_start,date_end,
                                                      port_dropdown,type_dropdown],className="box"),               
                                              html.Button("Refresh",id="update-button",
                                                             className="box")]


# Initialise the app
app = dash.Dash(__name__,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
app.title="Bunker Analytics"

server = app.server

#Authentication
auth = dash_auth.BasicAuth(app,VALID_USERNAME_PASSWORD_PAIRS)

# Define the app
app.layout = html.Div("Bunker Dash")


app.layout = html.Div(children=[dcc.ConfirmDialog(id='date-error',message='Wrong date range'),
                      html.Div(id="main-header",className="container-row twelve columns",
                                children=[
                                  html.Div(id="header",className="div-header bg-navy",##Header
                                      children=header_dropdown())
                                                        ]),
                      html.Div(id="main-rank",className='container three columns',
                                children=[
                                  html.Div(id="ranking-container",children=ranking()
                                           ,className='div-ranking bg-navy'),
                                  html.Div(id="age-container",children=barges(),className='div-ops bg-navy')
                                  ]),
                      html.Div(id="main-map",className="container five columns",
                                children=[
                                    html.Div(id="map-container",children=bunker_map(),##Map
                                             className='div-for-maps bg-navy'),
                                    html.Div(id="price-container",className="div-for-prices bg-navy")
                                  ],style={"margin-left":"0px","margin-right":"0px"}),
                      html.Div(id="main-stats-price",className="container four columns",
                                children=[
                                    html.Div(id="service-container",children=stats_graph(),className="div-for-service bg-navy"),
                                    html.Div(id="waiting-container",children=stats_graph(graph="waiting"),##Waiting time
                                             className="div-for-waiting bg-navy"),
                                    html.Div(id="brent-container",children=brent(),#Brent Price
                                             className="div-for-brent bg-navy")])
                                   ],className="main-box")


###############Callbacks
##Modal for missing ports
@app.callback(Output('modal', 'style'),
            [Input('modal-close-button', 'n_clicks')])
def close_modal(n):
    if (n is not None) and (n > 0):
        return {"display": "none"}
        
##Callback for error in date     
@app.callback(Output(component_id='date-error', component_property='displayed'),
              [Input('date-picker-start', 'date'),Input('date-picker-end', 'date')])

def date_check(value_start,value_end):
    if value_start is not None and value_end is not None:
        if pd.to_datetime(value_start)>pd.to_datetime(value_end):
            return True
    return False

##Refresh button
@app.callback(Output('map-container', 'children'),
              [Input('update-button', 'n_clicks')])    

def clearMap(n_clicks):
    if n_clicks !=0:
        return bunker_map()
    
@app.callback(Output('header', 'children'),
              [Input('update-button', 'n_clicks')])
    
def clearDropDown1(n_clicks):
    if n_clicks !=0: #Don't clear options when loading page for the first time
        return header_dropdown() #Return an empty list of options

##Service callback
@app.callback(Output("service-container","children"),
              [Input('update-button',"n_clicks"),
              Input('ports-dropdown', 'value'),
                     Input("types-dropdown", "value"),
                     Input('date-picker-start', 'date'),
                     Input('date-picker-end', 'date')])

def service_update(click,ports_val,types_val,date_s,date_e):
    ##If no value is entered then keep default
    if not ports_val:
        ports_val=["full"]
    if not types_val:
        types_val=["full"]
    if not date_s:
        date_s="01-01-2014"
    if not date_e:
        date_e="01-06-2019"
    ##Click trigger
    if click is not None and len(ports_val)<=5:
        return stats_graph()
    elif len(ports_val)<=5:
        return stats_graph(port=ports_val,type_vessel=types_val,fr=date_s,to=date_e)
    else:
        return stats_graph()
    
##Waiting callback
@app.callback(Output("waiting-container","children"),
              [Input('update-button',"n_clicks"),
              Input('ports-dropdown', 'value'),
                      Input("types-dropdown", "value"),
                      Input('date-picker-start', 'date'),
                      Input('date-picker-end', 'date')])   

def waiting_update(click,ports_val,types_val,date_s,date_e):
    ##If no value is entered then keep default
    if not ports_val:
        ports_val=["full"]
    if not types_val:
        types_val=["full"]
    if not date_s:
        date_s="01-01-2014"
    if not date_e:
        date_e="01-06-2019"
    ##Click trigger
    if click is not None:
        return stats_graph(graph="waiting")
    elif len(ports_val)<=5:
        return stats_graph(graph="waiting",port=ports_val,type_vessel=types_val,fr=date_s,to=date_e)
    else:
        return stats_graph(graph="waiting")

##Brent update
@app.callback(Output("brent-container","children"),
              [Input('update-button',"n_clicks"),
              Input('date-picker-start', 'date'),
                      Input('date-picker-end', 'date')])   

def brent_update(click,date_s,date_e):
    if not date_s:
        date_s="01-01-2014"
    if not date_e:
        date_e="01-06-2019"
    if click is not None:
        return brent()       
    else:
        return brent(fr=date_s,to=date_e)

##Ages update
@app.callback(Output("age-container","children"),
              [Input('update-button',"n_clicks"),
               Input('ports-dropdown', 'value'),
                      Input("types-dropdown", "value"),
                      Input('date-picker-start', 'date'),
                      Input('date-picker-end', 'date')])   

def age_update(click,ports_val,types_val,date_s,date_e):
    if not ports_val:
        ports_val=["full"]
    if not types_val:
        types_val=["full"]
    if not date_s:
        date_s="01-01-2014"
    if not date_e:
        date_e="01-06-2019"  
    if click is not None:
        return barges()
    else:
        return barges(fr=date_s,to=date_e,port=ports_val,type_vessel=types_val)

##Ranking update
@app.callback(Output("ranking-container","children"),
              [Input('update-button',"n_clicks"),
               Input('ports-dropdown', 'value'),
                      Input("types-dropdown", "value"),
                      Input('date-picker-start', 'date'),
                      Input('date-picker-end', 'date')])   

def ranking_update(click,ports_val,types_val,date_s,date_e):
    if not ports_val:
        ports_val=["full"]
    if not types_val:
        types_val=["full"]
    if not date_s:
        date_s="01-01-2014"
    if not date_e:
        date_e="01-06-2019"  
    if click is not None:
        return ranking()
    else:
        return ranking(fr=date_s,to=date_e,port=ports_val,type_vessel=types_val)      
 
##Map selection

@app.callback(Output("ports-dropdown","value"),
              [Input("map","selectedData")])

def display_selected_data(geo_select):
    if geo_select is not None:
        port=[]
        for point in geo_select["points"]:
            port.append(point["text"])
        return port
        

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
