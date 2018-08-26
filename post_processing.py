#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 26 16:16:58 2018

@author: rugantio
"""
import pandas as pd
df = pd.read_csv('./exploit.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by='date',ascending=False)
df.to_csv('./exploit_sorted.csv',index=False, float_format = '%.12g')
  

