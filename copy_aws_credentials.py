'''
this code will run on pie, this will update the credential file
on each instance.
'''
import boto3
import threading
import subprocess
from time import sleep


def start_and_upload():
	global ec2, source, destination, pem_files, ec2_client

	instance_id = threading.current_thread().name
	instance = ec2.Instance(instance_id)
	instance.start()

	while(instance.state['Code']!=16):
		sleep(7.5)
		instance = ec2.Instance(instance_id)
	print("Instance {}, Running".format(instance_id))
	sleep(7.5)	
	response = ec2_client.describe_instances(InstanceIds = [instance_id], DryRun=False)
	instance_dns = response['Reservations'][0]['Instances'][0]['PublicDnsName']
	sleep(7.5)
	cmd = "scp -o StrictHostKeyChecking=no -i ~/darknet/{} {} ubuntu@{}:{}".format(pem_files[instance_id], source, instance_dns, destination)
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	out, err = process.communicate("")

	if(err != b''):
		for i in range(3):
			print("{} try: {}".format(instance_id, i))
			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			out, err = process.communicate("")
			if(err == b''):
				break
			sleep(2)

	print("Instance {}, done| {}".format(instance_id, out))
	instance.stop()

	while(instance.state['Code']!=80):
		sleep(7.5)
		instance = ec2.Instance(instance_id)
	print("")
	print("Instance {}, stopped".format(instance_id))



if __name__=='__main__':
	global ec2, source, destination, pem_files, ec2_client
	
	ec2 = boto3.resource('ec2')
	ec2_client = boto3.client('ec2')
	source = "~/.aws/credentials"
	destination = "~/.aws/credentials"
	sid_instance_ids = ["i-0d420f853783ff495", "i-0107960d5744822e8", "i-0c77f45da8a62ee36", "i-0070a496eaa1f9b7c", "i-0c21691e4cb811a2e", "i-023b1e90c3b5a786f", "i-00daa984a1844ded9", "i-036b3f462db6132bd"]
	for i in sid_instance_ids:
		pem_files[i] = 'sid_key_pair.pem'
	instance_ids = sid_instance_ids + monil_instance_ids + dada_instance_ids

	threads = []
	for instance_id in instance_ids:
		t = threading.Thread(target=start_and_upload, args=(), name=instance_id)
		t.start()
		print(instance_id,"<-~~-")
		threads.append(t)

	for thread in threads:
		thread.join()

