"""
Exaple of how to use pyproj to convert to and from UK coordinates

It should be possble to do this more efficiently with arrays
"""

from pyproj import Transformer

# Some pairs of coordinates from gridfinder.com. lat long is to 3dp, E/N to the nearest metre
lat, long = 55.023,	-1.536
E, N = 429763, 569927

# Define the projection for British National Grid
bng = 'epsg:27700'
# Define the projection used by most SatNav Google etc.
wgs84 = 'epsg:4326'
# Define the transformation as from wgs84 (long, lat) to bng(Eastings/Northings)
transformer = Transformer.from_crs(wgs84, bng)
# Test them out ...
e2, n2 = transformer.transform(lat, long)

print('expecting coords', E, N)
print('returned coords', e2, n2)
print('difference is', E - e2, N - n2)

# To go the other way first switch the arguments to the transformer
transformer = Transformer.from_crs(bng, wgs84)
lat2, long2 = transformer.transform(E, N)

print('expecting coords', lat, long)
print('returned coords', lat2, long2)
print('difference is', lat - lat2, long - long2)
