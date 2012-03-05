#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The PdTextGen library for Pure Data text generation
#
# Copyright 2012 Pablo Duboue
# <pablo.duboue@gmail.com>
# http://duboue.net
#
# PdTextGen is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PdTextGen is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the gnu general public license
# along with PdTextGen.  If not, see <http://www.gnu.org/licenses/>.

from pyparsing import Word, Literal, Or, Optional, OneOrMore, alphanums
from pdfile import pdfile
import sys

"""
A compiler from message definitions into Pd patches.
"""

# reserved words
reserved_words = ['name', 'slots', 'constants', 'equations', 'output']
reserved_parsers = []

for reserved in reserved_words:
    literal = Literal(reserved.upper())
    globals()[reserved] = literal
    reserved_parsers.append(literal)

reserved = Or(reserved_parsers)
word = ~reserved + Word(alphanums + "_" + "-")
function = Literal("lexicon")

equation = word + "=" + function + "(" + OneOrMore(word) + \
           Optional(Literal(";") + OneOrMore(word + Optional(Literal("'")))) + ")"
def parse_equation(toks):
    name = toks[0]
    function = toks[2]
    first_slot = []
    second_slot = []
    in_first = True
    position = 4
    while position < len(toks)-1:
        token = toks[position]
        if token == ";":
            in_first = False
        elif token == "'":
            second_slot[-1] = (second_slot[-1][0], 1)
        elif in_first:
            first_slot.append(token)
        else:
            second_slot.append((token, 0))
        position += 1
    return ( name, function, first_slot, second_slot )
equation.addParseAction(parse_equation)

name_section = name + word
def parse_name(toks):
    global msg_name
    msg_name = toks[1]
name_section.addParseAction(parse_name)

slots_section = slots + OneOrMore(word)
def parse_slots(toks):
    global slot_names
    slot_names = toks[1:]
slots_section.addParseAction(parse_slots)

constants_section = Optional(constants + OneOrMore(word))
constant_names = []
def parse_constants(toks):
    global constant_names
    constant_names = toks[1:]
constants_section.addParseAction(parse_constants)

equations_section = equations + OneOrMore(equation)
equations = []
def parse_equations(toks):
    global equations
    equations = toks[1:]
equations_section.addParseAction(parse_equations)

output_section = output + OneOrMore(word)
def parse_outputs(toks):
    global output_names
    output_names = toks[1:]
output_section.addParseAction(parse_outputs)

message = name_section + slots_section + constants_section + \
          equations_section + output_section

def main():
    msg_file = open(sys.argv[1])
    msg_text = msg_file.read()
    msg_file.close()

    message.parseString(msg_text)
    print "Parsed:"
    print msg_name
    print slot_names
    print constant_names
    print equations
    print output_names

    pd = pdfile.PdFile(sys.argv[2] if len(sys.argv) > 2 else msg_name + ".pd", \
                       pos=[10, 10], size=[500, 500], font_size=16)
    pdfile.PdFile.modify_globals = True
    main = pd.main

    # inlets / outlet
    main.add(pdfile.PdObject('inlet', x=10, y=10), 'msg_in_bang')
    main.add(pdfile.PdObject('inlet', x=100, y=10), 'msg_in_slot')
    main.add(pdfile.PdObject('outlet', x=10, y=400), 'msg_out')

    # slot router
    main.add(pdfile.PdObject('route', *slot_names, x=100, y=50), 'msg_route')
    main.connect(pdfile.msg_in_slot, 0, pdfile.msg_route, 0)
    main.add(pdfile.PdObject('print', msg_name+":", 'unknown', 'slot', x=100, y=400),
             'msg_error')
    main.connect(pdfile.msg_route, len(slot_names), pdfile.msg_error, 0)

    # constants (if any)
    main.set_next_pos(x=300, y=122)
    for constant in constant_names:
        main.add(pdfile.PdMsg(constant), constant)

    # equations
    main.set_next_pos(x=100, y=100)
    for equation in equations:
        eq = main.add(pdfile.PdObject(equation[1]), equation[0])

        # fulfill connections
        for name in equation[2]:
            if name in slot_names:
                main.connect(pdfile.msg_route, slot_names.index(name), eq, 0)
            else:
                main.connect(name, 0, eq, 0)
        
        for name, slot in equation[3]:
            if name in slot_names:
                main.connect(pdfile.msg_route, slot_names.index(name), eq, 1)
            else:
                main.connect(name, slot, eq, 1)

    # output
    main.set_next_pos(x=10, y=100)
    main.add(pdfile.PdObject('t', *[ 'b' for x in range(len(constant_names)+1)]),
             'msg_triggers')
    main.connect(pdfile.msg_in_bang,0, pdfile.msg_triggers, 0)
    for idx in range(len(constant_names)):
        main.connect(pdfile.msg_triggers, idx+1, constant_names[idx], 0)

    previous = pdfile.msg_triggers
    for output in output_names:
        msg_list = main.add(pdfile.PdObject('list'), 'msg_list_' + output)
        main.connect(previous, 0, msg_list, 0)
        main.connect(output, 0, msg_list, 1)
        previous = msg_list

    main.connect(previous, 0, pdfile.msg_out, 0)
    pd.write()


if __name__ == '__main__':
    main()


                  
