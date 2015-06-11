scale = None
input_text1 = 'which map are you working on: '
input_text2 = 'System Map (sm), City Center (cc) or Pylon Maps (p)?: '
map_msg = input_text1 + input_text2
scale_flag = raw_input(map_msg)

# scale in feet, more common notation would be 1:scale, indicating that something
# that is 1 unit in size on the map as many times bigger as the value in 'scale'
# in the real world
while scale == None:
	if scale_flag.lower() in ('sm', 'system map'):
		scale = 100000
	elif scale_flag.lower() in ('cc', 'city center'):
		scale = 14000
	elif scale_flag.lower() in ('p', 'pylon'):
		scale = 3000
	else:
		scale_flag = raw_input('invalid map input, enter "sm", "cc" or "p": ')

# values below are in cartographic points
w1 = input('enter the width of the first line, in points: ')
w2 = input('enter the width of the second line, in points: ')
gap = input('enter the width the desired gap between the lines, in points: ')

# a point in graphic design/cartography in 1/72nd of an inch, this converts that
# value to feet 
# http://graphicdesign.stackexchange.com/questions/199/point-vs-pixel-what-is-the-difference
carto_pt_feet = 1 / float(72) / 12 
pt_at_scale = carto_pt_feet * scale

offset = ((w1 / float(2)) + (w2 / float(2)) + gap) * pt_at_scale
print 'The offset value at scale 1:{0}'.format(scale)
print 'with line witdths of {0} & {1} and a gap of {2}'.format(w1, w2, gap)

# round to nearest foot for small scales and nearest tenth of a foot for large
if scale > 10000:
	offset = int(round(offset))
else:
	offset = round(offset, 1)
print '***is {0} feet***'.format(offset)