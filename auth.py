# TODO: currently we are just using this dummy file but whenever the next user is going to work on this we request you to please make a secure and end to end auth instead of this dummy one . also make suer to focus on the security and  the authorisation prat of this
#Make sure to open a new pr to start with this work 

users = {
    "admin": "1234",
    "abhinav": "password"
}

username = input("Username: ")
password = input("Password: ")

if username in users and users[username] == password:
    print("Login successful!")
else:
    print("Invalid username or password.")
