"""
#          x  x  x# <-- Your opponent's aliens spawn here and move down
#                 #
#                 #
#                 #
#                 #
#                 #
# ---         --- #
# ---         --- #
# ---         --- #
#       AAA       #
#                 # <-- Your building row

------------------------------------------------------------------------------------------------------------------------
CALCULATE POSSIBLE ALIEN WAVES reduce a pow(2,17) problem to 155 possibilities!
------------------------------------------------------------------------------------------------------------------------

Possible waves
[    x  x  x  x  x]
[       x  x  x  x]
[          x  x  x]
[             x  x]
[                x]

[   x  x  x  x  x ]
[      x  x  x  x ]
[         x  x  x ]
[            x  x ]
[               x ]

[  x  x  x  x  x  ]
[     x  x  x  x  ]
[        x  x  x  ]
[           x  x  ]
[              x  ]

[  x  x  x  x  x  ]
[     x  x  x  x  ]
[        x  x  x  ]
[           x  x  ]
[              x  ] etc.

------------------------------------------------------------------------------------------------------------------------
POSSIBLE SYMBOLS IN EVERY ROW
------------------------------------------------------------------------------------------------------------------------
#                 # [XM!x|] = 5
#       VVV       # [V!x|]  = 4
# ---         --- # [i!x|-] = 5
# ---         --- # [i!x|-] = 5
# ---         --- # [i!x|-] = 5
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#          x  x  x# [i!x]   = 3
#                 # [i!]    = 2
#          x  x  x# [i!x]   = 3
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
#                 # [i!x|]  = 4
# ---         --- # [i!x|-] = 5
# ---         --- # [i!x|-] = 5
# ---         --- # [i!x|-] = 5
#       AAA       # [Aix|]  = 4
#                 # [XMix|] = 5

------------------------------------------------------------------------------------------------------------------------
POSSIBLE BUILDING / SHIP LAYOUTS
------------------------------------------------------------------------------------------------------------------------
[                 ]
[              MMM]
[             MMM ]
[            MMM  ]
[           MMM   ]
[          MMM    ] etc.

[                 ]
[              MMM]
[             MMM ]
[            MMM  ]
[           MMMXXX]
[    XXX   MMM    ] etc.

------------------------------------------------------------------------------------------------------------------------
PLAYER MISSILES * max of 2 missiles per player on board
------------------------------------------------------------------------------------------------------------------------
[!                ] Only one missile from a player can exist on a line
[!                ] A missile can only be on the next line if it is directly behind another missile
[  !              ] There must be at least one row between missiles if on separate lines (player moved)

"""

empty_row = '                 '

wave_forms = []
for i in range(1, 32):
    permutation = tuple('{0:05b}'.format(i).replace('0', ' ').replace('1', 'x'))
    wave_forms.append('    %s  %s  %s  %s  %s' % permutation)
    wave_forms.append('   %s  %s  %s  %s  %s ' % permutation)
    wave_forms.append('  %s  %s  %s  %s  %s  ' % permutation)
    wave_forms.append(' %s  %s  %s  %s  %s   ' % permutation)
    wave_forms.append('%s  %s  %s  %s  %s    ' % permutation)

print '%d wave forms' % len(wave_forms)
for wave in wave_forms:
    print '[%s]' % wave

unit_forms = []
for i in range(1, 16):
    unit_forms.append(' ' * (i - 1) + '***' + ' ' * (17 - i - 2))

print '%d unit forms' % len(unit_forms)
for unit_form in unit_forms:
    print '[%s]' % unit_form

enemy_ship_forms = []
missile_building_forms = []
factory_building_forms = []
building_forms = []
for unit_form in unit_forms:
    enemy_ship_forms.append(unit_form.replace('***', 'VVV'))
    missile_building_forms.append(unit_form.replace('***', 'MMM'))
    factory_building_forms.append(unit_form.replace('***', 'XXX'))
    building_forms.append(unit_form.replace('***', 'MMM'))
    building_forms.append(unit_form.replace('***', 'XXX'))


for m in range(0, 15):
    for f in range(0, 15):
        if abs(m - f) >= 3:
            row = list('                 ')
            row[m:m + 3] = ['M', 'M', 'M']
            row[f:f + 3] = ['X', 'X', 'X']
            building_forms.append(''.join(row))

print '%d building forms' % len(building_forms)
for building_form in building_forms:
    print '[%s]' % building_form