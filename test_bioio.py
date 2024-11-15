# %%
from bioio import BioImage
import os

# %%
test_dir = "/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents - Team - Bard Lab/Data/MaxineC/Microscopy/241108/"
test_file = os.path.join(test_dir, "Sample 1.nd2")
BioImage(test_file)

# %%
img.data
image.dims
# %%
img.save(os.path.join(test_dir, "test.tif"))
# %%
test_dir = "/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents - Team - Bard Lab/Data/JaredB/Microscopy"
test_file = os.path.join(test_dir, "241004-37--02.czi")
img_czi = BioImage(test_file)
img_czi.dims
# %%
