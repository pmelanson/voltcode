# Python 3
import matplotlib.path as mplPath
import numbers

class Point:
    def __init__(self, x, y):
        # We use reals because mplPath only takes Reals, and it's hard
        # to do for imaginaries
        assert isinstance(x, numbers.Real), "was not given a number for point"
        assert isinstance(y, numbers.Real), "was not given a number for point"
        self.x = x
        self.y = y


class Polygon:
    _vertices = []
    def __init__(self, vertices):
        try:
            for e in vertices:
                assert isinstance(e, Point), "Need points"
        except TypeError:
            print("Need a list of points")
        assert(len(vertices) > 2) # I assume this class will be probably used
        # for drawing things, not graph theorists. I don't have an actual client,
        # so I can't determine this. So I'll go with the most sane option.
        self._vertices = vertices

    def pointInPolygon(self, p):
        if len(self._vertices) < 3:
            return False # I decided to return False because
        polyEdges = []
        for e in self._vertices:
            polyEdges.append([e.x, e.y]) # build an Nx2 dimensional
            # because mplPath.Path takes Nx2 dimensional lists
        # making use of super-efficient
        return mplPath.Path(polyEdges).contains_point([p.x, p.y])

"""
Test cases to try:
    check if a point in a square works
    check if a point in a polygon where the order of vertices matters works
    for example:
        ___
         \|
         /|
        ---
    since this polygon could be mirrored depending on what order
    vertices are given in

    also, check for 0-gons, 1-gons, 2-gons, and 3-gons
    check if a point lying just inside a concave portion of a polygon
      is not inside the polygon
    finally, a stress test by generating a, say, 5000-gon approximation of
      a pacman shape, then test if a point lies outside in the 'mouth' and
      when outside of the radius
"""

"""
I haven't implemented a regularOctagon class because I was only given
a weekend to work on this and I have other assignments that are much
more time-sensitive and count directly for marks. I've done most of
the underlying work in the class above.
I realize deadlines are tight during continuous round, but I have to
prioritize school because I'm paying for that privilege.

Thanks for your understanding,
<3
-- Patrick Melanson
"""
