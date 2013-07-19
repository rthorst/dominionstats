import os

def B2MB(n):
    return n/(1024*1024.0)

def get_size(folder):
    folder_size = 0
    zip_size = 0
    fc = 0
    for (path, dirs, files) in os.walk(folder):
      for file in files:
        filename = os.path.join(path, file)
        size =  os.path.getsize(filename)
        if 'bz2' in filename:
            zip_size += size
        else:
            folder_size += os.path.getsize(filename)
        fc+=1
    return (folder_size, zip_size, fc)

FOLDERS = [('MONGO', './db'), 
           ('Scrape', './static/scrape_data'),
           ('Parsed', './parsed_out')]

for (name, folder) in FOLDERS:
    (size, zip_size, count) = get_size(folder)
    print "%-7s %8.2f MB"%(name, B2MB(size))
    if zip_size > 0:
        print " %-6s %8.2f MB"%('(zips)', B2MB(zip_size))
