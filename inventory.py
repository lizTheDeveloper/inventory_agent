import cv2
import os
import time
import requests
import base64
from openai import OpenAI



most_recent_timestamp = time.time()

openai_client = OpenAI()

last_few_frames = []
last_few_messages = []

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def capture_frames_from_stream():
        most_recent_timestamp = time.time()

        cap = cv2.VideoCapture(0)
        
        # Initialize video capture from the stream URL
        if not cap.isOpened():
            print("Error: Unable to open stream.")
            return
        try:
            ## move the current rover.jpg to the current timestamp.jpg in the /old_frames directory
            ## then save the current frame as rover.jpg
            ## this will allow us to keep a history of frames
            ## if the rover.jpg file does not exist, we will not move it
            if os.path.exists("rover.jpg"):
            
                old_frame_filename = f"old_frames/{most_recent_timestamp}.jpg"
                os.rename("rover.jpg", old_frame_filename)


            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to fetch frame.")
                return

            # Save the frame as an image file
            cv2.imwrite(f"rover.jpg", frame)
            print(f"Captured frame")


        except Exception as e:
            print(f"Error: {e}")
            # Release the video capture object
            print("video capture died")
        finally:
            cap.release()
            ## reconnect 
            cap = cv2.VideoCapture(0)
            cv2.destroyAllWindows()
            
def get_camera_frame():
    global most_recent_timestamp
    most_recent_timestamp = time.time()
    ## read rover.png
    output_filename = "rover.jpg"
    capture_frames_from_stream()
    

    return output_filename
            
def observe():
    global most_recent_timestamp
    global last_few_frames
    global last_few_messages
    frame = get_camera_frame()  
    
    
    observation = upload_images_to_openai(last_few_messages,[frame], """
    Your visual point of view is third-person
    What do you see? 
    You should see the last 5 images in order (so long as there are at least 5 frames to show), so you can see what you are looking at and where you've seen recently.
    Your response should help users inventory their homes.
    Please also make a short list of all objects that you see, for inventory purposes. 
    Don't list walls, doors, or other parts of the building, only objects that would be inventoried in a home.
    """)
    
    print(f"Observation: {observation}")
    ## log observations based on this timestamp 
    with open("observations.jsonl", "a") as f:
        f.write((str(most_recent_timestamp) + "|" + observation + "\n"))

    extract_items(observation)
    return observation
    
def extract_items(observation):
    ## send a call to openai to extract the items from the observation
    ## then save the items to a file
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Extract items listed from the observation, so we can keep track of these items in inventory. Reply with JSON."
            },
            {
                "role": "user",
                "content": observation
            }
        ],
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    items = response.choices[0].message.content
    print(f"Items: {items}")
    ## append
    with open('items.jsonl', "a") as f:
        f.write((str(most_recent_timestamp) + "|" + items + "\n"))

    
def upload_images_to_openai(messages, images, prompt):
    global last_few_frames
    last_few_messages = messages[-8:]
    for image in images:
        # Getting the base64 string
        base64_image = encode_image(image)
        ## put the current frame at the beginning of last_few_frames
        last_few_frames.insert(0, base64_image)
        if len(last_few_frames) > 2:
            last_few_frames.pop(-1)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_client.api_key}",
        }
        content = [{
            "type": "text",
            "text": prompt
        }]
        for image in last_few_frames:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

        payload = {
            "model": "gpt-4o-mini",
            "messages": last_few_messages + [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_json = response.json()
        ## return only the text
        messages.append({
            "role": "assistant",
            "content": response_json["choices"][0]["message"]["content"]
        })
        return response_json["choices"][0]["message"]["content"]
    
if __name__ == "__main__":
    # Example usage
    observe()
    ## make sure to run this every 5 seconds
    while True:
        time.sleep(5)
        observe()