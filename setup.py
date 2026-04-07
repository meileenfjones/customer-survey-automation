import requests
import lxml.html
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
############################################################################################################
# go to the general winscp download webpage
winscp_webpage = requests.get('https://winscp.net/eng/downloads.php')
webpage_content = lxml.html.fromstring(winscp_webpage.content)
port_exec_extension = webpage_content.xpath('//div[@id="stable_portablezip"]/p[2]/a')[0].get('href')
# go to winscp portable executables webpage
portable_executable = requests.get('https://winscp.net/'+webpage_content.xpath('//div[@id="stable_portablezip"]/p[2]/a')[0].get('href'))
portable_executable_content = lxml.html.fromstring(portable_executable.content)
direct_download_link = portable_executable_content.xpath('//a[contains(., "Direct download")]')[0]
# download zipfile with winscp.com file
zip_file_data = requests.get(direct_download_link.get('href'))
zipfile_content = ZipFile(BytesIO(zip_file_data.content))
zipfile_content.extractall(Path(r'\\ole-srv-01-app\D-Drive\GitHub\Crossroads-Survey-Automation\winscp_files'))
