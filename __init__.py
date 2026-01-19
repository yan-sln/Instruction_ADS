# -*- coding: utf-8 -*-
# Python 3

def classFactory(iface):
    from .Instruction_ADS import MainPlugin
    return MainPlugin(iface)


