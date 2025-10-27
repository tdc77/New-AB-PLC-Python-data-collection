A newer version of my Datacollection python program. I used customtkinter for a better looking gui and easier tag selecting.

when opening is vscode or pycharm make sure the Main_page.py, setup_page.py, __init__.py are in a folder called pages.  app.py and main.py must be outside of that folder.
<img width="379" height="788" alt="folderstructure" src="https://github.com/user-attachments/assets/005e5443-9ccd-4f79-8790-be3584dc92b4" />

INSTRUCTIONS:


From MAIN PAGE:  Select setup button.


<img width="1433" height="945" alt="Mainpagewsetup" src="https://github.com/user-attachments/assets/9feebdf1-60fb-460e-96e0-d97ed79b4b9c" />



In setup page fill out top portion for IP Address of PLC, Time interval you want to get data, and select a file save location.  IF you do not select a new location
It will save in the same folder location as main program.  Please note, The program will keep a backup copy in the folder as well.  Once top is filled out select "Connect and Load tags " button.


<img width="1407" height="940" alt="setuppage" src="https://github.com/user-attachments/assets/cfa706d0-8927-4301-8f73-67fdae3ed80d" />




If connection is successfull you should see your tags from the plc, select the ones you want by selecting the checkbox next to the tag.  If your tag is an array you can 
select how many you want on the right hand side of column.


<img width="1399" height="933" alt="selecttags" src="https://github.com/user-attachments/assets/7776add5-a3f5-4b46-b771-f6dcd338b5bc" />


Hit save selection and start logging button, it will automatically go to main page and start logging.


<img width="1418" height="930" alt="MainData" src="https://github.com/user-attachments/assets/d7f7a981-cf68-4477-954c-eb9bea176535" />

You can uncheck columns you do not want to chart.  You can start\stop logging at any time and clear the table.

Also a new sheet will start at midnight!




THIS IS STILL UNDER CONSTRUCTION:
Working on only getting data when the data changes so your not getting duplicates.
Saving in a separate folder instead of same folder as program.
checkbox for new sheet creatio.
