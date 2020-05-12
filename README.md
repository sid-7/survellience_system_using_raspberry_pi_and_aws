# Survellience System using RaspberryPi and AWS
With advancement in IoT(Internet of Things) devices, the growth of data has been explosive. Hence, the computation and processing of this large scale data takes a toll on the cloud resources and it struggles to meet all the computational demands due to the high response time. Here we are trying to address this problem with the help of edge computing by building an elastic and responsive application which utilizes cloud resources and the resources of IoT devices , as a result reducing the end-to-end latency.

  In this project, we are building a surveillance application which is built upon Raspberry Pi and Amazon Web Services(AWS). Raspberry Pi detects the motion which triggers its camera to start recording the video wherein it detects the objects in the video. Here the Raspberry Pi acts as an edge and AWS provides the cloud infrastructure. As the Raspberry pi’s processor cannot handle multiple video processing requests at the same time, we take help of the cloud resources which help the pi to carry out the process. Hence, the Raspberry pi provides responsiveness and AWS provides scalability.
  
  <h1> Architecture</h1>
  
  ![Architecture](https://github.com/sid-7/survellience_system_using_raspberry_pi_and_aws/blob/master/Architecture.PNG)
  
  <h1> Steps to run the application</h1>

- Creating AWS services:
    - Create a Bucket with an unique name
    - Create a Standard Queue with an unique name
    - Create an EC2 t2.micro instance with name Master using community AMI ami-0903fd482d7208724
    - Create an EC2 t2.micro instance with name Worker using community AMI ami-0903fd482d7208724
    
- Setting up the environment:
    - Raspberry Pi
      - Install everything from requirements.txt
      - Copy aws credentials in the credentials file
    - Master Instance
      - Install everything from requirements.txt
    - Worker Instance
      - Install everything from requirements.txt

- Transfering all darknet files to home directory
```
$~:mv darknet darknet2
$~:mv -rf darknet2/* ./
$~:rm -rf darknet
```
- Create a snapshot of the current instance and create multiple worker instances using this snapshot-image.

- Copy the following files:
  - Unzip the folder, keep all the files in the same folder.
  - Copy recorder_pi.py in Raspberry pi’s darknet folder.
  - Copy copy_aws_credentials.py in pi’s home folder.
  - Copy master.py in master instance’s darknet folder.
  - Copy worker.py in all the worker instance’s home folder.

- Setting up correct credentials:
  - From pi, run copy_aws_credentials.py
  - python3 copy_aws_credentials.py

- From Master instance, run master.py
  - python3 master.py

- From pi, run recorder_pi.py
``` $~: python3 recorder_pi.py```


