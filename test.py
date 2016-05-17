#coding: utf-8
import dxfgrabber, math, time
from PIL import Image, ImageDraw


class Point(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.valid = True

    def is_same_point(self, point):
        return self.x == point.x and self.y == point.y
    
    def distance(self, point):
        return math.sqrt((self.x - point.x)*(self.x - point.x) + (self.y - point.y)*(self.y - point.y))

    def __str__(self):
        return "%s,%s" % (self.x, self.y)

class Line(object):   
    def __init__(self, start, end):
        self.start = start
        self.end = end
        if self.start.x > self.end.x:
            self.start, self.end = self.end, self.start 
        elif self.start.x == self.end.x:
            if self.start.y > self.end.y:
                self.start, self.end = self.end, self.start 
        self.valid = True

    @property
    def angle(self):
        #范围-pi/2 , pi/2
        _x = self.end.x - self.start.x
        _y = self.end.y - self.start.y
        
        if _x == 0 :
            return math.pi/2
        else :
            return math.atan(_y / _x)
    
    #检查线之间距离是否合法
    def check(self, line, min_dis, max_dis):
        if self.start.distance(line.start) < min_dis or self.start.distance(line.start) > max_dis:
            return False
        elif self.end.distance(line.end) < min_dis or self.end.distance(line.end) > max_dis:
            return False
        return True
        

    #两直线距离，相交直线为0
    def distance_to_line(self, line):
        if abs(self.angle - line.angle) > 0.01 :
            return 0
        #y = kx + b1 & y = kx + b2 两平行直线的k 
        k = math.tan(self.angle)/2 + math.tan(line.angle)/2
        
        molecule = self.start.y - line.start.y - k * (self.start.x - line.start.x)
        denominator = math.sqrt(k*k + 1)
        
        return abs(molecule / denominator)

    def __str__(self):
        return "line from %s to %s" % (self.start, self.end)
    
class Speed(object):
    """docstring for Speed"""
    def __init__(self,filename):
        self.MinTrackWidth = 5
        self.MaxTrackWidth = 20

    	start = time.time()
        self.dxf = dxfgrabber.readfile(filename)
        print "readfile" , time.time() - start
        self.lines = self.get_line()
        print "get_line" , time.time() - start

        self.draw_line(self.get_track())
    
    def find_layer_by_name(self,name):
        for layer in self.dxf.layers:
            if layer.name == name:
                return layer
    
    def get_line(self):
        lines = []
        entities_on = [entity for entity in self.dxf.entities if self.find_layer_by_name(entity.layer).on ]

        for entity in entities_on:
            if entity.dxftype == 'LINE' :
                start = Point(entity.start[0], entity.start[1])
                end = Point(entity.end[0], entity.end[1])
                line = Line(start, end)
                lines.append(line)
            elif entity.dxftype == 'POLYLINE' :
                pl_points = entity.points
                for i in range(len(pl_points) - 1 ):
                    start = Point(pl_points[i-1][0], pl_points[i-1][1])
                    end = Point(pl_points[i][0], pl_points[i][1])
                    line = Line(start, end)
                    lines.append(line)
            elif entity.dxftype == 'LWPOLYLINE' :
                pl_points = entity.points
                for i in range(len(pl_points) - 1 ):
                    start = Point(pl_points[i-1][0], pl_points[i-1][1])
                    end = Point(pl_points[i][0], pl_points[i][1])
                    line = Line(start, end)
                    lines.append(line)
        return lines
    
    def get_track(self):
    	track = []
        self.lines.sort(key = lambda l: l.start.y)
        lines = self.lines

        processing_line = lines.pop(0)
        track.extend([processing_line.start, processing_line.end])
        while lines:
            line = lines.pop(0)
            if processing_line.start.distance(line.start) < 1 or processing_line.start.distance(line.end) < 1 or processing_line.end.distance(line.start) < 1 or processing_line.end.distance(line.end) < 1:
                lines.remove(processing_line)
                track.extend([line.start, line.end])
                processing_line = line
        
        print track,len(track)
        # for line1 in self.lines:
        #     if not line1.valid:
        #         continue
        #     for line2 in self.lines:

        #         if line1 == line2 or not line2.valid :
        #             continue
                
        #         # if not line1.check(line2,1,20):
        #         #     continue

        #         if abs(line1.angle - line2.angle) > 0.1:
        #             continue
        #         # if line1.distance_to_line(line2) < self.MinTrackWidth or line1.distance_to_line(line2) > self.MaxTrackWidth:
        #         #     continue
        #         line1.valid = False
        #         line2.valid = False
        #         # start = Point(line1.start.x/2 + line2.start.x/2 , line1.start.y/2 + line2.start.y/2)
        #         # end = Point(line1.end.x/2 + line2.end.x/2 , line1.end.y/2 + line2.end.y/2)
        #         # track.append(Line(start,end))
        #         track.extend([line1, line2])
        # lines = self.lines
        # for l in lines:
            # print l.start.x
        # line = lines.pop(0)
        # track.append(line)
        # while True:
        #     lines.sort(key = lambda l : l.start.distance(line.end))
        #     line_next = lines.pop(0)
        #     if line.end.distance(line_next.start) < 1 :
        #         print line.end.distance(line_next.start)
        #         line = line_next
        #         track.append(line)
        #         lines.sort(key = lambda l: l.start.y)
        #     else:
        #         break
        return self.lines

    def draw_line(self, lines):
        all_points = [l.start for l in lines] + [l.end for l in lines]
        all_x,all_y = [p.x for p in all_points] , [p.y for p in all_points]
        size = [int(max(all_x)-min(all_x))+200,int(max(all_y)-min(all_y))+200]
        im = Image.new('RGB', size, (255,255,255))
        draw = ImageDraw.Draw(im)
        center = Point(max(all_x)/2+min(all_x)/2, max(all_y)/2+min(all_y)/2)
        def _convert(center,size,point):
            return [point.x-center.x+size[0]/2, -point.y+center.y+size[1]/2]
       
        for l in lines:
            draw.line(_convert(center,size,l.start)+_convert(center,size,l.end),"black")
        
        im.save("test.jpg")

if __name__ == "__main__":
    # p1 = Point(13,521)
    # p2 = Point(123,4)
    # p3 = Point(12,2)
    # p4 = Point(1,1)
    # line1 = Line(p1,p2)
    # line2 = Line(p3,p4)
    # print line1.distance_to_line(line2)

    Speed("test.dxf")