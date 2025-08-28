# %%
from bioio import BioImage
import os

# %%
test_dir = "/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents - Team - Bard Lab/Data/MaxineC/Microscopy/241108/"
test_file = os.path.join(test_dir, "Sample 1.nd2")
img = BioImage(test_file)

# %%
import xml.dom.minidom
meta = img.metadata.to_xml()
parsed = xml.dom.minidom.parseString(str(meta))
pretty = parsed.toprettyxml()
print(pretty)

# %%
img.save(os.path.join(test_dir, "test.tif"))
# %%
test_dir = "/Users/jbard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents - Team - Bard Lab/Data/JaredB/Microscopy"
test_file = os.path.join(test_dir, "241004-37--02.czi")
img_czi = BioImage(test_file)
img_czi.dims
# %%
