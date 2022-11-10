import numpy as np
import matplotlib.pyplot as plt
import skimage
import tifffile
from tqdm.notebook import trange, tqdm
from datetime import date
import dill as pickle
import os as os

def noisy_imshow(img, n_stds=2):
    plt.imshow(img, vmin=img.mean()-n_stds*img.std(), vmax=img.mean()+n_stds*img.std()); plt.colorbar(); plt.show()

# def get_cwd():
#     return Path(os.get_cwd())
    
def read_nd2(fpath):
	with nd2.ND2File("data1/" + fpath + ".nd2") as f:
		return f.asarray()

def read_tiff(fpath):
	print("reading...")
	return tifffile.imread("data1/" + fpath + ".tif")

def save_tiff(fpath, data):
	tifffile.imsave("data1/" + fpath + ".tif", data)


def save_as_fig(fpath, data):
	data = data.copy().astype(float)
	data -= data.min()
	data /= data.max()
	print("saving", data.shape)
	skimage.io.imsave("figs/" + fpath + ".png", img_as_ubyte(data))
    

class Pickleable():
    stem = "pickled/"
    
    def __init__(self, dir_path=None):
        self.stem = dir_path + "/" if dir_path else type(self).stem
        self.name = None
        
    def save(self, name=None):
        if not os.path.exists(self.stem):
            os.mkdir(self.stem)
        if name is None:
            name = date.now().strftime("%d/%m/%Y-%H:%M:%S")
        self.name = name
        fpath = self.stem + name + ".pickle"
        print("saving to", fpath)
        with open(fpath, "wb") as f:
            pickle.dump(self, f)
        return self

    def load(self):
        if self.name is None:
            raise ValueError("Define a name first")
        with open(self.stem + self.name + ".pickle", "rb") as f:
            return pickle.load(f)
    
    @classmethod
    def load_name(cls, name):
        with open(cls.stem + name + ".pickle", "rb") as f:
            return pickle.load(f)
        
        

def get_tiff_info(path):
    with tifffile.TiffFile(path) as tif:
        
        if tif.imagej_metadata["Info"] is None:
            return None
                
        if "channels" in tif.imagej_metadata:
            n_channels = int(tif.imagej_metadata["channels"])
        else:
            n_channels = 1

        info = {
            "n_channels" : n_channels,
            "lens" : None,
            "magnification" : None,
            "NA" : None,
            "um_per_px" : None,
            "px_per_um" : None,
            "YFP_pwr" : None,
            "YFP_exp" : None,
            "YFP_channel" : None,
            "PC_pwr" : None,
            "PC_exp" : None,
            "PC_channel" : None
        }

        raw_info = tif.imagej_metadata["Info"].split("\n")
        
        for line in raw_info:
            if "wsObjectiveName" in line:
                info["lens"] = " ".join(line.split(" ")[5:-2][::-1])
                info["magnification"] = int(info["lens"][:2])
            if "Numerical Aperture" in line:
                info["NA"] = float(line.split(" = ")[1])
                
            
        if n_channels == 1:
            for line in raw_info:
                if "Widefield Fluorescence" in line:
                    info["YFP_channel"] = 1
                elif "Brightfield" in line:
                    info["PC_channel"] = 1

            for line in raw_info:
                if info["PC_channel"] is None:
                    if "514" in line and info["YFP_pwr"] is None:
                        for x in line.split("       "):
                            if "514; Power" in x:
                                try:
                                    string = x.split("514; Power")[1].split(";")[0][-5:]
                                    if string[0] == ":": 
                                        string = string[1:]
                                    info["YFP_pwr"] = float(string)
                                except:
                                    print(x)
                                    info["YFP_pwr"] = 100.
                                break
                else:
                    if "Nikon Ti2, Illuminator(DIA) Iris intensity" in line:
                        info["PC_pwr"] = float(line.split("= ")[1])
                            
                if "Exposure time (text)" in line:
                    if info["YFP_channel"] is None:
                        info["PC_exp"] = int(1000*float(line.split("= ")[1])+0.5)
                    else:
                        info["YFP_exp"] = int(1000*float(line.split("= ")[1])+0.5)

                    
        else:
            for line in raw_info:
                if "Widefield Fluorescence" in line:
                    info["YFP_channel"] = int(line.split(" = ")[0][-1])
                elif "Brightfield" in line:
                    info["PC_channel"] = int(line.split(" = ")[0][-1])
                    
            for line in raw_info:
                if "514" in line and info["YFP_pwr"] is None:
                    for x in line.split("       "):
                        if "514; Power" in x:
                            try:
                                string = x.split("514; Power")[1].split(";")[0][-5:]
                                if string[0] == ":": 
                                    string = string[1:]
                                info["YFP_pwr"] = float(string)
                            except:
                                print(x)
                                info["YFP_pwr"] = 100.
                            break

                if "Exposure time (text)" in line:
                    channel = int(line.split(" = ")[0][-1])
                    if channel == info["YFP_channel"]:
                        info["YFP_exp"] = int(1000*float(line.split("= ")[1])+0.5)
                    if channel == info["PC_channel"]:
                        info["PC_exp"] = int(1000*float(line.split("= ")[1])+0.5)

                if "Nikon Ti2, Illuminator(DIA) Iris intensity" in line:
                    channel = int(line.split(" = ")[0][-1])
                    if channel == info["PC_channel"]:
                        info["PC_pwr"] = float(line.split("= ")[1])

    
    um_per_px_20x = 0.3247368
    if info["lens"] == "20x":
        info["um_per_px"] = um_per_px_20x
        info["px_per_um"] = 1/um_per_px_20x
    
    else:
        info["um_per_px"] = um_per_px_20x*.5
        info["px_per_um"] = 2/um_per_px_20x
               
    return info