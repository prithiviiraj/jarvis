from PIL import Image,ImageDraw
from pathlib import Path
p=Path('src-tauri/icons');p.mkdir(exist_ok=True)
im=Image.new('RGBA',(256,256),(17,17,20,255));d=ImageDraw.Draw(im);d.rounded_rectangle((28,28,228,228),radius=52,fill='#5bc8b2');d.ellipse((69,81,101,119),fill='#212129');d.ellipse((154,81,186,119),fill='#212129');d.arc((79,120,177,193),0,180,fill='#212129',width=12);im.save(p/'icon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
