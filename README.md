So now workflow I assume is that an admin have python and everything 
installed, and runs script on a folder, script recognizes all images 
and creates excel file with results. 
The excel file contains both images and recognized names/damages

Readiness: 

- [x] initial image recognition
- [x] working with multiple resolutions
- [ ] auto ignore duplicated records
- [ ] parse multiple raid pictures
- [ ] create output excell file
- [ ] calculate hit time, corresponding to screenshot time

## Installation

1. Install tesseract

    https://github.com/UB-Mannheim/tesseract/wiki

2. Install python 
    
    https://anaconda.org/

3. Download this repo  
   (if you don't know how to use GitHub, you can download zipped file
   `Code -> Download zip`)
 
4. Open python console in a folder with cloned/unzipped code and do:

    ```
   pip install -m requirments.txt
    ```
5. Run test, to check you nailed and it working

   ```bash
    python test.py
   ```
   You should see in a details how a test image is processed (just press space)    

## Run

Now just help me develop this beast


## Add your resolution

If the beast is not working because your resolution is unknown, you have to edit
dimensions.yaml





