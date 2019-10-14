import cv2, face_recognition, numpy, time, os, telegram, io.BytesIO, configuration

class Camera:

    def __init__(self):
        # Use OpenCV to get video from the camera.
        self.camera = cv2.VideoCapture(configuration.camera["device_id"])
        # Store persons to recognize
        self.persons = persons
        # Initialize telegram bot.
        self.bot = telegram.Bot(token)
        # Create a list of known encodings and names
        self.known_encodings = []
        self.known_names = []
        for person in self.persons:
            self.known_names.append(person.name)
            self.known_encodings.append(person.face_encoding)

    def recognize_faces(self, frame):
        # Detect face locations in the current frame.
        frame_face_locations = face_recognition.face_locations(frame)
        # Detect face encodings in the current frame.
        frame_face_encodings = face_recognition.face_encodings(frame)
        # Empty list, that will be used later to put names of the persons
        frame_face_names = []

        # Loop through every face encoding
        for frame_face_encoding in frame_face_encodings:
            # Compare faces in the frame to known faces to find matches
            matches = face_recognition.compare_faces(self.known_encodings, frame_face_encoding)

            # Use distances to check if the matches are valid
            face_distances = face_recognition.face_distance(self.known_encodings, frame_face_encoding)
            # Determine the best match for a face.
            best_match = numpy.argmin(face_distances)
            # Check if the best match matches any of the matches.
            if matches[best_match]:
                # Set the name to the match
                name = self.known_names[best_match]
                # Append it to the list of names that match in the frame.
                frame_face_names.append(name)
            else:
                # If there is a face that does not match any known persons, set them as unknown.
                frame_face_names.append("Unknown")
            
        # Call the method to send a notification to the Telegram Chat.
        self.send_notification(frame_face_names, frame)


    def read(self):
        while self.camera.isOpened():
            # Read frame from OpenCV
            response, frame = self.camera.read()[:, :, ::-1]
            # Check if the camera responds
            if response == True:
                # Edit the frame to 1/4th the size of its original for faster processing.
                edited_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                # Facial Recognition
                self.recognize_faces(edited_frame)
            # Sleep for 0.45 of a second.
            time.sleep(0.75)
        # Release the camera once the loop closes.
        self.camera.release()

    def send_notification(self, names, frame):
        # Pass if the detected names are the same as the previously known names.
        if self.last_known_names == names:
            pass
        # Check if the number of names detected is greater than zero.
        elif len(names) > 0:
            # Create the string of name(s) detected.
            data = ""
            for i, item in enumerate(names):
                if i:
                    data += " and "
                data += item
            if len(names) == 1:
                data += " is at the door."
            else:
                data += " are at the door."
            # Send a message of the name(s) at the door.
            self.bot.send_message(chat_id=self.chat_id, text=data)
            # Send a photo of the door at the time.
            self.bot.send_photo(chat_id=self.chat_id, photo=BytesIO(cv2.imencode(".jpg", frame[:, :, ::-1])[1]))
        # Reset the last known names once new names are detected.
        if len(names) > 0 and self.last_known_names != names:
            self.last_known_names = names