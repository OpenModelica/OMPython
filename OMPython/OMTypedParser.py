# -*- coding: utf-8 -*-
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
    infixNotation,
    opAssoc,
)


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
    return "'"+tmp+"'"


def convertString(s, s2):
    return s2[0].replace("\\\"", '"')


def convertDict(d):
    return dict(d[0])


def convertTuple(t):
    return tuple(t[0])


def evaluateExpression(s, loc, toks):
    # Convert the tokens (ParseResults) into a string expression
    flat_list = [item for sublist in toks[0] for item in sublist]
    expr = "".join(flat_list)
    try:
        # Evaluate the expression safely
        return eval(expr)
    except Exception:
        return expr


# Number parsing (supports arithmetic expressions in dimensions) (e.g., {1 + 1, 1})
arrayDimension = infixNotation(
    Word(alphas + "_", alphanums + "_") | Word(nums),
    [
        (Word("+-", exact=1), 1, opAssoc.RIGHT),
        (Word("*/", exact=1), 2, opAssoc.LEFT),
        (Word("+-", exact=1), 2, opAssoc.LEFT),
    ],
).setParseAction(evaluateExpression)

omcRecord = Forward()
omcValue = Forward()

# pyparsing's replace_with (and thus replaceWith) has incorrect type
# annotation: https://github.com/pyparsing/pyparsing/issues/602
TRUE = Keyword("true").setParseAction(replaceWith(True))  # type: ignore
FALSE = Keyword("false").setParseAction(replaceWith(False))  # type: ignore
NONE = (Keyword("NONE") + Suppress("(") + Suppress(")")).setParseAction(replaceWith(None))  # type: ignore
SOME = (Suppress(Keyword("SOME")) + Suppress("(") + omcValue + Suppress(")"))

omcString = QuotedString(quoteChar='"', escChar='\\', multiline=True).setParseAction(convertString)
omcNumber = Combine(Optional('-') + ('0' | Word('123456789', nums)) +
                    Optional('.' + Word(nums)) +
                    Optional(Word('eE', exact=1) + Word(nums + '+-', nums)))

# ident = Word(alphas + "_", alphanums + "_") | Combine("'" + Word(alphanums + "!#$%&()*+,-./:;<>=?@[]^{}|~ ") + "'")
ident = Word(alphas + "_", alphanums + "_") | QuotedString(quoteChar='\'', escChar='\\').setParseAction(convertString2)
fqident = Forward()
fqident << ((ident + "." + fqident) | ident)
omcValues = delimitedList(omcValue)
omcTuple = Group(Suppress('(') + Optional(omcValues) + Suppress(')')).setParseAction(convertTuple)
omcArray = Group(Suppress('{') + Optional(omcValues) + Suppress('}')).setParseAction(convertTuple)
omcArraySpecialTypes = Group(Suppress('{') + delimitedList(arrayDimension) + Suppress('}')).setParseAction(convertTuple)
omcValue << (omcString | omcNumber | omcRecord | omcArray | omcArraySpecialTypes | omcTuple | SOME | TRUE | FALSE | NONE | Combine(fqident))
recordMember = delimitedList(Group(ident + Suppress('=') + omcValue))
omcRecord << Group(Suppress('record') + Suppress(fqident) + Dict(recordMember) + Suppress('end') + Suppress(fqident) + Suppress(';')).setParseAction(convertDict)

omcGrammar = Optional(omcValue) + StringEnd()

omcNumber.setParseAction(convertNumbers)


def parseString(string):
    res = omcGrammar.parseString(string)
    if len(res) == 0:
        return
    return res[0]
