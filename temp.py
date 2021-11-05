from urllib.parse import urlparse
from urllib.parse import unquote
import requests
import os

image_url = "https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2Fsecond_brain%2FD3c9s60Nm_.png?alt=media&token=9994598a-582a-4fb5-ab53-e97862cc5e72"


o = urlparse(image_url)
#path = unquote(o.path)
filename = os.path.basename(urlparse(image_url).path)
print(filename)
import pdb; pdb.set_trace()


#res = requests.get(image_url)
#with open("temp.png", "wb") as f:
#    f.write(res.content) 