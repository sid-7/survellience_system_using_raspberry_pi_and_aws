import boto3
import multiprocessing
from threading import Thread
import os, datetime
from time import sleep
import threading
import subprocess


# continuosly polls the output_queue and looks for signal to terminate master
def signal_fetcher(shared):

	global sqs_resource

	input_queue = sqs_resource.get_queue_by_name(QueueName = "Output_Queue")
	msg_size = input_queue.attributes["ApproximateNumberOfMessages"]
	if(int(msg_size) > 0):
			message = input_queue.receive_messages()
			message[0].delete()
			shared["master_closing_flag"] == True # if message is received, flag is made True

# used to fire ssh command on worker instances
def subprocess_cmd(command):
	process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	proc_stdout = process.communicate()[0].strip()
	print(proc_stdout)


# starts worker instaces and run worker.py with the help of ssh
def spawning_ec2(shared, instance_id, instance_threshold):
	global ec2_client, sqs_resource, ec2_resource

	Print("Master launching instance: " + instance_id)

	instance = ec2_resource.Instance(instance_id)
	instance.start()
	while(instance.state['Code'] != 16):
		sleep(5)
		instance = ec2_resource.Instance(instance_id)

	response1 = ec2_client.describe_instances(InstanceIds = [instance_id], DryRun=False) # capturing response from the worker instance 
	instance_dns = response1['Reservations'][0]['Instances'][0]['PublicDnsName'] #fetching public dns from the response

	cmd = "ssh -o StrictHostKeyChecking=no -i sid_key_pair.pem ubuntu@" + instance_dns + " xvfb-run python3 worker.py "

	while(True):
		print(instance_id)
		subprocess_cmd(cmd)
		messages = sqs_resource.get_queue_by_name(QueueName = "Input_Queue").attributes["ApproximateNumberOfMessages"]  
		if( int(messages) > instance_threshold):
			sleep(2)
			continue
		else:
			break

	print("Master stopping instance: " + instance_id)

	response = ec2_client.stop_instances(InstanceIds = [instance_id], DryRun=False)
	waiter = ec2_client.get_waiter("instance_stopped")
	waiter.wait(InstanceIds = [instance_id])
	shared['instance_names'] += [instance_id]
	shared['current_threshold'] -= 1




def scaling_ec2(shared):

	shared['instance_names'] = ["i-0107960d5744822e8", "i-0c77f45da8a62ee36", "i-0070a496eaa1f9b7c", "i-0c21691e4cb811a2e", "i-023b1e90c3b5a786f", "i-00daa984a1844ded9", "i-036b3f462db6132bd"]

	print("Master Monitoring.....")

	global sqs_resource, ec2_client

	input_queue = sqs_resource.get_queue_by_name(QueueName="Input_Queue")
	messages = sqs_resource.get_queue_by_name(QueueName = "Input_Queue").attributes["ApproximateNumberOfMessages"]

	while(True):
		messages = sqs_resource.get_queue_by_name(QueueName = "Input_Queue").attributes["ApproximateNumberOfMessages"]

		if(int(messages) > shared['current_threshold'] and len(shared['instance_names']) > 0):
			_name_ = shared['instance_names'][0]
			shared['instance_names'] = shared['instance_names'][1:]
			temp = shared['current_threshold']	
			threading.Thread(target=spawning_ec2, args = (shared, _name_, temp), name=_name_).start()
			shared['current_threshold'] += 1

		elif int(sqs_resource.get_queue_by_name(QueueName = "Input_Queue").attributes["ApproximateNumberOfMessages"]) == 0 and shared['current_threshold'] == 0 and shared["master_closing_flag"] == True:
			print("Master out......")
			break




if __name__=='__main__':
	global sqs_resource, ec2_client
	with multiprocessing.Manager() as manager:
		shared = manager.dict()
		
		ec2_client = boto3.client('ec2')
		sqs_resource = boto3.resource('sqs')
		ec2_resource = boto3.resource('ec2')
		

		shared['instance_names'] = []
		shared['current_threshold'] = 0
		shared["master_closing_flag"] = False


		p1 = multiprocessing.Process(target = scaling_ec2, args=(shared,))

		p2 = multiprocessing.Process(target = signal_fetcher, args=(shared,))
		
		p1.start()
		p2.start()

		
		p2.join()
		p1.join()
