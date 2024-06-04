log_file_path = '/Users/nurizaurulbaeva/Desktop/ChatIvy_Jake Li_20240603_122731.log'

with open(log_file_path, 'r') as log_file:
    log_contents = log_file.read()

return (log_contents[2000:4000])