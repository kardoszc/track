#coding: utf-8
import dxfgrabber, math, time
from PIL import Image, ImageDraw


class Point(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.valid = True
        self.path = 0  #路程
        self.direction = 0  #车头方向
        self.platform = False
        self.speed = 1

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


class Arc(object):
    def __init__(self, center, radius, start_angle, end_angle):
        self.center = center
        self.radius = radius
        self.start_angle = math.pi * start_angle / 180
        self.end_angle = math.pi * end_angle / 180
    
    @property
    def start(self):
        return self.point_by_angle(self.start_angle)
    
    @property
    def end(self):
        return self.point_by_angle(self.end_angle)

    def point_by_angle(self, angle):
        angle = self.start_angle + angle
        x = self.center.x + math.cos(angle)*self.radius
        y = self.center.y + math.sin(angle)*self.radius
        point = Point(x, y)
        point._from = "ARC"
        return point 

    def points(self, pace = 2):
        points = []
        pace_angle = pace / self.radius
        n = int((self.end_angle - self.start_angle) / pace_angle)
        for i in range(n):
            angle = self.start_angle + i * pace_angle
            points.append(self.point_by_angle(angle))
        return points


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
    def start_key(self):
        return "%s,%s" % (round(self.start.x,2), round(self.start.y,2))
    
    @property
    def end_key(self):
        return "%s,%s" % (round(self.end.x,2), round(self.end.y,2))

    @property
    def length(self):
        return self.start.distance(self.end)

    def points(self, pace = 2):
        if self.length <= pace:
            return [self.start]
        points = []
        n = int(self.length/pace)
        
        if self.k == "infinite":
            for i in range(0,n,pace):
                points.append(Point(self.start.x, self.start.y + i*pace))
        else:
            for i in range(0,n,pace):
                x = self.start.x + i * pace / math.sqrt(self.k *self.k  + 1)
                y = self.start.y + i * pace * self.k  / math.sqrt(self.k *self.k  + 1)
                point = Point(x, y)
                points.append(point)
        return points
            
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
        self.MaxSpeed = 70
        # self.a = 1.1

    	start = time.time()
        self.dxf = dxfgrabber.readfile(filename)
        print "readfile" , time.time() - start
        self.lines = self.get_line()
        print "get_line" , time.time() - start

        self.points = self.all_points()
        # self.angle()
        
        self.get_platform()

        self.html()
        self.draw_line(self.lines)
    
    def all_points(self):
        points = []
        for entity in self.lines:
            points.extend(entity.points())
        points.sort(key = lambda p : p.y)
        # endpoints = {}
        # for entity in self.lines :
        #     start_key = "%s,%s" % (round(entity.start.x,2), round(entity.start.y,2))
        #     end_key = "%s,%s" % (round(entity.end.x,2), round(entity.end.y,2))
        #     if endpoints.has_key(entity.start_key) :
        #         endpoints[entity.start_key].append({"start":entity})
        #     else :
        #         endpoints[entity.start_key] = [{"start":entity}]

        #     if endpoints.has_key(entity.end_key) :
        #         endpoints[entity.end_key].append({"end":entity})
        #     else :
        #         endpoints[entity.end_key] = [{"end":entity}]
        
        # key = ''
        # self.lines.sort(key = lambda l: l.start.y)
        # key = self.lines[0].start_key if self.lines[0].start.y < self.lines[0].end.y else self.lines[0].end_key
        # key_type = 'start' if self.lines[0].start.y < self.lines[0].end.y else 'end'
        # used_keys = []

        # while key:
        #     if key in used_keys:
        #         break
        #     values = endpoints[key]
        #     used_keys.append(key)

        #     for line in values:
        #         print line.values()[0]
        #         if line.keys()[0] != key_type:
        #             if key_type == "start":
        #                 points.extend(line.values()[0].points())
        #             else:
        #                 points.extend(line.values()[0].points()[::-1])
        #         elif line.keys()[0] == key_type:
        #             if key_type == "start":
        #                 key = line.values()[0].end_key
        #             else :
        #                 key = line.values()[0].start_key
        #             print key

        path = 0
        for i in range(len(points)-1):
            path += points[i].distance(points[i+1])
            points[i+1].path = path
            print points[i+1].y, points[i+1].path
        return points
    

    def get_platform(self):
        entities_on = self.entities_on
        points = self.points
        platform_points = []
        
        for entity in entities_on:
            if entity.dxftype == "INSERT":
                if entity.name == "platform_right":
                    pf_insert_point = Point(entity.insert[0], entity.insert[1])
                    points.sort(key = lambda p: pf_insert_point.distance(p))
                    points[0].platform = True
                    platform_points.append(points[0])
        
        for point in points:
            speed_list = [self.MaxSpeed]
            for platform_point in platform_points:
                distance = platform_point.path - point.path 
                if distance < 0 :
                    continue
                speed_list.append(math.sqrt(25.4*distance))
            point.stip_sight_speed = min(speed_list)

    @property
    def entities_on(self):
        def find_layer_by_name(name):
            for layer in self.dxf.layers:
                if layer.name == name:
                    return layer
        return [entity for entity in self.dxf.entities if find_layer_by_name(entity.layer).on ]
    
    # def get_arc(self):
    #     arcs = []
    #     entities_on = self.entities_on

    #     for entity in entities_on:
    #         if entity.dxftype == 'ARC' :
    #             center = Point(entity.center[0], entity.center[1])
    #             arcs.append(Arc(center, entity.radius, entity.start_angle, entity.end_angle))
    #     for arc in arcs:
    #         arc.points() 
    #     return arcs
    def get_line(self):
        lines = []
        entities_on = self.entities_on

        for entity in entities_on:
            if entity.dxftype == 'LINE' :
                start = Point(entity.start[0], entity.start[1])
                end = Point(entity.end[0], entity.end[1])
                line = Line(start, end)
                lines.append(line)
            elif entity.dxftype == 'POLYLINE' :
                pl_points = entity.points
                for i in range(len(pl_points) - 1 ):
                    start = Point(pl_points[i][0], pl_points[i][1])
                    end = Point(pl_points[i+1][0], pl_points[i+1][1])
                    line = Line(start, end)
                    lines.append(line)
            elif entity.dxftype == 'LWPOLYLINE' :
                pl_points = entity.points
                for i in range(len(pl_points) - 1 ):
                    start = Point(pl_points[i][0], pl_points[i][1])
                    end = Point(pl_points[i+1][0], pl_points[i+1][1])
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
        
        for p in self.points:
            p_coor = _convert(center,size,p)
            xy = [int(p_coor[0])-1, int(p_coor[1])-1, int(p_coor[0])+1, int(p_coor[1])+1] 
            # print p_coor, size, p.x, p.y
            draw.arc(xy,0,360,"red")
        
        im.save("test.jpg")
    

    def html(self):
        input_html = open("hc.html")
        s = input_html.read()
        input_html.close()
        
        categories = []
        series = []
        max_speed = {"name": 'max_speed', "data" : []}
        stop_sight_distance = {"name": 'stop_sight_distance', "data" : []}
        
        self.points.sort(key = lambda p: p.y)        
        for p in self.points:
            categories.append(p.path)
            max_speed["data"].append(self.MaxSpeed)
            stop_sight_distance["data"].append(p.stip_sight_speed)

        series.extend([stop_sight_distance, max_speed])
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

    s = Speed("test.dxf")

