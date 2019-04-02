# GridMovement class 
# Handles all grid based navigation for the robot

from . import grassfire as gf 
import time, math

NORTH = 90
SOUTH = 270
EAST = 0
WEST = 180
HOME = (4,4)

class GridMovement:

	def __init__(self, grid, serial):
		# direction bytes
		self.fwd = b'\xA0'
		self.rev = b'\x0A'
		self.rotl = b'\x00'
		self.rotr = b'\xAA'
		self.strl = b'\x22'
		self.strr = b'\x88'

		# motion bytes
		self.allmotors = b'\x55'
		self.right = b'\x05'
		self.left = b'\x50'
		self.front = b'\x11'
		self.rear = b'\x44'
		self.left45 = b'\x14'
		self.right45 = b'\x41'
	
		self.is_cam_up = True
		self.grid = grid
		self.serial = serial
		self.current = HOME
		self.goal = (7,7) #Hardcoded for now. Should be generated by find_goal()
		self.facing = NORTH
		self.path = []
		self.movement = {
			(0,1): [self.fwd, self.allmotors, 0], (0, -1): [self.rev, self.allmotors, 180],
			(1,0): [self.strr, self.allmotors, -90], (-1, 0): [self.strl, self.allmotors, 90],
			(1,1): [self.fwd, b'\x00', -45], (-1, 1): [self.fwd, b'\x00', 45],
			(1,-1): [self.fwd, b'\x00', -135], (-1,-1): [self.fwd, b'\x00', 135]
			}
		
	def get_obstacles(self):
		return self.grid.get_obstacles()

	# Not yet implemented
	# If we haven't aquired a block yet, set closest block as goal.
	# Otherwise we set mothership as goal.
	def find_goal(self):
		pass

	# Generates shortest path to goal using grassfire algorithim
	"""
	Change Log
		[0.0.1] Benji
			--- Add ability to include goal in path
	"""
	def find_path(self, include_goal=False):
		visited = gf.search(self.grid, self.current, self.goal)
		self.path = gf.construct_path(self.grid, visited, self.current, include_goal)

	def facing_next_step(self):
		mov = self.path[0]
		result = (mov[0] - self.current[0], mov[1] - self.current[1])
		return self.translate_dir(result) == (0,1)

	def follow_next_step(self):
		dist = 12

		diag = False if self.facing % 90 == 0 or self.facing == 0 else True
		
		mov = self.path[0]
		if not self.facing_next_step():
			self.face(mov)
		else:
			checking_dup = True
			while checking_dup and self.path:
				mov = self.path.pop(0)
				result = (mov[0] - self.current[0], mov[1] - self.current[1])
				if self.path:
					nextMov = self.path[0]
					nextResult = (nextMov[0] - mov[0], nextMov[1] - mov[1])
					if nextResult == result:
						dist = dist + 12
						self.current = mov
					else:
						checking_dup = False

			if dist > 12:
				self.accelerate(dist)
			else:
				self.move(self.fwd, dist)
			self.current = mov



	# Face a tile connected to current tile
	def face(self, obj):
		result = (obj[0] - self.current[0], obj[1] - self.current[1])
		result = self.translate_dir(result)
		degrees = self.movement[result][2]
		self.turn(degrees)

	# Should be called anytime facing is updated
	# Keeps facing between 0 and 360 
	def trim_facing(self):
		if self.facing < 0:
			self.facing = self.facing + 360
		elif self.facing >= 360:
			self.facing = self.facing - 360

	# Use facing to translate proper movement
	def translate_dir(self,mov):
		angle = self.facing - self.movement[mov][2]
		is_diagonal = angle is not 0 and angle % 90 is not 0
		angle = math.radians(angle)
		x = math.cos(angle)
		y = math.sin(angle)
		if is_diagonal:
			x = x/abs(x)
			y = y/abs(y)

		x = x*-1

		x = math.ceil(x) if x < 0 else math.floor(x)
		y = math.ceil(y) if y < 0 else math.floor(y)
		return (x,y)


	def map(self,obj, angle, dist):
		if abs(angle) > 30:
			return
		offset = 6
		cam_offset = 2.5
		diag_offset = 0#4#math.sqrt(288) / 2
		angle_rads = math.radians((angle* -1) + self.facing)

		o_length = math.sin(angle_rads) * dist
		a_length = math.cos(angle_rads) * dist

		if self.facing == EAST or self.facing == WEST:
			if -cam_offset<a_length<cam_offset:
				x = 0
			else:
				x =  (a_length+cam_offset)/12 if a_length < 0 else (a_length - offset)/12
			if -offset<o_length<offset:
				y= 0
			else:
				y = (o_length + offset)/12 if o_length < 0 else (o_length - offset)/12
			if x == 0 and y == 0:
				x = 1 if self.facing == EAST else -1 

		elif self.facing == NORTH or self.facing == SOUTH:
			if -offset<a_length<offset:
				x = 0
			else:
				x = (a_length + offset)/12 if a_length < 0 else (a_length - offset)/12
			if -cam_offset<o_length<cam_offset:
				y = 0
			else:
				y = (o_length+cam_offset)/12 if o_length < 0 else (o_length - offset)/12
			if x == 0 and y == 0:
				y = 1 if self.facing == NORTH else -1

		else:
			if dist > 39:
				return
			x = (a_length + diag_offset)/math.sqrt(288) if a_length < 0 else (a_length - diag_offset)/math.sqrt(288)
			y = (o_length + diag_offset)/math.sqrt(288) if o_length < 0 else (o_length - diag_offset)/math.sqrt(288)
			

		x = math.ceil(x) if x > 0 else math.floor(x)
		y = math.ceil(y) if y > 0 else math.floor(y)
		result = (self.current[0] + x, self.current[1] + y)
		print(result)
		if obj == 7:
			self.grid.add_obstacle(result)
		elif obj == 9: 
			self.grid.add_slope(result)
		elif obj == 8:
			self.grid.add_side(result)
			self.grid.last_side_angle = angle
	
			
	def map_target(self,target):
		self.grid.add_target(target)

	# Maps mothership based on provided side and current facing
	def map_mothership(self, side):
		sign = 1 if self.grid.last_side_angle < 0 else -1
		sx, sy = side[0], side[1]

		if self.facing == 90:

			mothership = [(sx,sy), (sx +1 * sign, sy), (sx, sy +1), (sx +1 * sign, sy +1)]
		elif self.facing == 0:
			mothership = [(sx,sy), (sx +1 , sy), (sx, sy -1 * sign), (sx +1, sy -1*sign)]
		elif self.facing == 180:
			mothership = [(sx,sy), (sx -1 , sy), (sx, sy +1 * sign), (sx -1, sy +1*sign)]
		elif self.facing == 270:
			mothership = [(sx,sy), (sx -1 * sign , sy), (sx, sy -1), (sx -1 * sign, sy -1)]
		elif self.facing == 135:
			mothership = [(sx,sy), (sx -1 , sy), (sx, sy +1 ), (sx-1, sy +1)]
		elif self.facing == 235:
			mothership = [(sx,sy), (sx -1 , sy), (sx, sy -1 ), (sx-1, sy -1)]
		elif self.facing == 315:
			mothership = [(sx,sy), (sx +1 , sy), (sx, sy -1 ), (sx+1, sy -1)]
		# facing == 45
		else:
			mothership = [(sx,sy), (sx +1 , sy), (sx, sy +1 ), (sx+1, sy +1)]

		self.grid.mothership = mothership

	# Communicates movement calls to Arduino
	# MOVEMENT FUNCTIONS #

	def turn(self,degrees):
		# Update current orientation 
		self.facing = self.facing + degrees
		self.trim_facing()
		slp_t = 0
		turn_dir = self.rotl
		print("Turning", degrees)
		if(degrees < 0):
			turn_dir = self.rotr

		byteArr = b'\x01' + turn_dir +bytes([abs(degrees)])+b'\x00'
		self.serial.write(byteArr)
		
		if abs(degrees) <= 25:
			slp_t = 1
		elif abs(degrees) <= 45:
			slp_t = 2
		elif abs(degrees) <= 90:
			slp_t = 3
		elif abs(degrees) <= 135:
			slp_t = 4
		else:
			slp_t = 5
		time.sleep(slp_t)
				

	def move(self,dir, dist, is_diagonal=False):
		slp_t = 0
		if dist < 5:
			slp_t = 1
		elif dist < 10:
			slp_t = 2
		elif dist == 255:
			slp_t = 2
		else:
			slp_t = 3
		print("Moving ", dist, " inches")
		byte = b'\x00' if is_diagonal else b'\x01'
		byteArr = b'\x00' + dir +bytes([dist])+byte
		self.serial.write(byteArr)
		time.sleep(slp_t)

	def accelerate(self,dist, is_diagonal=False):
		print("Accelerating ", dist, " inches")
		byte = b'\x00' if is_diagonal else b'\x01'
		byteArr = b'\x02' + self.fwd + bytes([dist]) + byte
		self.serial.write(byteArr)
		
		if dist <= 24:
			slp_t = 3
		elif dist <= 48:
			slp_t = 4
		else:
			slp_t = 5
		time.sleep(slp_t)

	def pickup(self): 
		byteArr = b'\x03'  + b'\x00' + b'\x00' + b'\x00'
		self.serial.write(byteArr)
		time.sleep(1)

	def drop(self): 
		byteArr = b'\x04'  + b'\x00' + b'\x00' + b'\x00'
		self.serial.write(byteArr)
		time.sleep(1)

	def reset_servo(self): 
		byteArr = b'\x05'  + b'\x00' + b'\x00' + b'\x00'
		self.serial.write(byteArr)
		time.sleep(1)

	def cam_up(self): 
		if not self.is_cam_up:
			byteArr = b'\x06'  + b'\x00' + b'\x00' + b'\x00'
			self.serial.write(byteArr)
			self.is_cam_up = True
			time.sleep(.2)

	def cam_down(self): 
		if self.is_cam_up:
			byteArr = b'\x07'  + b'\x00' + b'\x00' + b'\x00'
			self.serial.write(byteArr)
			self.is_cam_up = False
			time.sleep(.2)
