<a visibility=false href="#BLE-Mesh-Project"></a>

<!-- Original Readme Credit: https://github.com/othneildrew/Best-README-Template/blob/master/README.md -->

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

## BLE Mesh Project

<!-- TABLE OF CONTENTS -->

  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#architecture">Architecture</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#prerequisites">Prerequisites</a></li>
      </ul>
    </li>
    <li><a href="#provisioning">Provisioning</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#demo">Demo</a></li>
    <li><a href="#assumptions-and-special-notes">Assumptions and Special Notes</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>

<!-- ABOUT THE PROJECT -->
## About The Project

In this project, we wish to use an interactive web server to send commands to the mouse and record the neural responses.
For the scope of this demo, we shall be using a BLE device instead of a mouse.
We shall be hosting our webserver on Raspberry Pi and use Bluetooth for communication purposes.


![Introduction Diagram](https://github.com/matsy/BLE-Mesh-Project/blob/Demo/assets/img/Intro.PNG)


<p align="right">(<a href="#ble-mesh-project">back to top</a>)</p>

### Architecture

Our Software Architecture diagram looks as follows. For detailed information on the architecture of our project, please refer to Docs.


![Software Architecture Diagram](https://github.com/matsy/BLE-Mesh-Project/blob/Demo/assets/img/Architecture.png)

We have five software components as can be seen in the architecture diagram. They are:

* <em>UI/UX Interface</em>: Contains all the UI Views that are part of web interface.
* <em>Web Server</em>: Contains API endpoints for handling various functionalities floated in the above UI views.
* <em>Database System</em>: Stores all the user, log, command and scheduled jobs information.
* <em>Bluetooth Controller</em>: Acts as a bridge between the Mesh network and web server.
* <em>Bluetooth Mesh Network</em>: The main network containing chipsets (BLE devices) and provisioner. 

In our project,
* The first three components are hosted on Raspberry Pi. <br>
* Raspberry Pi and nRF52840 provisioner together form the Bluetooth controller component.  <br>
* All the nRF5284 chipsets together with the provisioner form the Bluetooth mesh network. <br> 

<p align="right">(<a href="#ble-mesh-project">back to top</a>)</p>

<!-- GETTING STARTED -->
## Installation

Please use the SDK that we provide, and it should be two SDK folders next to each other.

The directory structure for those two SDK folders should be as follows

```sh
nRF5_SDK_17.0.2_XXXXXXX
nrfXSDKforMeshv500src
```

And here are the links to the SDK download page:

[nrfXSDKforMeshv500src](https://www.nordicsemi.com/Products/Development-software/nRF5-SDK-for-Mesh/Download?lang=en#infotabs)

[nRF5_SDK_17.0.2_XXXXXXX](https://www.nordicsemi.com/Products/Development-software/nRF5-SDK/Download?lang=en#infotabs)

Use the Segger Embedded Studio to open the project file and flash the correct SDK into the board.

### Prerequisites

1. For server-end(BLE device), user should use the source code under *nrfXSDKforMeshvXXXsrc/examples/light_switch/*, and then choose the correct version for the BLE device (we used nRF52840DK), and please flash using the Segger Embedded Studio. <br> 
For provisoning-end(provisioner), user should use the source code under *nrfXSDKforMeshvXXXsrc/examples/serial/*, and then choose the correct versions for your board, and then flash using the Segger Embedded Studio.

2. Then install the required package to provision the nodes, go in the directory and install the requirements
```sh
$ cd scripts/interactive_pyaci
$ pip install -r requirements.txt
```

## Project Setup

The Webserver is capable of configuring and provisioning the Mesh Network. <br>
Take a clone of the <em>BLE-Mesh-Project</em> Repo and switch to the <em>Demo</em> branch using following commands. <br>
```sh
git clone https://github.com/sangtaeha/BLE-Mesh-Project.git
cd BLE-Mesh-Project/
git fetch origin Demo
git checkout --track origin/Demo
git branch
```

Now go to the <em>BLE-Mesh-Project</em> folder and install the requirements required for running the webserver using:

```sh
pip install -r requirements.txt
```

If there are any errors, please resolve them before you move to the next step. <br>
Now go ahead and run the webserver using the following commands in two different terminals
```sh
python3 Main.py
python3 Job_executor.py 
```

Now you can access the web server at 
```sh
http://127.0.0.1:5000/home_page or
http://<public_ip>:5000/home_page
```

If you wish to make your web server public, we can use ngrok and use it anywhere
```sh
ngrok http 5000
```

The URL returned after executing above command shall be the public URL.
<!-- Setup -->
## Initial Configuration
* Once the webserver is launched, navigate to the Add devices tab, enter the number of nodes to be provisioned.  
* Then Click on the start provision button.  
* Kindly wait till all the nodes are provisioned.    
* Then the user can schedule jobs through the Webserver.  
* Some times the provisioner might take time to respond even after sending the command, in that case the system would reinstantiate the command and returns only after the command is successful.   

<!-- DEMO -->
## Demo

To see the detailed Provisioning demo i.e pre-configuring our Mesh network, please see ProvisioningCMD.txt

You can also find recorded videos showcasing various functionalities [here](https://drive.google.com/drive/folders/1mj9k4nUD2uz2zvglwnFj10nvoBgDb3C5?usp=sharing). 

<!-- Assumptions -->
## Assumptions and Special Notes

* We also assume that the web server will be used on a single Mesh Network i.e. multiple people may use this web server to configure commands but all these commands shall be executed on the same Mesh Network. In effect, it means commands scheduled by a particular person can be seen by everyone.
* Each of the nRF52840 chips are reachable to at least one development kit in the Mesh Network.
* There exists atleast one path from every chip to the provisioner, not neccesarily an optimal one at any point of time.
* The interval used while scheduling the jobs/commands shall be atleast 60 seconds or 1 minute.
* For periodic scheduling, the end time is assumed to be more than the start time and the difference is atleast a minute.
* We also assume that the user doesn't schedule a command in the past and would schedule a command to either run immediately or at some point in the future.
* Sanity checks have been taken care of at as many places as possible but I couldn't cover every scenario and would have missed some. Please let me know if I missed any.
* We assume that the user shall input Group and Chip IDs as per the Mesh network and not give values of nodes that are not present in the Mesh Network. 
* Since our webserver checks for jobs (that need to be executed), every 30 seconds, while using periodic scheduling, please try to schedule the consecutive jobs some time apart. The webserver was able to run the commands as expected even if they are pretty close but we observed that the reliability of these commands being sent over network was low when scheduled immediately (maybe because of the serial connection used between Raspberry Pi and Provisioner).

<p align="right">(<a href="#ble-mesh-project">back to top</a>)</p>

## Contributing

I would like to express my special appreciation and thanks to Professor Dr. Sangtae Ha, for having been a tremendous mentor for me. I would like to thank him for his invaluable feedback and constant support throughout this project. 

<!-- CONTACT -->
## Contact
For any more information, please refer to the Docs or please feel free to contact Vignesh.Vadivel@colorado.edu or sangtae.ha@colorado.edu

<p align="right">(<a href="#ble-mesh-project">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Provisioning and running Nordic's BLE Mesh](https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci)
* [Interactive PyACI script](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.meshsdk.v5.0.0/md_scripts_interactive_pyaci_README.html)
* [Serial interface library](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.meshsdk.v5.0.0/md_doc_user_guide_modules_serial.html)

<p align="right">(<a href="#ble-mesh-project">back to top</a>)</p>


<!-- More info pleace take a look at those page-->

<!-- https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v5.0.0%2Fmd_examples_provisioner_README.html&anchor=provisioner_example_assignment -->

<!-- https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci -->

<!-- https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v5.0.0%2Fmd_examples_provisioner_README.html&anchor=provisioner_example_assignment -->





