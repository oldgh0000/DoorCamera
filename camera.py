import cv2, face_recognition, numpy, time, os, telegram, configuration
from io import BytesIO

class Camera:

    def __init__(self):
        # Use OpenCV to get video from the camera.
        self.camera = cv2.VideoCapture(configuration.camera["device_id"])
        # Initialize telegram bot.
        self.bot = telegram.Bot(configuration.telegram["token"])
        # Create a list of known encodings and names
        self.known_encodings = []
        self.known_names = []
        self.last_known_names = []
        for person in configuration.persons:
            self.known_names.append(person.name)
            self.known_encodings.append(person.face_encoding)
        self.known_names = tuple(self.known_names)

    def recognize_faces(self, frame):
        # Detect face locations in the current frame.
        frame_face_locations = face_recognition.face_locations(frame)
        # Detect face encodings in the current frame.
        frame_face_encodings = face_recognition.face_encodings(frame)
        # Empty list, that will be used later to put names of the persons
        frame_face_names = []
        frame_face_names_append = frame_face_names.append

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
                frame_face_names_append(name)
            else:
                # If there is a face that does not match any known persons, set them as unknown.
                frame_face_names_append("Unknown")
            
        # Call the method to send a notification to the Telegram Chat.
        if self.last_known_names == frame_face_names:
            pass
        else:
            self.send_notification(frame_face_names, frame)


    def read(self):
        while self.camera.isOpened():
            # Read frame from OpenCV
            response, frame = self.camera.read()
            # Check if the camera responds
            if response == True:
                # Edit the frame to 1/4th the size of its original for faster processing.
                edited_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                edited_frame = cv2.resize(edited_frame, (0, 0), fx=0.25, fy=0.25)
                # Facial Recognition
                self.recognize_faces(edited_frame)
            # Sleep for 0.45 of a second.
            time.sleep(0.75)
        # Release the camera once the loop closes.
        self.camera.release()

    def send_notification(self, names, frame):
        # Check if the number of names detected is greater than zero.
        print(names)
        if len(names) > 0:
            # Create the string of name(s) detected.
            data = ""
            for name in names:
                if len(data) > 0:
                    data += " and "
                data += name
            if len(names) == 1:
                data += " is at the door."
            else:
                data += " are at the door."
            # Find out who is not in the picture, to send them the message.
            people_to_send_message_to = self.known_names.copy()
            for name in names:
                if name in people_to_send_message_to:
                    people_to_send_message_to.remove(name)
            for person in people_to_send_message_to:
                # Send a message of the name(s) at the door.
                self.bot.send_message(chat_id=self.get_person(person).telegram_uid, text=data)
                # Send a photo of the door at the time.
                self.bot.send_photo(chat_id=self.get_person(person).telegram_uid, photo=BytesIO(cv2.imencode(".png", frame[:, :, ::-1])[1]))
        # Reset the last known names once new names are detected.
        if len(names) > 0 and self.last_known_names != names:
            self.last_known_names = names

    def get_person(self, name):
        for person in configuration.persons:
            if person.name == name:
                return person
        return None
