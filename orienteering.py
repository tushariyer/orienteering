# Tushar Iyer
# Intelligent Systems - CSCI 630 | Fall 2017 | Lab 1
from PIL import Image  # A whole lotta imports
import numpy as np
import traceback
import logging
import math
import sys
import re

# Terrain Colours
OPENLAND = (248, 148, 18)       # F89412
ROUGHMEADOW = (255, 192, 0)     # FFC000
EASYFOREST = (255, 255, 255)    # FFFFFF
RUNFOREST = (2, 208, 60)        # 02D03C
WALKFOREST = (2, 136, 40)       # 028828
IMPASSABLEVEG = (5, 73, 24)     # 054918
WATER = (0, 0, 255)             # 0000FF
ROAD = (71, 51, 3)              # 473303
FOOTPATH = (0, 0, 0)            # 000000
OUTOFBOUNDS = (205, 0, 101)     # CD0065

# Heuristics lists
SPEED = []
DIRECTIONS = []

# Movement speeds
LONGITUDE = 10.29
LATITUDE = 7.55

# Controls
CURRENT = []
NEXT = []

# Season
SEASON = ""


# Use this to represent the terrain types
class Terrain(object):
    def __init__(self, colour, speed, name):
        self.colour = colour
        self.speed = speed
        self.name = name


# Dict of terrain info, speeds are given in MPH
terrainColours = {
    OPENLAND: Terrain(OPENLAND, 5.5, 'Open Land'),
    ROUGHMEADOW: Terrain(ROUGHMEADOW, 3.5, 'Rough Meadow'),
    EASYFOREST: Terrain(EASYFOREST, 7.5, 'Easy Movement Forest'),
    RUNFOREST: Terrain(RUNFOREST, 10.0, 'Slow Run Forest'),
    WALKFOREST: Terrain(WALKFOREST, 6.0, 'Walk Forest'),
    IMPASSABLEVEG: Terrain(IMPASSABLEVEG, 1 / 100, 'Impassible Vegetation'),
    WATER: Terrain(WATER, 1/1000, 'Water'),
    ROAD: Terrain(ROAD, 12.5, 'Paved Road'),
    FOOTPATH: Terrain(FOOTPATH, 10.5, 'Footpath'),
    OUTOFBOUNDS: Terrain(OUTOFBOUNDS, 1/100000, 'Out Of Bounds')
    }


# Get the terrain type based on colour
def getTerrainType(rgb):
    return terrainColours.get(rgb)


# Statistics
def heuristicStatistics():
    # Calculate the sum and average speeds
    sumspeed = sum(SPEED)
    avgspeed = int(sumspeed / len(SPEED))
    print "Average walk/run speed to complete the course: " + str(avgspeed) + " MPH."
    print "Max walk/run speed achieved: " + str(max(SPEED)) + " MPH.\n"


# Add the speeds together in a list
def speedHeuristics(curSpeed):
    SPEED.append(curSpeed)


# Class to set the terrain, location and height
class CurrentCoordinates(object):
    def __init__(self, terrain, location, height=0):
        self.terrain = terrain
        self.location = location
        self.height = height

    # Return a printable representation
    def __repr__(self):
        return str(self.location)

    # Set height
    @classmethod
    def setHeight(self, height):
        self.height = height


# Class to represent the terrain as individual pixels with their own elevation
class TerrainMap(object):
    def __init__(self, image):
        pixels = image.convert("RGB").load()
        self.width, self.height = image.size
        self.location = []

        # For the width and height of each pixel
        for x in range(self.width):
            for y in range(self.height):
                self.location.append(CurrentCoordinates(getTerrainType(pixels[x, y]), (x, y)))
                speedHeuristics(getTerrainType(pixels[x, y]).speed)


# Correctly slots the point into the queue Adds the point into the correct position of the priorityQueue
def orderPoints(priorityQueue, points):
    i = 0
    while i < len(priorityQueue) and i != -1:
        if priorityQueue[i][0] == points[0]:
            priorityQueue.pop(i)
        i = i + 1
    i = 0
    while i < len(priorityQueue) and points[1] >= priorityQueue[i][1]:
        i = i + 1
    priorityQueue.insert(i, points)
    return priorityQueue


# Converts a coordinate into an array index
def convertToArrIndex(height, x, y):
    return height * x + y


# Gets the distance between two points
def dist(first, second):
    return math.hypot((first[1] - first[0]), (second[1] - second[0]))


# Find the degree bearing of the next point from the current point
def bearingHelper(first, second):
    return math.atan2(second[1] - second[0], first[1] - first[0])


# Finds the direction you need to go
def findBearing(first, second):
    # Get the radial bearing to the next control from where we are and then convert it to degrees
    deg = bearingHelper(first, second)
    deg = np.rad2deg(deg)

    # Account for if our bearing is represented as a negative number
    if deg < 0:
        deg = 360 - abs(deg)
    d = u'\xb0'.encode('utf8')  # Degree synbol
    deg = int(deg)
    heading = ""

    # Divided the unit circle, this tells us the direction
    if deg == 0:
        heading = "N"
    elif deg > 0 and deg <= 44:
        heading = "NNE"
    elif deg == 45:
        heading = "NE"
    elif deg > 45 and deg <= 89:
        heading = "ENE"
    elif deg == 90:
        heading = "E"
    elif deg > 90 and deg <= 134:
        heading = "ESE"
    elif deg == 135:
        heading = "SE"
    elif deg > 135 and deg <= 189:
        heading = "SSE"
    elif deg == 180:
        heading = "S"
    elif deg > 180 and deg <= 224:
        heading = "SSW"
    elif deg == 225:
        heading = "SW"
    elif deg > 225 and deg <= 269:
        heading = "WSW"
    elif deg == 270:
        heading = "W"
    elif deg > 270 and deg <= 314:
        heading = "WNW"
    elif deg == 315:
        heading = "NW"
    elif deg > 315 and deg <= 359:
        heading = "NNW"
    elif deg == 360:
        heading = "N"
    else:
        heading = ""

    # String out the heading that the next control is in
    direction = str(deg) + str(d) + heading + "."
    return direction


# Gets the time it takes to travel from one terrain pixel to another
def travelTime(terrain, first, second):
    distance = 0

    # Movement
    if first[0] == second[0]:
        distance = LONGITUDE  # Moving left or right
    elif first[1] == second[1]:
        distance = LATITUDE  # Moving up or down
    else:
        distance = math.sqrt((LONGITUDE ** 2) + (LATITUDE ** 2))  # Moving diagonally

    # The two terrains being compared
    terrainOne = terrain.location[convertToArrIndex(terrain.height, first[0], first[1])].terrain
    terrainTwo = terrain.location[convertToArrIndex(terrain.height, second[0], second[1])].terrain

    # The heights of the respective terrains
    heightOne = terrain.location[convertToArrIndex(terrain.height, second[0], second[1])].height
    heightTwo = terrain.location[convertToArrIndex(terrain.height, first[0], first[1])].height

    # Height multiplier
    heightMult = ((heightOne - heightTwo) / 200) + 1

    try:
        # If the time to go from one terrain spot to another is more than one
        time = heightMult * ((distance/2) / terrainOne.speed) + ((distance / 2) / terrainTwo.speed)
    except ZeroDivisionError:
        # We will usually have a set of terrains that are right next to each other
        # Since the travel cost is 0, we need to handle that, otherwise this exception is thrown
        time = 0

    # Please don't actually print the following. It prints a ton.
    DIRECTIONS.append("Going from " + str(first) + " -> " + str(second) + "in " + str(second) + "seconds.")
    return time


# Checks if coordinates are within bounds
def checkBounds(courseMap, x_axis, y_axis):
    return x_axis >= 0 and x_axis < courseMap.width and y_axis >= 0 and y_axis < courseMap.height


# Gets the neighbors of given coordinates
def findNeighbors(courseMap, point):
    # print "Finding Neighbors..."  # Oh god don't print this, there's little else you'll see in the console
    x_axis = point[0]
    y_axis = point[1]
    width = courseMap.width
    height = courseMap.height
    neighbors = {}
    sub_x, sub_y = x_axis - 1, y_axis - 1

    # Check if we're inside the map
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["topLeft"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis, y_axis - 1
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["topMiddle"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis + 1, y_axis - 1
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["topRight"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis - 1, y_axis
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["centerLeft"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis, y_axis
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["centerMiddle"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis + 1, y_axis
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["centerRight"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis - 1, y_axis + 1
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["bottomLeft"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis, y_axis + 1
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["bottomCenter"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)],
    sub_x, sub_y = x_axis + 1, y_axis + 1
    if checkBounds(courseMap, sub_x, sub_y):
        neighbors["bottomRight"] = courseMap.location[convertToArrIndex(height, sub_x, sub_y)]

    # print "Returning Neighbors."
    return neighbors


# Backtracks to build a path of pixels
def backtrackPath(pointMap, goal):
    path = [goal]  # The goal is at the end of the path, so let's add it now

    # While we're not yet at the goal
    while pointMap[goal][0] != goal:
        path.append(pointMap[goal][0])  # Add every new point to the head of the path, so the path is built in reverse
        goal = pointMap[goal][0]
    return path


# Run the A* algorithm
def aStar(courseMap, start, target):
    parents = {}
    priorityQueue = [(start, 0)]

    # While the queue still has points
    while len(priorityQueue):
        # The next-up state is at the head of the queue
        state = priorityQueue.pop(0)

        # If we've reached the end of the path
        if state[0] == target:
            print "Control at " + str(target) + " reached."
            return parents, state[1]

        # All the neighbors are the potential successor states
        neighbors = findNeighbors(courseMap, state[0])

        # Out of all the possible successors
        for loc in neighbors:
            if type(neighbors[loc]) == type((1, 1)):
                loc = neighbors[loc][0].location
            else:
                loc = neighbors[loc].location

            # Move successor from one list to another
            point = (loc, travelTime(courseMap, state[0], loc) + state[1])

            if loc not in parents:
                priorityQueue = orderPoints(priorityQueue, point)
                parents[loc] = state
            if parents[loc][1] > point[1]:
                priorityQueue = orderPoints(priorityQueue, point)
                parents[loc] = state


# Draws the final path over the original terrain image
def drawPath(terrainPNG, output, path, points):  # =[]
    mapDraw = Image.open(terrainPNG)
    for point in path:
        mapDraw.putpixel(point, (255, 0, 0))
    for point in points:
        mapDraw.putpixel(point, (0, 255, 255))
    mapDraw.putpixel(points[0], (16, 47, 100))  # My fav shade of blue #2a77ff
    mapDraw.save(output)


# Finds a path that visits all the control points [Classic method]
def planPath(courseMap, controlLocations):
    # We're referring to the global variables
    global CURRENT
    global NEXT

    totalDistance = 0.0  # We're going to keep adding to this, so we can see how far we've come
    path = []
    time = 0
    unvisited = controlLocations[:]
    controlCount = 0
    init = unvisited.pop()
    CURRENT = init

    # While there are unvisited controls
    while len(unvisited):
        goal = unvisited.pop()  # Goal is to visit the unvisited. Pretty straightforward, right?
        NEXT = goal
        controlCount += 1
        distance = dist(CURRENT, NEXT)
        direction = findBearing(CURRENT, NEXT)
        totalDistance += distance

        # Add to the output
        print "\nNext point is  Control " + str(controlCount) + ": "
        print "Located "+ str(round(distance, 2)) + " m away with the heading " + direction

        # We call A* here
        parents, t = aStar(courseMap, init, goal)

        # More output
        print "Time taken to reach Control " + str(controlCount) + ": " + str(round(t, 2)) + " seconds."
        print "\nTotal Distance so far: " + str(round(totalDistance, 2)) + " m. [" + str(round(distance/1000, 2)) + " km]"

        # Concatenate the path
        time += t
        for p in backtrackPath(parents, goal):
                path.append(p)
        init = goal
    return path, time


# Runs the course on the given terrain and saves the result to output
def doCourse(terrain, course, output, terrainPNG):
    # Read the red/white/brown file and store the coordinates
    coordinates = open(course, 'r')
    courseType = ""  # I modified the files so that the course type was the first line.
    points = []
    i = 0

    # For each Control location
    for line in coordinates:
        if i == 0:
            # Determine if this is the Red, White or Brown course
            courseType = str(line[0:-1])
        else:
            # Regex check for digits [0-9]
            point = re.findall('\d+', line)
            point = (int(point[0]), int(point[1]))
            points.append(point)
        i = i + 1

    # I put this in a try because the program just hangs if you pass in any other text file apart from whats given.
    try:
        print "\nSolving " + courseType + " Course in the " + str(SEASON.title()) + ": "
        path, time = planPath(terrain, points)  # Get the path
        print "Course solved in " + str(round(time, 2)) + " seconds."
        drawPath(terrainPNG, output + '-output.png', path, points)  # Draw it here
        print "\nCourse path saved as " + output + "-output.png\n"
        heuristicStatistics()  # Print stats
    except Exception as e:
        print("File is invalid. Please check your inputs.")
        logging.error(traceback.format_exc())


# Pixelate the courseMap so it becomes a grid of pixels
def pixelateTerrain(terrainpng, elevations):
    # Bring in the image. We're going to turn it into a TerrainMap object so we can overlay the elevations with it.
    png = Image.open(terrainpng)
    terrainMap = TerrainMap(png)
    terrainElevations = open(elevations, 'r')
    y = 0

    # Deal with each elevation value
    for line in terrainElevations:
        # Regex check for non-whitespace characters
        elevations = re.findall("\S+", line)
        for i in range(len(elevations) - 6):
                x = terrainMap.height * (i + 6) + y
                terrainMap.location[x].height = float(elevations[i])
        y = y + 1
    return terrainMap


# Make changes based on season
def seasonalChanges(mult):
    # For every terrain type
    for i in terrainColours:
        # Get the terrain's speed
        curSpeed = getTerrainType(i).speed

        # As long as its not IMPASSABLE or OUTOFBOUNDS or WATER
        if curSpeed > 0.1:
            getTerrainType(i).speed = abs(curSpeed - mult)  # Apply the seasonal multiplier
    print "\nCourse Heuristics modified for seasonal changes."


# Determine the modifier based on season
def seasonalModifier(s):
    # Refer to the global variable
    modifier = 0
    global SEASON
    SEASON = s
    s = s.lower()

    # Preset seasonal modifiers
    if s == "summer":
        modifier = 1  # Default, leave it at one
    elif s == "fall":
        modifier = 1.4  # Paths are gone, make it marginally harder
    elif s == "autumn":
        modifier = 1.4  # Paths are gone, make it marginally harder
    elif s == "winter":
        modifier = 2.2  # It's covered in snow, suffer on your walkthrough
    elif s == "spring":
        modifier = 1.2  # Clearing up, but not yet summer
    else:
        print "Error: Season not specified properly."  # This is if anything apart from the seasons are mentioned
        print "Please run again and specify \'summer\', \'fall\' or \'autumn\', \'winter\', or \'spring\'."
        exit()
    return modifier


# Main method
if __name__ == "__main__":
    # It's under a try because I wanted to prevent the program from hanging if anything was misspelled
    try:
        courseMap = pixelateTerrain(str(sys.argv[1]), str(sys.argv[2]))
        season = str(sys.argv[5])
        mult = seasonalModifier(season)
        seasonalChanges(mult)
        doCourse(courseMap, str(sys.argv[4]), str(sys.argv[3]), str(sys.argv[1]))
        exit()
    except Exception as e:
        # Instructions
        print "To run this and print the results to console:"
        print "Run using this structure: \"python labOneOrienteering.py terrain.png mpp.txt results [courseTextFile]\""
        print "\nTo run this and print to a text file:"
        print "\"python labOneOrienteering.py terrain.png mpp.txt results [courseTextFile] > [course]-output.txt\""
        logging.error(traceback.format_exc())
