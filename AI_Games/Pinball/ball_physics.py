# classes and movement for pinball
# computations only, no gui elements
import numpy as np
from scene import Vector2, Rect
import matplotlib.colors as mcolors
import math
import ui
import base_path
from Utilities.dotdict import DotDict
LEFT = 1
RIGHT = -1

def get_bounding_box(coords):
    """ Computes x, y, w, h from a numpy array of  coordinates.
    """
    min_xy = np.min(coords, axis=0)
    max_xy = np.max(coords, axis=0)
    # Compute width and height
    wh = max_xy - min_xy
    return Rect(*min_xy, *wh)


class Wall:

    def __init__(self, name, centroid, coordinates, inside_wall=True):
        self.name = name
        self.centroid = Vector2(*centroid)
        self.coordinates = coordinates
        self.node = None
        self.inside_wall = inside_wall
        self.bbox = get_bounding_box(self.coordinates)
        self.pos = self.bbox.center()
        self.bounce = 0.7

    def draw_(self):
        # Draw Wall
        coords = np.array([1, -1]) * self.coordinates
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        self.path = path
        return path
        


class Switch:

    def __init__(self, name, centroid, coordinates, action, score):
        self.name = name
        self.centroid = Vector2(*centroid)
        self.coordinates = coordinates
        self.score = score
        self.action = action
        self.node = None
        self.bbox = get_bounding_box(self.coordinates)
        self.pos = self.bbox.center()
        self.bounce = 0
        self.logged = False

    def draw_(self):
        coords = np.array([1, -1]) * (self.coordinates - self.pos)
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        self.path = path
        return path


class Flipper:

    def __init__(self, name, centroid, pivot,
                 length, coordinates,
                 min_angle=-20, max_angle=30):
        # pivot is a Vector2 . pivot.x is negative for left flipper, positive for right
        # TODO, lose side and just use pivot offset
        # lose all the inversions
        self.name = name
        self.pivot_offset = pivot # scalr x1 along x along flipper x axis
        
        self.length = length
        self.inside_wall = True
        self.centroid = Vector2(*centroid)
        # world coordinates
        self.pivot = np.array(self.centroid + self.pivot_offset) 
        self.bounce = 1.2
        
        self.is_active = False
        self.angular_vel = 0
        self.coordinates = coordinates
        
        self.node = None
        self.bbox = get_bounding_box(self.coordinates)
        self.pos = self.bbox.center()
        self.original_coordinates = np.copy(coordinates)  # ADD THIS
        self.original_center = np.array(centroid)  # ADD THIS
        
        # pivot is an offset from centroid along the x-axis of the unrotated
        # flipper.  Convert to an absolute world-space position so the rest of
        # the code can treat self.pivot as a plain (x, y) coordinate.
        centroid_arr = np.array(centroid, dtype=float)
        pivot_offset = pivot  # lies on x-axis
        #self.pivot = centroid_arr + pivot_offset              # world-space pivot

        self.length = length
        # colour of flipper
        colordict = mcolors.CSS4_COLORS  # a curated list of colors
        colour_name = name.split(' ')[1]
        first_colour = colour_name.split('/')[0]
        self.color = 'red' #colordict[first_colour]
        
        # Initial angle: direction from centroid to world-space pivot
        dx, dy = self.pivot - self.original_center
        self.initial_angle = 0 #-math.degrees(math.atan2(dy, dx))
        self.rotation = 0
        # Angle limits are always expressed as offsets from initial_angle.
        # side flips the direction of travel so left and right behave the same.
        self.side = 2 * (pivot.x < 0) - 1 # +/- 1
        self.min_angle = self.initial_angle + min_angle * self.side
        self.max_angle = self.initial_angle + max_angle * self.side
        self.angle = self.min_angle
        # print(f'{name=} {self.initial_angle=:.1f} {self.min_angle=:.1f} {self.max_angle=:.1f}')
        
    def draw_(self):
        coords = np.array([1, -1]) * (self.coordinates - self.pos)
        path = ui.Path()
        path.line_width = 3
        path.move_to(*coords[0])
        [path.line_to(*p) for p in coords[1:]]
        path.close()
        self.path = path
        return path
        
    def rotate_object_(self,theta):
        """
        Rotate an object around a pivot point.
        
        Parameters:
        -----------
        x0, y0     : float - centre of object (world coords)
        x1         : float - pivot x offset relative to (x0, y0); pivot y is always 0
        theta      : float - rotation angle in radians (counter-clockwise)
        perimeter  : np.ndarray of shape (N, 2) - perimeter points relative to (x0, y0)
        
        Returns:
        --------
        new_centre : np.ndarray [new_x0, new_y0] in world coords
        new_perim  : np.ndarray (N, 2) relative to new centre, in world coords
        """
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        R = np.array([[cos_t, -sin_t],
                      [ sin_t,  cos_t]])
        
        x1 = self.pivot_offset[0]
        x0, y0 = self.original_center
        pivot_world = np.array([x0 + x1, y0])

        # Centre relative to pivot (pivot is at (-x1, 0) relative to centre)
        centre_rel_pivot = np.array([x1, 0.0])
        new_centre_rel_pivot = R @ centre_rel_pivot
        new_centre = pivot_world + new_centre_rel_pivot   # world coords
    
        # Each perimeter point in world coords = (x0, y0) + point_rel_centre
        # Relative to pivot: point_rel_pivot = centre_rel_pivot + point_rel_centre
        perim_rel_pivot = centre_rel_pivot + self.original_coordinates          # (N, 2)
        new_perim_world = (R @ perim_rel_pivot.T).T + pivot_world  # (N, 2) world coords
    
        # Express perimeter relative to new centre
        new_perim_rel_centre = new_perim_world - new_centre
    
        return new_centre, new_perim_world 
    

    def rotate_object(self, theta):
        """
        Rotates an object around a pivot offset (x1, 0) relative to its center.
        Returns results relative to the original center (0,0).
        """
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        R = np.array([[cos_t, -sin_t],
                      [sin_t,  cos_t]])
        
        # Pivot location relative to current center
        x1 = self.pivot_offset[0]
        pivot = np.array([x1, 0.0])
    
        # 1. Calculate the new center position relative to the pivot
        # The center is at -pivot relative to the pivot point
        center_rel_pivot = -pivot
        new_center_rel_pivot = R @ center_rel_pivot
        
        # 2. Convert new center back to coordinates relative to original center
        # New Center = Pivot + (Rotated vector from pivot to center)
        new_center = pivot + new_center_rel_pivot
    
        # 3. Rotate perimeter points relative to the pivot
        # First, move perim to be pivot-relative, rotate, then move back
        perim_rel_pivot = self.original_coordinates - pivot
        new_perim_rel_pivot = (R @ perim_rel_pivot.T).T
        
        # Final perim relative to the original origin (0,0)
        new_perim_relative = new_perim_rel_pivot + pivot
    
        return new_center, new_perim_relative
       
    def update(self):
        #  allow for pivot relative to centre of unrotated flipper
        prev_angle = self.angle
        if self.is_active:
            self.angle = min(self.angle + 25, self.max_angle)
        else:
            self.angle = max(self.angle - 12, self.min_angle)
        self.angular_vel = self.angle - prev_angle

        # always update, even though it takes time (<100us)
        self.node.rotation = np.radians(self.angle)
        new_centre, new_perim = self.rotate_object(np.radians(self.angle))        
        self.coordinates = new_perim
 
 
    def rotation_matrix_(self, angle_rad: float) -> np.ndarray:
        c, s = np.cos(angle_rad), np.sin(angle_rad)
        return np.array([[c, -s], [s,  c]])

    def rotate_point_(self, point: np.ndarray, centre: np.ndarray, angle_rad: float) -> np.ndarray:
        """Rotate `point` around `centre` by `angle_rad`."""
        R = self.rotation_matrix(angle_rad)
        return centre + R @ (point - centre)
    
    def pivot_correction_translation_(self, pivot: np.ndarray, centre: np.ndarray,
                                     angle_rad: float) -> np.ndarray:
        """
        Returns the translation vector T such that, after rotating all flipper
        points around `centre` by `angle_rad`, adding T keeps `pivot` stationary.
    
        Derivation
        ----------
        After rotation the pivot lands at:
            pivot' = centre + R @ (pivot - centre)
    
        We need every point shifted by T = pivot - pivot',
        which cancels the displacement of the pivot exactly.
        """
        pivot_rotated = self.rotate_point(pivot, centre, angle_rad)
        return pivot - pivot_rotated
    
    def transform_perimeter_(self,
                            perimeter: np.ndarray,        # (N, 2) array of points
                            centre: np.ndarray,           # rotation centre
                            pivot: np.ndarray,            # stationary pivot point
                            angle_rad: float
                            ) -> tuple[np.ndarray, np.ndarray]:
        """
        Rotate all perimeter points around `centre`, then translate so `pivot`
        stays fixed.
    
        Returns
        -------
        transformed : (N, 2)  final positions of all perimeter points
        T           : (2,)    the single translation vector applied to every point
        """
        R = self.rotation_matrix(angle_rad)
        # Step 1 – rotate every point around the centre
        rotated = (centre + (R @ (perimeter - centre).T).T)
        # Step 2 – compute & apply pivot-correction translation
        T = self.pivot_correction_translation(pivot, centre, angle_rad)
        transformed = rotated + T
        return transformed, T
                             
    def get_endpoints_(self):
        rad = math.radians(self.angle * self.side)
        # For the right flipper, we flip the X direction
        tip_x = self.pivot.x + math.cos(rad) * self.length * self.side
        tip_y = self.pivot.y + math.sin(rad) * self.length * self.side
        return self.pivot, Vector2(tip_x, tip_y)       

    def compute_anchor_point(self):
        # set anchor point of spritenode to pivot       
        x1 = self.pivot_offset.x  # Your offset in pixels
        w = self.node.bbox.width       
        # Calculate the normalized anchor point
        # (0.5, 0.5) is the default center
        new_anchor_x = 0.5 + (x1 / w)        
        self.node.anchor_point = (new_anchor_x, 0.5)        
        # Now, moving the sprite back to center 
        #  changing the anchor shifts its visual position
        self.node.position = Vector2(self.centroid.x + x1, self.centroid.y)

    
class Bumper:

    def __init__(self, name, centroid, radius, score, bounce):
        self.name = name
        self.pos = np.array(centroid)
        self.radius = radius
        self.score = score
        self.bounces = True
        self.bounce = bounce
        self.node = None
        self.coordinates = self.circle_points()

    def draw_(self):
        # Draw Bumper
        color = (1, 0.2, 0.5) if self.score % 100 < 50 else (0.2, 1, 0.5)
        ui.set_color(color)
        path = ui.Path.oval(*(self.pos - self.radius),
                            self.radius * 2, self.radius * 2)
        path.line_width = 3
        path.fill()
        self.path = path
        return path

    def circle_points(self, n=90):
       angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
       x = self.pos[0] + self.radius * np.cos(angles)
       y = self.pos[1] + self.radius * np.sin(angles)
       return np.column_stack((x, y))


class Ball:

    def __init__(self, pos=(500, 900), parent=None, radius=12):
        self.pos = np.array(pos)
        self.vel = np.array([0, 12])
        self.radius = radius
        self.node = None
        self.start_pos = pos
        self.plunger_channel = None
        self.parent = parent
        
    def update(self):
       self.node.position = self.pos
       
    def place_start(self):
        # y_vel = random.randint(21, 35)
        # self.vel = np.array([0, y_vel])
        plunger = self.parent.plunger_rect  # a Rect
        ratio = 0.33
        x = plunger.x + plunger.w / 2
        y = plunger.y + ratio * plunger.h + self.radius
        self.start_pos = np.array([x, y])
        # Temporary overrides for testing
        # self.start_pos = np.array([600, 900])
        self.vel = np.array([0.0, 0.1])
        
    def draw_(self):
        # Draw Ball
        path = ui.Path.oval(*(self.pos - self.radius),
                            self.radius * 2, self.radius * 2)
        path.line_width = 3
        self.path = path
        return path

    def circle_points(self, n=7, arc=np.pi/2):
        # provide an arc of points around the direction vector
        # Calculate the magnitude (speed)
        magnitude = np.linalg.norm(self.vel)
        
        # Handle the case where the ball isn't moving
        if magnitude == 0:
            base_angle = 0.0
        else:
            # Get the angle of the velocity vector
            base_angle = np.arctan2(self.vel[1], self.vel[0])
        
        # Generate angles centered around the direction vector
        angles = np.linspace(base_angle - arc / 2, base_angle + arc / 2, n)
        x = self.pos[0] + self.radius * np.cos(angles)
        y = self.pos[1] + self.radius * np.sin(angles)
        return np.column_stack((x, y))

    def touch_point(self):
        # Calculate the magnitude (speed)
        magnitude = np.linalg.norm(self.vel)
        
        # Handle the case where the ball isn't moving
        if magnitude == 0:
            point = self.pos
        else:
            # Normalize and scale by radius
            point = self.pos + self.radius * self.vel / magnitude
        return point
        
    def get_plunger_channel(self, coords, x_tolerance=3):
        """ Attempt to identify plunger channel
        coords: Numpy array of [x, y] points of the table outline.
        relative to centre of outline
        x_tolerance: Max pixels x can drift while still being 'vertical'.
        """
        # 1. Isolate the right-side points
        x_outer = np.max(coords[:, 0])
        right_points = coords[coords[:, 0] > (x_outer - x_tolerance)]
        
        # 2. Sort by Y descending (bottom to top)
        # Note: In most image systems, 'bottom' is the HIGHEST Y value.
        sorted_pts = right_points[right_points[:, 1].argsort()[::-1]]
        # 2. Calculate horizontal differences between consecutive points
        if len(sorted_pts) > 1:
            x_diffs = np.diff(sorted_pts[:, 0])  # Check difference in X coordinates
            # Get indices where points are vertically aligned within tolerance
            # We add 1 to include the 'neighbor' point that matched the criteria
            match_indices = np.where(np.abs(x_diffs) < x_tolerance)[0]
            if match_indices.size > 0:
                # Combine the indices to get all points involved in the matches
                all_indices = np.unique(np.concatenate([match_indices, match_indices + 1]))
                y_subset = sorted_pts[all_indices]
                y_min = np.min(y_subset[:, 1])
                y_max = np.max(y_subset[:, 1])
            else:
               # Handle case where no points match tolerance
               y_min, y_max = None, None
        else:
            # Handle case with 0 or 1 point
            y_min, y_max = None, None
                            
        # 1. Define the expected lane width (approximate)
        # Most plunger lanes are very narrow.
        expected_width_range = (self.radius * 2, self.radius * 6)  # pixels, adjust based on image scale
        
        # 2. Search for points that fall within the same Y-range
        # but are slightly to the left of our outer wall.
        inner_wall_candidates = coords[
               (coords[:, 1] >= y_min)
             & (coords[:, 1] <= y_max)
             & (coords[:, 0] > x_outer - expected_width_range[1])
             & (coords[:, 0] < x_outer - 10)  # At least 10px to the left
        ]
        # no inner wall found, use default
        if len(inner_wall_candidates) == 0:
            x_inner = x_outer - expected_width_range[1]
        else:
            # 3. Find the most frequent X-coordinate in this subset (the inner wall)
            values, counts = np.unique(inner_wall_candidates[:, 0], return_counts=True)
            max_index = np.argmax(counts)
            # Return the value at that index
            x_inner = values[max_index]
        
        results = DotDict({
            "x_range": (x_inner, x_outer),
            "x_min": x_inner,
            "y_min": y_min,
            "height": (y_max - y_min),
            "width": x_outer - x_inner,
            "rect": Rect(x_inner, y_min, x_outer - x_inner, y_max - y_min)
        })
        #need                
        self.plunger_channel = results.rect
        return results

                
class Physics():
    def __init__(self, ball, walls, flippers, bumpers, switches, parent):
       self.score = 0
       self.timer = .02
       self.gravity = np.array([0, -0.1])
       # self.image = pinball_image
       self.ball = ball
       self.walls = walls
       self.flippers = flippers
       self.bumpers = bumpers
       self.switches = switches
       self.parent = parent
       self.size = parent.size
       self.y_start = None
       self.plunger_rect = Rect(0, 0, 1, 1)
       self.ball_ready = False
        
    def update(self, dt):
        
        self.timer -= dt
        if self.timer <= 0:
            self.timer = .02

            self.ball.vel = self.ball.vel + self.gravity
            self.ball.pos = self.ball.pos + self.ball.vel
            self.ball.update()
            # 1. Reset if out of bounds
            min_y = [wall.bbox.translate(*self.parent.origin) for wall in self.walls if not wall.inside_wall][0][1] + 10
            if self.ball.touch_point()[1] < min_y:
                self.emit_ball()
            # 2. reset if in pluger going down
            p = Vector2(*self.ball.touch_point())
            in_box = self.plunger_rect.contains_point(p)
            if in_box and (self.ball.vel[1] < 0):
                self.emit_ball()
                                  
            for flipper in self.flippers:
                flipper.update()
            
            for flipper in self.flippers:
                self.collide_flipper(flipper)
                    
            for wall in self.walls:
                self.collide_wall(wall)
 
            for bumper in self.bumpers:
                self.collide_bumper(bumper)
                        
            for switch in self.switches:
                self.collide_switch(switch)
                                
            self.score_node.text = f'SCORE: {self.score}'
                     
    def hit_test(self, path, point, inside=True):
        """
        Determines if a point is inside a polygon path.
        
        Args:
            path (np.ndarray): Array of shape (N, 2) representing (x, y) vertices.
            point (np.ndarray): Array of shape (2,) representing the (x, y) point.
            
        Returns:
            bool: True if the point is inside the path.
        """
        x, y = point
        # Ensure the path is closed by connecting the last point to the first
        # This creates the edges: (p0, p1), (p1, p2) ... (pN, p0)
        v1 = path
        v2 = np.roll(path, -1, axis=0)
        dy = v2[:, 1] - v1[:, 1]
        # Avoid division by zero; horizontal edges are excluded by the straddle check anyway
        safe_dy = np.where(dy == 0, 1, dy)
        
        straddle = (v1[:, 1] > y) != (v2[:, 1] > y)
        intersect = x < (v2[:, 0] - v1[:, 0]) * (y - v1[:, 1]) / safe_dy + v1[:, 0]
        # Check if the point's Y-coordinate is between the Y-coordinates of the edge vertices
        # and if the point is to the left of the edge's horizontal intersection
        mask = straddle & intersect
        # If the number of intersections is odd, the point is inside
        return np.sum(mask) % 2 == int(inside)

    def get_closest_vectors(self, path, point):
        # all vectors are numpy arrays
        # 1. Clean path (remove consecutive duplicates)
        mask = np.any(np.diff(path, axis=0, append=path[:1]), axis=1)
        clean_path = path[mask]
        
        # 2. Winding order for outward normal
        x, y = clean_path[:, 0], clean_path[:, 1]
        area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
        is_ccw = area > 0
    
        v1 = clean_path
        v2 = np.roll(clean_path, -1, axis=0)
        
        # Segment vectors and squared lengths
        segments = v2 - v1
        seg_sq_lens = np.sum(segments**2, axis=1)
        
        # 3. Find projection factor 't' for each segment
        # t is the progress along the segment from 0.0 to 1.0
        p_minus_v1 = point - v1
        dot_products = np.sum(p_minus_v1 * segments, axis=1)
        
        # Avoid division by zero for any remaining degenerate segments
        t = np.zeros_like(dot_products)
        nonzero = seg_sq_lens > 1e-12
        t[nonzero] = dot_products[nonzero] / seg_sq_lens[nonzero]
        t = np.clip(t, 0, 1)  # Keep projection within the segment bounds
        
        # 4. Calculate closest point on each segment
        closest_points = v1 + t[:, np.newaxis] * segments
        
        # 5. Find the segment with the minimum distance
        distances_sq = np.sum((point - closest_points)**2, axis=1)
        best_idx = np.argmin(distances_sq)
        
        actual_closest_point = closest_points[best_idx]
        
        # 6. Derive Tangent and Outward Normal
        seg_vec = segments[best_idx]
        seg_len = np.sqrt(seg_sq_lens[best_idx])
        
        tangent = seg_vec / seg_len
        tx, ty = tangent
        
        # CCW: Outward is (ty, -tx) | CW: Outward is (-ty, tx)
        normal = np.array([ty, -tx]) if is_ccw else np.array([-ty, tx])
            
        return actual_closest_point, tangent, normal
        
    def deflect_ball(self, point, object, closest, normal):
        """ Deflect a ball based on its location, object type,
            closest object point and normal vector """
                                    
        # Ensure normal points away from wall toward ball center
        to_ball = point - closest
        vector = np.dot(to_ball, normal)
        # print('normal', np.degrees(np.arctan2(normal[1], normal[0])))
        if vector < 0:
            normal = -normal  # cleaner negation
        # print('normal', np.degrees(np.arctan2(normal[1], normal[0])))
        # print('ball velocity', np.degrees(np.arctan2(self.ball.vel[1], self.ball.vel[0])))
        # Recompute dist as the actual penetration depth to be safe
        dist = self.ball.radius - np.linalg.norm(to_ball)  # penetration amount
        
        if dist > 0:
            # Push ball out along normal by exact penetration depth
            self.ball.pos = self.ball.pos - normal * dist
        
        # Reflect velocity along normal, apply restitution
        vel_along_normal = np.dot(self.ball.vel, normal)
        if vel_along_normal > 0:  # only reflect if moving INTO the wall
        
            self.ball.vel = self.ball.vel - (1 + object.bounce) * vel_along_normal * normal
    
        # Add flipper kick
        if isinstance(object, Flipper):
          # print('hit flipper')
          f_vel = object.angular_vel
          if f_vel > 0:
              self.ball.vel = self.ball.vel + normal * f_vel * object.bounce
                                                  
    def collide_wall(self, wall):
        """ detect wall crossing and deflect """
        coords = wall.coordinates + wall.centroid
        for point in self.ball.circle_points():
            if self.hit_test(coords, point, inside=wall.inside_wall):
                closest, tangent, normal = self.get_closest_vectors(coords, point)
                self.deflect_ball(point, wall, closest, normal)
                return True
        return False
    
    def collide_bumper(self, bumper):
        """ detect bumper hit, deflect and score """
        coords = bumper.coordinates
        for point in self.ball.circle_points():
            if self.hit_test(coords, point, inside=True):
                closest, tangent, normal = self.get_closest_vectors(coords, point)
                
                self.deflect_ball(point, bumper, closest, normal)
                self.score += bumper.score
                break
                
    def collide_flipper(self, flipper):
        """Detect flipper collision using distance to line segment."""
        coords = flipper.coordinates + flipper.centroid
        
        # Find the two endpoints of the flipper (the longest diagonal)
        # Use the pivot and the tip (furthest point from pivot)
        # self.pivot is now a plain (x, y) world-space numpy array
        pivot = flipper.pivot          # already np.ndarray after __init__
        distances_from_pivot = np.linalg.norm(coords - pivot, axis=1)
        tip = coords[np.argmax(distances_from_pivot)]
        
        # Find closest point on the pivot->tip line segment to ball center
        segment = tip - pivot
        seg_len_sq = np.dot(segment, segment)
        
        if seg_len_sq < 1e-12:
            return  # Degenerate flipper
        
        # Project ball center onto segment, clamp to [0,1]
        t = np.dot(self.ball.pos - pivot, segment) / seg_len_sq
        t = np.clip(t, 0.0, 1.0)
        closest = pivot + t * segment
        
        # Vector and distance from closest point to ball center
        to_ball = self.ball.pos - closest
        dist = np.linalg.norm(to_ball)
        
        # Flipper half-thickness (adjust to match your visual flipper width)
        flipper_thickness = 8
        
        if dist < self.ball.radius + flipper_thickness:
            # Normal points from flipper surface toward ball
            if dist > 1e-9:
                normal = to_ball / dist
            else:
                # Ball exactly on segment - use perpendicular to segment
                seg_norm = segment / np.sqrt(seg_len_sq)
                normal = np.array([-seg_norm[1], seg_norm[0]])
            
            # Push ball out of flipper
            penetration = (self.ball.radius + flipper_thickness) - dist
            self.ball.pos += normal * penetration
            
            # Reflect velocity
            vel_along_normal = np.dot(self.ball.vel, normal)
            if vel_along_normal < 0:  # Moving toward flipper
                self.ball.vel -= (1 + flipper.bounce) * vel_along_normal * normal
            
            # Add angular kick from flipper motion
            if flipper.angular_vel > 0:
                # Scale kick by position along flipper (more kick near tip)
                kick_scale = t  # 0 at pivot, 1 at tip
                self.ball.vel += normal * flipper.angular_vel * flipper.bounce * kick_scale
                                  
    def collide_switch(self, switch):
        # switch does some action and/or scores poiints
        # it does not deflect
        # shoukd only register once until ball is outside
        coords = switch.coordinates + switch.centroid
        for point in self.ball.circle_points():
          if self.hit_test(coords, point):
            if not switch.logged:
               switch.logged = True
               try:
                 switch.action()
               except TypeError as e:
                   print(f'action {switch.action} is missing {e}')
          else:
              switch.logged = False
              
    def emit_ball(self):
        self.ball.place_start()
        self.ball.pos = self.ball.start_pos
        self.ball_ready = True
        #self.paused = True
        self.ball.update()
              
    def touch_start(self, touch):
        # modify to emit ball
        if self.plunger_rect.contains_point(touch.location) and self.ball_ready:
           self.ball.pos = self.plunger_rect.center()
           self.paused = True
           self.y_start = touch.location.y
        elif touch.location.x < self.size.w / 2:
            for flipper in self.flippers:
                if flipper.side == LEFT:            
                    flipper.is_active = True
        else:
            for flipper in self.flippers:
                if flipper.side == RIGHT:            
                    flipper.is_active = True

    def touch_end(self, touch):
        # if emitting ball, set ball velocity relative to y touch length
        plunger = self.plunger_rect
        if plunger.min_x < touch.location.x < plunger.max_x and self.ball_ready:
           if self.y_start:
               touch_length = self.y_start - touch.location.y
               ratio = touch_length / plunger.height
               self.ball.vel = np.array([5, 40 * ratio])
               self.paused = False
               self.ball_ready = False
           
        for flipper in self.flippers:
            flipper.is_active = False
    
        

                 
