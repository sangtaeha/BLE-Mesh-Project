<a visibility=false href="#readme-top"></a>

<!-- Original Readme Credit: https://github.com/othneildrew/Best-README-Template/blob/master/README.md -->

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
## BLE-Mesh Project

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
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>

<!-- ABOUT THE PROJECT -->
## About The Project

In this project, we wish to use an interactive web server to send commands to the mouse and record the neural response.
For the scope of this demo, we shall be using a BLE device instead of a mouse.
We shall be hosting our webserver on Raspberry Pi and use Bluetooth for communication purposes.

![Introduction Diagram](https://github.com/matsy/BLE-Mesh-Project/blob/Demo/assets/img/Intro.PNG)

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

### Architecture

Our Software Architecture diagram looks as follows. For detailed information on the architecture of our project, please refer to Docs.

![Software Architecture Diagram](https://github.com/matsy/BLE-Mesh-Project/blob/Demo/assets/img/Architecture.png)

We have five software components as can be seen in the architecture diagram. They are:

* <em>UI/UX Interface</em>: Contains all the UI Views that are part of web interface.
* <em>Web Server</em>: Contains API endpoints for handling various functionalities floated in the above UI views.
* <em>Database System</em>: Stores all the user, log, command and scheduled jobs information.
* <em>Bluetooth Controller</em>: Acts as a bridge between the Mesh network and web server.
* <em>Bluetooth Mesh Network</em>: The main network containing chipsets (BLE devices) and provisioner.

* The first three components are hosted on Raspberry Pi. <br>
* Raspberry Pi and nRF52840 provisioner together form the Bluetooth controller component.  <br>
* All the nRF5284 chipsets together with the provisioner form the Bluetooth mesh network. <br> 

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

<!-- GETTING STARTED -->
## Installation

For us to start using the webserver, we need to first configure the Mesh Network that can be done using the steps mentioned below.

Please use the SDK that we provide, and it should be two SDK folders next to each other.

The directory structure for those two SDK folders should be as follows

```sh
nRF5_SDK_17.0.2_XXXXXXX
nrfXSDKforMeshv500src
```

And here is the link to the SDK download page:

*https://www.nordicsemi.com/Products/Development-software/nRF5-SDK-for-Mesh/Download?lang=en#infotabs*


*https://www.nordicsemi.com/Products/Development-software/nRF5-SDK/Download?lang=en#infotabs*

Use the Segger Embedded Studio to open the project file and flash the correct SDK into the board.

### Prerequisites

1. For server-end(BLE device), we should use the source code under *nrfXSDKforMeshvXXXsrc/examples/light_switch/*, and then choose the correct version for the BLE device (we used nRF52840DK), and please flash using the Segger Embedded Studio. <br> 
For provisoning-end(provisioner), we should use the source code under *nrfXSDKforMeshvXXXsrc/examples/serial/*, and then choose the correct versions for your board, and then flash using the Segger Embedded Studio.

2. Then install the PyACI package, go in the *nrfXSDKforMeshvXXXsrc/scripts/interactive_pyaci* directory and install the requirements
```sh
$ cd scripts/interactive_pyaci
$ pip install -r requirements.txt
```

3. Starting the interface. For all the administration and setup, we'll do it under the PyACI interface, here's how to start that interface.

```sh
$ cd scripts/interactive_pyaci
$ interactive_pyaci$ python interactive_pyaci.py -d <COM>
# Windows COM port: it should be COM*, For example COM0
# Ubuntu/Linux COM port: it should be /dev/tty*, For example /dev/ttyACM0
```
For Windows, (Start → Control Panel → Hardware and Sound → Device Manager) under the Device Manager list, open the category "Ports", and find the matching COM Port.

For Linux user, use the following code in terminal to find the correct port
```sh
dmesg | grep tty
```

*(Note: if you need to modify the number of groups, please make changes in "example_database.json" before any further setting, in the "example_database.json")*

This is an example of one groups, if you need more groups, you can expand it several times and change the key and index for each group to a unique.

```sh
    {
      "boundNetKey": 0,
      "index": 0, #increase for each groups
      "key": "4f68ad85d9f48ac8589df665b6b49b8a", #Change here
      "name": "lights"
    },
```
For the demo purposes, we provisioned the Mesh network using the nRF52840 chipset attached to the Raspberry Pi. <br>
However, you can also provision the network beforehand using operating system of your own and connect the same provisioner to Raspberry Pi(hosting web server) and use the same example_database.json.

4.  Loading the database which has the information of all the nodes


```sh
$ db = MeshDB("database/example_database.json")
$ db.provisioners
# Wait for logs return
$ p = Provisioner(device, db)
# Wait for logs return
```

5. Adding Configuration Client
```sh
$ cc = ConfigurationClient(db)
$ device.model_add(cc)
```

6. Scaning for new nodes, (pressing botton 4 on the boards will reset all the provisioning) <br>
<em>note: We can provision only one node at a time.</em>
```sh
$ p.scan_start()
# Wait for logs return
$ p.scan_stop()
# Wait for logs return
```


## Provisioning

1. Provisioning nodes
 ```sh
$ p.provision(name="AnyName")
# <AnyName> will be the name of this node once provisioned. Wait for the logs to return
# Plese remember the {'devkey_handle': X} and {'address_handle': X}> we were using this in the next steps. 

$ cc.publish_set(x, x) 

# (devkey_handle x,address_handle x) in default, it should be 8,0
# This function can switch to different nodes, and the settings can only be broadcast to one node only. This command must be added every time you want to broadcast settings changes to different nodes

$ cc.composition_data_get()
# Wait for logs return
```

2. Add node into different groups
```sh
$ cc.appkey_add(0) 
# This step lets this node know that the group 0 exists, And this can continue to the next step to add this node to this group.
# If you want this node to be freely remove and added to other groups please add other groups like "cc.appkey_add(1) cc.appkey_add(2) ..."
# Wait for logs return

$ cc.model_app_bind(db.nodes[0].unicast_address, 0, mt.ModelId(0x1000)) 
# Make the this node bind to appkey 0, which is the group 0

# you can also use cc.model_app_unbind() to unbind from the group
# Wait for logs return
$ cc.model_subscription_add(db.nodes[0].unicast_address, 0xc001, mt.ModelId(0x1000)) # Add to subscription to group 0xC001
# Wait for logs return
```
3. After adding all the nodes and and grouping them into different groups.
```sh
$ device.send(cmd.AddrSubscriptionAdd(0xc001)) # Creates a address_handle for all the set, this would be the entireGrops_index, we will use this to control different groups.

# Wait for logs return and take notes of the {'address_handle': X}, that will be the address_handle for the entire grops(We will use this to control different groups)
```
Please refer to following references for more information. 
1. [Interactive PyACI Script](https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v4.1.0%2Fmd_scripts_interactive_pyaci_README.html)
2. [Provisioning and running Nordic's BLE Mesh](https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci)

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

After provisioning, this is a simple test under the PyACI environment.

1. Adding GenericOnOffClient()
```sh
$ gc = GenericOnOffClient()
```
2. Turn on or off by single nodes or groups
```sh
$ device.model_add(gc)
$ gc.publish_set(0, 0) #publish_set(groups_index, node_index) turn on individual nodes
# #publish_set(groups_index, entireGrops_index) will turn on by groups
$ gc.set(True) #light should turn on
$ gc.set(False) #light should turn off
```

## WebServer Setup

Now that the Mesh network is already pre-configured, we will set up the webserver now. <br>
Take a clone of the <em>BLE-Mesh-Project</em> Repo and switch to the <em>Demo</em> branch. <br>
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

<!-- DEMO -->
## Demo

To see the detailed Provisioning demo, please see ProvisioningCMD.txt

<!-- ROADMAP -->
## Roadmap

xxxx

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

xxxx

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

<!-- LICENSE -->
## License

xxxx

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

<!-- CONTACT -->
## Contact

xxxx

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Provisioning and running Nordic's BLE Mesh](https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci)
* [Interactive PyACI script](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.meshsdk.v5.0.0/md_scripts_interactive_pyaci_README.html)
* [Serial interface library](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.meshsdk.v5.0.0/md_doc_user_guide_modules_serial.html)

<p align="right">(<a href="#BLE-Mesh Project">back to top</a>)</p>


<!-- More info pleace take a look at those page-->

<!-- https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v5.0.0%2Fmd_examples_provisioner_README.html&anchor=provisioner_example_assignment -->

<!-- https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci -->

<!-- https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v5.0.0%2Fmd_examples_provisioner_README.html&anchor=provisioner_example_assignment -->





