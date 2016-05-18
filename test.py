#coding: utf-8
import dxfgrabber, math, time
from PIL import Image, ImageDraw


class Point(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.valid = True
        self.path = 0  
        self.direction = 0 

    def is_same_point(self, point):
        return self.x == point.x and self.y == point.y
    
    def distance(self, point):
        return math.sqrt((self.x - point.x)*(self.x - point.x) + (self.y - point.y)*(self.y - point.y))
    
    def angle_to(self, point):
        if point.x == self.x:
            return math.pi/2 if point.y > self.y else 3*math.pi/2
        ang = math.atan(float(point.y-self.y)/float(point.x-self.x))
        if point.x < self.x:
            ang += math.pi
        if ang < 0:
            ang += math.pi*2
        return ang

    def __str__(self):
        return "%s,%s" % (self.x, self.y)

class Line(object):   
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.valid = True
        
        if self.start.x != self.end.x :
            if self.start.x > self.end.x:
                self.start, self.end = self.end, self.start
            self.k = (self.end.y - self.start.y) / (self.end.x - self.start.x) 
            self.b = self.end.y - self.k * self.end.x
        else :
            self.k = "infinite"   
            if self.start.y > self.end.y:
                self.start, self.end = self.end, self.start

    @property
    def length(self):
        return self.start.distance(self.end)

    def points(self):
        sub_points = []
        if self.length <= 4:
            return [self.start]
        n = int(self.length)
        
        if self.k == "infinite":
            for i in range(0,n,4):
                sub_points.append(Point(self.start.x, self.start.y + i))
        else:
            for i in range(0,n,4):
                x = self.start.x + i / math.sqrt(self.k *self.k  +1)
                y = self.start.y + i * self.k  / math.sqrt(self.k *self.k  +1)
                sub_points.append(Point(x, y))
        return sub_points
            
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
        self.points = self.all_points()
        self.angle()
        self.html()
        
        # self.draw_line(self.get_track())
    
    def all_points(self):
        points = []
        for l in self.lines:
            points.extend(l.points())
        points.sort(key = lambda p : p.y)
        path = 0
        for i in range(len(points)-1):
            path += points[i+1].distance(points[i])
            points[i+1].path = path
        return points

    def angle(self, pace = 20):
        for i in range(len(self.points)-pace):
            points = self.points[i:i+pace]
            angle = 0
            for j in range(pace-1):
                angle += points[j].angle_to(points[j+1])
            if i+pace/2 < len(self.points) : 
                self.points[i+pace/2].direction = angle/(pace-1)/math.pi*180
            # print angle/(pace-1)/math.pi*180#, [[p.x, p.y] for p in points]

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
            for p in l.points():
                p_coor = _convert(center,size,p)
                xy = [int(p_coor[0])-1, int(p_coor[1])-1, int(p_coor[0])+1, int(p_coor[1])+1] 
                draw.arc(xy,0,360,"red")
        
        im.save("test.jpg")
    
    def html(self):
        input_html = open("hc.html")
        s = input_html.read()
        input_html.close()
        
        # categories = ["1","2","3"]
        # series = [{"name": 'test', "data" : [3,2,1]}]
        categories = []
        series = []
        y = {"name": 'y', "data" : []}
        direction = {"name": 'direction', "data" : []}
        for p in self.points:
            categories.append(p.path)
            y["data"].append(p.y - self.points[0].y)
            direction["data"].append(p.direction)
            print p.direction

        series.append(direction)
        output_html = open('test.html', 'w')
        output_html.write(s % (categories, series))
        output_html.close()

        

if __name__ == "__main__":
    # p1 = Point(13,521)
    # p2 = Point(123,4)
    # p3 = Point(12,2)
    # p4 = Point(1,1)
    # line1 = Line(p1,p2)
    # line2 = Line(p3,p4)
    # print line1.distance_to_line(line2)

    Speed("test.dxf")