# values below are in cartographic points
w1 = input('enter the width of the first line, in points: ')
w2 = input('enter the width of the second line, in points: ')
gap = input('enter the width the desired gap between the lines, in points: ')

# scale in feet, more common notation would be 1:scale, indicating that something
# that is 1 unit in size on the map as many times bigger as the value in 'scale'
# in the real world
scale = 100000

# a point in graphic design/cartography in 1/72nd of an inch, this converts that
# value to feet 
# http://graphicdesign.stackexchange.com/questions/199/point-vs-pixel-what-is-the-difference
carto_pt_feet = 1 / float(72) / 12 
pt_at_scale = carto_pt_feet * scale

offset = ((w1 / 2) + (w2 / 2) + gap) * pt_at_scale
print 'The offset value at scale 1:{0}'.format(scale)
print 'with line witdths of {0} & {1} and a gap of {2}'.format(w1, w2, gap)
print '***is {0} feet***'.format(int(round(offset))) # round to nearest ft