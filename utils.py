import math
from numpy import array

def calculate_angle(point1, point2, invert=-1):
    if point2[0] - point1[0] == 0: # Prevent didivison by zero
        if point2[1] - point1[1] > 0:
            return  90
        else:
            return -90
    else:
        # Add a minus to the y difference as the y coordinates are inverted in pygame
        return math.degrees(math.atan2(invert*(point2[1] - point1[1]), (point2[0] - point1[0])))

def calculate_angle_diff(org_angle, food_angle):
    food_angle %= 360
    angle_difference = org_angle - food_angle
    
    if angle_difference > 180: 
        angle_difference -= 360
    if angle_difference < -180:
        angle_difference += 360
    
    return angle_difference

def calculate_distance(point1, point2):
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1]-point1[1])**2)

def inbox(p, box):
    return all(box[:,0] <= p) and all(p<= box[:,1])

# KdTree for optimizations
class KdTree:
    def __init__(self, P, d=0):
        n = len(P)
        m = n // 2
        P.sort(key = lambda x: x[d])
        self.point = P[m]
        self.d = d
        d = (d + 1) % len(P[0])-1 # -1 because then the last element will not be a dimension (wanted since last ele is info obj)
        self.left = self.right = None
        if m > 0 :
            self.left = KdTree(P[:m], d)
        if n - (m+1) > 0:
            self.right = KdTree(P[m+1:], d)

    def range_search(self, box):
        p = self.point
        if inbox(p[:2], box): # Only first two elements of p (x, y) 3rd is info object
            yield p
        min, max = box[self.d]
        split = p[self.d]
        if self.left is not None and split >= min:
            yield from self.left.range_search(box)
        if self.right is not None and split <= max:
            yield from self.right.range_search(box)