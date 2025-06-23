"""
Okay, this is a much more ambitious request! Using sceneKit via objc_util in Pythonista gives you powerful 3D capabilities, but it also means directly interacting with Apple's Objective-C API, which can be verbose.
Creating a full, interactive Rubik's Cube involves two major challenges:
 * Displaying the 26 Cubies: Instead of one cube, we need to create 26 smaller cubes (cubies) and position them correctly.
 * Implementing Rotations: This is the hardest part. When you rotate a face, 9 cubies need to move together. This requires grouping these cubies, rotating the group, and then updating their absolute positions and orientations. This involves significant 3D transformation logic.
For this example, I will focus on Challenge 1: Displaying a visually accurate, solved Rubik's Cube using 26 individual SCNBox nodes and correctly colored faces. I will keep the overall cube rotation for demonstration purposes, but implementing interactive face rotations is a separate, more advanced task that would involve complex hit-testing (to detect which cubie and face was tapped) and animated SCNAction sequences with matrix transformations.
Key Changes from the Original Code:
 * Sticker Colors: Instead of images, we'll create simple solid color materials for each face.
 * Multiple Cubies: We'll iterate through a 3x3x3 grid to create 26 individual SCNBox nodes (excluding the invisible center).
 * Face Material Assignment: For each cubie, we'll determine which of its 6 faces are "outer" faces (visible) and assign the appropriate Rubik's Cube color to them. Inner faces will be a neutral black/gray.
 * Gaps: We'll make each SCNBox slightly smaller than the unit size to create visible gaps between cubies.
"""
from objc_util import *
import sceneKit as scn
import ui
import math
from scene import get_screen_size
from _scene_types import Color

class RubiksCubeModel:
    """
    Represents the logical state of a Rubik's Cube using a 3D array of colors.
    This model assumes a solved cube initially and can perform logical moves.
    """
    def __init__(self):
        # Define standard colors for each face
        # 'W': White (Up)
        # 'Y': Yellow (Down)
        # 'R': Red (Right)
        # 'O': Orange (Left)
        # 'G': Green (Front)
        # 'B': Blue (Back)

        # Initialize a solved cube.
        # faces['U'][row][col] gives the color of sticker on Up face.
        # The indexing (row, col) is arbitrary but consistent.
        self.faces = {
            'U': [['W', 'W', 'W'], ['W', 'W', 'W'], ['W', 'W', 'W']],  # Up face (White)
            'D': [['Y', 'Y', 'Y'], ['Y', 'Y', 'Y'], ['Y', 'Y', 'Y']],  # Down face (Yellow)
            'R': [['R', 'R', 'R'], ['R', 'R', 'R'], ['R', 'R', 'R']],  # Right face (Red)
            'L': [['O', 'O', 'O'], ['O', 'O', 'O'], ['O', 'O', 'O']],  # Left face (Orange)
            'F': [['G', 'G', 'G'], ['G', 'G', 'G'], ['G', 'G', 'G']],  # Front face (Green)
            'B': [['B', 'B', 'B'], ['B', 'B', 'B'], ['B', 'B', 'B']]   # Back face (Blue)
        }
        
    def print_cube(self, msg=''):
        # A simple way to print the cube (can be improved for better visualization)
        # Up face
        if msg:
            print(msg)
        for row, spc, bspc in zip(self.faces['U'],
                   ["    U-", "L     ", "|     "], 
                   ["        ", "  F      ", " /    "]):
            print(spc + " ".join(row)+bspc)
        # Left, Front, Right, Back faces (middle rows aligned)
        for i in range(3):
            print(" ".join(self.faces['L'][i]) + " " +
                  " ".join(self.faces['F'][i]) + " " +
                  " ".join(self.faces['R'][i]) + " " +
                  " ".join(self.faces['B'][i]))
        # Down face
        for row, spc, bspc in zip(self.faces['D'], 
                   ["      ", "      ", "    D-"],
                   [" |     |", " R     B", "      "]):
            print(spc + " ".join(row) + bspc)
            
    def _rotate_matrix_clockwise(self, matrix):
        """Helper to rotate a 3x3 face matrix clockwise."""
        # Transpose and then reverse each row
        return [[matrix[2][0], matrix[1][0], matrix[0][0]],
                [matrix[2][1], matrix[1][1], matrix[0][1]],
                [matrix[2][2], matrix[1][2], matrix[0][2]]]

    def _rotate_matrix_counter_clockwise(self, matrix):
        """Helper to rotate a 3x3 face matrix counter-clockwise."""
        # Reverse each row and then transpose
        return [[matrix[0][2], matrix[1][2], matrix[2][2]],
                [matrix[0][1], matrix[1][1], matrix[2][1]],
                [matrix[0][0], matrix[1][0], matrix[2][0]]]

    def _get_row(self, face_char, row_idx):
        return self.faces[face_char][row_idx][:]

    def _set_row(self, face_char, row_idx, new_row):
        self.faces[face_char][row_idx] = new_row[:]

    def _get_col(self, face_char, col_idx):
        return [self.faces[face_char][i][col_idx] for i in range(3)]

    def _set_col(self, face_char, col_idx, new_col):
        for i in range(3):
            self.faces[face_char][i][col_idx] = new_col[i]
            
    def _reverse_strip(self, strip):
        return strip[::-1]
        
    def apply_move(self, face_char, direction='clockwise'):
        """
        Applies a logical move to the cube model.
        This updates the self.faces data structure.
        All 6 faces and both clockwise/counter-clockwise are implemented.
        """
        face_char = face_char.upper()
        if face_char not in self.faces:
            print(f"Invalid face character: {face_char}")
            return

        # Rotate the primary face
        if direction == 'clockwise':
            self.faces[face_char] = self._rotate_matrix_clockwise(self.faces[face_char])
        elif direction == 'counter-clockwise':
            self.faces[face_char] = self._rotate_matrix_counter_clockwise(self.faces[face_char])
        else:
            print(f"Invalid direction: {direction}. Use 'clockwise' or 'counter-clockwise'.")
            return

        # --- Handle adjacent face sticker permutations ---

        # F (Front) Face
        if face_char == 'F':
            # Store strips before modification
            temp_U_row2 = self._get_row('U', 2)
            temp_R_col0 = self._get_col('R', 0)
            temp_D_row0 = self._get_row('D', 0)
            temp_L_col2 = self._get_col('L', 2)

            if direction == 'clockwise':
                self._set_col('R', 0, temp_U_row2)
                self._set_row('D', 0, self._reverse_strip(temp_R_col0))
                self._set_col('L', 2, self._reverse_strip(temp_D_row0))
                self._set_row('U', 2, temp_L_col2)
            else: # counter-clockwise
                self._set_col('L', 2, temp_U_row2)
                self._set_row('D', 0, self._reverse_strip(temp_L_col2))
                self._set_col('R', 0, self._reverse_strip(temp_D_row0))
                self._set_row('U', 2, temp_R_col0)

        # B (Back) Face
        elif face_char == 'B':
            temp_U_row0 = self._get_row('U', 0)
            temp_L_col0 = self._get_col('L', 0)
            temp_D_row2 = self._get_row('D', 2)
            temp_R_col2 = self._get_col('R', 2)

            if direction == 'clockwise':
                self._set_col('L', 0, self._reverse_strip(temp_U_row0))
                self._set_row('D', 2, self._reverse_strip(temp_L_col0))
                self._set_col('R', 2, self._reverse_strip(temp_D_row2))
                self._set_row('U', 0, self._reverse_strip(temp_R_col2)) # Reverse is important for B-face context
            else: # counter-clockwise
                self._set_col('R', 2, self._reverse_strip(temp_U_row0))
                self._set_row('D', 2, self._reverse_strip(temp_R_col2))
                self._set_col('L', 0, self._reverse_strip(temp_D_row2))
                self._set_row('U', 0, self._reverse_strip(temp_L_col0))

        # U (Up) Face
        elif face_char == 'U':
            temp_F_row0 = self._get_row('F', 0)
            temp_R_row0 = self._get_row('R', 0)
            temp_B_row0 = self._get_row('B', 0)
            temp_L_row0 = self._get_row('L', 0)

            if direction == 'clockwise':
                self._set_row('R', 0, temp_F_row0)
                self._set_row('B', 0, temp_R_row0)
                self._set_row('L', 0, temp_B_row0)
                self._set_row('F', 0, temp_L_row0)
            else: # counter-clockwise
                self._set_row('L', 0, temp_F_row0)
                self._set_row('B', 0, temp_L_row0)
                self._set_row('R', 0, temp_B_row0)
                self._set_row('F', 0, temp_R_row0)

        # D (Down) Face
        elif face_char == 'D':
            temp_F_row2 = self._get_row('F', 2)
            temp_L_row2 = self._get_row('L', 2)
            temp_B_row2 = self._get_row('B', 2)
            temp_R_row2 = self._get_row('R', 2)

            if direction == 'clockwise':
                self._set_row('L', 2, temp_F_row2)
                self._set_row('B', 2, temp_L_row2)
                self._set_row('R', 2, temp_B_row2)
                self._set_row('F', 2, temp_R_row2)
            else: # counter-clockwise
                self._set_row('R', 2, temp_F_row2)
                self._set_row('B', 2, temp_R_row2)
                self._set_row('L', 2, temp_B_row2)
                self._set_row('F', 2, temp_L_row2)

        # R (Right) Face
        elif face_char == 'R':
            temp_U_col2 = self._get_col('U', 2)
            temp_F_col2 = self._get_col('F', 2)
            temp_D_col2 = self._get_col('D', 2)
            temp_B_col0 = self._get_col('B', 0)

            if direction == 'clockwise':
                self._set_col('B', 0, self._reverse_strip(temp_U_col2))
                self._set_col('D', 2, temp_B_col0)
                self._set_col('F', 2, temp_D_col2)
                self._set_col('U', 2, temp_F_col2)
            else: # counter-clockwise
                self._set_col('F', 2, temp_U_col2)
                self._set_col('D', 2, temp_F_col2)
                self._set_col('B', 0, self._reverse_strip(temp_D_col2))
                self._set_col('U', 2, temp_B_col0)

        # L (Left) Face
        elif face_char == 'L':
            temp_U_col0 = self._get_col('U', 0)
            temp_B_col2 = self._get_col('B', 2)
            temp_D_col0 = self._get_col('D', 0)
            temp_F_col0 = self._get_col('F', 0)

            if direction == 'clockwise':
                self._set_col('F', 0, temp_U_col0)
                self._set_col('D', 0, temp_F_col0)
                self._set_col('B', 2, self._reverse_strip(temp_D_col0))
                self._set_col('U', 0, self._reverse_strip(temp_B_col2))
            else: # counter-clockwise
                self._set_col('B', 2, self._reverse_strip(temp_U_col0))
                self._set_col('D', 0, self._reverse_strip(temp_B_col2))
                self._set_col('F', 0, temp_D_col0)
                self._set_col('U', 0, temp_F_col0)
                


class RubiksCubeScene(scn.Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cube_model = RubiksCubeModel()
        self.cubie_nodes = {} # Store cubie nodes by their (x,y,z) coordinate for easy lookup

        # Define Rubik's Cube Colors (as SCNMaterial objects)
        self.color_map_chars = {
            'W': (1.0, 1.0, 1.0),  # White (Up)
            'Y': (1.0, 1.0, 0.0),  # Yellow (Down)
            'R': (1.0, 0.0, 0.0),  # Red (Right)
            'O': (1.0, 0.5, 0.0),  # Orange (Left)
            'G': (0.0, 0.5, 0.0),  # Green (Front) - Darker green for contrast
            'B': (0.0, 0.0, 1.0),  # Blue (Back)
            'K': (0.15, 0.15, 0.15) # Black/Dark Gray for inner cubie faces
        }

        self.color_materials = {
            name: scn.Material.material() for name in self.color_map_chars
        }
        for name, rgb in self.color_map_chars.items():
            self.color_materials[name].diffuse.contents = tuple(Color(*rgb, 1))
            self.color_materials[name].lightingModelName= scn.sceneKitMaterial.LightingModelPhysicallyBased # Better lighting


    def setup(self, scene_view):
        self.background_color = 'black'
        self.scene_view = scene_view # Keep reference to the view

        self.root_node = self.rootNode # Renamed for consistency

        # Central node to hold all cubies
        self.cube_container_node = scn.Node.node()
        self.root_node.addChildNode(self.cube_container_node)

        self._create_cubies()
        self._setup_camera()
        self._setup_lighting()
        #self._start_initial_animation()        

        self.refresh_cube_display() # Initial display of solved cube

    def _create_cubies(self):
        cubie_size = 0.98
        
        # Loop to create 26 cubies (3x3x3 grid, skipping the very center)
        for x_idx in range(3):
            for y_idx in range(3):
                for z_idx in range(3):
                    if x_idx == 1 and y_idx == 1 and z_idx == 1:
                        continue # Skip the center cubie
                    cubie_geometry = scn.Box(width=cubie_size, height=cubie_size, length=cubie_size,  chamferRadius=0.02 )
                    
                    
                    # Store cubie_materials as a list of placeholders for now
                    cubie_node = scn.Node.nodeWithGeometry(cubie_geometry)
                    cubie_node.position = (
                        (x_idx - 1) * 1.0,
                        (y_idx - 1) * 1.0,
                        (z_idx - 1) * 1.0
                    )
                    
                    self.cube_container_node.addChildNode(cubie_node)
                    # Store cubie_node by its logical (0-2) coordinates
                    self.cubie_nodes[(x_idx, y_idx, z_idx)] = cubie_node

    def _setup_camera(self):
       
        constraint = scn.LookAtConstraint.lookAtConstraintWithTarget(self.cube_container_node)
        constraint.gimbalLockEnabled = True
        
        camera = scn.Camera.camera()
        self.camera_node = scn.Node.node()
        self.camera_node.name = 'main camera'
        self.camera_node.camera = camera
        self.camera_node.position = (-3.0, 3.0, 5.0)
        self.camera_node.constraints = [constraint]
        
        self.root_node.addChildNode(self.camera_node)
        self.scene_view.pointOfView = self.camera_node

    def _setup_lighting(self):
        ambient_light = scn.Light.light() 
        ambient_light.type = scn.LightTypeAmbient
        ambient_light.color = tuple(Color(.8, .8, .8, 1))
        ambient_node = scn.Node.node()
        ambient_node.light = ambient_light
        self.root_node.addChildNode(ambient_node)
        
        directional_light = scn.Light.light() 
        directional_light.type = scn.LightTypeDirectional
        directional_light.color = tuple(Color(0.8, 0.8, 0.8, 1))
        directional_node = scn.Node.node()
        directional_node.light = directional_light
        directional_node.position = (3.0, 3.0, 3.0) 
        directional_node.constraints = [scn.LookAtConstraint.lookAtConstraintWithTarget(self.cube_container_node)]
        self.root_node.addChildNode(directional_node)

    def _start_initial_animation(self):
        y_rotation_action = scn.Action.rotateBy(
            0, math.pi * 2, 0, 15.0
        )
        y_rotation_action = scn.sceneKitAnimation.RepeatActionForever(y_rotation_action)
        self.cube_container_node.runAction(y_rotation_action)
        
        self.cube_container_node.rotation = (1.0, 0.0, 0.0, math.radians(-20))
        #self.cube_container_node.rotateBy(0,0,1, math.radians(10), 0)

    def get_sticker_color(self, x_idx, y_idx, z_idx, face_char):
        """
        Determines the color of a specific sticker based on cube_model state.
        This mapping is crucial and needs to be carefully designed.
        """
        color_char = 'K' # Default for internal faces

        # Front Face (G): z_idx == 2
        if z_idx == 2 and face_char == 'F':
            # F face uses model's F face data. y is row (inverted), x is col.
            return self.cube_model.faces['F'][2-y_idx][x_idx]
        
        # Back Face (B): z_idx == 0
        elif z_idx == 0 and face_char == 'B':
            # B face uses model's B face data. y is row (inverted), x is col (inverted).
            return self.cube_model.faces['B'][2-y_idx][2-x_idx]

        # Up Face (W): y_idx == 2
        elif y_idx == 2 and face_char == 'U':
            # U face uses model's U face data. z is row (inverted), x is col.
            return self.cube_model.faces['U'][2-z_idx][x_idx]
            
        # Down Face (Y): y_idx == 0
        elif y_idx == 0 and face_char == 'D':
            # D face uses model's D face data. z is row, x is col.
            return self.cube_model.faces['D'][z_idx][x_idx]

        # Right Face (R): x_idx == 2
        elif x_idx == 2 and face_char == 'R':
            # R face uses model's R face data. y is row (inverted), z is col (inverted).
            return self.cube_model.faces['R'][2-y_idx][2-z_idx]

        # Left Face (O): x_idx == 0
        elif x_idx == 0 and face_char == 'L':
            # L face uses model's L face data. y is row (inverted), z is col.
            return self.cube_model.faces['L'][2-y_idx][z_idx]

        return color_char # Return black for non-matching faces or internal

    def refresh_cube_display(self):
        """
        Updates the colors of all cubie faces based on the current
        state of self.cube_model.
        """
        for x_idx in range(3):
            for y_idx in range(3):
                for z_idx in range(3):
                    if (x_idx, y_idx, z_idx) not in self.cubie_nodes:
                        continue # Skip the center cubie

                    cubie_node = self.cubie_nodes[(x_idx, y_idx, z_idx)]
                    cubie_geometry = cubie_node.geometry # Access the SCNGeometry

                    # Material indices for SCNBox: [right, left, top, bottom, front, back]
                    new_materials = [self.color_materials['K']] * 6
                    # Apply colors based on the current model state                    
                    #is this correct?
                    #R = 0 ; L = 1; U = 2; D = 3; F = 4; B = 5
                    R = 1 ; L = 3; U = 4; D = 5; F = 0; B = 2
                    if x_idx == 2: new_materials[R] = self.color_materials[self.get_sticker_color(x_idx, y_idx, z_idx, 'R')] # Right
                    if x_idx == 0: new_materials[L] = self.color_materials[self.get_sticker_color(x_idx, y_idx, z_idx, 'L')] # Left
                    if y_idx == 2: new_materials[U] = self.color_materials[self.get_sticker_color(x_idx, y_idx, z_idx, 'U')] # Top
                    if y_idx == 0: new_materials[D] = self.color_materials[self.get_sticker_color(x_idx, y_idx, z_idx, 'D')] # Bottom
                    if z_idx == 2: new_materials[F] = self.color_materials[self.get_sticker_color(x_idx, y_idx, z_idx, 'F')] # Front
                    if z_idx == 0: new_materials[B] = self.color_materials[self.get_sticker_color(x_idx, y_idx, z_idx, 'B')] # Back
                    #[print(material.contents) for material in new_materials]
                    cubie_geometry.setMaterials(new_materials) # Update materials

# --- Main Program Structure ---
@on_main_thread
def main():
    main_view = ui.View()
    w, h = ui.get_screen_size()
    main_view.frame = (0, 0, w, h)
    main_view.name = 'Rubik\'s Cube'

    scene_view = scn.View(main_view.frame)
    scene_view.autoresizingMask = (scn.ViewAutoresizing.FlexibleWidth, scn.ViewAutoresizing.FlexibleHeight)
    scene_view.allowsCameraControl = True
    
    # Create an instance of our custom SceneKit scene
    cube_scene = RubiksCubeScene()
    scene_view.scene = cube_scene
    
    scene_view.addToSuperview(main_view)
    
    # Setup the scene (camera, lights, cubies)
    cube_scene.setup(scene_view)
    
    
    # --- Add buttons to trigger a logical move and refresh display ---
    def rotate_front_button_tapped(sender):
        face = sender.title[7]
        dirn = sender.title[10:12]
        direction = 'clockwise' if dirn == 'CW' else 'counter-clockwise'

        print(f"Performing {face} face {direction} move...")
        cube_scene.cube_model.apply_move(face, direction)
        cube_scene.refresh_cube_display() # Update the visual display
        cube_scene.cube_model.print_cube()
        
    params = {'font': ('<System>', 18),
              'background_color': '#4CAF50',
              'tint_color': 'white',
              'corner_radius':  8,
              'action': rotate_front_button_tapped}
    rotate_buttons = []
    for i, item in enumerate(['F CW', 'B CW', 'U CW', 'D CW','L CW', 'R CW', 'F CCW', 'B CCW',  'U CCW','D CCW', 'L CCW', 'R CCW']):
        rotate_buttons.append(ui.Button(title=f'Rotate {item[0]} ({item[2:]})'))
        xoff = 0 if i>5 else w - 180
        rotate_buttons[i].frame = (10+xoff, 10+50*(i%6), 150, 40)
        for param, val in params.items():
            setattr(rotate_buttons[i], param, val)        
        main_view.add_subview(rotate_buttons[i])        
    
    main_view.present(style='fullscreen', hide_title_bar=False)

if __name__ == '__main__':
    main()
    


"""
How to Run This in Pythonista:
 * Open Pythonista.
 * Create a new file (+ button in the file browser).
 * Paste the code into the new file.
 * Run the script (play button in the top right).
You should see a fully assembled, correctly colored Rubik's Cube slowly rotating. You can use your fingers to drag and change the camera's perspective due to scene_view.allowsCameraControl = True.
Explanation of Key Changes:
 * colors Dictionary and color_materials: Instead of loading emoji images, we define a dictionary of RGB tuples for standard Rubik's Cube colors. These are then converted into SCNMaterial objects, which SceneKit uses for rendering surfaces. I've also set lightingModel = scn.LightingModel.PhysicallyBased for slightly more realistic lighting.
 * cube_container_node: This is a crucial new SCNNode. All 26 individual cubie nodes are added as children to this container. This allows us to apply a single rotation action (y_rotation_action) to the cube_container_node, which then affects all its child cubies, making the entire cube rotate as a single unit.
 * Cubie Creation Loop:
   * for x in range(3): for y in range(3): for z in range(3):: This triple loop iterates through all 27 possible positions in a 3x3x3 grid.
   * if x == 1 and y == 1 and z == 1: continue: This skips the central cubie because it's never visible.
   * cubie_size = 0.98: Each SCNBox is slightly smaller than 1 unit, creating the small black gaps that make the cubies distinct.
   * cubie_materials = [color_materials['K']] * 6: Each cubie starts with all its 6 faces set to the 'K' (black/dark gray) material.
   * Conditional Material Assignment: This is where the magic happens for coloring. Based on the cubie's x, y, or z coordinate (0, 1, or 2), we determine if it's on an outer face of the main cube. If it is, we assign the correct Rubik's Cube color material to that specific face's index in the cubie_materials list.
     * SCNBox material indices are fixed: [right, left, top, bottom, front, back].
     * For example, if x == 2: means the cubie is on the far-right column, so its right face (cubie_materials[0]) gets the 'R' (Red) color.
   * cubie_node.position = ((x - 1) * 1.0, (y - 1) * 1.0, (z - 1) * 1.0): This calculation positions each cubie correctly around the origin (0,0,0). Subtracting 1 centers the 3x3 grid around zero (e.g., x values become -1, 0, 1).
 * Lighting: I've added both SCNLightTypeAmbient (general fill light) and SCNLightTypeDirectional (light from a specific direction) to give the cube better depth and shading, making the colors pop. The directional light is constrained to lookAt the cube, so it always shines on it as the camera moves.
Next Steps for a Full Rubik's Cube:
To make this a fully functional Rubik's Cube simulation, the most significant challenge remaining is implementing face rotation logic:
 * Touch Handling: You'd need to replace scene_view.allowsCameraControl = True with custom touch handling.
   * Detect a touch on the screen.
   * Use scene_view.hitTest(touch_location, options=None) to determine which SCNNode (cubie) was touched and which face of that cubie.
   * Based on the cubie's position and the touched face, identify which face of the Rubik's Cube (U, D, F, B, L, R) the user intends to rotate.
   * Detect the direction of the swipe to determine clockwise or counter-clockwise rotation.
 * Grouping Cubies for Rotation:
   * When a face rotation is initiated, you'd identify the 9 cubie_node objects that belong to that face.
   * These 9 cubies would be temporarily removed from the cube_container_node and added as children to a new, temporary SCNNode (e.g., rotation_pivot_node).
   * The rotation_pivot_node would be positioned at the center of the face being rotated.
 * Animation and Transformations:
   * Apply an SCNAction.rotateBy_aroundAxis_duration_ to the rotation_pivot_node.
   * Crucially: After the rotation action completes, you'd need to:
     * Remove the 9 cubies from the rotation_pivot_node.
     * Reset their position and rotation properties (relative to the rotation_pivot_node) to identity.
     * Add them back to the main cube_container_node at their new absolute positions and new absolute orientations. This is where SCNMatrix4 (and potentially SCNVector4) operations become very important, as you'll need to transform the cubies' positions and orientations from the rotated pivot's coordinate system back to the main cube's system.
This level of detail requires careful handling of 3D vectors and matrices, which is beyond the scope of a single immediate modification but is the path forward for a fully interactive cube.
"""
