# configuration for jumping game
from multigame_config2 import Config


# associate an image name with object type and a list of alternative image names
types = { # level1
           'p1_front': ['Player', {'jump':'p1_jump' ,'walk': ['p1_walk01', 'p1_walk02', 'p1_walk03', 'p1_walk04']}],
           'barnacle': ['EnemyHorizontal', 'barnacle', 'barnacle_bite'], 
           'bee': ['EnemyVertical','bee','bee_fly'], 
           'slimeBlue': ['EnemyStatic', 'slimeBlue', 'slimeBlue_blue'],
           'metalCenter': ['Wall'], 
           'beam': ['PlatformStatic'], 
           'beamBoltsHoles': ['PlatformStatic'],
           'beamHoles': ['PlatformMoving'], 
           'metalPlatformWire': ['PlatformSlippy','metalPlatformWire', 'metalPlatformWireAlt'],
           'metalPlatformWireAlt': ['PlatformSlippy','metalPlatformWireAkt', 'metalPlatformWire'],
           'beamBoltsNarrow': ['PlatformSlippy',],
           'metalLeft': ['PlatformCollapsing', 'metalLeft', 'metalHalfLeft'],
           'laserSwitchBlueOff': ['Key','laserSwitchBlueOn'],
           'laserSwitchGreenOff': ['Key','laserSwitchGreenOn'],
           'doorLock': ['DoorExit', 'doorOpen'],
           'hud_gem_green': ['Prize', 'shield', 5],
           'hud_gem_red': ['Prize', 'shield', 5]
        }
LEVEL_FILE = 'new_game.txt'       
config = Config()

