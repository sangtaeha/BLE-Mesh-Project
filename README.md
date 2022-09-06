<a name="BLE Mesh Project Readme"></a>

<!-- Original Readme Credit: https://github.com/othneildrew/Best-README-Template/blob/master/README.md -->





<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->


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
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>




<!-- ABOUT THE PROJECT -->
## About The Project

texttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttext
* texttexttexttexttexttexttextttexttexttexttexttexttexttexttexttexttexttexttext

* textxttexttexttext

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Architecture

texttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttexttext

* text
* text
* text


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Installation

Pleas using the SDK that we provide, and it should be two SDK folder next to each other.

Those two SDK folder should be like the following

```sh
nRF5_SDK_XX.X.X_XXXXXXX
nrfXSDKforMeshvXXXsrc
```

By using the Segger Embedded Stuio to open the project file and to flash the correct SDK into the board

### Prerequisites

1. For the server-end(the lights) it should use the source code under *<nrfXSDKforMeshvXXXsrc>/examples/light_switch/*, and then choosing the correct versions for your board, then flash by using the Segger Embedded Stuio

And for the pervisoning-end(the controller) is should use the surce code under *<nrfXSDKforMeshvXXXsrc>/examples/serial/*, and then choosing the correct versions for your board, then flash by using the Segger 

2. Then install the PyACI package, go in the *scripts/interactive_pyaci* directory and install the requirements
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

6. Scaning for new nodes, (press botton 4 on the boards will reset all the pervisioning), notes that provisions can only add one node at the time
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
# Wait for logs return
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

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

After pervisioning, this is a simple test under the PyACI environment.

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



<!-- ROADMAP -->
## Roadmap

xxxx

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

xxxx

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

xxxx

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

xxxx

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments


* [Provisioning and running Nordic's BLE Mesh](https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci)
* [Interactive PyACI script](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.meshsdk.v5.0.0/md_scripts_interactive_pyaci_README.html)
* [Serial interface library](https://infocenter.nordicsemi.com/topic/com.nordic.infocenter.meshsdk.v5.0.0/md_doc_user_guide_modules_serial.html)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- More info pleace take a look at those page-->

<!-- https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v5.0.0%2Fmd_examples_provisioner_README.html&anchor=provisioner_example_assignment -->

<!-- https://devzone.nordicsemi.com/guides/short-range-guides/b/mesh-networks/posts/provisioning-and-running-nordic-s-ble-mesh-with-python-application-controller-interface-pyaci -->

<!-- https://infocenter.nordicsemi.com/index.jsp?topic=%2Fcom.nordic.infocenter.meshsdk.v5.0.0%2Fmd_examples_provisioner_README.html&anchor=provisioner_example_assignment -->





