# -*- coding: utf-8 -*-
"""

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

 Author : Anand Kalaiarasi Ganeson, ganan642@student.liu.se, 2012-03-19
 Version: 1.0
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from builtins import int, range

import sys

result = dict()

inner_sets = []
next_set_list = []
next_set = []
next_set.append('')


def bool_from_string(string):
    """Attempt conversion of string to a boolean """
    if string in {'true', 'True', 'TRUE'}:
        return True
    elif string in {'false', 'False', 'FALSE'}:
        return False
    else:
        raise ValueError


def typeCheck(string):
    """Attempt conversion of string to a usable value"""
    types = [bool_from_string, int, float, dict, str]

    if type(string) in {int, float}:
        return string

    string = string.strip()

    for t in types:
        try:
            return t(string)
        except ValueError:
            continue
    else:
        print("String contains un-handled datatype")
        return string


def make_values(strings, name):
    if strings[0] == "(" and strings[-1] == ")":
        strings = strings[1:-1]
    if strings[0] == "{" and strings[-1] == "}":
        strings = strings[1:-1]

    # find the highest Set number of SET
    for each_name in result:
        if each_name.find("SET") != -1:
            main_set_name = each_name

    if strings[0] == "\"" and strings[-1] == "\"":
        strings = strings.replace("\\\"", "\"")
        result[main_set_name]['Values'] = []
        result[main_set_name]['Values'].append(strings)
    else:
        anchor = 0
        position = 0
        stop = 0
        prop_str = strings
        main_set_name = "SET1"

        # remove braces & keep only the SET's values
        while position < len(prop_str):
            check = prop_str[position]
            if check == "{":
                anchor = position
            elif check == "}":
                stop = position
                delStr = prop_str[anchor:stop + 1]

                i = anchor
                while i > 0:
                    text = prop_str[i]
                    if text == ",":
                        name_start = i + 1
                        break
                    i -= 1
                name_of_set = prop_str[name_start:anchor]
                if name_of_set.find("=") == -1:
                    prop_str = prop_str.replace(delStr, '').strip()
                    position = 0

            position += 1

        for each_name in result:
            if each_name.find("SET") != -1:
                main_set_name = each_name

        values = []
        anchor = 0
        brace_count = 0
        for i, c in enumerate(prop_str):
            if c == "," and brace_count == 0:
                value = prop_str[anchor:i]
                value = (value.lstrip()).rstrip()
                if "=" in value:
                    result[main_set_name]['Elements'][name]['Properties']['Results'] = {}
                else:
                    result[main_set_name]['Elements'][name]['Properties']['Values'] = []
                values.append(value)
                anchor = i + 1
            elif c == "{":
                brace_count += 1
            elif c == "}":
                brace_count -= 1

            if i == len(prop_str) - 1:
                values.append(((prop_str[anchor:i + 1]).lstrip()).rstrip())

        for each_val in values:
            multiple_values = []
            if "=" in each_val:
                pos = each_val.find("=")
                varName = each_val[0:pos]
                varName = typeCheck(varName)
                varValue = each_val[pos + 1:len(each_val)]
                if varValue != "":
                    varValue = typeCheck(varValue)
            else:
                varName = ""
                varValue = each_val
                if varValue != "":
                    varValue = typeCheck(varValue)

            if isinstance(varValue, str) and "," in varValue:
                varValue = (varValue.replace('{', '').strip()).replace('}', '').strip()
                multiple_values = varValue.split(",")

            for n in range(len(multiple_values)):
                each_v = multiple_values[n]
                multiple_values.pop(n)
                each_v = typeCheck(each_v)
                multiple_values.append(each_v)

            if len(multiple_values) != 0:
                result[main_set_name]['Elements'][name]['Properties']['Results'][varName] = multiple_values
            elif varName != "" and varValue != "":
                result[main_set_name]['Elements'][name]['Properties']['Results'][varName] = varValue
            else:
                if varValue != "":
                    result[main_set_name]['Elements'][name]['Properties']['Values'].append(varValue)


def delete_elements(strings):
    index = 0
    while index < len(strings):
        character = strings[index]
        # handle data within the parenthesis ()
        if character == "(":
            pos = index
            while pos > 0:
                char = strings[pos]
                if char == "":
                    break
                elif char == ",":
                    break
                elif char == " ":
                    pos = pos + 1
                    break
                elif char == "{":
                    break
                pos = pos - 1
            delStr = strings[pos: strings.rfind(")")]
            strings = strings.replace(delStr, '').strip()
            strings = ''.join(c for c in strings if c not in '{}''()')
        index += 1
    return strings


def make_subset_sets(strings, name):
    index = 0
    anchor = 0
    main_set_name = "SET1"
    subset_name = "Subset1"
    set_name = "Set1"

    set_list = strings.split(",")
    items = []

    # make the values list, first
    for each_item in set_list:
        each_item = ''.join(c for c in each_item if c not in '{}')
        each_item = typeCheck(each_item)
        items.append(each_item)

    if "SET" in name:
        # find the highest SET number
        for each_name in result:
            if each_name.find("SET") != -1:
                main_set_name = each_name

        # find the highest Subset number
        for each_name in result[main_set_name]:
            if each_name.find("Subset") != -1:
                subset_name = each_name

        highest_count = 1
        # find the highest Set number & make the next Set in Subset
        for each_name in result[main_set_name][subset_name]:
            if each_name.find("Set") != -1:
                the_num = each_name.replace('Set', '')
                the_num = int(the_num)
                if the_num > highest_count:
                    highest_count = the_num
                    the_num += 1
                elif highest_count > the_num:
                    the_num = highest_count + 1
                else:
                    the_num += 1
                set_name = 'Set' + str(the_num)

        result[main_set_name][subset_name] = {}
        result[main_set_name][subset_name][set_name] = []
        result[main_set_name][subset_name][set_name] = items

    else:
        for each_name in result:
            if each_name.find("SET") != -1:
                main_set_name = each_name

        if "Subset1" not in result[main_set_name]['Elements'][name]['Properties']:
            result[main_set_name]['Elements'][name]['Properties'][subset_name] = {}

        for each_name in result[main_set_name]['Elements'][name]['Properties']:
            if each_name.find("Subset") != -1:
                subset_name = each_name

        highest_count = 1
        for each_name in result[main_set_name]['Elements'][name]['Properties'][subset_name]:
            if each_name.find("Set") != -1:
                the_num = each_name.replace('Set', '')
                the_num = int(the_num)
                if the_num > highest_count:
                    highest_count = the_num
                    the_num += 1
                elif highest_count > the_num:
                    the_num = highest_count + 1
                else:
                    the_num += 1
                set_name = 'Set' + str(the_num)

        result[main_set_name]['Elements'][name]['Properties'][subset_name][set_name] = []
        result[main_set_name]['Elements'][name]['Properties'][subset_name][set_name] = items


def make_sets(strings, name):
    if strings == "{}":
        return
    index = 0
    anchor = 0
    main_set_name = "SET1"
    set_name = "Set1"

    if strings[0] == "{" and strings[-1] == "}":
        strings = strings[1:-1]

    set_list = strings.split(",")
    items = []

    for each_item in set_list:
        each_item = typeCheck(each_item)
        if isinstance(each_item, str):
            each_item = (each_item.lstrip()).rstrip()
        items.append(each_item)

    for each_name in result:
        if each_name.find("SET") != -1:
            main_set_name = each_name

    if "SET" in name:
        highest_count = 1
        for each_name in result[main_set_name]:
            if each_name.find("Set") != -1:
                the_num = each_name.replace('Set', '')
                the_num = int(the_num)
                if the_num > highest_count:
                    highest_count = the_num
                    the_num += 1
                elif highest_count > the_num:
                    the_num = highest_count + 1
                else:
                    the_num += 1
                set_name = 'Set' + str(the_num)

        result[main_set_name][set_name] = []
        result[main_set_name][set_name] = items

    else:
        highest_count = 1
        for each_name in result[main_set_name]['Elements'][name]['Properties']:
            if each_name.find("Set") != -1:
                the_num = each_name.replace('Set', '')
                the_num = int(the_num)
                if the_num > highest_count:
                    highest_count = the_num
                    the_num += 1
                elif highest_count > the_num:
                    the_num = highest_count + 1
                else:
                    the_num += 1
                set_name = 'Set' + str(the_num)
        result[main_set_name]['Elements'][name]['Properties'][set_name] = []
        result[main_set_name]['Elements'][name]['Properties'][set_name] = items


def get_inner_sets(strings, for_this, name):
    start = 0
    end = 0
    main_set_name = "SET1"
    subset_name = "Subset1"

    if "{{" in strings:
        for each_name in result:
            if each_name.find("SET") != -1:
                main_set_name = each_name
        if "SET" in name:
            highest_count = 1
            for each_name in result[main_set_name]:
                if each_name.find("Subset") != -1:
                    the_num = each_name.replace('Subset', '')
                    the_num = int(the_num)
                    if the_num > highest_count:
                        highest_count = the_num
                        the_num += 1
                    elif highest_count > the_num:
                        the_num = highest_count + 1
                    else:
                        the_num += 1
                    subset_name = subset_name + str(the_num)
            result[main_set_name][subset_name] = {}
        else:
            highest_count = 1
            for each_name in result[main_set_name]['Elements'][name]['Properties']:
                if each_name.find("Subset") != -1:
                    the_num = each_name.replace('Subset', '')
                    the_num = int(the_num)
                    if the_num > highest_count:
                        highest_count = the_num
                        the_num += 1
                    elif highest_count > the_num:
                        the_num = highest_count + 1
                    else:
                        the_num += 1
                    subset_name = "Subset" + str(the_num)
            result[main_set_name]['Elements'][name]['Properties'][subset_name] = {}

        start = strings.find("{{")
        end = strings.find("}}")
        sets = strings[start + 1:end + 1]
        index = 0
        while index < len(sets):
            inner_set_start = sets.find("{")
            if inner_set_start != -1:
                inner_set_end = sets.find("}")
                inner_set = sets[inner_set_start:inner_set_end + 1]
                sets = sets.replace(inner_set, '')
                index = 0
                make_subset_sets(inner_set, name)
            index += 1
    elif "{" in strings:
        position = 0
        b_count = 0
        while position < len(strings):
            character = strings[position]
            if character == "{":
                b_count += 1
                if b_count == 1:
                    mark_start = position
            elif character == "}":
                b_count -= 1
                if b_count == 0:
                    mark_end = position + 1
                    sets = strings[mark_start:mark_end]
                    make_sets(sets, name)
            position += 1


def make_elements(strings):
    original_string = strings
    index = 0
    main_set_name = "SET1"

    while index < len(strings):
        character = strings[index]
        if character == "(":
            pos = index - 1
            while pos > 0:
                char = strings[pos]
                if char.isalnum():
                    begin = pos
                    pos = pos - 1
                else:
                    break

            name = strings[begin:index]
            index = pos
            original_name = name
            name = name + str(1)

            for each_name in result:
                if each_name.find("SET") != -1:
                    main_set_name = each_name

            highest_count = 1
            for each_name in result[main_set_name]['Elements']:
                if original_name in each_name:
                    the_num = each_name.replace(original_name, '')
                    the_num = int(the_num)
                    if the_num > highest_count:
                        highest_count = the_num
                        the_num += 1
                    elif highest_count > the_num:
                        the_num = highest_count + 1
                    else:
                        the_num += 1
                    name = original_name + str(the_num)

            result[main_set_name]['Elements'][name] = {}
            result[main_set_name]['Elements'][name]['Properties'] = {}

            brace_count = 0

            skip_brace = 0
            while index < len(strings):
                character = strings[index]
                if character == "(":
                    brace_count += 1
                    if brace_count == 1:
                        mark_start = index
                elif character == ")":
                    brace_count -= 1
                    mark_end = index + 1
                    if brace_count == 0:
                        mark_end = index + 1
                        index += 1
                        break
                elif character == "=":
                    skip_start = index + 1
                    if strings[skip_start] == "{":
                        skip_brace += 1
                        indx = skip_start
                        while indx < len(strings):
                            char = strings[indx]
                            if char == "}":
                                skip_brace -= 1
                                if skip_brace == 0:
                                    index = indx + 1
                                    break
                            indx += 1

                index += 1

            element_str = strings[mark_start:mark_end]
            del_element_str = original_name + element_str
            strings = strings.replace(del_element_str, '').strip()

            index = 0
            start = 0
            end = 0
            position = 0
            while position < len(element_str):
                char = element_str[position]
                if char == "{" and element_str[position + 1] == "{":
                    start = position - 1
                    end = element_str.find("}}")
                    sets = element_str[start:end + 2]
                    position = position + len(sets)
                    element_str = element_str.replace(sets, '')
                    position = 0
                    if len(sets) > 1:
                        get_inner_sets(sets, "Subset", name)
                elif char == "{":
                    start = position
                    end = element_str.find("}")
                    sets = element_str[start:end + 1]

                    i = start
                    while i > 0:
                        text = element_str[i]
                        if text == ",":
                            name_start = i + 1
                            break
                        i -= 1
                    name_of_set = element_str[name_start:start]
                    if name_of_set.find("=") == -1:
                        element_str = element_str.replace(element_str[start:end + 1], '').strip()
                        position = 0
                        if len(sets) > 1:
                            get_inner_sets(sets, "Set", name)
                position += 1
            make_values(element_str, name)
        index += 1


def check_for_next_string(next_string):
    anchorr = 0
    positionn = 0
    stopp = 0

    # remove braces & keep only the SET's values
    while positionn < len(next_string):
        check_str = next_string[positionn]
        if check_str == "{":
            anchorr = positionn
        elif check_str == "}":
            stopp = positionn
            delStr = next_string[anchorr:stopp + 1]
            next_string = next_string.replace(delStr, '')
            positionn = -1
        positionn += 1

        if isinstance(next_string, str):
            if len(next_string) == 0:
                next_set = ""
                return next_set


def get_the_set(string):

    def skip_all_inner_sets(position):
        position += 1
        count = 1
        main_count = 1
        max_count = main_count
        last_set = 0
        last_subset = 0
        last_brace = 0
        pos = position

        while pos < len(string):
            charac = string[pos]
            if charac == "{":
                count += 1
                max_count = count
            elif charac == "}":
                count -= 1
                if count == 0:
                    end_of_main_set = pos
                    break
            pos += 1
        if count != 0:
            print("\nParser Error: Are you missing one or more '}'s? \n")
            sys.exit(1)

        if max_count >= 2:
            while position < end_of_main_set:
                brace_count = 0
                char = string[position]
                if char == "{" and string[position + 1] != "{":
                    start = position
                    main_count += 1
                    if main_count >= 2:
                        mark_index = position

                    b_count = 0
                    while position < len(string):
                        ch = string[position]
                        if ch == "{":
                            main_count += 1
                            b_count += 1
                        elif ch == "}":
                            b_count -= 1
                            if b_count == 0:
                                if main_count <= 2:
                                    skip = position + 1
                                    last_set = skip
                                    inner_sets.append(string[start:skip])
                                elif main_count > 2:
                                    skip = position + 1
                                    last_set = skip
                                    position = skip
                                    next_set_list.append(string[mark_index:skip])
                                    if next_set[0] == '':
                                        next_set[0] = string[mark_index:skip]
                                    else:
                                        next_set[0] = next_set[0] + string[mark_index:skip]
                                break
                        elif ch == "(":
                            brace_count += 1
                            brace_start = position
                            position += 1
                            while position < end_of_main_set:
                                s = string[position]
                                if s == "(":
                                    brace_count += 1
                                elif s == ")":
                                    brace_count -= 1
                                    if brace_count == 0:
                                        last_brace = position
                                        break
                                elif s == "=" and string[position + 1] == "{":
                                    indx = position + 2
                                    skip_brace = 1
                                    while indx < end_of_main_set:
                                        char = string[indx]
                                        if char == "}":
                                            skip_brace -= 1
                                            if skip_brace == 0:
                                                position = indx + 1
                                                break
                                        indx += 1
                                position += 1
                        position += 1
                elif char == "{" and string[position + 1] == "{":
                    start = position
                    main_count += 1
                    if main_count >= 2:
                        mark_index = position
                    position += 1
                    b_count = 1

                    while position < len(string):
                        ch = string[position]
                        if ch == "{":
                            main_count += 1
                            b_count += 1
                        elif ch == "}":
                            b_count -= 1
                            if b_count == 0:
                                if main_count <= 3:
                                    skip = position + 1
                                    last_subset = skip
                                    inner_sets.append(string[start:skip])
                                elif main_count > 3:
                                    skip = position + 1
                                    last_subset = skip
                                    position = skip
                                    next_set_list.append(string[mark_index:skip])
                                    if next_set[0] == '':
                                        next_set[0] = string[mark_index:skip]
                                    else:
                                        next_set[0] = next_set[0] + string[mark_index:skip]
                                break
                        elif ch == "(":
                            brace_count += 1
                            brace_start = position
                            position += 1
                            while position < end_of_main_set:
                                s = string[position]
                                if s == "(":
                                    brace_count += 1
                                elif s == ")":
                                    brace_count -= 1
                                    if brace_count == 0:
                                        last_brace = position
                                        break
                                position += 1
                        position += 1
                elif char == "(":
                    brace_count += 1
                    brace_start = position
                    position += 1
                    while position < end_of_main_set:
                        s = string[position]
                        if s == "(":
                            brace_count += 1
                        elif s == ")":
                            brace_count -= 1
                            if brace_count == 0:
                                last_brace = position
                                break
                        position += 1

                position += 1
        else:
            next_set[0] = ""
            return (len(string) - 1)

        max_of_sets = max(last_set, last_subset)
        max_of_main_set = max(max_of_sets, last_subset)

        if max_of_main_set != 0:
            return max_of_main_set
        else:
            return (len(string) - 1)

    # Main entry of get_the_string()
    index = 0
    count = 0
    next_set[0] = ''
    inner_sets = []
    next_set_list = []
    end = len(string)

    if "{" and "}" in string:
        while index < len(string):
            character = string[index]
            if character == "{":
                count += 1
                if count == 1:
                    anchor = index
                index = skip_all_inner_sets(index)
                if index == (len(string) - 1):
                    if string[index] == "}":
                        count -= 1
                        end = index
            elif character == "}":
                count -= 1
                if count == 0:
                    end = index
            index += 1
        main_set = string[anchor:end + 1]
        current_set = main_set

        if next_set[0] != "":
            for each_next in next_set_list:
                current_set = current_set.replace(each_next, '').strip()

            pos = 0
            # remove unwanted commas from CS
            while pos < len(current_set):
                char = current_set[pos]
                if char == ",":
                    if current_set[pos + 1] == "}":
                        current_set = current_set[0:pos] + current_set[pos + 1:(len(current_set))]
                        pos = 0
                pos += 1

            check_string = ''.join(e for e in current_set if e.isalnum())

            if len(check_string) > 0:
                return current_set, next_set[0]
            else:
                current_set = ""
                return current_set, next_set[0]
        else:
            return current_set, next_set[0]
    else:
        print("\nThe following String has no {}s to proceed\n")
        print(string)

    # End of get_the_string()

# String parsing function for SimulationResults


def formatSimRes(strings):
    result['SimulationResults'] = {}
    simRes = strings[strings.find('  resultFile') + 1:strings.find('\nend SimulationResult')]
    simRes = simRes.translate(None, "\\")
    simRes = simRes.split('\n')
    simOps = simRes.pop(1)
    options = simOps[simOps.find('"startTime') + 1:simOps.find('",')]
    options = options + ","
    index = 0
    anchor = 0

    for i in simRes:
        var = i[i.find('') + 1:i.find(" =")]
        var = (var.lstrip()).rstrip()
        value = i[i.find("= ") + 1:i.find(",")]
        value = (value.lstrip()).rstrip()
        value = typeCheck(value)
        result['SimulationResults'][var] = value

    result['SimulationOptions'] = {}

    while index < len(options):
        update = False
        character = options[index]
        if character == "=":
            opVar = options[anchor:index]
            opVar = (opVar.lstrip()).rstrip()
            anchor = index + 1
            update = False
        elif character == ",":
            opVal = options[anchor:index]
            opVal = (opVal.lstrip()).rstrip()
            anchor = index + 1
            update = True
        index = index + 1
        if update:
            opVal = typeCheck(opVal)
            result['SimulationOptions'][opVar] = opVal

# string parsing function for Record types


def formatRecords(strings):
    result['RecordResults'] = {}
    recordName = strings[strings.find("record ") + 1:strings.find("\n")]
    recordName = recordName.replace("ecord ", '').strip()
    strings = strings.replace(("end " + recordName + ";"), '').strip()
    recordItems = strings[strings.find("\n") + 1: len(strings)]
    recordItems = recordItems.translate(None, "\\")
    recordItems = recordItems.split("\n")
    for each_item in recordItems:
        var = each_item[each_item.find('') + 1:each_item.find(" =")]
        var = (var.lstrip()).rstrip()
        value = each_item[each_item.find("= ") + 1:each_item.find(",")]
        value = (value.lstrip()).rstrip()
        value = typeCheck(value)
        if var != "":
            result['RecordResults'][var] = value
    result['RecordResults']['RecordName'] = recordName


# Main entry to the OMParser module


def check_for_values(string):
    main_set_name = "SET1"
    if len(string) == 0:
        return result

    # changing untyped results to typed results
    if string[0] == "(":
        string = "{" + string[1:-2] + "}"

    if string[0] == "\"":
        string = string.replace("\\\"", "\"")
        string = string.replace("\\?", "?")
        string = string.replace("\\'", "'")
        return string

    if "record SimulationResult" in string:
        formatSimRes(string)
        return result
    elif "record " in string:
        formatRecords(string)
        return result

    string = typeCheck(string)

    if not isinstance(string, str):
        return string
    elif string.find("{") == -1:
        return string

    current_set, next_set = get_the_set(string)

    for each_name in result:
        if each_name.find("SET") != -1:
            the_num = each_name.replace("SET", '')
            the_num = int(the_num)
            the_num = the_num + 1
            main_set_name = "SET" + str(the_num)

    result[main_set_name] = {}

    if current_set != "":
        if current_set[1] == "\"" and current_set[-2] == "\"":
            make_values(current_set, "SET")
            current_set = ""
            check_for_next_iteration = ''.join(e for e in next_set if e.isalnum())
            if len(check_for_next_iteration) > 0:
                check_for_values(next_set)

        elif "(" in current_set:
            for each_name in result:
                if each_name.find("SET") != -1:
                    main_set_name = each_name
            result[main_set_name]['Elements'] = {}

            make_elements(current_set)
            current_set = delete_elements(current_set)

    if "{{" in current_set:
        get_inner_sets(current_set, "Subset", main_set_name)

    if "{" in current_set:
        get_inner_sets(current_set, "Set", main_set_name)

    check_for_next_iteration = ''.join(e for e in next_set if e not in {""})
    if len(check_for_next_iteration) > 0:
        check_for_values(next_set)
    else:
        check_for_next_iteration = ''.join(e for e in next_set if e.isalnum())
        if len(check_for_next_iteration) > 0:
            check_for_values(next_set)

    return result
