# -*- coding: utf-8 -*-
"""

"""
from numpy import array
from matplotlib import pyplot as plt
from PIL import Image
import numpy as np
import harris_corner
import perspective
import ui
    
def find_corners(img_path):
    #img_path = 'chess.png'
    if isinstance(img_path, str):
        img = array(Image.open(img_path).convert('L'))
    elif isinstance(img_path, bytearray):
        img = array(ui.Image.from_data(img_path).convert('L'))
    img = (img - img.min())/(img.max()-img.min())
    C, I_x, I_y, L_1, L_2 = harris_corner.detect(img, k=0.06)
    C = (C - C.min())/(C.max()-C.min())
    
    
    plt.imshow(2*C*(C >= 0.457), cmap='gray', vmin=0, vmax=1)
    
    plt.title('Detected Corners')
    plt.tight_layout()
    plt.show()    
    print(f'{C.shape=}')
    print(C.max(), C.min(), C.mean())
    a = np.argwhere(C<0.4)
    
    return harris_corner.order_points(a)
        
def straighten(img_data):
    img = ui.Image.from_data(img_data)
    image_corners = find_corners(img_data)
    image_corners = [np.flip(image_corners[0]), np.flip(image_corners[3]), np.flip(image_corners[2]), np.flip(image_corners[1])]
    corners = perspective.absolutecorners(img)
    w, h = img.size
    image_corners[0] = [0, 0]
    image_corners[2] = [w, h]
    straightened = perspective.transform(image_corners, corners, img)
    return straightened
    
if __name__ == "__main__":
    img_path = 'Pieceword7.jpg'
    image_corners = find_corners(img_path)
    #[tl=[0,0], bl=[h, 0], br=[h, w], tr=[0, w]]
    #reorder
    image_corners = [np.flip(image_corners[0]), np.flip(image_corners[3]), np.flip(image_corners[2]), np.flip(image_corners[1])]
    img = Image.open(img_path)
    corners = perspective.absolutecorners(img)
    # [(0, 0), (width, 0), (width, height), (0, height)]
    w, h = img.size
    image_corners[0] = [0, 0]
    image_corners[2] = [w, h]
    #image_corners[3] = [0, h]
    
    straightened = perspective.transform(image_corners, corners, img)
    plt.imshow(straightened)
    plt.show()
    print(f'{image_corners=}')
    straightened.save('str_' + img_path, fmt='jpg')
    


