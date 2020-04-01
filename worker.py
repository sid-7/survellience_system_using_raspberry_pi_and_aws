import sys
import boto3
import os, datetime
from time import sleep


# takes the output files and filters only the objects detected and returns them as a list of strings.
def parse_output(file_name):
	objects = set()
	with open(file_name, "r") as f:
		lines = f.readlines()
		for line in lines:
			line = line.split("%")
			if(len(line)==2):
				objects.add(line[0].split(":")[0])
	with open(file_name, "w") as f:
		if len(list(objects)) == 0:
			f.write("no objects detected")
		else:
			f.write(str(list(objects)))
	print("-"*10,"File {} updated {} ".format(file_name, len(objects)))


if __name__ == "__main__":

	s3_client = boto3.client('s3')
	s3_resource = boto3.resource('s3')
	sqs_resource = boto3.resource('sqs')
	bucket_name = "bucket23797" #change the bucket name to match your bucket
	
	while True:

		input_queue = sqs_resource.get_queue_by_name(QueueName = "Input_Queue")
		msg_size = input_queue.attributes["ApproximateNumberOfMessages"]

		if(int(msg_size) > 0):
			message = input_queue.receive_messages()
			if(len(message)==0):
				continue
			file_name = message[0].body
			message[0].delete()
			
			#downloading videos
			s3_resource.Bucket(bucket_name).download_file(str(file_name),str(file_name))

			#processing videos
			output_file = file_name.split(".")[0]
			cmd = "./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights " + file_name + " > "  + output_file + " 2>err_" + output_file + ".txt"
			os.system(cmd)

			#parse file to remove unncessary text
			parse_output(output_file)

			#sending output to s3
			response = s3_client.upload_file( output_file, bucket_name ,"output/" + output_file)


		else:
			sleep(2)
			input_queue = sqs_resource.get_queue_by_name(QueueName = "Input_Queue")
			msg_size = input_queue.attributes["ApproximateNumberOfMessages"]
			if msg_size == '0':
				break
