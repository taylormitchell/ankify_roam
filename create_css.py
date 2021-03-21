import os
from ankify_roam.default_models import ROAM_BASIC, ROAM_CLOZE

dir_css = "css"

with open(os.path.join(dir_css, "roam_basic.css"), "w") as f:
    f.write(ROAM_BASIC["css"])

with open(os.path.join(dir_css, "roam_cloze.css"), "w") as f:
    f.write(ROAM_CLOZE["css"])
