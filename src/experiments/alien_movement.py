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

Possible waves
[ x  x  x  x  x  x]
[    x  x  x  x  x]
[       x  x  x  x]
[          x  x  x]
[             x  x]
[                x]

[    x  x  x  x  x]
[       x  x  x  x]
[          x  x  x]
[             x  x]
[                x]
[                 ]

[       x  x  x  x]
[          x  x  x]
[             x  x]
[                x]
[                 ]
[                 ] etc.
"""

wave_forms = []
wave_forms.append('                 ')
for i in range(1, 64):
    permutation = tuple('{0:06b}'.format(i).replace('0', ' ').replace('1', 'x'))
    wave_forms.append(' %s  %s  %s  %s  %s  %s' % permutation)
    wave_forms.append('%s  %s  %s  %s  %s  %s ' % permutation)

print '%d wave forms' % len(wave_forms)
for wave in wave_forms:
    print '[%s]' % wave