#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from builtins import int, range

__author__ = "Anand Kalaiarasi Ganeson, ganan642@student.liu.se, 2012-03-19, and Martin Sjölund"
__license__ = """
 This file is part of OpenModelica.

 Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
 c/o Linköpings universitet, Department of Computer and Information Science,
 SE-58183 Linköping, Sweden.

 All rights reserved.

 THIS PROGRAM IS PROVIDED UNDER THE TERMS OF THE BSD NEW LICENSE OR THE
 GPL VERSION 3 LICENSE OR THE OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
 ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
 RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
 ACCORDING TO RECIPIENTS CHOICE.

 The OpenModelica software and the OSMC (Open Source Modelica Consortium)
 Public License (OSMC-PL) are obtained from OSMC, either from the above
 address, from the URLs: http://www.openmodelica.org or
 http://www.ida.liu.se/projects/OpenModelica, and in the OpenModelica
 distribution. GNU version 3 is obtained from:
 http://www.gnu.org/copyleft/gpl.html. The New BSD License is obtained from:
 http://www.opensource.org/licenses/BSD-3-Clause.

 This program is distributed WITHOUT ANY WARRANTY; without even the implied
 warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE, EXCEPT AS
 EXPRESSLY SET FORTH IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE
 CONDITIONS OF OSMC-PL.
"""
__status__ = "Prototype"
__maintainer__ = "https://openmodelica.org"

from pyparsing import (
    Combine,
    Dict,
    Forward,
    Group,
    Keyword,
    Optional,
    QuotedString,
    StringEnd,
    Suppress,
    Word,
    alphanums,
    alphas,
    delimitedList,
    nums,
    replaceWith,
)

import sys

def convertNumbers(s, l, toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError:
        return float(n)


def convertString2(s, s2):
    tmp = s2[0].replace("\\\"", "\"")
    tmp = tmp.replace("\"", "\\\"")
    tmp = tmp.replace("\'", "\\'")
    tmp = tmp.replace("\f", "\\f")
    tmp = tmp.replace("\n", "\\n")
    tmp = tmp.replace("\r", "\\r")
    tmp = tmp.replace("\t", "\\t")
    return "'"+tmp+"'";

def convertString(s, s2):
    return s2[0].replace("\\\"", '"')


def convertDict(d):
    return dict(d[0])


def convertTuple(t):
    return tuple(t[0])


omcRecord = Forward()
omcValue = Forward()

TRUE = Keyword("true").setParseAction(replaceWith(True))
FALSE = Keyword("false").setParseAction(replaceWith(False))
NONE = (Keyword("NONE") + Suppress("(") + Suppress(")")).setParseAction(replaceWith(None))
SOME = (Suppress(Keyword("SOME")) + Suppress("(") + omcValue + Suppress(")"))

omcString = QuotedString(quoteChar='"', escChar='\\', multiline=True).setParseAction(convertString)
omcNumber = Combine(Optional('-') + ('0' | Word('123456789', nums)) +
                    Optional('.' + Word(nums)) +
                    Optional(Word('eE', exact=1) + Word(nums + '+-', nums)))

#ident = Word(alphas + "_", alphanums + "_") | Combine("'" + Word(alphanums + "!#$%&()*+,-./:;<>=?@[]^{}|~ ") + "'")
ident = Word(alphas + "_", alphanums + "_") | QuotedString(quoteChar='\'', escChar='\\').setParseAction(convertString2)
fqident = Forward()
fqident << ((ident + "." + fqident) | ident)
omcValues = delimitedList(omcValue)
omcTuple = Group(Suppress('(') + Optional(omcValues) + Suppress(')')).setParseAction(convertTuple)
omcArray = Group(Suppress('{') + Optional(omcValues) + Suppress('}')).setParseAction(convertTuple)
omcValue << (omcString | omcNumber | omcRecord | omcArray | omcTuple | SOME | TRUE | FALSE | NONE | Combine(fqident))
recordMember = delimitedList(Group(ident + Suppress('=') + omcValue))
omcRecord << Group(Suppress('record') + Suppress(fqident) + Dict(recordMember) + Suppress('end') + Suppress(fqident) + Suppress(';')).setParseAction(convertDict)

omcGrammar = Optional(omcValue) + StringEnd()

omcNumber.setParseAction(convertNumbers)


def parseString(string):
    res = omcGrammar.parseString(string)
    if len(res) == 0:
      return
    return res[0]


if __name__ == "__main__":
    testdata = """
   (1.0,{{1,true,3},{"4\\"
",5.9,6,NONE ( )},record ABC
  startTime = ErrorLevel.warning,
  'stop*Time' = SOME(1.0)
end ABC;})
    """
    expected = (1.0, ((1, True, 3), ('4"\n', 5.9, 6, None), {"'stop*Time'": 1.0, 'startTime': 'ErrorLevel.warning'}))
    results = parseString(testdata)
    if results != expected:
        print("Results:", results)
        print("Expected:", expected)
        print("Failed")
        sys.exit(1)
    print("Matches expected output")
    print(type(results), repr(results))
