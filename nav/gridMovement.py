# GridMovement class 
# Handles all grid based navigation for the robot

from .grid import Grid
from . import grassfire as gf 
import queue, time, math

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
	def find_path(self):
		visited = gf.search(self.grid, self.current, self.goal)
		self.path = gf.construct_path(self.grid, visited, self.current)

	# Follows the generated path by subtracting the next location
	# from self.current and using translate_dir() and self.movement
	# to determine the proper movement
	def follow_path(self):
		dist = 12 # Default distance we want to move
		# Loop with index so that we can check the next movement
		# along with curent move
		for index, mov in enumerate(self.path):
			currentResult = (mov[0] - self.current[0], mov[1] - self.current[1])
			currentResult = self.translate_dir(currentResult)
			diagonal = gf.is_diagonal(self.current, mov)
			end_of_path = index == len(self.path) - 1

			# Don't bother checking next move if it doesn't exist
			if (not end_of_path):
				nextMov = self.path[index+1]
				nextResult = (nextMov[0] - mov[0], nextMov[1] - mov[1])
				nextResult = self.translate_dir(nextResult)
				# If next move request is the same as current 
				# increase distance moved
				if (currentResult == nextResult):
					self.face(mov)	
					dist = dist +12
					self.current = mov
					# We want to skip over the rest of the loop
					# We're not ready to push a movement call to queue
					continue

			# if dist > 12 then we have duplicate movements
			# We will accelerate
			if(dist > 12):
				self.accelerate(self.movement[currentResult][0], dist)
			# Otherwise normal movement
			else:
				# if mov is diagonal turn towards it first
				if(diagonal):
					self.face(mov)

				self.move(self.movement[currentResult][0], dist)
				# if mov was diagonal and we're not at end of path
				# turn towards the next mov
				if(diagonal and not end_of_path):
					self.face(self.path[index + 1])

			# reset distance in case there was a stacked call 
			dist = 12
			self.current = mov
		
		# face goal after following path
		self.face(self.goal)

	# def follow_next_step(self):
	# 	dist = 12
	# 	checking_dup = True
	# 	result = None
	# 	is_diagonal = False
	# 	mov = None
	# 	while checking_dup and self.path:
	# 		mov = self.path.pop(0)
	# 		result = (mov[0] - self.current[0], mov[1] - self.current[1])
	# 		if self.path:
	# 			nextMov = self.path[0]
	# 			nextResult = (nextMov[0] - mov[0], nextMov[1] - mov[1])
	# 			if nextResult == result:
	# 				dist = dist + 12
	# 				self.current = mov
	# 			else:
	# 				checking_dup = False
		
	# 	if dist > 12:
	# 		self.face(mov)
	# 		self.accelerate(dist, is_diagonal)
	# 		if is_diagonal and self.path:
	# 			self.face(self.path[0])
	# 	elif is_diagonal:
	# 		self.face(mov)
	# 		result = self.translate_dir(result)
	# 		self.move(self.movement[result][0], dist)
	# 		if self.path:
	# 			self.face(self.path[0])
	# 	else:
	# 		result = self.translate_dir(result)
	# 		self.move(self.movement[result][0], dist)
	# 	self.current = mov
	# 	if not self.path:
	# 		self.face(self.goal)

	def facing_next_step(self):
		mov = self.path[0]
		result = (mov[0] - current[0], mov[1] - current[1])
		return self.translate_dir(result) == (0,1)

	def follow_next_step(self):
		dist = 12
		
		
		if not facing_next_step:
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
				self.accelerate(self.fwd, dist)
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
		if abs(angle) > 25:
			return
		offset = 6
		cam_offset = 2.5
		diag_offset = 4#math.sqrt(288) / 2
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
			
	def map_target(self,target):
		self.grid.add_target(target)

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
	
	def old_grid_turn(self, degrees):
		strafe = self.strr if degrees > 0 else self.strl
		sign = 1 if degrees > 0 else -1
		facing_is_diag = False if self.facing % 90 == 0 or self.facing == 0 else True
		turn_is_diag = False if degrees % 90 == 0 or degrees == 0 else True 
		
		if not facing_is_diag and degrees > 0:
				temp = 90*sign if abs(degrees) > 45 else 45*sign 
				self.move(strafe, 255)
				self.turn(temp)
				if not degrees == 45:
					self.move(strafe, 255)
				self.grid_turn(degrees - temp)
		elif degrees > 0:
				temp = 45 * sign
				self.turn(temp)
				self.move(strafe, 255)
				self.grid_turn(degrees - temp)
				

	def move(self,dir, dist):
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
		byteArr = b'\x00' + dir +bytes([dist])+b'\x00'
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
