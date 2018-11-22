# -*- coding: utf-8 -*-
#%%

import numpy as np
import math
import sys
import os
import codecs
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--f', '-f', default='dif_lut.v', type=str,
                    help='file name')

args = parser.parse_args()
fn = args.f
f = open(fn, "w")

I_len = np.array([1, 6, 5]) # [符号,  整数部,    小数部]
O_len = np.array([1, 2, 13]) # [符号,  整数部,    小数部]
act_f = 'sigmoid'
name = 'dif_lut' #出力モジュール名
#name = 'dif_lut'
dif_en = 1 # 普通の活性化関数なら0,微分関数なら1


def act_func(x, act): #活性化関数
    if act == 'relu':
        return np.array( 0.5 * (np.absolute(x)+x))
    elif act == 'sigmoid':
        #return bit(np.array( 0.5 * ( 1 + np.tanh(x)) , dtype=np.float64))
        return  1. / ( 1. + np.exp(-x))
    elif act == 'no':
        return x
    elif act == 'tanh':
        return np.tanh(x)
    elif act == 'softmax':
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()
        # これは誤り

def dif(x, act): #活性化関数の微分
    if act == 'relu':
        return bit_16(np.sign(x))
    elif act == 'sigmoid':
        return act_func(x,'sigmoid') * ( 1 - act_func(x,'sigmoid') )
    # 2倍しないとうまくいかない。
    elif act == 'no':
        return 1
    elif act == 'tanh':
        return bit( 1.0 / (np.cosh(x)**2))
    elif act == 'softmax':
        return act_func(x,'sigmoid') * ( 1 - act_func(x,'sigmoid') )

def float2binary(in_x, O_len):
    in_reg = in_x
    total_bit = np.sum(O_len)
    bin_str = str(total_bit) + u"'b"

    # 正のとき
    if in_x >= 0:
        bin_str = bin_str + u"0"
        # 整数領域
        for i in range(0, O_len[1]):
            if (in_reg >= 2**(O_len[1]-i-1)):
                bin_str = bin_str + u"1"
                in_reg = in_reg - 2**(O_len[1]-i-1)
            else:
                bin_str = bin_str + u"0"
        # 小数領域
        for i in range(0, O_len[2]):
            if (in_reg >= math.pow(2, (-1)*(i+1))):
                bin_str = bin_str + u"1"
                in_reg = in_reg - math.pow(2, (-1)*(i+1))
            else:
                bin_str = bin_str + u"0"
    # 負のとき
    else:
        bin_str = bin_str + u"1"
        in_reg = (-1) * in_reg - math.pow(2, (-1)*O_len[2])
        for i in range(0, O_len[1]):
            if (in_reg >= 2**(O_len[1]-i-1)):
                bin_str = bin_str + u"0"
                in_reg = in_reg - 2**(O_len[1]-i-1)
            else:
                bin_str = bin_str + u"1"
        # 小数領域
        for i in range(0, O_len[2]):
            if (in_reg >= math.pow(2, (-1)*(i+1))):
                bin_str = bin_str + u"0"
                in_reg = in_reg - math.pow(2, (-1)*(i+1))
            else:
                bin_str = bin_str + u"1"

    return bin_str

# 書式
f.write('// function = {}\n\n module {}(\n  input [{}:0] in,\n  output [{}:0] y\n );\n\n  function [{}:0] FUNC_OUT;\n     input [{}:0] in;\n      begin\n         case(in)\n'.format(act_f, name, np.sum(I_len)-1, np.sum(O_len)-1 ,np.sum(O_len)-1, np.sum(I_len)-1))


#正領域
counter = 0
for i_integer in range(0, (2**I_len[1])):
    for i_fractal in range(0, (2**I_len[2])):
        value_i = i_integer + i_fractal * math.pow(2,(-1)*I_len[2])
        if dif_en == 0:
            value_o = act_func(value_i, act_f)
        if dif_en == 1:
            value_o = dif(value_i, act_f)
        counter = counter + 1
        i_str = float2binary(value_i,I_len)
        o_str = float2binary(value_o,O_len)
        f.write('             {} : FUNC_OUT = {};\n'.format(i_str,o_str))





#負領域
for i_integer in range(0, (2**I_len[1])):
    for i_fractal in range(0, (2**I_len[2])):
        value_i = (-1) * i_integer + (-1) * i_fractal * math.pow(2,(-1)*I_len[2])
        if dif_en == 0:
            value_o = act_func(value_i, act_f)
        if dif_en == 1:
            value_o = dif(value_i, act_f)

        if value_i != 0:
            i_str = float2binary(value_i,I_len)
            o_str = float2binary(value_o,O_len)
            f.write('             {} : FUNC_OUT = {};\n'.format(i_str,o_str))
            counter = counter + 1

#負領域その2
value_i = float((-1) * ((2**I_len[1])))
if dif_en == 0:
    value_o = act_func(value_i, act_f)
if dif_en == 1:
    value_o = dif(value_i, act_f)
i_str = float2binary(value_i,I_len)
o_str = float2binary(value_o,O_len)
f.write('             {} : FUNC_OUT = {};\n'.format(i_str,o_str))

# default
default_str = float2binary(0,O_len)
f.write('             default : FUNC_OUT = {};\n'.format(default_str))


f.write('           endcase\n       end\n   endfunction\n\n assign y = FUNC_OUT(in);\nendmodule')
