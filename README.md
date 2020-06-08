# Bunker Analytics dashboard
[Dashboard](http://bunker.gabrielfuentes.org) with Mediterranean bukering statistics generated from AIS data.

Online app that generates an interactive dashboard for bunkering information for the Mediterranean Sea from 01-01-2014 to 01-06-2019. 

The database was generated from a [bunkering recognition algorithm](https://github.com/gabrielfuenmar/bunkering-recognition) that uses raw AIS information.

Dependencies:

      pandas 1.0.3
      dash 1.12.0
      numpy 1.18.4
      dash_auth 1.3.2
      gunicorn 19.9.0
      requests 2.23.0
      scipy 1.4.1

Parameters: 

      bunkering_ops_mediterranean: dataframe with bunkering ops information
      brent_prices: dataframe with historical brent spot prices from EIA.
      ports_positions: dataframe of port codes and positions.
      style.css. Default Css settings for dashboard design.

Returns: 

      Dashboard deployed in bunker.gabrielfuentes.org via Heroku
        
Code development:
  
        1.Def functions built for every container and linked via a bigger div.html
        2.Particulars of every container retrieved from style.css
        3.Callbacks assigned to every relevant container from every input and map
  
Credits: Gabriel Fuentes Lezcano

Licence: MIT License

Copyright (c) 2020 Gabriel Fuentes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
© 2019 GitHub, Inc.
