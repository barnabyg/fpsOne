"""Editable T05 furniture, in metres. Run with Blender 4.5.3 --background.

Reuses the apartment's authored-mesh helpers and material slots. No downloads,
textures, add-ons, or copyrighted product designs are required.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_room_a_furniture import (
    FABRIC, METAL, PIPING, RUG, SHADE, WOOD, box, clear, cylinder, export,
)


def desk():
    clear()
    box("Solid oak desktop", (0, 0, .752), (1.8, .60, .038), WOOD, .012)
    for x in (-.81, .81):
        for y in (-.22, .22):
            box("Tapered metal leg", (x, y, .363), (.034, .034, .726), METAL, .005)
    box("Rear stretcher", (0, .22, .65), (1.64, .025, .055), METAL, .004)
    box("Shallow drawer", (.48, -.01, .665), (.55, .51, .13), WOOD, .008)
    box("Drawer pull", (.48, -.279, .68), (.17, .025, .013), METAL, .004)
    # A closed-back monitor and keyboard make the office purpose readable.
    box("Monitor foot", (-.15, .07, .783), (.30, .19, .018), METAL, .008)
    box("Monitor stem", (-.15, .12, .89), (.035, .035, .21), METAL, .004)
    box("Monitor bezel", (-.15, .12, 1.09), (.55, .035, .33), METAL, .008)
    box("Unlit display", (-.15, .099, 1.09), (.523, .003, .298), PIPING, .003)
    box("Keyboard", (-.15, -.13, .787), (.40, .14, .025), METAL, .008)
    for row in range(4):
        for column in range(13):
            box("Key", (-.325 + column * .028, -.175 + row * .026, .804),
                (.023, .020, .009), PIPING, .003)
    box("Mouse", (.14, -.12, .796), (.06, .10, .035), METAL, .016)
    cylinder("Task lamp base", (.66, .12, .784), .095, .025, METAL)
    cylinder("Task lamp stem", (.66, .12, .97), .008, .36, METAL)
    box("Task lamp head", (.61, .10, 1.17), (.23, .14, .035), METAL, .015)
    box("Task lamp diffuser", (.61, .10, 1.15), (.20, .11, .008), SHADE, .005)
    export("SM_WritingDesk")


def chair():
    clear()
    for x in (-.205, .205):
        for y in (-.20, .20):
            box("Chair leg", (x, y, .23), (.03, .03, .46), WOOD, .008)
    box("Seat seam", (0, 0, .445), (.49, .49, .04), PIPING, .019)
    box("Upholstered seat", (0, 0, .48), (.48, .48, .085), RUG, .04)
    for x in (-.205, .205):
        box("Back support", (x, .19, .66), (.028, .028, .40), WOOD, .006)
    back = box("Upholstered back", (0, .21, .77), (.48, .085, .31), RUG, .039)
    back.rotation_euler.x = math.radians(-8)
    export("SM_DeskChair")


def daybed():
    clear()
    for x in (-.97, .97):
        for y in (-.34, .34):
            box("Recessed foot", (x, y, .10), (.055, .055, .20), WOOD, .008)
    box("Upholstered base", (0, 0, .27), (2.20, .88, .26), RUG, .055)
    box("Mattress welt", (0, -.01, .425), (2.09, .815, .017), PIPING, .007)
    box("Linen mattress", (0, -.01, .465), (2.08, .81, .17), FABRIC, .08)
    box("Upholstered back", (0, .375, .62), (2.20, .16, .66), RUG, .058)
    for x in (-1.04, 1.04):
        box("Padded end", (x, 0, .49), (.15, .89, .40), RUG, .062)
    for x, angle in ((-.76, -12), (-.38, 12)):
        pillow = box("Guest pillow", (x, .07, .66), (.45, .23, .32), FABRIC, .092)
        pillow.rotation_euler = (math.radians(18), math.radians(angle), 0)
    # A folded woven throw draped across the foot end, with irregular soft ribs.
    box("Folded throw", (.62, -.06, .57), (.47, .70, .045), RUG, .021)
    box("Hanging throw", (.62, -.425, .40), (.47, .032, .35), RUG, .014)
    for i in range(9):
        box("Throw fold", (.411 + i * .052, -.06, .596), (.023, .67, .016), RUG, .008)
    export("SM_GuestDaybed")


def bookcase():
    clear()
    for x in (-.32, .32):
        box("Side", (x, 0, .97), (.035, .31, 1.94), WOOD, .005)
    box("Inset back", (0, .145, .97), (.64, .016, 1.94), WOOD, .003)
    for z in (.10, .49, .94, 1.39, 1.92):
        box("Shelf", (0, 0, z), (.67, .32, .026), WOOD, .005)
    for shelf, z in enumerate((.515, .965, 1.415)):
        for i in range(6 if shelf != 1 else 3):
            height = .19 + ((i + shelf) % 3) * .022
            x = -.235 + i * .051
            box("Book cover", (x, -.015, z + height / 2), (.042, .18, height),
                (RUG, FABRIC, PIPING)[(i + shelf) % 3], .002)
            box("Page block", (x, -.020, z + height / 2), (.034, .172, height - .008), SHADE, .001)
    box("Guest linen basket", (0, -.015, .275), (.53, .26, .25), RUG, .025)
    box("Folded linen", (0, -.018, .415), (.48, .24, .035), FABRIC, .014)
    export("SM_Bookcase")


if __name__ == "__main__":
    desk()
    chair()
    daybed()
    bookcase()
    print("ROOM_B_AUTHORED_MESHES_CREATED")
