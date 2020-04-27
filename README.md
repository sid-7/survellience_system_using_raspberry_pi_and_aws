# survellience_system_using_raspberry_pi_and_aws
The Application detects motion and starts recording using the camera connected to the raspberry pi. The videos are processed to detects object using the darknet model. The application balances the processing load between raspberry pi and EC2 instances. We have hard coded the auto-scaling feature to control the number of instances that are launched.
